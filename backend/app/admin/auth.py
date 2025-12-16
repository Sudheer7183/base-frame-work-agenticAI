"""Admin authentication and authorization"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import BaseModel
from app.core.config import settings

security = HTTPBearer()


class AdminUser(BaseModel):
    """Admin user model"""
    user_id: str
    email: str
    role: str
    is_super_admin: bool = False


def decode_token(token: str) -> dict:
    """Decode JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> AdminUser:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = decode_token(token)
    
    return AdminUser(
        user_id=payload.get("sub"),
        email=payload.get("email"),
        role=payload.get("role", "user"),
        is_super_admin=payload.get("role") == "SUPER_ADMIN"
    )


async def admin_required(
    current_user: AdminUser = Depends(get_current_user)
) -> AdminUser:
    """Require admin role"""
    if current_user.role not in ["ADMIN", "SUPER_ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


async def super_admin_required(
    current_user: AdminUser = Depends(get_current_user)
) -> AdminUser:
    """Require super admin role"""
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user
