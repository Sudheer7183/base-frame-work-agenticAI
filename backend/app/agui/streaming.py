# """
# AG-UI Streaming Manager
# Handles SSE streaming of AG-UI events
# """

# import asyncio
# import logging
# import json
# from typing import AsyncGenerator, Dict, Any
# from queue import Queue
# from threading import Lock

# logger = logging.getLogger(__name__)


# class AGUIStreamManager:
#     """
#     Manages AG-UI event streaming
    
#     Handles event queuing and SSE formatting
#     """
    
#     def __init__(self):
#         self.events: Queue = Queue()
#         self.lock = Lock()
#         self.active = True
    
#     def emit_event(self, event: Dict[str, Any]):
#         """
#         Emit an AG-UI event
        
#         Args:
#             event: AG-UI event dict
#         """
#         if not self.active:
#             logger.warning("Attempted to emit event on inactive stream")
#             return
        
#         with self.lock:
#             self.events.put(event)
#             logger.debug(f"Emitted event: {event['type']}")
    
#     def format_sse(self, event: Dict[str, Any]) -> str:
#         """
#         Format event as SSE
        
#         Args:
#             event: AG-UI event dict
            
#         Returns:
#             SSE formatted string
#         """
#         event_type = event.get("type", "message")
#         data = json.dumps(event)
        
#         return f"event: {event_type}\ndata: {data}\n\n"
    
#     async def stream_events(self) -> AsyncGenerator[str, None]:
#         """
#         Stream events as SSE
        
#         Yields:
#             SSE formatted event strings
#         """
#         logger.info("Starting AG-UI event stream")
        
#         try:
#             while self.active:
#                 # Check for events
#                 if not self.events.empty():
#                     with self.lock:
#                         event = self.events.get()
                    
#                     # Format and yield
#                     sse_data = self.format_sse(event)
#                     yield sse_data
                    
#                     # Check for completion
#                     if event.get("type") == "completion":
#                         logger.info("Completion event sent, ending stream")
#                         break
#                 else:
#                     # Small delay to avoid busy waiting
#                     await asyncio.sleep(0.1)
        
#         except Exception as e:
#             logger.error(f"Error in event stream: {e}", exc_info=True)
#             # Send error event
#             from .events import create_error_event
#             error_event = create_error_event(str(e))
#             yield self.format_sse(error_event)
        
#         finally:
#             self.active = False
#             logger.info("AG-UI event stream ended")
    
#     def close(self):
#         """Close the stream"""
#         self.active = False


"""
AG-UI Streaming Manager
Async event-based SSE streaming
"""

import asyncio
import logging
import json
from typing import AsyncGenerator, Dict, Any, Optional
from asyncio import Queue
from datetime import datetime

logger = logging.getLogger(__name__)


class AGUIStreamManager:
    """
    Manages AG-UI event streaming with async queue
    
    Features:
    - Async event queue (thread-safe)
    - SSE formatting
    - Automatic lifecycle management
    - Error handling
    - Heartbeat support
    """
    
    def __init__(self, heartbeat_interval: int = 30):
        """
        Initialize stream manager
        
        Args:
            heartbeat_interval: Seconds between heartbeat pings
        """
        self.events: Queue = Queue()
        self.active = True
        self.heartbeat_interval = heartbeat_interval
        self.last_event_time = datetime.utcnow()
        self.stream_id = None
    
    async def emit_event(self, event: Dict[str, Any]):
        """
        Emit an AG-UI event (async)
        
        Args:
            event: AG-UI event dict
        """
        if not self.active:
            logger.warning("Attempted to emit event on inactive stream")
            return
        
        await self.events.put(event)
        self.last_event_time = datetime.utcnow()
        logger.debug(f"Emitted event: {event.get('type')}")
    
    def format_sse(self, event: Dict[str, Any]) -> str:
        """
        Format event as Server-Sent Event
        
        Args:
            event: AG-UI event dict
            
        Returns:
            SSE formatted string
        """
        event_type = event.get("type", "message")
        
        # Ensure event has required fields
        if "id" not in event:
            event["id"] = str(id(event))
        if "timestamp" not in event:
            event["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        data = json.dumps(event, ensure_ascii=False)
        
        # SSE format: event, id, data fields
        return f"event: {event_type}\nid: {event['id']}\ndata: {data}\n\n"
    
    def format_heartbeat(self) -> str:
        """Format a heartbeat ping"""
        return ": heartbeat\n\n"
    
    async def stream_events(self) -> AsyncGenerator[str, None]:
        """
        Stream events as SSE (async generator)
        
        Yields:
            SSE formatted event strings
        """
        logger.info(f"Starting AG-UI event stream {self.stream_id}")
        
        last_heartbeat = datetime.utcnow()
        
        try:
            while self.active:
                try:
                    # Wait for event with timeout for heartbeat
                    event = await asyncio.wait_for(
                        self.events.get(),
                        timeout=self.heartbeat_interval
                    )
                    
                    # Format and yield event
                    sse_data = self.format_sse(event)
                    yield sse_data
                    
                    # Check for completion
                    if event.get("type") == "completion":
                        logger.info("Completion event sent, ending stream")
                        break
                    
                    # Check for error that should end stream
                    if event.get("type") == "error":
                        error_data = event.get("data", {})
                        if not error_data.get("recoverable", False):
                            logger.info("Non-recoverable error, ending stream")
                            break
                    
                    last_heartbeat = datetime.utcnow()
                    
                except asyncio.TimeoutError:
                    # Send heartbeat if no events
                    now = datetime.utcnow()
                    if (now - last_heartbeat).seconds >= self.heartbeat_interval:
                        yield self.format_heartbeat()
                        last_heartbeat = now
                
        except asyncio.CancelledError:
            logger.info("Stream cancelled by client")
            
        except Exception as e:
            logger.error(f"Error in event stream: {e}", exc_info=True)
            # Send error event
            from .events import create_error_event
            error_event = create_error_event(
                error_message=str(e),
                error_code="STREAM_ERROR"
            )
            yield self.format_sse(error_event)
        
        finally:
            self.active = False
            logger.info(f"AG-UI event stream {self.stream_id} ended")
    
    async def close(self):
        """Close the stream gracefully"""
        self.active = False
        # Drain remaining events
        while not self.events.empty():
            try:
                self.events.get_nowait()
            except:
                break