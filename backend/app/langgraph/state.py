"""
LangGraph State Management
TypedDict-based state for graphs
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from operator import add
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """
    State for LangGraph agents
    
    This is the primary state container passed between nodes
    """
    # Messages
    messages: Annotated[List[BaseMessage], add]
    
    # Agent context
    agent_id: int
    agent_name: str
    execution_id: str
    
    # Input/Output
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]]
    
    # Configuration
    config: Dict[str, Any]
    
    # HITL
    requires_hitl: bool
    hitl_decision: Optional[str]  # "approved", "rejected", None
    hitl_feedback: Optional[Dict[str, Any]]
    
    # Error handling
    error: Optional[str]
    retry_count: int
    
    # Metadata
    metadata: Dict[str, Any]
    
    # Next step
    next_step: Optional[str]


class StateManager:
    """Manages state transformations and validations"""
    
    @staticmethod
    def initialize_state(
        agent_id: int,
        agent_name: str,
        execution_id: str,
        input_data: Dict[str, Any],
        config: Dict[str, Any]
    ) -> AgentState:
        """Initialize a new agent state"""
        return AgentState(
            messages=[],
            agent_id=agent_id,
            agent_name=agent_name,
            execution_id=execution_id,
            input_data=input_data,
            output_data=None,
            config=config,
            requires_hitl=False,
            hitl_decision=None,
            hitl_feedback=None,
            error=None,
            retry_count=0,
            metadata={},
            next_step=None
        )
    
    @staticmethod
    def update_state(state: AgentState, **updates) -> AgentState:
        """Update state with new values"""
        return {**state, **updates}
    
    @staticmethod
    def add_message(state: AgentState, message: BaseMessage) -> AgentState:
        """Add a message to state"""
        state["messages"].append(message)
        return state