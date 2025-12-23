"""Agent execution state management"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class AgentState:
    """
    Agent execution state
    
    Tracks the current state during agent execution
    """
    agent_id: int
    agent_name: str
    execution_id: str
    
    # Input/output
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    
    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Status
    status: str = "initializing"
    step: int = 0
    total_steps: int = 0
    
    # HITL
    requires_hitl: bool = False
    hitl_record_id: Optional[int] = None
    
    # Error handling
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "execution_id": self.execution_id,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "config": self.config,
            "status": self.status,
            "step": self.step,
            "total_steps": self.total_steps,
            "requires_hitl": self.requires_hitl,
            "hitl_record_id": self.hitl_record_id,
            "error": self.error,
            "retry_count": self.retry_count,
            "metadata": self.metadata,
        }