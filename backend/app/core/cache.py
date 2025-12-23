"""
Caching Layer Implementation
Provides Redis-based caching with fallback to in-memory cache
"""

import logging
import json
import hashlib
from typing import Any, Optional, Callable
from datetime import timedelta
from functools import wraps
import asyncio

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

logger = logging.getLogger(__name__)


class CacheBackend:
    """Abstract cache backend interface"""
    
    async def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        raise NotImplementedError
    
    async def delete(self, key: str) -> bool:
        raise NotImplementedError
    
    async def exists(self, key: str) -> bool:
        raise NotImplementedError
    
    async def clear_pattern(self, pattern: str) -> int:
        raise NotImplementedError


class RedisCache(CacheBackend):
    """Redis-based cache backend"""
    
    def __init__(self, redis_url: str, default_ttl: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self._client: Optional[aioredis.Redis] = None
        self._connected = False
    
    # async def connect(self):
    #     """Connect to Redis"""
    #     if not REDIS_AVAILABLE:
    #         raise RuntimeError("redis package not installed")
        
    #     try:
    #         self._client = await aioredis.from_url(
    #             self.redis_url,
    #             encoding="utf-8",
    #             decode_responses=True
    #         )
    #         await self._client.ping()
    #         self._connected = True
    #         logger.info("Connected to Redis cache")
    #     except Exception as e:
    #         logger.error(f"Failed to connect to Redis: {e}")
    #         self._connected = False
    #         raise
    
    async def connect(self):
        """Connect to Redis"""
        if not REDIS_AVAILABLE:
            raise RuntimeError("redis package not installed")
        
        try:
            self._client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5  # Add timeout
            )
            # Test the connection
            await self._client.ping()
            self._connected = True
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._connected = False
            raise

    async def disconnect(self):
        """Disconnect from Redis"""
        if self._client:
            await self._client.close()
            self._connected = False
            logger.info("Disconnected from Redis")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self._connected:
            return None
        
        try:
            value = await self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        if not self._connected:
            return False
        
        try:
            serialized = json.dumps(value)
            ttl_seconds = ttl or self.default_ttl
            
            await self._client.set(key, serialized, ex=ttl_seconds)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self._connected:
            return False
        
        try:
            result = await self._client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self._connected:
            return False
        
        try:
            result = await self._client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self._connected:
            return 0
        
        try:
            cursor = 0
            deleted_count = 0
            
            while True:
                cursor, keys = await self._client.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted_count += await self._client.delete(*keys)
                
                if cursor == 0:
                    break
            
            logger.info(f"Cleared {deleted_count} keys matching pattern: {pattern}")
            return deleted_count
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0


class InMemoryCache(CacheBackend):
    """In-memory cache backend (fallback)"""
    
    def __init__(self, default_ttl: int = 3600):
        self.default_ttl = default_ttl
        self._cache: dict = {}
        self._expiry: dict = {}
        logger.info("Using in-memory cache")
    
    async def _cleanup_expired(self):
        """Remove expired entries"""
        import time
        current_time = time.time()
        expired_keys = [
            key for key, expiry in self._expiry.items()
            if expiry < current_time
        ]
        for key in expired_keys:
            del self._cache[key]
            del self._expiry[key]
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        await self._cleanup_expired()
        return self._cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        import time
        self._cache[key] = value
        ttl_seconds = ttl or self.default_ttl
        self._expiry[key] = time.time() + ttl_seconds
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if key in self._cache:
            del self._cache[key]
            del self._expiry[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        await self._cleanup_expired()
        return key in self._cache
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        import re
        # Convert glob pattern to regex
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        regex = re.compile(regex_pattern)
        
        matching_keys = [key for key in self._cache.keys() if regex.match(key)]
        for key in matching_keys:
            del self._cache[key]
            if key in self._expiry:
                del self._expiry[key]
        
        return len(matching_keys)


class CacheManager:
    """
    High-level cache manager
    Provides caching utilities and decorators
    """
    
    def __init__(self, backend: CacheBackend):
        self.backend = backend
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with stats tracking"""
        value = await self.backend.get(key)
        if value is not None:
            self._stats["hits"] += 1
            logger.debug(f"Cache hit: {key}")
        else:
            self._stats["misses"] += 1
            logger.debug(f"Cache miss: {key}")
        return value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with stats tracking"""
        result = await self.backend.set(key, value, ttl)
        if result:
            self._stats["sets"] += 1
        return result
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        result = await self.backend.delete(key)
        if result:
            self._stats["deletes"] += 1
        return result
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get value from cache or compute and cache it
        
        Args:
            key: Cache key
            factory: Function to compute value if not cached
            ttl: Time to live in seconds
            
        Returns:
            Cached or computed value
        """
        # Try cache first
        value = await self.get(key)
        if value is not None:
            return value
        
        # Compute value
        if asyncio.iscoroutinefunction(factory):
            value = await factory()
        else:
            value = factory()
        
        # Cache it
        await self.set(key, value, ttl)
        return value
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            self._stats["hits"] / total_requests * 100
            if total_requests > 0 else 0
        )
        
        return {
            **self._stats,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2)
        }
    
    def reset_stats(self):
        """Reset statistics"""
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }


def cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from function arguments
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        MD5 hash of arguments
    """
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator to cache function results
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
        
    Usage:
        @cached(ttl=300, key_prefix="user")
        async def get_user(user_id: int):
            # Expensive operation
            return fetch_user_from_db(user_id)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache manager from somewhere (could be injected)
            # For now, this is a placeholder
            cache_manager = get_cache_manager()
            
            # Generate cache key
            func_name = f"{func.__module__}.{func.__name__}"
            arg_hash = cache_key(*args, **kwargs)
            cache_key_str = f"{key_prefix}:{func_name}:{arg_hash}"
            
            # Try to get from cache
            cached_value = await cache_manager.get(cache_key_str)
            if cached_value is not None:
                return cached_value
            
            # Execute function
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Cache result
            await cache_manager.set(cache_key_str, result, ttl)
            return result
        
        return wrapper
    return decorator


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


# def init_cache(redis_url: Optional[str] = None, default_ttl: int = 3600):
#     """
#     Initialize cache system
    
#     Args:
#         redis_url: Redis connection URL (None for in-memory)
#         default_ttl: Default TTL in seconds
#     """
#     global _cache_manager
    
#     if redis_url and REDIS_AVAILABLE:
#         backend = RedisCache(redis_url, default_ttl)
#         asyncio.create_task(backend.connect())
#     else:
#         if redis_url and not REDIS_AVAILABLE:
#             logger.warning("Redis not available, using in-memory cache")
#         backend = InMemoryCache(default_ttl)
    
#     _cache_manager = CacheManager(backend)
#     logger.info("Cache system initialized")
def init_cache(redis_url: Optional[str] = None, default_ttl: int = 3600):
    """Initialize cache system"""
    global _cache_manager
    
    if redis_url:
        try:
            import redis
            # Test sync connection first
            r = redis.from_url(redis_url, socket_connect_timeout=2)
            r.ping()
            r.close()
            
            # Use async version
            backend = RedisCache(redis_url, default_ttl)
            # Note: Connection established on first use
            logger.info("Redis cache backend created")
        except Exception as e:
            logger.warning(f"Redis unavailable: {e}, using in-memory")
            backend = InMemoryCache(default_ttl)
    else:
        backend = InMemoryCache(default_ttl)
    
    _cache_manager = CacheManager(backend)

def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    if _cache_manager is None:
        raise RuntimeError("Cache not initialized. Call init_cache() first")
    return _cache_manager
