"""Tenant resolution middleware"""

import logging
import time
from typing import Set
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN
from .resolver import TenantResolver
from .context import clear_tenant
from .exceptions import TenantError, TenantNotFoundError, TenantInactiveError
from .db import get_session

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware to resolve and set tenant context for each request
    
    Exempts certain paths from tenant resolution (health checks, docs, etc.)
    """
    
    # Paths that don't require tenant resolution
    EXEMPT_PATHS: Set[str] = {
        "/health",
        "/healthz",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/platform/tenants",  # Tenant management endpoints
        "/auth/login",
        "/auth/callback",
        "/api/v1/users/me",
        "/api/v1/auth/invitation",      # Invitation details (public)
        "/api/v1/auth/sso/callback",    # SSO callback
        "/api/v1/auth/sso/providers",   # SSO providers list
    }
    
    def __init__(self, app, exempt_paths: Set[str] = None):
        super().__init__(app)
        if exempt_paths:
            self.EXEMPT_PATHS = self.EXEMPT_PATHS.union(exempt_paths)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process each request"""
        start_time = time.time()
        
        # Clear any existing tenant context
        if request.method == "OPTIONS":
            return await call_next(request)

        clear_tenant()
        
        # Check if path is exempt
        if self._is_exempt_path(request.url.path):
            logger.debug(f"Exempt path, skipping tenant resolution: {request.url.path}")
            response = await call_next(request)
            return response
        
        # Resolve tenant
        db = get_session()
        try:
            resolver = TenantResolver(db)
            
            # Get JWT payload if available (set by auth middleware)
            # jwt_payload = getattr(request.state, "user", None)
            auth_header = request.headers.get("Authorization")
            jwt_payload = None
            if auth_header and auth_header.startswith("Bearer "):
                try:
                    import jwt
                    token = auth_header.split(" ")[1]
                    # Decode without verification just for tenant resolution
                    jwt_payload = jwt.decode(token, options={"verify_signature": False})
                except Exception:
                    jwt_payload = None
            
            # Resolve tenant
            tenant = resolver.resolve(request, jwt_payload)
            
            # Store tenant in request state for later access
            request.state.tenant = tenant
            
            # Log tenant resolution time
            resolution_time = time.time() - start_time
            logger.debug(
                f"Tenant resolved in {resolution_time:.3f}s: "
                f"{tenant.slug} ({tenant.schema_name})"
            )
            
            # Process request
            response = await call_next(request)
            
            # Add tenant header to response (for debugging)
            response.headers["X-Tenant-Slug"] = tenant.slug
            
            return response
            
        except TenantNotFoundError as e:
            logger.warning(f"Tenant not found: {e}")
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={
                    "error": "tenant_not_found",
                    "message": str(e),
                    "details": "Please provide a valid tenant identifier"
                }
            )
        
        except TenantInactiveError as e:
            logger.warning(f"Inactive tenant access attempt: {e}")
            return JSONResponse(
                status_code=HTTP_403_FORBIDDEN,
                content={
                    "error": "tenant_inactive",
                    "message": str(e),
                    "details": "This tenant is currently inactive or suspended"
                }
            )
        
        except TenantError as e:
            logger.error(f"Tenant error: {e}")
            return JSONResponse(
                status_code=HTTP_400_BAD_REQUEST,
                content={
                    "error": "tenant_error",
                    "message": str(e)
                }
            )
        
        except Exception as e:
            logger.exception(f"Unexpected error in tenant middleware: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "internal_error",
                    "message": "An unexpected error occurred"
                }
            )
        
        finally:
            db.close()
            clear_tenant()
    
    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from tenant resolution"""
        # Exact match
        if path in self.EXEMPT_PATHS:
            return True
        
        # Prefix match for paths like /platform/tenants/*
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path):
                return True
        
        return False
