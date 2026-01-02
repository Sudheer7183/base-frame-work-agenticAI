"""
Computational Audit Models - COMPLETE IMPLEMENTATION
Cost tracking models for LLM usage in multi-tenant environment

File: backend/app/models/computational_audit.py
Version: 2.0 COMPLETE
Author: Computational Audit Module
Date: 2025-12-31

INTEGRATION: Copy to backend/app/models/computational_audit.py
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, JSON, DateTime, 
    ForeignKey, Numeric, Boolean, Text, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# Import from your existing base
from app.models.base import Base, TimestampMixin


# =============================================================================
# MODEL 1: ComputationalAuditUsage
# =============================================================================

class ComputationalAuditUsage(Base, TimestampMixin):
    """
    Track individual LLM calls
    
    Lives in: tenant schemas (tenant_*)
    Purpose: One record per LLM invocation with token counts and costs
    Links to: agent_execution_logs.execution_id, agents.id
    
    Example Usage:
        usage = ComputationalAuditUsage(
            execution_id="exec_abc123",
            agent_id=1,
            stage_name="planning",
            model_provider="openai",
            model_name="gpt-4",
            input_tokens=1000,
            output_tokens=500,
            unit_cost_input=Decimal("0.03"),
            unit_cost_output=Decimal("0.06"),
            computed_cost_usd=Decimal("0.06")
        )
    """
    __tablename__ = "computational_audit_usage"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # =========================================================================
    # Link to existing execution log
    # =========================================================================
    execution_id = Column(
        String(255),
        ForeignKey('agent_execution_logs.execution_id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Links to agent execution log"
    )
    
    # =========================================================================
    # Agent reference
    # =========================================================================
    agent_id = Column(
        Integer,
        ForeignKey('agents.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Agent that made this LLM call"
    )
    
    # =========================================================================
    # Workflow context
    # =========================================================================
    stage_name = Column(
        String(100), 
        nullable=False, 
        index=True,
        comment="Workflow stage (e.g., 'planning', 'execution', 'reflection')"
    )
    
    step_number = Column(
        Integer, 
        nullable=True,
        comment="Step number within the stage"
    )
    
    node_name = Column(
        String(100), 
        nullable=True,
        comment="LangGraph node name (e.g., 'llm_processing_node')"
    )
    
    # =========================================================================
    # Model information
    # =========================================================================
    model_provider = Column(
        String(50), 
        nullable=False, 
        index=True,
        comment="Provider: openai, anthropic, self-hosted, etc."
    )
    
    model_name = Column(
        String(100), 
        nullable=False, 
        index=True,
        comment="Model name: gpt-4, claude-3-opus, llama-2-70b, etc."
    )
    
    model_version = Column(
        String(50), 
        nullable=True,
        comment="Model version if applicable"
    )
    
    # =========================================================================
    # Token usage
    # =========================================================================
    input_tokens = Column(
        Integer, 
        nullable=False, 
        default=0,
        comment="Input/prompt tokens"
    )
    
    output_tokens = Column(
        Integer, 
        nullable=False, 
        default=0,
        comment="Output/completion tokens"
    )
    
    cache_read_tokens = Column(
        Integer, 
        nullable=False, 
        default=0,
        comment="Tokens read from cache (Anthropic feature)"
    )
    
    cache_write_tokens = Column(
        Integer, 
        nullable=False, 
        default=0,
        comment="Tokens written to cache (Anthropic feature)"
    )
    
    total_tokens = Column(
        Integer, 
        nullable=False, 
        default=0,
        comment="Sum of all token types"
    )
    
    # =========================================================================
    # Cost calculation
    # =========================================================================
    unit_cost_input = Column(
        Numeric(12, 8), 
        nullable=False,
        comment="Cost per 1K input tokens in USD"
    )
    
    unit_cost_output = Column(
        Numeric(12, 8), 
        nullable=False,
        comment="Cost per 1K output tokens in USD"
    )
    
    computed_cost_usd = Column(
        Numeric(16, 8), 
        nullable=False,
        comment="Total computed cost in USD"
    )
    
    # =========================================================================
    # Performance metrics
    # =========================================================================
    latency_ms = Column(
        Integer, 
        nullable=True,
        comment="Total latency in milliseconds"
    )
    
    ttft_ms = Column(
        Integer, 
        nullable=True,
        comment="Time to first token in milliseconds"
    )
    
    # =========================================================================
    # Retry tracking
    # =========================================================================
    retry_count = Column(
        Integer, 
        default=0,
        comment="Number of retries before success"
    )
    
    retry_reason = Column(
        String(255), 
        nullable=True,
        comment="Reason for retry (rate limit, timeout, etc.)"
    )
    
    # =========================================================================
    # Tool calls (for agentic workflows)
    # =========================================================================
    tool_calls_count = Column(
        Integer, 
        default=0,
        comment="Number of tool calls in this LLM invocation"
    )
    
    tool_calls_data = Column(
        JSON, 
        nullable=True,
        comment="Details of tool calls made"
    )
    
    # =========================================================================
    # Prompt tracking
    # =========================================================================
    prompt_hash = Column(
        String(64), 
        nullable=True, 
        index=True,
        comment="Hash of prompt for deduplication analysis"
    )
    
    prompt_template_id = Column(
        String(100), 
        nullable=True,
        comment="Template ID if using prompt templates"
    )
    
    # =========================================================================
    # Metadata
    # =========================================================================
    finish_reason = Column(
        String(50), 
        nullable=True,
        comment="Why generation stopped (stop, length, tool_calls, etc.)"
    )
    
    model_metadata = Column(
        JSON, 
        nullable=True,
        comment="Additional provider-specific metadata"
    )
    
    # created_at and updated_at from TimestampMixin
    
    # =========================================================================
    # Indexes for performance
    # =========================================================================
    __table_args__ = (
        Index('idx_usage_execution_agent', 'execution_id', 'agent_id'),
        Index('idx_usage_model_created', 'model_provider', 'model_name', 'created_at'),
        Index('idx_usage_cost', 'computed_cost_usd'),
    )
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'execution_id': self.execution_id,
            'agent_id': self.agent_id,
            'stage_name': self.stage_name,
            'model_provider': self.model_provider,
            'model_name': self.model_name,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'total_tokens': self.total_tokens,
            'computed_cost_usd': float(self.computed_cost_usd),
            'latency_ms': self.latency_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# =============================================================================
# MODEL 2: ComputationalAuditCostSummary
# =============================================================================

class ComputationalAuditCostSummary(Base, TimestampMixin):
    """
    Aggregated cost summary per execution
    
    Lives in: tenant schemas (tenant_*)
    Purpose: One record per execution with rolled-up costs from all LLM calls
    Links to: execution_id (unique)
    
    Auto-updated: By CostTracker service when usage records are created
    
    Example Usage:
        summary = ComputationalAuditCostSummary(
            execution_id="exec_abc123",
            agent_id=1,
            total_llm_cost_usd=Decimal("1.25"),
            total_tokens=25000,
            total_llm_calls=10,
            total_cost_usd=Decimal("1.25")
        )
    """
    __tablename__ = "computational_audit_cost_summary"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # =========================================================================
    # Unique execution identifier
    # =========================================================================
    execution_id = Column(
        String(255), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="Unique execution ID (one summary per execution)"
    )
    
    agent_id = Column(
        Integer, 
        nullable=False, 
        index=True,
        comment="Agent ID for this execution"
    )
    
    # =========================================================================
    # Aggregated LLM costs
    # =========================================================================
    total_llm_cost_usd = Column(
        Numeric(16, 8), 
        nullable=False, 
        default=0,
        comment="Sum of all LLM call costs"
    )
    
    total_tokens = Column(
        Integer, 
        nullable=False, 
        default=0,
        comment="Sum of all tokens used"
    )
    
    total_llm_calls = Column(
        Integer, 
        nullable=False, 
        default=0,
        comment="Count of LLM invocations"
    )
    
    # =========================================================================
    # HITL costs (if applicable)
    # =========================================================================
    hitl_cost_usd = Column(
        Numeric(16, 8), 
        nullable=False, 
        default=0,
        comment="Human-in-the-loop review costs"
    )
    
    hitl_duration_seconds = Column(
        Integer, 
        nullable=False, 
        default=0,
        comment="Total HITL review duration"
    )
    
    # =========================================================================
    # Infrastructure costs (for self-hosted models)
    # =========================================================================
    infrastructure_cost_usd = Column(
        Numeric(16, 8), 
        nullable=False, 
        default=0,
        comment="GPU/hardware costs for self-hosted models"
    )
    
    # =========================================================================
    # Total cost (sum of all cost types)
    # =========================================================================
    total_cost_usd = Column(
        Numeric(16, 8), 
        nullable=False, 
        default=0,
        comment="Total: LLM + HITL + Infrastructure"
    )
    
    # =========================================================================
    # Execution timing
    # =========================================================================
    execution_started_at = Column(
        DateTime, 
        nullable=True,
        comment="When execution started"
    )
    
    execution_completed_at = Column(
        DateTime, 
        nullable=True,
        comment="When execution completed"
    )
    
    # created_at and updated_at from TimestampMixin
    
    # =========================================================================
    # Indexes
    # =========================================================================
    __table_args__ = (
        Index('idx_summary_agent_created', 'agent_id', 'created_at'),
        Index('idx_summary_cost', 'total_cost_usd'),
        Index('idx_summary_dates', 'execution_started_at', 'execution_completed_at'),
    )
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'execution_id': self.execution_id,
            'agent_id': self.agent_id,
            'total_llm_cost_usd': float(self.total_llm_cost_usd),
            'total_tokens': self.total_tokens,
            'total_llm_calls': self.total_llm_calls,
            'hitl_cost_usd': float(self.hitl_cost_usd),
            'infrastructure_cost_usd': float(self.infrastructure_cost_usd),
            'total_cost_usd': float(self.total_cost_usd),
            'execution_started_at': self.execution_started_at.isoformat() if self.execution_started_at else None,
            'execution_completed_at': self.execution_completed_at.isoformat() if self.execution_completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# =============================================================================
# MODEL 3: ModelPricing (PUBLIC SCHEMA)
# =============================================================================

# class ModelPricing(Base, TimestampMixin):
#     """
#     Model pricing configuration
    
#     Lives in: PUBLIC schema (shared across all tenants)
#     Purpose: Centralized pricing data for all LLM models
#     Version control: Uses effective_from/effective_until for price history
    
#     Example Usage:
#         pricing = ModelPricing(
#             model_provider="openai",
#             model_name="gpt-4",
#             input_cost_per_1k=Decimal("0.03"),
#             output_cost_per_1k=Decimal("0.06"),
#             effective_from=datetime.utcnow(),
#             active=True
#         )
#     """
#     __tablename__ = "model_pricing"
#     __table_args__ = {"schema": "public"}  # IMPORTANT: Public schema
    
#     id = Column(Integer, primary_key=True, index=True)
    
#     # =========================================================================
#     # Model identification
#     # =========================================================================
#     model_provider = Column(
#         String(50), 
#         nullable=False, 
#         index=True,
#         comment="Provider: openai, anthropic, self-hosted, etc."
#     )
    
#     model_name = Column(
#         String(100), 
#         nullable=False, 
#         index=True,
#         comment="Model name: gpt-4, claude-3-opus, etc."
#     )
    
#     model_version = Column(
#         String(50), 
#         nullable=True,
#         comment="Specific version if applicable"
#     )
    
#     # =========================================================================
#     # Pricing per 1K tokens (USD)
#     # =========================================================================
#     input_cost_per_1k = Column(
#         Numeric(12, 8), 
#         nullable=False,
#         comment="Cost per 1,000 input tokens in USD"
#     )
    
#     output_cost_per_1k = Column(
#         Numeric(12, 8), 
#         nullable=False,
#         comment="Cost per 1,000 output tokens in USD"
#     )
    
#     cache_read_per_1k = Column(
#         Numeric(12, 8), 
#         nullable=False, 
#         default=0,
#         comment="Cost per 1,000 cache read tokens (Anthropic)"
#     )
    
#     cache_write_per_1k = Column(
#         Numeric(12, 8), 
#         nullable=False, 
#         default=0,
#         comment="Cost per 1,000 cache write tokens (Anthropic)"
#     )
    
#     # =========================================================================
#     # Validity period (for price history)
#     # =========================================================================
#     effective_from = Column(
#         DateTime, 
#         nullable=False, 
#         default=datetime.utcnow,
#         index=True,
#         comment="When this pricing becomes effective"
#     )
    
#     effective_until = Column(
#         DateTime, 
#         nullable=True,
#         comment="When this pricing expires (NULL = current)"
#     )
    
#     # =========================================================================
#     # Metadata
#     # =========================================================================
#     currency = Column(
#         String(3), 
#         nullable=False, 
#         default='USD',
#         comment="Currency code (USD, EUR, etc.)"
#     )
    
#     active = Column(
#         Boolean, 
#         nullable=False, 
#         default=True,
#         index=True,
#         comment="Whether this pricing is active"
#     )
    
#     notes = Column(
#         String(500), 
#         nullable=True,
#         comment="Additional notes about this pricing"
#     )
    
#     source_url = Column(
#         String(500), 
#         nullable=True,
#         comment="Link to official pricing page"
#     )
    
#     # created_at and updated_at from TimestampMixin
    
#     # =========================================================================
#     # Indexes
#     # =========================================================================
#     __table_args__ = (
#         {"schema": "public"},
#         Index('idx_pricing_provider_name', 'model_provider', 'model_name'),
#         Index('idx_pricing_effective', 'effective_from', 'effective_until'),
#         Index('idx_pricing_active', 'active'),
#     )
    
#     def to_dict(self):
#         """Convert to dictionary"""
#         return {
#             'id': self.id,
#             'model_provider': self.model_provider,
#             'model_name': self.model_name,
#             'model_version': self.model_version,
#             'input_cost_per_1k': float(self.input_cost_per_1k),
#             'output_cost_per_1k': float(self.output_cost_per_1k),
#             'cache_read_per_1k': float(self.cache_read_per_1k),
#             'cache_write_per_1k': float(self.cache_write_per_1k),
#             'effective_from': self.effective_from.isoformat() if self.effective_from else None,
#             'effective_until': self.effective_until.isoformat() if self.effective_until else None,
#             'currency': self.currency,
#             'active': self.active
#         }

class ModelPricing(Base):
    """
    Model pricing table - stores LLM pricing information
    Located in PUBLIC schema (shared across all tenants)
    """
    __tablename__ = "model_pricing"
    __table_args__ = {'schema': 'public'}
    
    id = Column(Integer, primary_key=True, index=True)
    model_provider = Column(String(50), nullable=False, index=True)
    model_name = Column(String(100), nullable=False, index=True)
    model_version = Column(String(50), nullable=True)
    
    # Pricing per 1k tokens
    input_cost_per_1k = Column(Numeric(12, 8), nullable=False)
    output_cost_per_1k = Column(Numeric(12, 8), nullable=False)
    cache_read_per_1k = Column(Numeric(12, 8), default=0)
    cache_write_per_1k = Column(Numeric(12, 8), default=0)
    
    # Effective dates
    effective_from = Column(DateTime, nullable=False, default=func.now())
    effective_until = Column(DateTime, nullable=True)
    
    # Metadata
    currency = Column(String(3), default='USD', nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    notes = Column(String(500), nullable=True)
    source_url = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<ModelPricing({self.model_provider}:{self.model_name})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'model_provider': self.model_provider,
            'model_name': self.model_name,
            'model_version': self.model_version,
            'input_cost_per_1k': float(self.input_cost_per_1k),
            'output_cost_per_1k': float(self.output_cost_per_1k),
            'cache_read_per_1k': float(self.cache_read_per_1k) if self.cache_read_per_1k else 0,
            'cache_write_per_1k': float(self.cache_write_per_1k) if self.cache_write_per_1k else 0,
            'effective_from': self.effective_from.isoformat() if self.effective_from else None,
            'effective_until': self.effective_until.isoformat() if self.effective_until else None,
            'currency': self.currency,
            'active': self.active,
            'notes': self.notes,
            'source_url': self.source_url,
        }

# =============================================================================
# MODEL 4: TenantPricingConfig
# =============================================================================

class TenantPricingConfig(Base, TimestampMixin):
    """
    Tenant-specific pricing configuration
    
    Lives in: tenant schemas (tenant_*)
    Purpose: Per-tenant quotas, rates, and billing settings
    
    Example Usage:
        config = TenantPricingConfig(
            pricing_tier="professional",
            monthly_token_quota=10000000,
            monthly_budget_usd=Decimal("1000.00"),
            hitl_hourly_rate_usd=Decimal("50.00"),
            cost_alert_threshold_usd=Decimal("800.00"),
            active=True
        )
    """
    __tablename__ = "tenant_pricing_config"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # =========================================================================
    # Pricing tier
    # =========================================================================
    pricing_tier = Column(
        String(50),
        nullable=False,
        default='professional',
        comment="Tier: starter, professional, enterprise, custom"
    )
    
    # =========================================================================
    # Monthly quotas (NULL = unlimited)
    # =========================================================================
    monthly_token_quota = Column(
        Integer, 
        nullable=True,
        comment="Monthly token quota (NULL = unlimited)"
    )
    
    monthly_execution_quota = Column(
        Integer, 
        nullable=True,
        comment="Monthly execution quota (NULL = unlimited)"
    )
    
    monthly_budget_usd = Column(
        Numeric(12, 2), 
        nullable=True,
        comment="Monthly budget in USD (NULL = unlimited)"
    )
    
    # =========================================================================
    # Overage rates
    # =========================================================================
    overage_rate_per_1k_tokens = Column(
        Numeric(12, 8), 
        nullable=True,
        comment="Cost per 1K tokens over quota"
    )
    
    overage_rate_multiplier = Column(
        Numeric(5, 2), 
        nullable=True, 
        default=1.5,
        comment="Multiplier for overage pricing (e.g., 1.5x)"
    )
    
    # =========================================================================
    # HITL pricing
    # =========================================================================
    hitl_hourly_rate_usd = Column(
        Numeric(10, 2), 
        nullable=False, 
        default=50.00,
        comment="Hourly rate for human review in USD"
    )
    
    hitl_included_percent = Column(
        Numeric(5, 2), 
        nullable=False, 
        default=0,
        comment="Percent of HITL included in tier (0-100)"
    )
    
    # =========================================================================
    # Alert thresholds
    # =========================================================================
    cost_alert_threshold_usd = Column(
        Numeric(12, 2), 
        nullable=True,
        comment="Alert when cost exceeds this amount"
    )
    
    token_alert_threshold = Column(
        Integer, 
        nullable=True,
        comment="Alert when tokens exceed this amount"
    )
    
    budget_alert_percentage = Column(
        Numeric(5, 2), 
        nullable=False, 
        default=80,
        comment="Alert at what % of budget (default 80%)"
    )
    
    # =========================================================================
    # Billing settings
    # =========================================================================
    billing_cycle_day = Column(
        Integer, 
        nullable=False, 
        default=1,
        comment="Day of month for billing cycle (1-31)"
    )
    
    billing_email = Column(
        String(255), 
        nullable=True,
        comment="Email for billing notifications"
    )
    
    # =========================================================================
    # Self-hosted model configuration
    # =========================================================================
    self_hosted_gpu_type = Column(
        String(50), 
        nullable=True,
        comment="GPU type for self-hosted models (A100, H100, etc.)"
    )
    
    self_hosted_gpu_count = Column(
        Integer, 
        nullable=True,
        comment="Number of GPUs"
    )
    
    self_hosted_cost_per_hour = Column(
        Numeric(10, 4), 
        nullable=True,
        comment="Cost per hour for self-hosted infrastructure"
    )
    
    # =========================================================================
    # Status and metadata
    # =========================================================================
    active = Column(
        Boolean, 
        nullable=False, 
        default=True,
        comment="Whether this config is active"
    )
    
    custom_config = Column(
        JSON, 
        nullable=True,
        comment="Additional custom configuration"
    )
    
    # created_at and updated_at from TimestampMixin
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'pricing_tier': self.pricing_tier,
            'monthly_token_quota': self.monthly_token_quota,
            'monthly_execution_quota': self.monthly_execution_quota,
            'monthly_budget_usd': float(self.monthly_budget_usd) if self.monthly_budget_usd else None,
            'overage_rate_per_1k_tokens': float(self.overage_rate_per_1k_tokens) if self.overage_rate_per_1k_tokens else None,
            'hitl_hourly_rate_usd': float(self.hitl_hourly_rate_usd),
            'hitl_included_percent': float(self.hitl_included_percent),
            'cost_alert_threshold_usd': float(self.cost_alert_threshold_usd) if self.cost_alert_threshold_usd else None,
            'self_hosted_gpu_type': self.self_hosted_gpu_type,
            'self_hosted_gpu_count': self.self_hosted_gpu_count,
            'active': self.active
        }


# =============================================================================
# OPTIONAL: Relationships to existing models
# =============================================================================

# You can add these relationships to your existing models if desired:
#
# In backend/app/models/agent.py:
# 
# class AgentExecutionLog:
#     # ... existing fields ...
#     
#     # Add relationships
#     usage_records = relationship(
#         "ComputationalAuditUsage",
#         back_populates="execution_log",
#         cascade="all, delete-orphan"
#     )
#     
#     cost_summary = relationship(
#         "ComputationalAuditCostSummary",
#         back_populates="execution_log",
#         uselist=False,
#         cascade="all, delete-orphan"
#     )
#
# class AgentConfig:
#     # ... existing fields ...
#     
#     # Add relationship
#     usage_records = relationship(
#         "ComputationalAuditUsage",
#         back_populates="agent",
#         cascade="all, delete-orphan"
#     )


# =============================================================================
# END OF FILE - All 4 models complete
# =============================================================================
