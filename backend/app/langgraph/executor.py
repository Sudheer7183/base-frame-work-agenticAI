"""
LangGraph Executor with AG-UI Streaming
Executes LangGraph workflows with event streaming
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.agent import AgentConfig, AgentExecutionLog
from app.langgraph.graph_builder import create_agent_graph
from app.langgraph.state import StateManager

logger = logging.getLogger(__name__)


class LangGraphExecutor:
    """
    Executes LangGraph workflows
    
    Handles graph execution with streaming support
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.state_manager = StateManager()
    
    async def execute(
        self,
        agent_id: int,
        input_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute agent workflow
        
        Args:
            agent_id: Agent ID
            input_data: Input data
            user_id: User triggering execution
            
        Returns:
            Execution result
        """
        # Get agent
        agent = self.db.query(AgentConfig).filter(
            AgentConfig.id == agent_id
        ).first()
        
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Generate execution ID
        execution_id = f"exec_{uuid.uuid4().hex[:16]}"
        start_time = datetime.utcnow()
        
        logger.info(f"Starting LangGraph execution {execution_id} for agent {agent.name}")
        
        # Create execution log
        log = AgentExecutionLog(
            agent_id=agent_id,
            execution_id=execution_id,
            status="running",
            input_data=input_data,
            started_by=user_id,
            started_at=start_time
        )
        self.db.add(log)
        self.db.commit()
        
        try:
            # Create graph
            graph = create_agent_graph(agent.config)
            
            # Initialize state
            initial_state = self.state_manager.initialize_state(
                agent_id=agent_id,
                agent_name=agent.name,
                execution_id=execution_id,
                input_data=input_data,
                config=agent.config
            )
            
            # Configure thread for checkpointing
            config = {
                "configurable": {
                    "thread_id": input_data.get("thread_id", execution_id)
                }
            }
            
            # Execute graph
            final_state = await graph.ainvoke(initial_state, config=config)
            
            # Update log
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            log.status = "completed"
            log.output_data = final_state.get("output_data")
            log.duration_ms = duration_ms
            log.completed_at = end_time
            self.db.commit()
            
            logger.info(f"Execution {execution_id} completed in {duration_ms}ms")
            
            return {
                "execution_id": execution_id,
                "status": "completed",
                "output": final_state.get("output_data"),
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            logger.error(f"Execution {execution_id} failed: {e}", exc_info=True)
            
            log.status = "failed"
            log.error = str(e)
            log.completed_at = datetime.utcnow()
            self.db.commit()
            
            raise
    
    async def execute_with_streaming(
        self,
        agent_id: int,
        input_data: Dict[str, Any],
        stream: Any,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute agent with AG-UI event streaming
        
        Args:
            agent_id: Agent ID
            input_data: Input data
            stream: AGUIStreamManager instance
            user_id: User ID
            
        Returns:
            Execution result
        """
        # Get agent
        agent = self.db.query(AgentConfig).filter(
            AgentConfig.id == agent_id
        ).first()
        
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Generate execution ID
        execution_id = f"exec_{uuid.uuid4().hex[:16]}"
        start_time = datetime.utcnow()
        
        # Create graph
        graph = create_agent_graph(agent.config)
        
        # Initialize state
        initial_state = self.state_manager.initialize_state(
            agent_id=agent_id,
            agent_name=agent.name,
            execution_id=execution_id,
            input_data=input_data,
            config=agent.config
        )
        
        # Configure for streaming
        config = {
            "configurable": {
                "thread_id": input_data.get("thread_id", execution_id)
            }
        }
        
        # Stream execution
        from app.agui.events import create_message_event, create_state_event
        
        final_state = None
        async for event in graph.astream_events(initial_state, config=config, version="v1"):
            event_type = event.get("event")
            
            # Emit AG-UI events based on LangGraph events
            if event_type == "on_chat_model_stream":
                # Stream LLM tokens
                data = event.get("data", {})
                chunk = data.get("chunk")
                if chunk and hasattr(chunk, "content"):
                    stream.emit_event(
                        create_message_event(
                            content=chunk.content,
                            role="assistant"
                        )
                    )
            
            elif event_type == "on_chat_model_end":
                # Model completed
                pass
            
            elif event_type == "on_chain_end":
                # Node completed
                final_state = event.get("data", {}).get("output")
        
        # Calculate duration
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return {
            "execution_id": execution_id,
            "status": "completed",
            "output": final_state.get("output_data") if final_state else {},
            "duration_ms": duration_ms
        }
