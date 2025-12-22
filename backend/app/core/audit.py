"""
Audit Logging System - P1 Fix
Comprehensive audit trail for all system actions
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Index
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import Base

logger = logging.getLogger(__name__)


class AuditAction(str, Enum):
    """Standard audit actions"""
    # Agent actions
    AGENT_CREATED = "agent.created"
    AGENT_UPDATED = "agent.updated"
    AGENT_DELETED = "agent.deleted"
    AGENT_EXECUTION_STARTED = "agent.execution.started"
    AGENT_EXECUTION_COMPLETED = "agent.execution.completed"
    AGENT_EXECUTION_FAILED = "agent.execution.failed"
    AGENT_EXECUTION_CANCELLED = "agent.execution.cancelled"
    
    # HITL actions
    HITL_CREATED = "hitl.created"
    HITL_APPROVED = "hitl.approved"
    HITL_REJECTED = "hitl.rejected"
    HITL_ESCALATED = "hitl.escalated"
    
    # User actions
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_PASSWORD_CHANGED = "user.password_changed"
    
    # Tenant actions
    TENANT_CREATED = "tenant.created"
    TENANT_UPDATED = "tenant.updated"
    TENANT_SUSPENDED = "tenant.suspended"
    TENANT_ACTIVATED = "tenant.activated"
    TENANT_DELETED = "tenant.deleted"
    
    # Config actions
    CONFIG_UPDATED = "config.updated"
    
    # System actions
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"


class AuditLog(Base):
    """Audit log database model"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # When & Who
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    user_email = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    
    # What
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True, index=True)
    resource_id = Column(String(255), nullable=True, index=True)
    
    # Details
    details = Column(JSON, nullable=True)
    
    # Tenant context (for multi-tenant)
    tenant_id = Column(Integer, nullable=True, index=True)
    
    # Status
    status = Column(String(20), nullable=False, default="success", index=True)
    error_message = Column(Text, nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_audit_user_action', 'user_id', 'action'),
        Index('idx_audit_resource', 'resource_type', 'resource_id'),
        Index('idx_audit_timestamp_action', 'timestamp', 'action'),
        Index('idx_audit_tenant_timestamp', 'tenant_id', 'timestamp'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "ip_address": self.ip_address,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "tenant_id": self.tenant_id,
            "status": self.status,
            "error_message": self.error_message
        }


class AuditLogEntry(BaseModel):
    """Audit log entry schema"""
    id: int
    timestamp: datetime
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    tenant_id: Optional[int] = None
    status: str = "success"
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class AuditLogger:
    """
    Audit logging service
    
    Features:
    - Comprehensive action tracking
    - User context capture
    - Resource tracking
    - Async and sync logging
    - Query and reporting capabilities
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def log(
        self,
        action: str,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        Log an audit event (synchronous)
        
        Args:
            action: Action performed
            user_id: User ID
            user_email: User email
            ip_address: Client IP address
            user_agent: User agent string
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            details: Additional details
            tenant_id: Tenant ID (for multi-tenant)
            status: Status (success/failure)
            error_message: Error message if failed
            
        Returns:
            Created audit log entry
        """
        log_entry = AuditLog(
            timestamp=datetime.utcnow(),
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            tenant_id=tenant_id,
            status=status,
            error_message=error_message
        )
        
        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        
        logger.debug(f"Audit log created: {action} by user {user_id}")
        
        return log_entry
    
    async def log_async(
        self,
        action: str,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        Log an audit event (asynchronous)
        
        Same parameters as log(), but runs asynchronously
        """
        return await asyncio.to_thread(
            self.log,
            action=action,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            tenant_id=tenant_id,
            status=status,
            error_message=error_message
        )
    
    def log_from_request(
        self,
        action: str,
        request: Any,  # FastAPI Request
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> AuditLog:
        """
        Log an audit event from FastAPI request
        
        Automatically extracts user context from request
        """
        ip_address = request.client.host if hasattr(request, 'client') else None
        user_agent = request.headers.get("user-agent") if hasattr(request, 'headers') else None
        
        return self.log(
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            status=status,
            error_message=error_message
        )
    
    def query_logs(
        self,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        tenant_id: Optional[int] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[AuditLog]:
        """
        Query audit logs with filters
        
        Args:
            user_id: Filter by user
            action: Filter by action
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            tenant_id: Filter by tenant
            status: Filter by status
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum results
            offset: Result offset
            
        Returns:
            List of audit log entries
        """
        query = self.db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)
        if tenant_id:
            query = query.filter(AuditLog.tenant_id == tenant_id)
        if status:
            query = query.filter(AuditLog.status == status)
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        query = query.order_by(AuditLog.timestamp.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    def get_user_activity(
        self,
        user_id: int,
        limit: int = 50
    ) -> list[AuditLog]:
        """Get recent activity for a user"""
        return self.query_logs(user_id=user_id, limit=limit)
    
    def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50
    ) -> list[AuditLog]:
        """Get history for a specific resource"""
        return self.query_logs(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit
        )


# Audit logging middleware for FastAPI
class AuditMiddleware:
    """
    FastAPI middleware for automatic audit logging
    """
    
    def __init__(self, audit_logger: AuditLogger):
        self.audit_logger = audit_logger
    
    async def __call__(self, request, call_next):
        """Process request and log audit trail"""
        # Skip audit for health checks and metrics
        if request.url.path in ["/health", "/metrics", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        start_time = datetime.utcnow()
        
        try:
            response = await call_next(request)
            
            # Log successful request
            if response.status_code < 400:
                await self.audit_logger.log_async(
                    action=f"api.{request.method.lower()}",
                    ip_address=request.client.host if hasattr(request, 'client') else None,
                    user_agent=request.headers.get("user-agent"),
                    details={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000)
                    },
                    status="success"
                )
            
            return response
            
        except Exception as e:
            # Log failed request
            await self.audit_logger.log_async(
                action=f"api.{request.method.lower()}",
                ip_address=request.client.host if hasattr(request, 'client') else None,
                user_agent=request.headers.get("user-agent"),
                details={
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(e).__name__
                },
                status="failure",
                error_message=str(e)
            )
            raise
