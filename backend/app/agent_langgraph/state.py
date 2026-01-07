"""
LangGraph State Definition
Defines the state structure for agent workflows
"""

from typing import TypedDict, Dict, Any, List, Optional


class AgentState(TypedDict, total=False):
    """
    State for LangGraph agent workflows
    
    This state is passed through all nodes in the graph.
    Nodes can read from and write to any field.
    
    Fields marked as required (in __required_keys__) must be present,
    all others are optional.
    """
    # Execution metadata
    execution_id: str
    agent_id: int
    agent_name: str
    timestamp: str
    
    # Input/Output
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    
    # Configuration
    config: Dict[str, Any]
    
    # Messages (for conversational agents)
    messages: List[Dict[str, Any]]
    
    # Data processing fields
    ingestion: Dict[str, Any]  # Data from ingestion node
    analysis: Dict[str, Any]   # Data from analysis node
    decision: Dict[str, Any]   # Data from decision node
    
    # Workflow control
    requires_hitl: bool
    hitl_approved: bool
    hitl_feedback: Dict[str, Any]
    hitl_reason: str
    
    # Status tracking
    ingestion_complete: bool
    validation_complete: bool
    processing_complete: bool
    decision_complete: bool
    
    # Error handling
    error: Optional[str]
    warnings: List[str]
    
    # Internal (for framework use)
    _stream: Any  # Stream manager for HITL communication


class StateManager:
    """
    Manages state initialization and updates
    """
    
    def initialize_state(
        self,
        agent_id: int,
        agent_name: str,
        execution_id: str,
        input_data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> AgentState:
        """
        Initialize a new agent state
        
        Args:
            agent_id: Agent ID
            agent_name: Agent name
            execution_id: Unique execution ID
            input_data: Input data from user/API
            config: Agent configuration
            
        Returns:
            Initialized state dictionary
        """
        from datetime import datetime
        
        return AgentState(
            execution_id=execution_id,
            agent_id=agent_id,
            agent_name=agent_name,
            timestamp=datetime.utcnow().isoformat(),
            input_data=input_data,
            output_data={},
            config=config,
            messages=[],
            ingestion={},
            analysis={},
            decision={},
            requires_hitl=False,
            hitl_approved=False,
            hitl_feedback={},
            hitl_reason="",
            ingestion_complete=False,
            validation_complete=False,
            processing_complete=False,
            decision_complete=False,
            error=None,
            warnings=[],
            _stream=None
        )