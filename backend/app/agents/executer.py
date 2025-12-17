"""Agent execution engine using LangGraph"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.agent import AgentConfig, AgentExecutionLog
from app.models.hitl import HITLRecord
from app.agents.registry import AgentRegistry
from app.workflows.base import WorkflowState

logger = logging.getLogger(__name__)


class AgentExecutor:
    """
    Agent execution engine
    
    Handles agent execution with LangGraph workflows
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.registry = AgentRegistry()
    
    async def execute(
        self,
        agent_id: int,
        input_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute an agent
        
        Args:
            agent_id: Agent ID to execute
            input_data: Input data for the agent
            user_id: ID of user triggering execution
            
        Returns:
            Execution result with output data
        """
        # Get agent config
        agent = self.db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        if not agent.active:
            raise ValueError(f"Agent {agent.name} is not active")
        
        # Generate execution ID
        execution_id = f"exec_{uuid.uuid4().hex[:16]}"
        start_time = datetime.utcnow()
        
        logger.info(f"Starting execution {execution_id} for agent {agent.name}")
        
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
            # Get workflow
            workflow = self.registry.get_workflow(agent.workflow)
            if not workflow:
                raise ValueError(f"Workflow {agent.workflow} not found")
            
            # Prepare initial state
            initial_state = WorkflowState(
                agent_id=agent_id,
                agent_name=agent.name,
                execution_id=execution_id,
                input_data=input_data,
                config=agent.config,
                requires_hitl=False,
                hitl_record_id=None,
                output_data=None,
                error=None
            )
            
            # Execute workflow
            final_state = await workflow.execute(initial_state)
            
            # Check if HITL is required
            if final_state.requires_hitl:
                logger.info(f"Execution {execution_id} requires HITL approval")
                
                # Create HITL record
                hitl_record = HITLRecord(
                    agent_id=agent_id,
                    agent_name=agent.name,
                    execution_id=execution_id,
                    input_data=input_data,
                    output_data=final_state.output_data,
                    status='pending',
                    priority='normal'
                )
                self.db.add(hitl_record)
                self.db.flush()
                
                final_state.hitl_record_id = hitl_record.id
                
                # Update log
                log.status = "pending_hitl"
                log.output_data = final_state.output_data
            else:
                # Normal completion
                log.status = "completed"
                log.output_data = final_state.output_data
            
            # Calculate duration
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            log.duration_ms = duration_ms
            log.completed_at = end_time
            
            self.db.commit()
            
            logger.info(f"Execution {execution_id} completed in {duration_ms}ms")
            
            return {
                "execution_id": execution_id,
                "status": log.status,
                "output": final_state.output_data,
                "requires_hitl": final_state.requires_hitl,
                "hitl_record_id": final_state.hitl_record_id,
                "duration_ms": duration_ms
            }
            
        except Exception as e:
            logger.error(f"Execution {execution_id} failed: {e}", exc_info=True)
            
            # Update log with error
            log.status = "failed"
            log.error = str(e)
            log.completed_at = datetime.utcnow()
            
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            log.duration_ms = duration_ms
            
            self.db.commit()
            
            raise
