"""Base workflow definitions"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WorkflowState:
    """Base workflow state"""
    agent_id: int
    agent_name: str
    execution_id: str
    input_data: Dict[str, Any]
    config: Dict[str, Any]
    requires_hitl: bool = False
    hitl_record_id: Optional[int] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaseWorkflow(ABC):
    """
    Base class for all workflows
    
    Subclass this to create custom workflows
    """
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def execute(self, state: WorkflowState) -> WorkflowState:
        """
        Execute the workflow
        
        Args:
            state: Initial workflow state
            
        Returns:
            Final workflow state
        """
        pass
    
    def should_require_hitl(self, state: WorkflowState) -> bool:
        """
        Determine if HITL is required
        
        Override this method to implement custom HITL logic
        """
        return False
    
    async def process_input(self, state: WorkflowState) -> WorkflowState:
        """Process and validate input data"""
        logger.info(f"Processing input for {state.agent_name}")
        return state
    
    async def process_output(self, state: WorkflowState) -> WorkflowState:
        """Process and format output data"""
        logger.info(f"Processing output for {state.agent_name}")
        return state
