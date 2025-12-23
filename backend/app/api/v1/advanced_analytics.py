"""
Advanced Analytics Module
Provides comprehensive analytics for agents, workflows, and system performance
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
from fastapi import APIRouter, Depends, Query
from sqlalchemy import Column, Integer, String, Float, JSON, DateTime, func, and_, or_
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.security import get_current_user, TokenData
from app.models.base import Base
from sqlalchemy.dialects.postgresql import JSONB

# ============================================================================
# Enums
# ============================================================================

class MetricType(str, Enum):
    """Types of metrics tracked"""
    EXECUTION_TIME = "execution_time"
    SUCCESS_RATE = "success_rate"
    ERROR_RATE = "error_rate"
    HITL_RATE = "hitl_rate"
    COST = "cost"
    TOKEN_USAGE = "token_usage"
    LATENCY = "latency"


class TimeGranularity(str, Enum):
    """Time granularity for analytics"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


# ============================================================================
# Database Models
# ============================================================================

class AnalyticsEvent(Base):
    """Store analytics events"""
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_slug = Column(String(100), nullable=False, index=True)
    
    # Event identification
    event_type = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)  # agent, workflow, user
    entity_id = Column(Integer, nullable=False, index=True)
    

    execution_time_ms = Column(Integer, nullable=True)
    # Metrics
    success = Column(Integer, nullable=True)  # 1 for success, 0 for failure
    error_message = Column(String(500), nullable=True)
    hitl_triggered = Column(Integer, nullable=True)  # 1 if HITL was triggered
    
    # Cost tracking
    cost_usd = Column(Float, nullable=True)
    token_count = Column(Integer, nullable=True)
    
    # Additional metadata
    event_metadata = Column(
        "metadata", JSONB, nullable=False, server_default="{}"
    )
    
    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class AnalyticsAggregate(Base):
    """Pre-computed analytics aggregates for performance"""
    __tablename__ = "analytics_aggregates"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_slug = Column(String(100), nullable=False, index=True)
    
    # Aggregation keys
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(Integer, nullable=False, index=True)
    metric_type = Column(String(50), nullable=False, index=True)
    granularity = Column(String(20), nullable=False, index=True)
    
    # Time period
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)
    
    # Aggregated values
    count = Column(Integer, nullable=False, default=0)
    sum_value = Column(Float, nullable=False, default=0.0)
    avg_value = Column(Float, nullable=False, default=0.0)
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)
    
    # Additional stats
    percentile_50 = Column(Float, nullable=True)
    percentile_95 = Column(Float, nullable=True)
    percentile_99 = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# Pydantic Schemas
# ============================================================================

class AnalyticsEventCreate(BaseModel):
    """Create an analytics event"""
    event_type: str
    entity_type: str
    entity_id: int
    execution_time_ms: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    hitl_triggered: bool = False
    cost_usd: Optional[float] = None
    token_count: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TimeSeriesDataPoint(BaseModel):
    """A single data point in a time series"""
    timestamp: datetime
    value: float
    count: int


class AgentPerformanceMetrics(BaseModel):
    """Performance metrics for an agent"""
    agent_id: int
    agent_name: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    success_rate: float
    avg_execution_time_ms: float
    hitl_triggered_count: int
    hitl_rate: float
    total_cost_usd: float
    total_tokens: int


class WorkflowAnalytics(BaseModel):
    """Analytics for a specific workflow"""
    workflow_name: str
    execution_count: int
    avg_execution_time_ms: float
    success_rate: float
    most_common_errors: List[Dict[str, Any]]
    top_agents: List[Dict[str, Any]]


class SystemHealthMetrics(BaseModel):
    """Overall system health metrics"""
    total_executions_24h: int
    success_rate_24h: float
    avg_response_time_ms: float
    error_rate_24h: float
    hitl_rate_24h: float
    total_cost_24h: float
    active_agents: int
    peak_load_time: Optional[datetime]
    peak_load_value: Optional[int]


class CostBreakdown(BaseModel):
    """Cost breakdown by various dimensions"""
    total_cost: float
    by_agent: List[Dict[str, Any]]
    by_workflow: List[Dict[str, Any]]
    by_day: List[Dict[str, Any]]


class AnalyticsQueryParams(BaseModel):
    """Common query parameters for analytics"""
    start_date: datetime
    end_date: datetime
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    granularity: TimeGranularity = TimeGranularity.DAY


# ============================================================================
# Analytics Service
# ============================================================================

class AnalyticsService:
    """Service for analytics operations"""
    
    def __init__(self, db: Session, tenant_slug: str):
        self.db = db
        self.tenant_slug = tenant_slug
    
    def record_event(self, event: AnalyticsEventCreate) -> AnalyticsEvent:
        """Record an analytics event"""
        db_event = AnalyticsEvent(
            tenant_slug=self.tenant_slug,
            event_type=event.event_type,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            success=1 if event.success else 0,
            error_message=event.error_message,
            hitl_triggered=1 if event.hitl_triggered else 0,
            cost_usd=event.cost_usd,
            token_count=event.token_count,
            metadata=event.metadata,
            execution_time_ms=0,
        )
        
        self.db.add(db_event)
        self.db.commit()
        self.db.refresh(db_event)
        
        return db_event
    
    def get_agent_performance(
        self,
        agent_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> AgentPerformanceMetrics:
        """Get performance metrics for a specific agent"""
        from app.models.agent import AgentConfig
        
        agent = self.db.query(AgentConfig).filter(
            AgentConfig.id == agent_id
        ).first()
        
        if not agent:
            return None
        
        # Query analytics events
        events = self.db.query(AnalyticsEvent).filter(
            and_(
                AnalyticsEvent.tenant_slug == self.tenant_slug,
                AnalyticsEvent.entity_type == "agent",
                AnalyticsEvent.entity_id == agent_id,
                AnalyticsEvent.timestamp >= start_date,
                AnalyticsEvent.timestamp <= end_date
            )
        )
        
        total = events.count()
        successful = events.filter(AnalyticsEvent.success == 1).count()
        failed = total - successful
        
        avg_time = events.filter(
            AnalyticsEvent.execution_time_ms.isnot(None)
        ).with_entities(
            func.avg(AnalyticsEvent.execution_time_ms)
        ).scalar() or 0.0
        
        hitl_count = events.filter(AnalyticsEvent.hitl_triggered == 1).count()
        
        total_cost = events.filter(
            AnalyticsEvent.cost_usd.isnot(None)
        ).with_entities(
            func.sum(AnalyticsEvent.cost_usd)
        ).scalar() or 0.0
        
        total_tokens = events.filter(
            AnalyticsEvent.token_count.isnot(None)
        ).with_entities(
            func.sum(AnalyticsEvent.token_count)
        ).scalar() or 0
        
        return AgentPerformanceMetrics(
            agent_id=agent_id,
            agent_name=agent.name,
            total_executions=total,
            successful_executions=successful,
            failed_executions=failed,
            success_rate=successful / total if total > 0 else 0.0,
            avg_execution_time_ms=float(avg_time),
            hitl_triggered_count=hitl_count,
            hitl_rate=hitl_count / total if total > 0 else 0.0,
            total_cost_usd=float(total_cost),
            total_tokens=int(total_tokens)
        )
    
    def get_time_series(
        self,
        metric_type: MetricType,
        start_date: datetime,
        end_date: datetime,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        granularity: TimeGranularity = TimeGranularity.DAY
    ) -> List[TimeSeriesDataPoint]:
        """Get time series data for a metric"""
        
        # Determine time bucket based on granularity
        if granularity == TimeGranularity.HOUR:
            time_bucket = func.date_trunc('hour', AnalyticsEvent.timestamp)
        elif granularity == TimeGranularity.DAY:
            time_bucket = func.date_trunc('day', AnalyticsEvent.timestamp)
        elif granularity == TimeGranularity.WEEK:
            time_bucket = func.date_trunc('week', AnalyticsEvent.timestamp)
        else:  # MONTH
            time_bucket = func.date_trunc('month', AnalyticsEvent.timestamp)
        
        # Build query
        query = self.db.query(
            time_bucket.label('period'),
            func.count(AnalyticsEvent.id).label('count')
        ).filter(
            and_(
                AnalyticsEvent.tenant_slug == self.tenant_slug,
                AnalyticsEvent.timestamp >= start_date,
                AnalyticsEvent.timestamp <= end_date
            )
        )
        
        # Apply entity filters
        if entity_type:
            query = query.filter(AnalyticsEvent.entity_type == entity_type)
        if entity_id:
            query = query.filter(AnalyticsEvent.entity_id == entity_id)
        
        # Select metric-specific aggregation
        if metric_type == MetricType.EXECUTION_TIME:
            query = query.add_columns(
                func.avg(AnalyticsEvent.execution_time_ms).label('value')
            ).filter(AnalyticsEvent.execution_time_ms.isnot(None))
        
        elif metric_type == MetricType.SUCCESS_RATE:
            query = query.add_columns(
                (func.sum(AnalyticsEvent.success) * 100.0 / func.count(AnalyticsEvent.id)).label('value')
            )
        
        elif metric_type == MetricType.ERROR_RATE:
            query = query.add_columns(
                ((func.count(AnalyticsEvent.id) - func.sum(AnalyticsEvent.success)) * 100.0 / func.count(AnalyticsEvent.id)).label('value')
            )
        
        elif metric_type == MetricType.HITL_RATE:
            query = query.add_columns(
                (func.sum(AnalyticsEvent.hitl_triggered) * 100.0 / func.count(AnalyticsEvent.id)).label('value')
            )
        
        elif metric_type == MetricType.COST:
            query = query.add_columns(
                func.sum(AnalyticsEvent.cost_usd).label('value')
            ).filter(AnalyticsEvent.cost_usd.isnot(None))
        
        elif metric_type == MetricType.TOKEN_USAGE:
            query = query.add_columns(
                func.sum(AnalyticsEvent.token_count).label('value')
            ).filter(AnalyticsEvent.token_count.isnot(None))
        
        # Group by time bucket
        query = query.group_by('period').order_by('period')
        
        results = query.all()
        
        return [
            TimeSeriesDataPoint(
                timestamp=row.period,
                value=float(row.value or 0),
                count=row.count
            )
            for row in results
        ]
    
    def get_system_health(self) -> SystemHealthMetrics:
        """Get overall system health metrics"""
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        
        # 24h metrics
        events_24h = self.db.query(AnalyticsEvent).filter(
            and_(
                AnalyticsEvent.tenant_slug == self.tenant_slug,
                AnalyticsEvent.timestamp >= day_ago
            )
        )
        
        total_24h = events_24h.count()
        successful_24h = events_24h.filter(AnalyticsEvent.success == 1).count()
        
        avg_response = events_24h.filter(
            AnalyticsEvent.execution_time_ms.isnot(None)
        ).with_entities(
            func.avg(AnalyticsEvent.execution_time_ms)
        ).scalar() or 0.0
        
        hitl_24h = events_24h.filter(AnalyticsEvent.hitl_triggered == 1).count()
        
        cost_24h = events_24h.filter(
            AnalyticsEvent.cost_usd.isnot(None)
        ).with_entities(
            func.sum(AnalyticsEvent.cost_usd)
        ).scalar() or 0.0
        
        # Active agents
        from app.models.agent import AgentConfig
        active_agents = self.db.query(AgentConfig).filter(
            AgentConfig.active == True
        ).count()
        
        # Peak load
        peak = events_24h.with_entities(
            func.date_trunc('hour', AnalyticsEvent.timestamp).label('hour'),
            func.count(AnalyticsEvent.id).label('count')
        ).group_by('hour').order_by(func.count(AnalyticsEvent.id).desc()).first()
        
        return SystemHealthMetrics(
            total_executions_24h=total_24h,
            success_rate_24h=successful_24h / total_24h * 100 if total_24h > 0 else 0.0,
            avg_response_time_ms=float(avg_response),
            error_rate_24h=(total_24h - successful_24h) / total_24h * 100 if total_24h > 0 else 0.0,
            hitl_rate_24h=hitl_24h / total_24h * 100 if total_24h > 0 else 0.0,
            total_cost_24h=float(cost_24h),
            active_agents=active_agents,
            peak_load_time=peak.hour if peak else None,
            peak_load_value=peak.count if peak else None
        )
    
    def get_cost_breakdown(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> CostBreakdown:
        """Get cost breakdown by different dimensions"""
        
        # Total cost
        total = self.db.query(
            func.sum(AnalyticsEvent.cost_usd)
        ).filter(
            and_(
                AnalyticsEvent.tenant_slug == self.tenant_slug,
                AnalyticsEvent.timestamp >= start_date,
                AnalyticsEvent.timestamp <= end_date,
                AnalyticsEvent.cost_usd.isnot(None)
            )
        ).scalar() or 0.0
        
        # By agent
        by_agent = self.db.query(
            AnalyticsEvent.entity_id,
            func.sum(AnalyticsEvent.cost_usd).label('cost')
        ).filter(
            and_(
                AnalyticsEvent.tenant_slug == self.tenant_slug,
                AnalyticsEvent.entity_type == "agent",
                AnalyticsEvent.timestamp >= start_date,
                AnalyticsEvent.timestamp <= end_date,
                AnalyticsEvent.cost_usd.isnot(None)
            )
        ).group_by(AnalyticsEvent.entity_id).order_by(func.sum(AnalyticsEvent.cost_usd).desc()).limit(10).all()
        
        # By day
        by_day = self.db.query(
            func.date_trunc('day', AnalyticsEvent.timestamp).label('day'),
            func.sum(AnalyticsEvent.cost_usd).label('cost')
        ).filter(
            and_(
                AnalyticsEvent.tenant_slug == self.tenant_slug,
                AnalyticsEvent.timestamp >= start_date,
                AnalyticsEvent.timestamp <= end_date,
                AnalyticsEvent.cost_usd.isnot(None)
            )
        ).group_by('day').order_by('day').all()
        
        return CostBreakdown(
            total_cost=float(total),
            by_agent=[{"agent_id": a.entity_id, "cost": float(a.cost)} for a in by_agent],
            by_workflow=[],  # Implement if needed
            by_day=[{"date": d.day.isoformat(), "cost": float(d.cost)} for d in by_day]
        )


# ============================================================================
# API Router
# ============================================================================

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.post("/events")
async def record_analytics_event(
    event: AnalyticsEventCreate,
    tenant_slug: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Record an analytics event"""
    service = AnalyticsService(db, tenant_slug)
    db_event = service.record_event(event)
    
    return {"message": "Event recorded", "event_id": db_event.id}


@router.get("/agents/{agent_id}/performance", response_model=AgentPerformanceMetrics)
async def get_agent_performance(
    agent_id: int,
    tenant_slug: str,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get performance metrics for a specific agent"""
    service = AnalyticsService(db, tenant_slug)
    metrics = service.get_agent_performance(agent_id, start_date, end_date)
    
    if not metrics:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return metrics


@router.get("/time-series", response_model=List[TimeSeriesDataPoint])
async def get_time_series_data(
    metric_type: MetricType,
    tenant_slug: str,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    granularity: TimeGranularity = Query(TimeGranularity.DAY),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get time series data for a metric"""
    service = AnalyticsService(db, tenant_slug)
    data = service.get_time_series(
        metric_type,
        start_date,
        end_date,
        entity_type,
        entity_id,
        granularity
    )
    
    return data


@router.get("/system/health", response_model=SystemHealthMetrics)
async def get_system_health(
    tenant_slug: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get overall system health metrics"""
    service = AnalyticsService(db, tenant_slug)
    health = service.get_system_health()
    
    return health


@router.get("/cost/breakdown", response_model=CostBreakdown)
async def get_cost_breakdown(
    tenant_slug: str,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get cost breakdown by various dimensions"""
    service = AnalyticsService(db, tenant_slug)
    breakdown = service.get_cost_breakdown(start_date, end_date)
    
    return breakdown


@router.get("/dashboard")
async def get_dashboard_data(
    tenant_slug: str,
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """Get comprehensive dashboard data"""
    service = AnalyticsService(db, tenant_slug)
    
    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    
    return {
        "system_health": service.get_system_health(),
        "cost_7d": service.get_cost_breakdown(week_ago, now),
        "execution_trend": service.get_time_series(
            MetricType.SUCCESS_RATE,
            week_ago,
            now,
            granularity=TimeGranularity.DAY
        )
    }
