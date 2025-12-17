"""Test script for user creation"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.tenancy.db import init_db, get_session
from app.services.user_service import UserService
from app.schemas.user import UserCreate
from app.tenancy.context import set_tenant

def test_user_creation():
    # Initialize database
    init_db("postgresql://postgres:postgres@localhost:5433/agenticbase2")
    
    # Use context manager for proper session handling
    db = get_session()
    
    try:
        # Set tenant context
        set_tenant("tenant_demo", "demo")
        
        service = UserService(db)
        
        # Create test user
        user_data = UserCreate(
            email="testuser4@example.com",
            username="testuser4",
            full_name="Test User4",
            password="SecurePass",
            roles=["USER"],
            is_active=True
        )
        
        user = service.create_user(user_data, "demo")
        
        print(f"✓ User created successfully!")
        print(f"  ID: {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Tenant: {user.tenant_slug}")
        print(f"  Roles: {user.roles}")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        # Properly close the session
        db.close()

if __name__ == "__main__":
    test_user_creation()