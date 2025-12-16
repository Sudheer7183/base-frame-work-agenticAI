"""Thread-safe tenant context management using contextvars"""

from contextvars import ContextVar
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Context variable for current tenant schema
tenant_context: ContextVar[Optional[str]] = ContextVar("tenant_schema", default=None)

# Context variable for tenant slug (for logging)
tenant_slug_context: ContextVar[Optional[str]] = ContextVar("tenant_slug", default=None)


def set_tenant(schema: str, slug: str = None) -> None:
    """
    Set the current tenant context
    
    Args:
        schema: PostgreSQL schema name (e.g., 'tenant_acme')
        slug: Tenant slug for logging (e.g., 'acme')
    """
    tenant_context.set(schema)
    if slug:
        tenant_slug_context.set(slug)
    logger.debug(f"Tenant context set: schema={schema}, slug={slug}")


def get_tenant() -> Optional[str]:
    """Get the current tenant schema from context"""
    return tenant_context.get()


def get_tenant_slug() -> Optional[str]:
    """Get the current tenant slug from context"""
    return tenant_slug_context.get()


def clear_tenant() -> None:
    """Clear the tenant context"""
    tenant_context.set(None)
    tenant_slug_context.set(None)
    logger.debug("Tenant context cleared")


def require_tenant() -> str:
    """
    Get tenant schema, raising error if not set
    
    Raises:
        TenantNotFoundError: If no tenant is set in context
    """
    from .exceptions import TenantNotFoundError
    
    tenant = get_tenant()
    if not tenant:
        raise TenantNotFoundError("No tenant set in current context")
    return tenant