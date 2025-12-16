"""User management API endpoints"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user, get_admin_user, TokenData
from app.core.exceptions import NotFoundException, BadRequestException
from app.models.user import User
from app.schemas.user import UserResponse, UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    user = User.get_by_keycloak_id(db, current_user.sub)
    
    if not user:
        # Create user if doesn't exist (first login)
        user = User(
            keycloak_id=current_user.sub,
            email=current_user.email or "",
            username=current_user.email,
            roles=current_user.roles,
            is_active=True,
            last_login=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
    
    return UserResponse(**user.to_dict())


@router.get("", response_model=List[UserResponse])
async def list_users(
    active_only: bool = Query(True),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    admin: TokenData = Depends(get_admin_user)
):
    """
    List all users (admin only)
    """
    query = db.query(User)
    
    if active_only:
        query = query.filter(User.is_active == True)
    
    users = query.offset(offset).limit(limit).all()
    return [UserResponse(**user.to_dict()) for user in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: TokenData = Depends(get_admin_user)
):
    """Get user by ID (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise NotFoundException(f"User with ID {user_id} not found")
    
    return UserResponse(**user.to_dict())


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    admin: TokenData = Depends(get_admin_user)
):
    """Update user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise NotFoundException(f"User with ID {user_id} not found")
    
    # Update fields
    if user_data.username is not None:
        user.username = user_data.username
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.roles is not None:
        user.roles = user_data.roles
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    db.commit()
    db.refresh(user)
    
    return UserResponse(**user.to_dict())


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: TokenData = Depends(get_admin_user)
):
    """Delete user (admin only)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise NotFoundException(f"User with ID {user_id} not found")
    
    db.delete(user)
    db.commit()
