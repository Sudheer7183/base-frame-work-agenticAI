# FastAPI Multi-Tenancy Package
# Schema-based PostgreSQL multitenancy with enterprise features
"""

from .context import get_tenant, set_tenant, clear_tenant
from .exceptions import (
    TenantError,
    TenantNotFoundError,
    InvalidTenantError,
    TenantProvisionError,
)
from .middleware import TenantMiddleware
from .models import Tenant, TenantStatus
from .resolver import TenantResolver
from .service import TenantService
from .dependencies import get_current_tenant, require_tenant

__version__ = "1.0.0"
__all__ = [
    "get_tenant", "set_tenant", "clear_tenant",
    "TenantError", "TenantNotFoundError", "InvalidTenantError",
    "TenantProvisionError", "TenantMiddleware", "Tenant",
    "TenantStatus", "TenantResolver", "TenantService",
    "get_current_tenant", "require_tenant",
]


# """
# FastAPI Multi-Tenancy Package
# Schema-based PostgreSQL multitenancy with enterprise features
# """

# from .context import get_tenant, set_tenant, clear_tenant
# from .exceptions import (
#     TenantError,
#     TenantNotFoundError,
#     InvalidTenantError,
#     TenantProvisionError,
# )
# from .middleware import TenantMiddleware
# from .models import Tenant, TenantStatus
# from .resolver import TenantResolver
# from .service import TenantService
# from .dependencies import get_current_tenant, require_tenant

# __version__ = "1.0.0"
# __all__ = [
#     "get_tenant",
#     "set_tenant",
#     "clear_tenant",
#     "TenantError",
#     "TenantNotFoundError",
#     "InvalidTenantError",
#     "TenantProvisionError",
#     "TenantMiddleware",
#     "Tenant",
#     "TenantStatus",
#     "TenantResolver",
#     "TenantService",
#     "get_current_tenant",
#     "require_tenant",
# ]
