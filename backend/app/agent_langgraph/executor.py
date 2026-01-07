"""
LangGraph Executor - FIXED JSON Serialization
Handles datetime serialization in input_data
"""

import asyncio
import logging
import uuid
import json
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.agent import AgentConfig, AgentExecutionLog
from app.agent_langgraph.graph_builder import create_new_agent_graph
from app.agent_langgraph.state import StateManager
from app.agui.streaming import AGUIStreamManager
from app.agui.transformer import EventTransformer
from app.agui.events import (
    create_agent_status_event,
    create_completion_event,
    create_error_event
)

logger = logging.getLogger(__name__)


def serialize_for_json(obj):
    """
    Recursively serialize objects for JSON storage
    
    Handles datetime objects and other non-serializable types
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [serialize_for_json(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        # Handle custom objects
        return serialize_for_json(obj.__dict__)
    else:
        return obj


class AsyncLangGraphExecutor:
    """
    Async LangGraph executor with AG-UI streaming and cost tracking
    
    Features:
    - Fully async execution
    - Event streaming via AG-UI protocol
    - Automatic LLM cost tracking
    - JSON serialization handling
    - Error handling and recovery
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.state_manager = StateManager()
    
    async def execute(
        self,
        agent_id: int,
        input_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute agent without streaming (for direct API calls)
        """
        stream = AGUIStreamManager()
        
        return await self.execute_with_streaming(
            agent_id=agent_id,
            input_data=input_data,
            stream=stream,
            user_id=user_id
        )
    
    async def execute_with_streaming(
        self,
        agent_id: int,
        input_data: Dict[str, Any],
        stream: AGUIStreamManager,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute agent with AG-UI streaming and cost tracking
        """
        # Get agent
        agent = self.db.query(AgentConfig).filter(AgentConfig.id == agent_id).first()
        
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        if not agent.active:
            raise ValueError(f"Agent {agent.name} is not active")
        
        # Get builder config
        builder_config = self.db.execute(text("""
            SELECT * FROM agent_builder_configs 
            WHERE agent_id = :agent_id 
            ORDER BY version DESC LIMIT 1
        """), {"agent_id": agent_id}).fetchone()
        
        # Merge configs
        if builder_config:
            config = self._merge_configs(agent.config, dict(builder_config))
        else:
            config = agent.config
        
        # Generate execution ID
        execution_id = f"exec_{uuid.uuid4().hex[:16]}"
        start_time = datetime.utcnow()
        
        logger.info(f"Starting execution {execution_id} for agent {agent.name} (workflow: {agent.workflow})")
        
        # Set stream ID
        stream.stream_id = execution_id
        
        # ✅ FIX: Serialize input_data to handle datetime objects
        serialized_input = serialize_for_json(input_data)
        
        # Create execution log
        log = AgentExecutionLog(
            agent_id=agent_id,
            execution_id=execution_id,
            status="running",
            input_data=serialized_input,  # ✅ Use serialized version
            started_by=user_id,
            started_at=start_time
        )
        
        # ✅ FIX: Separate add and commit operations
        await asyncio.to_thread(self.db.add, log)
        await asyncio.to_thread(self.db.commit)
        
        # Initialize cost tracking
        total_llm_cost = 0.0
        total_llm_calls = 0
        total_tokens = 0
        
        try:
            # Send status event
            await stream.emit_event(
                create_agent_status_event(
                    status="running",
                    message=f"Agent {agent.name} execution started"
                )
            )
            
            # Create graph
            logger.info(f"Creating graph for workflow type: {agent.workflow}")
            graph = await asyncio.to_thread(
                create_new_agent_graph(agent),
                agent.config
            )
            
            # Initialize state
            initial_state = await asyncio.to_thread(
                self.state_manager.initialize_state,
                agent_id=agent_id,
                agent_name=agent.name,
                execution_id=execution_id,
                input_data=input_data,
                config=agent.config
            )
            
            # Add stream reference to state for HITL
            initial_state["_stream"] = stream
            
            # Configure for streaming
            run_config = {
                "configurable": {
                    "thread_id": input_data.get("thread_id", execution_id)
                }
            }
            
            # Create event transformer
            transformer = EventTransformer()
            
            # Stream execution
            final_state = None
            current_stage = "initialization"
            
            logger.info(f"Starting LangGraph execution with config: {run_config}")
            
            async for event in graph.astream_events(
                initial_state,
                config=run_config,
                version="v2"
            ):
                # Transform event
                agui_event = transformer.transform_langgraph_event(event)
                
                if agui_event:
                    await stream.emit_event(agui_event)
                
                event_type = event.get("event")
                
                # Log important events
                if event_type in ["on_chain_start", "on_chain_end"]:
                    logger.debug(f"Event: {event_type} - {event.get('name', 'unknown')}")
                
                # Update stage
                tags = event.get("tags", [])
                if tags:
                    current_stage = tags[0]
                
                # Track LLM usage
                if event_type == "on_chat_model_end":
                    cost_data = await self._track_llm_usage(
                        event=event,
                        execution_id=execution_id,
                        agent_id=agent_id,
                        stage_name=current_stage
                    )
                    
                    if cost_data:
                        total_llm_cost += cost_data['cost']
                        total_llm_calls += 1
                        total_tokens += cost_data['total_tokens']
                
                # Capture final state
                if event_type == "on_chain_end":
                    output = event.get("data", {}).get("output")
                    if output:
                        final_state = output
                        logger.debug(f"Captured final state: {type(final_state)}")
            
            # If no final state, invoke directly
            if not final_state:
                logger.info("No final state from streaming, invoking graph directly")
                final_state = await graph.ainvoke(initial_state, config=run_config)
            
            # Calculate duration
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Finalize costs
            await self._finalize_execution_costs(
                execution_id=execution_id,
                agent_id=agent_id,
                total_llm_cost=total_llm_cost,
                total_llm_calls=total_llm_calls,
                total_tokens=total_tokens,
                started_at=start_time,
                completed_at=end_time
            )
            
            # ✅ FIX: Serialize output_data before storing
            output = final_state.get("output_data") if isinstance(final_state, dict) else final_state
            serialized_output = serialize_for_json(output)
            
            # Update log
            log.status = "completed"
            log.output_data = serialized_output
            log.duration_ms = duration_ms
            log.completed_at = end_time
            await asyncio.to_thread(self.db.commit)
            
            logger.info(
                f"Execution {execution_id} completed in {duration_ms}ms | "
                f"Cost: ${total_llm_cost:.6f} | Tokens: {total_tokens} | LLM calls: {total_llm_calls}"
            )
            
            # Send completion event
            await stream.emit_event(
                create_completion_event(
                    final_output=output,
                    metadata={
                        "execution_id": execution_id,
                        "duration_ms": duration_ms,
                        "agent_name": agent.name,
                        "workflow": agent.workflow,
                        "cost_usd": round(total_llm_cost, 6),
                        "total_tokens": total_tokens,
                        "llm_calls": total_llm_calls
                    }
                )
            )
            
            return {
                "execution_id": execution_id,
                "status": "completed",
                "output": output,
                "duration_ms": duration_ms,
                "cost_usd": round(total_llm_cost, 6),
                "total_tokens": total_tokens,
                "llm_calls": total_llm_calls
            }
            
        except Exception as e:
            logger.error(f"Execution {execution_id} failed: {e}", exc_info=True)
            
            # Update log
            log.status = "failed"
            log.error = str(e)
            log.completed_at = datetime.utcnow()
            await asyncio.to_thread(self.db.commit)
            
            # Send error event
            await stream.emit_event(
                create_error_event(
                    error_message=str(e),
                    error_code="EXECUTION_ERROR",
                    recoverable=False
                )
            )
            
            raise
    
    async def _track_llm_usage(
        self,
        event: Dict[str, Any],
        execution_id: str,
        agent_id: int,
        stage_name: str
    ) -> Optional[Dict[str, Any]]:
        """Track LLM usage from events"""
        try:
            data = event.get('data', {})
            output = data.get('output', {})
            
            usage = (
                output.get('usage_metadata') or 
                output.get('usage') or 
                output.get('token_usage') or 
                {}
            )
            
            if not usage:
                return None
            
            input_tokens = usage.get('input_tokens') or usage.get('prompt_tokens') or 0
            output_tokens = usage.get('output_tokens') or usage.get('completion_tokens') or 0
            cache_read_tokens = usage.get('cache_read_tokens', 0)
            cache_write_tokens = usage.get('cache_creation_input_tokens', 0)
            
            total_tokens = input_tokens + output_tokens
            
            if total_tokens == 0:
                return None
            
            model_name = (
                output.get('model') or 
                event.get('metadata', {}).get('ls_model_name') or 
                event.get('name', 'unknown')
            )
            
            provider = self._extract_provider(model_name)
            latency_ms = event.get('metadata', {}).get('duration_ms')
            
            schema_result = await asyncio.to_thread(
                lambda: self.db.execute(text("SELECT current_schema()")).scalar()
            )
            current_schema = schema_result
            
            cost_query = text("""
                SELECT public.calculate_llm_cost(
                    :provider,
                    :model,
                    :input_tokens,
                    :output_tokens,
                    CURRENT_DATE
                )
            """)
            
            cost_result = await asyncio.to_thread(
                lambda: self.db.execute(cost_query, {
                    "provider": provider,
                    "model": model_name,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }).scalar()
            )
            
            computed_cost = float(cost_result or 0)
            
            pricing_query = text("""
                SELECT 
                    input_cost_per_1k,
                    output_cost_per_1k
                FROM public.model_pricing
                WHERE model_provider = :provider
                    AND model_name = :model
                    AND active = true
                ORDER BY effective_from DESC
                LIMIT 1
            """)
            
            pricing_result = await asyncio.to_thread(
                lambda: self.db.execute(pricing_query, {
                    "provider": provider,
                    "model": model_name
                }).fetchone()
            )
            
            if pricing_result:
                unit_cost_input = float(pricing_result[0])
                unit_cost_output = float(pricing_result[1])
            else:
                unit_cost_input = 0.0
                unit_cost_output = 0.0
                logger.warning(f"No pricing found for {provider}:{model_name}")
            
            insert_query = text(f"""
                INSERT INTO "{current_schema}".computational_audit_usage (
                    execution_id,
                    agent_id,
                    stage_name,
                    model_provider,
                    model_name,
                    input_tokens,
                    output_tokens,
                    cache_read_tokens,
                    cache_write_tokens,
                    total_tokens,
                    unit_cost_input,
                    unit_cost_output,
                    computed_cost_usd,
                    latency_ms,
                    created_at
                ) VALUES (
                    :execution_id,
                    :agent_id,
                    :stage_name,
                    :provider,
                    :model,
                    :input_tokens,
                    :output_tokens,
                    :cache_read_tokens,
                    :cache_write_tokens,
                    :total_tokens,
                    :unit_cost_input,
                    :unit_cost_output,
                    :computed_cost,
                    :latency_ms,
                    NOW()
                )
            """)
            
            await asyncio.to_thread(
                lambda: self.db.execute(insert_query, {
                    "execution_id": execution_id,
                    "agent_id": agent_id,
                    "stage_name": stage_name,
                    "provider": provider,
                    "model": model_name,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cache_read_tokens": cache_read_tokens,
                    "cache_write_tokens": cache_write_tokens,
                    "total_tokens": total_tokens,
                    "unit_cost_input": unit_cost_input,
                    "unit_cost_output": unit_cost_output,
                    "computed_cost": computed_cost,
                    "latency_ms": latency_ms
                })
            )
            
            await asyncio.to_thread(self.db.commit)
            
            logger.debug(
                f"Tracked LLM usage: {provider}:{model_name} | "
                f"Tokens: {total_tokens} | Cost: ${computed_cost:.6f}"
            )
            
            return {
                'cost': computed_cost,
                'total_tokens': total_tokens,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'provider': provider,
                'model': model_name
            }
            
        except Exception as e:
            logger.error(f"Failed to track LLM usage: {e}", exc_info=True)
            return None
    
    async def _finalize_execution_costs(
        self,
        execution_id: str,
        agent_id: int,
        total_llm_cost: float,
        total_llm_calls: int,
        total_tokens: int,
        started_at: datetime,
        completed_at: datetime
    ):
        """Create cost summary record"""
        try:
            schema_result = await asyncio.to_thread(
                lambda: self.db.execute(text("SELECT current_schema()")).scalar()
            )
            current_schema = schema_result
            
            insert_query = text(f"""
                INSERT INTO "{current_schema}".computational_audit_cost_summary (
                    execution_id,
                    agent_id,
                    total_llm_cost_usd,
                    total_tokens,
                    total_llm_calls,
                    execution_started_at,
                    execution_completed_at,
                    total_cost_usd,
                    created_at
                ) VALUES (
                    :execution_id,
                    :agent_id,
                    :total_llm_cost,
                    :total_tokens,
                    :total_llm_calls,
                    :started_at,
                    :completed_at,
                    :total_cost,
                    NOW()
                )
                ON CONFLICT (execution_id) DO UPDATE SET
                    total_llm_cost_usd = EXCLUDED.total_llm_cost_usd,
                    total_tokens = EXCLUDED.total_tokens,
                    total_llm_calls = EXCLUDED.total_llm_calls,
                    total_cost_usd = EXCLUDED.total_cost_usd,
                    updated_at = NOW()
            """)
            
            await asyncio.to_thread(
                lambda: self.db.execute(insert_query, {
                    "execution_id": execution_id,
                    "agent_id": agent_id,
                    "total_llm_cost": total_llm_cost,
                    "total_tokens": total_tokens,
                    "total_llm_calls": total_llm_calls,
                    "started_at": started_at,
                    "completed_at": completed_at,
                    "total_cost": total_llm_cost
                })
            )
            
            await asyncio.to_thread(self.db.commit)
            
            logger.info(
                f"Finalized cost summary for {execution_id}: "
                f"${total_llm_cost:.6f} | {total_tokens} tokens | {total_llm_calls} calls"
            )
            
        except Exception as e:
            logger.error(f"Failed to finalize execution costs: {e}", exc_info=True)
    
    def _extract_provider(self, model_name: str) -> str:
        """Extract provider from model name"""
        model_lower = model_name.lower()
        
        if 'gpt' in model_lower or 'davinci' in model_lower or 'turbo' in model_lower:
            return 'openai'
        elif 'claude' in model_lower:
            return 'anthropic'
        elif 'gemini' in model_lower or 'palm' in model_lower:
            return 'google'
        elif 'mistral' in model_lower or 'mixtral' in model_lower:
            return 'mistral'
        elif 'llama' in model_lower:
            return 'meta'
        elif 'command' in model_lower:
            return 'cohere'
        else:
            return 'unknown'
    
    def _merge_configs(self, base_config: Dict, builder_config: Dict) -> Dict:
        """Merge configs"""
        merged = base_config.copy()
        merged.update(builder_config)
        return merged