"""
LangGraph to AG-UI Event Transformer
Converts LangGraph events to AG-UI protocol events
"""

import logging
from typing import Dict, Any, Optional
from .events import (
    create_message_chunk_event,
    create_tool_call_event,
    create_tool_result_event,
    create_node_event,
    create_state_event,
    create_error_event
)

logger = logging.getLogger(__name__)


class EventTransformer:
    """
    Transforms LangGraph events to AG-UI events
    
    Handles:
    - LLM token streaming
    - Tool calls and results
    - Node execution tracking
    - State updates
    """
    
    def __init__(self):
        self.current_message_id = None
        self.tool_calls = {}  # Track tool calls by ID
        self.current_node = None
    
    def transform_langgraph_event(
        self,
        event: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Transform a LangGraph event to AG-UI event
        
        Args:
            event: LangGraph event from astream_events()
            
        Returns:
            AG-UI event or None if event should be skipped
        """
        event_type = event.get("event")
        
        # Map LangGraph events to AG-UI events
        if event_type == "on_chat_model_stream":
            return self._handle_llm_stream(event)
        
        elif event_type == "on_chat_model_start":
            return self._handle_llm_start(event)
        
        elif event_type == "on_chat_model_end":
            return self._handle_llm_end(event)
        
        elif event_type == "on_tool_start":
            return self._handle_tool_start(event)
        
        elif event_type == "on_tool_end":
            return self._handle_tool_end(event)
        
        elif event_type == "on_chain_start":
            return self._handle_node_start(event)
        
        elif event_type == "on_chain_end":
            return self._handle_node_end(event)
        
        else:
            logger.debug(f"Unhandled event type: {event_type}")
            return None
    
    def _handle_llm_stream(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle LLM token streaming"""
        data = event.get("data", {})
        chunk = data.get("chunk")
        
        if not chunk:
            return None
        
        # Extract content from chunk
        content = ""
        if hasattr(chunk, "content"):
            content = chunk.content
        elif isinstance(chunk, dict) and "content" in chunk:
            content = chunk["content"]
        
        if not content:
            return None
        
        # Generate message ID if needed
        if not self.current_message_id:
            import uuid
            self.current_message_id = str(uuid.uuid4())
        
        return create_message_chunk_event(
            content=content,
            role="assistant",
            message_id=self.current_message_id
        )
    
    def _handle_llm_start(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle LLM generation start"""
        import uuid
        self.current_message_id = str(uuid.uuid4())
        
        # Could emit a node_start event for the LLM
        return create_node_event(
            node_name="llm",
            is_start=True,
            metadata={"type": "language_model"}
        )
    
    def _handle_llm_end(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle LLM generation end"""
        self.current_message_id = None
        
        return create_node_event(
            node_name="llm",
            is_start=False,
            metadata={"type": "language_model"}
        )
    
    def _handle_tool_start(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle tool execution start"""
        data = event.get("data", {})
        input_data = data.get("input", {})
        
        name = event.get("name", "unknown_tool")
        run_id = event.get("run_id")
        
        # Store tool call
        if run_id:
            self.tool_calls[run_id] = {
                "name": name,
                "input": input_data
            }
        
        return create_tool_call_event(
            tool_name=name,
            tool_input=input_data,
            tool_call_id=run_id
        )
    
    def _handle_tool_end(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle tool execution end"""
        data = event.get("data", {})
        output = data.get("output")
        
        run_id = event.get("run_id")
        
        # Get tool info
        tool_info = self.tool_calls.get(run_id, {})
        tool_name = tool_info.get("name", "unknown_tool")
        
        # Check for error
        error = None
        if isinstance(output, dict) and "error" in output:
            error = output["error"]
        
        return create_tool_result_event(
            tool_name=tool_name,
            tool_result=output,
            tool_call_id=run_id,
            error=error
        )
    
    def _handle_node_start(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle node (chain) start"""
        name = event.get("name", "unknown")
        
        # Skip certain internal chains
        if name.startswith("RunnableSequence") or name.startswith("RunnableParallel"):
            return None
        
        self.current_node = name
        
        return create_node_event(
            node_name=name,
            is_start=True
        )
    
    def _handle_node_end(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle node (chain) end"""
        name = event.get("name", "unknown")
        
        # Skip certain internal chains
        if name.startswith("RunnableSequence") or name.startswith("RunnableParallel"):
            return None
        
        data = event.get("data", {})
        output = data.get("output")
        
        # Emit state update if output has state
        state_event = None
        if isinstance(output, dict):
            state_event = create_state_event(
                state=output,
                is_patch=False,
                node_name=name
            )
        
        node_event = create_node_event(
            node_name=name,
            is_start=False
        )
        
        self.current_node = None
        
        # Return node end event (state event handled separately)
        return node_event