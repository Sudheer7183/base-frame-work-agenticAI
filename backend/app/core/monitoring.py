"""
Monitoring Integration
Provides metrics, tracing, and observability
"""

import logging
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime
from contextlib import asynccontextmanager

try:
    from prometheus_client import Counter, Histogram, Gauge, Info
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

logger = logging.getLogger(__name__)


from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time

class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically record HTTP request metrics
    """
    
    def __init__(self, app, monitoring):
        super().__init__(app)
        self.monitoring = monitoring
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Record metrics for each HTTP request"""
        
        # Skip metrics endpoint itself to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        self.monitoring.metrics.record_http_request(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
            duration=duration
        )
        
        return response

class MetricsCollector:
    """
    Prometheus metrics collector
    Tracks application metrics
    """
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled and PROMETHEUS_AVAILABLE
        
        if not self.enabled:
            if not PROMETHEUS_AVAILABLE:
                logger.warning("Prometheus client not available")
            return
        
        # HTTP metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status']
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint']
        )
        
        # Agent execution metrics
        self.agent_executions_total = Counter(
            'agent_executions_total',
            'Total agent executions',
            ['agent_id', 'agent_name', 'status']
        )
        
        self.agent_execution_duration = Histogram(
            'agent_execution_duration_seconds',
            'Agent execution duration',
            ['agent_id', 'agent_name']
        )
        
        # HITL metrics
        self.hitl_records_total = Counter(
            'hitl_records_total',
            'Total HITL records',
            ['status', 'priority']
        )
        
        self.hitl_pending_count = Gauge(
            'hitl_pending_count',
            'Number of pending HITL records'
        )
        
        self.hitl_review_duration = Histogram(
            'hitl_review_duration_seconds',
            'HITL review duration'
        )
        
        # Tool execution metrics
        self.tool_executions_total = Counter(
            'tool_executions_total',
            'Total tool executions',
            ['tool_name', 'status']
        )
        
        self.tool_execution_duration = Histogram(
            'tool_execution_duration_seconds',
            'Tool execution duration',
            ['tool_name']
        )
        
        # Cache metrics
        self.cache_hits_total = Counter(
            'cache_hits_total',
            'Total cache hits'
        )
        
        self.cache_misses_total = Counter(
            'cache_misses_total',
            'Total cache misses'
        )
        
        # System metrics
        self.system_info = Info(
            'system',
            'System information'
        )
        
        logger.info("Metrics collector initialized")
    
    def record_http_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record HTTP request metrics"""
        if not self.enabled:
            return
        
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        self.http_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_agent_execution(
        self,
        agent_id: int,
        agent_name: str,
        status: str,
        duration: float
    ):
        """Record agent execution metrics"""
        if not self.enabled:
            return
        
        self.agent_executions_total.labels(
            agent_id=agent_id,
            agent_name=agent_name,
            status=status
        ).inc()
        
        self.agent_execution_duration.labels(
            agent_id=agent_id,
            agent_name=agent_name
        ).observe(duration)
    
    def record_hitl_event(self, status: str, priority: str):
        """Record HITL event"""
        if not self.enabled:
            return
        
        self.hitl_records_total.labels(
            status=status,
            priority=priority
        ).inc()
    
    def update_hitl_pending_count(self, count: int):
        """Update HITL pending count"""
        if not self.enabled:
            return
        
        self.hitl_pending_count.set(count)
    
    def record_tool_execution(self, tool_name: str, status: str, duration: float):
        """Record tool execution metrics"""
        if not self.enabled:
            return
        
        self.tool_executions_total.labels(
            tool_name=tool_name,
            status=status
        ).inc()
        
        self.tool_execution_duration.labels(
            tool_name=tool_name
        ).observe(duration)
    
    def record_cache_hit(self):
        """Record cache hit"""
        if not self.enabled:
            return
        self.cache_hits_total.inc()
    
    def record_cache_miss(self):
        """Record cache miss"""
        if not self.enabled:
            return
        self.cache_misses_total.inc()


class Tracer:
    """
    OpenTelemetry tracer wrapper
    Provides distributed tracing capabilities
    """
    
    def __init__(self, service_name: str, enabled: bool = True):
        self.service_name = service_name
        self.enabled = enabled and OTEL_AVAILABLE
        
        if not self.enabled:
            if not OTEL_AVAILABLE:
                logger.warning("OpenTelemetry not available")
            return
        
        self.tracer = trace.get_tracer(service_name)
        logger.info(f"Tracer initialized for service: {service_name}")
    
    @asynccontextmanager
    async def span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Create a trace span
        
        Usage:
            async with tracer.span("operation_name", {"key": "value"}):
                # Your code here
                pass
        """
        if not self.enabled:
            yield None
            return
        
        with self.tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
            
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def trace_function(self, span_name: Optional[str] = None):
        """
        Decorator to trace function execution
        
        Usage:
            @tracer.trace_function("my_function")
            async def my_function():
                pass
        """
        def decorator(func: Callable):
            name = span_name or f"{func.__module__}.{func.__name__}"
            
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if not self.enabled:
                    return await func(*args, **kwargs)
                
                async with self.span(name):
                    return await func(*args, **kwargs)
            
            return wrapper
        return decorator


class PerformanceMonitor:
    """
    Performance monitoring utilities
    Tracks execution times and performance metrics
    """
    
    def __init__(self):
        self._timers: Dict[str, float] = {}
        self._metrics: Dict[str, list] = {}
    
    def start_timer(self, name: str):
        """Start a named timer"""
        self._timers[name] = time.time()
    
    def stop_timer(self, name: str) -> float:
        """Stop a timer and return elapsed time"""
        if name not in self._timers:
            logger.warning(f"Timer '{name}' was not started")
            return 0.0
        
        elapsed = time.time() - self._timers[name]
        del self._timers[name]
        
        # Store metric
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(elapsed)
        
        return elapsed
    
    @asynccontextmanager
    async def measure(self, name: str):
        """
        Context manager to measure execution time
        
        Usage:
            async with monitor.measure("operation"):
                # Your code here
                pass
        """
        start = time.time()
        try:
            yield
        finally:
            elapsed = time.time() - start
            if name not in self._metrics:
                self._metrics[name] = []
            self._metrics[name].append(elapsed)
    
    def get_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a metric"""
        if name not in self._metrics or not self._metrics[name]:
            return {}
        
        values = self._metrics[name]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "total": sum(values)
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all metrics"""
        return {name: self.get_stats(name) for name in self._metrics.keys()}
    
    def reset(self, name: Optional[str] = None):
        """Reset metrics"""
        if name:
            if name in self._metrics:
                self._metrics[name] = []
        else:
            self._metrics = {}


class MonitoringManager:
    """
    Centralized monitoring manager
    Combines metrics, tracing, and performance monitoring
    """
    
    def __init__(
        self,
        service_name: str = "agentic-ai-platform",
        metrics_enabled: bool = True,
        tracing_enabled: bool = True
    ):
        self.metrics = MetricsCollector(enabled=metrics_enabled)
        self.tracer = Tracer(service_name, enabled=tracing_enabled)
        self.performance = PerformanceMonitor()
        
        logger.info("Monitoring manager initialized")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status"""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "metrics_enabled": self.metrics.enabled,
            "tracing_enabled": self.tracer.enabled,
            "performance_stats": self.performance.get_all_stats()
        }


# Global monitoring instance
_monitoring: Optional[MonitoringManager] = None


# def init_monitoring(
#     service_name: str = "agentic-ai-platform",
#     metrics_enabled: bool = True,
#     tracing_enabled: bool = True
# ):
#     """Initialize monitoring system"""
#     global _monitoring
#     _monitoring = MonitoringManager(
#         service_name=service_name,
#         metrics_enabled=metrics_enabled,
#         tracing_enabled=tracing_enabled
#     )
#     logger.info("Monitoring system initialized")

def init_monitoring(
    service_name: str = "agentic-ai-platform",
    metrics_enabled: bool = True,
    tracing_enabled: bool = True
):
    """Initialize monitoring system (idempotent - safe to call multiple times)"""
    global _monitoring
    
    # If already initialized, return existing instance
    if _monitoring is not None:
        logger.debug("Monitoring already initialized")
        return _monitoring
    
    _monitoring = MonitoringManager(
        service_name=service_name,
        metrics_enabled=metrics_enabled,
        tracing_enabled=tracing_enabled
    )
    logger.info("Monitoring system initialized")
    return _monitoring


def get_monitoring() -> MonitoringManager:
    """Get global monitoring instance"""
    if _monitoring is None:
        raise RuntimeError("Monitoring not initialized. Call init_monitoring() first")
    return _monitoring


# Convenience decorators
def monitor_execution(metric_name: str):
    """
    Decorator to monitor function execution
    Records duration and success/failure
    
    Usage:
        @monitor_execution("process_data")
        async def process_data():
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            monitoring = get_monitoring()
            start = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                
                # Record metrics
                monitoring.performance._metrics.setdefault(metric_name, []).append(duration)
                
                return result
            except Exception as e:
                duration = time.time() - start
                monitoring.performance._metrics.setdefault(f"{metric_name}_error", []).append(duration)
                raise
        
        return wrapper
    return decorator
