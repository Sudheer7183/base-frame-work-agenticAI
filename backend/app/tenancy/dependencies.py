"""FastAPI dependency injection functions"""

from typing import Optional
from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from .models import Tenant
from .context import get_tenant as get_tenant_from_context
from .db import get_session
from .exceptions import TenantError, TenantNotFoundError, TenantInactiveError


def get_db() -> Session:
    """Dependency to get database session"""
    db = get_session()
    try:
        yield db
    finally:
        db.close()


def get_current_tenant(request: Request) -> Optional[Tenant]:
    """
    Dependency to get current tenant from request state
    
    The tenant should be set by TenantMiddleware
    Returns None if no tenant is set (for public endpoints)
    """
    return getattr(request.state, "tenant", None)


def require_tenant(tenant: Optional[Tenant] = Depends(get_current_tenant)) -> Tenant:
    """
    Dependency to require a tenant (for protected endpoints)
    
    Raises 400 if no tenant is set
    """
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant identifier required"
        )
    return tenant


def get_tenant_schema() -> Optional[str]:
    """Dependency to get current tenant schema from context"""
    return get_tenant_from_context()


def require_tenant_schema(schema: Optional[str] = Depends(get_tenant_schema)) -> str:
    """
    Dependency to require tenant schema
    
    Raises 400 if no tenant schema is set
    """
    if schema is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No tenant context set"
        )
    return schema