
"""Main FastAPI application with multi-tenancy"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import register_exception_handlers
from app.core.database import check_db_connection

# Secrets Management
from app.core.secrets import get_secrets_manager

# Multi-tenancy imports
from app.tenancy.middleware import TenantMiddleware
from app.tenancy.api import router as tenant_router
from app.tenancy.db import init_db as init_tenant_db

# Admin imports
from app.admin.routes import router as admin_router

# Existing imports
from app.api.v1 import agents, hitl, health, users

#ag-ui imports

from app.agui.server import create_agui_router
from app.core.security import get_current_user  # Use enhanced version
from app.keycloak.service import get_keycloak_service

from app.core.rate_limiting import rate_limiter

#P2 features implementation. 

from app.tools.registry import register_default_tools
from app.core.cache import init_cache
from app.core.monitoring import init_monitoring
from app.api.p2_features import router as p2_router

#P3 features implementation

from app.api.v1.workflow_marketplace import router as marketplace_router
from app.api.v1.sso_integration import router as sso_router
from app.api.v1.advanced_analytics import router as analytics_router
from app.api.v1.ai_model_management import router as models_router
from app.api.v1.auth import router as auth_api_router
from app.api.v1.agent_builder import router as agent_builder_router  # Add this

#Backup routes 

from app.backup.backup_service import DatabaseBackupService
from app.backup.backup_scheduler import BackupScheduler
from app.backup import backup_routes

#metrics route
from app.api.metrics import router as metrics_router

# Setup logging
setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME + " (Multi-Tenant)",
    version="1.3.0",
    description="Enterprise-grade multi-tenant AI platform",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS (MUST be first)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.CORS_ORIGINS,
#     allow_credentials=settings.CORS_CREDENTIALS,
#     allow_methods=settings.CORS_METHODS,
#     allow_headers=settings.CORS_HEADERS,
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",  # Vite alt
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Tenant-Slug"],
)

# Add tenant middleware (AFTER CORS)
app.add_middleware(
    TenantMiddleware,
    exempt_paths={
        "/api/v1/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
)

# Register exception handlers
register_exception_handlers(app)

# Include routers
app.include_router(health.router, prefix=settings.API_PREFIX, tags=["health"])
app.include_router(tenant_router, tags=["Tenant Management"])
app.include_router(admin_router, tags=["Admin"])
app.include_router(agents.router, prefix=settings.API_PREFIX, tags=["agents"])
app.include_router(hitl.router, prefix=settings.API_PREFIX, tags=["hitl"])
app.include_router(users.router, prefix=settings.API_PREFIX, tags=["users"])
app.include_router(p2_router, prefix="/api", tags=["P2 Features"])
app.include_router(auth_api_router,prefix=settings.API_PREFIX,tags=["Authentication"])
#ag-ui-routers

# app.include_router(agents_router, prefix="/agents", tags=["agents"])
app.include_router(agent_builder_router,prefix=settings.API_PREFIX, tags=["agent-builder"])  # Add this


app.include_router(create_agui_router(), tags=["AG-UI"])

#P3 routers

app.include_router(marketplace_router, prefix="/api/v1")
app.include_router(sso_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(models_router, prefix="/api/v1")
app.include_router(metrics_router)


# @app.on_event("startup")
# async def startup_event():
#     """Run on application startup."""
#     logger.info("Starting Agentic AI Platform (Multi-Tenant)...")
    
#     # Initialize database connections
#     if not check_db_connection():
#         raise RuntimeError("Database connection failed")
    
#     # Initialize tenant database
#     init_tenant_db(settings.DB_URL)
    
#     logger.info("Platform started successfully")

# @app.on_event("startup")
# async def startup():
#     """Initialize Keycloak connection on startup"""
#     keycloak = get_keycloak_service()
    
#     # Verify connection
#     try:
#         await keycloak.get_admin_token()
#         logger.info("✓ Keycloak connection established")
#     except Exception as e:
#         logger.error(f"✗ Keycloak connection failed: {e}")

@app.on_event("startup")
async def startup():
    await rate_limiter.connect()

    init_cache(
        redis_url=settings.REDIS_URL,
        default_ttl=settings.CACHE_DEFAULT_TTL
    )
    
    # Initialize monitoring
    init_monitoring(
        service_name="agentic-ai-platform",
        metrics_enabled=settings.METRICS_ENABLED,
        tracing_enabled=settings.OTEL_ENABLED
    )
    
    # Register default tools
    register_default_tools()


@app.on_event("shutdown")
async def shutdown():
    await rate_limiter.disconnect()

@app.on_event("startup")
async def startup_event():

    # ========================================================================
    # STEP 1: Initialize Secrets Manager (MUST BE FIRST)
    # ========================================================================
    try:
        logger.info("Initializing secrets manager...")
        secrets_manager = get_secrets_manager()
        app.state.secrets_manager = secrets_manager
        
        # Health check
        health = secrets_manager.health_check()
        logger.info(f"✓ Secrets manager initialized successfully")
        logger.info(f"  - Provider: {health['provider']}")
        logger.info(f"  - Status: {'Healthy' if health['provider_healthy'] else 'Unhealthy'}")
        logger.info(f"  - Secrets count: {health.get('secrets_count', 'N/A')}")
        logger.info(f"  - Cache size: {health['cache_size']}")
        
    except Exception as e:
        logger.error(f"✗ Failed to initialize secrets manager: {e}")
        logger.error("  Secrets management is required for secure operation")
        raise RuntimeError(f"Secrets manager initialization failed: {e}")


    logger.info("Starting Agentic AI Platform (Multi-Tenant)...")
    
    # 1️⃣ Initialize Tenant Database FIRST
    try:
        print("setting db url at main",settings.DB_URL)
        init_tenant_db(settings.DB_URL)
        logger.info("✓ Tenant database initialized")
    except Exception as e:
        logger.error(f"✗ Tenant DB initialization failed: {e}")
        raise

    # 2️⃣ Optional: Check DB connectivity
    if not check_db_connection():
        raise RuntimeError("Database connection check failed")

    # 3️⃣ Initialize Keycloak
    try:
        keycloak = get_keycloak_service()
        await keycloak.get_admin_token()
        logger.info("✓ Keycloak connection established")
    except Exception as e:
        logger.error(f"✗ Keycloak connection failed: {e}")
        raise
    
    #Backup intialization
    if settings.BACKUP_ENABLED:
        try:
            backup_service = DatabaseBackupService(
                db_host=settings.DB_HOST,
                db_port=settings.DB_PORT,
                db_name=settings.DB_NAME,
                db_user=settings.DB_USER,
                db_password=settings.DB_PASSWORD,
                backup_dir=settings.BACKUP_DIR,
                retention_days=settings.BACKUP_RETENTION_DAYS,
                max_backups=settings.BACKUP_MAX_COUNT
            )
            
            backup_scheduler = BackupScheduler(
                backup_service=backup_service,
                full_backup_schedule=settings.BACKUP_FULL_SCHEDULE,
                tenant_backup_interval_hours=settings.BACKUP_TENANT_INTERVAL_HOURS,
                enable_monitoring=settings.BACKUP_MONITORING_ENABLED
            )
            
            backup_scheduler.start()
            
            app.state.backup_service = backup_service
            app.state.backup_scheduler = backup_scheduler
            
            logger.info("✓ Backup system initialized")
        except Exception as e:
            logger.error(f"✗ Backup initialization failed: {e}")


    logger.info("✓ Platform startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    if hasattr(app.state, 'backup_scheduler'):
        app.state.backup_scheduler.stop()
    from app.core.database import close_db_connections
    close_db_connections()
    logger.info("Platform shutdown complete")

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Agentic AI Platform API",
        "version": "1.3.0",
        "multitenancy": "enabled",
        "docs": "/docs",
        "health": "/health",
        "admin": "/admin"
    }