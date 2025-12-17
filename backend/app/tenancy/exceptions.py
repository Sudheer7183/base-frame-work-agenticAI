"""Custom exceptions for multi-tenancy"""

class TenantError(Exception):
    """Base exception for all tenant-related errors"""
    pass


class TenantNotFoundError(TenantError):
    """Raised when tenant cannot be found"""
    def __init__(self, identifier: str = None):
        msg = "Tenant not found"
        if identifier:
            msg = f"Tenant not found: {identifier}"
        super().__init__(msg)


class InvalidTenantError(TenantError):
    """Raised when tenant identifier is invalid"""
    def __init__(self, reason: str = None):
        msg = "Invalid tenant identifier"
        if reason:
            msg = f"Invalid tenant: {reason}"
        super().__init__(msg)


class TenantProvisionError(TenantError):
    """Raised when tenant provisioning fails"""
    pass


class TenantDeprovisionError(TenantError):
    """Raised when tenant deprovisioning fails"""
    pass


class TenantInactiveError(TenantError):
    """Raised when attempting to access inactive tenant"""
    def __init__(self, slug: str):
        super().__init__(f"Tenant is inactive: {slug}")
