"""Pydantic schemas for Agent API"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    """Schema for creating an agent"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    workflow: str = Field(..., min_length=1, max_length=255)
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    active: bool = True


class AgentUpdate(BaseModel):
    """Schema for updating an agent"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    workflow: Optional[str] = Field(None, min_length=1, max_length=255)
    config: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None


class AgentResponse(BaseModel):
    """Schema for agent response"""
    id: int
    name: str
    description: Optional[str]
    workflow: str
    config: Dict[str, Any]
    active: bool
    version: int
    created_by: Optional[int]
    created_at: Optional[str]
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True