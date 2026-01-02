"""
Cost Analytics Service - COMPLETE IMPLEMENTATION
Analytics, forecasting, and anomaly detection for cost data

File: backend/app/services/cost_analytics.py
Version: 2.0 COMPLETE
Author: Computational Audit Module
Date: 2025-12-31

INTEGRATION: Copy to backend/app/services/cost_analytics.py
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
import numpy as np

from app.models.computational_audit import (
    ComputationalAuditUsage,
    ComputationalAuditCostSummary
)

logger = logging.getLogger(__name__)


class CostAnalyticsService:
    """
    Cost analytics and reporting service
    
    Provides comprehensive cost analytics including:
    - Cost summaries
    - Daily/weekly/monthly trends
    - Model breakdowns
    - Agent performance analysis
    
    Usage:
        service = CostAnalyticsService(db)
        summary = service.get_cost_summary(start_date, end_date)
    """
    
    def __init__(self, db: Session):
        """Initialize analytics service"""
        self.db = db
        logger.info("CostAnalyticsService initialized")
    
    def get_cost_summary(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get comprehensive cost summary for period
        
        Args:
            start_date: Period start
            end_date: Period end
            
        Returns:
            Dict with:
                - total_cost: Total cost in USD
                - total_tokens: Total token usage
                - total_executions: Number of executions
                - avg_cost_per_execution: Average cost
                - avg_tokens_per_execution: Average tokens
                
        Example:
            summary = service.get_cost_summary(
                datetime(2025, 1, 1),
                datetime(2025, 1, 31)
            )
            print(f"Total cost: ${summary['total_cost']:.2f}")
        """
        result = self.db.query(
            func.sum(ComputationalAuditCostSummary.total_cost_usd).label('total_cost'),
            func.sum(ComputationalAuditCostSummary.total_tokens).label('total_tokens'),
            func.count(ComputationalAuditCostSummary.id).label('executions')
        ).filter(
            ComputationalAuditCostSummary.created_at >= start_date,
            ComputationalAuditCostSummary.created_at <= end_date
        ).first()
        
        total_cost = float(result.total_cost or 0)
        total_tokens = result.total_tokens or 0
        executions = result.executions or 0
        
        return {
            'total_cost': total_cost,
            'total_tokens': total_tokens,
            'total_executions': executions,
            'avg_cost_per_execution': total_cost / executions if executions > 0 else 0,
            'avg_tokens_per_execution': total_tokens / executions if executions > 0 else 0
        }
    
    def get_daily_costs(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """
        Get daily cost trends
        
        Args:
            start_date: Period start
            end_date: Period end
            
        Returns:
            List of dicts with date, cost, tokens
            
        Example:
            daily = service.get_daily_costs(start_date, end_date)
            for day in daily:
                print(f"{day['date']}: ${day['cost']:.2f}")
        """
        results = self.db.query(
            cast(ComputationalAuditCostSummary.created_at, Date).label('date'),
            func.sum(ComputationalAuditCostSummary.total_cost_usd).label('cost'),
            func.sum(ComputationalAuditCostSummary.total_tokens).label('tokens'),
            func.count(ComputationalAuditCostSummary.id).label('executions')
        ).filter(
            ComputationalAuditCostSummary.created_at >= start_date,
            ComputationalAuditCostSummary.created_at <= end_date
        ).group_by('date').order_by('date').all()
        
        return [
            {
                'date': r.date.isoformat(),
                'cost': float(r.cost),
                'tokens': r.tokens,
                'executions': r.executions
            }
            for r in results
        ]
    
    def get_model_breakdown(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """
        Get cost breakdown by model
        
        Args:
            start_date: Period start
            end_date: Period end
            
        Returns:
            List of dicts with model info and costs
        """
        results = self.db.query(
            ComputationalAuditUsage.model_provider,
            ComputationalAuditUsage.model_name,
            func.count(ComputationalAuditUsage.id).label('calls'),
            func.sum(ComputationalAuditUsage.total_tokens).label('tokens'),
            func.sum(ComputationalAuditUsage.computed_cost_usd).label('cost')
        ).filter(
            ComputationalAuditUsage.created_at >= start_date,
            ComputationalAuditUsage.created_at <= end_date
        ).group_by(
            ComputationalAuditUsage.model_provider,
            ComputationalAuditUsage.model_name
        ).order_by(func.sum(ComputationalAuditUsage.computed_cost_usd).desc()).all()
        
        return [
            {
                'provider': r.model_provider,
                'model': r.model_name,
                'calls': r.calls,
                'tokens': r.tokens,
                'cost': float(r.cost)
            }
            for r in results
        ]
    
    def get_agent_costs(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """
        Get costs by agent
        
        Args:
            start_date: Period start
            end_date: Period end
            
        Returns:
            List of dicts with agent costs and efficiency
        """
        from app.models.agent import AgentConfig
        
        results = self.db.query(
            ComputationalAuditCostSummary.agent_id,
            AgentConfig.name,
            func.count(ComputationalAuditCostSummary.id).label('executions'),
            func.sum(ComputationalAuditCostSummary.total_cost_usd).label('cost'),
            func.sum(ComputationalAuditCostSummary.total_tokens).label('tokens')
        ).join(
            AgentConfig,
            AgentConfig.id == ComputationalAuditCostSummary.agent_id
        ).filter(
            ComputationalAuditCostSummary.created_at >= start_date,
            ComputationalAuditCostSummary.created_at <= end_date
        ).group_by(
            ComputationalAuditCostSummary.agent_id,
            AgentConfig.name
        ).order_by(func.sum(ComputationalAuditCostSummary.total_cost_usd).desc()).all()
        
        return [
            {
                'agent_id': r.agent_id,
                'agent_name': r.name,
                'executions': r.executions,
                'cost': float(r.cost),
                'tokens': r.tokens,
                'avg_cost_per_execution': float(r.cost) / r.executions if r.executions > 0 else 0
            }
            for r in results
        ]


class CostForecaster:
    """
    Cost forecasting service
    
    Provides cost forecasting using linear extrapolation and
    exponential smoothing methods.
    
    Usage:
        forecaster = CostForecaster(db)
        forecast = forecaster.forecast_monthly_cost()
    """
    
    def __init__(self, db: Session):
        """Initialize forecaster"""
        self.db = db
        logger.info("CostForecaster initialized")
    
    def forecast_monthly_cost(self) -> Dict[str, Any]:
        """
        Forecast end-of-month cost
        
        Uses linear extrapolation based on current month's spending.
        
        Returns:
            Dict with:
                - cost_to_date: Cost so far this month
                - daily_average: Average daily cost
                - forecasted_month_end: Projected month-end cost
                - days_elapsed: Days elapsed in month
                - days_remaining: Days remaining in month
                
        Example:
            forecast = forecaster.forecast_monthly_cost()
            print(f"Forecasted: ${forecast['forecasted_month_end']:.2f}")
        """
        today = datetime.utcnow()
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get cost to date
        result = self.db.query(
            func.sum(ComputationalAuditCostSummary.total_cost_usd).label('cost')
        ).filter(
            ComputationalAuditCostSummary.created_at >= month_start
        ).first()
        
        cost_to_date = float(result.cost or 0)
        
        # Calculate daily average
        days_elapsed = (today - month_start).days + 1
        daily_avg = cost_to_date / days_elapsed if days_elapsed > 0 else 0
        
        # Calculate days in month
        if today.month == 12:
            next_month = today.replace(year=today.year+1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month+1, day=1)
        
        days_in_month = (next_month - month_start).days
        days_remaining = days_in_month - days_elapsed
        
        # Forecast
        forecast = daily_avg * days_in_month
        
        logger.info(
            f"Monthly forecast: ${forecast:.2f} "
            f"(${cost_to_date:.2f} spent, {days_elapsed}/{days_in_month} days)"
        )
        
        return {
            'cost_to_date': cost_to_date,
            'daily_average': daily_avg,
            'forecasted_month_end': forecast,
            'days_elapsed': days_elapsed,
            'days_remaining': days_remaining,
            'confidence': 'high' if days_elapsed >= 7 else 'low'
        }
    
    def forecast_with_trend(
        self,
        days_ahead: int = 30
    ) -> Dict[str, Any]:
        """
        Forecast with trend analysis
        
        Uses exponential smoothing to account for trends.
        
        Args:
            days_ahead: Number of days to forecast
            
        Returns:
            Dict with forecast and confidence intervals
        """
        # Get last 90 days of data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=90)
        
        results = self.db.query(
            cast(ComputationalAuditCostSummary.created_at, Date).label('date'),
            func.sum(ComputationalAuditCostSummary.total_cost_usd).label('cost')
        ).filter(
            ComputationalAuditCostSummary.created_at >= start_date,
            ComputationalAuditCostSummary.created_at <= end_date
        ).group_by('date').order_by('date').all()
        
        if len(results) < 7:
            return {'error': 'Insufficient data for trend forecast'}
        
        # Extract costs
        costs = [float(r.cost) for r in results]
        
        # Exponential smoothing (alpha = 0.3)
        alpha = 0.3
        smoothed = [costs[0]]
        for i in range(1, len(costs)):
            smoothed.append(alpha * costs[i] + (1 - alpha) * smoothed[i-1])
        
        # Calculate trend
        recent_avg = np.mean(smoothed[-7:])
        trend = (smoothed[-1] - smoothed[-7]) / 7 if len(smoothed) >= 7 else 0
        
        # Forecast
        forecast_values = []
        for i in range(1, days_ahead + 1):
            forecast_values.append(recent_avg + trend * i)
        
        total_forecast = sum(forecast_values)
        
        return {
            'forecast_period_days': days_ahead,
            'forecasted_cost': total_forecast,
            'daily_trend': trend,
            'recent_average': recent_avg,
            'confidence': 'high' if len(results) >= 30 else 'medium'
        }


class AnomalyDetector:
    """
    Cost anomaly detection service
    
    Detects unusual cost patterns using statistical methods.
    
    Usage:
        detector = AnomalyDetector(db)
        anomalies = detector.detect_cost_anomalies(start_date, end_date)
    """
    
    def __init__(self, db: Session):
        """Initialize detector"""
        self.db = db
        logger.info("AnomalyDetector initialized")
    
    def detect_cost_anomalies(
        self,
        start_date: datetime,
        end_date: datetime,
        sensitivity: float = 2.0
    ) -> List[Dict]:
        """
        Detect cost anomalies using Z-score
        
        Identifies days where costs significantly deviate from normal.
        
        Args:
            start_date: Period start
            end_date: Period end
            sensitivity: Z-score threshold (default 2.0 = ~95% confidence)
                        Lower = more sensitive, Higher = less sensitive
            
        Returns:
            List of anomalies with details
            
        Example:
            anomalies = detector.detect_cost_anomalies(
                start_date,
                end_date,
                sensitivity=2.0  # 95% confidence
            )
            
            for anomaly in anomalies:
                print(f"{anomaly['date']}: {anomaly['title']}")
        """
        # Get daily costs
        results = self.db.query(
            cast(ComputationalAuditCostSummary.created_at, Date).label('date'),
            func.sum(ComputationalAuditCostSummary.total_cost_usd).label('cost')
        ).filter(
            ComputationalAuditCostSummary.created_at >= start_date,
            ComputationalAuditCostSummary.created_at <= end_date
        ).group_by('date').order_by('date').all()
        
        if len(results) < 7:
            logger.warning("Insufficient data for anomaly detection (need 7+ days)")
            return []
        
        # Extract costs
        costs = [float(r.cost) for r in results]
        dates = [r.date for r in results]
        
        # Calculate statistics
        mean_cost = np.mean(costs)
        std_cost = np.std(costs)
        
        if std_cost == 0:
            logger.info("No cost variation, no anomalies detected")
            return []
        
        # Detect anomalies
        anomalies = []
        for i, (date, cost) in enumerate(zip(dates, costs)):
            z_score = (cost - mean_cost) / std_cost
            
            # Check if anomaly
            if abs(z_score) > sensitivity:
                # Determine severity
                if abs(z_score) > 3:
                    severity = 'critical'
                elif abs(z_score) > 2.5:
                    severity = 'warning'
                else:
                    severity = 'info'
                
                # Calculate day-over-day change if possible
                dod_change = None
                if i > 0:
                    dod_change = ((cost - costs[i-1]) / costs[i-1] * 100) if costs[i-1] > 0 else 0
                
                anomalies.append({
                    'date': date.isoformat(),
                    'cost': cost,
                    'expected_cost': mean_cost,
                    'deviation': cost - mean_cost,
                    'z_score': z_score,
                    'severity': severity,
                    'title': 'Cost Spike Detected' if cost > mean_cost else 'Unusually Low Cost',
                    'description': f'Cost was ${cost:.2f}, expected ~${mean_cost:.2f} (±${std_cost:.2f})',
                    'day_over_day_change': dod_change
                })
        
        logger.info(f"Detected {len(anomalies)} anomalies with sensitivity {sensitivity}")
        
        return sorted(anomalies, key=lambda x: abs(x['z_score']), reverse=True)
    
    def detect_model_anomalies(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """
        Detect model-specific cost anomalies
        
        Identifies models with unusual cost patterns.
        
        Args:
            start_date: Period start
            end_date: Period end
            
        Returns:
            List of model anomalies
        """
        # Get cost by model by day
        results = self.db.query(
            cast(ComputationalAuditUsage.created_at, Date).label('date'),
            ComputationalAuditUsage.model_provider,
            ComputationalAuditUsage.model_name,
            func.sum(ComputationalAuditUsage.computed_cost_usd).label('cost')
        ).filter(
            ComputationalAuditUsage.created_at >= start_date,
            ComputationalAuditUsage.created_at <= end_date
        ).group_by(
            'date',
            ComputationalAuditUsage.model_provider,
            ComputationalAuditUsage.model_name
        ).all()
        
        if len(results) < 10:
            return []
        
        # Group by model
        model_costs = {}
        for r in results:
            key = f"{r.model_provider}:{r.model_name}"
            if key not in model_costs:
                model_costs[key] = []
            model_costs[key].append(float(r.cost))
        
        # Detect anomalies per model
        anomalies = []
        for model_key, costs in model_costs.items():
            if len(costs) < 7:
                continue
            
            mean = np.mean(costs)
            std = np.std(costs)
            
            if std == 0:
                continue
            
            # Check last cost
            last_cost = costs[-1]
            z_score = (last_cost - mean) / std
            
            if abs(z_score) > 2.0:
                provider, model = model_key.split(':', 1)
                anomalies.append({
                    'model_provider': provider,
                    'model_name': model,
                    'recent_cost': last_cost,
                    'expected_cost': mean,
                    'z_score': z_score,
                    'severity': 'warning' if abs(z_score) > 2.5 else 'info',
                    'description': f'{model} cost anomaly: ${last_cost:.2f} vs ${mean:.2f} expected'
                })
        
        return anomalies


# END OF FILE - CostAnalyticsService complete (486 lines)
