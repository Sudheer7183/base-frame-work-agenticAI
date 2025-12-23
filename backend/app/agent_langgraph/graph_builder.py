"""
LangGraph Graph Builder
Creates StateGraph instances with proper node connections
"""

import logging
from typing import Dict, Any, Callable
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import AgentState
from .nodes import (
    input_validation_node,
    llm_processing_node,
    hitl_gate_node,
    output_formatting_node,
    error_handler_node,
    tool_execution_node
)

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Builds LangGraph StateGraph instances
    
    Provides fluent API for graph construction
    """
    
    def __init__(self):
        self.graph = StateGraph(AgentState)
        self.nodes: Dict[str, Callable] = {}
        self.edges: list = []
        self.conditional_edges: list = []
        self.entry_point: str = None
    
    def add_node(self, name: str, func: Callable) -> 'GraphBuilder':
        """Add a node to the graph"""
        self.nodes[name] = func
        self.graph.add_node(name, func)
        logger.debug(f"Added node: {name}")
        return self
    
    def add_edge(self, from_node: str, to_node: str) -> 'GraphBuilder':
        """Add a directed edge"""
        self.edges.append((from_node, to_node))
        self.graph.add_edge(from_node, to_node)
        logger.debug(f"Added edge: {from_node} -> {to_node}")
        return self
    
    def add_conditional_edge(
        self,
        from_node: str,
        router: Callable,
        path_map: Dict[str, str]
    ) -> 'GraphBuilder':
        """Add a conditional edge with routing logic"""
        self.conditional_edges.append((from_node, router, path_map))
        self.graph.add_conditional_edges(from_node, router, path_map)
        logger.debug(f"Added conditional edge from: {from_node}")
        return self
    
    def set_entry_point(self, node: str) -> 'GraphBuilder':
        """Set the entry point node"""
        self.entry_point = node
        self.graph.set_entry_point(node)
        logger.debug(f"Set entry point: {node}")
        return self
    
    def compile(self, checkpointer=None):
        """Compile the graph"""
        if checkpointer is None:
            checkpointer = MemorySaver()
        
        compiled = self.graph.compile(checkpointer=checkpointer)
        logger.info("Graph compiled successfully")
        return compiled


def create_agent_graph(agent_config: Dict[str, Any]):
    """
    Create a standard agent graph based on configuration
    
    Standard flow:
    1. Input Validation
    2. LLM Processing
    3. Tool Execution (if needed)
    4. HITL Gate
    5. Output Formatting
    
    Args:
        agent_config: Agent configuration dict
        
    Returns:
        Compiled LangGraph
    """
    builder = GraphBuilder()
    
    # Add all nodes
    builder.add_node("validate_input", input_validation_node)
    builder.add_node("process_llm", llm_processing_node)
    builder.add_node("execute_tools", tool_execution_node)
    builder.add_node("hitl_gate", hitl_gate_node)
    builder.add_node("format_output", output_formatting_node)
    builder.add_node("handle_error", error_handler_node)
    
    # Set entry point
    builder.set_entry_point("validate_input")
    
    # Add edges
    builder.add_edge("validate_input", "process_llm")
    
    # Conditional: Tools or HITL?
    def should_execute_tools(state: AgentState) -> str:
        """Determine if tools need execution"""
        if state.get("error"):
            return "handle_error"
        # Check if LLM requested tools
        last_message = state["messages"][-1] if state["messages"] else None
        if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "execute_tools"
        return "hitl_gate"
    
    builder.add_conditional_edge(
        "process_llm",
        should_execute_tools,
        {
            "execute_tools": "execute_tools",
            "hitl_gate": "hitl_gate",
            "handle_error": "handle_error"
        }
    )
    
    builder.add_edge("execute_tools", "hitl_gate")
    
    # Conditional: HITL required?
    def check_hitl_requirement(state: AgentState) -> str:
        """Check if HITL is required"""
        if state.get("requires_hitl"):
            return "pause_for_hitl"
        return "format_output"
    
    builder.add_conditional_edge(
        "hitl_gate",
        check_hitl_requirement,
        {
            "pause_for_hitl": END,  # Pause execution
            "format_output": "format_output"
        }
    )
    
    builder.add_edge("format_output", END)
    builder.add_edge("handle_error", END)
    
    # Compile with checkpointer for state persistence
    from .checkpointer import get_checkpointer
    checkpointer = get_checkpointer()
    
    return builder.compile(checkpointer=checkpointer)


# Pre-built graph templates
def create_simple_chat_graph():
    """Simple chat graph without tools"""
    builder = GraphBuilder()
    
    builder.add_node("process", llm_processing_node)
    builder.add_node("format", output_formatting_node)
    
    builder.set_entry_point("process")
    builder.add_edge("process", "format")
    builder.add_edge("format", END)
    
    return builder.compile()


def create_hitl_approval_graph():
    """Graph with mandatory HITL approval"""
    builder = GraphBuilder()
    
    builder.add_node("validate", input_validation_node)
    builder.add_node("process", llm_processing_node)
    builder.add_node("hitl", hitl_gate_node)
    builder.add_node("format", output_formatting_node)
    
    builder.set_entry_point("validate")
    builder.add_edge("validate", "process")
    builder.add_edge("process", "hitl")
    builder.add_edge("hitl", END)  # Always pause for approval
    builder.add_edge("format", END)
    
    return builder.compile()