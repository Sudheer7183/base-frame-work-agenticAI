"""
LangGraph Node Functions
Individual processing nodes for the graph
"""

import logging
from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)


async def input_validation_node(state: AgentState) -> AgentState:
    """
    Validate input data
    
    Ensures all required fields are present
    """
    logger.info(f"Validating input for execution {state['execution_id']}")
    
    config = state["config"]
    required_fields = config.get("required_fields", [])
    input_data = state["input_data"]
    
    # Validate required fields
    missing_fields = [f for f in required_fields if f not in input_data]
    
    if missing_fields:
        state["error"] = f"Missing required fields: {', '.join(missing_fields)}"
        state["next_step"] = "handle_error"
        return state
    
    logger.info("Input validation passed")
    state["next_step"] = "process_llm"
    return state


async def llm_processing_node(state: AgentState) -> AgentState:
    """
    Process with LLM
    
    Uses configured LLM to process user input
    """
    logger.info(f"Processing with LLM for execution {state['execution_id']}")
    
    try:
        # Get LLM configuration
        config = state["config"]
        model_name = config.get("model", "gpt-4")
        temperature = config.get("temperature", 0.7)
        
        # Initialize LLM
        llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=settings.OPENAI_API_KEY if hasattr(settings, 'OPENAI_API_KEY') else None
        )
        
        # Prepare messages
        messages = state["messages"].copy() if state["messages"] else []
        
        # Add system message if configured
        system_prompt = config.get("system_prompt")
        if system_prompt and (not messages or not isinstance(messages[0], SystemMessage)):
            messages.insert(0, SystemMessage(content=system_prompt))
        
        # Add user input if not already in messages
        if not messages or not isinstance(messages[-1], HumanMessage):
            user_content = state["input_data"].get("message", str(state["input_data"]))
            messages.append(HumanMessage(content=user_content))
        
        # Invoke LLM
        response = await llm.ainvoke(messages)
        
        # Add response to messages
        state["messages"] = messages + [response]
        
        # Extract output
        state["output_data"] = {
            "response": response.content,
            "model": model_name,
            "finish_reason": "completed"
        }
        
        logger.info("LLM processing completed")
        state["next_step"] = "hitl_gate"
        
    except Exception as e:
        logger.error(f"LLM processing failed: {e}", exc_info=True)
        state["error"] = str(e)
        state["next_step"] = "handle_error"
    
    return state


async def tool_execution_node(state: AgentState) -> AgentState:
    """
    Execute tools requested by LLM
    
    Handles function calling and tool execution
    """
    logger.info(f"Executing tools for execution {state['execution_id']}")
    
    # Get last message (should have tool calls)
    last_message = state["messages"][-1]
    
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        logger.warning("No tool calls found in message")
        state["next_step"] = "hitl_gate"
        return state
    
    # TODO: Implement actual tool execution
    # This is a placeholder - integrate with your tool registry
    
    tool_results = []
    for tool_call in last_message.tool_calls:
        logger.info(f"Executing tool: {tool_call.get('name')}")
        # Execute tool and collect results
        tool_results.append({
            "tool": tool_call.get("name"),
            "result": "Tool execution placeholder"
        })
    
    # Update state with tool results
    if state["output_data"] is None:
        state["output_data"] = {}
    state["output_data"]["tool_results"] = tool_results
    
    state["next_step"] = "hitl_gate"
    return state


async def hitl_gate_node(state: AgentState) -> AgentState:
    """
    HITL gate - determines if human review is needed
    
    Configure via agent config: {"hitl": {"enabled": true, "threshold": 0.8}}
    """
    logger.info(f"Checking HITL requirements for execution {state['execution_id']}")
    
    hitl_config = state["config"].get("hitl", {})
    
    if not hitl_config.get("enabled", False):
        logger.info("HITL not enabled for this agent")
        state["requires_hitl"] = False
        state["next_step"] = "format_output"
        return state
    
    # Check confidence threshold
    output_data = state.get("output_data") or {}
    confidence = output_data.get("confidence", 1.0)
    threshold = hitl_config.get("threshold", 0.8)
    
    if confidence < threshold:
        logger.info(f"HITL required: confidence {confidence} < threshold {threshold}")
        state["requires_hitl"] = True
        state["next_step"] = "pause_for_hitl"
    else:
        logger.info(f"HITL not required: confidence {confidence} >= threshold {threshold}")
        state["requires_hitl"] = False
        state["next_step"] = "format_output"
    
    return state


async def output_formatting_node(state: AgentState) -> AgentState:
    """
    Format output data
    
    Ensures output is in the expected format
    """
    logger.info(f"Formatting output for execution {state['execution_id']}")
    
    output_data = state.get("output_data") or {}
    
    # Add formatting
    output_data["formatted"] = True
    output_data["execution_id"] = state["execution_id"]
    output_data["agent_name"] = state["agent_name"]
    
    # Add messages summary
    if state["messages"]:
        output_data["message_count"] = len(state["messages"])
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage):
            output_data["final_response"] = last_message.content
    
    state["output_data"] = output_data
    state["next_step"] = END
    
    logger.info("Output formatting completed")
    return state


async def error_handler_node(state: AgentState) -> AgentState:
    """
    Handle errors in the workflow
    
    Logs errors and formats error responses
    """
    error = state.get("error", "Unknown error")
    logger.error(f"Error in execution {state['execution_id']}: {error}")
    
    state["output_data"] = {
        "error": True,
        "message": error,
        "execution_id": state["execution_id"],
        "agent_name": state["agent_name"]
    }
    
    state["next_step"] = END
    return state