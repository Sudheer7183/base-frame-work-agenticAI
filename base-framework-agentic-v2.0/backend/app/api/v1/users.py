"""User management API endpoints with multi-tenant support"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, get_admin_user, TokenData
from app.core.exceptions import NotFoundException, BadRequestException, ConflictException
from app.models.user import User
from app.schemas.user import (
    UserResponse,
    UserCreate,
    UserUpdate,
    UserInvite,
    UserListResponse,
    PasswordChange,
    UserStats
)
from app.services.user_service import UserService
from app.tenancy.dependencies import get_current_tenant
from app.tenancy.models import Tenant

router = APIRouter(prefix="/users", tags=["Users"])


# ============================================================================
# Current User Endpoints
# ============================================================================

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user information
    
    Returns the authenticated user's profile
    """
    user = User.get_by_keycloak_id(db, current_user.sub)
    
    if not user:
        # Create user on first login if using Keycloak
        from datetime import datetime
        user = User(
            keycloak_id=current_user.sub,
            email=current_user.email or "",
            username=current_user.email,
            roles=current_user.roles,
            tenant_slug=getattr(current_user, 'tenant', 'default'),
            is_active=True,
            last_login=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update last login
        service = UserService(db)
        service.update_last_login(user.id)
    
    return UserResponse(**user.to_dict())


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile
    
    Users can update their own profile information
    """
    user = User.get_by_keycloak_id(db, current_user.sub)
    if not user:
        raise NotFoundException("User not found")
    
    service = UserService(db)
    
    # Don't allow self-role modification
    user_data.roles = None
    user_data.permissions = None
    user_data.is_active = None
    
    updated_user = service.update_user(user.id, user_data)
    return UserResponse(**updated_user.to_dict())


@router.post("/me/change-password", response_model=UserResponse)
async def change_own_password(
    password_data: PasswordChange,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password
    
    Requires current password for verification
    """
    user = User.get_by_keycloak_id(db, current_user.sub)
    if not user:
        raise NotFoundException("User not found")
    
    service = UserService(db)
    updated_user = service.change_password(
        user.id,
        password_data.current_password,
        password_data.new_password
    )
    
    return UserResponse(**updated_user.to_dict())


# ============================================================================
# User Management Endpoints (Admin)
# ============================================================================

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    tenant: Tenant = Depends(get_current_tenant),
    admin: TokenData = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new user (Admin only)
    
    Creates a user in the current tenant's schema
    """
    service = UserService(db)
    
    try:
        user = service.create_user(user_data, tenant.slug)
        return UserResponse(**user.to_dict())
    except ConflictException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/invite", response_model=UserResponse)
async def invite_user(
    invite_data: UserInvite,
    tenant: Tenant = Depends(get_current_tenant),
    admin: TokenData = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Invite a new user (Admin only)
    
    Creates user account and optionally sends invitation email
    """
    service = UserService(db)
    
    # Create user with unverified status
    user_data = UserCreate(
        email=invite_data.email,
        full_name=invite_data.full_name,
        roles=invite_data.roles,
        is_active=True,
        is_verified=False
    )
    
    user = service.create_user(user_data, tenant.slug)
    
    # TODO: Send invitation email if invite_data.send_email is True
    # This would integrate with your email service
    
    return UserResponse(**user.to_dict())


@router.get("", response_model=UserListResponse)
async def list_users(
    active_only: bool = Query(False),
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    tenant: Tenant = Depends(get_current_tenant),
    admin: TokenData = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all users in current tenant (Admin only)
    
    Supports filtering by status, role, and search
    """
    service = UserService(db)
    users, total = service.list_users(
        tenant_slug=tenant.slug,
        active_only=active_only,
        role=role,
        search=search,
        limit=limit,
        offset=offset
    )
    
    return UserListResponse(
        users=[UserResponse(**user.to_dict()) for user in users],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/stats", response_model=UserStats)
async def get_user_statistics(
    tenant: Tenant = Depends(get_current_tenant),
    admin: TokenData = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get user statistics for current tenant (Admin only)
    
    Returns counts, role distribution, and recent activity
    """
    service = UserService(db)
    return service.get_user_stats(tenant.slug)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    admin: TokenData = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID (Admin only)
    
    Returns full user profile
    """
    service = UserService(db)
    
    try:
        user = service.get_user(user_id)
        return UserResponse(**user.to_dict())
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    admin: TokenData = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update user (Admin only)
    
    Can modify roles, permissions, and status
    """
    service = UserService(db)
    
    try:
        user = service.update_user(user_id, user_data)
        return UserResponse(**user.to_dict())
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    admin: TokenData = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete user (Admin only)
    
    Permanently removes user from tenant
    """
    service = UserService(db)
    
    try:
        service.delete_user(user_id)
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: int,
    admin: TokenData = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Activate a user (Admin only)
    
    Sets user's is_active status to True
    """
    service = UserService(db)
    
    try:
        user_data = UserUpdate(is_active=True)
        user = service.update_user(user_id, user_data)
        return UserResponse(**user.to_dict())
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: int,
    admin: TokenData = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate a user (Admin only)
    
    Sets user's is_active status to False
    """
    service = UserService(db)
    
    try:
        user_data = UserUpdate(is_active=False)
        user = service.update_user(user_id, user_data)
        return UserResponse(**user.to_dict())
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{user_id}/verify", response_model=UserResponse)
async def verify_user(
    user_id: int,
    admin: TokenData = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Verify a user (Admin only)
    
    Marks user as verified
    """
    service = UserService(db)
    
    try:
        user_data = UserUpdate(is_verified=True)
        user = service.update_user(user_id, user_data)
        return UserResponse(**user.to_dict())
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
