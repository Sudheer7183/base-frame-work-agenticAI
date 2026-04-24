

"""
Enhanced security module with proper RBAC enforcement

Place this at: backend/app/core/security.py
"""

from typing import Optional, List
from datetime import datetime
import logging

from fastapi import Depends, HTTPException, status, Request, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.core.config import settings
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.keycloak.service import get_keycloak_service

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)  # Don't auto-error, we'll handle it


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


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> TokenData:
    """
    Extract and validate current user from JWT token
    
    This is the main authentication dependency
    """
    if not credentials:
        logger.warning("No credentials provided")
        raise UnauthorizedException("Authentication required")
    
    try:
        # Get Keycloak service
        keycloak = get_keycloak_service()
        
        # Get expected tenant from request (set by tenant middleware)
        expected_tenant = getattr(request.state, "tenant", None)
        tenant_slug = expected_tenant.slug if expected_tenant else None
        
        # Verify token (skip tenant validation for now - we'll do it separately)
        payload = await keycloak.verify_token(
            credentials.credentials,
            tenant_slug=None  # Don't validate tenant in token verification
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
        
        # Extract permissions
        permissions = []
        authorization = payload.get("authorization", {})
        permissions.extend(authorization.get("permissions", []))
        
        # Parse expiration
        exp = None
        if "exp" in payload:
            exp = datetime.fromtimestamp(payload["exp"])
        
        token_data = TokenData(
            sub=sub,
            email=email,
            username=username,
            tenant=tenant,
            roles=roles,
            permissions=permissions,
            exp=exp,
        )
        
        logger.debug(f"User authenticated: {email}, roles: {roles}")
        
        return token_data
    
    except UnauthorizedException:
        raise
    except Exception as e:
        logger.error(f"Authentication failed: {e}", exc_info=True)
        raise UnauthorizedException("Authentication failed")


# Convenience dependency for requiring authentication without role checks
get_current_active_user = get_current_user


async def get_admin_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Require admin or super admin role
    
    Use this as a dependency on endpoints that need admin access
    """
    if not current_user.is_admin():
        logger.warning(
            f"User {current_user.email} attempted admin access with roles: {current_user.roles}"
        )
        raise ForbiddenException("Admin access required")
    return current_user


async def get_super_admin_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Require super admin role
    
    Use this for platform-level operations
    """
    if not current_user.is_super_admin():
        logger.warning(
            f"User {current_user.email} attempted super admin access with roles: {current_user.roles}"
        )
        raise ForbiddenException("Super admin access required")
    return current_user


def require_role(required_role: str):
    """
    Create a dependency that requires a specific role
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(user: TokenData = Depends(require_role(Role.ADMIN))):
            ...
    """
    async def dependency(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if not current_user.has_role(required_role):
            logger.warning(
                f"User {current_user.email} missing required role {required_role}. "
                f"Has: {current_user.roles}"
            )
            raise ForbiddenException(
                f"Role '{required_role}' required for this operation"
            )
        return current_user
    
    return dependency


def require_any_role(required_roles: List[str]):
    """
    Create a dependency that requires any of the specified roles
    
    Usage:
        @router.get("/endpoint")
        async def endpoint(
            user: TokenData = Depends(require_any_role([Role.ADMIN, Role.USER]))
        ):
            ...
    """
    async def dependency(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if not current_user.has_any_role(required_roles):
            logger.warning(
                f"User {current_user.email} missing required roles {required_roles}. "
                f"Has: {current_user.roles}"
            )
            raise ForbiddenException(
                f"One of roles {required_roles} required for this operation"
            )
        return current_user
    
    return dependency