"""
FastAPI Routes for Database Backup Management
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from .backup_service import (
    DatabaseBackupService,
    BackupMetadata,
    BackupType,
    BackupStatus
)
from app.core.config import settings

router = APIRouter(prefix="/backups", tags=["backups"])


# ============================================================================
# Pydantic Models
# ============================================================================

class BackupCreateRequest(BaseModel):
    """Request to create a backup"""
    backup_type: BackupType = Field(..., description="Type of backup")
    schema_name: Optional[str] = Field(None, description="Schema name for tenant backups")


class BackupResponse(BaseModel):
    """Backup response"""
    backup_id: str
    backup_type: str
    timestamp: datetime
    status: str
    schemas: List[str]
    size_mb: float
    file_path: str
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None
    
    @classmethod
    def from_metadata(cls, metadata: BackupMetadata) -> "BackupResponse":
        return cls(
            backup_id=metadata.backup_id,
            backup_type=metadata.backup_type.value,
            timestamp=metadata.timestamp,
            status=metadata.status.value,
            schemas=metadata.schemas,
            size_mb=metadata.size_bytes / 1024 / 1024,
            file_path=metadata.file_path,
            error_message=metadata.error_message,
            duration_seconds=metadata.duration_seconds
        )


class BackupRestoreRequest(BaseModel):
    """Request to restore a backup"""
    backup_id: str = Field(..., description="Backup ID to restore")
    target_schema: Optional[str] = Field(None, description="Target schema (for tenant backups)")
    clean: bool = Field(False, description="Drop existing objects first")


class BackupStatsResponse(BaseModel):
    """Backup statistics"""
    total_backups: int
    completed_backups: int
    failed_backups: int
    total_size_mb: float
    oldest_backup: Optional[datetime]
    newest_backup: Optional[datetime]
    retention_days: int
    max_backups: int


# ============================================================================
# Dependency Injection
# ============================================================================

def get_backup_service() -> DatabaseBackupService:
    """Get backup service instance"""
    return DatabaseBackupService(
        db_host=settings.DB_HOST,
        db_port=settings.DB_PORT,
        db_name=settings.DB_NAME,
        db_user=settings.DB_USER,
        db_password=settings.DB_PASSWORD,
        backup_dir=getattr(settings, 'BACKUP_DIR', '/backups'),
        retention_days=getattr(settings, 'BACKUP_RETENTION_DAYS', 30),
        max_backups=getattr(settings, 'BACKUP_MAX_COUNT', 50)
    )


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ============================================================================
# Routes
# ============================================================================

@router.post("/create", response_model=BackupResponse, status_code=201)
async def create_backup(
    request: BackupCreateRequest,
    background_tasks: BackgroundTasks,
    backup_service: DatabaseBackupService = Depends(get_backup_service),
    current_user: User = Depends(require_admin)
):
    """
    Create a database backup
    
    - **Full backup**: Backs up all schemas
    - **Tenant backup**: Backs up single tenant schema
    - **Public backup**: Backs up only public schema (tenant registry)
    
    Requires admin privileges.
    """
    try:
        if request.backup_type == BackupType.FULL:
            metadata = backup_service.create_full_backup()
            
        elif request.backup_type == BackupType.TENANT:
            if not request.schema_name:
                raise HTTPException(
                    status_code=400,
                    detail="schema_name required for tenant backups"
                )
            metadata = backup_service.create_tenant_backup(request.schema_name)
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported backup type: {request.backup_type}"
            )
        
        return BackupResponse.from_metadata(metadata)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")


@router.get("/list", response_model=List[BackupResponse])
async def list_backups(
    backup_type: Optional[BackupType] = Query(None, description="Filter by backup type"),
    schema: Optional[str] = Query(None, description="Filter by schema name"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
    backup_service: DatabaseBackupService = Depends(get_backup_service),
    current_user: User = Depends(require_admin)
):
    """
    List available backups
    
    Supports filtering by:
    - Backup type (full, tenant, public)
    - Schema name
    - Limit
    
    Requires admin privileges.
    """
    try:
        backups = backup_service.list_backups(
            backup_type=backup_type,
            schema=schema,
            limit=limit
        )
        
        return [BackupResponse.from_metadata(b) for b in backups]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")


@router.get("/stats", response_model=BackupStatsResponse)
async def get_backup_stats(
    backup_service: DatabaseBackupService = Depends(get_backup_service),
    current_user: User = Depends(require_admin)
):
    """
    Get backup statistics
    
    Returns:
    - Total number of backups
    - Completed/failed counts
    - Total storage size
    - Oldest/newest backup dates
    - Retention policy
    
    Requires admin privileges.
    """
    try:
        stats = backup_service.get_backup_stats()
        
        return BackupStatsResponse(
            total_backups=stats['total_backups'],
            completed_backups=stats['completed_backups'],
            failed_backups=stats['failed_backups'],
            total_size_mb=stats['total_size_mb'],
            oldest_backup=datetime.fromisoformat(stats['oldest_backup']) if stats['oldest_backup'] else None,
            newest_backup=datetime.fromisoformat(stats['newest_backup']) if stats['newest_backup'] else None,
            retention_days=stats['retention_days'],
            max_backups=stats['max_backups']
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/{backup_id}", response_model=BackupResponse)
async def get_backup(
    backup_id: str,
    backup_service: DatabaseBackupService = Depends(get_backup_service),
    current_user: User = Depends(require_admin)
):
    """
    Get backup details by ID
    
    Requires admin privileges.
    """
    metadata = backup_service._load_metadata(backup_id)
    
    if not metadata:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    return BackupResponse.from_metadata(metadata)


@router.post("/restore", status_code=202)
async def restore_backup(
    request: BackupRestoreRequest,
    background_tasks: BackgroundTasks,
    backup_service: DatabaseBackupService = Depends(get_backup_service),
    current_user: User = Depends(require_admin)
):
    """
    Restore database from backup
    
    **WARNING**: This is a destructive operation!
    
    Options:
    - **clean**: Drop existing objects before restore
    - **target_schema**: Restore to different schema (tenant backups only)
    
    Restore runs as a background task.
    
    Requires admin privileges.
    """
    def _restore():
        try:
            backup_service.restore_backup(
                backup_id=request.backup_id,
                target_schema=request.target_schema,
                clean=request.clean
            )
        except Exception as e:
            # Log error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Restore failed: {e}")
    
    # Run restore in background
    background_tasks.add_task(_restore)
    
    return {
        "message": "Restore initiated",
        "backup_id": request.backup_id,
        "status": "in_progress"
    }


@router.post("/{backup_id}/verify")
async def verify_backup(
    backup_id: str,
    backup_service: DatabaseBackupService = Depends(get_backup_service),
    current_user: User = Depends(require_admin)
):
    """
    Verify backup integrity
    
    Checks:
    - File exists
    - File size matches metadata
    - Backup can be read by pg_restore
    
    Requires admin privileges.
    """
    try:
        is_valid = backup_service.verify_backup(backup_id)
        
        return {
            "backup_id": backup_id,
            "valid": is_valid,
            "verified_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.delete("/{backup_id}", status_code=204)
async def delete_backup(
    backup_id: str,
    backup_service: DatabaseBackupService = Depends(get_backup_service),
    current_user: User = Depends(require_admin)
):
    """
    Delete a backup
    
    **WARNING**: This cannot be undone!
    
    Requires admin privileges.
    """
    try:
        backup_service.delete_backup(backup_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")
