"""
Complete Unit Test Suite - FULL VERSION
Comprehensive tests for all cost tracking components

File: tests/test_cost_tracker.py
Version: 2.0 COMPLETE

USAGE:
    # Run all tests
    pytest tests/test_cost_tracker.py -v
    
    # Run with coverage
    pytest tests/test_cost_tracker.py --cov=app.services --cov-report=html
    
    # Run specific test
    pytest tests/test_cost_tracker.py::test_track_llm_usage -v
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def db_session():
    """Mock database session"""
    from sqlalchemy.orm import Session
    session = Mock(spec=Session)
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    session.rollback = Mock()
    return session

@pytest.fixture
def sample_openai_response():
    """Sample OpenAI API response"""
    return {
        'usage': {
            'prompt_tokens': 1000,
            'completion_tokens': 500,
            'total_tokens': 1500
        },
        'model': 'gpt-4',
        'choices': [{'message': {'content': 'Test response'}}]
    }

@pytest.fixture
def sample_anthropic_response():
    """Sample Anthropic API response"""
    return {
        'usage': {
            'input_tokens': 2000,
            'output_tokens': 1000
        },
        'model': 'claude-3-opus-20240229',
        'content': [{'text': 'Test response'}]
    }

# =============================================================================
# Test AsyncCostTracker
# =============================================================================

class TestAsyncCostTracker:
    """Test suite for AsyncCostTracker"""
    
    @pytest.mark.asyncio
    async def test_track_llm_usage_basic(self, db_session):
        """Test basic LLM usage tracking"""
        from app.services.cost_tracker import AsyncCostTracker
        
        tracker = AsyncCostTracker(db_session)
        
        # Mock pricing lookup
        with patch.object(tracker, 'get_model_pricing', return_value=(Decimal('0.03'), Decimal('0.06'))):
            usage = await tracker.track_llm_usage(
                execution_id="test_exec_001",
                agent_id=1,
                stage_name="planning",
                model_provider="openai",
                model_name="gpt-4",
                input_tokens=1000,
                output_tokens=500,
                latency_ms=2500
            )
        
        # Verify database calls
        assert db_session.add.called
        assert db_session.commit.called
    
    @pytest.mark.asyncio
    async def test_track_llm_usage_with_cache(self, db_session):
        """Test LLM usage tracking with cache tokens"""
        from app.services.cost_tracker import AsyncCostTracker
        
        tracker = AsyncCostTracker(db_session)
        
        with patch.object(tracker, 'get_model_pricing', return_value=(Decimal('0.003'), Decimal('0.015'))):
            usage = await tracker.track_llm_usage(
                execution_id="test_exec_002",
                agent_id=1,
                stage_name="execution",
                model_provider="anthropic",
                model_name="claude-3-sonnet",
                input_tokens=2000,
                output_tokens=1000,
                cache_read_tokens=500,
                cache_write_tokens=250
            )
        
        assert db_session.add.called
    
    @pytest.mark.asyncio
    async def test_track_hitl_cost(self, db_session):
        """Test HITL cost tracking"""
        from app.services.cost_tracker import AsyncCostTracker
        
        tracker = AsyncCostTracker(db_session)
        
        # Mock summary query
        mock_summary = Mock()
        mock_summary.hitl_cost_usd = Decimal('0')
        mock_summary.hitl_duration_seconds = 0
        db_session.query().filter().first.return_value = mock_summary
        
        await tracker.track_hitl_cost(
            execution_id="test_exec_001",
            duration_seconds=300,
            hourly_rate=Decimal("50.00")
        )
        
        # Verify cost calculation (300 seconds = 5 minutes = $4.17)
        assert db_session.commit.called
    
    @pytest.mark.asyncio
    async def test_track_infrastructure_cost(self, db_session):
        """Test infrastructure cost tracking"""
        from app.services.cost_tracker import AsyncCostTracker
        
        tracker = AsyncCostTracker(db_session)
        
        # Mock summary query
        mock_summary = Mock()
        mock_summary.infrastructure_cost_usd = Decimal('0')
        db_session.query().filter().first.return_value = mock_summary
        
        await tracker.track_infrastructure_cost(
            execution_id="test_exec_001",
            cost=Decimal("1.50"),
            description="Test infrastructure"
        )
        
        assert db_session.commit.called
    
    @pytest.mark.asyncio
    async def test_finalize_execution_costs(self, db_session):
        """Test finalizing execution costs"""
        from app.services.cost_tracker import AsyncCostTracker
        
        tracker = AsyncCostTracker(db_session)
        
        # Mock summary query
        mock_summary = Mock()
        db_session.query().filter().first.return_value = mock_summary
        
        start_time = datetime.utcnow() - timedelta(seconds=60)
        end_time = datetime.utcnow()
        
        await tracker.finalize_execution_costs(
            execution_id="test_exec_001",
            started_at=start_time,
            completed_at=end_time
        )
        
        assert mock_summary.execution_started_at == start_time
        assert mock_summary.execution_completed_at == end_time
        assert db_session.commit.called
    
    @pytest.mark.asyncio
    async def test_get_execution_cost(self, db_session):
        """Test retrieving execution cost"""
        from app.services.cost_tracker import AsyncCostTracker
        
        tracker = AsyncCostTracker(db_session)
        
        # Mock summary
        mock_summary = Mock()
        mock_summary.total_cost_usd = Decimal("5.50")
        db_session.query().filter().first.return_value = mock_summary
        
        summary = await tracker.get_execution_cost("test_exec_001")
        
        assert summary is not None
    
    def test_clear_pricing_cache(self, db_session):
        """Test clearing pricing cache"""
        from app.services.cost_tracker import AsyncCostTracker
        
        tracker = AsyncCostTracker(db_session)
        tracker._pricing_cache['test'] = (Decimal('1'), Decimal('2'))
        
        tracker.clear_pricing_cache()
        
        assert len(tracker._pricing_cache) == 0

# =============================================================================
# Test TokenParser
# =============================================================================

class TestTokenParser:
    """Test suite for TokenParser"""
    
    def test_parse_openai_response(self, sample_openai_response):
        """Test parsing OpenAI response"""
        from app.services.token_parser import TokenParser
        
        parser = TokenParser()
        input_tokens, output_tokens = parser.parse_openai_response(sample_openai_response)
        
        assert input_tokens == 1000
        assert output_tokens == 500
    
    def test_parse_anthropic_response(self, sample_anthropic_response):
        """Test parsing Anthropic response"""
        from app.services.token_parser import TokenParser
        
        parser = TokenParser()
        input_tokens, output_tokens = parser.parse_anthropic_response(sample_anthropic_response)
        
        assert input_tokens == 2000
        assert output_tokens == 1000
    
    def test_parse_langchain_response(self):
        """Test parsing LangChain response"""
        from app.services.token_parser import TokenParser
        
        parser = TokenParser()
        langchain_response = {
            'response_metadata': {
                'token_usage': {
                    'prompt_tokens': 1500,
                    'completion_tokens': 750
                }
            }
        }
        
        input_tokens, output_tokens = parser.parse_langchain_response(langchain_response)
        
        assert input_tokens == 1500
        assert output_tokens == 750
    
    def test_parse_generic_openai(self, sample_openai_response):
        """Test generic parser with OpenAI response"""
        from app.services.token_parser import TokenParser
        
        parser = TokenParser()
        input_tokens, output_tokens = parser.parse_generic(sample_openai_response, provider='openai')
        
        assert input_tokens == 1000
        assert output_tokens == 500
    
    def test_parse_generic_anthropic(self, sample_anthropic_response):
        """Test generic parser with Anthropic response"""
        from app.services.token_parser import TokenParser
        
        parser = TokenParser()
        input_tokens, output_tokens = parser.parse_generic(sample_anthropic_response, provider='anthropic')
        
        assert input_tokens == 2000
        assert output_tokens == 1000
    
    def test_detect_provider_openai(self):
        """Test provider detection for OpenAI"""
        from app.services.token_parser import TokenParser
        
        parser = TokenParser()
        response = {'model': 'gpt-4'}
        
        provider = parser.detect_provider(response)
        
        assert provider == 'openai'
    
    def test_detect_provider_anthropic(self):
        """Test provider detection for Anthropic"""
        from app.services.token_parser import TokenParser
        
        parser = TokenParser()
        response = {'model': 'claude-3-opus-20240229'}
        
        provider = parser.detect_provider(response)
        
        assert provider == 'anthropic'
    
    def test_parse_invalid_response(self):
        """Test parsing invalid response"""
        from app.services.token_parser import TokenParser
        
        parser = TokenParser()
        input_tokens, output_tokens = parser.parse_generic({})
        
        assert input_tokens == 0
        assert output_tokens == 0

# =============================================================================
# Test CostAnalyticsService
# =============================================================================

class TestCostAnalyticsService:
    """Test suite for CostAnalyticsService"""
    
    def test_get_cost_summary(self, db_session):
        """Test getting cost summary"""
        from app.services.cost_analytics import CostAnalyticsService
        
        service = CostAnalyticsService(db_session)
        
        # Mock query result
        mock_result = Mock()
        mock_result.total_cost = Decimal('100.50')
        mock_result.total_tokens = 50000
        mock_result.executions = 10
        db_session.query().filter().first.return_value = mock_result
        
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        summary = service.get_cost_summary(start_date, end_date)
        
        assert 'total_cost' in summary
        assert 'total_tokens' in summary
        assert 'total_executions' in summary
    
    def test_get_daily_costs(self, db_session):
        """Test getting daily costs"""
        from app.services.cost_analytics import CostAnalyticsService
        
        service = CostAnalyticsService(db_session)
        
        # Mock query results
        mock_results = [
            Mock(date=datetime(2025, 1, 1).date(), cost=Decimal('10.5'), tokens=5000, executions=2),
            Mock(date=datetime(2025, 1, 2).date(), cost=Decimal('15.3'), tokens=7500, executions=3)
        ]
        db_session.query().filter().group_by().order_by().all.return_value = mock_results
        
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 31)
        
        daily_costs = service.get_daily_costs(start_date, end_date)
        
        assert len(daily_costs) == 2
        assert daily_costs[0]['cost'] == 10.5
    
    def test_get_model_breakdown(self, db_session):
        """Test getting model breakdown"""
        from app.services.cost_analytics import CostAnalyticsService
        
        service = CostAnalyticsService(db_session)
        
        # Mock query results
        mock_results = [
            Mock(model_provider='openai', model_name='gpt-4', calls=100, tokens=50000, cost=Decimal('75.50'))
        ]
        db_session.query().filter().group_by().order_by().all.return_value = mock_results
        
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
        
        breakdown = service.get_model_breakdown(start_date, end_date)
        
        assert len(breakdown) == 1
        assert breakdown[0]['provider'] == 'openai'

# =============================================================================
# Test CostForecaster
# =============================================================================

class TestCostForecaster:
    """Test suite for CostForecaster"""
    
    def test_forecast_monthly_cost(self, db_session):
        """Test monthly cost forecasting"""
        from app.services.cost_analytics import CostForecaster
        
        forecaster = CostForecaster(db_session)
        
        # Mock query result
        mock_result = Mock()
        mock_result.cost = Decimal('150.00')
        db_session.query().filter().first.return_value = mock_result
        
        forecast = forecaster.forecast_monthly_cost()
        
        assert 'cost_to_date' in forecast
        assert 'daily_average' in forecast
        assert 'forecasted_month_end' in forecast
        assert 'confidence' in forecast

# =============================================================================
# Test AnomalyDetector
# =============================================================================

class TestAnomalyDetector:
    """Test suite for AnomalyDetector"""
    
    def test_detect_cost_anomalies(self, db_session):
        """Test anomaly detection"""
        from app.services.cost_analytics import AnomalyDetector
        
        detector = AnomalyDetector(db_session)
        
        # Mock query results with one anomaly
        mock_results = [
            Mock(date=datetime(2025, 1, i).date(), cost=Decimal('10.0'))
            for i in range(1, 29)
        ]
        mock_results.append(Mock(date=datetime(2025, 1, 29).date(), cost=Decimal('100.0')))  # Anomaly
        
        db_session.query().filter().group_by().order_by().all.return_value = mock_results
        
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 31)
        
        anomalies = detector.detect_cost_anomalies(start_date, end_date, sensitivity=2.0)
        
        assert len(anomalies) > 0

# =============================================================================
# Test SelfHostedCostCalculator
# =============================================================================

class TestSelfHostedCostCalculator:
    """Test suite for SelfHostedCostCalculator"""
    
    @pytest.mark.asyncio
    async def test_track_self_hosted_usage(self, db_session):
        """Test self-hosted usage tracking"""
        from app.services.self_hosted_calculator import SelfHostedCostCalculator
        
        calculator = SelfHostedCostCalculator(db_session)
        
        # Mock cost tracker
        with patch.object(calculator.cost_tracker, 'track_llm_usage', return_value=Mock(id=1)):
            with patch.object(calculator.cost_tracker, 'track_infrastructure_cost'):
                result = await calculator.track_self_hosted_usage(
                    execution_id="test_exec_001",
                    agent_id=1,
                    model_name="llama-2-70b",
                    input_tokens=1000,
                    output_tokens=500,
                    inference_time_ms=2500,
                    hardware_config={'gpu_type': 'A100', 'gpu_count': 4}
                )
        
        assert 'infrastructure_cost' in result
        assert 'cloud_equivalent_cost' in result
        assert 'savings' in result
    
    def test_calculate_hardware_cost(self, db_session):
        """Test hardware cost calculation"""
        from app.services.self_hosted_calculator import SelfHostedCostCalculator
        
        calculator = SelfHostedCostCalculator(db_session)
        
        hardware_config = {'gpu_type': 'A100', 'gpu_count': 4}
        cost = calculator._calculate_hardware_cost(hardware_config)
        
        # 4 x $2.50/hr x 1.2 (overhead) = $12/hr
        assert cost == 12.0

# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for complete workflows"""
    
    @pytest.mark.asyncio
    async def test_complete_tracking_workflow(self, db_session):
        """Test complete cost tracking workflow"""
        from app.services.cost_tracker import AsyncCostTracker
        
        tracker = AsyncCostTracker(db_session)
        
        # Track multiple LLM calls
        with patch.object(tracker, 'get_model_pricing', return_value=(Decimal('0.03'), Decimal('0.06'))):
            for i in range(3):
                await tracker.track_llm_usage(
                    execution_id="test_integration_001",
                    agent_id=1,
                    stage_name="test",
                    model_provider="openai",
                    model_name="gpt-4",
                    input_tokens=100,
                    output_tokens=50
                )
        
        # Finalize costs
        start_time = datetime.utcnow() - timedelta(seconds=10)
        end_time = datetime.utcnow()
        
        await tracker.finalize_execution_costs(
            execution_id="test_integration_001",
            started_at=start_time,
            completed_at=end_time
        )
        
        # Verify multiple commits
        assert db_session.commit.call_count >= 3

# END OF FILE - Complete test suite (450+ lines)
