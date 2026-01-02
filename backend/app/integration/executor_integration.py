"""
AsyncLangGraphExecutor Integration Guide - COMPLETE
Complete code for integrating cost tracking into your executor

File: integration/executor_integration.py
Version: 2.0 COMPLETE

This file contains the COMPLETE integration code for your
AsyncLangGraphExecutor. Copy the relevant sections into your
backend/app/agent_langgraph/executor.py file.
"""

# =============================================================================
# STEP 1: Add Imports (at top of executor.py)
# =============================================================================

# Add these imports to your executor.py
from app.services.cost_tracker import AsyncCostTracker
from app.services.token_parser import TokenParser
from app.services.self_hosted_calculator import SelfHostedCostCalculator


# =============================================================================
# STEP 2: Initialize in __init__ method
# =============================================================================

class AsyncLangGraphExecutor:
    """Your existing executor class"""
    
    def __init__(self, db: Session):
        """
        Initialize executor
        
        MODIFY THIS METHOD to add cost tracking
        """
        # Your existing initialization
        self.db = db
        self.state_manager = StateManager()
        
        # ADD THESE THREE LINES:
        self.cost_tracker = AsyncCostTracker(db)
        self.token_parser = TokenParser()
        self.self_hosted_calc = SelfHostedCostCalculator(db)  # Optional, for self-hosted models
        
        # Rest of your initialization...


# =============================================================================
# STEP 3: Track costs in execute_with_streaming method
# =============================================================================

    async def execute_with_streaming(
        self,
        agent_id: int,
        initial_state: Dict[str, Any],
        stream: AsyncEventStream
    ) -> Dict[str, Any]:
        """
        Execute agent with streaming
        
        MODIFY THIS METHOD to add cost tracking
        """
        # Your existing code to build graph
        graph = self._build_graph(agent_id)
        config = {"configurable": {"thread_id": execution_id}}
        
        # ADD THIS: Track start time
        start_time = datetime.utcnow()
        
        try:
            # Your existing streaming loop
            async for event in graph.astream_events(initial_state, config=config, version="v2"):
                # Your existing event handling
                agui_event = transformer.transform_langgraph_event(event)
                if agui_event:
                    await stream.emit_event(agui_event)
                
                # ADD THIS: Track costs for this event
                await self._track_event_costs(event, execution_id, agent_id)
            
            # ADD THIS: Finalize costs when done
            end_time = datetime.utcnow()
            await self.cost_tracker.finalize_execution_costs(
                execution_id=execution_id,
                started_at=start_time,
                completed_at=end_time
            )
            
            # Your existing return
            return final_state
            
        except Exception as e:
            # Your existing error handling
            raise


# =============================================================================
# STEP 4: Add cost tracking method (NEW METHOD)
# =============================================================================

    async def _track_event_costs(
        self,
        event: Dict[str, Any],
        execution_id: str,
        agent_id: int
    ):
        """
        Track costs from LangGraph events
        
        ADD THIS NEW METHOD to your executor class
        
        This method automatically extracts token counts and costs
        from LangGraph events and tracks them.
        """
        try:
            event_type = event.get('event')
            
            # Track LLM calls
            if event_type == 'on_chat_model_end':
                data = event.get('data', {})
                output = data.get('output', {})
                
                # Parse tokens using TokenParser
                provider = self._detect_provider(event)
                input_tokens, output_tokens = self.token_parser.parse_generic(
                    output,
                    provider=provider
                )
                
                # Only track if we got tokens
                if input_tokens > 0 or output_tokens > 0:
                    # Extract metadata
                    name = event.get('name', 'unknown')
                    tags = event.get('tags', [])
                    stage_name = tags[0] if tags else 'processing'
                    
                    # Get latency if available
                    latency_ms = None
                    if 'metadata' in data:
                        latency_ms = data['metadata'].get('duration_ms')
                    
                    # Track the usage
                    await self.cost_tracker.track_llm_usage(
                        execution_id=execution_id,
                        agent_id=agent_id,
                        stage_name=stage_name,
                        model_provider=provider,
                        model_name=name,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        latency_ms=latency_ms,
                        node_name=event.get('name')
                    )
                    
        except Exception as e:
            # Don't fail execution if cost tracking fails
            logger.error(f"Error tracking event costs: {e}", exc_info=True)


    def _detect_provider(self, event: Dict[str, Any]) -> str:
        """
        Detect LLM provider from event
        
        ADD THIS NEW METHOD to your executor class
        """
        name = event.get('name', '').lower()
        
        # Check model name for provider hints
        if 'gpt' in name or 'openai' in name or 'turbo' in name:
            return 'openai'
        elif 'claude' in name or 'anthropic' in name:
            return 'anthropic'
        elif 'llama' in name or 'mistral' in name or 'mixtral' in name:
            return 'self-hosted'
        
        # Check metadata if available
        data = event.get('data', {})
        if 'metadata' in data:
            model_info = data['metadata'].get('model', '')
            if 'gpt' in model_info.lower():
                return 'openai'
            if 'claude' in model_info.lower():
                return 'anthropic'
        
        return 'unknown'


# =============================================================================
# STEP 5: (Optional) Track self-hosted models
# =============================================================================

    async def _track_self_hosted_model(
        self,
        event: Dict[str, Any],
        execution_id: str,
        agent_id: int
    ):
        """
        Track self-hosted model usage with infrastructure costs
        
        ADD THIS NEW METHOD if you use self-hosted models
        
        Call this instead of _track_event_costs for self-hosted models
        """
        try:
            if event.get('event') == 'on_chat_model_end':
                data = event.get('data', {})
                output = data.get('output', {})
                
                # Parse tokens
                input_tokens, output_tokens = self.token_parser.parse_generic(output)
                
                if input_tokens > 0 or output_tokens > 0:
                    # Get model name and hardware config
                    model_name = event.get('name', 'unknown')
                    
                    # Get hardware config from your configuration
                    # This example assumes you store it in agent config
                    hardware_config = {
                        'gpu_type': 'A100',  # Get from your config
                        'gpu_count': 4,      # Get from your config
                        'memory_gb': 320     # Get from your config
                    }
                    
                    # Get inference time
                    inference_time_ms = data.get('metadata', {}).get('duration_ms', 0)
                    
                    # Track with infrastructure costs
                    result = await self.self_hosted_calc.track_self_hosted_usage(
                        execution_id=execution_id,
                        agent_id=agent_id,
                        model_name=model_name,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        inference_time_ms=inference_time_ms,
                        hardware_config=hardware_config
                    )
                    
                    logger.info(
                        f"Self-hosted tracking: ${result['infrastructure_cost']:.4f} "
                        f"(saved ${result['savings']:.4f} vs cloud)"
                    )
                    
        except Exception as e:
            logger.error(f"Error tracking self-hosted model: {e}", exc_info=True)


# =============================================================================
# COMPLETE EXAMPLE: Full executor with cost tracking
# =============================================================================

"""
Here's a complete example of what your modified executor.py should look like:

```python
# backend/app/agent_langgraph/executor.py

from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session

# Your existing imports
from app.agent_langgraph.state_manager import StateManager
from app.agent_langgraph.event_stream import AsyncEventStream

# NEW: Add these imports
from app.services.cost_tracker import AsyncCostTracker
from app.services.token_parser import TokenParser
from app.services.self_hosted_calculator import SelfHostedCostCalculator


class AsyncLangGraphExecutor:
    def __init__(self, db: Session):
        self.db = db
        self.state_manager = StateManager()
        
        # NEW: Initialize cost tracking
        self.cost_tracker = AsyncCostTracker(db)
        self.token_parser = TokenParser()
        self.self_hosted_calc = SelfHostedCostCalculator(db)
    
    async def execute_with_streaming(
        self,
        agent_id: int,
        initial_state: Dict[str, Any],
        stream: AsyncEventStream
    ) -> Dict[str, Any]:
        execution_id = initial_state.get('execution_id')
        graph = self._build_graph(agent_id)
        config = {"configurable": {"thread_id": execution_id}}
        
        # NEW: Track start time
        start_time = datetime.utcnow()
        
        try:
            async for event in graph.astream_events(initial_state, config=config, version="v2"):
                agui_event = transformer.transform_langgraph_event(event)
                if agui_event:
                    await stream.emit_event(agui_event)
                
                # NEW: Track costs
                await self._track_event_costs(event, execution_id, agent_id)
            
            # NEW: Finalize costs
            end_time = datetime.utcnow()
            await self.cost_tracker.finalize_execution_costs(
                execution_id, start_time, end_time
            )
            
            return final_state
            
        except Exception as e:
            raise
    
    # NEW: Add these methods
    async def _track_event_costs(self, event, execution_id, agent_id):
        # See implementation above
        pass
    
    def _detect_provider(self, event):
        # See implementation above
        pass
```
"""


# =============================================================================
# STEP 6: Register API router in main.py
# =============================================================================

"""
Add this to your backend/app/main.py:

```python
# In your imports section
from app.api.v1 import cost_analytics_api

# In your router registration section (after creating app)
app.include_router(
    cost_analytics_api.router,
    prefix="/api/v1",
    tags=["cost-analytics"]
)
```

Now you'll have these endpoints available:
- GET /api/v1/cost-analytics/summary
- GET /api/v1/cost-analytics/daily-costs
- GET /api/v1/cost-analytics/model-breakdown
- GET /api/v1/cost-analytics/agent-costs
- GET /api/v1/cost-analytics/forecast
- GET /api/v1/cost-analytics/anomalies
- GET /api/v1/cost-analytics/health
"""


# =============================================================================
# That's it! You're done with integration.
# =============================================================================

"""
Summary of changes:
1. Added 3 imports to executor.py
2. Added 3 lines to __init__ method
3. Added 2 lines to execute_with_streaming method
4. Added 2 new methods (_track_event_costs, _detect_provider)
5. Optional: Added 1 method for self-hosted tracking
6. Registered API router in main.py

Total: ~50 lines of code added to integrate complete cost tracking!
"""

# END OF FILE - Integration guide complete (343 lines)
