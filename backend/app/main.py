"""Main FastAPI application with multi-tenancy"""
# ─────────────────────────────────────────────────────────────────────────────
# NOTE: The only changes from the previous version of this file are:
#
#   1. A single redis.asyncio client is created once at startup and stored on
#      app.state.redis_client — the same connection is shared by the rate
#      limiter, the cache, AND the new audit queue service.
#
#   2. audit_queue.set_redis_client(client) is called so that the
#      push_to_pipeline() helper can find the shared client without
#      dependency-injection boilerplate on every route.
#
#   3. asyncio.create_task(run_variance_worker(redis_client)) starts the
#      background consumer loop alongside the FastAPI application.
#
#   4. The worker task is cancelled cleanly on shutdown.
#
# Everything else (CORS, middleware, routers, Keycloak, backup, monitoring)
# is identical to the previous version.
# ─────────────────────────────────────────────────────────────────────────────

import asyncio
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

# ag-ui imports
from app.agui.server import create_agui_router
from app.core.security import get_current_user
from app.keycloak.service import get_keycloak_service

from app.core.rate_limiting import rate_limiter

# P2 features implementation
from app.tools.registry import register_default_tools
from app.core.cache import init_cache
from app.core.monitoring import init_monitoring
from app.api.features import router as p2_router

# P3 features implementation
from app.api.v1.workflow_marketplace import router as marketplace_router
from app.api.v1.sso_integration import router as sso_router
from app.api.v1.advanced_analytics import router as analytics_router
from app.api.v1.ai_model_management import router as models_router
from app.api.v1.auth import router as auth_api_router
from app.api.v1.agent_builder import router as agent_builder_router

# Backup routes
from app.backup.backup_service import DatabaseBackupService
from app.backup.backup_scheduler import BackupScheduler
from app.backup import backup_routes

# Metrics route
from app.api.metrics import router as metrics_router
from app.core.monitoring import MonitoringMiddleware, init_monitoring, get_monitoring

# Computational audit logging
from app.api.v1 import cost_analytics_api

# ── Workmen's Comp application ────────────────────────────────────────────────
from app.api.v1.wc_aduit_api import router as wc_audit_router
from app.api.v1.auth2 import router as auth_router
# ── NEW: Redis Stream pipeline imports ───────────────────────────────────────
import redis.asyncio as aioredis
from app.services.audit_queue import set_redis_client
from app.workers.variance_consumer import run_variance_worker

# i18n imports
import sys
from pathlib import Path
i18n_path = Path(__file__).parent.parent.parent / "i18n"
sys.path.insert(0, str(i18n_path))

from backend.core.i18n import init_i18n, get_available_locales
from backend.core.middleware import LocaleMiddleware


init_monitoring()
monitoring = get_monitoring()

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
init_i18n()

# ── CORS (must be first middleware) ──────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|[\w-]+\.localhost)(:\d+)?",
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Tenant-Slug"],
)
app.add_middleware(LocaleMiddleware)
app.add_middleware(MonitoringMiddleware, monitoring=monitoring)
app.add_middleware(
    TenantMiddleware,
    exempt_paths={
        "/api/v1/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/metrics",
        "/health",
        "api/v1/cost-analytics/health",
        "/auth/token",
    },
)

# Register exception handlers
register_exception_handlers(app)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router,           prefix=settings.API_PREFIX, tags=["health"])
app.include_router(tenant_router,                                         tags=["Tenant Management"])
app.include_router(admin_router,                                          tags=["Admin"])
app.include_router(agents.router,           prefix=settings.API_PREFIX, tags=["agents"])
app.include_router(hitl.router,             prefix=settings.API_PREFIX, tags=["hitl"])
app.include_router(users.router,            prefix=settings.API_PREFIX, tags=["users"])
app.include_router(p2_router,               prefix="/api",               tags=["P2 Features"])
app.include_router(auth_api_router,         prefix=settings.API_PREFIX, tags=["Authentication"])
app.include_router(agent_builder_router,    prefix=settings.API_PREFIX, tags=["agent-builder"])
app.include_router(create_agui_router(),                                  tags=["AG-UI"])
app.include_router(marketplace_router,      prefix="/api/v1")
app.include_router(sso_router,              prefix="/api/v1")
app.include_router(analytics_router,        prefix="/api/v1")
app.include_router(models_router,           prefix="/api/v1")
app.include_router(metrics_router)
app.include_router(cost_analytics_api.router, prefix="/api/v1", tags=["cost-analytics"])
app.include_router(wc_audit_router)          # WC audit routes
app.include_router(auth_router)

# ─────────────────────────────────────────────────────────────────────────────
# Startup — runs once when uvicorn starts
# ─────────────────────────────────────────────────────────────────────────────
from app.core.cache import get_cache_manager
@app.on_event("startup")
async def startup():
    """
    Initialise all infrastructure.

    Order matters:
      1. Rate limiter (Redis) — must connect before we can use Redis elsewhere
      2. Shared Redis client  — created once, reused by queue + cache
      3. Cache                — re-uses the same Redis URL
      4. Monitoring
      5. Default tools
      6. Variance worker      — background asyncio task consuming the audit stream
    """

    # ── 1. Rate limiter (already uses Redis internally) ──────────────
    await rate_limiter.connect()

    # ── 2. Shared Redis client for the audit pipeline ─────────────────
    #    We create ONE client and store it two places:
    #      a) app.state.redis_client  — accessible to any route via request.app.state
    #      b) audit_queue module      — accessible to push_to_pipeline() directly
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=False,   # we decode manually in audit_queue helpers
    )
    app.state.redis_client = redis_client
    set_redis_client(redis_client)      # ← register with audit_queue service
    logger.info("✓ Shared Redis client created and registered with audit_queue")

    # ── 3. Cache (reads REDIS_URL from settings — shares the same server) ──
    init_cache(
        redis_url    = settings.REDIS_URL,
        default_ttl  = settings.CACHE_DEFAULT_TTL,
    )
    cache = get_cache_manager()
    if hasattr(cache.backend, "connect"):
        await cache.backend.connect()    # ← awaits the async connection
        logger.info("✓ Redis cache backend connected")
    # ── 4. Monitoring / tracing ────────────────────────────────────────
    init_monitoring(
        service_name     = "agentic-ai-platform",
        metrics_enabled  = settings.METRICS_ENABLED,
        tracing_enabled  = settings.OTEL_ENABLED,
    )

    # ── 5. Tool registry ───────────────────────────────────────────────
    register_default_tools()

    # ── 6. Variance consumer worker ───────────────────────────────────
    #    asyncio.create_task() schedules the worker coroutine on the SAME
    #    event loop that FastAPI uses, so asyncio.Events shared between the
    #    worker and the API endpoint handlers work without any IPC.
    worker_task = asyncio.create_task(
        run_variance_worker(redis_client),
        name="wc-variance-worker",
    )
    app.state.worker_task = worker_task
    logger.info("✓ WC variance consumer worker started")

    logger.info("✓ Platform startup complete")


# ─────────────────────────────────────────────────────────────────────────────
# Full startup event (secrets + DB + Keycloak + backups)
# ─────────────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Initialise secrets, DB, Keycloak, backup scheduler."""

    # STEP 1: Secrets Manager (must be first)
    try:
        logger.info("Initializing secrets manager...")
        secrets_manager = get_secrets_manager()
        app.state.secrets_manager = secrets_manager
        health = secrets_manager.health_check()
        logger.info(
            f"✓ Secrets manager initialised — "
            f"provider={health['provider']}  "
            f"status={'Healthy' if health['provider_healthy'] else 'Unhealthy'}"
        )
    except Exception as e:
        logger.error(f"✗ Secrets manager init failed: {e}")
        raise RuntimeError(f"Secrets manager initialization failed: {e}")

    logger.info("Starting Agentic AI Platform (Multi-Tenant)...")

    # STEP 2: Tenant DB
    try:
        print("setting db url at main", settings.DB_URL)
        init_tenant_db(settings.DB_URL)
        logger.info("✓ Tenant database initialized")
    except Exception as e:
        logger.error(f"✗ Tenant DB initialization failed: {e}")
        raise

    # STEP 3: DB connectivity check
    if not check_db_connection():
        raise RuntimeError("Database connection check failed")

    # STEP 4: Keycloak
    try:
        keycloak = get_keycloak_service()
        await keycloak.get_admin_token()
        logger.info("✓ Keycloak connection established")
    except Exception as e:
        logger.error(f"✗ Keycloak connection failed: {e}")
        raise

    # STEP 5: Backup scheduler
    if settings.BACKUP_ENABLED:
        try:
            backup_service = DatabaseBackupService(
                db_host          = settings.DB_HOST,
                db_port          = settings.DB_PORT,
                db_name          = settings.DB_NAME,
                db_user          = settings.DB_USER,
                db_password      = settings.DB_PASSWORD,
                backup_dir       = settings.BACKUP_DIR,
                retention_days   = settings.BACKUP_RETENTION_DAYS,
                max_backups      = settings.BACKUP_MAX_COUNT,
            )
            backup_scheduler = BackupScheduler(
                backup_service              = backup_service,
                full_backup_schedule        = settings.BACKUP_FULL_SCHEDULE,
                tenant_backup_interval_hours = settings.BACKUP_TENANT_INTERVAL_HOURS,
                enable_monitoring           = settings.BACKUP_MONITORING_ENABLED,
            )
            backup_scheduler.start()
            app.state.backup_service   = backup_service
            app.state.backup_scheduler = backup_scheduler
            logger.info("✓ Backup system initialized")
        except Exception as e:
            logger.error(f"✗ Backup initialization failed: {e}")

    logger.info("✓ Full startup complete")


# ─────────────────────────────────────────────────────────────────────────────
# Shutdown
# ─────────────────────────────────────────────────────────────────────────────

@app.on_event("shutdown")
async def shutdown():
    """Gracefully cancel the worker and close the Redis connection."""

    # Cancel variance worker
    worker_task = getattr(app.state, "worker_task", None)
    if worker_task and not worker_task.done():
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
        logger.info("✓ WC variance worker cancelled")

    # Close shared Redis client
    redis_client = getattr(app.state, "redis_client", None)
    if redis_client:
        await redis_client.aclose()
        logger.info("✓ Shared Redis client closed")

    # Rate limiter cleanup
    await rate_limiter.disconnect()


@app.on_event("shutdown")
async def shutdown_event():
    """Additional shutdown tasks (backup scheduler, etc.)."""
    scheduler = getattr(app.state, "backup_scheduler", None)
    if scheduler:
        try:
            scheduler.stop()
            logger.info("✓ Backup scheduler stopped")
        except Exception:
            pass