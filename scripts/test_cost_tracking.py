"""
Test Cost Tracking - TENANT AWARE (FIXED)

Ensures all DB operations run under the tenant schema
so computational audit tables resolve correctly.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

# -------------------------------------------------------------------
# Add backend to PYTHONPATH
# -------------------------------------------------------------------
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# -------------------------------------------------------------------
# Imports
# -------------------------------------------------------------------
from app.core.database import SessionLocal
from app.services.cost_tracker import AsyncCostTracker
from app.services.token_parser import TokenParser
from app.services.cost_analytics import (
    CostAnalyticsService,
    CostForecaster,
    AnomalyDetector,
)
from app.services.self_hosted_calculator import SelfHostedCostCalculator
from sqlalchemy import text
from app.core.database import SessionLocal
# -------------------------------------------------------------------
# TEST CONFIG
# -------------------------------------------------------------------
TEST_TENANT_SCHEMA = "tenant_demo"  # 👈 CHANGE IF NEEDED


# -------------------------------------------------------------------
# Helper: tenant-aware DB session
# -------------------------------------------------------------------
def get_tenant_session():
    db = SessionLocal()
    db.execute(text(f"SET search_path TO {TEST_TENANT_SCHEMA}, public"))
    return db

# ===================================================================
# TEST 1: AsyncCostTracker
# ===================================================================
async def test_cost_tracker():
    print("\n" + "=" * 60)
    print("TEST 1: AsyncCostTracker")
    print("=" * 60)

    db = get_tenant_session()
    tracker = AsyncCostTracker(db)

    try:
        print("\n1️⃣ Testing track_llm_usage()...")
        usage = await tracker.track_llm_usage(
            execution_id="test_exec_001",
            agent_id=1,
            stage_name="planning",
            model_provider="openai",
            model_name="gpt-4",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=2500,
        )

        assert usage is not None
        print(f"   ✅ Usage created: ID={usage.id}")
        print(f"   📊 Tokens: {usage.total_tokens}")
        print(f"   💰 Cost: ${usage.computed_cost_usd:.6f}")

        print("\n2️⃣ Testing get_execution_cost()...")
        summary = await tracker.get_execution_cost("test_exec_001")
        assert summary is not None
        print(f"   ✅ Execution cost: ${summary.total_cost_usd:.6f}")

        print("\n3️⃣ Testing finalize_execution_costs()...")
        await tracker.finalize_execution_costs(
            execution_id="test_exec_001",
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
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


# ===================================================================
# TEST 2: TokenParser
# ===================================================================
def test_token_parser():
    print("\n" + "=" * 60)
    print("TEST 2: TokenParser")
    print("=" * 60)

    parser = TokenParser()

    try:
        print("\n1️⃣ parse_openai_response()...")
        openai_response = {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            }
        }

        inp, out = parser.parse_openai_response(openai_response)
        assert inp == 100 and out == 50
        print("   ✅ OpenAI parsed correctly")

        print("\n2️⃣ parse_anthropic_response()...")
        anthropic_response = {
            "usage": {"input_tokens": 200, "output_tokens": 100}
        }

        inp, out = parser.parse_anthropic_response(anthropic_response)
        assert inp == 200 and out == 100
        print("   ✅ Anthropic parsed correctly")

        print("\n3️⃣ parse_generic()...")
        tokens = parser.parse_generic(openai_response, provider="openai")
        print(f"   ✅ Generic parser: {tokens}")

        print("\n4️⃣ detect_provider()...")
        provider = parser.detect_provider({"model": "gpt-4"})
        assert provider == "openai"
        print("   ✅ Provider detected")

        print("\n✅ TokenParser tests PASSED")
        return True

    except Exception as e:
        print(f"\n❌ TokenParser test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


# ===================================================================
# TEST 3: CostAnalyticsService
# ===================================================================
def test_cost_analytics():
    print("\n" + "=" * 60)
    print("TEST 3: CostAnalyticsService")
    print("=" * 60)

    db = get_tenant_session()
    service = CostAnalyticsService(db)

    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        print("\n1️⃣ get_cost_summary()...")
        summary = service.get_cost_summary(start_date, end_date)

        print(f"   💰 Total cost: ${summary['total_cost']:.2f}")
        print(f"   📊 Total tokens: {summary['total_tokens']}")
        print(f"   🔄 Executions: {summary['total_executions']}")

        print("\n2️⃣ CostForecaster...")
        forecaster = CostForecaster(db)
        forecast = forecaster.forecast_monthly_cost()
        print(f"   📈 Forecast: ${forecast['forecasted_month_end']:.2f}")

        print("\n3️⃣ AnomalyDetector...")
        detector = AnomalyDetector(db)
        anomalies = detector.detect_cost_anomalies(start_date, end_date)
        print(f"   🚨 Anomalies detected: {len(anomalies)}")

        print("\n✅ CostAnalyticsService tests PASSED")
        return True

    except Exception as e:
        print(f"\n❌ CostAnalyticsService test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


# ===================================================================
# TEST 4: SelfHostedCostCalculator
# ===================================================================
async def test_self_hosted():
    print("\n" + "=" * 60)
    print("TEST 4: SelfHostedCostCalculator")
    print("=" * 60)

    db = get_tenant_session()
    calculator = SelfHostedCostCalculator(db)

    try:
        result = await calculator.track_self_hosted_usage(
            execution_id="test_self_hosted_001",
            agent_id=1,
            model_name="llama-2-70b",
            input_tokens=1000,
            output_tokens=500,
            inference_time_ms=2500,
            hardware_config={
                "gpu_type": "A100",
                "gpu_count": 4,
                "memory_gb": 320,
            },
        )

        print(f"   💰 Infra cost: ${result['infrastructure_cost']:.4f}")
        print(f"   ☁️ Cloud cost: ${result['cloud_equivalent_cost']:.4f}")
        print(f"   💵 Savings: ${result['savings']:.4f}")

        print("\n✅ SelfHostedCostCalculator tests PASSED")
        return True

    except Exception as e:
        print(f"\n❌ SelfHostedCostCalculator test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        db.close()


# ===================================================================
# RUN ALL TESTS
# ===================================================================
async def run_all_tests():
    print("\n" + "=" * 60)
    print("🧪 COST TRACKING TEST SUITE (TENANT AWARE)")
    print("=" * 60)

    results = []
    results.append(("AsyncCostTracker", await test_cost_tracker()))
    results.append(("TokenParser", test_token_parser()))
    results.append(("CostAnalyticsService", test_cost_analytics()))
    results.append(("SelfHostedCostCalculator", await test_self_hosted()))

    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    for name, r in results:
        print(f"{'✅ PASS' if r else '❌ FAIL'}: {name}")

    print(f"\n{passed}/{len(results)} tests passed")

    if passed == len(results):
        print("\n🎉 ALL TESTS PASSED 🎉")
        return 0
    else:
        print("\n⚠️ SOME TESTS FAILED")
        return 1


# ===================================================================
# ENTRY POINT
# ===================================================================
if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
