"""Common Pydantic schemas"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Pagination parameters"""
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    items: List[Any]
    total: int
    limit: int
    offset: int
    has_more: bool


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


class SuccessResponse(BaseModel):
    """Success response schema"""
    message: str
    data: Optional[Dict[str, Any]] = None