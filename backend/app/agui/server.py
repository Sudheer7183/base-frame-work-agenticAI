# """
# AG-UI Server Implementation
# FastAPI endpoints for AG-UI protocol
# """

# import logging
# from typing import Dict, Any
# from fastapi import APIRouter, Depends, HTTPException
# from fastapi.responses import StreamingResponse
# from sqlalchemy.orm import Session
# from pydantic import BaseModel

# from app.core.database import get_db
# from app.core.security import get_current_user, TokenData
# from app.models.agent import AgentConfig
# from .streaming import AGUIStreamManager
# from .events import (
#     create_message_event,
#     create_agent_status_event,
#     create_completion_event,
#     create_error_event
# )
# from app.agent_langgraph.executor import AsyncLangGraphExecutor

# logger = logging.getLogger(__name__)


# class AGUIRunRequest(BaseModel):
#     """AG-UI run request"""
#     threadId: str
#     messages: list
#     state: Dict[str, Any] = {}


# class AGUIServer:
#     """
#     AG-UI Protocol Server
    
#     Handles AG-UI compliant requests and streaming
#     """
    
#     def __init__(self, db: Session):
#         self.db = db
#         self.executor = LangGraphExecutor(db)
    
#     async def run_agent_stream(
#         self,
#         agent_id: int,
#         request: AGUIRunRequest,
#         user: TokenData
#     ) -> AGUIStreamManager:
#         """
#         Run agent with AG-UI streaming
        
#         Args:
#             agent_id: Agent ID
#             request: AG-UI run request
#             user: Current user
            
#         Returns:
#             Stream manager for SSE streaming
#         """
#         # Create stream manager
#         stream = AGUIStreamManager()
        
#         try:
#             # Send status event
#             stream.emit_event(
#                 create_agent_status_event("running", "Agent execution started")
#             )
            
#             # Get agent
#             agent = self.db.query(AgentConfig).filter(
#                 AgentConfig.id == agent_id
#             ).first()
            
#             if not agent or not agent.active:
#                 raise ValueError(f"Agent {agent_id} not found or inactive")
            
#             # Prepare input from AG-UI request
#             input_data = {
#                 "messages": request.messages,
#                 "thread_id": request.threadId,
#                 "state": request.state
#             }
            
#             # Send initial message event
#             if request.messages:
#                 last_message = request.messages[-1]
#                 stream.emit_event(
#                     create_message_event(
#                         content=last_message.get("content", ""),
#                         role=last_message.get("role", "user")
#                     )
#                 )
            
#             # Execute agent with LangGraph
#             result = await self.executor.execute_with_streaming(
#                 agent_id=agent_id,
#                 input_data=input_data,
#                 stream=stream,
#                 user_id=user.sub if hasattr(user, 'sub') else None
#             )
            
#             # Send completion event
#             stream.emit_event(
#                 create_completion_event(
#                     final_output=result["output"],
#                     metadata={
#                         "execution_id": result["execution_id"],
#                         "duration_ms": result.get("duration_ms")
#                     }
#                 )
#             )
            
#         except Exception as e:
#             logger.error(f"Error in AG-UI agent execution: {e}", exc_info=True)
#             stream.emit_event(
#                 create_error_event(
#                     error_message=str(e),
#                     error_code="EXECUTION_ERROR"
#                 )
#             )
        
#         return stream


# def create_agui_router() -> APIRouter:
#     """
#     Create AG-UI protocol router
    
#     Returns:
#         FastAPI router with AG-UI endpoints
#     """
#     router = APIRouter(prefix="/agui", tags=["AG-UI"])
    
#     @router.post("/agents/{agent_id}/run")
#     async def run_agent(
#         agent_id: int,
#         request: AGUIRunRequest,
#         db: Session = Depends(get_db),
#         user: TokenData = Depends(get_current_user)
#     ):
#         """
#         Run agent with AG-UI protocol
        
#         Streams events via Server-Sent Events (SSE)
#         """
#         server = AGUIServer(db)
#         stream = await server.run_agent_stream(agent_id, request, user)
        
#         return StreamingResponse(
#             stream.stream_events(),
#             media_type="text/event-stream",
#             headers={
#                 "Cache-Control": "no-cache",
#                 "Connection": "keep-alive",
#                 "X-Accel-Buffering": "no"
#             }
#         )
    
#     @router.get("/agents/{agent_id}/state/{thread_id}")
#     async def get_agent_state(
#         agent_id: int,
#         thread_id: str,
#         db: Session = Depends(get_db),
#         user: TokenData = Depends(get_current_user)
#     ):
#         """
#         Get current agent state for a thread
        
#         Used to resume conversations
#         """
#         # TODO: Implement state retrieval from checkpointer
#         return {
#             "thread_id": thread_id,
#             "agent_id": agent_id,
#             "state": {}
#         }
    
#     return router


"""
AG-UI Server Implementation
FastAPI endpoints for AG-UI protocol streaming
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user, TokenData
from app.models.agent import AgentConfig
from .streaming import AGUIStreamManager
from .events import create_message_event, create_error_event
from app.agent_langgraph.executor import AsyncLangGraphExecutor

logger = logging.getLogger(__name__)


class AGUIMessage(BaseModel):
    """AG-UI message format"""
    role: str = Field(..., description="Message role (user, assistant, system)")
    content: str = Field(..., description="Message content")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AGUIRunRequest(BaseModel):
    """AG-UI run request"""
    threadId: str = Field(..., description="Thread ID for conversation continuity")
    messages: list[AGUIMessage] = Field(..., description="Conversation messages")
    state: Dict[str, Any] = Field(default_factory=dict, description="Additional state")


class AGUIServer:
    """
    AG-UI Protocol Server
    
    Handles AG-UI compliant requests and streaming
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.executor = AsyncLangGraphExecutor(db)
    
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
        stream = AGUIStreamManager(heartbeat_interval=30)
        
        # Validate agent
        agent = self.db.query(AgentConfig).filter(
            AgentConfig.id == agent_id
        ).first()
        
        if not agent:
            await stream.emit_event(
                create_error_event(
                    error_message=f"Agent {agent_id} not found",
                    error_code="AGENT_NOT_FOUND",
                    recoverable=False
                )
            )
            return stream
        
        if not agent.active:
            await stream.emit_event(
                create_error_event(
                    error_message=f"Agent {agent.name} is not active",
                    error_code="AGENT_INACTIVE",
                    recoverable=False
                )
            )
            return stream
        
        try:
            # Prepare input from AG-UI request
            input_data = {
                "messages": [msg.dict() for msg in request.messages],
                "thread_id": request.threadId,
                "state": request.state
            }
            
            # Echo last user message
            if request.messages:
                last_message = request.messages[-1]
                if last_message.role == "user":
                    await stream.emit_event(
                        create_message_event(
                            content=last_message.content,
                            role="user",
                            metadata=last_message.metadata
                        )
                    )
            
            # Execute agent with streaming
            # This runs in background, emitting events to stream
            import asyncio
            asyncio.create_task(
                self.executor.execute_with_streaming(
                    agent_id=agent_id,
                    input_data=input_data,
                    stream=stream,
                    user_id=getattr(user, 'sub', None)
                )
            )
            
        except Exception as e:
            logger.error(f"Error in AG-UI agent execution: {e}", exc_info=True)
            await stream.emit_event(
                create_error_event(
                    error_message=str(e),
                    error_code="EXECUTION_ERROR",
                    recoverable=False
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
        Run agent with AG-UI protocol streaming
        
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
                "X-Accel-Buffering": "no",  # Disable nginx buffering
                "Access-Control-Allow-Origin": "*",  # CORS for SSE
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
        
        Used to resume conversations or inspect state
        """
        # TODO: Implement state retrieval from LangGraph checkpointer
        # This would query the checkpointer for the given thread_id
        
        return {
            "thread_id": thread_id,
            "agent_id": agent_id,
            "state": {},
            "message": "State retrieval not yet implemented"
        }
    
    @router.post("/agents/{agent_id}/cancel/{thread_id}")
    async def cancel_execution(
        agent_id: int,
        thread_id: str,
        db: Session = Depends(get_db),
        user: TokenData = Depends(get_current_user)
    ):
        """
        Cancel an ongoing execution
        
        Attempts to gracefully stop the execution for the given thread
        """
        # TODO: Implement execution cancellation
        # This would need a registry of active executions
        
        return {
            "thread_id": thread_id,
            "agent_id": agent_id,
            "status": "cancellation_requested",
            "message": "Cancellation not yet implemented"
        }
    
    return router