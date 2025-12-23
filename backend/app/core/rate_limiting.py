"""
Rate Limiting System - P1 Fix
Advanced rate limiting with Redis backend, multiple strategies, and quota management
"""

import asyncio
import logging
import time
from typing import Optional, Callable, Dict, Any
from datetime import datetime, timedelta
from functools import wraps
from enum import Enum

import redis.asyncio as aioredis
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies"""
    FIXED_WINDOW = "fixed_window"  # Simple fixed time window
    SLIDING_WINDOW = "sliding_window"  # More accurate, uses sorted sets
    TOKEN_BUCKET = "token_bucket"  # Allows bursts
    LEAKY_BUCKET = "leaky_bucket"  # Smooth rate


class RateLimitScope(str, Enum):
    """Rate limit scopes"""
    GLOBAL = "global"  # All requests
    PER_USER = "per_user"  # Per authenticated user
    PER_IP = "per_ip"  # Per IP address
    PER_ENDPOINT = "per_endpoint"  # Per API endpoint
    PER_TENANT = "per_tenant"  # Per tenant (multi-tenant)


class RateLimitExceeded(HTTPException):
    """Rate limit exceeded exception"""
    
    def __init__(
        self,
        limit: int,
        window: int,
        retry_after: int,
        scope: str = "global"
    ):
        detail = {
            "error": "rate_limit_exceeded",
            "message": f"Rate limit exceeded: {limit} requests per {window} seconds",
            "limit": limit,
            "window": window,
            "retry_after": retry_after,
            "scope": scope
        }
        
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after)}
        )


class RateLimiter:
    """
    Advanced rate limiter with Redis backend
    
    Features:
    - Multiple strategies (fixed window, sliding window, token bucket)
    - Multiple scopes (global, per-user, per-IP, per-endpoint, per-tenant)
    - Quota management
    - Async support
    - Detailed metrics
    """
    
    def __init__(
        self,
        redis_url: str = None,
        default_limit: int = 60,
        default_window: int = 60,
        strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    ):
        """
        Initialize rate limiter
        
        Args:
            redis_url: Redis connection URL
            default_limit: Default requests per window
            default_window: Default time window (seconds)
            strategy: Rate limiting strategy
        """
        self.redis_url = redis_url or settings.REDIS_URL or "redis://localhost:6379"
        self.default_limit = default_limit
        self.default_window = default_window
        self.strategy = strategy
        self.redis_client: Optional[aioredis.Redis] = None
    
    async def connect(self):
        """Connect to Redis"""
        if not self.redis_client:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Rate limiter connected to Redis")
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("Rate limiter disconnected from Redis")
    
    def _get_key(
        self,
        scope: RateLimitScope,
        identifier: str,
        endpoint: Optional[str] = None
    ) -> str:
        """
        Generate Redis key for rate limit tracking
        
        Args:
            scope: Rate limit scope
            identifier: Unique identifier (user_id, IP, etc.)
            endpoint: API endpoint (optional)
            
        Returns:
            Redis key
        """
        parts = ["ratelimit", scope.value]
        
        if endpoint:
            # Sanitize endpoint for Redis key
            endpoint_safe = endpoint.replace("/", ":").strip(":")
            parts.append(endpoint_safe)
        
        parts.append(identifier)
        
        return ":".join(parts)
    
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if rate limit is exceeded
        
        Args:
            key: Redis key
            limit: Request limit
            window: Time window (seconds)
            
        Returns:
            Tuple of (is_allowed, metadata)
        """
        await self.connect()
        
        if self.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._check_sliding_window(key, limit, window)
        elif self.strategy == RateLimitStrategy.FIXED_WINDOW:
            return await self._check_fixed_window(key, limit, window)
        elif self.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._check_token_bucket(key, limit, window)
        else:
            return await self._check_fixed_window(key, limit, window)
    
    async def _check_sliding_window(
        self,
        key: str,
        limit: int,
        window: int
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check rate limit using sliding window algorithm
        
        Most accurate but slightly more expensive
        """
        now = time.time()
        window_start = now - window
        
        # Remove old entries
        await self.redis_client.zremrangebyscore(key, 0, window_start)
        
        # Count requests in current window
        current_count = await self.redis_client.zcard(key)
        
        # Calculate metadata
        remaining = max(0, limit - current_count)
        
        if current_count >= limit:
            # Get oldest request time to calculate retry_after
            oldest = await self.redis_client.zrange(key, 0, 0, withscores=True)
            if oldest:
                oldest_time = oldest[0][1]
                retry_after = int(window - (now - oldest_time)) + 1
            else:
                retry_after = window
            
            metadata = {
                "limit": limit,
                "remaining": 0,
                "reset": int(now + retry_after),
                "retry_after": retry_after,
                "current_count": current_count
            }
            return False, metadata
        
        # Add current request
        await self.redis_client.zadd(key, {str(now): now})
        
        # Set expiration
        await self.redis_client.expire(key, window)
        
        # Calculate reset time
        reset = int(now + window)
        
        metadata = {
            "limit": limit,
            "remaining": remaining - 1,  # Account for current request
            "reset": reset,
            "retry_after": 0,
            "current_count": current_count + 1
        }
        
        return True, metadata
    
    async def _check_fixed_window(
        self,
        key: str,
        limit: int,
        window: int
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check rate limit using fixed window algorithm
        
        Simple and efficient but can have burst issues at window boundaries
        """
        now = int(time.time())
        window_key = f"{key}:{now // window}"
        
        # Increment counter
        current_count = await self.redis_client.incr(window_key)
        
        # Set expiration on first request
        if current_count == 1:
            await self.redis_client.expire(window_key, window)
        
        remaining = max(0, limit - current_count)
        reset = ((now // window) + 1) * window
        
        if current_count > limit:
            retry_after = reset - now
            metadata = {
                "limit": limit,
                "remaining": 0,
                "reset": reset,
                "retry_after": retry_after,
                "current_count": current_count
            }
            return False, metadata
        
        metadata = {
            "limit": limit,
            "remaining": remaining,
            "reset": reset,
            "retry_after": 0,
            "current_count": current_count
        }
        
        return True, metadata
    
    async def _check_token_bucket(
        self,
        key: str,
        limit: int,
        window: int
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check rate limit using token bucket algorithm
        
        Allows bursts while maintaining average rate
        """
        now = time.time()
        refill_rate = limit / window  # tokens per second
        
        # Get bucket state
        bucket_data = await self.redis_client.hgetall(key)
        
        if bucket_data:
            tokens = float(bucket_data.get("tokens", limit))
            last_refill = float(bucket_data.get("last_refill", now))
        else:
            tokens = limit
            last_refill = now
        
        # Refill tokens
        time_passed = now - last_refill
        tokens = min(limit, tokens + (time_passed * refill_rate))
        
        if tokens < 1:
            # Not enough tokens
            retry_after = int((1 - tokens) / refill_rate) + 1
            metadata = {
                "limit": limit,
                "remaining": 0,
                "reset": int(now + retry_after),
                "retry_after": retry_after,
                "current_count": int(limit - tokens)
            }
            return False, metadata
        
        # Consume token
        tokens -= 1
        
        # Update bucket state
        await self.redis_client.hset(key, mapping={
            "tokens": str(tokens),
            "last_refill": str(now)
        })
        await self.redis_client.expire(key, window * 2)
        
        metadata = {
            "limit": limit,
            "remaining": int(tokens),
            "reset": int(now + window),
            "retry_after": 0,
            "current_count": int(limit - tokens)
        }
        
        return True, metadata
    
    async def is_allowed(
        self,
        identifier: str,
        scope: RateLimitScope = RateLimitScope.GLOBAL,
        endpoint: Optional[str] = None,
        limit: Optional[int] = None,
        window: Optional[int] = None
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed
        
        Args:
            identifier: Unique identifier (user_id, IP, etc.)
            scope: Rate limit scope
            endpoint: API endpoint
            limit: Request limit (uses default if None)
            window: Time window in seconds (uses default if None)
            
        Returns:
            Tuple of (is_allowed, metadata)
        """
        limit = limit or self.default_limit
        window = window or self.default_window
        
        key = self._get_key(scope, identifier, endpoint)
        
        return await self.check_rate_limit(key, limit, window)
    
    async def reset(
        self,
        identifier: str,
        scope: RateLimitScope = RateLimitScope.GLOBAL,
        endpoint: Optional[str] = None
    ):
        """
        Reset rate limit for an identifier
        
        Args:
            identifier: Unique identifier
            scope: Rate limit scope
            endpoint: API endpoint
        """
        await self.connect()
        key = self._get_key(scope, identifier, endpoint)
        await self.redis_client.delete(key)
        logger.info(f"Rate limit reset for {key}")
    
    async def get_stats(
        self,
        identifier: str,
        scope: RateLimitScope = RateLimitScope.GLOBAL,
        endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get rate limit statistics
        
        Args:
            identifier: Unique identifier
            scope: Rate limit scope
            endpoint: API endpoint
            
        Returns:
            Statistics dictionary
        """
        await self.connect()
        key = self._get_key(scope, identifier, endpoint)
        
        if self.strategy == RateLimitStrategy.SLIDING_WINDOW:
            count = await self.redis_client.zcard(key)
            return {
                "current_count": count,
                "limit": self.default_limit,
                "remaining": max(0, self.default_limit - count),
                "strategy": self.strategy.value
            }
        elif self.strategy == RateLimitStrategy.TOKEN_BUCKET:
            bucket_data = await self.redis_client.hgetall(key)
            tokens = float(bucket_data.get("tokens", self.default_limit)) if bucket_data else self.default_limit
            return {
                "current_tokens": tokens,
                "limit": self.default_limit,
                "remaining": int(tokens),
                "strategy": self.strategy.value
            }
        else:
            # Fixed window
            now = int(time.time())
            window_key = f"{key}:{now // self.default_window}"
            count = await self.redis_client.get(window_key)
            count = int(count) if count else 0
            return {
                "current_count": count,
                "limit": self.default_limit,
                "remaining": max(0, self.default_limit - count),
                "strategy": self.strategy.value
            }


# Global rate limiter instance
rate_limiter = RateLimiter(
    default_limit=settings.RATE_LIMIT_PER_MINUTE if hasattr(settings, 'RATE_LIMIT_PER_MINUTE') else 60,
    default_window=60,
    strategy=RateLimitStrategy.SLIDING_WINDOW
)


# Dependency for FastAPI
async def check_rate_limit_dependency(
    request: Request,
    scope: RateLimitScope = RateLimitScope.PER_IP,
    limit: Optional[int] = None,
    window: Optional[int] = None
):
    """
    FastAPI dependency for rate limiting
    
    Usage:
        @app.get("/endpoint", dependencies=[Depends(check_rate_limit_dependency)])
        async def endpoint(): ...
    """
    # Get identifier based on scope
    if scope == RateLimitScope.PER_IP:
        identifier = request.client.host if hasattr(request, 'client') else "unknown"
    elif scope == RateLimitScope.PER_USER:
        # Extract user ID from request (assuming auth middleware sets it)
        identifier = str(getattr(request.state, 'user_id', 'anonymous'))
    elif scope == RateLimitScope.PER_ENDPOINT:
        identifier = request.url.path
    else:
        identifier = "global"
    
    # Check rate limit
    is_allowed, metadata = await rate_limiter.is_allowed(
        identifier=identifier,
        scope=scope,
        endpoint=request.url.path,
        limit=limit,
        window=window
    )
    
    # Add rate limit headers to response
    request.state.rate_limit_metadata = metadata
    
    if not is_allowed:
        raise RateLimitExceeded(
            limit=metadata["limit"],
            window=window or rate_limiter.default_window,
            retry_after=metadata["retry_after"],
            scope=scope.value
        )


# Decorator for rate limiting
def rate_limit(
    limit: int = 60,
    window: int = 60,
    scope: RateLimitScope = RateLimitScope.PER_IP
):
    """
    Decorator for rate limiting functions
    
    Usage:
        @rate_limit(limit=10, window=60, scope=RateLimitScope.PER_USER)
        async def my_function(request: Request): ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find Request object in args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # If no request found, execute without rate limiting
                logger.warning(f"No Request object found in {func.__name__}, skipping rate limit")
                return await func(*args, **kwargs)
            
            # Check rate limit
            await check_rate_limit_dependency(request, scope, limit, window)
            
            # Execute function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator
