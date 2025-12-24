"""
SSO Callback Handler with Invitation Acceptance

File: backend/app/api/v1/auth.py
Purpose: Handle SSO callbacks and link to invitations
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.keycloak.service import get_keycloak_service
from app.services.user_service import UserService
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/sso/callback")
async def sso_callback(
    code: str = Query(..., description="Authorization code from IdP"),
    state: Optional[str] = Query(None, description="State with invitation token"),
    invitation_token: Optional[str] = Query(None, description="Invitation token (alternative)"),
    db: Session = Depends(get_db)
):
    """
    Handle SSO callback after user authenticates
    
    This is the critical integration point that:
    1. Exchanges authorization code for tokens
    2. Verifies and decodes JWT
    3. Checks for pending invitation (by token or email)
    4. Activates invitation if found
    5. Returns access token for frontend
    
    Query Params:
        code: Authorization code from Keycloak
        state: Optional state containing invitation_token
        invitation_token: Optional direct invitation token
    
    Returns:
        access_token, refresh_token, and user info
    """
    try:
        keycloak = get_keycloak_service()
        user_service = UserService(db)
        
        # ====================================================================
        # Step 1: Exchange Code for Tokens
        # ====================================================================
        logger.info("Exchanging authorization code for tokens")
        
        try:
            tokens = await keycloak.exchange_code_for_tokens(code)
        except Exception as e:
            logger.error(f"Failed to exchange code: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid authorization code"
            )
        
        # ====================================================================
        # Step 2: Verify and Decode Token
        # ====================================================================
        logger.info("Verifying JWT token")
        
        try:
            user_info = await keycloak.verify_token(tokens['access_token'])
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Extract user data
        email = user_info.get('email')
        keycloak_id = user_info.get('sub')
        
        if not email or not keycloak_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required user information from SSO"
            )
        
        logger.info(f"SSO login: {email}")
        
        # ====================================================================
        # Step 3: Determine Invitation Token
        # ====================================================================
        # Priority:
        # 1. Explicit invitation_token parameter
        # 2. invitation_token from state parameter
        # 3. None (will try to match by email)
        
        token = invitation_token
        
        if not token and state:
            # Try to parse state as JSON
            try:
                import json
                state_data = json.loads(state)
                token = state_data.get('invitation_token')
            except:
                # State might be just the token itself
                token = state
        
        logger.info(f"Invitation token: {token[:10] if token else 'None'}")
        
        # ====================================================================
        # Step 4: Check for Pending Invitation
        # ====================================================================
        
        user = None
        invitation_accepted = False
        
        # Option A: Explicit invitation token provided
        if token:
            logger.info("Checking for invitation by token")
            try:
                user = user_service.accept_invitation(
                    invitation_token=token,
                    keycloak_id=keycloak_id,
                    sso_data=user_info
                )
                invitation_accepted = True
                logger.info(f"Invitation accepted via token for {email}")
            except Exception as e:
                logger.warning(f"Failed to accept invitation by token: {e}")
                # Continue to check by email
        
        # Option B: No token, try to match by email
        if not user:
            logger.info("Checking for pending invitation by email")
            pending_user = user_service.get_pending_invitation_by_email(email)
            
            if pending_user:
                try:
                    user = user_service.accept_invitation(
                        invitation_token=pending_user.invitation_token,
                        keycloak_id=keycloak_id,
                        sso_data=user_info
                    )
                    invitation_accepted = True
                    logger.info(f"Invitation accepted via email match for {email}")
                except Exception as e:
                    logger.error(f"Failed to accept invitation by email: {e}")
        
        # Option C: Check if user already exists
        if not user:
            logger.info("Checking for existing user")
            user = user_service.get_by_keycloak_id(keycloak_id)
            
            if user:
                # Existing user, update last login
                user_service.update_last_login(user.id)
                logger.info(f"Existing user logged in: {email}")
            else:
                # Also check by email (in case keycloak_id changed)
                user = user_service.get_user_by_email(email)
                
                if user:
                    # Link keycloak_id
                    user.keycloak_id = keycloak_id
                    db.commit()
                    logger.info(f"Linked existing user to keycloak_id: {email}")
        
        # ====================================================================
        # Step 5: Handle No User Found
        # ====================================================================
        
        if not user:
            # No invitation, no existing user = unauthorized
            logger.warning(f"No access for user: {email}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You don't have access to this platform. "
                    "Please contact your administrator for an invitation."
                )
            )
        
        # ====================================================================
        # Step 6: Return Success Response
        # ====================================================================
        
        return {
            "access_token": tokens['access_token'],
            "refresh_token": tokens.get('refresh_token'),
            "token_type": "bearer",
            "expires_in": tokens.get('expires_in', 3600),
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.full_name,
                "username": user.username,
                "roles": user.roles,
                "tenant": user.tenant_slug,
                "invitation_accepted": invitation_accepted
            },
            "message": "Welcome!" if invitation_accepted else "Welcome back!"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"SSO callback error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed. Please try again."
        )


@router.get("/sso/providers")
async def get_sso_providers(
    tenant_slug: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get available SSO providers for a tenant
    
    Returns list of configured identity providers
    """
    # This would query tenant configuration for SSO providers
    # For now, return defaults
    
    return {
        "providers": [
            {
                "alias": "okta",
                "name": "Okta",
                "display_name": "Login with Okta",
                "logo_url": "/assets/okta-logo.png",
                "enabled": True
            },
            {
                "alias": "azure",
                "name": "Azure AD",
                "display_name": "Login with Microsoft",
                "logo_url": "/assets/microsoft-logo.png",
                "enabled": True
            },
            {
                "alias": "google",
                "name": "Google Workspace",
                "display_name": "Login with Google",
                "logo_url": "/assets/google-logo.png",
                "enabled": True
            }
        ]
    }
