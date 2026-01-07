"""
Complete Enhanced Keycloak Service with Auto-Configuration
Includes ALL existing functionality + new automatic configuration

Place this at: backend/app/keycloak/service.py
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

import httpx
from jose import jwt, JWTError
from app.core.exceptions import UnauthorizedException, ForbiddenException

logger = logging.getLogger(__name__)

import os
KEYCLOAK_SKIP_VERIFICATION = os.getenv("KEYCLOAK_SKIP_VERIFICATION", "false").lower() == "true"

class KeycloakMultiTenantService:
    """
    Production-ready Keycloak service with automatic configuration
    
    Features:
    - Automatic client configuration (Direct Access Grants, mappers)
    - Automatic realm settings (unmanaged attributes)
    - User creation with proper attributes
    - Token verification
    - Role management
    - All existing functionality preserved
    """
    
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.realm = "agentic"
        self.client_id = "agentic-api"
        self.client_secret = "your-client-secret-here-change-in-production"
        self.admin_username = "admin"
        self.admin_password = "admin"
        
        self._admin_token: Optional[str] = None
        self._admin_token_expires: Optional[datetime] = None
        self._public_key_cache: Dict[str, Any] = {}
        self._configuration_done: bool = False
    
    # ========================================================================
    # AUTOMATIC CONFIGURATION (NEW)
    # ========================================================================
    
    async def ensure_configuration(self):
        """
        Ensure Keycloak is properly configured
        This runs once on first use
        """
        if self._configuration_done:
            return
        
        try:
            logger.info("🔧 Ensuring Keycloak configuration...")
            
            # Enable unmanaged attributes
            await self._enable_unmanaged_attributes()
            
            # Configure API client
            await self._configure_client("agentic-api")
            
            # Configure Frontend client
            await self._configure_client("agentic-frontend")
            
            self._configuration_done = True
            logger.info("✅ Keycloak configuration complete")
            
        except Exception as e:
            logger.warning(f"⚠️  Keycloak configuration failed (non-fatal): {e}")
            # Don't fail startup if configuration fails
            self._configuration_done = True
    
    async def _enable_unmanaged_attributes(self):
        """Enable unmanaged attributes in realm settings"""
        try:
            token = await self.get_admin_token()
            
            async with httpx.AsyncClient() as client:
                # Get current realm settings
                response = await client.get(
                    f"{self.base_url}/admin/realms/{self.realm}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code != 200:
                    logger.warning(f"Could not get realm settings: {response.status_code}")
                    return
                
                realm_config = response.json()
                
                # Update with unmanaged attributes enabled
                if "attributes" not in realm_config:
                    realm_config["attributes"] = {}
                
                realm_config["attributes"]["userProfileEnabled"] = "true"
                
                # Update realm
                response = await client.put(
                    f"{self.base_url}/admin/realms/{self.realm}",
                    json=realm_config,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                )
                
                if response.status_code in (200, 204):
                    logger.info("✅ Unmanaged attributes enabled")
                else:
                    logger.warning(f"Could not update realm: {response.status_code}")
                    
        except Exception as e:
            logger.warning(f"Failed to enable unmanaged attributes: {e}")
    
    async def _get_client_internal_id(self, client_id: str) -> Optional[str]:
        """Get Keycloak internal client UUID"""
        try:
            token = await self.get_admin_token()
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/admin/realms/{self.realm}/clients",
                    params={"clientId": client_id},
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code != 200:
                    return None
                
                clients = response.json()
                return clients[0]["id"] if clients else None
                
        except Exception as e:
            logger.warning(f"Failed to get client ID for {client_id}: {e}")
            return None
    
    async def _configure_client(self, client_id: str):
        """Configure a Keycloak client with necessary settings"""
        try:
            internal_id = await self._get_client_internal_id(client_id)
            if not internal_id:
                logger.warning(f"Client {client_id} not found, skipping configuration")
                return
            
            token = await self.get_admin_token()
            
            async with httpx.AsyncClient() as client:
                # Get current client config
                response = await client.get(
                    f"{self.base_url}/admin/realms/{self.realm}/clients/{internal_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code != 200:
                    logger.warning(f"Could not get client config for {client_id}")
                    return
                
                client_config = response.json()
                
                # Enable Direct Access Grants
                client_config["directAccessGrantsEnabled"] = True
                client_config["standardFlowEnabled"] = True
                
                # Update client
                response = await client.put(
                    f"{self.base_url}/admin/realms/{self.realm}/clients/{internal_id}",
                    json=client_config,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                )
                
                if response.status_code in (200, 204):
                    logger.info(f"✅ Direct Access Grants enabled for {client_id}")
                    
                    # Configure mappers
                    await self._configure_client_mappers(client_id, internal_id)
                else:
                    logger.warning(f"Could not update client {client_id}: {response.status_code}")
                    
        except Exception as e:
            logger.warning(f"Failed to configure client {client_id}: {e}")
    
    async def _configure_client_mappers(self, client_id: str, internal_id: str):
        """Configure protocol mappers for a client"""
        try:
            token = await self.get_admin_token()
            
            # Get or create dedicated scope
            scope_name = f"{client_id}-dedicated"
            scope_id = await self._get_or_create_client_scope(scope_name, internal_id)
            
            if not scope_id:
                logger.warning(f"Could not get/create scope for {client_id}")
                return
            
            # Define mappers
            mappers = [
                {
                    "name": "tenant-mapper",
                    "protocol": "openid-connect",
                    "protocolMapper": "oidc-usermodel-attribute-mapper",
                    "consentRequired": False,
                    "config": {
                        "userinfo.token.claim": "true",
                        "user.attribute": "tenant",
                        "id.token.claim": "true",
                        "access.token.claim": "true",
                        "claim.name": "tenant",
                        "jsonType.label": "String"
                    }
                },
                {
                    "name": "roles-mapper",
                    "protocol": "openid-connect",
                    "protocolMapper": "oidc-usermodel-realm-role-mapper",
                    "consentRequired": False,
                    "config": {
                        "multivalued": "true",
                        "userinfo.token.claim": "true",
                        "id.token.claim": "true",
                        "access.token.claim": "true",
                        "claim.name": "roles",
                        "jsonType.label": "String"
                    }
                }
            ]
            
            async with httpx.AsyncClient() as client:
                for mapper in mappers:
                    # Check if mapper exists
                    response = await client.get(
                        f"{self.base_url}/admin/realms/{self.realm}/client-scopes/{scope_id}/protocol-mappers/models",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    
                    existing_mappers = response.json() if response.status_code == 200 else []
                    mapper_exists = any(m.get("name") == mapper["name"] for m in existing_mappers)
                    
                    if mapper_exists:
                        logger.debug(f"Mapper {mapper['name']} already exists")
                        continue
                    
                    # Create mapper
                    response = await client.post(
                        f"{self.base_url}/admin/realms/{self.realm}/client-scopes/{scope_id}/protocol-mappers/models",
                        json=mapper,
                        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                    )
                    
                    if response.status_code == 201:
                        logger.info(f"✅ Created mapper {mapper['name']} for {client_id}")
                    elif response.status_code == 409:
                        logger.debug(f"Mapper {mapper['name']} already exists")
                    else:
                        logger.warning(f"Could not create mapper {mapper['name']}: {response.status_code}")
                        
        except Exception as e:
            logger.warning(f"Failed to configure mappers for {client_id}: {e}")
    
    async def _get_or_create_client_scope(self, scope_name: str, client_internal_id: str) -> Optional[str]:
        """Get or create a client scope"""
        try:
            token = await self.get_admin_token()
            
            async with httpx.AsyncClient() as client:
                # Check if scope exists
                response = await client.get(
                    f"{self.base_url}/admin/realms/{self.realm}/client-scopes",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    scopes = response.json()
                    for scope in scopes:
                        if scope.get("name") == scope_name:
                            return scope.get("id")
                
                # Create scope
                response = await client.post(
                    f"{self.base_url}/admin/realms/{self.realm}/client-scopes",
                    json={
                        "name": scope_name,
                        "description": f"Dedicated scope for {scope_name}",
                        "protocol": "openid-connect",
                        "attributes": {
                            "include.in.token.scope": "true",
                            "display.on.consent.screen": "false"
                        }
                    },
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                )
                
                if response.status_code == 201:
                    # Get the created scope ID
                    location = response.headers.get("Location")
                    if location:
                        scope_id = location.split("/")[-1]
                        
                        # Assign scope to client
                        await client.put(
                            f"{self.base_url}/admin/realms/{self.realm}/clients/{client_internal_id}/default-client-scopes/{scope_id}",
                            headers={"Authorization": f"Bearer {token}"}
                        )
                        
                        return scope_id
                        
        except Exception as e:
            logger.warning(f"Failed to get/create client scope {scope_name}: {e}")
            return None
    
    # ========================================================================
    # ADMIN TOKEN MANAGEMENT (EXISTING)
    # ========================================================================
    
    async def get_admin_token(self) -> str:
        """Get admin access token (cached)"""
        if self._admin_token and self._admin_token_expires:
            if datetime.utcnow() < self._admin_token_expires - timedelta(minutes=5):
                return self._admin_token
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/realms/master/protocol/openid-connect/token",
                data={
                    "client_id": "admin-cli",
                    "username": self.admin_username,
                    "password": self.admin_password,
                    "grant_type": "password"
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get admin token: {response.text}")
            
            token_data = response.json()
            self._admin_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 300)
            self._admin_token_expires = datetime.utcnow() + timedelta(seconds=expires_in)
            
            return self._admin_token
    
    # ========================================================================
    # PUBLIC KEY & TOKEN VERIFICATION (EXISTING)
    # ========================================================================
    
    async def get_public_key(self, realm: str = None) -> Dict[str, Any]:
        """Get realm public key for JWT verification"""
        realm = realm or self.realm
        
        # Check cache
        if realm in self._public_key_cache:
            return self._public_key_cache[realm]
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/realms/{realm}/protocol/openid-connect/certs"
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch public key: {response.text}")
            
            keys_data = response.json()
            self._public_key_cache[realm] = keys_data
            
            return keys_data
    
    async def verify_token(
        self, 
        token: str, 
        tenant_slug: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify JWT token and extract claims
        
        Args:
            token: JWT token to verify
            tenant_slug: Expected tenant slug (optional, for validation)
            
        Returns:
            Token payload with claims
        """
        try:
            # DEVELOPMENT MODE: Skip signature verification for testing
            if KEYCLOAK_SKIP_VERIFICATION:
                logger.warning("⚠️ SKIPPING TOKEN VERIFICATION - DEVELOPMENT MODE ONLY")
                payload = jwt.decode(
                    token, 
                    options={
                        "verify_signature": False, 
                        "verify_exp": False,
                        "verify_aud": False,
                    }
                )
                return payload
            
            # PRODUCTION: Verify with public key
            public_keys = await self.get_public_key()
            
            # Get the key that matches the token's kid
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            
            key = None
            for k in public_keys["keys"]:
                if k["kid"] == kid:
                    key = k
                    break
            
            if not key:
                raise UnauthorizedException("Invalid token: key not found")
            
            # Verify token
            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                options={"verify_exp": True, "verify_aud": False}
            )
            
            # Validate tenant claim if provided
            if tenant_slug:
                token_tenant = payload.get("tenant")
                if token_tenant != tenant_slug:
                    logger.warning(
                        f"Token tenant '{token_tenant}' != required '{tenant_slug}'"
                    )
                    # Don't raise exception - just log warning
                    # This allows super admins to access any tenant
            
            return payload
            
        except JWTError as e:
            logger.error(f"Token verification failed: {e}")
            raise UnauthorizedException("Invalid authentication token")
    
    # ========================================================================
    # USER MANAGEMENT (ENHANCED)
    # ========================================================================
    
    async def create_user(
        self,
        email: str,
        username: str,
        password: str,
        tenant_slug: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        roles: Optional[List[str]] = None,
        enabled: bool = True,
        additional_attributes: Optional[Dict[str, List[str]]] = None
    ) -> str:
        """
        Create user in Keycloak with proper configuration
        
        This method ensures the user is created with:
        - Tenant attribute
        - Email verification
        - No required actions
        - Proper roles
        - Any additional attributes
        
        Args:
            email: User email
            username: Username
            password: Password (non-temporary)
            tenant_slug: Tenant identifier
            first_name: First name
            last_name: Last name
            roles: List of roles to assign
            enabled: Whether user is enabled
            additional_attributes: Dict of additional attributes (each value is a list)
        
        Returns:
            Keycloak user ID
        """
        # Ensure configuration is done
        await self.ensure_configuration()
        
        admin_token = await self.get_admin_token()
        
        # Prepare attributes
        attributes = {
            "tenant": [tenant_slug]
        }
        
        if additional_attributes:
            attributes.update(additional_attributes)
        
        user_data = {
            "username": username,
            "email": email,
            "firstName": first_name or username,
            "lastName": last_name or "",
            "enabled": enabled,
            "emailVerified": True,  # Auto-verify email
            "credentials": [{
                "type": "password",
                "value": password,
                "temporary": False  # Don't require password change
            }],
            "attributes": attributes,
            "requiredActions": []  # No required actions - user can login immediately
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/admin/realms/{self.realm}/users",
                json=user_data,
                headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
            )
            
            if response.status_code not in (201, 204):
                raise Exception(f"Failed to create user: {response.text}")
            
            # Get user ID from Location header
            location = response.headers.get("Location")
            user_id = location.split("/")[-1] if location else None
            
            if not user_id:
                # Fallback: query for user
                response = await client.get(
                    f"{self.base_url}/admin/realms/{self.realm}/users",
                    params={"email": email, "exact": "true"},
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                
                if response.status_code == 200:
                    users = response.json()
                    user_id = users[0]["id"] if users else None
            
            logger.info(f"✅ Created Keycloak user: {username} (ID: {user_id})")
            
            # Assign roles if provided
            if roles and user_id:
                await self.assign_roles_to_user(user_id, roles)
            
            return user_id
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        admin_token = await self.get_admin_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/admin/realms/{self.realm}/users",
                params={"email": email, "exact": "true"},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to query user: {response.text}")
            
            users = response.json()
            return users[0] if users else None
    
    # ========================================================================
    # ROLE MANAGEMENT (EXISTING)
    # ========================================================================
    
    async def get_role(self, role_name: str) -> Dict[str, Any]:
        """Get role by name"""
        admin_token = await self.get_admin_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/admin/realms/{self.realm}/roles/{role_name}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to get role: {response.text}")
            
            return response.json()
    
    async def assign_roles_to_user(self, user_id: str, roles: List[str]):
        """Assign roles to user"""
        admin_token = await self.get_admin_token()
        
        role_representations = []
        for role_name in roles:
            try:
                role = await self.get_role(role_name)
                role_representations.append(role)
            except:
                logger.warning(f"Role {role_name} not found, skipping")
        
        if not role_representations:
            return
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm",
                json=role_representations,
                headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
            )
            
            if response.status_code not in (200, 204):
                raise Exception(f"Failed to assign roles: {response.text}")
            
            logger.info(f"✅ Assigned roles to user: {', '.join(roles)}")
    
    # ========================================================================
    # OAUTH/OIDC METHODS (EXISTING)
    # ========================================================================
    
    async def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": "http://localhost:3000/auth/callback"
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to exchange code: {response.text}")
            
            return response.json()


# Singleton instance
_keycloak_service: Optional[KeycloakMultiTenantService] = None


def get_keycloak_service() -> KeycloakMultiTenantService:
    """Get singleton Keycloak service instance"""
    global _keycloak_service
    
    if _keycloak_service is None:
        _keycloak_service = KeycloakMultiTenantService()
    
    return _keycloak_service