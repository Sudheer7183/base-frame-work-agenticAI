

"""API endpoints for tenant management with i18n support"""

from typing import List, Optional
from venv import logger
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session


from sqlalchemy import text
from sqlalchemy.orm import Session


from .service import TenantService
from .models import Tenant, TenantStatus
from .dependencies import get_db
from .exceptions import TenantError, InvalidTenantError, TenantNotFoundError

# Import security dependencies to protect these endpoints
from app.core.security import get_super_admin_user, TokenData

from app.core.realtime_translation import (
    translate_text_realtime,
    translate_dict_fields,
    should_translate
)
from app.tenancy.db import get_session
from app.services.user_service import UserService
from app.schemas.user import UserCreate
# ============================================================================
# i18n imports (UPDATED)
# ============================================================================
import sys
from pathlib import Path
i18n_path = Path(__file__).parent.parent.parent.parent / "i18n"
sys.path.insert(0, str(i18n_path))

from backend.core.i18n import (
    _,                          # Basic translation
    _n,                         # Pluralization
    pgettext,                   # Context-aware translation
    format_datetime,            # Date/time formatting
    format_number,              # Number formatting
    get_current_locale,         # Get active locale
    get_locale_info,            # Get locale information
    is_rtl                      # Check if RTL language
)



router = APIRouter(prefix="/platform/tenants", tags=["Tenant Management"])


# ============================================================================
# Pydantic Models (UPDATED with i18n descriptions)
# ============================================================================

class TenantCreate(BaseModel):
    """Request model for creating a tenant"""
    slug: str = Field(..., min_length=1, max_length=63, description="Unique tenant identifier")
    name: str = Field(..., min_length=1, max_length=255, description="Display name")
    schema_name: Optional[str] = Field(None, description="PostgreSQL schema name (auto-generated if not provided)")
    admin_email: Optional[EmailStr] = Field(None, description="Admin contact email")
    description: Optional[str] = Field(None, description="Tenant description")
    max_users: Optional[int] = Field(None, gt=0, description="Maximum users allowed")
    config: Optional[dict] = Field(default_factory=dict, description="Additional configuration")


class TenantUpdate(BaseModel):
    """Request model for updating a tenant"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    admin_email: Optional[EmailStr] = None
    max_users: Optional[int] = Field(None, gt=0)
    config: Optional[dict] = None

class TenantWithAdminCreate(TenantCreate):
    """Extends TenantCreate with admin user fields for one-shot tenant+user creation"""
    username:  str = Field(..., description="Login username for the admin account")
    full_name: str = Field(..., description="Display name for the admin account")
    password:  str = Field(..., min_length=8, description="Password for the admin account")

class TenantResponse(BaseModel):
    """Response model for tenant data (UPDATED with formatted fields)"""
    slug: str
    schema_name: str
    name: str
    description: Optional[str]
    status: str
    status_display: Optional[str] = None  # NEW: Translated status
    config: dict
    max_users: Optional[int]
    created_at: str
    created_at_formatted: Optional[str] = None  # NEW: Formatted date
    updated_at: str
    updated_at_formatted: Optional[str] = None  # NEW: Formatted date
    admin_email: Optional[str]
    
    class Config:
        from_attributes = True


class TenantListResponse(BaseModel):
    """Response model for tenant list (UPDATED with i18n metadata)"""
    message: str  # NEW: Translated message
    tenants: List[TenantResponse]
    total: int
    total_display: str  # NEW: Formatted total count
    limit: int
    offset: int
    locale: str  # NEW: Current locale
    direction: str  # NEW: Text direction (ltr/rtl)


# ============================================================================
# Helper Functions (NEW)
# ============================================================================

def translate_status(status: str) -> str:
    """Translate tenant status to current locale"""
    status_translations = {
        "active": _("Active"),
        "suspended": _("Suspended"),
        "pending": _("Pending"),
        "inactive": _("Inactive"),
        "archived": _("Archived")
    }
    return status_translations.get(status.lower(), status)




def format_tenant_response(tenant) -> dict:
    """Format tenant data with i18n fields"""
    from datetime import datetime
    
    tenant_dict = tenant.to_dict()
    tenant_dict['status_display'] = translate_status(tenant_dict['status'])
    
    # FIX: Handle both datetime objects and strings
    for date_field in ['created_at', 'updated_at']:
        if date_field in tenant_dict:
            date_value = tenant_dict[date_field]
            
            # Convert string to datetime if needed
            if isinstance(date_value, str):
                try:
                    date_value = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    pass
            
            # Format if it's a datetime object
            if isinstance(date_value, datetime):
                tenant_dict[f'{date_field}_formatted'] = format_datetime(
                    date_value, format='medium'
                )
    
    return tenant_dict

# ============================================================================
# API Endpoints (UPDATED with i18n)
# ============================================================================




@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantWithAdminCreate,
    current_admin: TokenData = Depends(get_super_admin_user),
):
    """
    Create a new tenant AND its first admin user.
    Requires Super Admin privileges.
 
    Why two sessions?
    -----------------
    TenantService.create_tenant() runs Alembic migrations as a subprocess.
    Sharing one SQLAlchemy session across that boundary corrupts its state
    and silently kills the process before the user can be created.
    Closing db1 before opening db2 gives each step a clean connection,
    exactly as the working CLI script does.
    """
 
    # ── STEP 1: Create Tenant ─────────────────────────────────────────────
    db1 = get_session()
    schema_name = None
    response_data = {}
 
    try:
        service = TenantService(db1)
        tenant = service.create_tenant(
            slug=tenant_data.slug,
            name=tenant_data.name,
            schema_name=tenant_data.schema_name,
            admin_email=tenant_data.admin_email,
            description=tenant_data.description,
            config=tenant_data.config,
            max_users=tenant_data.max_users,
        )
 
        schema_name = str(tenant.schema_name)           # read before session closes
        response_data = format_tenant_response(tenant)  # read before session closes
        response_data["message"] = _(
            "Tenant '{name}' created successfully"
        ).format(name=tenant_data.name)
 
    except InvalidTenantError as e:
        db1.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_("Invalid tenant data: {error}").format(error=str(e)),
        )
    except TenantError as e:
        db1.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("Failed to create tenant: {error}").format(error=str(e)),
        )
    finally:
        db1.close()   # CRITICAL: must close before opening db2
 
    # ── STEP 2: Create Admin User ─────────────────────────────────────────
    db2 = get_session()
    try:
        db2.execute(text(f'SET search_path TO "{schema_name}", public'))
 
        user = await UserService(db2).create_user(
            UserCreate(
                email=tenant_data.admin_email,
                username=tenant_data.username,
                full_name=tenant_data.full_name,
                password=tenant_data.password,
                roles=["ADMIN"],
                is_active=True,
            ),
            tenant_data.slug,
        )
        user_id = user.id   # store before commit

        db2.commit()

        response_data["admin_user_id"] = str(user_id)
 

 
    except Exception as e:
        db2.rollback()
        # Tenant is already committed — surface a clear error so the caller
        # knows the tenant exists and only the user needs to be created manually.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_(
                "Tenant '{slug}' was created but admin user setup failed: {error}. "
                "Please create the admin user manually."
            ).format(slug=tenant_data.slug, error=str(e)),
        )
    finally:
        db2.close()
 
    return TenantResponse(**response_data)
 

@router.get("/get-tenants", response_model=List[TenantResponse])
async def get_all_tenants(
    translate_content: bool = False,
    db: Session = Depends(get_db),
    current_admin: TokenData = Depends(get_super_admin_user)
):
    """
    Get all tenants from public schema
    """
    service = TenantService(db)

    try:
        tenants = service.get_all_tenants()

        response = []
        for tenant in tenants:
            tenant_dict = format_tenant_response(tenant)
            
            tenant_dict["max_users"] = service.get_user_count_for_schema(
                tenant.schema_name
            )

            # Optional translation
            # if translate_content and should_translate():
            #     tenant_dict = translate_tenant_fields(tenant_dict)

            response.append(TenantResponse(**tenant_dict))

        return response

    except Exception as e:
        logger.error(f"Error retrieving tenants: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving tenants: {str(e)}"
        )

@router.get("/{slug}", response_model=TenantResponse)
async def get_tenant(
    slug: str,
    translate_content: bool = True,  # ← ADD THIS PARAMETER
    db: Session = Depends(get_db),
    current_admin: TokenData = Depends(get_super_admin_user)
):
    """
    Get tenant by slug
    
    Args:
        slug: Tenant slug
        translate_content: Enable real-time translation of user content (default: True)
        db: Database session
        current_admin: Current admin user
        
    Returns:
        Tenant details with optional translated content
    """
    service = TenantService(db)
    
    try:
        tenant = service.get_tenant(slug)
        tenant_dict = format_tenant_response(tenant)
        
        # ========== ADD THIS BLOCK ==========
        # Real-time translation of user-generated content
        if translate_content and should_translate():

            
            if tenant_dict.get('description'):
                original = tenant_dict['description']

                
                translated = translate_text_realtime(original)

                
                tenant_dict['description'] = translated
        # ====================================
        
        return TenantResponse(**tenant_dict)
        
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("Tenant '{slug}' not found").format(slug=slug)
        )
    except Exception as e:
        logger.error(f"Error retrieving tenant {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("Error retrieving tenant: {error}").format(error=str(e))
        )



@router.get("")
async def list_tenants(
    translate_descriptions: bool = True,  # NEW
    status_filter: Optional[TenantStatus] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_admin: TokenData = Depends(get_super_admin_user)
):
    """List tenants with optional description translation"""
    service = TenantService(db)
    tenants = service.list_tenants(status=status_filter, limit=limit, offset=offset)
    
    formatted_tenants = []
    for tenant in tenants:
        tenant_dict = format_tenant_response(tenant)
        
        # Translate description if enabled and locale is not English
        if translate_descriptions and should_translate() and tenant.description:
            tenant_dict['description'] = translate_text_realtime(
                tenant.description
            )
        
        formatted_tenants.append(TenantResponse(**tenant_dict))
    
    total_count = len(tenants)
    current_locale = get_current_locale()
    
    return TenantListResponse(
        message=_n("Found {n} tenant", "Found {n} tenants", total_count).format(n=total_count),
        tenants=formatted_tenants,
        total=total_count,
        total_display=_n("{n} tenant", "{n} tenants", total_count).format(n=total_count),
        limit=limit,
        offset=offset,
        locale=current_locale,
        direction="rtl" if current_locale == "ar" else "ltr"
    )


@router.patch("/{slug}", response_model=TenantResponse)
def update_tenant(
    slug: str,
    update_data: TenantUpdate,
    db: Session = Depends(get_db),
    current_admin: TokenData = Depends(get_super_admin_user)
):
    """Update tenant metadata (Super Admin only)"""
    service = TenantService(db)
    
    try:
        tenant = service.update_tenant(
            slug=slug,
            name=update_data.name,
            description=update_data.description,
            admin_email=update_data.admin_email,
            config=update_data.config,
            max_users=update_data.max_users
        )
        
        response_data = format_tenant_response(tenant)
        response_data['message'] = _("Tenant '{name}' updated successfully").format(
            name=tenant.name
        )
        
        return TenantResponse(**response_data)
        
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("Tenant '{slug}' not found").format(slug=slug)
        )
    except TenantError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("Failed to update tenant: {error}").format(error=str(e))
        )


@router.post("/{slug}/suspend", response_model=TenantResponse)
def suspend_tenant(
    slug: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: TokenData = Depends(get_super_admin_user)
):
    """Suspend a tenant (Super Admin only)"""
    service = TenantService(db)
    
    try:
        tenant = service.suspend_tenant(slug, reason)
        response_data = format_tenant_response(tenant)
        
        if reason:
            response_data['message'] = _("Tenant '{name}' suspended. Reason: {reason}").format(
                name=tenant.name,
                reason=reason
            )
        else:
            response_data['message'] = _("Tenant '{name}' suspended").format(
                name=tenant.name
            )
        
        return TenantResponse(**response_data)
        
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("Tenant '{slug}' not found").format(slug=slug)
        )


@router.post("/{slug}/activate", response_model=TenantResponse)
def activate_tenant(
    slug: str,
    db: Session = Depends(get_db),
    current_admin: TokenData = Depends(get_super_admin_user)
):
    """Activate a suspended tenant (Super Admin only)"""
    service = TenantService(db)
    
    try:
        tenant = service.activate_tenant(slug)
        response_data = format_tenant_response(tenant)
        response_data['message'] = _("Tenant '{name}' activated successfully").format(
            name=tenant.name
        )
        
        return TenantResponse(**response_data)
        
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("Tenant '{slug}' not found").format(slug=slug)
        )


@router.delete("/{slug}")
def deprovision_tenant(
    slug: str,
    delete_schema: bool = False,
    backup_first: bool = True,
    db: Session = Depends(get_db),
    current_admin: TokenData = Depends(get_super_admin_user)
):
    """
    Deprovision a tenant (Super Admin only)
    
    WARNING: This is a destructive operation!
    """
    service = TenantService(db)
    
    try:
        service.deprovision_tenant(slug, delete_schema, backup_first)
        
        # Build detailed message
        if delete_schema:
            if backup_first:
                message = _("Tenant '{slug}' deprovisioned successfully. Schema deleted after backup.").format(
                    slug=slug
                )
            else:
                message = _("Tenant '{slug}' deprovisioned successfully. Schema deleted (no backup).").format(
                    slug=slug
                )
        else:
            message = _("Tenant '{slug}' deprovisioned successfully. Schema preserved.").format(
                slug=slug
            )
        
        return {
            "message": message,
            "slug": slug,
            "deleted_schema": delete_schema,
            "backup_created": backup_first if delete_schema else False
        }
        
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("Tenant '{slug}' not found").format(slug=slug)
        )
    except TenantError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_("Failed to deprovision tenant: {error}").format(error=str(e))
        )


# ============================================================================
# Additional i18n-aware Endpoints (NEW)
# ============================================================================

@router.get("/{slug}/summary")
def get_tenant_summary(
    slug: str,
    db: Session = Depends(get_db),
    current_admin: TokenData = Depends(get_super_admin_user)
):
    """
    Get a localized summary of tenant information
    """
    service = TenantService(db)
    
    try:
        tenant = service.get_tenant(slug)
        
        # Get locale info
        current_locale = get_current_locale()
        
        # Build summary with proper i18n
        summary = {
            "title": _("Tenant Summary"),
            "tenant_name": tenant.name,
            "status": {
                "value": tenant.status,
                "display": translate_status(tenant.status)
            },
            "created": {
                "value": tenant.created_at.isoformat(),
                "display": format_datetime(tenant.created_at, format='long')
            },
            "details": {
                "schema": tenant.schema_name,
                "admin_email": tenant.admin_email or _("Not set"),
                "max_users": tenant.max_users or _("Unlimited")
            },
            "locale_info": {
                "locale": current_locale,
                "direction": "rtl" if is_rtl(current_locale) else "ltr"
            }
        }
        
        return summary
        
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("Tenant '{slug}' not found").format(slug=slug)
        )


@router.get("/{slug}/stats")
def get_tenant_stats(
    slug: str,
    db: Session = Depends(get_db),
    current_admin: TokenData = Depends(get_super_admin_user)
):
    """
    Get tenant statistics with proper number formatting
    """
    service = TenantService(db)
    
    try:
        tenant = service.get_tenant(slug)
        
        # Example stats (replace with real data from your service)
        stats = {
            "users": 42,
            "agents": 15,
            "workflows": 8,
            "tasks_completed": 1234,
            "storage_used_mb": 567.89
        }
        
        # Format with locale-aware numbers
        formatted_stats = {
            "title": _("Statistics for {name}").format(name=tenant.name),
            "data": {
                "users": {
                    "label": _("Users"),
                    "value": stats["users"],
                    "display": format_number(stats["users"])
                },
                "agents": {
                    "label": _("Agents"),
                    "value": stats["agents"],
                    "display": _n("{n} agent", "{n} agents", stats["agents"]).format(
                        n=format_number(stats["agents"])
                    )
                },
                "workflows": {
                    "label": _("Workflows"),
                    "value": stats["workflows"],
                    "display": format_number(stats["workflows"])
                },
                "tasks_completed": {
                    "label": _("Tasks Completed"),
                    "value": stats["tasks_completed"],
                    "display": format_number(stats["tasks_completed"])
                },
                "storage_used": {
                    "label": _("Storage Used"),
                    "value": stats["storage_used_mb"],
                    "display": _("{size} MB").format(
                        size=format_number(stats["storage_used_mb"])
                    )
                }
            }
        }
        
        return formatted_stats
        
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_("Tenant '{slug}' not found").format(slug=slug)
        )