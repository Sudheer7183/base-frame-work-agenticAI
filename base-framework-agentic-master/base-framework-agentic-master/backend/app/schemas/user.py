"""Pydantic schemas for User API"""

from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a user"""
    keycloak_id: str = Field(..., min_length=1)
    email: EmailStr
    username: Optional[str] = None
    full_name: Optional[str] = None
    roles: Optional[List[str]] = Field(default_factory=list)
    is_active: bool = True


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    username: Optional[str] = None
    full_name: Optional[str] = None
    roles: Optional[List[str]] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    keycloak_id: str
    email: str
    username: Optional[str]
    full_name: Optional[str]
    roles: Optional[List[str]]
    is_active: bool
    last_login: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True