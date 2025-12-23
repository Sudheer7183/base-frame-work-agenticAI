"""Database models for tenant management"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import (
    Column, String, DateTime, Boolean, Text, JSON, Integer
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

Base = declarative_base()


class TenantStatus(str, Enum):
    """Tenant status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROVISIONING = "provisioning"
    SUSPENDED = "suspended"
    DEPROVISIONING = "deprovisioning"


class Tenant(Base):
    """
    Tenant registry stored in public schema
    
    This table tracks all tenants and their schemas
    """
    __tablename__ = "tenants"
    __table_args__ = {"schema": "public"}
    #tenant related data for users
    # users = relationship("UserTenant", backref="tenant", cascade="all, delete")
    # Primary identifiers
    slug = Column(String(100), primary_key=True, index=True)
    schema_name = Column(String(100), unique=True, nullable=False, index=True)
    
    # Metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default=TenantStatus.ACTIVE.value)
    
    # Configuration
    config = Column(JSON, default={})
    max_users = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    suspended_at = Column(DateTime, nullable=True)
    
    # Contact info
    admin_email = Column(String(255), nullable=True)
    
    @classmethod
    def get_by_slug(cls, db: Session, slug: str) -> Optional["Tenant"]:
        """Get tenant by slug"""
        return db.query(cls).filter(cls.slug == slug).first()
    
    @classmethod
    def get_by_schema(cls, db: Session, schema: str) -> Optional["Tenant"]:
        """Get tenant by schema name"""
        return db.query(cls).filter(cls.schema_name == schema).first()
    
    @classmethod
    def get_all_active(cls, db: Session) -> List["Tenant"]:
        """Get all active tenants"""
        return db.query(cls).filter(cls.status == TenantStatus.ACTIVE.value).all()
    
    @classmethod
    def exists(cls, db: Session, slug: str = None, schema: str = None) -> bool:
        """Check if tenant exists by slug or schema"""
        query = db.query(cls)
        if slug:
            query = query.filter(cls.slug == slug)
        if schema:
            query = query.filter(cls.schema_name == schema)
        return query.first() is not None
    
    def is_active(self) -> bool:
        """Check if tenant is active"""
        return self.status == TenantStatus.ACTIVE.value
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "slug": self.slug,
            "schema_name": self.schema_name,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "config": self.config,
            "max_users": self.max_users,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "admin_email": self.admin_email,
        }

