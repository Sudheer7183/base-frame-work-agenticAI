"""
Test AG-UI Streaming Implementation
"""
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
import asyncio
import pytest
from app.agui.streaming import AGUIStreamManager
from app.agui.events import (
    create_message_chunk_event,
    create_tool_call_event,
    create_completion_event
)


@pytest.mark.asyncio
async def test_stream_manager():
    """Test basic stream manager functionality"""
    stream = AGUIStreamManager(heartbeat_interval=5)
    
    # Emit some events
    await stream.emit_event(create_message_chunk_event("Hello"))
    await stream.emit_event(create_message_chunk_event(" world"))
    await stream.emit_event(create_completion_event({"text": "Hello world"}))
    
    # Collect events
    events = []
    async for sse_data in stream.stream_events():
        events.append(sse_data)
        # Stream ends after completion
    
    assert len(events) >= 3
    assert "message_chunk" in events[0]
    assert "completion" in events[-1]


@pytest.mark.asyncio
async def test_event_formatting():
    """Test SSE formatting"""
    stream = AGUIStreamManager()
    
    event = create_message_chunk_event("Test", message_id="msg_123")
    sse = stream.format_sse(event)
    
    assert "event: message_chunk" in sse
    assert "data: {" in sse
    assert "msg_123" in sse
    assert sse.endswith("\n\n")


@pytest.mark.asyncio
async def test_heartbeat():
    """Test heartbeat functionality"""
    stream = AGUIStreamManager(heartbeat_interval=1)
    
    # Don't emit events, wait for heartbeat
    received_heartbeat = False
    
    async def check_heartbeat():
        nonlocal received_heartbeat
        async for data in stream.stream_events():
            if ": heartbeat" in data:
                received_heartbeat = True
                stream.active = False
                break
    
    # Run with timeout
    try:
        await asyncio.wait_for(check_heartbeat(), timeout=3)
    except asyncio.TimeoutError:
        pass
    
    assert received_heartbeat, "Heartbeat not received"


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_stream_manager())
    asyncio.run(test_event_formatting())
    asyncio.run(test_heartbeat())
    print("✅ All tests passed!")