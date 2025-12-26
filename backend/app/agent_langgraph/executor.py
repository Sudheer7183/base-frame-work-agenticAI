# # """
# # LangGraph Executor with AG-UI Streaming
# # Executes LangGraph workflows with event streaming
# # """

# # import logging
# # import uuid
# # from typing import Dict, Any, Optional
# # from datetime import datetime
# # from sqlalchemy.orm import Session

# # from app.models.agent import AgentConfig, AgentExecutionLog
# # from app.agent_langgraph.graph_builder import create_agent_graph
# # from app.agent_langgraph.state import StateManager

# # logger = logging.getLogger(__name__)


# # class LangGraphExecutor:
# #     """
# #     Executes LangGraph workflows
    
# #     Handles graph execution with streaming support
# #     """
    
# #     def __init__(self, db: Session):
# #         self.db = db
# #         self.state_manager = StateManager()
    
# #     async def execute(
# #         self,
# #         agent_id: int,
# #         input_data: Dict[str, Any],
# #         user_id: Optional[int] = None
# #     ) -> Dict[str, Any]:
# #         """
# #         Execute agent workflow
        
# #         Args:
# #             agent_id: Agent ID
# #             input_data: Input data
# #             user_id: User triggering execution
            
# #         Returns:
# #             Execution result
# #         """
# #         # Get agent
# #         agent = self.db.query(AgentConfig).filter(
# #             AgentConfig.id == agent_id
# #         ).first()
        
# #         if not agent:
# #             raise ValueError(f"Agent {agent_id} not found")
        
# #         # Generate execution ID
# #         execution_id = f"exec_{uuid.uuid4().hex[:16]}"
# #         start_time = datetime.utcnow()
        
# #         logger.info(f"Starting LangGraph execution {execution_id} for agent {agent.name}")
        
# #         # Create execution log
# #         log = AgentExecutionLog(
# #             agent_id=agent_id,
# #             execution_id=execution_id,
# #             status="running",
# #             input_data=input_data,
# #             started_by=user_id,
# #             started_at=start_time
# #         )
# #         self.db.add(log)
# #         self.db.commit()
        
# #         try:
# #             # Create graph
# #             graph = create_agent_graph(agent.config)
            
# #             # Initialize state
# #             initial_state = self.state_manager.initialize_state(
# #                 agent_id=agent_id,
# #                 agent_name=agent.name,
# #                 execution_id=execution_id,
# #                 input_data=input_data,
# #                 config=agent.config
# #             )
            
# #             # Configure thread for checkpointing
# #             config = {
# #                 "configurable": {
# #                     "thread_id": input_data.get("thread_id", execution_id)
# #                 }
# #             }
            
# #             # Execute graph
# #             final_state = await graph.ainvoke(initial_state, config=config)
            
# #             # Update log
# #             end_time = datetime.utcnow()
# #             duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
# #             log.status = "completed"
# #             log.output_data = final_state.get("output_data")
# #             log.duration_ms = duration_ms
# #             log.completed_at = end_time
# #             self.db.commit()
            
# #             logger.info(f"Execution {execution_id} completed in {duration_ms}ms")
            
# #             return {
# #                 "execution_id": execution_id,
# #                 "status": "completed",
# #                 "output": final_state.get("output_data"),
# #                 "duration_ms": duration_ms
# #             }
            
# #         except Exception as e:
# #             logger.error(f"Execution {execution_id} failed: {e}", exc_info=True)
            
# #             log.status = "failed"
# #             log.error = str(e)
# #             log.completed_at = datetime.utcnow()
# #             self.db.commit()
            
# #             raise
    
# #     async def execute_with_streaming(
# #         self,
# #         agent_id: int,
# #         input_data: Dict[str, Any],
# #         stream: Any,
# #         user_id: Optional[int] = None
# #     ) -> Dict[str, Any]:
# #         """
# #         Execute agent with AG-UI event streaming
        
# #         Args:
# #             agent_id: Agent ID
# #             input_data: Input data
# #             stream: AGUIStreamManager instance
# #             user_id: User ID
            
# #         Returns:
# #             Execution result
# #         """
# #         # Get agent
# #         agent = self.db.query(AgentConfig).filter(
# #             AgentConfig.id == agent_id
# #         ).first()
        
# #         if not agent:
# #             raise ValueError(f"Agent {agent_id} not found")
        
# #         # Generate execution ID
# #         execution_id = f"exec_{uuid.uuid4().hex[:16]}"
# #         start_time = datetime.utcnow()
        
# #         # Create graph
# #         graph = create_agent_graph(agent.config)
        
# #         # Initialize state
# #         initial_state = self.state_manager.initialize_state(
# #             agent_id=agent_id,
# #             agent_name=agent.name,
# #             execution_id=execution_id,
# #             input_data=input_data,
# #             config=agent.config
# #         )
        
# #         # Configure for streaming
# #         config = {
# #             "configurable": {
# #                 "thread_id": input_data.get("thread_id", execution_id)
# #             }
# #         }
        
# #         # Stream execution
# #         from app.agui.events import create_message_event, create_state_event
        
# #         final_state = None
# #         async for event in graph.astream_events(initial_state, config=config, version="v1"):
# #             event_type = event.get("event")
            
# #             # Emit AG-UI events based on LangGraph events
# #             if event_type == "on_chat_model_stream":
# #                 # Stream LLM tokens
# #                 data = event.get("data", {})
# #                 chunk = data.get("chunk")
# #                 if chunk and hasattr(chunk, "content"):
# #                     stream.emit_event(
# #                         create_message_event(
# #                             content=chunk.content,
# #                             role="assistant"
# #                         )
# #                     )
            
# #             elif event_type == "on_chat_model_end":
# #                 # Model completed
# #                 pass
            
# #             elif event_type == "on_chain_end":
# #                 # Node completed
# #                 final_state = event.get("data", {}).get("output")
        
# #         # Calculate duration
# #         end_time = datetime.utcnow()
# #         duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
# #         return {
# #             "execution_id": execution_id,
# #             "status": "completed",
# #             "output": final_state.get("output_data") if final_state else {},
# #             "duration_ms": duration_ms
# #         }

# """
# Async LangGraph Executor - P1 Fix
# Fully asynchronous agent execution with streaming support
# """

# import asyncio
# import logging
# import uuid
# from typing import Dict, Any, Optional, AsyncGenerator
# from datetime import datetime
# from sqlalchemy.orm import Session
# from sqlalchemy.ext.asyncio import AsyncSession

# from app.models.agent import AgentConfig, AgentExecutionLog
# from app.agent_langgraph.graph_builder import create_agent_graph
# from app.agent_langgraph.state import StateManager
# from app.core.audit import AuditLogger
# from app.core.notifications import NotificationService

# logger = logging.getLogger(__name__)


# class AsyncLangGraphExecutor:
#     """
#     Fully asynchronous LangGraph workflow executor
    
#     Features:
#     - Async execution with proper await patterns
#     - Event streaming support
#     - Audit logging integration
#     - Notification system integration
#     - Proper error handling and recovery
#     """
    
#     def __init__(self, db: Session, audit_logger: Optional[AuditLogger] = None,
#                  notification_service: Optional[NotificationService] = None):
#         self.db = db
#         self.state_manager = StateManager()
#         self.audit_logger = audit_logger or AuditLogger(db)
#         self.notification_service = notification_service or NotificationService()
    
#     async def execute(
#         self,
#         agent_id: int,
#         input_data: Dict[str, Any],
#         user_id: Optional[int] = None,
#         stream: bool = False
#     ) -> Dict[str, Any]:
#         """
#         Execute agent workflow asynchronously
        
#         Args:
#             agent_id: Agent ID
#             input_data: Input data
#             user_id: User triggering execution
#             stream: Whether to stream events
            
#         Returns:
#             Execution result
#         """
#         # Get agent
#         agent = await asyncio.to_thread(
#             self.db.query(AgentConfig).filter(
#                 AgentConfig.id == agent_id
#             ).first
#         )
        
#         if not agent:
#             raise ValueError(f"Agent {agent_id} not found")
        
#         if not agent.active:
#             raise ValueError(f"Agent {agent.name} is not active")
        
#         # Generate execution ID
#         execution_id = f"exec_{uuid.uuid4().hex[:16]}"
#         start_time = datetime.utcnow()
        
#         logger.info(f"Starting async execution {execution_id} for agent {agent.name}")
        
#         # Audit log - execution started
#         await self.audit_logger.log_async(
#             action="agent.execution.started",
#             resource_type="agent",
#             resource_id=str(agent_id),
#             user_id=user_id,
#             details={
#                 "execution_id": execution_id,
#                 "agent_name": agent.name,
#                 "input_size": len(str(input_data))
#             }
#         )
        
#         # Create execution log
#         log = AgentExecutionLog(
#             agent_id=agent_id,
#             execution_id=execution_id,
#             status="running",
#             input_data=input_data,
#             started_by=user_id,
#             started_at=start_time
#         )
#         await asyncio.to_thread(self.db.add, log)
#         await asyncio.to_thread(self.db.commit)
        
#         try:
#             # Create graph
#             graph = await asyncio.to_thread(create_agent_graph, agent.config)
            
#             # Initialize state
#             initial_state = await asyncio.to_thread(
#                 self.state_manager.initialize_state,
#                 agent_id=agent_id,
#                 agent_name=agent.name,
#                 execution_id=execution_id,
#                 input_data=input_data,
#                 config=agent.config
#             )
            
#             # Configure thread for checkpointing
#             config = {
#                 "configurable": {
#                     "thread_id": input_data.get("thread_id", execution_id)
#                 }
#             }
            
#             # Execute graph asynchronously
#             final_state = await graph.ainvoke(initial_state, config=config)
            
#             # Update log
#             end_time = datetime.utcnow()
#             duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
#             log.status = "completed"
#             log.output_data = final_state.get("output_data")
#             log.duration_ms = duration_ms
#             log.completed_at = end_time
#             await asyncio.to_thread(self.db.commit)
            
#             # Audit log - execution completed
#             await self.audit_logger.log_async(
#                 action="agent.execution.completed",
#                 resource_type="agent",
#                 resource_id=str(agent_id),
#                 user_id=user_id,
#                 details={
#                     "execution_id": execution_id,
#                     "duration_ms": duration_ms,
#                     "status": "completed"
#                 }
#             )
            
#             # Send notification on completion
#             if self.notification_service:
#                 await self.notification_service.send_async(
#                     user_id=user_id,
#                     notification_type="agent_execution_completed",
#                     title=f"Agent {agent.name} completed",
#                     message=f"Execution {execution_id} completed in {duration_ms}ms",
#                     data={
#                         "agent_id": agent_id,
#                         "execution_id": execution_id,
#                         "duration_ms": duration_ms
#                     }
#                 )
            
#             logger.info(f"Async execution {execution_id} completed in {duration_ms}ms")
            
#             return {
#                 "execution_id": execution_id,
#                 "status": "completed",
#                 "output": final_state.get("output_data"),
#                 "duration_ms": duration_ms,
#                 "agent_name": agent.name
#             }
            
#         except Exception as e:
#             logger.error(f"Async execution {execution_id} failed: {e}", exc_info=True)
            
#             # Update log
#             log.status = "failed"
#             log.error = str(e)
#             log.completed_at = datetime.utcnow()
#             await asyncio.to_thread(self.db.commit)
            
#             # Audit log - execution failed
#             await self.audit_logger.log_async(
#                 action="agent.execution.failed",
#                 resource_type="agent",
#                 resource_id=str(agent_id),
#                 user_id=user_id,
#                 details={
#                     "execution_id": execution_id,
#                     "error": str(e),
#                     "error_type": type(e).__name__
#                 }
#             )
            
#             # Send error notification
#             if self.notification_service:
#                 await self.notification_service.send_async(
#                     user_id=user_id,
#                     notification_type="agent_execution_failed",
#                     title=f"Agent {agent.name} failed",
#                     message=f"Execution {execution_id} failed: {str(e)}",
#                     data={
#                         "agent_id": agent_id,
#                         "execution_id": execution_id,
#                         "error": str(e)
#                     },
#                     priority="high"
#                 )
            
#             raise
    
#     async def execute_with_streaming(
#         self,
#         agent_id: int,
#         input_data: Dict[str, Any],
#         user_id: Optional[int] = None
#     ) -> AsyncGenerator[Dict[str, Any], None]:
#         """
#         Execute agent with event streaming
        
#         Args:
#             agent_id: Agent ID
#             input_data: Input data
#             user_id: User triggering execution
            
#         Yields:
#             Execution events
#         """
#         # Get agent
#         agent = await asyncio.to_thread(
#             self.db.query(AgentConfig).filter(
#                 AgentConfig.id == agent_id
#             ).first
#         )
        
#         if not agent:
#             raise ValueError(f"Agent {agent_id} not found")
        
#         execution_id = f"exec_{uuid.uuid4().hex[:16]}"
#         start_time = datetime.utcnow()
        
#         # Yield start event
#         yield {
#             "type": "execution_started",
#             "execution_id": execution_id,
#             "agent_id": agent_id,
#             "agent_name": agent.name,
#             "timestamp": start_time.isoformat()
#         }
        
#         try:
#             # Create graph
#             graph = await asyncio.to_thread(create_agent_graph, agent.config)
            
#             # Initialize state
#             initial_state = await asyncio.to_thread(
#                 self.state_manager.initialize_state,
#                 agent_id=agent_id,
#                 agent_name=agent.name,
#                 execution_id=execution_id,
#                 input_data=input_data,
#                 config=agent.config
#             )
            
#             config = {
#                 "configurable": {
#                     "thread_id": input_data.get("thread_id", execution_id)
#                 }
#             }
            
#             # Stream execution
#             async for event in graph.astream_events(initial_state, config=config, version="v2"):
#                 # Transform and yield event
#                 yield {
#                     "type": "execution_event",
#                     "execution_id": execution_id,
#                     "event": event,
#                     "timestamp": datetime.utcnow().isoformat()
#                 }
            
#             # Final state
#             final_state = await graph.ainvoke(initial_state, config=config)
            
#             end_time = datetime.utcnow()
#             duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
#             # Yield completion event
#             yield {
#                 "type": "execution_completed",
#                 "execution_id": execution_id,
#                 "status": "completed",
#                 "output": final_state.get("output_data"),
#                 "duration_ms": duration_ms,
#                 "timestamp": end_time.isoformat()
#             }
            
#         except Exception as e:
#             logger.error(f"Streaming execution {execution_id} failed: {e}", exc_info=True)
            
#             # Yield error event
#             yield {
#                 "type": "execution_failed",
#                 "execution_id": execution_id,
#                 "error": str(e),
#                 "error_type": type(e).__name__,
#                 "timestamp": datetime.utcnow().isoformat()
#             }
            
#             raise
    
#     async def cancel_execution(self, execution_id: str, user_id: Optional[int] = None):
#         """
#         Cancel a running execution
        
#         Args:
#             execution_id: Execution ID to cancel
#             user_id: User requesting cancellation
#         """
#         logger.info(f"Cancelling execution {execution_id}")
        
#         # Find execution log
#         log = await asyncio.to_thread(
#             self.db.query(AgentExecutionLog).filter(
#                 AgentExecutionLog.execution_id == execution_id
#             ).first
#         )
        
#         if not log:
#             raise ValueError(f"Execution {execution_id} not found")
        
#         if log.status != "running":
#             raise ValueError(f"Execution {execution_id} is not running (status: {log.status})")
        
#         # Update status
#         log.status = "cancelled"
#         log.completed_at = datetime.utcnow()
#         await asyncio.to_thread(self.db.commit)
        
#         # Audit log
#         await self.audit_logger.log_async(
#             action="agent.execution.cancelled",
#             resource_type="agent",
#             resource_id=str(log.agent_id),
#             user_id=user_id,
#             details={
#                 "execution_id": execution_id,
#                 "cancelled_by": user_id
#             }
#         )
        
#         logger.info(f"Execution {execution_id} cancelled successfully")



"""
LangGraph Executor with AG-UI Streaming
Async execution with event streaming support
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.agent import AgentConfig, AgentExecutionLog
from app.agent_langgraph.graph_builder import create_agent_graph
from app.agent_langgraph.state import StateManager
from app.agui.streaming import AGUIStreamManager
from app.agui.transformer import EventTransformer
from app.agui.events import (
    create_agent_status_event,
    create_completion_event,
    create_error_event
)

logger = logging.getLogger(__name__)


class AsyncLangGraphExecutor:
    """
    Async LangGraph executor with AG-UI streaming
    
    Features:
    - Fully async execution
    - Event streaming via AG-UI protocol
    - Error handling and recovery
    - Execution logging
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.state_manager = StateManager()
    
    async def execute_with_streaming(
        self,
        agent_id: int,
        input_data: Dict[str, Any],
        stream: AGUIStreamManager,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute agent with AG-UI streaming
        
        Args:
            agent_id: Agent ID
            input_data: Input data including messages, thread_id
            stream: Stream manager for events
            user_id: User triggering execution
            
        Returns:
            Execution result with output and metadata
        """
        # Get agent
        agent = await asyncio.to_thread(
            lambda: self.db.query(AgentConfig).filter(
                AgentConfig.id == agent_id
            ).first()
        )
        
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        if not agent.active:
            raise ValueError(f"Agent {agent.name} is not active")
        
        # Generate execution ID
        execution_id = f"exec_{uuid.uuid4().hex[:16]}"
        start_time = datetime.utcnow()
        
        logger.info(f"Starting streaming execution {execution_id} for agent {agent.name}")
        
        # Set stream ID
        stream.stream_id = execution_id
        
        # Create execution log
        log = AgentExecutionLog(
            agent_id=agent_id,
            execution_id=execution_id,
            status="running",
            input_data=input_data,
            started_by=user_id,
            started_at=start_time
        )
        await asyncio.to_thread(lambda: (self.db.add(log), self.db.commit()))
        
        try:
            # Send status event
            await stream.emit_event(
                create_agent_status_event(
                    status="running",
                    message=f"Agent {agent.name} execution started"
                )
            )
            
            # Create graph
            graph = await asyncio.to_thread(
                create_agent_graph,
                agent.config
            )
            
            # Initialize state
            initial_state = await asyncio.to_thread(
                self.state_manager.initialize_state,
                agent_id=agent_id,
                agent_name=agent.name,
                execution_id=execution_id,
                input_data=input_data,
                config=agent.config
            )
            
            # Configure for streaming with thread_id
            config = {
                "configurable": {
                    "thread_id": input_data.get("thread_id", execution_id)
                }
            }
            
            # Create event transformer
            transformer = EventTransformer()
            
            # Stream execution with LangGraph
            final_state = None
            
            async for event in graph.astream_events(
                initial_state,
                config=config,
                version="v2"  # Use v2 for better event structure
            ):
                # Transform LangGraph event to AG-UI event
                agui_event = transformer.transform_langgraph_event(event)
                
                if agui_event:
                    await stream.emit_event(agui_event)
                
                # Capture final state from chain_end events
                if event.get("event") == "on_chain_end":
                    output = event.get("data", {}).get("output")
                    if output:
                        final_state = output
            
            # If no final state captured, invoke once to get it
            if not final_state:
                final_state = await graph.ainvoke(initial_state, config=config)
            
            # Calculate duration
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Update log
            log.status = "completed"
            log.output_data = final_state.get("output_data") if isinstance(final_state, dict) else final_state
            log.duration_ms = duration_ms
            log.completed_at = end_time
            await asyncio.to_thread(self.db.commit)
            
            logger.info(f"Execution {execution_id} completed in {duration_ms}ms")
            
            # Send completion event
            output = final_state.get("output_data") if isinstance(final_state, dict) else final_state
            await stream.emit_event(
                create_completion_event(
                    final_output=output,
                    metadata={
                        "execution_id": execution_id,
                        "duration_ms": duration_ms,
                        "agent_name": agent.name
                    }
                )
            )
            
            return {
                "execution_id": execution_id,
                "status": "completed",
                "output": output,
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            logger.error(f"Execution {execution_id} failed: {e}", exc_info=True)
            
            # Update log
            log.status = "failed"
            log.error = str(e)
            log.completed_at = datetime.utcnow()
            await asyncio.to_thread(self.db.commit)
            
            # Send error event
            await stream.emit_event(
                create_error_event(
                    error_message=str(e),
                    error_code="EXECUTION_ERROR",
                    recoverable=False
                )
            )
            
            raise