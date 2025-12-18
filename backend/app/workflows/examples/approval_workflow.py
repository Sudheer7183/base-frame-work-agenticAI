"""Example: Approval workflow with HITL"""

import logging
from app.workflows.base import BaseWorkflow, WorkflowState
from app.workflows.nodes import (
    input_validation_node,
    llm_processing_node,
    hitl_gate_node,
    output_formatting_node,
    error_handling_node
)

logger = logging.getLogger(__name__)


class ApprovalWorkflow(BaseWorkflow):
    """
    Simple approval workflow
    
    Steps:
    1. Validate input
    2. Process with LLM
    3. Check if HITL approval is needed
    4. Format output
    """
    
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """Execute the approval workflow"""
        logger.info(f"Starting approval workflow for {state.agent_name}")
        
        try:
            # Step 1: Validate input
            state = await input_validation_node(state)
            if state.error:
                return await error_handling_node(state)
            
            # Step 2: Process with LLM
            state = await llm_processing_node(state)
            if state.error:
                return await error_handling_node(state)
            
            # Step 3: Check HITL requirements
            state = await hitl_gate_node(state)
            
            # Step 4: Format output
            state = await output_formatting_node(state)
            
            logger.info(f"Approval workflow completed for {state.agent_name}")
            return state
            
        except Exception as e:
            logger.error(f"Error in approval workflow: {e}", exc_info=True)
            state.error = str(e)
            return await error_handling_node(state)
