"""Admin API routes"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.tenancy.models import Tenant, TenantStatus
from app.tenancy.service import TenantService
from app.tenancy.dependencies import get_db
from .auth import admin_required, super_admin_required, AdminUser

router = APIRouter(prefix="/admin", tags=["Admin"])


# ============================================================================
# Response Models
# ============================================================================

class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_tenants: int
    active_tenants: int
    suspended_tenants: int
    provisioning_tenants: int
    total_max_users: int
    tenants_created_this_month: int
    tenants_created_this_week: int


class TenantUsageStats(BaseModel):
    """Tenant usage statistics"""
    slug: str
    name: str
    schema_name: str
    status: str
    user_count: int
    max_users: Optional[int]
    storage_mb: float
    api_calls_today: int
    last_activity: Optional[datetime]


class AuditLogEntry(BaseModel):
    """Audit log entry"""
    id: str
    timestamp: datetime
    actor_id: str
    actor_email: str
    action: str
    target_type: str
    target_id: str
    details: dict
    ip_address: Optional[str]


# ============================================================================
# Dashboard & Statistics
# ============================================================================

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(admin_required)
):
    """Get dashboard statistics"""
    
    now = datetime.utcnow()
    month_ago = now - timedelta(days=30)
    week_ago = now - timedelta(days=7)
    
    total = db.query(Tenant).count()
    active = db.query(Tenant).filter(Tenant.status == TenantStatus.ACTIVE.value).count()
    suspended = db.query(Tenant).filter(Tenant.status == TenantStatus.SUSPENDED.value).count()
    provisioning = db.query(Tenant).filter(Tenant.status == TenantStatus.PROVISIONING.value).count()
    
    total_users = db.query(func.sum(Tenant.max_users)).scalar() or 0
    
    created_month = db.query(Tenant).filter(Tenant.created_at >= month_ago).count()
    created_week = db.query(Tenant).filter(Tenant.created_at >= week_ago).count()
    
    return DashboardStats(
        total_tenants=total,
        active_tenants=active,
        suspended_tenants=suspended,
        provisioning_tenants=provisioning,
        total_max_users=int(total_users),
        tenants_created_this_month=created_month,
        tenants_created_this_week=created_week
    )


@router.get("/tenants/{slug}/usage", response_model=TenantUsageStats)
async def get_tenant_usage(
    slug: str,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(admin_required)
):
    """Get detailed usage statistics for a tenant"""
    
    service = TenantService(db)
    tenant = service.get_tenant(slug)
    
    # In a real implementation, you would query actual usage metrics
    # This is a mock implementation
    return TenantUsageStats(
        slug=tenant.slug,
        name=tenant.name,
        schema_name=tenant.schema_name,
        status=tenant.status,
        user_count=42,  # Mock data
        max_users=tenant.max_users,
        storage_mb=1234.56,  # Mock data
        api_calls_today=5678,  # Mock data
        last_activity=datetime.utcnow()
    )


# ============================================================================
# Bulk Operations
# ============================================================================

class BulkActionRequest(BaseModel):
    """Request for bulk actions"""
    tenant_slugs: List[str]
    action: str  # 'suspend', 'activate', 'delete'
    reason: Optional[str] = None


class BulkActionResult(BaseModel):
    """Result of bulk action"""
    success: List[str]
    failed: List[dict]
    total: int


@router.post("/tenants/bulk-action", response_model=BulkActionResult)
async def bulk_tenant_action(
    request: BulkActionRequest,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(super_admin_required)
):
    """Perform bulk actions on tenants (super admin only)"""
    
    service = TenantService(db)
    success = []
    failed = []
    
    for slug in request.tenant_slugs:
        try:
            if request.action == "suspend":
                service.suspend_tenant(slug, request.reason)
                success.append(slug)
            elif request.action == "activate":
                service.activate_tenant(slug)
                success.append(slug)
            elif request.action == "delete":
                service.deprovision_tenant(slug, delete_schema=False)
                success.append(slug)
            else:
                failed.append({"slug": slug, "error": "Invalid action"})
        except Exception as e:
            failed.append({"slug": slug, "error": str(e)})
    
    return BulkActionResult(
        success=success,
        failed=failed,
        total=len(request.tenant_slugs)
    )


# ============================================================================
# Audit Logs
# ============================================================================

@router.get("/audit-logs", response_model=List[AuditLogEntry])
async def get_audit_logs(
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    tenant_slug: Optional[str] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(admin_required)
):
    """Get audit logs"""
    
    # In a real implementation, you would query an audit_logs table
    # This is a mock implementation
    mock_logs = [
        AuditLogEntry(
            id="log_1",
            timestamp=datetime.utcnow(),
            actor_id="admin_123",
            actor_email="admin@example.com",
            action="tenant.created",
            target_type="tenant",
            target_id="acme",
            details={"name": "Acme Corp"},
            ip_address="192.168.1.1"
        ),
        AuditLogEntry(
            id="log_2",
            timestamp=datetime.utcnow() - timedelta(hours=1),
            actor_id="admin_123",
            actor_email="admin@example.com",
            action="tenant.suspended",
            target_type="tenant",
            target_id="demo",
            details={"reason": "Payment overdue"},
            ip_address="192.168.1.1"
        )
    ]
    
    return mock_logs


# ============================================================================
# System Health
# ============================================================================

class SystemHealth(BaseModel):
    """System health status"""
    status: str
    database: str
    total_schemas: int
    disk_usage_percent: float
    memory_usage_percent: float
    active_connections: int
    last_backup: Optional[datetime]


@router.get("/system/health", response_model=SystemHealth)
async def get_system_health(
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(admin_required)
):
    """Get system health metrics"""
    
    # Count total schemas
    from sqlalchemy import text
    result = db.execute(text("""
        SELECT count(*) 
        FROM information_schema.schemata 
        WHERE schema_name LIKE 'tenant_%'
    """))
    schema_count = result.scalar()
    
    # Mock other metrics (in production, you'd query actual system stats)
    return SystemHealth(
        status="healthy",
        database="connected",
        total_schemas=schema_count,
        disk_usage_percent=45.2,
        memory_usage_percent=62.8,
        active_connections=15,
        last_backup=datetime.utcnow() - timedelta(hours=2)
    )


# ============================================================================
# Tenant Search & Advanced Filters
# ============================================================================

class TenantSearchRequest(BaseModel):
    """Advanced tenant search"""
    query: Optional[str] = None
    status: Optional[List[str]] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    has_email: Optional[bool] = None
    min_users: Optional[int] = None
    max_users: Optional[int] = None


@router.post("/tenants/search")
async def search_tenants(
    search: TenantSearchRequest,
    limit: int = Query(50, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(admin_required)
):
    """Advanced tenant search with filters"""
    
    query = db.query(Tenant)
    
    # Apply filters
    if search.query:
        query = query.filter(
            (Tenant.name.ilike(f"%{search.query}%")) |
            (Tenant.slug.ilike(f"%{search.query}%"))
        )
    
    if search.status:
        query = query.filter(Tenant.status.in_(search.status))
    
    if search.created_after:
        query = query.filter(Tenant.created_at >= search.created_after)
    
    if search.created_before:
        query = query.filter(Tenant.created_at <= search.created_before)
    
    if search.has_email is not None:
        if search.has_email:
            query = query.filter(Tenant.admin_email.isnot(None))
        else:
            query = query.filter(Tenant.admin_email.is_(None))
    
    if search.min_users is not None:
        query = query.filter(Tenant.max_users >= search.min_users)
    
    if search.max_users is not None:
        query = query.filter(Tenant.max_users <= search.max_users)
    
    # Get results
    tenants = query.offset(offset).limit(limit).all()
    total = query.count()
    
    return {
        "tenants": [t.to_dict() for t in tenants],
        "total": total,
        "limit": limit,
        "offset": offset
    }


# ============================================================================
# Configuration Management
# ============================================================================

class SystemConfig(BaseModel):
    """System configuration"""
    max_tenants: int
    default_max_users: int
    allow_self_signup: bool
    require_email_verification: bool
    backup_enabled: bool
    backup_frequency_hours: int


@router.get("/config", response_model=SystemConfig)
async def get_system_config(
    admin: AdminUser = Depends(admin_required)
):
    """Get system configuration"""
    
    # In production, load from database or config file
    return SystemConfig(
        max_tenants=1000,
        default_max_users=100,
        allow_self_signup=False,
        require_email_verification=True,
        backup_enabled=True,
        backup_frequency_hours=24
    )


@router.put("/config", response_model=SystemConfig)
async def update_system_config(
    config: SystemConfig,
    admin: AdminUser = Depends(super_admin_required)
):
    """Update system configuration (super admin only)"""
    
    # In production, save to database or config file
    return config


# ============================================================================
# Export & Reporting
# ============================================================================

@router.get("/reports/tenants/csv")
async def export_tenants_csv(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(admin_required)
):
    """Export tenants to CSV"""
    
    import csv
    from io import StringIO
    from fastapi.responses import StreamingResponse
    
    query = db.query(Tenant)
    if status:
        query = query.filter(Tenant.status == status)
    
    tenants = query.all()
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Slug', 'Name', 'Schema', 'Status', 'Admin Email',
        'Max Users', 'Created At', 'Updated At'
    ])
    
    # Data
    for tenant in tenants:
        writer.writerow([
            tenant.slug,
            tenant.name,
            tenant.schema_name,
            tenant.status,
            tenant.admin_email or '',
            tenant.max_users or '',
            tenant.created_at.isoformat(),
            tenant.updated_at.isoformat()
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=tenants_{datetime.utcnow().date()}.csv"
        }
    )


# ============================================================================
# Maintenance Operations
# ============================================================================

class MaintenanceTask(BaseModel):
    """Maintenance task"""
    task_id: str
    task_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    result: Optional[dict]


@router.post("/maintenance/vacuum")
async def run_vacuum(
    admin: AdminUser = Depends(super_admin_required)
):
    """Run database vacuum (super admin only)"""
    
    # In production, this would schedule a background task
    return {
        "task_id": "vacuum_123",
        "message": "Vacuum operation scheduled",
        "status": "scheduled"
    }


@router.post("/maintenance/cleanup-inactive")
async def cleanup_inactive_tenants(
    days_inactive: int = Query(90, ge=30),
    admin: AdminUser = Depends(super_admin_required)
):
    """Clean up inactive tenants (super admin only)"""
    
    # In production, this would schedule a background task
    return {
        "task_id": "cleanup_123",
        "message": f"Cleanup scheduled for tenants inactive > {days_inactive} days",
        "status": "scheduled"
    }


@router.get("/maintenance/tasks", response_model=List[MaintenanceTask])
async def get_maintenance_tasks(
    admin: AdminUser = Depends(admin_required)
):
    """Get maintenance task history"""
    
    # Mock data
    return [
        MaintenanceTask(
            task_id="vacuum_123",
            task_type="vacuum",
            status="completed",
            started_at=datetime.utcnow() - timedelta(hours=2),
            completed_at=datetime.utcnow() - timedelta(hours=1, minutes=45),
            result={"schemas_processed": 15, "space_freed_mb": 234}
        )
    ]