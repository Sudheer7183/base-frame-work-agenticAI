"""
Prometheus Metrics Endpoint
Exposes metrics for Prometheus scraping
"""

from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.core.monitoring import get_monitoring

router = APIRouter(prefix="/metrics", tags=["Monitoring"])


@router.get("")
async def metrics():
    """
    Prometheus metrics endpoint
    
    Returns:
        Prometheus-formatted metrics
    """
    monitoring = get_monitoring()
    
    # Generate metrics in Prometheus format
    metrics_output = generate_latest()
    
    return Response(
        content=metrics_output,
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    
    Returns:
        System health status
    """
    monitoring = get_monitoring()
    return monitoring.get_health_status()
