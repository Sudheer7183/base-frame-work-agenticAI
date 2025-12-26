# """
# AG-UI Event Creators
# Standard AG-UI protocol events
# """

# from typing import Dict, Any, Optional
# from datetime import datetime
# from enum import Enum


# class EventType(str, Enum):
#     """AG-UI standard event types"""
#     MESSAGE = "message"
#     STATE_SNAPSHOT = "state_snapshot"
#     STATE_PATCH = "state_patch"
#     TOOL_CALL = "tool_call"
#     TOOL_RESULT = "tool_result"
#     ERROR = "error"
#     COMPLETION = "completion"
#     AGENT_STATUS = "agent_status"
#     CUSTOM = "custom"


# def create_message_event(
#     content: str,
#     role: str = "assistant",
#     metadata: Optional[Dict[str, Any]] = None
# ) -> Dict[str, Any]:
#     """
#     Create a message event
    
#     Args:
#         content: Message content
#         role: Message role (user, assistant, system)
#         metadata: Additional metadata
        
#     Returns:
#         AG-UI message event
#     """
#     return {
#         "type": EventType.MESSAGE,
#         "timestamp": datetime.utcnow().isoformat(),
#         "data": {
#             "role": role,
#             "content": content,
#             "metadata": metadata or {}
#         }
#     }


# def create_state_event(
#     state: Dict[str, Any],
#     is_patch: bool = False
# ) -> Dict[str, Any]:
#     """
#     Create a state update event
    
#     Args:
#         state: State data
#         is_patch: Whether this is a patch or full snapshot
        
#     Returns:
#         AG-UI state event
#     """
#     event_type = EventType.STATE_PATCH if is_patch else EventType.STATE_SNAPSHOT
    
#     return {
#         "type": event_type,
#         "timestamp": datetime.utcnow().isoformat(),
#         "data": {
#             "state": state
#         }
#     }


# def create_tool_event(
#     tool_name: str,
#     tool_input: Dict[str, Any],
#     tool_result: Optional[Any] = None,
#     is_call: bool = True
# ) -> Dict[str, Any]:
#     """
#     Create a tool event (call or result)
    
#     Args:
#         tool_name: Name of the tool
#         tool_input: Tool input parameters
#         tool_result: Tool execution result (for result events)
#         is_call: Whether this is a call or result event
        
#     Returns:
#         AG-UI tool event
#     """
#     event_type = EventType.TOOL_CALL if is_call else EventType.TOOL_RESULT
    
#     event_data = {
#         "tool": tool_name,
#         "input": tool_input
#     }
    
#     if not is_call and tool_result is not None:
#         event_data["result"] = tool_result
    
#     return {
#         "type": event_type,
#         "timestamp": datetime.utcnow().isoformat(),
#         "data": event_data
#     }


# def create_error_event(
#     error_message: str,
#     error_code: Optional[str] = None,
#     details: Optional[Dict[str, Any]] = None
# ) -> Dict[str, Any]:
#     """
#     Create an error event
    
#     Args:
#         error_message: Error message
#         error_code: Optional error code
#         details: Additional error details
        
#     Returns:
#         AG-UI error event
#     """
#     return {
#         "type": EventType.ERROR,
#         "timestamp": datetime.utcnow().isoformat(),
#         "data": {
#             "message": error_message,
#             "code": error_code,
#             "details": details or {}
#         }
#     }


# def create_completion_event(
#     final_output: Dict[str, Any],
#     metadata: Optional[Dict[str, Any]] = None
# ) -> Dict[str, Any]:
#     """
#     Create a completion event
    
#     Args:
#         final_output: Final agent output
#         metadata: Additional metadata
        
#     Returns:
#         AG-UI completion event
#     """
#     return {
#         "type": EventType.COMPLETION,
#         "timestamp": datetime.utcnow().isoformat(),
#         "data": {
#             "output": final_output,
#             "metadata": metadata or {}
#         }
#     }


# def create_agent_status_event(
#     status: str,
#     message: Optional[str] = None
# ) -> Dict[str, Any]:
#     """
#     Create an agent status event
    
#     Args:
#         status: Status (running, paused, completed, error)
#         message: Optional status message
        
#     Returns:
#         AG-UI status event
#     """
#     return {
#         "type": EventType.AGENT_STATUS,
#         "timestamp": datetime.utcnow().isoformat(),
#         "data": {
#             "status": status,
#             "message": message
#         }
#     }


from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import uuid


class EventType(str, Enum):
    """AG-UI standard event types"""
    MESSAGE = "message"
    MESSAGE_CHUNK = "message_chunk"  # For streaming tokens
    STATE_SNAPSHOT = "state_snapshot"
    STATE_PATCH = "state_patch"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    COMPLETION = "completion"
    AGENT_STATUS = "agent_status"
    NODE_START = "node_start"
    NODE_END = "node_end"


def create_event_base() -> Dict[str, Any]:
    """Create base event structure"""
    return {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


def create_message_chunk_event(
    content: str,
    role: str = "assistant",
    message_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a streaming message chunk event
    
    Args:
        content: Token/chunk content
        role: Message role
        message_id: Message identifier for chunking
        metadata: Additional metadata
        
    Returns:
        AG-UI message chunk event
    """
    event = create_event_base()
    event.update({
        "type": EventType.MESSAGE_CHUNK,
        "data": {
            "role": role,
            "content": content,
            "message_id": message_id or str(uuid.uuid4()),
            "metadata": metadata or {}
        }
    })
    return event


def create_message_event(
    content: str,
    role: str = "assistant",
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a complete message event
    
    Args:
        content: Full message content
        role: Message role
        metadata: Additional metadata
        
    Returns:
        AG-UI message event
    """
    event = create_event_base()
    event.update({
        "type": EventType.MESSAGE,
        "data": {
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
    })
    return event


def create_state_event(
    state: Dict[str, Any],
    is_patch: bool = False,
    node_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a state update event
    
    Args:
        state: State data
        is_patch: Whether this is a patch or full snapshot
        node_name: Name of node that produced this state
        
    Returns:
        AG-UI state event
    """
    event = create_event_base()
    event_type = EventType.STATE_PATCH if is_patch else EventType.STATE_SNAPSHOT
    
    event.update({
        "type": event_type,
        "data": {
            "state": state,
            "node": node_name
        }
    })
    return event


def create_tool_call_event(
    tool_name: str,
    tool_input: Dict[str, Any],
    tool_call_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a tool call event
    
    Args:
        tool_name: Name of the tool
        tool_input: Tool input parameters
        tool_call_id: Unique tool call identifier
        
    Returns:
        AG-UI tool call event
    """
    event = create_event_base()
    event.update({
        "type": EventType.TOOL_CALL,
        "data": {
            "tool": tool_name,
            "input": tool_input,
            "tool_call_id": tool_call_id or str(uuid.uuid4())
        }
    })
    return event


def create_tool_result_event(
    tool_name: str,
    tool_result: Any,
    tool_call_id: str,
    error: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a tool result event
    
    Args:
        tool_name: Name of the tool
        tool_result: Tool execution result
        tool_call_id: Tool call identifier
        error: Error message if tool failed
        
    Returns:
        AG-UI tool result event
    """
    event = create_event_base()
    event.update({
        "type": EventType.TOOL_RESULT,
        "data": {
            "tool": tool_name,
            "result": tool_result,
            "tool_call_id": tool_call_id,
            "error": error
        }
    })
    return event


def create_node_event(
    node_name: str,
    is_start: bool = True,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a node start/end event
    
    Args:
        node_name: Name of the node
        is_start: Whether this is start or end
        metadata: Additional metadata
        
    Returns:
        AG-UI node event
    """
    event = create_event_base()
    event_type = EventType.NODE_START if is_start else EventType.NODE_END
    
    event.update({
        "type": event_type,
        "data": {
            "node": node_name,
            "metadata": metadata or {}
        }
    })
    return event


def create_agent_status_event(
    status: str,
    message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create an agent status event
    
    Args:
        status: Status string (running, paused, completed, failed)
        message: Status message
        metadata: Additional metadata
        
    Returns:
        AG-UI agent status event
    """
    event = create_event_base()
    event.update({
        "type": EventType.AGENT_STATUS,
        "data": {
            "status": status,
            "message": message,
            "metadata": metadata or {}
        }
    })
    return event


def create_error_event(
    error_message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    recoverable: bool = False
) -> Dict[str, Any]:
    """
    Create an error event
    
    Args:
        error_message: Error message
        error_code: Optional error code
        details: Additional error details
        recoverable: Whether error is recoverable
        
    Returns:
        AG-UI error event
    """
    event = create_event_base()
    event.update({
        "type": EventType.ERROR,
        "data": {
            "message": error_message,
            "code": error_code,
            "details": details or {},
            "recoverable": recoverable
        }
    })
    return event


def create_completion_event(
    final_output: Any,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a completion event
    
    Args:
        final_output: Final execution output
        metadata: Additional metadata
        
    Returns:
        AG-UI completion event
    """
    event = create_event_base()
    event.update({
        "type": EventType.COMPLETION,
        "data": {
            "output": final_output,
            "metadata": metadata or {}
        }
    })
    return event