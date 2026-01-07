"""
LangGraph Graph Builder
Creates StateGraph instances with proper node connections
FIXED: Properly routes to workflow based on agent config
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

# ✅ Import your custom agent
from app.agent.data_ingestion_agent import DataIngestionAgent

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


def create_sample_agent_graph():
    """
    Build the retail inventory management workflow
    
    This workflow:
    1. Ingests data from multiple sources (APIs, databases, spreadsheets)
    2. Processes and normalizes the data
    3. Returns structured output for downstream analysis
    """
    logger.info("Building retail agent graph")
    
    # Instantiate DataIngestionAgent
    data_fetcher = DataIngestionAgent(uploaded_data={})

    def sample_ingestion_node(state: AgentState) -> Dict[str, Any]:
        """
        Data Ingestion Node
        
        Fetches data from all external and internal sources
        """
        logger.info(f"Starting data ingestion for execution {state.get('execution_id', 'unknown')}")
        
        # 🟢 STEP 1: Fetch ALL data sources using DataIngestionAgent methods
        
        # External API Data
        current_weather = data_fetcher.get_weather()
        forecast = data_fetcher.get_weather_forecast()
        festivals = data_fetcher.get_festival_events()
        notes = data_fetcher.get_user_notes()
        
        # 🟢 STEP 2: Consolidate ALL fetched data
        all_fetched_data = {
            "weather": current_weather,
            "weather_forecast": forecast,
            "calendar_events": festivals,
            "user_notes": notes,
        }
        
        logger.info(f"Data ingestion completed. Collected data from {len(all_fetched_data)} sources")
        
        # 🟢 STEP 3: Return updated state with ingested data
        return {
            "ingestion": all_fetched_data,
            "output_data": all_fetched_data,  # Set output for completion
            "ingestion_complete": True
        }
    
    # Build the graph
    workflow = StateGraph(AgentState)
    workflow.add_node("ingestion_node", sample_ingestion_node)
    
    # Set entry and exit
    workflow.set_entry_point("ingestion_node")
    workflow.add_edge("ingestion_node", END)
    
    logger.info("Retail agent graph built successfully")
    
    return workflow.compile(checkpointer=MemorySaver())


def create_simple_chat_graph():
    """Simple chat graph without tools"""
    logger.info("Building simple chat graph")
    
    builder = GraphBuilder()
    
    builder.add_node("process", llm_processing_node)
    builder.add_node("format", output_formatting_node)
    
    builder.set_entry_point("process")
    builder.add_edge("process", "format")
    builder.add_edge("format", END)
    
    return builder.compile()


def create_hitl_approval_graph():
    """Graph with mandatory HITL approval"""
    logger.info("Building HITL approval graph")
    
    builder = GraphBuilder()
    
    builder.add_node("validate", input_validation_node)
    builder.add_node("process", llm_processing_node)
    builder.add_node("hitl", hitl_gate_node)
    builder.add_node("format", output_formatting_node)
    
    builder.set_entry_point("validate")
    builder.add_edge("validate", "process")
    builder.add_edge("process", "hitl")
    builder.add_edge("hitl", END)
    builder.add_edge("format", END)
    
    return builder.compile()


def create_agent_graph(agent_config: Dict[str, Any]):
    """
    OLD FUNCTION - kept for backward compatibility
    
    Creates a standard agent graph based on configuration
    """
    logger.warning("create_agent_graph() is deprecated, use create_new_agent_graph()")
    
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
        if state.get("error"):
            return "handle_error"
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
        if state.get("requires_hitl"):
            return "pause_for_hitl"
        return "format_output"
    
    builder.add_conditional_edge(
        "hitl_gate",
        check_hitl_requirement,
        {
            "pause_for_hitl": END,
            "format_output": "format_output"
        }
    )
    
    builder.add_edge("format_output", END)
    builder.add_edge("handle_error", END)
    
    # Compile with checkpointer
    from .checkpointer import get_checkpointer
    checkpointer = get_checkpointer()
    
    return builder.compile(checkpointer=checkpointer)


def create_new_agent_graph(agent_config: Dict[str, Any]):
    """
    ✅ NEW FUNCTION - Main entry point for graph creation
    
    Creates agent graph based on workflow type from agent config
    
    Args:
        agent_config: Agent configuration dict with 'workflow' key
        
    Returns:
        Compiled LangGraph
        
    Raises:
        ValueError: If workflow type is unknown
    """
    # Extract workflow type from config
    print("agent config type",type(agent_config))
    workflow_type = agent_config.workflow
    print("workflow type",workflow_type)
    logger.info(f"Creating graph for workflow type: '{workflow_type}'")
    
    # Route to appropriate workflow builder
    if workflow_type == "sample_ingestion_decision":
        return create_sample_agent_graph()
    
    
    elif workflow_type == "simple_chat":
        return create_simple_chat_graph()
    
    elif workflow_type == "approval":
        return create_hitl_approval_graph()
    
    elif workflow_type == "hitl_approval":
        return create_hitl_approval_graph()
    

    
    else:
        error_msg = f"Unknown workflow type: '{workflow_type}'"
        logger.error(error_msg)
        raise ValueError(error_msg)


# ✅ Export both functions for compatibility
__all__ = [
    'GraphBuilder',
    'create_agent_graph',      # Old function (backward compat)
    'create_new_agent_graph',  # New function (recommended)
    'create_simple_chat_graph',
    'create_hitl_approval_graph',
    'create_sample_agent_graph'
]