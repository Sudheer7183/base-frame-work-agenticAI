"""API endpoints for tenant management"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session
from .service import TenantService
from .models import Tenant, TenantStatus
from .dependencies import get_db
from .exceptions import TenantError, InvalidTenantError, TenantNotFoundError

router = APIRouter(prefix="/platform/tenants", tags=["Tenant Management"])


# ============================================================================
# Pydantic Models
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


class TenantResponse(BaseModel):
    """Response model for tenant data"""
    slug: str
    schema_name: str
    name: str
    description: Optional[str]
    status: str
    config: dict
    max_users: Optional[int]
    created_at: str
    updated_at: str
    admin_email: Optional[str]
    
    class Config:
        from_attributes = True


class TenantListResponse(BaseModel):
    """Response model for tenant list"""
    tenants: List[TenantResponse]
    total: int
    limit: int
    offset: int


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(
    tenant_data: TenantCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new tenant
    
    This will:
    1. Create a PostgreSQL schema
    2. Run migrations
    3. Register the tenant
    """
    service = TenantService(db)
    
    try:
        tenant = service.create_tenant(
            slug=tenant_data.slug,
            name=tenant_data.name,
            schema_name=tenant_data.schema_name,
            admin_email=tenant_data.admin_email,
            description=tenant_data.description,
            config=tenant_data.config,
            max_users=tenant_data.max_users
        )
        
        return TenantResponse(**tenant.to_dict())
        
    except InvalidTenantError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except TenantError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{slug}", response_model=TenantResponse)
def get_tenant(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get tenant by slug"""
    service = TenantService(db)
    
    try:
        tenant = service.get_tenant(slug)
        return TenantResponse(**tenant.to_dict())
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("", response_model=TenantListResponse)
def list_tenants(
    status_filter: Optional[TenantStatus] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List all tenants"""
    service = TenantService(db)
    
    tenants = service.list_tenants(status=status_filter, limit=limit, offset=offset)
    
    return TenantListResponse(
        tenants=[TenantResponse(**t.to_dict()) for t in tenants],
        total=len(tenants),
        limit=limit,
        offset=offset
    )


@router.patch("/{slug}", response_model=TenantResponse)
def update_tenant(
    slug: str,
    update_data: TenantUpdate,
    db: Session = Depends(get_db)
):
    """Update tenant metadata"""
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
        
        return TenantResponse(**tenant.to_dict())
        
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{slug}/suspend", response_model=TenantResponse)
def suspend_tenant(
    slug: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Suspend a tenant"""
    service = TenantService(db)
    
    try:
        tenant = service.suspend_tenant(slug, reason)
        return TenantResponse(**tenant.to_dict())
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{slug}/activate", response_model=TenantResponse)
def activate_tenant(
    slug: str,
    db: Session = Depends(get_db)
):
    """Activate a suspended tenant"""
    service = TenantService(db)
    
    try:
        tenant = service.activate_tenant(slug)
        return TenantResponse(**tenant.to_dict())
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{slug}")
def deprovision_tenant(
    slug: str,
    delete_schema: bool = False,
    backup_first: bool = True,
    db: Session = Depends(get_db)
):
    """
    Deprovision a tenant
    
    WARNING: This is a destructive operation!
    """
    service = TenantService(db)
    
    try:
        service.deprovision_tenant(slug, delete_schema, backup_first)
        return {"message": f"Tenant {slug} deprovisioned successfully"}
    except TenantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except TenantError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )