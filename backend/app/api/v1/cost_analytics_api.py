"""
Cost Analytics API Endpoints - COMPLETE IMPLEMENTATION
REST API for cost analytics, forecasting, and reporting

File: backend/app/api/v1/cost_analytics_api.py
Version: 2.1 FIXED
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user, TokenData
from app.services.cost_analytics import (
    CostAnalyticsService,
    CostForecaster,
    AnomalyDetector
)


# =============================================================================
# Response Models
# =============================================================================

class CostSummaryResponse(BaseModel):
    """Cost summary response"""
    total_cost: float
    total_tokens: int
    total_executions: int
    avg_cost_per_execution: float
    avg_tokens_per_execution: float


class DailyCostResponse(BaseModel):
    """Daily cost response"""
    date: str
    cost: float
    tokens: int
    executions: int


class ModelBreakdownResponse(BaseModel):
    """Model breakdown response"""
    provider: str
    model: str
    calls: int
    tokens: int
    cost: float


class AgentCostResponse(BaseModel):
    """Agent cost response"""
    agent_id: int
    agent_name: str
    executions: int
    cost: float
    tokens: int
    avg_cost_per_execution: float


class ForecastResponse(BaseModel):
    """Forecast response"""
    cost_to_date: float
    daily_average: float
    forecasted_month_end: float
    days_elapsed: int
    days_remaining: int
    confidence: str


class AnomalyResponse(BaseModel):
    """Anomaly response"""
    date: str
    cost: float
    expected_cost: float
    deviation: float
    z_score: float
    severity: str
    title: str
    description: str
    day_over_day_change: Optional[float] = None


# =============================================================================
# Router
# =============================================================================

router = APIRouter(
    prefix="/cost-analytics",
    tags=["Cost Analytics"]
)


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/summary", response_model=CostSummaryResponse)
async def get_cost_summary(
    start_date: Optional[datetime] = Query(
        default=None,
        description="Start date (defaults to 30 days ago)"
    ),
    end_date: Optional[datetime] = Query(
        default=None,
        description="End date (defaults to now)"
    ),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get cost summary for period
    
    Returns total cost, tokens, executions, and averages.
    
    Example:
        GET /api/v1/cost-analytics/summary?start_date=2025-01-01&end_date=2025-01-31
    """
    try:
        # Default dates
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        service = CostAnalyticsService(db)
        summary = service.get_cost_summary(start_date, end_date)
        
        return CostSummaryResponse(**summary)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cost summary: {str(e)}")


@router.get("/daily-costs", response_model=List[DailyCostResponse])
async def get_daily_costs(
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date"),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get daily cost trends
    
    Returns cost, tokens, and executions per day.
    
    Example:
        GET /api/v1/cost-analytics/daily-costs?start_date=2025-01-01&end_date=2025-01-31
    """
    try:
        service = CostAnalyticsService(db)
        daily_costs = service.get_daily_costs(start_date, end_date)
        
        return [DailyCostResponse(**item) for item in daily_costs]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get daily costs: {str(e)}")


@router.get("/model-breakdown", response_model=List[ModelBreakdownResponse])
async def get_model_breakdown(
    start_date: Optional[datetime] = Query(
        default=None,
        description="Start date (defaults to 30 days ago)"
    ),
    end_date: Optional[datetime] = Query(
        default=None,
        description="End date (defaults to now)"
    ),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get cost breakdown by model
    
    Returns costs grouped by provider and model.
    
    Example:
        GET /api/v1/cost-analytics/model-breakdown?start_date=2025-01-01
    """
    try:
        # Default dates
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        service = CostAnalyticsService(db)
        breakdown = service.get_model_breakdown(start_date, end_date)
        
        return [ModelBreakdownResponse(**item) for item in breakdown]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model breakdown: {str(e)}")


@router.get("/agent-costs", response_model=List[AgentCostResponse])
async def get_agent_costs(
    start_date: Optional[datetime] = Query(
        default=None,
        description="Start date (defaults to 30 days ago)"
    ),
    end_date: Optional[datetime] = Query(
        default=None,
        description="End date (defaults to now)"
    ),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get costs by agent
    
    Returns cost and performance metrics per agent.
    
    Example:
        GET /api/v1/cost-analytics/agent-costs?start_date=2025-01-01
    """
    try:
        # Default dates
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=30)
        
        service = CostAnalyticsService(db)
        agent_costs = service.get_agent_costs(start_date, end_date)
        
        return [AgentCostResponse(**item) for item in agent_costs]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent costs: {str(e)}")


@router.get("/forecast", response_model=ForecastResponse)
async def get_forecast(
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get monthly cost forecast
    
    Projects end-of-month cost based on current spending.
    
    Example:
        GET /api/v1/cost-analytics/forecast
    """
    try:
        forecaster = CostForecaster(db)
        forecast = forecaster.forecast_monthly_cost()
        
        return ForecastResponse(**forecast)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate forecast: {str(e)}")


@router.get("/anomalies", response_model=List[AnomalyResponse])
async def get_anomalies(
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    sensitivity: float = Query(
        2.0,
        ge=1.0,
        le=5.0,
        description="Detection sensitivity (lower = more sensitive)"
    ),
    db: Session = Depends(get_db),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Detect cost anomalies
    
    Uses statistical analysis to identify unusual cost patterns.
    
    Args:
        days: Number of days to analyze (7-365)
        sensitivity: Z-score threshold (1.0-5.0)
            - 1.0 = ~68% confidence (very sensitive)
            - 2.0 = ~95% confidence (recommended)
            - 3.0 = ~99% confidence (less sensitive)
    
    Example:
        GET /api/v1/cost-analytics/anomalies?days=30&sensitivity=2.0
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        detector = AnomalyDetector(db)
        anomalies = detector.detect_cost_anomalies(start_date, end_date, sensitivity)
        
        return [AnomalyResponse(**item) for item in anomalies]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to detect anomalies: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns service status.
    
    Example:
        GET /api/v1/cost-analytics/health
    """
    return {
        "status": "healthy",
        "service": "cost-analytics",
        "version": "2.1"
    }


# END OF FILE - API endpoints complete (FIXED - removed invalid exception handler)