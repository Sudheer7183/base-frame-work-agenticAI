"""
SSO (Single Sign-On) Integration Module
Supports multiple SSO providers: SAML, OAuth2, OpenID Connect
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import Column, Integer, String, Boolean, JSON, Text, DateTime
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, EmailStr
import httpx
import jwt
from urllib.parse import urlencode

from app.core.database import get_db
from app.core.config import settings
from app.models.base import Base


# ============================================================================
# SSO Provider Types
# ============================================================================

class SSOProviderType(str, Enum):
    """Supported SSO provider types"""
    SAML = "saml"
    OAUTH2 = "oauth2"
    OIDC = "oidc"
    GOOGLE = "google"
    MICROSOFT = "microsoft"
    OKTA = "okta"
    AUTH0 = "auth0"


# ============================================================================
# Database Models
# ============================================================================

class SSOConfiguration(Base):
    """SSO configuration for tenants"""
    __tablename__ = "sso_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_slug = Column(String(100), nullable=False, index=True)
    provider_type = Column(String(50), nullable=False)
    provider_name = Column(String(255), nullable=False)
    
    # OAuth2/OIDC Configuration
    client_id = Column(String(500), nullable=True)
    client_secret = Column(Text, nullable=True)  # Encrypted
    authorization_endpoint = Column(String(500), nullable=True)
    token_endpoint = Column(String(500), nullable=True)
    userinfo_endpoint = Column(String(500), nullable=True)
    jwks_uri = Column(String(500), nullable=True)
    
    # SAML Configuration
    saml_entity_id = Column(String(500), nullable=True)
    saml_sso_url = Column(String(500), nullable=True)
    saml_certificate = Column(Text, nullable=True)
    
    # Common Configuration
    scopes = Column(JSON, nullable=False, default=["openid", "email", "profile"])
    redirect_uri = Column(String(500), nullable=False)
    
    # Attribute Mapping (maps SSO attributes to our user model)
    attribute_mapping = Column(JSON, nullable=False, default={
        "email": "email",
        "given_name": "first_name",
        "family_name": "last_name",
        "name": "full_name"
    })
    
    # Settings
    is_enabled = Column(Boolean, default=True, index=True)
    auto_provision_users = Column(Boolean, default=True)
    default_role = Column(String(100), nullable=True, default="user")
    require_email_verification = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "tenant_slug": self.tenant_slug,
            "provider_type": self.provider_type,
            "provider_name": self.provider_name,
            "is_enabled": self.is_enabled,
            "redirect_uri": self.redirect_uri,
            "scopes": self.scopes,
            "auto_provision_users": self.auto_provision_users
        }


class SSOSession(Base):
    """Track SSO sessions"""
    __tablename__ = "sso_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    tenant_slug = Column(String(100), nullable=False, index=True)
    provider_type = Column(String(50), nullable=False)
    
    sso_user_id = Column(String(500), nullable=False)  # ID from SSO provider
    access_token = Column(Text, nullable=True)  # Encrypted
    refresh_token = Column(Text, nullable=True)  # Encrypted
    id_token = Column(Text, nullable=True)
    
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=False, default=datetime.utcnow)


# ============================================================================
# Pydantic Schemas
# ============================================================================

class SSOConfigurationCreate(BaseModel):
    """Create SSO configuration"""
    provider_type: SSOProviderType
    provider_name: str = Field(..., max_length=255)
    
    # OAuth2/OIDC
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    authorization_endpoint: Optional[str] = None
    token_endpoint: Optional[str] = None
    userinfo_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None
    
    # SAML
    saml_entity_id: Optional[str] = None
    saml_sso_url: Optional[str] = None
    saml_certificate: Optional[str] = None
    
    scopes: List[str] = Field(default=["openid", "email", "profile"])
    redirect_uri: str
    attribute_mapping: Dict[str, str] = Field(default={
        "email": "email",
        "given_name": "first_name",
        "family_name": "last_name",
        "name": "full_name"
    })
    
    auto_provision_users: bool = True
    default_role: str = "user"
    require_email_verification: bool = False


class SSOConfigurationResponse(BaseModel):
    """SSO configuration response (without secrets)"""
    id: int
    tenant_slug: str
    provider_type: str
    provider_name: str
    is_enabled: bool
    redirect_uri: str
    scopes: List[str]
    auto_provision_users: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SSOInitiateRequest(BaseModel):
    """Request to initiate SSO login"""
    provider_id: int
    return_url: Optional[str] = None


class SSOCallbackRequest(BaseModel):
    """SSO callback data"""
    code: str
    state: str


class SSOUserInfo(BaseModel):
    """User information from SSO provider"""
    sso_user_id: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# SSO Service
# ============================================================================

class SSOService:
    """Service for handling SSO operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_configuration(self, provider_id: int, tenant_slug: str) -> Optional[SSOConfiguration]:
        """Get SSO configuration"""
        return self.db.query(SSOConfiguration).filter(
            SSOConfiguration.id == provider_id,
            SSOConfiguration.tenant_slug == tenant_slug,
            SSOConfiguration.is_enabled == True
        ).first()
    
    def generate_authorization_url(self, config: SSOConfiguration, state: str) -> str:
        """Generate OAuth2/OIDC authorization URL"""
        params = {
            "client_id": config.client_id,
            "redirect_uri": config.redirect_uri,
            "response_type": "code",
            "scope": " ".join(config.scopes),
            "state": state
        }
        
        return f"{config.authorization_endpoint}?{urlencode(params)}"
    
    async def exchange_code_for_token(
        self,
        config: SSOConfiguration,
        code: str
    ) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                config.token_endpoint,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": config.redirect_uri,
                    "client_id": config.client_id,
                    "client_secret": config.client_secret
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to exchange code for token: {response.text}"
                )
            
            return response.json()
    
    async def get_user_info(
        self,
        config: SSOConfiguration,
        access_token: str
    ) -> SSOUserInfo:
        """Fetch user information from SSO provider"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                config.userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to fetch user info: {response.text}"
                )
            
            user_data = response.json()
            
            # Map attributes according to configuration
            mapped_data = {}
            for our_attr, sso_attr in config.attribute_mapping.items():
                if sso_attr in user_data:
                    mapped_data[our_attr] = user_data[sso_attr]
            
            return SSOUserInfo(
                sso_user_id=user_data.get("sub") or user_data.get("id"),
                email=mapped_data.get("email"),
                first_name=mapped_data.get("first_name"),
                last_name=mapped_data.get("last_name"),
                full_name=mapped_data.get("full_name"),
                attributes=user_data
            )
    
    def provision_user(
        self,
        tenant_slug: str,
        user_info: SSOUserInfo,
        default_role: str
    ) -> int:
        """
        Provision a new user from SSO data
        Returns user_id
        """
        # This is a simplified version - implement actual user creation
        # based on your User model
        
        from app.models.user import User
        
        # Check if user exists
        existing_user = self.db.query(User).filter(
            User.email == user_info.email,
            User.tenant_slug == tenant_slug
        ).first()
        
        if existing_user:
            return existing_user.id
        
        # Create new user
        new_user = User(
            email=user_info.email,
            full_name=user_info.full_name,
            tenant_slug=tenant_slug,
            roles=[default_role],
            is_verified=True,  # SSO users are pre-verified
            is_active=True
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        return new_user.id
    
    def create_sso_session(
        self,
        user_id: int,
        tenant_slug: str,
        provider_type: str,
        sso_user_id: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        id_token: Optional[str] = None,
        expires_in: Optional[int] = None
    ) -> SSOSession:
        """Create SSO session record"""
        expires_at = None
        if expires_in:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        session = SSOSession(
            user_id=user_id,
            tenant_slug=tenant_slug,
            provider_type=provider_type,
            sso_user_id=sso_user_id,
            access_token=access_token,  # Should be encrypted
            refresh_token=refresh_token,  # Should be encrypted
            id_token=id_token,
            expires_at=expires_at
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session


# ============================================================================
# API Router
# ============================================================================

router = APIRouter(prefix="/sso", tags=["SSO"])


@router.get("/configurations", response_model=List[SSOConfigurationResponse])
async def list_sso_configurations(
    tenant_slug: str,
    db: Session = Depends(get_db)
):
    """List SSO configurations for a tenant"""
    configs = db.query(SSOConfiguration).filter(
        SSOConfiguration.tenant_slug == tenant_slug
    ).all()
    
    return configs


@router.post("/configurations", response_model=SSOConfigurationResponse)
async def create_sso_configuration(
    tenant_slug: str,
    config: SSOConfigurationCreate,
    db: Session = Depends(get_db)
):
    """Create new SSO configuration"""
    db_config = SSOConfiguration(
        tenant_slug=tenant_slug,
        **config.dict()
    )
    
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    
    return db_config


@router.post("/initiate")
async def initiate_sso_login(
    request: SSOInitiateRequest,
    tenant_slug: str,
    db: Session = Depends(get_db)
):
    """
    Initiate SSO login flow
    Returns authorization URL to redirect user to
    """
    service = SSOService(db)
    config = await service.get_configuration(request.provider_id, tenant_slug)
    
    if not config:
        raise HTTPException(status_code=404, detail="SSO configuration not found")
    
    # Generate state token for CSRF protection
    import secrets
    state = secrets.token_urlsafe(32)
    
    # Store state in session or cache (Redis)
    # TODO: Implement state storage
    
    auth_url = service.generate_authorization_url(config, state)
    
    return {
        "authorization_url": auth_url,
        "state": state
    }


@router.get("/callback/{provider_id}")
async def sso_callback(
    provider_id: int,
    code: str,
    state: str,
    tenant_slug: str,
    db: Session = Depends(get_db)
):
    """
    Handle SSO callback
    This is called by the SSO provider after user authentication
    """
    service = SSOService(db)
    config = await service.get_configuration(provider_id, tenant_slug)
    
    if not config:
        raise HTTPException(status_code=404, detail="SSO configuration not found")
    
    # Verify state (CSRF protection)
    # TODO: Implement state verification
    
    # Exchange code for tokens
    tokens = await service.exchange_code_for_token(config, code)
    
    # Get user information
    user_info = await service.get_user_info(config, tokens["access_token"])
    
    # Provision or get user
    if config.auto_provision_users:
        user_id = service.provision_user(
            tenant_slug,
            user_info,
            config.default_role
        )
    else:
        # User must exist
        from app.models.user import User
        user = db.query(User).filter(
            User.email == user_info.email,
            User.tenant_slug == tenant_slug
        ).first()
        
        if not user:
            raise HTTPException(
                status_code=403,
                detail="User not found. Auto-provisioning is disabled."
            )
        
        user_id = user.id
    
    # Create SSO session
    service.create_sso_session(
        user_id=user_id,
        tenant_slug=tenant_slug,
        provider_type=config.provider_type,
        sso_user_id=user_info.sso_user_id,
        access_token=tokens["access_token"],
        refresh_token=tokens.get("refresh_token"),
        id_token=tokens.get("id_token"),
        expires_in=tokens.get("expires_in")
    )
    
    # Generate application JWT token
    # TODO: Implement JWT token generation
    app_token = "generated_jwt_token_here"
    
    # Redirect to application with token
    return RedirectResponse(
        url=f"/auth/sso-success?token={app_token}",
        status_code=302
    )


@router.delete("/configurations/{config_id}")
async def delete_sso_configuration(
    config_id: int,
    tenant_slug: str,
    db: Session = Depends(get_db)
):
    """Delete SSO configuration"""
    config = db.query(SSOConfiguration).filter(
        SSOConfiguration.id == config_id,
        SSOConfiguration.tenant_slug == tenant_slug
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    db.delete(config)
    db.commit()
    
    return {"message": "SSO configuration deleted successfully"}


@router.put("/configurations/{config_id}/toggle")
async def toggle_sso_configuration(
    config_id: int,
    tenant_slug: str,
    enabled: bool,
    db: Session = Depends(get_db)
):
    """Enable or disable SSO configuration"""
    config = db.query(SSOConfiguration).filter(
        SSOConfiguration.id == config_id,
        SSOConfiguration.tenant_slug == tenant_slug
    ).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    config.is_enabled = enabled
    db.commit()
    
    return {"message": f"SSO configuration {'enabled' if enabled else 'disabled'}"}
