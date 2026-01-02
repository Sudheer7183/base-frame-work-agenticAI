"""
Async Cost Tracker Service - COMPLETE IMPLEMENTATION
Tracks LLM usage and costs in async context

File: backend/app/services/cost_tracker.py
Version: 2.0 COMPLETE
Author: Computational Audit Module
Date: 2025-12-31

INTEGRATION: Copy to backend/app/services/cost_tracker.py
"""

import asyncio
import logging
import hashlib
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.computational_audit import (
    ComputationalAuditUsage,
    ComputationalAuditCostSummary,
    ModelPricing
)

logger = logging.getLogger(__name__)


class AsyncCostTracker:
    """
    Async cost tracking service
    
    Integrates with AsyncLangGraphExecutor for automatic cost tracking.
    All methods are async-safe for use in your async execution flow.
    
    Features:
    - Automatic pricing lookup with caching
    - Async-safe database operations
    - Cost aggregation per execution
    - HITL cost tracking
    - Infrastructure cost tracking
    - Comprehensive error handling
    
    Usage:
        tracker = AsyncCostTracker(db)
        
        # Track LLM usage
        usage = await tracker.track_llm_usage(
            execution_id="exec_123",
            agent_id=1,
            stage_name="planning",
            model_provider="openai",
            model_name="gpt-4",
            input_tokens=1000,
            output_tokens=500
        )
        
        # Finalize when execution completes
        await tracker.finalize_execution_costs(
            execution_id="exec_123",
            started_at=start_time,
            completed_at=end_time
        )
    """
    
    def __init__(self, db: Session):
        """
        Initialize cost tracker
        
        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self._pricing_cache: Dict[str, Tuple[Decimal, Decimal]] = {}
        logger.info("AsyncCostTracker initialized")
    
    async def get_model_pricing(
        self,
        model_provider: str,
        model_name: str
    ) -> Tuple[Decimal, Decimal]:
        """
        Get model pricing (async-safe with caching)
        
        Queries database for current pricing, with intelligent caching
        to avoid repeated queries for the same model.
        
        Args:
            model_provider: Provider (openai, anthropic, self-hosted)
            model_name: Model name (gpt-4, claude-3-opus, etc.)
            
        Returns:
            Tuple of (input_cost_per_1k, output_cost_per_1k)
            
        Example:
            input_cost, output_cost = await tracker.get_model_pricing("openai", "gpt-4")
            # Returns: (Decimal('0.03'), Decimal('0.06'))
        """
        cache_key = f"{model_provider}:{model_name}"
        
        # Check cache first
        if cache_key in self._pricing_cache:
            logger.debug(f"Using cached pricing for {cache_key}")
            return self._pricing_cache[cache_key]
        
        # Query database in thread pool (async-safe)
        def _query_pricing():
            pricing = self.db.query(ModelPricing).filter(
                ModelPricing.model_provider == model_provider,
                ModelPricing.model_name == model_name,
                ModelPricing.active == True,
                ModelPricing.effective_from <= datetime.utcnow()
            ).order_by(ModelPricing.effective_from.desc()).first()
            
            if not pricing:
                logger.warning(
                    f"No pricing found for {model_provider}:{model_name}, using defaults"
                )
                # Fallback defaults (conservative estimates)
                return (Decimal("0.001"), Decimal("0.002"))
            
            return (pricing.input_cost_per_1k, pricing.output_cost_per_1k)
        
        result = await asyncio.to_thread(_query_pricing)
        
        # Cache result
        self._pricing_cache[cache_key] = result
        logger.debug(f"Cached pricing for {cache_key}: ${result[0]}, ${result[1]}")
        
        return result
    
    async def track_llm_usage(
        self,
        execution_id: str,
        agent_id: int,
        stage_name: str,
        model_provider: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: Optional[int] = None,
        step_number: Optional[int] = None,
        node_name: Optional[str] = None,
        model_version: Optional[str] = None,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        retry_count: int = 0,
        retry_reason: Optional[str] = None,
        tool_calls_count: int = 0,
        tool_calls_data: Optional[Dict] = None,
        finish_reason: Optional[str] = None,
        prompt: Optional[str] = None,
        ttft_ms: Optional[int] = None,
        prompt_template_id: Optional[str] = None,
        **kwargs
    ) -> Optional[ComputationalAuditUsage]:
        """
        Track LLM usage (async-safe)
        
        Called automatically from AsyncLangGraphExecutor for each LLM call.
        Creates a usage record and updates the cost summary.
        
        Args:
            execution_id: Execution ID
            agent_id: Agent ID
            stage_name: Workflow stage (e.g., 'planning', 'execution')
            model_provider: Provider (openai, anthropic, self-hosted)
            model_name: Model name (gpt-4, claude-3-opus, etc.)
            input_tokens: Input token count
            output_tokens: Output token count
            latency_ms: Response latency in milliseconds
            step_number: Step number within stage
            node_name: LangGraph node name
            model_version: Model version
            cache_read_tokens: Cache read tokens (Anthropic)
            cache_write_tokens: Cache write tokens (Anthropic)
            retry_count: Number of retries
            retry_reason: Reason for retry
            tool_calls_count: Number of tool calls
            tool_calls_data: Tool call details
            finish_reason: Why generation stopped
            prompt: Prompt text (for hashing)
            ttft_ms: Time to first token
            prompt_template_id: Template ID if using templates
            **kwargs: Additional metadata
            
        Returns:
            ComputationalAuditUsage record or None if error
            
        Example:
            usage = await tracker.track_llm_usage(
                execution_id="exec_abc123",
                agent_id=1,
                stage_name="planning",
                model_provider="openai",
                model_name="gpt-4",
                input_tokens=1000,
                output_tokens=500,
                latency_ms=2500
            )
        """
        try:
            # Get pricing
            input_cost, output_cost = await self.get_model_pricing(
                model_provider, model_name
            )
            
            # Calculate total tokens
            total_tokens = input_tokens + output_tokens + cache_read_tokens + cache_write_tokens
            
            # Calculate cost
            computed_cost = (
                Decimal(input_tokens) * input_cost / 1000 +
                Decimal(output_tokens) * output_cost / 1000
            )
            
            # Add cache costs
            # Cache read typically 10% of input cost
            # Cache write typically 25% of input cost
            if cache_read_tokens > 0:
                computed_cost += Decimal(cache_read_tokens) * input_cost * Decimal("0.1") / 1000
            if cache_write_tokens > 0:
                computed_cost += Decimal(cache_write_tokens) * input_cost * Decimal("0.25") / 1000
            
            # Generate prompt hash if prompt provided
            prompt_hash = None
            if prompt:
                prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]
            
            # Create audit record (in thread pool for async safety)
            def _create_record():
                usage = ComputationalAuditUsage(
                    execution_id=execution_id,
                    agent_id=agent_id,
                    stage_name=stage_name,
                    step_number=step_number,
                    node_name=node_name,
                    model_provider=model_provider,
                    model_name=model_name,
                    model_version=model_version,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cache_read_tokens=cache_read_tokens,
                    cache_write_tokens=cache_write_tokens,
                    total_tokens=total_tokens,
                    unit_cost_input=input_cost,
                    unit_cost_output=output_cost,
                    computed_cost_usd=computed_cost,
                    latency_ms=latency_ms,
                    ttft_ms=ttft_ms,
                    retry_count=retry_count,
                    retry_reason=retry_reason,
                    tool_calls_count=tool_calls_count,
                    tool_calls_data=tool_calls_data,
                    finish_reason=finish_reason,
                    prompt_hash=prompt_hash,
                    prompt_template_id=prompt_template_id,
                    model_metadata=kwargs.get('model_metadata')
                )
                
                self.db.add(usage)
                self.db.commit()
                self.db.refresh(usage)
                
                logger.info(
                    f"Tracked LLM usage: {model_provider}:{model_name}, "
                    f"tokens={total_tokens} (in={input_tokens}, out={output_tokens}), "
                    f"cost=${computed_cost:.6f}, latency={latency_ms}ms"
                )
                
                return usage
            
            usage = await asyncio.to_thread(_create_record)
            
            # Update cost summary (async)
            await self._update_cost_summary(execution_id, agent_id)
            
            return usage
            
        except Exception as e:
            logger.error(f"Error tracking LLM usage: {e}", exc_info=True)
            # Don't fail execution if cost tracking fails
            return None
    
    async def _update_cost_summary(self, execution_id: str, agent_id: int):
        """
        Update or create cost summary (async-safe)
        
        Aggregates all LLM usage for the execution and updates
        the cost summary table.
        
        Args:
            execution_id: Execution ID
            agent_id: Agent ID
        """
        try:
            def _update():
                # Aggregate from individual usage records
                aggregates = self.db.query(
                    func.sum(ComputationalAuditUsage.computed_cost_usd).label('total_cost'),
                    func.sum(ComputationalAuditUsage.total_tokens).label('total_tokens'),
                    func.count(ComputationalAuditUsage.id).label('call_count')
                ).filter(
                    ComputationalAuditUsage.execution_id == execution_id
                ).first()
                
                # Get or create summary
                summary = self.db.query(ComputationalAuditCostSummary).filter(
                    ComputationalAuditCostSummary.execution_id == execution_id
                ).first()
                
                if not summary:
                    summary = ComputationalAuditCostSummary(
                        execution_id=execution_id,
                        agent_id=agent_id
                    )
                    self.db.add(summary)
                
                # Update LLM costs
                summary.total_llm_cost_usd = aggregates.total_cost or Decimal("0")
                summary.total_tokens = aggregates.total_tokens or 0
                summary.total_llm_calls = aggregates.call_count or 0
                
                # Recalculate total cost
                summary.total_cost_usd = (
                    summary.total_llm_cost_usd +
                    summary.hitl_cost_usd +
                    summary.infrastructure_cost_usd
                )
                
                summary.updated_at = datetime.utcnow()
                
                self.db.commit()
                
                logger.debug(
                    f"Updated cost summary for {execution_id}: "
                    f"${summary.total_cost_usd:.6f} "
                    f"({summary.total_llm_calls} calls, {summary.total_tokens} tokens)"
                )
            
            await asyncio.to_thread(_update)
            
        except Exception as e:
            logger.error(f"Error updating cost summary: {e}", exc_info=True)
    
    async def track_hitl_cost(
        self,
        execution_id: str,
        duration_seconds: int,
        hourly_rate: Optional[Decimal] = None
    ):
        """
        Track HITL (Human-in-the-Loop) cost (async-safe)
        
        Tracks costs for human review/intervention during execution.
        
        Args:
            execution_id: Execution ID
            duration_seconds: Duration of human review in seconds
            hourly_rate: Hourly rate (uses tenant config if not provided)
            
        Example:
            await tracker.track_hitl_cost(
                execution_id="exec_123",
                duration_seconds=300,  # 5 minutes
                hourly_rate=Decimal("50.00")
            )
        """
        try:
            def _track():
                # Get hourly rate from tenant config if not provided
                if hourly_rate is None:
                    from app.models.computational_audit import TenantPricingConfig
                    config = self.db.query(TenantPricingConfig).first()
                    rate = config.hitl_hourly_rate_usd if config else Decimal("50.00")
                else:
                    rate = hourly_rate
                
                # Calculate cost
                cost = (Decimal(duration_seconds) / 3600) * rate
                
                # Update summary
                summary = self.db.query(ComputationalAuditCostSummary).filter(
                    ComputationalAuditCostSummary.execution_id == execution_id
                ).first()
                
                if summary:
                    summary.hitl_cost_usd += cost
                    summary.hitl_duration_seconds += duration_seconds
                    summary.total_cost_usd = (
                        summary.total_llm_cost_usd +
                        summary.hitl_cost_usd +
                        summary.infrastructure_cost_usd
                    )
                    self.db.commit()
                    
                    logger.info(
                        f"Tracked HITL for {execution_id}: "
                        f"${cost:.2f} ({duration_seconds}s @ ${rate}/hr)"
                    )
            
            await asyncio.to_thread(_track)
            
        except Exception as e:
            logger.error(f"Error tracking HITL cost: {e}", exc_info=True)
    
    async def track_infrastructure_cost(
        self,
        execution_id: str,
        cost: Decimal,
        description: Optional[str] = None
    ):
        """
        Track infrastructure/self-hosted costs (async-safe)
        
        Tracks GPU/hardware costs for self-hosted models.
        
        Args:
            execution_id: Execution ID
            cost: Infrastructure cost in USD
            description: Cost description
            
        Example:
            await tracker.track_infrastructure_cost(
                execution_id="exec_123",
                cost=Decimal("0.50"),
                description="4x A100 GPUs for 2.5 seconds"
            )
        """
        try:
            def _track():
                summary = self.db.query(ComputationalAuditCostSummary).filter(
                    ComputationalAuditCostSummary.execution_id == execution_id
                ).first()
                
                if summary:
                    summary.infrastructure_cost_usd += cost
                    summary.total_cost_usd = (
                        summary.total_llm_cost_usd +
                        summary.hitl_cost_usd +
                        summary.infrastructure_cost_usd
                    )
                    self.db.commit()
                    
                    logger.info(
                        f"Tracked infrastructure for {execution_id}: "
                        f"${cost:.2f} ({description})"
                    )
            
            await asyncio.to_thread(_track)
            
        except Exception as e:
            logger.error(f"Error tracking infrastructure cost: {e}", exc_info=True)
    
    async def finalize_execution_costs(
        self,
        execution_id: str,
        started_at: datetime,
        completed_at: datetime
    ):
        """
        Finalize costs when execution completes (async-safe)
        
        Sets execution timestamps in cost summary. Call this at the
        end of your AsyncLangGraphExecutor's execute_with_streaming method.
        
        Args:
            execution_id: Execution ID
            started_at: Execution start time
            completed_at: Execution completion time
            
        Example:
            await tracker.finalize_execution_costs(
                execution_id="exec_123",
                started_at=start_time,
                completed_at=datetime.utcnow()
            )
        """
        try:
            def _finalize():
                summary = self.db.query(ComputationalAuditCostSummary).filter(
                    ComputationalAuditCostSummary.execution_id == execution_id
                ).first()
                
                if summary:
                    summary.execution_started_at = started_at
                    summary.execution_completed_at = completed_at
                    self.db.commit()
                    
                    duration = (completed_at - started_at).total_seconds()
                    
                    logger.info(
                        f"Finalized costs for {execution_id}: "
                        f"${summary.total_cost_usd:.6f} "
                        f"({summary.total_tokens} tokens, {summary.total_llm_calls} calls, "
                        f"{duration:.1f}s)"
                    )
                else:
                    logger.warning(f"No cost summary found for {execution_id}")
            
            await asyncio.to_thread(_finalize)
            
        except Exception as e:
            logger.error(f"Error finalizing costs: {e}", exc_info=True)
    
    async def get_execution_cost(
        self,
        execution_id: str
    ) -> Optional[ComputationalAuditCostSummary]:
        """
        Get cost summary for an execution (async-safe)
        
        Args:
            execution_id: Execution ID
            
        Returns:
            Cost summary or None if not found
            
        Example:
            summary = await tracker.get_execution_cost("exec_123")
            if summary:
                print(f"Total cost: ${summary.total_cost_usd}")
        """
        try:
            def _get():
                return self.db.query(ComputationalAuditCostSummary).filter(
                    ComputationalAuditCostSummary.execution_id == execution_id
                ).first()
            
            return await asyncio.to_thread(_get)
            
        except Exception as e:
            logger.error(f"Error getting execution cost: {e}")
            return None
    
    def clear_pricing_cache(self):
        """
        Clear pricing cache
        
        Call this when pricing data changes to force fresh lookups.
        
        Example:
            tracker.clear_pricing_cache()
        """
        self._pricing_cache.clear()
        logger.info("Pricing cache cleared")


# END OF FILE - AsyncCostTracker complete (574 lines)
