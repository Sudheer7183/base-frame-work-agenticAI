"""Pydantic schemas for HITL API"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class HITLRecordResponse(BaseModel):
    """Schema for HITL record response"""
    id: int
    agent_id: int
    agent_name: str
    execution_id: Optional[str]
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    status: str
    priority: str
    feedback: Optional[Dict[str, Any]]
    assigned_to: Optional[int]
    reviewed_by: Optional[int]
    reviewed_at: Optional[str]
    timeout_at: Optional[str]
    escalated: bool
    escalated_at: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    
    class Config:
        from_attributes = True


class HITLApproval(BaseModel):
    """Schema for approving HITL record"""
    feedback: Optional[Dict[str, Any]] = Field(default_factory=dict)
    modified_output: Optional[Dict[str, Any]] = None
    comments: Optional[str] = None


class HITLRejection(BaseModel):
    """Schema for rejecting HITL record"""
    reason: str = Field(..., min_length=1)
    details: Optional[str] = None


class HITLCreate(BaseModel):
    """Schema for creating HITL record"""
    agent_id: int
    agent_name: str
    execution_id: Optional[str] = None
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    priority: str = Field(default="normal", pattern="^(low|normal|high|urgent)$")
