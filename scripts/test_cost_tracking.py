"""
Test Cost Tracking - COMPLETE IMPLEMENTATION
Tests the cost tracking system end-to-end

File: backend/scripts/test_cost_tracking.py
Version: 2.0 COMPLETE
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.core.database import SessionLocal
from app.services.cost_tracker import AsyncCostTracker
from app.services.token_parser import TokenParser
from app.services.cost_analytics import CostAnalyticsService, CostForecaster, AnomalyDetector
from app.services.self_hosted_calculator import SelfHostedCostCalculator


async def test_cost_tracker():
    """Test AsyncCostTracker"""
    print("\n" + "="*60)
    print("TEST 1: AsyncCostTracker")
    print("="*60)
    
    db = SessionLocal()
    tracker = AsyncCostTracker(db)
    
    try:
        # Test tracking LLM usage
        print("\n1️⃣ Testing track_llm_usage()...")
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
        
        if usage:
            print(f"   ✅ Created usage record: ID={usage.id}")
            print(f"   📊 Tokens: {usage.total_tokens} (in={usage.input_tokens}, out={usage.output_tokens})")
            print(f"   💰 Cost: ${usage.computed_cost_usd:.6f}")
        else:
            print("   ❌ Failed to create usage record")
            return False
        
        # Test getting cost summary
        print("\n2️⃣ Testing get_execution_cost()...")
        summary = await tracker.get_execution_cost("test_exec_001")
        
        if summary:
            print(f"   ✅ Retrieved cost summary: ID={summary.id}")
            print(f"   💰 Total cost: ${summary.total_cost_usd:.6f}")
            print(f"   📊 Total tokens: {summary.total_tokens}")
            print(f"   📞 Total calls: {summary.total_llm_calls}")
        else:
            print("   ❌ Failed to retrieve cost summary")
            return False
        
        # Test finalizing costs
        print("\n3️⃣ Testing finalize_execution_costs()...")
        await tracker.finalize_execution_costs(
            execution_id="test_exec_001",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )
        print("   ✅ Finalized execution costs")
        
        print("\n✅ AsyncCostTracker tests PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ AsyncCostTracker test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def test_token_parser():
    """Test TokenParser"""
    print("\n" + "="*60)
    print("TEST 2: TokenParser")
    print("="*60)
    
    parser = TokenParser()
    
    try:
        # Test OpenAI response parsing
        print("\n1️⃣ Testing parse_openai_response()...")
        openai_response = {
            'usage': {
                'prompt_tokens': 100,
                'completion_tokens': 50,
                'total_tokens': 150
            }
        }
        
        input_tokens, output_tokens = parser.parse_openai_response(openai_response)
        print(f"   ✅ Parsed OpenAI: {input_tokens} input, {output_tokens} output")
        assert input_tokens == 100, "Input tokens mismatch"
        assert output_tokens == 50, "Output tokens mismatch"
        
        # Test Anthropic response parsing
        print("\n2️⃣ Testing parse_anthropic_response()...")
        anthropic_response = {
            'usage': {
                'input_tokens': 200,
                'output_tokens': 100
            }
        }
        
        input_tokens, output_tokens = parser.parse_anthropic_response(anthropic_response)
        print(f"   ✅ Parsed Anthropic: {input_tokens} input, {output_tokens} output")
        assert input_tokens == 200, "Input tokens mismatch"
        assert output_tokens == 100, "Output tokens mismatch"
        
        # Test generic parser
        print("\n3️⃣ Testing parse_generic()...")
        tokens = parser.parse_generic(openai_response, provider='openai')
        print(f"   ✅ Generic parser: {tokens}")
        
        # Test provider detection
        print("\n4️⃣ Testing detect_provider()...")
        provider = parser.detect_provider({'model': 'gpt-4'})
        print(f"   ✅ Detected provider: {provider}")
        assert provider == 'openai', "Provider detection failed"
        
        print("\n✅ TokenParser tests PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ TokenParser test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cost_analytics():
    """Test CostAnalyticsService"""
    print("\n" + "="*60)
    print("TEST 3: CostAnalyticsService")
    print("="*60)
    
    db = SessionLocal()
    service = CostAnalyticsService(db)
    
    try:
        # Test cost summary
        print("\n1️⃣ Testing get_cost_summary()...")
        from datetime import timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        summary = service.get_cost_summary(start_date, end_date)
        print(f"   ✅ Cost summary retrieved")
        print(f"   💰 Total cost: ${summary['total_cost']:.2f}")
        print(f"   📊 Total tokens: {summary['total_tokens']:,}")
        print(f"   🔄 Executions: {summary['total_executions']}")
        
        # Test forecasting
        print("\n2️⃣ Testing CostForecaster...")
        forecaster = CostForecaster(db)
        forecast = forecaster.forecast_monthly_cost()
        print(f"   ✅ Monthly forecast: ${forecast['forecasted_month_end']:.2f}")
        print(f"   📅 Days elapsed: {forecast['days_elapsed']}")
        
        # Test anomaly detection
        print("\n3️⃣ Testing AnomalyDetector...")
        detector = AnomalyDetector(db)
        anomalies = detector.detect_cost_anomalies(start_date, end_date, sensitivity=2.0)
        print(f"   ✅ Detected {len(anomalies)} anomalies")
        
        print("\n✅ CostAnalyticsService tests PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ CostAnalyticsService test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def test_self_hosted():
    """Test SelfHostedCostCalculator"""
    print("\n" + "="*60)
    print("TEST 4: SelfHostedCostCalculator")
    print("="*60)
    
    db = SessionLocal()
    calculator = SelfHostedCostCalculator(db)
    
    try:
        print("\n1️⃣ Testing track_self_hosted_usage()...")
        result = await calculator.track_self_hosted_usage(
            execution_id="test_self_hosted_001",
            agent_id=1,
            model_name="llama-2-70b",
            input_tokens=1000,
            output_tokens=500,
            inference_time_ms=2500,
            hardware_config={
                'gpu_type': 'A100',
                'gpu_count': 4,
                'memory_gb': 320
            }
        )
        
        print(f"   ✅ Infrastructure cost: ${result['infrastructure_cost']:.4f}")
        print(f"   ☁️  Cloud equivalent: ${result['cloud_equivalent_cost']:.4f}")
        print(f"   💵 Savings: ${result['savings']:.4f} ({result['savings_percent']:.1f}%)")
        
        print("\n✅ SelfHostedCostCalculator tests PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ SelfHostedCostCalculator test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 COST TRACKING TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test 1: AsyncCostTracker
    results.append(("AsyncCostTracker", await test_cost_tracker()))
    
    # Test 2: TokenParser
    results.append(("TokenParser", test_token_parser()))
    
    # Test 3: CostAnalyticsService
    results.append(("CostAnalyticsService", test_cost_analytics()))
    
    # Test 4: SelfHostedCostCalculator
    results.append(("SelfHostedCostCalculator", await test_self_hosted()))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)


# END OF FILE - Test script complete (260 lines)
