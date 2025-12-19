#!/usr/bin/env python3
"""
Create Keycloak test users from scratch

This script:
1. Deletes existing users (if any)
2. Creates fresh users with proper configuration
3. Sets passwords
4. Assigns roles
5. Tests authentication
"""

import asyncio
import logging
import httpx
from typing import Optional, Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Keycloak configuration
KEYCLOAK_URL = "http://localhost:8080"
REALM = "agentic"
CLIENT_ID = "agentic-api"
CLIENT_SECRET = "your-client-secret-here-change-in-production"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin"

# Test users to create
TEST_USERS = [
    {
        "email": "admin@test.com",
        "username": "super_admin",
        "password": "Test123!",
        "firstName": "Super",
        "lastName": "Admin",
        "roles": ["SUPER_ADMIN", "ADMIN", "USER"],
        "tenant": "demo"
    },
    {
        "email": "admin@example.com",
        "username": "admin",
        "password": "Test123!",
        "firstName": "Admin",
        "lastName": "User",
        "roles": ["ADMIN", "USER"],
        "tenant": "demo"
    },
    {
        "email": "user@test.com",
        "username": "user",
        "password": "Test123!",
        "firstName": "Regular",
        "lastName": "User",
        "roles": ["USER"],
        "tenant": "demo"
    },
    {
        "email": "viewer@test.com",
        "username": "viewer",
        "password": "Test123!",
        "firstName": "Viewer",
        "lastName": "User",
        "roles": ["VIEWER"],
        "tenant": "demo"
    }
]


async def get_admin_token() -> str:
    """Get admin token for Keycloak API"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
            data={
                "client_id": "admin-cli",
                "username": ADMIN_USERNAME,
                "password": ADMIN_PASSWORD,
                "grant_type": "password"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to get admin token: {response.text}")
        
        return response.json()["access_token"]


async def find_user_by_username(admin_token: str, username: str) -> Optional[Dict]:
    """Find user by username"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/users",
            params={"username": username, "exact": "true"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code == 200:
            users = response.json()
            return users[0] if users else None
        return None


async def find_user_by_email(admin_token: str, email: str) -> Optional[Dict]:
    """Find user by email"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/users",
            params={"email": email, "exact": "true"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code == 200:
            users = response.json()
            return users[0] if users else None
        return None


async def delete_user(admin_token: str, user_id: str):
    """Delete a user"""
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code not in (200, 204):
            raise Exception(f"Failed to delete user: {response.text}")


async def create_user(admin_token: str, user_data: Dict) -> str:
    """Create a new user"""
    payload = {
        "username": user_data["username"],
        "email": user_data["email"],
        "firstName": user_data["firstName"],
        "lastName": user_data["lastName"],
        "enabled": True,
        "emailVerified": True,
        "attributes": {
            "tenant": [user_data["tenant"]]
        },
        "credentials": [{
            "type": "password",
            "value": user_data["password"],
            "temporary": False
        }]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/users",
            json=payload,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code not in (201, 204):
            raise Exception(f"Failed to create user: {response.text}")
        
        # Extract user ID from Location header
        location = response.headers.get("Location", "")
        user_id = location.split("/")[-1]
        
        return user_id


async def get_role(admin_token: str, role_name: str) -> Optional[Dict]:
    """Get role by name"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/roles/{role_name}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code == 200:
            return response.json()
        return None


async def assign_roles(admin_token: str, user_id: str, role_names: list):
    """Assign roles to user"""
    # Get role objects
    roles = []
    for role_name in role_names:
        role = await get_role(admin_token, role_name)
        if role:
            roles.append(role)
        else:
            logger.warning(f"  ⚠️  Role not found: {role_name}")
    
    if not roles:
        logger.warning(f"  ⚠️  No valid roles to assign")
        return
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}/role-mappings/realm",
            json=roles,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        if response.status_code not in (200, 204):
            raise Exception(f"Failed to assign roles: {response.text}")


async def test_login(username: str, password: str) -> tuple[bool, Any]:
    """Test user login"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "password",
                "username": username,
                "password": password
            }
        )
        
        return response.status_code == 200, response


async def process_user(admin_token: str, user_data: Dict) -> bool:
    """Process a single user: delete if exists, create fresh, assign roles, test"""
    username = user_data["username"]
    email = user_data["email"]
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Processing: {username} ({email})")
    logger.info(f"{'='*80}")
    
    try:
        # Check if user exists by username or email
        logger.info("🔍 Checking for existing user...")
        existing_by_username = await find_user_by_username(admin_token, username)
        existing_by_email = await find_user_by_email(admin_token, email)
        
        # Delete if exists
        if existing_by_username:
            logger.info(f"  Found by username: {existing_by_username['id']}")
            logger.info(f"  🗑️  Deleting old user...")
            await delete_user(admin_token, existing_by_username["id"])
            logger.info(f"  ✅ Deleted")
        
        if existing_by_email and (not existing_by_username or existing_by_email["id"] != existing_by_username["id"]):
            logger.info(f"  Found by email: {existing_by_email['id']}")
            logger.info(f"  🗑️  Deleting old user...")
            await delete_user(admin_token, existing_by_email["id"])
            logger.info(f"  ✅ Deleted")
        
        if not existing_by_username and not existing_by_email:
            logger.info(f"  No existing user found")
        
        # Create fresh user
        logger.info(f"👤 Creating user...")
        user_id = await create_user(admin_token, user_data)
        logger.info(f"  ✅ Created: {user_id}")
        
        # Assign roles
        logger.info(f"🔐 Assigning roles: {user_data['roles']}")
        await assign_roles(admin_token, user_id, user_data["roles"])
        logger.info(f"  ✅ Roles assigned")
        
        # Test login
        logger.info(f"🧪 Testing login...")
        success, response = await test_login(username, user_data["password"])
        
        if success:
            logger.info(f"  ✅ Login successful!")
            token_data = response.json()
            logger.info(f"     Token expires in: {token_data.get('expires_in')} seconds")
            return True
        else:
            logger.error(f"  ❌ Login failed: {response.text}")
            return False
    
    except Exception as e:
        logger.error(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def verify_roles_exist(admin_token: str):
    """Verify that required roles exist in Keycloak"""
    logger.info("\n🔍 Verifying required roles exist...")
    
    required_roles = ["SUPER_ADMIN", "ADMIN", "USER", "VIEWER"]
    missing_roles = []
    
    for role_name in required_roles:
        role = await get_role(admin_token, role_name)
        if role:
            logger.info(f"  ✅ {role_name}")
        else:
            logger.error(f"  ❌ {role_name} - NOT FOUND")
            missing_roles.append(role_name)
    
    if missing_roles:
        logger.error(f"\n❌ Missing roles: {missing_roles}")
        logger.error("Please create these roles in Keycloak first:")
        logger.error(f"  1. Go to http://localhost:8080")
        logger.error(f"  2. Login as admin")
        logger.error(f"  3. Select realm: {REALM}")
        logger.error(f"  4. Go to Realm Roles")
        logger.error(f"  5. Create missing roles")
        return False
    
    return True


async def main():
    """Main execution"""
    logger.info("="*80)
    logger.info("CREATE KEYCLOAK TEST USERS")
    logger.info("="*80)
    
    try:
        # Get admin token
        logger.info("\n📝 Getting admin token...")
        admin_token = await get_admin_token()
        logger.info("✅ Admin token obtained")
        
        # Verify roles exist
        if not await verify_roles_exist(admin_token):
            return
        
        # Process each user
        success_count = 0
        for user_data in TEST_USERS:
            if await process_user(admin_token, user_data):
                success_count += 1
        
        # Summary
        logger.info(f"\n{'='*80}")
        logger.info("SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"Total users: {len(TEST_USERS)}")
        logger.info(f"Successfully created and tested: {success_count}/{len(TEST_USERS)}")
        
        if success_count == len(TEST_USERS):
            logger.info("\n✅ All users ready!")
            logger.info("\n🧪 Run RBAC tests:")
            logger.info("   python scripts/RABC_testsuite.py")
        else:
            logger.error("\n❌ Some users failed")
    
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())