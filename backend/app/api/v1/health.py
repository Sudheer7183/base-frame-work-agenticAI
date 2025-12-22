"""Health check endpoints"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db, get_db_health
from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Basic health check
    
    Returns OK if service is running
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with component status
    
    Checks:
    - Database connectivity
    - Connection pool status
    - Configuration
    """
    db_health = get_db_health()
    
    return {
        "status": "healthy" if db_health["connected"] else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "components": {
            "database": db_health,
            "config": {
                "multitenancy": settings.ENABLE_MULTITENANCY if hasattr(settings, 'ENABLE_MULTITENANCY') else False,
                "debug": settings.DEBUG,
            }
        }
    }


@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """
    Readiness check for Kubernetes
    
    Returns 200 if ready to serve traffic
    """
    db_health = get_db_health()
    
    if not db_health["connected"]:
        return {"ready": False, "reason": "Database not connected"}, 503
    
    return {"ready": True, "timestamp": datetime.utcnow().isoformat()}


@router.get("/health/live")
async def liveness_check():
    """
    Liveness check for Kubernetes
    
    Returns 200 if process is alive
    """
    return {"alive": True, "timestamp": datetime.utcnow().isoformat()}