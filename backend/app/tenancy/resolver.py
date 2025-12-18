"""Tenant resolution logic"""

import logging
from typing import Optional, Dict, Any
from fastapi import Request, Header
from .context import set_tenant
from .exceptions import TenantNotFoundError, InvalidTenantError, TenantInactiveError
from .validators import validate_schema_name
from .models import Tenant
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class TenantResolver:
    """
    Resolves tenant from various sources with fallback chain
    
    Resolution order:
    1. JWT payload (tenant claim)
    2. X-Tenant-ID header
    3. Subdomain (optional)
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def resolve(
        self, 
        request: Request, 
        jwt_payload: Optional[Dict[str, Any]] = None
    ) -> Tenant:
        """
        Resolve tenant from request
        
        Args:
            request: FastAPI request object
            jwt_payload: Decoded JWT payload (if authenticated)
            
        Returns:
            Tenant object
            
        Raises:
            TenantNotFoundError: If tenant cannot be resolved
            InvalidTenantError: If tenant identifier is invalid
            TenantInactiveError: If tenant is not active
        """
        tenant_identifier = None
        source = None
        
        # 1. Try JWT claim (most secure)
        if jwt_payload:
            tenant_identifier = jwt_payload.get("tenant")
            if tenant_identifier:
                source = "jwt"
                logger.info(f"Tenant resolved from JWT: {tenant_identifier}")
        
        # 2. Try X-Tenant-ID header (for internal tools/testing)
        if not tenant_identifier:
            tenant_identifier = request.headers.get("X-Tenant-ID")
            if tenant_identifier:
                source = "header"
                logger.info(f"Tenant resolved from header: {tenant_identifier}")
        
        # 3. Try subdomain (optional)
        if not tenant_identifier:
            tenant_identifier = self._extract_from_subdomain(request)
            if tenant_identifier:
                source = "subdomain"
                logger.info(f"Tenant resolved from subdomain: {tenant_identifier}")
        
        if not tenant_identifier:
            logger.error("No tenant identifier found in request")
            raise TenantNotFoundError("No tenant identifier provided")
        
        # Look up tenant in database
        tenant = Tenant.get_by_slug(self.db, tenant_identifier)
        
        if not tenant:
            logger.error(f"Tenant not found in database: {tenant_identifier}")
            raise TenantNotFoundError(tenant_identifier)
        
        # Check if tenant is active
        if not tenant.is_active():
            logger.warning(f"Attempted access to inactive tenant: {tenant_identifier}")
            raise TenantInactiveError(tenant_identifier)
        
        # Validate schema name (defense in depth)
        try:
            validate_schema_name(tenant.schema_name)
        except InvalidTenantError as e:
            logger.error(f"Invalid schema name in database: {tenant.schema_name}")
            raise
        
        # Set tenant in context
        set_tenant(tenant.schema_name, tenant.slug)
        
        logger.info(
            f"Tenant resolved successfully: slug={tenant.slug}, "
            f"schema={tenant.schema_name}, source={source}"
        )
        
        return tenant
    
    def _extract_from_subdomain(self, request: Request) -> Optional[str]:
        """
        Extract tenant from subdomain
        
        Example: acme.example.com -> acme
        """
        host = request.headers.get("host", "")
        
        # Skip localhost and IP addresses
        if "localhost" in host or host.replace(".", "").replace(":", "").isdigit():
            return None
        
        parts = host.split(".")
        
        # Need at least subdomain.domain.tld
        if len(parts) < 3:
            return None
        
        # First part is the subdomain
        subdomain = parts[0]
        
        # Skip www and api subdomains
        if subdomain in ("www", "api", "app"):
            return None
        
        return subdomain

