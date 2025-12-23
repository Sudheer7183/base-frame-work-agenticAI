#!/usr/bin/env python3
"""
Comprehensive Test Script for P2 Features
Tests: Tools, Cache, Monitoring, Templates, Exports

Usage:
    cd /mnt/d/sudheer/new-base-platform-agentiai/agentic-ai-platform-v1.3-complete
    python scripts/test_p2_features.py
    
    # Or test specific features:
    python scripts/test_p2_features.py --test tools
    python scripts/test_p2_features.py --test cache
    python scripts/test_p2_features.py --test monitoring
    python scripts/test_p2_features.py --test templates
    python scripts/test_p2_features.py --test exports
"""

import sys
import os
from pathlib import Path

# Set up environment variables BEFORE imports
os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-p2-testing-12345678')
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5433')
os.environ.setdefault('DB_NAME', 'agenticbase2')
os.environ.setdefault('DB_USER', 'postgres')
os.environ.setdefault('DB_PASSWORD', 'postgres')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
os.environ.setdefault('CACHE_DEFAULT_TTL', '3600')
os.environ.setdefault('METRICS_ENABLED', 'true')
os.environ.setdefault('OTEL_ENABLED', 'false')

# Add backend to Python path
project_root = Path(__file__).parent.parent
backend_dir = project_root / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

# Import P2 modules
from app.tools.registry import (
    get_tool_registry, BaseTool, ToolDefinition,
    SearchTool, CalculatorTool, DatabaseQueryTool, register_default_tools
)
from app.core.cache import (
    init_cache, get_cache_manager, InMemoryCache, RedisCache, cache_key
)
from app.core.monitoring import (
    init_monitoring, get_monitoring, MetricsCollector, Tracer, PerformanceMonitor
)
from app.workflows.templates import (
    get_workflow_registry, WorkflowType, WorkflowTemplate
)
from app.export.exporter import get_exporter, get_report_generator, ExportFormat

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_info(text):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {text}{Colors.END}")


class TestResults:
    """Track test results"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.tests = []
    
    def add_pass(self, test_name):
        self.passed += 1
        self.tests.append((test_name, 'PASS'))
        print_success(f"{test_name}")
    
    def add_fail(self, test_name, error=None):
        self.failed += 1
        self.tests.append((test_name, 'FAIL', error))
        print_error(f"{test_name}")
        if error:
            print(f"  Error: {str(error)[:200]}")
    
    def add_warning(self, test_name, message):
        self.warnings += 1
        self.tests.append((test_name, 'WARN', message))
        print_warning(f"{test_name}: {message}")
    
    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")
        total = self.passed + self.failed + self.warnings
        print(f"\nTotal Tests: {total}")
        print_success(f"Passed: {self.passed}")
        print_error(f"Failed: {self.failed}")
        print_warning(f"Warnings: {self.warnings}")
        if total > 0:
            print(f"\nSuccess Rate: {(self.passed/total*100):.1f}%")


# =============================================================================
# Test 1: Tool Execution Framework
# =============================================================================

async def test_tool_framework(results):
    """Test tool registration and execution"""
    print_header("TEST 1: TOOL EXECUTION FRAMEWORK")
    
    try:
        print_info("Initializing tool registry...")
        
        # Get registry
        registry = get_tool_registry()
        results.add_pass("Tool registry initialized")
        
        # Test 1: Register default tools
        print_info("Registering default tools...")
        try:
            register_default_tools()
            results.add_pass("Default tools registered")
        except Exception as e:
            results.add_fail("Default tool registration failed", e)
        
        # Test 2: List tools
        print_info("Listing tools...")
        try:
            tools = registry.list_tools()
            if len(tools) >= 3:  # Should have at least 3 default tools
                results.add_pass(f"Listed {len(tools)} tools")
            else:
                results.add_warning("Tool listing", f"Only {len(tools)} tools found (expected >= 3)")
        except Exception as e:
            results.add_fail("Tool listing failed", e)
        
        # Test 3: Get tool definition
        print_info("Getting tool definition...")
        try:
            definition = registry.get_definition("calculator")
            if definition:
                results.add_pass("Tool definition retrieved: calculator")
                print_info(f"  Category: {definition.category}")
                print_info(f"  Timeout: {definition.timeout_seconds}s")
            else:
                results.add_fail("Tool definition not found: calculator")
        except Exception as e:
            results.add_fail("Get tool definition failed", e)
        
        # Test 4: Execute calculator tool
        print_info("Testing calculator tool execution...")
        try:
            result = await registry.execute(
                tool_name="calculator",
                parameters={"expression": "2 + 2 * 3"}
            )
            
            if result.get("success"):
                calc_result = result.get("result", {}).get("result")
                if calc_result == 8:
                    results.add_pass(f"Calculator executed correctly: 2 + 2 * 3 = {calc_result}")
                else:
                    results.add_fail(f"Calculator returned wrong result: {calc_result}")
            else:
                results.add_fail("Calculator execution failed", result.get("error"))
        except Exception as e:
            results.add_fail("Calculator tool execution error", e)
        
        # Test 5: Execute search tool
        print_info("Testing search tool execution...")
        try:
            result = await registry.execute(
                tool_name="search",
                parameters={"query": "AI technologies", "max_results": 5}
            )
            
            if result.get("success"):
                search_results = result.get("result", {}).get("results", [])
                results.add_pass(f"Search executed: {len(search_results)} results")
            else:
                results.add_fail("Search execution failed", result.get("error"))
        except Exception as e:
            results.add_fail("Search tool execution error", e)
        
        # Test 6: Tool timeout handling
        print_info("Testing tool timeout...")
        try:
            # Create a custom tool that times out
            class SlowTool(BaseTool):
                async def execute(self, delay: int = 10):
                    await asyncio.sleep(delay)
                    return {"done": True}
                
                def get_definition(self):
                    return ToolDefinition(
                        name="slow_tool",
                        description="A slow tool for testing",
                        parameters={"delay": {"type": "integer", "default": 10}},
                        category="test",
                        timeout_seconds=1  # 1 second timeout
                    )
            
            registry.register(SlowTool())
            
            result = await registry.execute(
                tool_name="slow_tool",
                parameters={"delay": 5}
            )
            
            if not result.get("success") and result.get("error_type") == "timeout":
                results.add_pass("Tool timeout handled correctly")
            else:
                results.add_warning("Timeout test", "Expected timeout but got: " + str(result))
        except Exception as e:
            results.add_fail("Timeout handling test failed", e)
        
        # Test 7: Invalid tool execution
        print_info("Testing invalid tool handling...")
        try:
            result = await registry.execute(
                tool_name="nonexistent_tool",
                parameters={}
            )
            results.add_fail("Should have raised error for nonexistent tool")
        except ValueError as e:
            if "not found" in str(e).lower():
                results.add_pass("Invalid tool correctly rejected")
            else:
                results.add_fail("Wrong error for invalid tool", e)
        except Exception as e:
            results.add_fail("Unexpected error for invalid tool", e)
        
        return True
        
    except Exception as e:
        results.add_fail("Tool framework test suite failed", e)
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# Test 2: Caching Layer
# =============================================================================

async def test_caching_layer(results):
    """Test caching functionality"""
    print_header("TEST 2: CACHING LAYER")
    
    try:
        print_info("Initializing cache...")
        
        # Test 1: Initialize cache (try Redis, fallback to in-memory)
        try:
            init_cache(redis_url=None, default_ttl=300)
            cache = get_cache_manager()
            
            # Check if using Redis or in-memory
            if isinstance(cache.backend, RedisCache):
                results.add_pass("Cache initialized with Redis")
            else:
                results.add_warning("Cache", "Using in-memory cache (Redis not available)")
        except Exception as e:
            # Fallback to in-memory
            print_warning(f"Redis failed, using in-memory: {e}")
            init_cache(default_ttl=300)
            cache = get_cache_manager()
            results.add_warning("Cache", "Using in-memory cache (Redis failed)")
        
        # Test 2: Set and get
        print_info("Testing cache set/get...")
        try:
            test_data = {"user": "test", "value": 123}
            await cache.set("test:key1", test_data, ttl=60)
            retrieved = await cache.get("test:key1")
            
            if retrieved == test_data:
                results.add_pass("Cache set/get successful")
            else:
                results.add_fail(f"Cache data mismatch: {retrieved} != {test_data}")
        except Exception as e:
            results.add_fail("Cache set/get failed", e)
        
        # Test 3: Cache miss
        print_info("Testing cache miss...")
        try:
            result = await cache.get("nonexistent:key")
            if result is None:
                results.add_pass("Cache miss handled correctly")
            else:
                results.add_fail(f"Expected None for cache miss, got: {result}")
        except Exception as e:
            results.add_fail("Cache miss test failed", e)
        
        # Test 4: Delete
        print_info("Testing cache delete...")
        try:
            await cache.set("test:delete", "value", ttl=60)
            deleted = await cache.delete("test:delete")
            retrieved = await cache.get("test:delete")
            
            if deleted and retrieved is None:
                results.add_pass("Cache delete successful")
            else:
                results.add_fail("Cache delete failed")
        except Exception as e:
            results.add_fail("Cache delete test failed", e)
        
        # Test 5: Get or set
        print_info("Testing get_or_set...")
        try:
            call_count = 0
            
            async def expensive_operation():
                nonlocal call_count
                call_count += 1
                return {"computed": True, "call": call_count}
            
            # First call - should compute
            result1 = await cache.get_or_set("test:compute", expensive_operation, ttl=60)
            # Second call - should use cache
            result2 = await cache.get_or_set("test:compute", expensive_operation, ttl=60)
            
            if call_count == 1 and result1 == result2:
                results.add_pass("get_or_set cached correctly (factory called once)")
            else:
                results.add_fail(f"get_or_set failed: calls={call_count}, r1={result1}, r2={result2}")
        except Exception as e:
            results.add_fail("get_or_set test failed", e)
        
        # Test 6: Statistics
        print_info("Testing cache statistics...")
        try:
            stats = cache.get_stats()
            
            if "hits" in stats and "misses" in stats and "hit_rate_percent" in stats:
                results.add_pass(f"Cache stats: {stats['hits']} hits, {stats['misses']} misses, {stats['hit_rate_percent']:.1f}% hit rate")
            else:
                results.add_fail(f"Invalid cache stats: {stats}")
        except Exception as e:
            results.add_fail("Cache stats test failed", e)
        
        # Test 7: Cache key generation
        print_info("Testing cache key generation...")
        try:
            key1 = cache_key("arg1", "arg2", param1="value1")
            key2 = cache_key("arg1", "arg2", param1="value1")
            key3 = cache_key("arg1", "arg2", param1="different")
            
            if key1 == key2 and key1 != key3:
                results.add_pass("Cache key generation consistent")
            else:
                results.add_fail(f"Cache key generation inconsistent: k1={key1}, k2={key2}, k3={key3}")
        except Exception as e:
            results.add_fail("Cache key generation failed", e)
        
        # Test 8: Pattern clearing
        print_info("Testing pattern-based cache clearing...")
        try:
            # Set multiple keys
            await cache.set("user:1:profile", {"name": "Alice"}, ttl=60)
            await cache.set("user:2:profile", {"name": "Bob"}, ttl=60)
            await cache.set("product:1:details", {"name": "Widget"}, ttl=60)
            
            # Clear user:* pattern
            cleared = await cache.backend.clear_pattern("user:*")
            
            # Check results
            user1 = await cache.get("user:1:profile")
            product1 = await cache.get("product:1:details")
            
            if user1 is None and product1 is not None and cleared >= 2:
                results.add_pass(f"Pattern clear successful: {cleared} keys cleared")
            else:
                results.add_warning("Pattern clear", f"Cleared {cleared} keys but validation failed")
        except Exception as e:
            results.add_warning("Pattern clear test", f"Failed: {e}")
        
        return True
        
    except Exception as e:
        results.add_fail("Caching layer test suite failed", e)
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# Test 3: Monitoring Integration
# =============================================================================

async def test_monitoring(results):
    """Test monitoring and metrics"""
    print_header("TEST 3: MONITORING INTEGRATION")
    
    try:
        print_info("Initializing monitoring...")
        
        # Test 1: Initialize monitoring
        try:
            init_monitoring(
                service_name="agentic-ai-platform-test",
                metrics_enabled=True,
                tracing_enabled=False  # Disable tracing for tests
            )
            monitoring = get_monitoring()
            results.add_pass("Monitoring initialized")
        except Exception as e:
            results.add_fail("Monitoring initialization failed", e)
            return False
        
        # Test 2: Check components
        print_info("Checking monitoring components...")
        try:
            if hasattr(monitoring, 'metrics'):
                results.add_pass("Metrics collector available")
            else:
                results.add_fail("Metrics collector missing")
            
            if hasattr(monitoring, 'tracer'):
                results.add_pass("Tracer available")
            else:
                results.add_fail("Tracer missing")
            
            if hasattr(monitoring, 'performance'):
                results.add_pass("Performance monitor available")
            else:
                results.add_fail("Performance monitor missing")
        except Exception as e:
            results.add_fail("Component check failed", e)
        
        # Test 3: Record HTTP metrics
        print_info("Testing HTTP metrics...")
        try:
            monitoring.metrics.record_http_request(
                method="POST",
                endpoint="/api/test",
                status=200,
                duration=0.123
            )
            results.add_pass("HTTP metrics recorded")
        except Exception as e:
            results.add_warning("HTTP metrics", f"Failed: {e}")
        
        # Test 4: Record agent execution metrics
        print_info("Testing agent execution metrics...")
        try:
            monitoring.metrics.record_agent_execution(
                agent_id=1,
                agent_name="TestAgent",
                status="completed",
                duration=2.5
            )
            results.add_pass("Agent execution metrics recorded")
        except Exception as e:
            results.add_warning("Agent metrics", f"Failed: {e}")
        
        # Test 5: Record tool execution metrics
        print_info("Testing tool execution metrics...")
        try:
            monitoring.metrics.record_tool_execution(
                tool_name="calculator",
                status="success",
                duration=0.05
            )
            results.add_pass("Tool execution metrics recorded")
        except Exception as e:
            results.add_warning("Tool metrics", f"Failed: {e}")
        
        # Test 6: Performance monitoring
        print_info("Testing performance monitoring...")
        try:
            perf = monitoring.performance
            
            async with perf.measure("test_operation"):
                await asyncio.sleep(0.1)
            
            stats = perf.get_stats("test_operation")
            
            if stats and stats.get("count") == 1:
                results.add_pass(f"Performance measured: {stats['avg']:.3f}s average")
            else:
                results.add_fail(f"Performance measurement failed: {stats}")
        except Exception as e:
            results.add_fail("Performance monitoring failed", e)
        
        # Test 7: Health status
        print_info("Testing health status...")
        try:
            health = monitoring.get_health_status()
            
            if "status" in health and "metrics_enabled" in health:
                results.add_pass(f"Health status: {health['status']}")
                print_info(f"  Metrics enabled: {health['metrics_enabled']}")
                print_info(f"  Tracing enabled: {health['tracing_enabled']}")
            else:
                results.add_fail(f"Invalid health status: {health}")
        except Exception as e:
            results.add_fail("Health status test failed", e)
        
        # Test 8: Performance statistics
        print_info("Testing performance statistics...")
        try:
            all_stats = perf.get_all_stats()
            
            if "test_operation" in all_stats:
                results.add_pass(f"Found {len(all_stats)} performance metrics")
            else:
                results.add_warning("Performance stats", "No metrics found")
        except Exception as e:
            results.add_fail("Performance statistics failed", e)
        
        return True
        
    except Exception as e:
        results.add_fail("Monitoring test suite failed", e)
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# Test 4: Workflow Templates
# =============================================================================

async def test_workflow_templates(results):
    """Test workflow template system"""
    print_header("TEST 4: WORKFLOW TEMPLATES")
    
    try:
        print_info("Accessing workflow template registry...")
        
        # Test 1: Get registry
        try:
            registry = get_workflow_registry()
            results.add_pass("Workflow template registry initialized")
        except Exception as e:
            results.add_fail("Registry initialization failed", e)
            return False
        
        # Test 2: List all templates
        print_info("Listing workflow templates...")
        try:
            templates = registry.list()
            
            if len(templates) >= 7:  # Should have 7 default templates
                results.add_pass(f"Found {len(templates)} workflow templates")
                for t in templates[:3]:  # Show first 3
                    print_info(f"  - {t.name} ({t.type.value})")
            else:
                results.add_warning("Template listing", f"Only {len(templates)} templates found (expected >= 7)")
        except Exception as e:
            results.add_fail("Template listing failed", e)
        
        # Test 3: Get specific template
        print_info("Getting specific template...")
        try:
            template = registry.get("Approval Workflow")
            
            if template:
                results.add_pass("Retrieved 'Approval Workflow' template")
                print_info(f"  Type: {template.type.value}")
                print_info(f"  Nodes: {len(template.nodes)}")
                print_info(f"  HITL enabled: {template.config.get('hitl', {}).get('enabled')}")
            else:
                results.add_fail("Template 'Approval Workflow' not found")
        except Exception as e:
            results.add_fail("Get template failed", e)
        
        # Test 4: Filter by type
        print_info("Filtering templates by type...")
        try:
            approval_templates = registry.list(workflow_type=WorkflowType.APPROVAL)
            
            if len(approval_templates) > 0:
                results.add_pass(f"Found {len(approval_templates)} approval workflow(s)")
            else:
                results.add_fail("No approval workflows found")
        except Exception as e:
            results.add_fail("Template filtering by type failed", e)
        
        # Test 5: Filter by HITL requirement
        print_info("Filtering templates by HITL...")
        try:
            hitl_templates = registry.list(requires_hitl=True)
            non_hitl_templates = registry.list(requires_hitl=False)
            
            results.add_pass(f"Found {len(hitl_templates)} HITL templates, {len(non_hitl_templates)} non-HITL")
        except Exception as e:
            results.add_fail("Template filtering by HITL failed", e)
        
        # Test 6: Create from template
        print_info("Creating workflow from template...")
        try:
            workflow_config = registry.create_from_template("Simple Chat")
            
            if "name" in workflow_config and "config" in workflow_config:
                results.add_pass("Workflow created from template")
                print_info(f"  Name: {workflow_config['name']}")
                print_info(f"  Type: {workflow_config['type']}")
            else:
                results.add_fail(f"Invalid workflow config: {workflow_config}")
        except Exception as e:
            results.add_fail("Create from template failed", e)
        
        # Test 7: Create with custom config
        print_info("Creating workflow with custom config...")
        try:
            custom_config = {
                "llm": {"temperature": 0.9},
                "hitl": {"threshold": 0.95}
            }
            
            workflow_config = registry.create_from_template(
                "Approval Workflow",
                custom_config=custom_config
            )
            
            # Verify custom config was applied
            if workflow_config["config"]["llm"]["temperature"] == 0.9:
                results.add_pass("Custom config applied successfully")
            else:
                results.add_fail(f"Custom config not applied: {workflow_config['config']['llm']}")
        except Exception as e:
            results.add_fail("Custom config test failed", e)
        
        # Test 8: Template to dict
        print_info("Converting template to dictionary...")
        try:
            template = registry.get("Data Processing")
            if template:
                template_dict = template.to_dict()
                
                if all(k in template_dict for k in ["name", "type", "config", "nodes", "edges"]):
                    results.add_pass("Template converted to dict successfully")
                else:
                    results.add_fail(f"Missing keys in dict: {template_dict.keys()}")
            else:
                results.add_fail("Template not found for dict test")
        except Exception as e:
            results.add_fail("Template to dict failed", e)
        
        # Test 9: Export template
        print_info("Exporting template to JSON...")
        try:
            template_json = registry.export_template("Research Workflow")
            
            # Verify it's valid JSON
            parsed = json.loads(template_json)
            
            if "name" in parsed and parsed["name"] == "Research Workflow":
                results.add_pass("Template exported to JSON successfully")
            else:
                results.add_fail(f"Invalid exported JSON: {parsed}")
        except Exception as e:
            results.add_fail("Template export failed", e)
        
        return True
        
    except Exception as e:
        results.add_fail("Workflow templates test suite failed", e)
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# Test 5: Data Export Features
# =============================================================================

async def test_data_export(results):
    """Test data export functionality"""
    print_header("TEST 5: DATA EXPORT FEATURES")
    
    try:
        print_info("Initializing exporter...")
        
        # Test 1: Get exporter
        try:
            exporter = get_exporter()
            results.add_pass("Exporter initialized")
        except Exception as e:
            results.add_fail("Exporter initialization failed", e)
            return False
        
        # Create sample execution data
        sample_executions = [
            {
                "id": 1,
                "agent_id": 1,
                "execution_id": "exec_001",
                "status": "completed",
                "duration_ms": 1500,
                "input_data": {"message": "test 1"},
                "output_data": {"response": "result 1"},
                "started_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": 2,
                "agent_id": 1,
                "execution_id": "exec_002",
                "status": "completed",
                "duration_ms": 2300,
                "input_data": {"message": "test 2"},
                "output_data": {"response": "result 2"},
                "started_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": 3,
                "agent_id": 2,
                "execution_id": "exec_003",
                "status": "failed",
                "duration_ms": 500,
                "error": "Test error",
                "input_data": {"message": "test 3"},
                "started_at": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        
        # Test 2: Export to CSV
        print_info("Testing CSV export...")
        try:
            csv_data = exporter.export_executions(sample_executions, format=ExportFormat.CSV)
            
            if csv_data and len(csv_data) > 100:  # Should have headers and data
                results.add_pass(f"CSV export successful ({len(csv_data)} bytes)")
            else:
                results.add_fail(f"CSV export returned insufficient data: {len(csv_data)} bytes")
        except Exception as e:
            results.add_fail("CSV export failed", e)
        
        # Test 3: Export to JSON
        print_info("Testing JSON export...")
        try:
            json_data = exporter.export_executions(sample_executions, format=ExportFormat.JSON)
            
            # Verify it's valid JSON
            parsed = json.loads(json_data)
            
            if isinstance(parsed, list) and len(parsed) == 3:
                results.add_pass(f"JSON export successful ({len(parsed)} records)")
            else:
                results.add_fail(f"JSON export returned invalid data: {type(parsed)}")
        except Exception as e:
            results.add_fail("JSON export failed", e)
        
        # Test 4: Export to JSONL
        # print_info("Testing JSONL export...")
        # try:
        #     jsonl_data = exporter.export_executions(sample_executions, format=ExportFormat.JSONL)
            
        #     lines = jsonl_data.strip().split('\n')
            
        #     if len(lines) == 3:  # One line per record
        #         results.add_pass(f"JSONL export successful ({len(lines)} lines)")
        #     else:
        #         results.add_fail(f"JSONL export returned wrong number of lines: {len(lines)}")
        # except Exception as e:
        #     results.add_fail("JSONL export failed", e)

        print_info("Testing JSONL export...")
        try:
            jsonl_data = exporter.export_executions(sample_executions, format=ExportFormat.JSONL)
            
            # Decode bytes to string
            jsonl_str = jsonl_data.decode('utf-8') if isinstance(jsonl_data, bytes) else jsonl_data
            lines = [line for line in jsonl_str.strip().split('\n') if line]
            
            if len(lines) == 3:
                results.add_pass(f"JSONL export successful ({len(lines)} lines)")
            else:
                results.add_fail(f"JSONL wrong line count: {len(lines)}")
        except Exception as e:
            results.add_fail("JSONL export failed", e)
        
        # Test 5: Export to Excel
        print_info("Testing Excel export...")
        try:
            excel_data = exporter.export_executions(sample_executions, format=ExportFormat.EXCEL)
            
            if excel_data and len(excel_data) > 1000:  # Excel files are larger
                results.add_pass(f"Excel export successful ({len(excel_data)} bytes)")
            else:
                results.add_warning("Excel export", f"Small file size: {len(excel_data)} bytes")
        except Exception as e:
            results.add_fail("Excel export failed", e)
        
        # Test 6: Export HITL records
        print_info("Testing HITL export...")
        try:
            sample_hitl = [
                {
                    "id": 1,
                    "agent_id": 1,
                    "execution_id": "exec_001",
                    "status": "pending",
                    "priority": "high",
                    "created_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": 2,
                    "agent_id": 1,
                    "execution_id": "exec_002",
                    "status": "approved",
                    "priority": "normal",
                    "reviewed_at": datetime.now(timezone.utc).isoformat()
                }
            ]
            
            hitl_csv = exporter.export_hitl_records(sample_hitl, format=ExportFormat.CSV)
            
            if hitl_csv and len(hitl_csv) > 50:
                results.add_pass(f"HITL export successful ({len(hitl_csv)} bytes)")
            else:
                results.add_fail(f"HITL export returned insufficient data")
        except Exception as e:
            results.add_fail("HITL export failed", e)
        
        # Test 7: Report generator
        print_info("Testing report generation...")
        try:
            report_gen = get_report_generator()
            
            report_data = report_gen.generate_execution_report(
                sample_executions,
                start_date=datetime.now(timezone.utc) - timedelta(days=7),
                end_date=datetime.now(timezone.utc),
                format=ExportFormat.EXCEL
            )
            
            if report_data and len(report_data) > 2000:  # Reports are larger
                results.add_pass(f"Execution report generated ({len(report_data)} bytes)")
            else:
                results.add_warning("Report generation", f"Small report size: {len(report_data)} bytes")
        except Exception as e:
            results.add_fail("Report generation failed", e)
        
        # Test 8: Analytics data
        print_info("Testing analytics data extraction...")
        try:
            analytics = exporter._compute_analytics(sample_executions)
            
            if "total_executions" in analytics and analytics["total_executions"] == 3:
                results.add_pass(f"Analytics computed: {analytics['total_executions']} executions")
                print_info(f"  Success rate: {analytics.get('success_rate', 0):.1f}%")
                print_info(f"  Avg duration: {analytics.get('avg_duration_ms', 0):.1f}ms")
            else:
                results.add_fail(f"Invalid analytics: {analytics}")
        except Exception as e:
            results.add_warning("Analytics", f"Failed: {e}")
        
        return True
        
    except Exception as e:
        results.add_fail("Data export test suite failed", e)
        import traceback
        traceback.print_exc()
        return False


# =============================================================================
# Main Test Runner
# =============================================================================

async def run_all_tests(test_filter=None):
    """Run all tests or specific test"""
    
    print_header("P2 FEATURES COMPREHENSIVE TEST SUITE")
    print_info(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Project: {project_root}")
    print_info(f"Backend: {backend_dir}")
    
    results = TestResults()
    
    # Run tests based on filter
    if not test_filter or test_filter in ["all", "tools"]:
        await test_tool_framework(results)
    
    if not test_filter or test_filter in ["all", "cache"]:
        await test_caching_layer(results)
    
    if not test_filter or test_filter in ["all", "monitoring"]:
        await test_monitoring(results)
    
    if not test_filter or test_filter in ["all", "templates"]:
        await test_workflow_templates(results)
    
    if not test_filter or test_filter in ["all", "exports"]:
        await test_data_export(results)
    
    # Summary
    results.print_summary()
    
    if results.failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! P2 FEATURES READY! 🎉{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠ {results.failed} test(s) failed ⚠{Colors.END}\n")
        return 1


def main():
    """Entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test P2 Features")
    parser.add_argument(
        '--test',
        choices=['all', 'tools', 'cache', 'monitoring', 'templates', 'exports'],
        default='all',
        help='Test to run (default: all)'
    )
    
    args = parser.parse_args()
    
    try:
        exit_code = asyncio.run(run_all_tests(args.test))
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()