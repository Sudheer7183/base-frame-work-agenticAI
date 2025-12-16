"""Agent management API endpoints"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user, TokenData
from app.core.exceptions import NotFoundException, BadRequestException
from app.models.agent import AgentConfig
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    active_only: bool = Query(True),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    List all agents
    
    - **active_only**: Filter to show only active agents
    - **limit**: Maximum number of results
    - **offset**: Offset for pagination
    """
    query = db.query(AgentConfig)
    
    if active_only:
        query = query.filter(AgentConfig.active == True)
    
    agents = query.offset(offset).limit(limit).all()
    return [AgentResponse(**agent.to_dict()) for agent in agents]


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent_data: AgentCreate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Create a new agent
    
    Requires authentication
    """
    # Check if agent with same name exists
    existing = db.query(AgentConfig).filter(AgentConfig.name == agent_data.name).first()
    if existing:
        raise BadRequestException(f"Agent with name '{agent_data.name}' already exists")
    
    # Create agent
    agent = AgentConfig(
        name=agent_data.name,
        description=agent_data.description,
        workflow=agent_data.workflow,
        config=agent_data.config or {},
        active=agent_data.active,
        created_by=current_user.sub if hasattr(current_user, 'sub') else None
    )
    
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    return AgentResponse(**agent.to_dict())


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get agent by ID"""
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    
    if not agent:
        raise NotFoundException(f"Agent with ID {agent_id} not found")
    
    return AgentResponse(**agent.to_dict())


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_data: AgentUpdate,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Update agent configuration"""
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    
    if not agent:
        raise NotFoundException(f"Agent with ID {agent_id} not found")
    
    # Update fields
    if agent_data.name is not None:
        agent.name = agent_data.name
    if agent_data.description is not None:
        agent.description = agent_data.description
    if agent_data.workflow is not None:
        agent.workflow = agent_data.workflow
    if agent_data.config is not None:
        agent.config = agent_data.config
    if agent_data.active is not None:
        agent.active = agent_data.active
    
    db.commit()
    db.refresh(agent)
    
    return AgentResponse(**agent.to_dict())


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Delete an agent"""
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    
    if not agent:
        raise NotFoundException(f"Agent with ID {agent_id} not found")
    
    db.delete(agent)
    db.commit()


@router.post("/{agent_id}/execute")
async def execute_agent(
    agent_id: int,
    input_data: dict,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Execute an agent
    
    This is a placeholder - implement actual execution logic
    """
    agent = db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
    
    if not agent:
        raise NotFoundException(f"Agent with ID {agent_id} not found")
    
    if not agent.active:
        raise BadRequestException(f"Agent '{agent.name}' is not active")
    
    # TODO: Implement actual agent execution using LangGraph
    return {
        "status": "executed",
        "agent_id": agent_id,
        "agent_name": agent.name,
        "input": input_data,
        "output": {"message": "Execution placeholder - implement actual logic"}
    }