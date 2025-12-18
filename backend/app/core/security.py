# """
# Enhanced security module with Keycloak integration, RBAC, and utilities.
# """
# from typing import Optional, List
# from datetime import datetime, timedelta
# from functools import wraps
# import logging

# from fastapi import Depends, HTTPException, status, Security
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from jose import JWTError, jwt
# import httpx

# from app.core.config import settings
# from app.core.exceptions import UnauthorizedException, ForbiddenException

# logger = logging.getLogger(__name__)

# # Security schemes
# bearer_scheme = HTTPBearer(auto_error=False)


# class Role:
#     """Define user roles."""
#     SUPER_ADMIN = "SUPER_ADMIN"
#     ADMIN = "ADMIN"
#     USER = "USER"
    
#     @classmethod
#     def all_roles(cls) -> List[str]:
#         return [cls.SUPER_ADMIN, cls.ADMIN, cls.USER]
    
#     @classmethod
#     def admin_roles(cls) -> List[str]:
#         return [cls.SUPER_ADMIN, cls.ADMIN]


# class TokenData:
#     """Parsed token data."""
    
#     def __init__(
#         self,
#         sub: str,
#         email: Optional[str] = None,
#         roles: Optional[List[str]] = None,
#         exp: Optional[datetime] = None,
#     ):
#         self.sub = sub
#         self.email = email
#         self.roles = roles or []
#         self.exp = exp
    
#     def has_role(self, role: str) -> bool:
#         """Check if user has specific role."""
#         return role in self.roles
    
#     def has_any_role(self, roles: List[str]) -> bool:
#         """Check if user has any of the specified roles."""
#         return any(role in self.roles for role in roles)
    
#     def is_admin(self) -> bool:
#         """Check if user is admin or super admin."""
#         return self.has_any_role(Role.admin_roles())
    
#     def is_super_admin(self) -> bool:
#         """Check if user is super admin."""
#         return self.has_role(Role.SUPER_ADMIN)


# class KeycloakClient:
#     """Client for Keycloak operations."""
    
#     def __init__(self):
#         self.base_url = settings.KEYCLOAK_URL
#         self.realm = settings.KEYCLOAK_REALM
#         self.client_id = settings.KEYCLOAK_CLIENT_ID
#         self.client_secret = settings.KEYCLOAK_CLIENT_SECRET
#         self._public_key: Optional[str] = None
    
#     async def get_public_key(self) -> str:
#         """Fetch and cache Keycloak public key."""
#         if self._public_key:
#             return self._public_key
        
#         try:
#             async with httpx.AsyncClient() as client:
#                 response = await client.get(settings.JWT_PUBLIC_KEY_URL)
#                 response.raise_for_status()
#                 keys = response.json()["keys"]
                
#                 # Get first RSA key
#                 for key in keys:
#                     if key["kty"] == "RSA":
#                         self._public_key = key
#                         return self._public_key
                
#                 raise ValueError("No RSA public key found")
#         except Exception as e:
#             logger.error(f"Failed to fetch Keycloak public key: {e}")
#             raise
    
#     async def verify_token(self, token: str) -> dict:
#         """Verify JWT token with Keycloak."""
#         try:
#             # For development, we can use unverified decode
#             # In production, verify with public key
#             if settings.is_development:
#                 payload = jwt.decode(
#                     token,
#                     options={"verify_signature": False}
#                 )
#             else:
#                 public_key = await self.get_public_key()
#                 payload = jwt.decode(
#                     token,
#                     public_key,
#                     algorithms=[settings.JWT_ALGORITHM],
#                     audience=self.client_id,
#                 )
            
#             return payload
#         except JWTError as e:
#             logger.error(f"Token verification failed: {e}")
#             raise UnauthorizedException("Invalid authentication token")


# # Global Keycloak client instance
# keycloak = KeycloakClient()


# async def get_current_user(
#     credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
# ) -> TokenData:
#     """
#     Extract and validate current user from JWT token.
    
#     Args:
#         credentials: HTTP Bearer token credentials
        
#     Returns:
#         TokenData: Parsed token data with user info
        
#     Raises:
#         UnauthorizedException: If token is missing or invalid
#     """
#     if not credentials:
#         raise UnauthorizedException("Authentication required")
    
#     try:
#         # Verify token with Keycloak
#         payload = await keycloak.verify_token(credentials.credentials)
        
#         # Extract user data
#         sub = payload.get("sub")
#         if not sub:
#             raise UnauthorizedException("Invalid token: missing subject")
        
#         email = payload.get("email")
        
#         # Extract roles from token
#         roles = []
#         realm_access = payload.get("realm_access", {})
#         roles.extend(realm_access.get("roles", []))
        
#         resource_access = payload.get("resource_access", {})
#         client_roles = resource_access.get(settings.KEYCLOAK_CLIENT_ID, {})
#         roles.extend(client_roles.get("roles", []))
        
#         # Parse expiration
#         exp = None
#         if "exp" in payload:
#             exp = datetime.fromtimestamp(payload["exp"])
        
#         return TokenData(
#             sub=sub,
#             email=email,
#             roles=roles,
#             exp=exp,
#         )
    
#     except UnauthorizedException:
#         raise
#     except Exception as e:
#         logger.error(f"Authentication failed: {e}")
#         raise UnauthorizedException("Authentication failed")


# def require_role(required_role: str):
#     """
#     Decorator to enforce role-based access control.
    
#     Args:
#         required_role: Role required to access the endpoint
        
#     Example:
#         @app.get("/admin")
#         @require_role(Role.ADMIN)
#         async def admin_endpoint(user: TokenData = Depends(get_current_user)):
#             return {"message": "Admin access granted"}
#     """
#     def decorator(func):
#         @wraps(func)
#         async def wrapper(*args, user: TokenData = Depends(get_current_user), **kwargs):
#             if not user.has_role(required_role):
#                 raise ForbiddenException(
#                     f"Role '{required_role}' required for this operation"
#                 )
#             return await func(*args, user=user, **kwargs)
#         return wrapper
#     return decorator


# def require_any_role(required_roles: List[str]):
#     """
#     Decorator to enforce role-based access control (any of roles).
    
#     Args:
#         required_roles: List of roles, user must have at least one
        
#     Example:
#         @app.get("/admin")
#         @require_any_role([Role.ADMIN, Role.SUPER_ADMIN])
#         async def admin_endpoint(user: TokenData = Depends(get_current_user)):
#             return {"message": "Admin access granted"}
#     """
#     def decorator(func):
#         @wraps(func)
#         async def wrapper(*args, user: TokenData = Depends(get_current_user), **kwargs):
#             if not user.has_any_role(required_roles):
#                 raise ForbiddenException(
#                     f"One of roles {required_roles} required for this operation"
#                 )
#             return await func(*args, user=user, **kwargs)
#         return wrapper
#     return decorator


# async def get_admin_user(user: TokenData = Depends(get_current_user)) -> TokenData:
#     """
#     Dependency to ensure user is admin or super admin.
    
#     Example:
#         @app.get("/admin")
#         async def admin_endpoint(user: TokenData = Depends(get_admin_user)):
#             return {"message": "Admin access granted"}
#     """
#     if not user.is_admin():
#         raise ForbiddenException("Admin access required")
#     return user


# async def get_super_admin_user(user: TokenData = Depends(get_current_user)) -> TokenData:
#     """
#     Dependency to ensure user is super admin.
    
#     Example:
#         @app.get("/super-admin")
#         async def super_admin_endpoint(user: TokenData = Depends(get_super_admin_user)):
#             return {"message": "Super admin access granted"}
#     """
#     if not user.is_super_admin():
#         raise ForbiddenException("Super admin access required")
#     return user


# # Optional: API Key authentication (for service-to-service)
# class APIKeyAuth:
#     """API Key authentication handler."""
    
#     def __init__(self):
#         self.valid_keys = set()  # In production, load from database
    
#     def add_key(self, api_key: str) -> None:
#         """Add valid API key."""
#         self.valid_keys.add(api_key)
    
#     def remove_key(self, api_key: str) -> None:
#         """Remove API key."""
#         self.valid_keys.discard(api_key)
    
#     def verify_key(self, api_key: str) -> bool:
#         """Verify API key."""
#         return api_key in self.valid_keys


# api_key_auth = APIKeyAuth()


# async def verify_api_key(
#     api_key: Optional[str] = Depends(lambda: None)  # Extract from header
# ) -> bool:
#     """
#     Verify API key for service-to-service authentication.
    
#     Args:
#         api_key: API key from header
        
#     Returns:
#         bool: True if valid
        
#     Raises:
#         UnauthorizedException: If key is invalid
#     """
#     if not settings.API_KEY_ENABLED:
#         return True
    
#     if not api_key:
#         raise UnauthorizedException("API key required")
    
#     if not api_key_auth.verify_key(api_key):
#         raise UnauthorizedException("Invalid API key")
    
#     return True


# # Password validation utilities
# def validate_password(password: str) -> bool:
#     """
#     Validate password against security requirements.
    
#     Args:
#         password: Password to validate
        
#     Returns:
#         bool: True if valid
        
#     Raises:
#         ValueError: If password doesn't meet requirements
#     """
#     errors = []
    
#     if len(password) < settings.PASSWORD_MIN_LENGTH:
#         errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters")
    
#     if settings.PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
#         errors.append("Password must contain at least one uppercase letter")
    
#     if settings.PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
#         errors.append("Password must contain at least one lowercase letter")
    
#     if settings.PASSWORD_REQUIRE_DIGITS and not any(c.isdigit() for c in password):
#         errors.append("Password must contain at least one digit")
    
#     if settings.PASSWORD_REQUIRE_SPECIAL:
#         special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
#         if not any(c in special_chars for c in password):
#             errors.append("Password must contain at least one special character")
    
#     if errors:
#         raise ValueError("; ".join(errors))
    
#     return True


"""
Enhanced security module with production-ready Keycloak integration

Place this as: backend/app/core/security_enhanced.py
Or replace backend/app/core/security.py
"""

from typing import Optional, List
from datetime import datetime
import logging

from fastapi import Depends, HTTPException, status, Request,Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.keycloak.service import get_keycloak_service

logger = logging.getLogger(__name__)

security = HTTPBearer()


class Role:
    """Define user roles"""
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    USER = "USER"
    VIEWER = "VIEWER"
    
    @classmethod
    def all_roles(cls) -> List[str]:
        return [cls.SUPER_ADMIN, cls.ADMIN, cls.USER, cls.VIEWER]
    
    @classmethod
    def admin_roles(cls) -> List[str]:
        return [cls.SUPER_ADMIN, cls.ADMIN]


class TokenData(BaseModel):
    """Parsed token data with multi-tenant support"""
    sub: str  # User ID (Keycloak ID)
    email: Optional[str] = None
    username: Optional[str] = None
    tenant: Optional[str] = None  # Tenant slug from token
    roles: List[str] = []
    permissions: List[str] = []
    exp: Optional[datetime] = None
    
    def has_role(self, role: str) -> bool:
        """Check if user has specific role"""
        return role in self.roles
    
    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles"""
        return any(role in self.roles for role in roles)
    
    def is_admin(self) -> bool:
        """Check if user is admin or super admin"""
        return self.has_any_role(Role.admin_roles())
    
    def is_super_admin(self) -> bool:
        """Check if user is super admin"""
        return self.has_role(Role.SUPER_ADMIN)
    
    def has_tenant_access(self, tenant_slug: str) -> bool:
        """Check if user has access to specific tenant"""
        if self.is_super_admin():
            return True  # Super admin has access to all tenants
        return self.tenant == tenant_slug
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> TokenData:
    """
    Extract and validate current user from JWT token
    
    Args:
        request: FastAPI request (for tenant context)
        credentials: HTTP Bearer token credentials
        
    Returns:
        TokenData: Parsed token data with user info
        
    Raises:
        UnauthorizedException: If token is missing or invalid
    """
    if not credentials:
        raise UnauthorizedException("Authentication required")
    
    try:
        # Get Keycloak service
        keycloak = get_keycloak_service()
        
        # Get expected tenant from request (set by tenant middleware)
        expected_tenant = getattr(request.state, "tenant", None)
        tenant_slug = expected_tenant.slug if expected_tenant else None
        
        # Verify token with tenant validation
        payload = await keycloak.verify_token(
            credentials.credentials,
            tenant_slug=tenant_slug
        )
        
        # Extract user data
        sub = payload.get("sub")
        if not sub:
            raise UnauthorizedException("Invalid token: missing subject")
        
        email = payload.get("email")
        username = payload.get("preferred_username")
        
        # Extract tenant from custom attribute
        tenant = None
        if "tenant" in payload:
            tenant = payload["tenant"]
        elif "attributes" in payload and "tenant" in payload["attributes"]:
            tenant = payload["attributes"]["tenant"]
            if isinstance(tenant, list):
                tenant = tenant[0] if tenant else None
        
        # Extract roles from token
        roles = []
        
        # Realm roles
        realm_access = payload.get("realm_access", {})
        roles.extend(realm_access.get("roles", []))
        
        # Client roles
        resource_access = payload.get("resource_access", {})
        client_roles = resource_access.get(settings.KEYCLOAK_CLIENT_ID, {})
        roles.extend(client_roles.get("roles", []))
        
        # Extract permissions (if using authorization services)
        permissions = []
        authorization = payload.get("authorization", {})
        permissions.extend(authorization.get("permissions", []))
        
        # Parse expiration
        exp = None
        if "exp" in payload:
            exp = datetime.fromtimestamp(payload["exp"])
        
        return TokenData(
            sub=sub,
            email=email,
            username=username,
            tenant=tenant,
            roles=roles,
            permissions=permissions,
            exp=exp,
        )
    
    except UnauthorizedException:
        raise
    except Exception as e:
        logger.error(f"Authentication failed: {e}", exc_info=True)
        raise UnauthorizedException("Authentication failed")


async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Get current active user (additional validation can be added here)
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        TokenData: Validated active user
    """
    # Add additional checks here (e.g., is_active from database)
    return current_user


async def require_tenant_access(
    tenant_slug: str,
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Require user to have access to specific tenant
    
    Args:
        tenant_slug: Required tenant slug
        current_user: Current authenticated user
        
    Returns:
        TokenData: User with verified tenant access
        
    Raises:
        ForbiddenException: If user doesn't have access to tenant
    """
    if not current_user.has_tenant_access(tenant_slug):
        raise ForbiddenException(
            f"Access denied: User does not have access to tenant '{tenant_slug}'"
        )
    return current_user


def require_role(required_role: str):
    """
    Decorator to enforce role-based access control
    
    Args:
        required_role: Role required to access the endpoint
        
    Example:
        @router.get("/admin")
        @require_role(Role.ADMIN)
        async def admin_endpoint(user: TokenData = Depends(get_current_user)):
            return {"message": "Admin access granted"}
    """
    async def dependency(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if not current_user.has_role(required_role):
            raise ForbiddenException(
                f"Role '{required_role}' required for this operation"
            )
        return current_user
    
    return dependency


def require_any_role(required_roles: List[str]):
    """
    Decorator to enforce role-based access control (any of roles)
    
    Args:
        required_roles: List of roles, user must have at least one
        
    Example:
        @router.get("/admin")
        @require_any_role([Role.ADMIN, Role.SUPER_ADMIN])
        async def admin_endpoint(user: TokenData = Depends(get_current_user)):
            return {"message": "Admin access granted"}
    """
    async def dependency(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if not current_user.has_any_role(required_roles):
            raise ForbiddenException(
                f"One of roles {required_roles} required for this operation"
            )
        return current_user
    
    return dependency


def require_permission(permission: str):
    """
    Decorator to enforce permission-based access control
    
    Args:
        permission: Permission required to access the endpoint
        
    Example:
        @router.post("/users")
        @require_permission("users:create")
        async def create_user(user: TokenData = Depends(get_current_user)):
            return {"message": "User created"}
    """
    async def dependency(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if not current_user.has_permission(permission):
            raise ForbiddenException(
                f"Permission '{permission}' required for this operation"
            )
        return current_user
    
    return dependency


# Convenience dependencies for common use cases
async def get_admin_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """
    Dependency to ensure user is admin or super admin
    
    Example:
        @router.get("/admin/stats")
        async def get_stats(user: TokenData = Depends(get_admin_user)):
            return {"stats": "..."}
    """
    if not current_user.is_admin():
        raise ForbiddenException("Admin access required")
    return current_user


async def get_super_admin_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """
    Dependency to ensure user is super admin
    
    Example:
        @router.delete("/tenants/{slug}")
        async def delete_tenant(user: TokenData = Depends(get_super_admin_user)):
            return {"message": "Tenant deleted"}
    """
    if not current_user.is_super_admin():
        raise ForbiddenException("Super admin access required")
    return current_user