"""
Integration Tests for Multi-Tenant Platform

File: backend/tests/test_integration.py
Run with: pytest backend/tests/test_integration.py -v
"""

import pytest
import asyncio
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.tenancy.db import init_db
from app.tenancy.service import TenantService
from app.tenancy.models import Tenant, TenantStatus
from app.services.user_service import UserService
from app.schemas.user import UserCreate
from app.tenancy.context import set_tenant, clear_tenant
from app.workflows.nodes import llm_processing_node
from app.workflows.base import WorkflowState

# Test configuration
TEST_DB_URL = "postgresql://postgres:postgres@localhost:5433/agenticbase_test"


@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine"""
    engine = create_engine(TEST_DB_URL, isolation_level="READ COMMITTED")
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a fresh database session for each test"""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    
    # Clean up test data before each test
    try:
        session.execute(text("DROP SCHEMA IF EXISTS tenant_testcompany CASCADE"))
        session.execute(text("DELETE FROM public.tenants WHERE slug = 'testcompany'"))
        session.commit()
    except:
        session.rollback()
    
    yield session
    
    # Cleanup after test
    try:
        session.execute(text("DROP SCHEMA IF EXISTS tenant_testcompany CASCADE"))
        session.execute(text("DELETE FROM public.tenants WHERE slug = 'testcompany'"))
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()
        clear_tenant()


class TestTenantProvisioning:
    """Test tenant creation and provisioning"""
    
    def test_create_tenant(self, db_session):
        """Test basic tenant creation"""
        service = TenantService(db_session)
        
        tenant = service.create_tenant(
            slug="testcompany",
            name="Test Company",
            admin_email="admin@testcompany.com"
        )
        
        assert tenant.slug == "testcompany"
        assert tenant.name == "Test Company"
        assert tenant.status == TenantStatus.ACTIVE.value
        assert tenant.schema_name == "tenant_testcompany"
        
        # Verify schema was created
        result = db_session.execute(
            text("SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = :schema"),
            {"schema": "tenant_testcompany"}
        )
        assert result.scalar() == 1
    
    def test_duplicate_tenant_fails(self, db_session):
        """Test that duplicate tenant creation fails"""
        service = TenantService(db_session)
        
        # Create first tenant
        service.create_tenant(
            slug="testcompany",
            name="Test Company"
        )
        
        # Attempt to create duplicate should fail
        with pytest.raises(Exception) as exc_info:
            service.create_tenant(
                slug="testcompany",
                name="Another Company"
            )
        
        assert "already exists" in str(exc_info.value).lower()
    
    def test_tenant_suspension(self, db_session):
        """Test tenant suspension and activation"""
        service = TenantService(db_session)
        
        tenant = service.create_tenant(
            slug="testcompany",
            name="Test Company"
        )
        
        # Suspend tenant
        suspended = service.suspend_tenant("testcompany", reason="Non-payment")
        assert suspended.status == TenantStatus.SUSPENDED.value
        assert not suspended.is_active()
        
        # Reactivate
        activated = service.activate_tenant("testcompany")
        assert activated.status == TenantStatus.ACTIVE.value
        assert activated.is_active()


class TestUserManagement:
    """Test user creation and management in tenant schema"""
    
    @pytest.fixture
    def tenant(self, db_session):
        """Create a test tenant"""
        service = TenantService(db_session)
        tenant = service.create_tenant(
            slug="testcompany",
            name="Test Company"
        )
        set_tenant(tenant.schema_name, tenant.slug)
        yield tenant
        clear_tenant()
    
    def test_create_user_in_tenant(self, db_session, tenant):
        """Test user creation in tenant schema"""
        user_service = UserService(db_session)
        
        user_data = UserCreate(
            email="user@testcompany.com",
            username="testuser",
            full_name="Test User",
            password="SecurePassword123!",
            roles=["USER"],
            is_active=True
        )
        
        user = user_service.create_user(user_data, tenant.slug)
        
        assert user.email == "user@testcompany.com"
        assert user.tenant_slug == tenant.slug
        assert "USER" in user.roles
        
        # Verify user exists in tenant schema
        result = db_session.execute(
            text(f'SELECT COUNT(*) FROM "{tenant.schema_name}".users WHERE email = :email'),
            {"email": "user@testcompany.com"}
        )
        assert result.scalar() == 1
    
    def test_user_password_hashing(self, db_session, tenant):
        """Test that passwords are properly hashed"""
        user_service = UserService(db_session)
        
        password = "SecurePassword123!"
        user_data = UserCreate(
            email="user@testcompany.com",
            password=password,
            roles=["USER"]
        )
        
        user = user_service.create_user(user_data, tenant.slug)
        
        # Password should be hashed, not plain text
        assert user.hashed_password != password
        assert len(user.hashed_password) > 50  # Hashed passwords are long
        
        # Should be able to verify password
        assert user_service.verify_password(password, user.hashed_password)
        assert not user_service.verify_password("WrongPassword", user.hashed_password)


class TestLLMIntegration:
    """Test LLM integration in workflows"""
    
    @pytest.mark.asyncio
    async def test_ollama_llm_processing(self):
        """Test LLM processing with Ollama (requires Ollama running)"""
        state = WorkflowState(
            agent_id=1,
            agent_name="Test Agent",
            execution_id="test_exec_1",
            input_data={"message": "What is 2+2?"},
            config={
                "provider": "ollama",
                "model": "llama2",
                "temperature": 0.7,
                "system_prompt": "You are a helpful math tutor."
            }
        )
        
        try:
            result_state = await llm_processing_node(state)
            
            assert result_state.output_data is not None
            assert "response" in result_state.output_data
            assert result_state.output_data["success"] is True
            assert result_state.output_data["provider"] == "ollama"
            assert result_state.error is None
            
            # Response should contain something about "4"
            assert "4" in result_state.output_data["response"]
            
        except Exception as e:
            pytest.skip(f"Ollama not available: {e}")
    
    @pytest.mark.asyncio
    async def test_llm_error_handling(self):
        """Test LLM error handling with invalid configuration"""
        state = WorkflowState(
            agent_id=1,
            agent_name="Test Agent",
            execution_id="test_exec_2",
            input_data={"message": "Hello"},
            config={
                "provider": "ollama",
                "ollama_base_url": "http://invalid-url:9999",
                "model": "llama2"
            }
        )
        
        result_state = await llm_processing_node(state)
        
        # Should handle error gracefully
        assert result_state.error is not None
        assert result_state.output_data["success"] is False


class TestEndToEndWorkflow:
    """End-to-end integration tests"""
    
    @pytest.fixture
    def setup_complete_tenant(self, db_session):
        """Setup a complete tenant with users and agents"""
        # Create tenant
        tenant_service = TenantService(db_session)
        tenant = tenant_service.create_tenant(
            slug="testcompany",
            name="Test Company"
        )
        
        # Set context
        set_tenant(tenant.schema_name, tenant.slug)
        
        # Create admin user
        user_service = UserService(db_session)
        admin = user_service.create_user(
            UserCreate(
                email="admin@testcompany.com",
                password="AdminPass123!",
                roles=["ADMIN"],
                is_active=True
            ),
            tenant.slug
        )
        
        # Create agent
        db_session.execute(
            text(f'''
                INSERT INTO "{tenant.schema_name}".agents 
                (name, description, workflow, config, active, version, created_at, updated_at)
                VALUES 
                ('Test Agent', 'Test agent for integration', 'approval', 
                 '{{"model": "llama2", "temperature": 0.7}}'::jsonb, 
                 true, 1, NOW(), NOW())
            ''')
        )
        db_session.commit()
        
        yield {"tenant": tenant, "admin": admin}
        
        clear_tenant()
    
    def test_complete_tenant_setup(self, db_session, setup_complete_tenant):
        """Test complete tenant setup"""
        data = setup_complete_tenant
        tenant = data["tenant"]
        admin = data["admin"]
        
        # Verify tenant exists
        assert tenant.is_active()
        
        # Verify admin user exists
        assert admin.has_role("ADMIN")
        
        # Verify agent exists
        result = db_session.execute(
            text(f'SELECT COUNT(*) FROM "{tenant.schema_name}".agents')
        )
        assert result.scalar() == 1
        
        # Verify tables exist
        result = db_session.execute(
            text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = :schema
            """),
            {"schema": tenant.schema_name}
        )
        table_count = result.scalar()
        assert table_count >= 3  # At least users, agents, hitl_records


class TestSchemaIsolation:
    """Test that tenant schemas are properly isolated"""
    
    def test_tenant_isolation(self, db_session):
        """Test that tenants are isolated from each other"""
        service = TenantService(db_session)
        
        # Create two tenants
        tenant1 = service.create_tenant(slug="tenant1", name="Tenant 1")
        tenant2 = service.create_tenant(slug="tenant2", name="Tenant 2")
        
        # Create user in tenant1
        set_tenant(tenant1.schema_name, tenant1.slug)
        user_service = UserService(db_session)
        user1 = user_service.create_user(
            UserCreate(email="user@tenant1.com", password="Pass123!", roles=["USER"]),
            tenant1.slug
        )
        
        # Create user in tenant2
        set_tenant(tenant2.schema_name, tenant2.slug)
        user2 = user_service.create_user(
            UserCreate(email="user@tenant2.com", password="Pass123!", roles=["USER"]),
            tenant2.slug
        )
        
        # Verify isolation - tenant1 user shouldn't appear in tenant2
        result = db_session.execute(
            text(f'SELECT COUNT(*) FROM "{tenant2.schema_name}".users WHERE email = :email'),
            {"email": "user@tenant1.com"}
        )
        assert result.scalar() == 0
        
        # And vice versa
        result = db_session.execute(
            text(f'SELECT COUNT(*) FROM "{tenant1.schema_name}".users WHERE email = :email'),
            {"email": "user@tenant2.com"}
        )
        assert result.scalar() == 0
        
        clear_tenant()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])