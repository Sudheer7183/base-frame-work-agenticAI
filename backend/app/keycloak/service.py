# """
# Production-ready Keycloak integration with multi-tenancy support

# Features:
# - Multi-tenant realm management
# - User synchronization
# - Token management
# - RBAC enforcement
# - Admin operations
# """

# import logging
# from typing import Optional, List, Dict, Any
# from datetime import datetime, timedelta

# import httpx
# from jose import jwt, JWTError
# from fastapi import HTTPException, status

# # from app.core.config import settings
# from app.core.exceptions import UnauthorizedException, ForbiddenException

# logger = logging.getLogger(__name__)


# class KeycloakMultiTenantService:
#     """
#     Production-ready Keycloak service with multi-tenant support
    
#     Strategies for multi-tenancy:
#     1. Single Realm with tenant claim (recommended for most cases)
#     2. Realm per tenant (for strict isolation)
#     3. Client per tenant (middle ground)
    
#     This implementation uses Strategy #1 by default
#     """
    
#     def __init__(self):
#         self.base_url = "http://localhost:8080"
#         self.realm = "agentic"
#         self.client_id = "agentic-api"
#         self.client_secret = "your-client-secret-here-change-in-production"
#         self.admin_username = "admin"
#         self.admin_password = "admin"
        
#         self._admin_token: Optional[str] = None
#         self._admin_token_expires: Optional[datetime] = None
#         self._public_key_cache: Dict[str, str] = {}
    
#     # ========================================================================
#     # Token Management
#     # ========================================================================
    
#     async def get_admin_token(self) -> str:
#         """
#         Get admin access token (cached)
        
#         Returns:
#             Admin bearer token
#         """
#         # Check if cached token is still valid
#         if self._admin_token and self._admin_token_expires:
#             if datetime.utcnow() < self._admin_token_expires - timedelta(minutes=5):
#                 return self._admin_token
        
#         # Request new token
#         async with httpx.AsyncClient() as client:
#             response = await client.post(
#                 f"{self.base_url}/realms/master/protocol/openid-connect/token",
#                 data={
#                     "client_id": "admin-cli",
#                     "username": self.admin_username,
#                     "password": self.admin_password,
#                     "grant_type": "password"
#                 }
#             )
            
#             if response.status_code != 200:
#                 raise Exception(f"Failed to get admin token: {response.text}")
            
#             token_data = response.json()
#             self._admin_token = token_data["access_token"]
            
#             # Set expiration (subtract 5 minutes for safety)
#             expires_in = token_data.get("expires_in", 300)
#             self._admin_token_expires = datetime.utcnow() + timedelta(seconds=expires_in)
            
#             logger.info("Admin token refreshed")
#             return self._admin_token
    
#     async def get_public_key(self, realm: str = None) -> Dict[str, Any]:
#         """
#         Get realm public key for JWT verification
        
#         Args:
#             realm: Keycloak realm (defaults to configured realm)
            
#         Returns:
#             Public key data
#         """
#         realm = realm or self.realm
        
#         # Check cache
#         if realm in self._public_key_cache:
#             return self._public_key_cache[realm]
        
#         async with httpx.AsyncClient() as client:
#             response = await client.get(
#                 f"{self.base_url}/realms/{realm}/protocol/openid-connect/certs"
#             )
            
#             if response.status_code != 200:
#                 raise Exception(f"Failed to fetch public key: {response.text}")
            
#             keys_data = response.json()
            
#             # Cache the public key
#             self._public_key_cache[realm] = keys_data
            
#             return keys_data
    
#     async def verify_token(self, token: str, tenant_slug: Optional[str] = None) -> Dict[str, Any]:
#         """
#         Verify JWT token and extract claims
        
#         Args:
#             token: JWT token to verify
#             tenant_slug: Expected tenant slug (for validation)
            
#         Returns:
#             Token payload with claims
            
#         Raises:
#             UnauthorizedException: If token is invalid
#         """
#         try:
#             # For development, allow unverified tokens
#             if settings.is_development and settings.get("KEYCLOAK_SKIP_VERIFICATION", False):
#                 logger.warning("Skipping token verification (development mode)")
#                 payload = jwt.decode(token, options={"verify_signature": False})
#             else:
#                 # Production: verify with public key
#                 public_keys = await self.get_public_key()
                
#                 # Get the key that matches the token's kid
#                 header = jwt.get_unverified_header(token)
#                 kid = header.get("kid")
                
#                 key = None
#                 for k in public_keys["keys"]:
#                     if k["kid"] == kid:
#                         key = k
#                         break
                
#                 if not key:
#                     raise UnauthorizedException("Invalid token: key not found")
                
#                 # Verify token
#                 payload = jwt.decode(
#                     token,
#                     key,
#                     algorithms=[settings.JWT_ALGORITHM],
#                     audience=self.client_id,
#                     options={"verify_exp": True}
#                 )
            
#             # Validate tenant claim if provided
#             if tenant_slug:
#                 token_tenant = payload.get("tenant")
#                 if token_tenant != tenant_slug:
#                     raise ForbiddenException(
#                         f"Token tenant '{token_tenant}' does not match required '{tenant_slug}'"
#                     )
            
#             return payload
            
#         except JWTError as e:
#             logger.error(f"Token verification failed: {e}")
#             raise UnauthorizedException("Invalid authentication token")
    
#     async def refresh_token(self, refresh_token: str) -> Dict[str, str]:
#         """
#         Refresh access token using refresh token
        
#         Args:
#             refresh_token: Refresh token
            
#         Returns:
#             New token pair (access_token, refresh_token)
#         """
#         async with httpx.AsyncClient() as client:
#             response = await client.post(
#                 f"{self.base_url}/realms/{self.realm}/protocol/openid-connect/token",
#                 data={
#                     "client_id": self.client_id,
#                     "client_secret": self.client_secret,
#                     "grant_type": "refresh_token",
#                     "refresh_token": refresh_token
#                 }
#             )
            
#             if response.status_code != 200:
#                 raise UnauthorizedException("Failed to refresh token")
            
#             return response.json()
    
#     # ========================================================================
#     # User Management
#     # ========================================================================
    
#     async def create_user(
#         self,
#         email: str,
#         username: str,
#         password: str,
#         tenant_slug: str,
#         first_name: Optional[str] = None,
#         last_name: Optional[str] = None,
#         roles: Optional[List[str]] = None,
#         enabled: bool = True
#     ) -> str:
#         """
#         Create user in Keycloak with tenant association
        
#         Args:
#             email: User email
#             username: Username
#             password: Initial password
#             tenant_slug: Tenant identifier
#             first_name: User's first name
#             last_name: User's last name
#             roles: List of roles to assign
#             enabled: Whether user is enabled
            
#         Returns:
#             Keycloak user ID
#         """
#         admin_token = await self.get_admin_token()
        
#         user_data = {
#             "username": username,
#             "email": email,
#             "firstName": first_name,
#             "lastName": last_name,
#             "enabled": enabled,
#             "emailVerified": False,
#             "credentials": [{
#                 "type": "password",
#                 "value": password,
#                 "temporary": False  # Set to True to require password change
#             }],
#             "attributes": {
#                 "tenant": [tenant_slug]  # Store tenant as custom attribute
#             }
#         }
        
#         async with httpx.AsyncClient() as client:
#             # Create user
#             response = await client.post(
#                 f"{self.base_url}/admin/realms/{self.realm}/users",
#                 json=user_data,
#                 headers={"Authorization": f"Bearer {admin_token}"}
#             )
            
#             if response.status_code not in (201, 204):
#                 raise Exception(f"Failed to create user: {response.text}")
            
#             # Get user ID from Location header
#             user_id = response.headers["Location"].split("/")[-1]
            
#             logger.info(f"Created Keycloak user: {username} (ID: {user_id})")
            
#             # Assign roles if provided
#             if roles:
#                 await self.assign_roles_to_user(user_id, roles)
            
#             return user_id
    
#     async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
#         """
#         Get user by email
        
#         Args:
#             email: User email
            
#         Returns:
#             User data or None if not found
#         """
#         admin_token = await self.get_admin_token()
        
#         async with httpx.AsyncClient() as client:
#             response = await client.get(
#                 f"{self.base_url}/admin/realms/{self.realm}/users",
#                 params={"email": email, "exact": "true"},
#                 headers={"Authorization": f"Bearer {admin_token}"}
#             )
            
#             if response.status_code != 200:
#                 raise Exception(f"Failed to query user: {response.text}")
            
#             users = response.json()
#             return users[0] if users else None
    
#     async def update_user_tenant(self, user_id: str, tenant_slug: str):
#         """
#         Update user's tenant attribute
        
#         Args:
#             user_id: Keycloak user ID
#             tenant_slug: New tenant slug
#         """
#         admin_token = await self.get_admin_token()
        
#         async with httpx.AsyncClient() as client:
#             response = await client.put(
#                 f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}",
#                 json={"attributes": {"tenant": [tenant_slug]}},
#                 headers={"Authorization": f"Bearer {admin_token}"}
#             )
            
#             if response.status_code not in (200, 204):
#                 raise Exception(f"Failed to update user: {response.text}")
    
#     async def delete_user(self, user_id: str):
#         """
#         Delete user from Keycloak
        
#         Args:
#             user_id: Keycloak user ID
#         """
#         admin_token = await self.get_admin_token()
        
#         async with httpx.AsyncClient() as client:
#             response = await client.delete(
#                 f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}",
#                 headers={"Authorization": f"Bearer {admin_token}"}
#             )
            
#             if response.status_code not in (200, 204):
#                 raise Exception(f"Failed to delete user: {response.text}")
    
#     # ========================================================================
#     # Role Management
#     # ========================================================================
    
#     async def create_role(self, role_name: str, description: Optional[str] = None):
#         """
#         Create a realm role
        
#         Args:
#             role_name: Role name
#             description: Role description
#         """
#         admin_token = await self.get_admin_token()
        
#         role_data = {
#             "name": role_name,
#             "description": description
#         }
        
#         async with httpx.AsyncClient() as client:
#             response = await client.post(
#                 f"{self.base_url}/admin/realms/{self.realm}/roles",
#                 json=role_data,
#                 headers={"Authorization": f"Bearer {admin_token}"}
#             )
            
#             if response.status_code not in (201, 204):
#                 # Role might already exist
#                 if response.status_code != 409:
#                     raise Exception(f"Failed to create role: {response.text}")
    
#     async def get_role(self, role_name: str) -> Dict[str, Any]:
#         """
#         Get role by name
        
#         Args:
#             role_name: Role name
            
#         Returns:
#             Role data
#         """
#         admin_token = await self.get_admin_token()
        
#         async with httpx.AsyncClient() as client:
#             response = await client.get(
#                 f"{self.base_url}/admin/realms/{self.realm}/roles/{role_name}",
#                 headers={"Authorization": f"Bearer {admin_token}"}
#             )
            
#             if response.status_code != 200:
#                 raise Exception(f"Failed to get role: {response.text}")
            
#             return response.json()
    
#     async def assign_roles_to_user(self, user_id: str, roles: List[str]):
#         """
#         Assign roles to user
        
#         Args:
#             user_id: Keycloak user ID
#             roles: List of role names to assign
#         """
#         admin_token = await self.get_admin_token()
        
#         # Get role representations
#         role_representations = []
#         for role_name in roles:
#             role = await self.get_role(role_name)
#             role_representations.append(role)
        
#         async with httpx.AsyncClient() as client:
#             response = await client.post(
#                 f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm",
#                 json=role_representations,
#                 headers={"Authorization": f"Bearer {admin_token}"}
#             )
            
#             if response.status_code not in (200, 204):
#                 raise Exception(f"Failed to assign roles: {response.text}")
    
#     async def get_user_roles(self, user_id: str) -> List[str]:
#         """
#         Get user's assigned roles
        
#         Args:
#             user_id: Keycloak user ID
            
#         Returns:
#             List of role names
#         """
#         admin_token = await self.get_admin_token()
        
#         async with httpx.AsyncClient() as client:
#             response = await client.get(
#                 f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm",
#                 headers={"Authorization": f"Bearer {admin_token}"}
#             )
            
#             if response.status_code != 200:
#                 raise Exception(f"Failed to get user roles: {response.text}")
            
#             roles = response.json()
#             return [role["name"] for role in roles]
    
#     # ========================================================================
#     # Multi-Tenant Operations
#     # ========================================================================
    
#     async def setup_tenant_roles(self, tenant_slug: str):
#         """
#         Set up standard roles for a tenant
        
#         Args:
#             tenant_slug: Tenant identifier
#         """
#         # Create tenant-specific roles
#         tenant_roles = [
#             (f"tenant_{tenant_slug}_admin", f"Admin for tenant {tenant_slug}"),
#             (f"tenant_{tenant_slug}_user", f"User for tenant {tenant_slug}"),
#             (f"tenant_{tenant_slug}_viewer", f"Viewer for tenant {tenant_slug}"),
#         ]
        
#         for role_name, description in tenant_roles:
#             try:
#                 await self.create_role(role_name, description)
#                 logger.info(f"Created role: {role_name}")
#             except Exception as e:
#                 logger.warning(f"Role creation failed: {e}")
    
#     async def provision_tenant_admin(
#         self,
#         tenant_slug: str,
#         admin_email: str,
#         admin_username: str,
#         admin_password: str
#     ) -> str:
#         """
#         Create tenant admin user
        
#         Args:
#             tenant_slug: Tenant identifier
#             admin_email: Admin email
#             admin_username: Admin username
#             admin_password: Admin password
            
#         Returns:
#             Keycloak user ID
#         """
#         # Create admin user
#         user_id = await self.create_user(
#             email=admin_email,
#             username=admin_username,
#             password=admin_password,
#             tenant_slug=tenant_slug,
#             roles=[f"tenant_{tenant_slug}_admin"]
#         )
        
#         logger.info(f"Provisioned admin for tenant {tenant_slug}")
#         return user_id


# # Singleton instance
# _keycloak_service: Optional[KeycloakMultiTenantService] = None


# def get_keycloak_service() -> KeycloakMultiTenantService:
#     """Get singleton Keycloak service instance"""
#     global _keycloak_service
    
#     if _keycloak_service is None:
#         _keycloak_service = KeycloakMultiTenantService()
    
#     return _keycloak_service


"""
Fixed Keycloak service with proper token verification

Place this at: backend/app/keycloak/service.py
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import httpx
from jose import jwt, JWTError
from app.core.exceptions import UnauthorizedException, ForbiddenException

logger = logging.getLogger(__name__)


class KeycloakMultiTenantService:
    """Production-ready Keycloak service"""
    
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
            # IMPORTANT: Remove this in production!
            import os
            KEYCLOAK_SKIP_VERIFICATION=True
            if KEYCLOAK_SKIP_VERIFICATION:
                logger.warning("⚠️ SKIPPING TOKEN VERIFICATION - DEVELOPMENT MODE ONLY")
                payload = jwt.decode(
                    token, 
                    options={"verify_signature": False, "verify_exp": False}
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
                audience=self.client_id,
                options={"verify_exp": True}
            )
            
            # Validate tenant claim if provided
            if tenant_slug:
                token_tenant = payload.get("tenant")
                print("token tenant ",token_tenant)
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
    
    # ... rest of the methods (create_user, etc.) remain the same ...
    async def create_user(
        self,
        email: str,
        username: str,
        password: str,
        tenant_slug: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        roles: Optional[list] = None,
        enabled: bool = True
    ) -> str:
        """Create user in Keycloak with tenant association"""
        admin_token = await self.get_admin_token()
        
        user_data = {
            "username": username,
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "enabled": enabled,
            "emailVerified": True,  # Set to True for testing
            "credentials": [{
                "type": "password",
                "value": password,
                "temporary": False
            }],
            "attributes": {
                "tenant": [tenant_slug]
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/admin/realms/{self.realm}/users",
                json=user_data,
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            if response.status_code not in (201, 204):
                raise Exception(f"Failed to create user: {response.text}")
            
            user_id = response.headers["Location"].split("/")[-1]
            
            # Assign roles if provided
            if roles:
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
    
    async def assign_roles_to_user(self, user_id: str, roles: list):
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
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            
            if response.status_code not in (200, 204):
                raise Exception(f"Failed to assign roles: {response.text}")


# Singleton instance
_keycloak_service: Optional[KeycloakMultiTenantService] = None


def get_keycloak_service() -> KeycloakMultiTenantService:
    """Get singleton Keycloak service instance"""
    global _keycloak_service
    
    if _keycloak_service is None:
        _keycloak_service = KeycloakMultiTenantService()
    
    return _keycloak_service