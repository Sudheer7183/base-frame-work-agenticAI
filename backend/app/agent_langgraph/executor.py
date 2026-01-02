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



# """
# LangGraph Executor with AG-UI Streaming
# Async execution with event streaming support
# """

# import asyncio
# import logging
# import uuid
# from typing import Dict, Any, Optional
# from datetime import datetime
# from sqlalchemy.orm import Session

# from app.models.agent import AgentConfig, AgentExecutionLog
# from app.agent_langgraph.graph_builder import create_agent_graph
# from app.agent_langgraph.state import StateManager
# from app.agui.streaming import AGUIStreamManager
# from app.agui.transformer import EventTransformer
# from app.agui.events import (
#     create_agent_status_event,
#     create_completion_event,
#     create_error_event
# )

# from datetime import datetime
# from app.services.cost_tracker import AsyncCostTracker
# from app.services.token_parser import TokenParser
# from app.services.self_hosted_calculator import SelfHostedCostCalculator  # Optional

# logger = logging.getLogger(__name__)


# class AsyncLangGraphExecutor:
#     """
#     Async LangGraph executor with AG-UI streaming
    
#     Features:
#     - Fully async execution
#     - Event streaming via AG-UI protocol
#     - Error handling and recovery
#     - Execution logging
#     """
    
#     def __init__(self, db: Session):
#         self.db = db
#         self.state_manager = StateManager()
#         self.cost_tracker = AsyncCostTracker(db)
#         self.token_parser = TokenParser()
#         self.self_hosted_calc = SelfHostedCostCalculator(db)  # Optional
    
#     async def execute_with_streaming(
#         self,
#         agent_id: int,
#         input_data: Dict[str, Any],
#         stream: AGUIStreamManager,
#         user_id: Optional[int] = None
#     ) -> Dict[str, Any]:
#         """
#         Execute agent with AG-UI streaming
        
#         Args:
#             agent_id: Agent ID
#             input_data: Input data including messages, thread_id
#             stream: Stream manager for events
#             user_id: User triggering execution
            
#         Returns:
#             Execution result with output and metadata
#         """
#         # Get agent
#         # agent = await asyncio.to_thread(
#         #     lambda: self.db.query(AgentConfig).filter(
#         #         AgentConfig.id == agent_id
#         #     ).first()
#         # )

#         agent = self.db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
        
#         # Get builder config
#         builder_config = self.db.execute(text("""
#             SELECT * FROM agent_builder_configs 
#             WHERE agent_id = :agent_id 
#             ORDER BY version DESC LIMIT 1
#         """), {"agent_id": agent_id}).fetchone()
        
#         if builder_config:
#             # Use builder config to create LangGraph
#             config = self._merge_configs(agent.config, dict(builder_config))
#         else:
#             config = agent.config
        
#         if not agent:
#             raise ValueError(f"Agent {agent_id} not found")
        
#         if not agent.active:
#             raise ValueError(f"Agent {agent.name} is not active")
        
#         # Generate execution ID
#         execution_id = f"exec_{uuid.uuid4().hex[:16]}"
#         start_time = datetime.utcnow()
        
#         logger.info(f"Starting streaming execution {execution_id} for agent {agent.name}")
        
#         # Set stream ID
#         stream.stream_id = execution_id
        
#         # Create execution log
#         log = AgentExecutionLog(
#             agent_id=agent_id,
#             execution_id=execution_id,
#             status="running",
#             input_data=input_data,
#             started_by=user_id,
#             started_at=start_time
#         )
#         await asyncio.to_thread(lambda: (self.db.add(log), self.db.commit()))
        
#         try:
#             # Send status event
#             await stream.emit_event(
#                 create_agent_status_event(
#                     status="running",
#                     message=f"Agent {agent.name} execution started"
#                 )
#             )
            
#             # Create graph
#             graph = await asyncio.to_thread(
#                 create_agent_graph,
#                 agent.config
#             )
            
#             # Initialize state
#             initial_state = await asyncio.to_thread(
#                 self.state_manager.initialize_state,
#                 agent_id=agent_id,
#                 agent_name=agent.name,
#                 execution_id=execution_id,
#                 input_data=input_data,
#                 config=agent.config
#             )
            
#             # Configure for streaming with thread_id
#             config = {
#                 "configurable": {
#                     "thread_id": input_data.get("thread_id", execution_id)
#                 }
#             }
            
#             # Create event transformer
#             transformer = EventTransformer()
            
#             # Stream execution with LangGraph
#             final_state = None
            
#             async for event in graph.astream_events(
#                 initial_state,
#                 config=config,
#                 version="v2"  # Use v2 for better event structure
#             ):
#                 # Transform LangGraph event to AG-UI event
#                 agui_event = transformer.transform_langgraph_event(event)
                
#                 if agui_event:
#                     await stream.emit_event(agui_event)
                
#                 # Capture final state from chain_end events
#                 if event.get("event") == "on_chain_end":
#                     output = event.get("data", {}).get("output")
#                     if output:
#                         final_state = output
            
#             # If no final state captured, invoke once to get it
#             if not final_state:
#                 final_state = await graph.ainvoke(initial_state, config=config)
            
#             # Calculate duration
#             end_time = datetime.utcnow()
#             duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
#             # Update log
#             log.status = "completed"
#             log.output_data = final_state.get("output_data") if isinstance(final_state, dict) else final_state
#             log.duration_ms = duration_ms
#             log.completed_at = end_time
#             await asyncio.to_thread(self.db.commit)
            
#             logger.info(f"Execution {execution_id} completed in {duration_ms}ms")
            
#             # Send completion event
#             output = final_state.get("output_data") if isinstance(final_state, dict) else final_state
#             await stream.emit_event(
#                 create_completion_event(
#                     final_output=output,
#                     metadata={
#                         "execution_id": execution_id,
#                         "duration_ms": duration_ms,
#                         "agent_name": agent.name
#                     }
#                 )
#             )
            
#             return {
#                 "execution_id": execution_id,
#                 "status": "completed",
#                 "output": output,
#                 "duration_ms": duration_ms
#             }
            
#         except Exception as e:
#             logger.error(f"Execution {execution_id} failed: {e}", exc_info=True)
            
#             # Update log
#             log.status = "failed"
#             log.error = str(e)
#             log.completed_at = datetime.utcnow()
#             await asyncio.to_thread(self.db.commit)
            
#             # Send error event
#             await stream.emit_event(
#                 create_error_event(
#                     error_message=str(e),
#                     error_code="EXECUTION_ERROR",
#                     recoverable=False
#                 )
#             )
            
#             raise


"""
LangGraph Executor with AG-UI Streaming + Computational Audit
Async execution with event streaming and cost tracking support
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

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
    Async LangGraph executor with AG-UI streaming and cost tracking
    
    Features:
    - Fully async execution
    - Event streaming via AG-UI protocol
    - Automatic LLM cost tracking
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
        Execute agent with AG-UI streaming and cost tracking
        
        Args:
            agent_id: Agent ID
            input_data: Input data including messages, thread_id
            stream: Stream manager for events
            user_id: User triggering execution
            
        Returns:
            Execution result with output and metadata
        """
        # Get agent
        agent = self.db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
        
        # Get builder config
        builder_config = self.db.execute(text("""
            SELECT * FROM agent_builder_configs 
            WHERE agent_id = :agent_id 
            ORDER BY version DESC LIMIT 1
        """), {"agent_id": agent_id}).fetchone()
        
        if builder_config:
            # Use builder config to create LangGraph
            config = self._merge_configs(agent.config, dict(builder_config))
        else:
            config = agent.config
        
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
        
        # Initialize cost tracking for this execution
        total_llm_cost = 0.0
        total_llm_calls = 0
        total_tokens = 0
        
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
            current_stage = "initialization"
            
            async for event in graph.astream_events(
                initial_state,
                config=config,
                version="v2"  # Use v2 for better event structure
            ):
                # Transform LangGraph event to AG-UI event
                agui_event = transformer.transform_langgraph_event(event)
                
                if agui_event:
                    await stream.emit_event(agui_event)
                
                # Track costs from LLM events
                event_type = event.get("event")
                
                # Update current stage from tags
                tags = event.get("tags", [])
                if tags:
                    current_stage = tags[0]
                
                # Track LLM usage
                if event_type == "on_chat_model_end":
                    cost_data = await self._track_llm_usage(
                        event=event,
                        execution_id=execution_id,
                        agent_id=agent_id,
                        stage_name=current_stage
                    )
                    
                    if cost_data:
                        total_llm_cost += cost_data['cost']
                        total_llm_calls += 1
                        total_tokens += cost_data['total_tokens']
                
                # Capture final state from chain_end events
                if event_type == "on_chain_end":
                    output = event.get("data", {}).get("output")
                    if output:
                        final_state = output
            
            # If no final state captured, invoke once to get it
            if not final_state:
                final_state = await graph.ainvoke(initial_state, config=config)
            
            # Calculate duration
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Finalize cost tracking - create cost summary
            await self._finalize_execution_costs(
                execution_id=execution_id,
                agent_id=agent_id,
                total_llm_cost=total_llm_cost,
                total_llm_calls=total_llm_calls,
                total_tokens=total_tokens,
                started_at=start_time,
                completed_at=end_time
            )
            
            # Update log
            log.status = "completed"
            log.output_data = final_state.get("output_data") if isinstance(final_state, dict) else final_state
            log.duration_ms = duration_ms
            log.completed_at = end_time
            await asyncio.to_thread(self.db.commit)
            
            logger.info(
                f"Execution {execution_id} completed in {duration_ms}ms | "
                f"Cost: ${total_llm_cost:.6f} | Tokens: {total_tokens} | LLM calls: {total_llm_calls}"
            )
            
            # Send completion event with cost metadata
            output = final_state.get("output_data") if isinstance(final_state, dict) else final_state
            await stream.emit_event(
                create_completion_event(
                    final_output=output,
                    metadata={
                        "execution_id": execution_id,
                        "duration_ms": duration_ms,
                        "agent_name": agent.name,
                        "cost_usd": round(total_llm_cost, 6),
                        "total_tokens": total_tokens,
                        "llm_calls": total_llm_calls
                    }
                )
            )
            
            return {
                "execution_id": execution_id,
                "status": "completed",
                "output": output,
                "duration_ms": duration_ms,
                "cost_usd": round(total_llm_cost, 6),
                "total_tokens": total_tokens,
                "llm_calls": total_llm_calls
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
    
    async def _track_llm_usage(
        self,
        event: Dict[str, Any],
        execution_id: str,
        agent_id: int,
        stage_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Track LLM usage from LangGraph events
        
        Automatically extracts token counts and costs from LLM completion events.
        Inserts records into tenant_xxx.computational_audit_usage table.
        
        Args:
            event: LangGraph event data
            execution_id: Current execution ID
            agent_id: Agent ID
            stage_name: Current stage/node name
            
        Returns:
            Dict with cost data or None if no usage to track
        """
        try:
            data = event.get('data', {})
            output = data.get('output', {})
            
            # Extract token usage from various response formats
            usage = (
                output.get('usage_metadata') or 
                output.get('usage') or 
                output.get('token_usage') or 
                {}
            )
            
            if not usage:
                return None
            
            # Parse tokens (handle different naming conventions)
            input_tokens = (
                usage.get('input_tokens') or 
                usage.get('prompt_tokens') or 
                0
            )
            output_tokens = (
                usage.get('output_tokens') or 
                usage.get('completion_tokens') or 
                0
            )
            cache_read_tokens = usage.get('cache_read_tokens', 0)
            cache_write_tokens = usage.get('cache_creation_input_tokens', 0)
            
            total_tokens = input_tokens + output_tokens
            
            if total_tokens == 0:
                return None
            
            # Extract model information
            model_name = (
                output.get('model') or 
                event.get('metadata', {}).get('ls_model_name') or 
                event.get('name', 'unknown')
            )
            
            # Detect provider from model name
            provider = self._extract_provider(model_name)
            
            # Get latency if available
            latency_ms = event.get('metadata', {}).get('duration_ms')
            
            # Get current schema (tenant context)
            schema_result = await asyncio.to_thread(
                lambda: self.db.execute(text("SELECT current_schema()")).scalar()
            )
            current_schema = schema_result
            
            # Calculate cost using database function
            cost_query = text("""
                SELECT public.calculate_llm_cost(
                    :provider,
                    :model,
                    :input_tokens,
                    :output_tokens,
                    CURRENT_DATE
                )
            """)
            
            cost_result = await asyncio.to_thread(
                lambda: self.db.execute(cost_query, {
                    "provider": provider,
                    "model": model_name,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }).scalar()
            )
            
            computed_cost = float(cost_result or 0)
            
            # Get unit costs from pricing table
            pricing_query = text("""
                SELECT 
                    input_cost_per_1k,
                    output_cost_per_1k
                FROM public.model_pricing
                WHERE model_provider = :provider
                    AND model_name = :model
                    AND active = true
                ORDER BY effective_from DESC
                LIMIT 1
            """)
            
            pricing_result = await asyncio.to_thread(
                lambda: self.db.execute(pricing_query, {
                    "provider": provider,
                    "model": model_name
                }).fetchone()
            )
            
            if pricing_result:
                unit_cost_input = float(pricing_result[0])
                unit_cost_output = float(pricing_result[1])
            else:
                # Default to 0 if no pricing found
                unit_cost_input = 0.0
                unit_cost_output = 0.0
                logger.warning(
                    f"No pricing found for {provider}:{model_name}, "
                    f"using $0. Please seed pricing data."
                )
            
            # Insert usage record into computational_audit_usage
            insert_query = text(f"""
                INSERT INTO "{current_schema}".computational_audit_usage (
                    execution_id,
                    agent_id,
                    stage_name,
                    model_provider,
                    model_name,
                    input_tokens,
                    output_tokens,
                    cache_read_tokens,
                    cache_write_tokens,
                    total_tokens,
                    unit_cost_input,
                    unit_cost_output,
                    computed_cost_usd,
                    latency_ms,
                    created_at
                ) VALUES (
                    :execution_id,
                    :agent_id,
                    :stage_name,
                    :provider,
                    :model,
                    :input_tokens,
                    :output_tokens,
                    :cache_read_tokens,
                    :cache_write_tokens,
                    :total_tokens,
                    :unit_cost_input,
                    :unit_cost_output,
                    :computed_cost,
                    :latency_ms,
                    NOW()
                )
            """)
            
            await asyncio.to_thread(
                lambda: self.db.execute(insert_query, {
                    "execution_id": execution_id,
                    "agent_id": agent_id,
                    "stage_name": stage_name,
                    "provider": provider,
                    "model": model_name,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cache_read_tokens": cache_read_tokens,
                    "cache_write_tokens": cache_write_tokens,
                    "total_tokens": total_tokens,
                    "unit_cost_input": unit_cost_input,
                    "unit_cost_output": unit_cost_output,
                    "computed_cost": computed_cost,
                    "latency_ms": latency_ms
                })
            )
            
            await asyncio.to_thread(self.db.commit)
            
            logger.debug(
                f"Tracked LLM usage: {provider}:{model_name} | "
                f"Tokens: {total_tokens} | Cost: ${computed_cost:.6f}"
            )
            
            return {
                'cost': computed_cost,
                'total_tokens': total_tokens,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'provider': provider,
                'model': model_name
            }
            
        except Exception as e:
            logger.error(f"Failed to track LLM usage: {e}", exc_info=True)
            # Don't fail execution if cost tracking fails
            return None
    
    async def _finalize_execution_costs(
        self,
        execution_id: str,
        agent_id: int,
        total_llm_cost: float,
        total_llm_calls: int,
        total_tokens: int,
        started_at: datetime,
        completed_at: datetime
    ):
        """
        Create cost summary record for the execution
        
        Inserts a summary record into computational_audit_cost_summary table.
        
        Args:
            execution_id: Execution ID
            agent_id: Agent ID
            total_llm_cost: Total LLM cost in USD
            total_llm_calls: Number of LLM calls
            total_tokens: Total tokens used
            started_at: Execution start time
            completed_at: Execution end time
        """
        try:
            # Get current schema
            schema_result = await asyncio.to_thread(
                lambda: self.db.execute(text("SELECT current_schema()")).scalar()
            )
            current_schema = schema_result
            
            # Insert cost summary
            insert_query = text(f"""
                INSERT INTO "{current_schema}".computational_audit_cost_summary (
                    execution_id,
                    agent_id,
                    total_llm_cost_usd,
                    total_tokens,
                    total_llm_calls,
                    execution_started_at,
                    execution_completed_at,
                    total_cost_usd,
                    created_at
                ) VALUES (
                    :execution_id,
                    :agent_id,
                    :total_llm_cost,
                    :total_tokens,
                    :total_llm_calls,
                    :started_at,
                    :completed_at,
                    :total_cost,
                    NOW()
                )
                ON CONFLICT (execution_id) DO UPDATE SET
                    total_llm_cost_usd = EXCLUDED.total_llm_cost_usd,
                    total_tokens = EXCLUDED.total_tokens,
                    total_llm_calls = EXCLUDED.total_llm_calls,
                    total_cost_usd = EXCLUDED.total_cost_usd,
                    updated_at = NOW()
            """)
            
            await asyncio.to_thread(
                lambda: self.db.execute(insert_query, {
                    "execution_id": execution_id,
                    "agent_id": agent_id,
                    "total_llm_cost": total_llm_cost,
                    "total_tokens": total_tokens,
                    "total_llm_calls": total_llm_calls,
                    "started_at": started_at,
                    "completed_at": completed_at,
                    "total_cost": total_llm_cost  # Can add HITL/infra costs later
                })
            )
            
            await asyncio.to_thread(self.db.commit)
            
            logger.info(
                f"Finalized cost summary for {execution_id}: "
                f"${total_llm_cost:.6f} | {total_tokens} tokens | {total_llm_calls} calls"
            )
            
        except Exception as e:
            logger.error(f"Failed to finalize execution costs: {e}", exc_info=True)
            # Don't fail execution if cost summary fails
    
    def _extract_provider(self, model_name: str) -> str:
        """
        Extract provider from model name
        
        Args:
            model_name: Model name (e.g., 'gpt-4', 'claude-3-opus')
            
        Returns:
            Provider name (e.g., 'openai', 'anthropic')
        """
        model_lower = model_name.lower()
        
        if 'gpt' in model_lower or 'davinci' in model_lower or 'turbo' in model_lower:
            return 'openai'
        elif 'claude' in model_lower:
            return 'anthropic'
        elif 'gemini' in model_lower or 'palm' in model_lower:
            return 'google'
        elif 'mistral' in model_lower or 'mixtral' in model_lower:
            return 'mistral'
        elif 'llama' in model_lower:
            return 'meta'
        elif 'command' in model_lower:
            return 'cohere'
        else:
            return 'unknown'
    
    def _merge_configs(self, base_config: Dict, builder_config: Dict) -> Dict:
        """
        Merge base agent config with builder config
        
        Args:
            base_config: Base agent configuration
            builder_config: Builder configuration from agent_builder_configs
            
        Returns:
            Merged configuration
        """
        # Simple merge - builder config takes precedence
        merged = base_config.copy()
        merged.update(builder_config)
        return merged


# END OF FILE - Updated executor with computational audit integration