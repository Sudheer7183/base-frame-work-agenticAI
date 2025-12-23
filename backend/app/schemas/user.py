"""Pydantic schemas for User API"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(BaseModel):
    """Schema for creating a user"""
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)
    roles: Optional[List[str]] = Field(default_factory=lambda: ["USER"])
    permissions: Optional[List[str]] = Field(default_factory=list)
    is_active: bool = True
    is_verified: bool = False
    
    @validator('roles')
    def validate_roles(cls, v):
        """Validate roles"""
        allowed_roles = ["USER", "ADMIN", "SUPER_ADMIN"]
        for role in v:
            if role not in allowed_roles:
                raise ValueError(f"Invalid role: {role}")
        return v


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    username: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    roles: Optional[List[str]] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    preferences: Optional[dict] = None


class UserInvite(BaseModel):
    """Schema for inviting a user"""
    email: EmailStr
    full_name: Optional[str] = None
    roles: Optional[List[str]] = Field(default_factory=lambda: ["USER"])
    send_email: bool = True
    custom_message: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    keycloak_id: Optional[str]
    email: str
    username: Optional[str]
    full_name: Optional[str]
    avatar_url: Optional[str]
    phone: Optional[str]
    roles: Optional[List[str]]
    permissions: Optional[List[str]]
    tenant_slug: str
    is_active: bool
    is_verified: bool
    is_superuser: bool
    created_at: Optional[str]
    updated_at: Optional[str]
    last_login: Optional[str]
    last_seen: Optional[str]
    preferences: Optional[dict]
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for paginated user list"""
    users: List[UserResponse]
    total: int
    limit: int
    offset: int


class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserStats(BaseModel):
    """Schema for user statistics"""
    total_users: int
    active_users: int
    verified_users: int
    users_by_role: dict
    recent_signups: int
    recent_logins: int
