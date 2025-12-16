"""
AG-UI Event Creators
Standard AG-UI protocol events
"""

from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """AG-UI standard event types"""
    MESSAGE = "message"
    STATE_SNAPSHOT = "state_snapshot"
    STATE_PATCH = "state_patch"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    COMPLETION = "completion"
    AGENT_STATUS = "agent_status"
    CUSTOM = "custom"


def create_message_event(
    content: str,
    role: str = "assistant",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a message event
    
    Args:
        content: Message content
        role: Message role (user, assistant, system)
        metadata: Additional metadata
        
    Returns:
        AG-UI message event
    """
    return {
        "type": EventType.MESSAGE,
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
    }


def create_state_event(
    state: Dict[str, Any],
    is_patch: bool = False
) -> Dict[str, Any]:
    """
    Create a state update event
    
    Args:
        state: State data
        is_patch: Whether this is a patch or full snapshot
        
    Returns:
        AG-UI state event
    """
    event_type = EventType.STATE_PATCH if is_patch else EventType.STATE_SNAPSHOT
    
    return {
        "type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "state": state
        }
    }


def create_tool_event(
    tool_name: str,
    tool_input: Dict[str, Any],
    tool_result: Optional[Any] = None,
    is_call: bool = True
) -> Dict[str, Any]:
    """
    Create a tool event (call or result)
    
    Args:
        tool_name: Name of the tool
        tool_input: Tool input parameters
        tool_result: Tool execution result (for result events)
        is_call: Whether this is a call or result event
        
    Returns:
        AG-UI tool event
    """
    event_type = EventType.TOOL_CALL if is_call else EventType.TOOL_RESULT
    
    event_data = {
        "tool": tool_name,
        "input": tool_input
    }
    
    if not is_call and tool_result is not None:
        event_data["result"] = tool_result
    
    return {
        "type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": event_data
    }


def create_error_event(
    error_message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create an error event
    
    Args:
        error_message: Error message
        error_code: Optional error code
        details: Additional error details
        
    Returns:
        AG-UI error event
    """
    return {
        "type": EventType.ERROR,
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "message": error_message,
            "code": error_code,
            "details": details or {}
        }
    }


def create_completion_event(
    final_output: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a completion event
    
    Args:
        final_output: Final agent output
        metadata: Additional metadata
        
    Returns:
        AG-UI completion event
    """
    return {
        "type": EventType.COMPLETION,
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "output": final_output,
            "metadata": metadata or {}
        }
    }


def create_agent_status_event(
    status: str,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an agent status event
    
    Args:
        status: Status (running, paused, completed, error)
        message: Optional status message
        
    Returns:
        AG-UI status event
    """
    return {
        "type": EventType.AGENT_STATUS,
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "status": status,
            "message": message
        }
    }