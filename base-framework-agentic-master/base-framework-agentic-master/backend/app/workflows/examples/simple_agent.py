"""Example: Simple agent workflow"""

import logging
from app.workflows.base import BaseWorkflow, WorkflowState

logger = logging.getLogger(__name__)


class SimpleAgentWorkflow(BaseWorkflow):
    """
    Simple agent that echoes input
    
    Useful for testing and examples
    """
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute simple echo workflow"""
        logger.info(f"Starting simple workflow for {state.agent_name}")
        
        # Simply echo the input back
        state.output_data = {
            "message": "Echo response",
            "input": state.input_data,
            "agent": state.agent_name,
            "execution_id": state.execution_id
        }
        
        logger.info(f"Simple workflow completed for {state.agent_name}")
        return state