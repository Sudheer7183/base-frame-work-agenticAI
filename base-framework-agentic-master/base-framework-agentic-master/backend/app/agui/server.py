"""
AG-UI Server Implementation
FastAPI endpoints for AG-UI protocol
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user, TokenData
from app.models.agent import AgentConfig
from .streaming import AGUIStreamManager
from .events import (
    create_message_event,
    create_agent_status_event,
    create_completion_event,
    create_error_event
)
from app.langgraph.executor import LangGraphExecutor

logger = logging.getLogger(__name__)


class AGUIRunRequest(BaseModel):
    """AG-UI run request"""
    threadId: str
    messages: list
    state: Dict[str, Any] = {}


class AGUIServer:
    """
    AG-UI Protocol Server
    
    Handles AG-UI compliant requests and streaming
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.executor = LangGraphExecutor(db)
    
    async def run_agent_stream(
        self,
        agent_id: int,
        request: AGUIRunRequest,
        user: TokenData
    ) -> AGUIStreamManager:
        """
        Run agent with AG-UI streaming
        
        Args:
            agent_id: Agent ID
            request: AG-UI run request
            user: Current user
            
        Returns:
            Stream manager for SSE streaming
        """
        # Create stream manager
        stream = AGUIStreamManager()
        
        try:
            # Send status event
            stream.emit_event(
                create_agent_status_event("running", "Agent execution started")
            )
            
            # Get agent
            agent = self.db.query(AgentConfig).filter(
                AgentConfig.id == agent_id
            ).first()
            
            if not agent or not agent.active:
                raise ValueError(f"Agent {agent_id} not found or inactive")
            
            # Prepare input from AG-UI request
            input_data = {
                "messages": request.messages,
                "thread_id": request.threadId,
                "state": request.state
            }
            
            # Send initial message event
            if request.messages:
                last_message = request.messages[-1]
                stream.emit_event(
                    create_message_event(
                        content=last_message.get("content", ""),
                        role=last_message.get("role", "user")
                    )
                )
            
            # Execute agent with LangGraph
            result = await self.executor.execute_with_streaming(
                agent_id=agent_id,
                input_data=input_data,
                stream=stream,
                user_id=user.sub if hasattr(user, 'sub') else None
            )
            
            # Send completion event
            stream.emit_event(
                create_completion_event(
                    final_output=result["output"],
                    metadata={
                        "execution_id": result["execution_id"],
                        "duration_ms": result.get("duration_ms")
                    }
                )
            )
            
        except Exception as e:
            logger.error(f"Error in AG-UI agent execution: {e}", exc_info=True)
            stream.emit_event(
                create_error_event(
                    error_message=str(e),
                    error_code="EXECUTION_ERROR"
                )
            )
        
        return stream


def create_agui_router() -> APIRouter:
    """
    Create AG-UI protocol router
    
    Returns:
        FastAPI router with AG-UI endpoints
    """
    router = APIRouter(prefix="/agui", tags=["AG-UI"])
    
    @router.post("/agents/{agent_id}/run")
    async def run_agent(
        agent_id: int,
        request: AGUIRunRequest,
        db: Session = Depends(get_db),
        user: TokenData = Depends(get_current_user)
    ):
        """
        Run agent with AG-UI protocol
        
        Streams events via Server-Sent Events (SSE)
        """
        server = AGUIServer(db)
        stream = await server.run_agent_stream(agent_id, request, user)
        
        return StreamingResponse(
            stream.stream_events(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    
    @router.get("/agents/{agent_id}/state/{thread_id}")
    async def get_agent_state(
        agent_id: int,
        thread_id: str,
        db: Session = Depends(get_db),
        user: TokenData = Depends(get_current_user)
    ):
        """
        Get current agent state for a thread
        
        Used to resume conversations
        """
        # TODO: Implement state retrieval from checkpointer
        return {
            "thread_id": thread_id,
            "agent_id": agent_id,
            "state": {}
        }
    
    return router
