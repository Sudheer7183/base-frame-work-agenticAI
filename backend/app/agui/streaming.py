"""
AG-UI Streaming Manager
Handles SSE streaming of AG-UI events
"""

import asyncio
import logging
import json
from typing import AsyncGenerator, Dict, Any
from queue import Queue
from threading import Lock

logger = logging.getLogger(__name__)


class AGUIStreamManager:
    """
    Manages AG-UI event streaming
    
    Handles event queuing and SSE formatting
    """
    
    def __init__(self):
        self.events: Queue = Queue()
        self.lock = Lock()
        self.active = True
    
    def emit_event(self, event: Dict[str, Any]):
        """
        Emit an AG-UI event
        
        Args:
            event: AG-UI event dict
        """
        if not self.active:
            logger.warning("Attempted to emit event on inactive stream")
            return
        
        with self.lock:
            self.events.put(event)
            logger.debug(f"Emitted event: {event['type']}")
    
    def format_sse(self, event: Dict[str, Any]) -> str:
        """
        Format event as SSE
        
        Args:
            event: AG-UI event dict
            
        Returns:
            SSE formatted string
        """
        event_type = event.get("type", "message")
        data = json.dumps(event)
        
        return f"event: {event_type}\ndata: {data}\n\n"
    
    async def stream_events(self) -> AsyncGenerator[str, None]:
        """
        Stream events as SSE
        
        Yields:
            SSE formatted event strings
        """
        logger.info("Starting AG-UI event stream")
        
        try:
            while self.active:
                # Check for events
                if not self.events.empty():
                    with self.lock:
                        event = self.events.get()
                    
                    # Format and yield
                    sse_data = self.format_sse(event)
                    yield sse_data
                    
                    # Check for completion
                    if event.get("type") == "completion":
                        logger.info("Completion event sent, ending stream")
                        break
                else:
                    # Small delay to avoid busy waiting
                    await asyncio.sleep(0.1)
        
        except Exception as e:
            logger.error(f"Error in event stream: {e}", exc_info=True)
            # Send error event
            from .events import create_error_event
            error_event = create_error_event(str(e))
            yield self.format_sse(error_event)
        
        finally:
            self.active = False
            logger.info("AG-UI event stream ended")
    
    def close(self):
        """Close the stream"""
        self.active = False