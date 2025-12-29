"""
Agent Builder API Router (Updated for Tenant Middleware)
FastAPI endpoints for agent creation and management

This version works with multi-tenant architecture

File: backend/app/api/v1/agent_builder.py
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.security import TokenData
from app.services.agent_builder_service import AgentBuilderService
from app.schemas.agent_builder import (
    CompleteAgentCreate,
    AgentBuilderConfigUpdate,
    DatabaseConnectionCreate,
    DatabaseConnectionResponse,
    APIConfigurationCreate,
    APIConfigurationResponse,
    ToolCreate,
    ToolResponse,
    AgentTemplateResponse,
    AgentVariableCreate,
    AgentVariableResponse,
    ExecutionTriggerCreate,
    ExecutionTriggerResponse,
    DropdownOptions,
    ConfigValidationRequest,
    ConfigValidationResponse
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-builder", tags=["Agent Builder"])


# Helper function to get tenant_id from header or user context
def get_tenant_id(
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    current_user: TokenData = Depends(get_current_user)
) -> str:
    """
    Extract tenant ID from header or user token
    Handles multi-tenant architecture
    """
    # Priority: Header > User token > Raise error
    if x_tenant_id:
        return x_tenant_id
    
    # Try to get from user token
    if hasattr(current_user, 'tenant_id') and current_user.tenant_id:
        return current_user.tenant_id
    
    # Last resort: check if it's in the sub (user ID might contain tenant info)
    # This depends on your token structure
    logger.warning(f"No tenant ID found for user {current_user.sub}")
    raise HTTPException(
        status_code=400,
        detail="Tenant ID is required. Please include X-Tenant-ID header."
    )


# ============================================================================
# COMPLETE AGENT CREATION
# ============================================================================

@router.post("/agents/complete", response_model=Dict[str, Any])
async def create_complete_agent(
    agent_data: CompleteAgentCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Create a complete agent with all configurations
    
    This is the main endpoint for creating agents via the UI builder
    """
    logger.info(f"Creating agent for tenant: {tenant_id}, user: {current_user.sub}")
    service = AgentBuilderService(db)
    
    try:
        result = service.create_complete_agent(agent_data, current_user.sub)
        return result
    except Exception as e:
        logger.error(f"Error creating complete agent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}/complete", response_model=Dict[str, Any])
async def get_complete_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Get complete agent with all configurations"""
    service = AgentBuilderService(db)
    
    result = service.get_agent_with_config(agent_id)
    if not result:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return result


@router.get("/agents", response_model=List[Dict[str, Any]])
async def list_agents_with_summary(
    workflow: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """List all agents with summary information"""
    service = AgentBuilderService(db)
    
    return service.list_agents_with_summary(workflow, active_only)


# ============================================================================
# DROPDOWN OPTIONS & UI HELPERS
# ============================================================================

@router.get("/ui/options", response_model=DropdownOptions)
async def get_dropdown_options(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Get all dropdown options for UI
    
    Returns all available options for dropdowns in the agent builder UI
    """
    logger.info(f"Getting dropdown options for tenant: {tenant_id}")
    service = AgentBuilderService(db)
    
    return service.get_dropdown_options()


@router.get("/ui/tools", response_model=List[Dict[str, Any]])
async def get_available_tools(
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Get available tools for agent configuration"""
    logger.info(f"Getting tools for tenant: {tenant_id}, category: {category}")
    service = AgentBuilderService(db)
    
    return service.get_available_tools(category)


# ... (rest of the endpoints remain the same, just add tenant_id dependency)

# ============================================================================
# VALIDATION
# ============================================================================

@router.post("/validate", response_model=ConfigValidationResponse)
async def validate_config(
    validation_request: ConfigValidationRequest,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Validate agent configuration before creation
    """
    service = AgentBuilderService(db)
    
    combined_config = {
        **validation_request.agent_config,
        **validation_request.builder_config
    }
    
    return service.validate_agent_config(combined_config)


# ============================================================================
# DATABASE CONNECTIONS
# ============================================================================

@router.post("/database-connections", response_model=Dict[str, int])
async def create_database_connection(
    connection: DatabaseConnectionCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    tenant_id: str = Depends(get_tenant_id)
):
    """Create a new database connection"""
    from sqlalchemy import text
    import json
    from base64 import b64encode
    
    encrypted_password = b64encode(connection.password.encode()).decode() if connection.password else None
    
    query = text("""
        INSERT INTO database_connections (
            name, description, db_type, host, port, database_name,
            username, password_encrypted, pool_size, max_overflow,
            ssl_enabled, created_by, allowed_operations
        ) VALUES (
            :name, :description, :db_type, :host, :port, :database_name,
            :username, :password, :pool_size, :max_overflow,
            :ssl_enabled, :created_by, :allowed_operations
        ) RETURNING id
    """)
    
    result = db.execute(query, {
        "name": connection.name,
        "description": connection.description,
        "db_type": connection.db_type,
        "host": connection.host,
        "port": connection.port,
        "database_name": connection.database_name,
        "username": connection.username,
        "password": encrypted_password,
        "pool_size": connection.pool_size,
        "max_overflow": connection.max_overflow,
        "ssl_enabled": connection.ssl_enabled,
        "created_by": current_user.sub,
        "allowed_operations": json.dumps(connection.allowed_operations)
    })
    
    db.commit()
    connection_id = result.fetchone()[0]
    
    return {"id": connection_id}


# ... Rest of endpoints (add tenant_id: str = Depends(get_tenant_id) to each)