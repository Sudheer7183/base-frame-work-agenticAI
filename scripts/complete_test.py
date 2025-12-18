#!/usr/bin/env python3
"""
Complete tenant testing script
Tests tenant creation, user creation, and agent creation
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.tenancy.db import init_db, get_session
from app.tenancy.service import TenantService
from app.services.user_service import UserService
from app.schemas.user import UserCreate
from app.tenancy.context import set_tenant
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_complete_flow():
    """Test complete tenant + user + agent flow"""
    
    # Initialize DB
    init_db("postgresql://postgres:postgres@localhost:5433/agenticbase2")
    db = get_session()
    
    try:
        # =================================================================
        # STEP 1: Create a Test Tenant
        # =================================================================
        logger.info("="*80)
        logger.info("STEP 1: Creating Test Tenant")
        logger.info("="*80)
        
        tenant_service = TenantService(db)
        
        try:
            tenant = tenant_service.create_tenant(
                slug="testcompany",
                name="Test Company Inc",
                admin_email="admin@testcompany.com",
                max_users=100
            )
            logger.info(f"✓ Tenant created: {tenant.slug} ({tenant.schema_name})")
        except Exception as e:
            if "already exists" in str(e):
                logger.info("✓ Tenant already exists, using existing tenant")
                tenant = tenant_service.get_tenant("testcompany")
            else:
                raise
        
        # =================================================================
        # STEP 2: Create Users in Tenant Schema
        # =================================================================
        logger.info("\n" + "="*80)
        logger.info("STEP 2: Creating Users")
        logger.info("="*80)
        
        # Set tenant context
        set_tenant(tenant.schema_name, tenant.slug)
        
        user_service = UserService(db)
        
        # Create Super Admin (tenant-level)
        try:
            super_admin = user_service.create_user(
                UserCreate(
                    email="superadmin@testcompany.com",
                    username="superadmin",
                    full_name="Super Admin",
                    password="SuperSecure123!",
                    roles=["SUPER_ADMIN"],
                    is_active=True,
                    is_verified=True
                ),
                tenant.slug
            )
            logger.info(f"✓ Super Admin created: {super_admin.email}")
        except Exception as e:
            if "already exists" in str(e):
                logger.info("✓ Super Admin already exists")
            else:
                raise
        
        # Create Regular Admin
        try:
            admin = user_service.create_user(
                UserCreate(
                    email="admin@testcompany.com",
                    username="admin",
                    full_name="Admin User",
                    password="AdminSecure123!",
                    roles=["ADMIN"],
                    is_active=True,
                    is_verified=True
                ),
                tenant.slug
            )
            logger.info(f"✓ Admin created: {admin.email}")
        except Exception as e:
            if "already exists" in str(e):
                logger.info("✓ Admin already exists")
            else:
                raise
        
        # Create Regular User
        try:
            user = user_service.create_user(
                UserCreate(
                    email="user@testcompany.com",
                    username="regularuser",
                    full_name="Regular User",
                    password="UserSecure123!",
                    roles=["USER"],
                    is_active=True,
                    is_verified=True
                ),
                tenant.slug
            )
            logger.info(f"✓ Regular User created: {user.email}")
        except Exception as e:
            if "already exists" in str(e):
                logger.info("✓ Regular User already exists")
            else:
                raise
        
        # =================================================================
        # STEP 3: Create Test Agent
        # =================================================================
        logger.info("\n" + "="*80)
        logger.info("STEP 3: Creating Test Agent")
        logger.info("="*80)
        
        # Create agent in tenant schema
        db.execute(text(f'SET search_path TO "{tenant.schema_name}", public'))
        
        agent_query = text(f"""
            INSERT INTO "{tenant.schema_name}".agents 
            (name, description, workflow, config, active, version, created_at, updated_at)
            VALUES 
            (:name, :description, :workflow, :config, :active, :version, NOW(), NOW())
            ON CONFLICT (name) DO NOTHING
            RETURNING id, name
        """)
        
        result = db.execute(agent_query, {
            "name": "Test Approval Agent",
            "description": "Agent for testing approval workflow with HITL",
            "workflow": "approval",
            "config": '{"model": "gpt-4", "temperature": 0.7, "hitl": {"enabled": true, "threshold": 0.8}}',
            "active": True,
            "version": 1
        })
        
        db.commit()
        
        agent_row = result.fetchone()
        if agent_row:
            logger.info(f"✓ Agent created: {agent_row[1]} (ID: {agent_row[0]})")
        else:
            logger.info("✓ Agent already exists")
        
        # =================================================================
        # STEP 4: Verify Everything
        # =================================================================
        logger.info("\n" + "="*80)
        logger.info("STEP 4: Verification")
        logger.info("="*80)
        
        # Check users
        user_count = db.execute(
            text(f'SELECT COUNT(*) FROM "{tenant.schema_name}".users')
        ).scalar()
        logger.info(f"✓ Users in tenant: {user_count}")
        
        # Check agents
        agent_count = db.execute(
            text(f'SELECT COUNT(*) FROM "{tenant.schema_name}".agents')
        ).scalar()
        logger.info(f"✓ Agents in tenant: {agent_count}")
        
        # List all users
        users_result = db.execute(
            text(f'SELECT id, email, roles FROM "{tenant.schema_name}".users')
        )
        
        logger.info("\nUsers in tenant:")
        for row in users_result:
            logger.info(f"  - {row[1]} (Roles: {row[2]})")
        
        # List all agents
        agents_result = db.execute(
            text(f'SELECT id, name, workflow, active FROM "{tenant.schema_name}".agents')
        )
        
        logger.info("\nAgents in tenant:")
        for row in agents_result:
            logger.info(f"  - {row[1]} (Workflow: {row[2]}, Active: {row[3]})")
        
        # =================================================================
        # SUCCESS
        # =================================================================
        logger.info("\n" + "="*80)
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("="*80)
        
        logger.info("\nYou can now test the API with:")
        logger.info(f"  Tenant: {tenant.slug}")
        logger.info(f"  Schema: {tenant.schema_name}")
        logger.info("\nTest API calls:")
        logger.info(f'  curl -X GET http://localhost:8000/api/v1/agents -H "X-Tenant-ID: {tenant.schema_name}"')
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        raise
    
    finally:
        db.close()


if __name__ == "__main__":
    test_complete_flow()