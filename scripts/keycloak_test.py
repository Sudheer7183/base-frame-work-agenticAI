#!/usr/bin/env python3
"""
Keycloak initialization script for Agentic AI Platform

Run this after Keycloak is started to:
1. Verify Keycloak connection
2. Setup default roles
3. Create test users
4. Validate configuration

Usage:
    python scripts/init_keycloak.py
    python scripts/init_keycloak.py --create-test-users
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import logging
from app.keycloak.service import get_keycloak_service


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def verify_connection():
    """Verify Keycloak connection"""
    logger.info("="*80)
    logger.info("KEYCLOAK CONNECTION TEST")
    logger.info("="*80)
    
    try:
        keycloak = get_keycloak_service()
        

        
        token = await keycloak.get_admin_token()
        logger.info("✓ Admin authentication successful")
        
        # Test public key retrieval
        public_key = await keycloak.get_public_key()
        logger.info(f"✓ Retrieved public key (found {len(public_key.get('keys', []))} keys)")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Connection failed: {e}")
        return False


async def setup_default_roles():
    """Create default roles in Keycloak"""
    logger.info("\n" + "="*80)
    logger.info("SETTING UP DEFAULT ROLES")
    logger.info("="*80)
    
    keycloak = get_keycloak_service()
    
    roles = [
        ("SUPER_ADMIN", "Super administrator with full system access"),
        ("ADMIN", "Tenant administrator"),
        ("USER", "Standard user"),
        ("VIEWER", "Read-only access"),
    ]
    
    for role_name, description in roles:
        try:
            await keycloak.create_role(role_name, description)
            logger.info(f"✓ Created role: {role_name}")
        except Exception as e:
            if "409" in str(e):  # Conflict - already exists
                logger.info(f"○ Role already exists: {role_name}")
            else:
                logger.error(f"✗ Failed to create role {role_name}: {e}")


async def create_test_users():
    """Create test users for development"""
    logger.info("\n" + "="*80)
    logger.info("CREATING TEST USERS")
    logger.info("="*80)
    
    keycloak = get_keycloak_service()
    
    test_users = [
        {
            "email": "admin@test.com",
            "username": "testadmin",
            "password": "Test123!",
            "tenant_slug": "demo",
            "first_name": "Test",
            "last_name": "Admin",
            "roles": ["ADMIN", "USER"]
        },
        {
            "email": "user@test.com",
            "username": "testuser",
            "password": "Test123!",
            "tenant_slug": "demo",
            "first_name": "Test",
            "last_name": "User",
            "roles": ["USER"]
        },
        {
            "email": "viewer@test.com",
            "username": "testviewer",
            "password": "Test123!",
            "tenant_slug": "demo",
            "first_name": "Test",
            "last_name": "Viewer",
            "roles": ["VIEWER"]
        }
    ]
    
    for user_data in test_users:
        try:
            # Check if user exists
            existing = await keycloak.get_user_by_email(user_data["email"])
            
            if existing:
                logger.info(f"○ User already exists: {user_data['email']}")
                continue
            
            # Create user
            user_id = await keycloak.create_user(**user_data)
            logger.info(f"✓ Created user: {user_data['email']} (ID: {user_id})")
            
        except Exception as e:
            logger.error(f"✗ Failed to create user {user_data['email']}: {e}")


async def setup_demo_tenant():
    """Setup demo tenant with admin user"""
    logger.info("\n" + "="*80)
    logger.info("SETTING UP DEMO TENANT")
    logger.info("="*80)
    
    keycloak = get_keycloak_service()
    tenant_slug = "demo"
    
    try:
        # Setup tenant roles
        await keycloak.setup_tenant_roles(tenant_slug)
        logger.info(f"✓ Setup roles for tenant: {tenant_slug}")
        
        # Check if admin exists
        admin_email = "demo-admin@test.com"
        existing = await keycloak.get_user_by_email(admin_email)
        
        if existing:
            logger.info(f"○ Demo admin already exists: {admin_email}")
            return
        
        # Create tenant admin
        user_id = await keycloak.provision_tenant_admin(
            tenant_slug=tenant_slug,
            admin_email=admin_email,
            admin_username="demo-admin",
            admin_password="DemoAdmin123!"
        )
        
        logger.info(f"✓ Created demo admin: {admin_email}")
        logger.info(f"  Username: demo-admin")
        logger.info(f"  Password: DemoAdmin123!")
        logger.info(f"  Tenant: {tenant_slug}")
        
    except Exception as e:
        logger.error(f"✗ Failed to setup demo tenant: {e}")


async def verify_token_flow():
    """Test complete token flow"""
    logger.info("\n" + "="*80)
    logger.info("TESTING TOKEN FLOW")
    logger.info("="*80)
    
    keycloak = get_keycloak_service()
    
    try:
        # This would normally be done via OAuth2 flow
        # For testing, we just verify the token verification works
        
        import httpx
        
        # Get token for admin user
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:8080/realms/agentic/protocol/openid-connect/token",
                data={
                    "client_id": "agentic-api",
                    "client_secret": "your-client-secret-here-change-in-production",
                    "grant_type": "password",
                    "username": "admin",
                    "password": "admin"
                }
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data["access_token"]
                
                logger.info("✓ Successfully obtained access token")
                
                # Verify token
                payload = await keycloak.verify_token(access_token)
                logger.info(f"✓ Token verified successfully")
                logger.info(f"  Subject: {payload.get('sub')}")
                logger.info(f"  Email: {payload.get('email')}")
                logger.info(f"  Roles: {payload.get('realm_access', {}).get('roles', [])}")
                
                return True
            else:
                logger.error(f"✗ Failed to get token: {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"✗ Token flow test failed: {e}")
        logger.info("\nNote: Make sure the default admin user exists in Keycloak")
        logger.info("      (username: admin, password: admin)")
        return False


async def show_summary():
    """Show setup summary and next steps"""
    logger.info("\n" + "="*80)
    logger.info("SETUP COMPLETE - SUMMARY")
    logger.info("="*80)
    
    logger.info("\n✓ Keycloak is configured and ready!")
    logger.info("\nTest Users Created:")
    logger.info("  1. Admin User:")
    logger.info("     Email: admin@test.com")
    logger.info("     Username: testadmin")
    logger.info("     Password: Test123!")
    logger.info("     Tenant: demo")
    logger.info("")
    logger.info("  2. Standard User:")
    logger.info("     Email: user@test.com")
    logger.info("     Username: testuser")
    logger.info("     Password: Test123!")
    logger.info("     Tenant: demo")
    logger.info("")
    logger.info("  3. Demo Tenant Admin:")
    logger.info("     Email: demo-admin@test.com")
    logger.info("     Username: demo-admin")
    logger.info("     Password: DemoAdmin123!")
    logger.info("     Tenant: demo")
    
    logger.info("\n" + "="*80)
    logger.info("NEXT STEPS")
    logger.info("="*80)
    logger.info("\n1. Test authentication:")
    logger.info("   curl -X POST http://localhost:8080/realms/agentic/protocol/openid-connect/token \\")
    logger.info("     -d 'client_id=agentic-api' \\")
    logger.info("     -d 'client_secret=your-client-secret-here' \\")
    logger.info("     -d 'grant_type=password' \\")
    logger.info("     -d 'username=testadmin' \\")
    logger.info("     -d 'password=Test123!'")
    
    logger.info("\n2. Access Keycloak Admin Console:")
    logger.info("   URL: http://localhost:8080")
    logger.info("   Username: admin")
    logger.info("   Password: admin")
    
    logger.info("\n3. Start your backend:")
    logger.info("   cd backend && uvicorn app.main:app --reload")
    
    logger.info("\n4. Test protected endpoint:")
    logger.info("   curl -X GET http://localhost:8000/api/v1/profile \\")
    logger.info("     -H 'Authorization: Bearer <access_token>'")
    
    logger.info("\n" + "="*80)


async def main():
    """Main initialization flow"""
    parser = argparse.ArgumentParser(description="Initialize Keycloak for Agentic AI Platform")
    parser.add_argument("--create-test-users", action="store_true", help="Create test users")
    parser.add_argument("--setup-demo", action="store_true", help="Setup demo tenant")
    parser.add_argument("--test-token", action="store_true", help="Test token flow")
    parser.add_argument("--full", action="store_true", help="Run full setup")
    
    args = parser.parse_args()
    
    # If no args, run full setup
    if not any([args.create_test_users, args.setup_demo, args.test_token, args.full]):
        args.full = True
    
    logger.info("Agentic AI Platform - Keycloak Initialization")
    logger.info("=" * 80)
    
    # Step 1: Verify connection
    if not await verify_connection():
        logger.error("\nSetup failed: Could not connect to Keycloak")
        logger.info("\nTroubleshooting:")
        logger.info("1. Is Keycloak running? Check: docker compose ps")
        logger.info("2. Is it accessible at the configured URL?")
        logger.info("3. Are credentials correct in .env?")
        sys.exit(1)
    
    # Step 2: Setup roles
    if args.full:
        await setup_default_roles()
    
    # Step 3: Create test users
    if args.create_test_users or args.full:
        await create_test_users()
    
    # Step 4: Setup demo tenant
    if args.setup_demo or args.full:
        await setup_demo_tenant()
    
    # Step 5: Test token flow
    if args.test_token or args.full:
        await verify_token_flow()
    
    # Step 6: Show summary
    if args.full:
        await show_summary()
    
    logger.info("\n✓ Initialization complete!")


if __name__ == "__main__":
    asyncio.run(main())