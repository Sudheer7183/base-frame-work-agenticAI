"""Agent and workflow registry"""

import logging
from typing import Dict, Optional, Type
from app.workflows.base import BaseWorkflow
from app.workflows.examples.approval_workflow import ApprovalWorkflow

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Registry for agent workflows
    
    Maps workflow names to workflow classes
    """
    
    def __init__(self):
        self._workflows: Dict[str, Type[BaseWorkflow]] = {}
        self._register_default_workflows()
    
    def _register_default_workflows(self):
        """Register default workflows"""
        self.register_workflow("approval", ApprovalWorkflow)
        logger.info("Registered default workflows")
    
    def register_workflow(self, name: str, workflow_class: Type[BaseWorkflow]):
        """
        Register a workflow
        
        Args:
            name: Workflow identifier
            workflow_class: Workflow class
        """
        self._workflows[name] = workflow_class
        logger.info(f"Registered workflow: {name}")
    
    def get_workflow(self, name: str) -> Optional[BaseWorkflow]:
        """
        Get workflow instance by name
        
        Args:
            name: Workflow identifier
            
        Returns:
            Workflow instance or None if not found
        """
        workflow_class = self._workflows.get(name)
        if workflow_class:
            return workflow_class()
        return None
    
    def list_workflows(self) -> list:
        """List all registered workflows"""
        return list(self._workflows.keys())


# Singleton instance
_registry = AgentRegistry()


def get_registry() -> AgentRegistry:
    """Get global agent registry"""
    return _registry
