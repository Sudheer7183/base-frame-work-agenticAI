"""Enhanced User model with multi-tenant support"""

from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, List
from .base import Base


class User(Base):
    """
    User model with multi-tenant support
    Each tenant schema has its own users table
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication
    keycloak_id = Column(String(255), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True, index=True)
    hashed_password = Column(String(255), nullable=True)  # For non-Keycloak auth
    
    # Profile
    full_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    phone = Column(String(50), nullable=True)
    
    # Authorization
    roles = Column(JSON, nullable=True, default=list)
    permissions = Column(JSON, nullable=True, default=list)
    
    # Tenant context
    tenant_slug = Column(String(100), nullable=False, index=True)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    is_superuser = Column(Boolean, nullable=False, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    
    # Preferences
    preferences = Column(JSON, nullable=True, default=dict)
    
    # Relationships
    agents = relationship("AgentConfig", back_populates="creator")
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "keycloak_id": self.keycloak_id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "phone": self.phone,
            "roles": self.roles,
            "permissions": self.permissions,
            "tenant_slug": self.tenant_slug,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_superuser": self.is_superuser,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "preferences": self.preferences,
        }
    
    def has_role(self, role: str) -> bool:
        """Check if user has specific role"""
        return role in (self.roles or [])
    
    def has_any_role(self, roles: list) -> bool:
        """Check if user has any of the specified roles"""
        user_roles = self.roles or []
        return any(role in user_roles for role in roles)
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in (self.permissions or [])
    
    @classmethod
    def get_by_keycloak_id(cls, db: Session, keycloak_id: str) -> Optional["User"]:
        """Get user by Keycloak ID"""
        return db.query(cls).filter(cls.keycloak_id == keycloak_id).first()
    
    @classmethod
    def get_by_email(cls, db: Session, email: str) -> Optional["User"]:
        """Get user by email"""
        return db.query(cls).filter(cls.email == email).first()
    
    @classmethod
    def get_active_users(cls, db: Session, tenant_slug: str) -> List["User"]:
        """Get all active users for a tenant"""
        return db.query(cls).filter(
            cls.tenant_slug == tenant_slug,
            cls.is_active == True
        ).all()
    
    @classmethod
    def count_users(cls, db: Session, tenant_slug: str) -> int:
        """Count users for a tenant"""
        return db.query(cls).filter(cls.tenant_slug == tenant_slug).count()
    
    def update_last_seen(self, db: Session):
        """Update last seen timestamp"""
        self.last_seen = datetime.utcnow()
        db.commit()
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', tenant='{self.tenant_slug}')>"
