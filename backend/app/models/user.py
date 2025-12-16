"""User models for authentication and authorization"""

from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base


class User(Base):
    """
    User model
    Stores user information from Keycloak
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    # Keycloak integration
    keycloak_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # User info
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True, index=True)
    full_name = Column(String(255), nullable=True)
    
    # Authorization
    roles = Column(JSON, nullable=True, default=[])
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
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
            "roles": self.roles,
            "is_active": self.is_active,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def has_role(self, role: str) -> bool:
        """Check if user has specific role"""
        return role in (self.roles or [])
    
    def has_any_role(self, roles: list) -> bool:
        """Check if user has any of the specified roles"""
        user_roles = self.roles or []
        return any(role in user_roles for role in roles)
    
    @classmethod
    def get_by_keycloak_id(cls, db, keycloak_id: str):
        """Get user by Keycloak ID"""
        return db.query(cls).filter(cls.keycloak_id == keycloak_id).first()
    
    @classmethod
    def get_by_email(cls, db, email: str):
        """Get user by email"""
        return db.query(cls).filter(cls.email == email).first()
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', active={self.is_active})>"
