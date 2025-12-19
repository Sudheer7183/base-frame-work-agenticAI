# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from app.core.config import settings
# from app.core.database import init_db
# from app.core.exceptions import register_exception_handlers
# from app.api.v1 import agents, hitl, health, users

# app = FastAPI(title="Agentic AI Platform", version="1.3.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# register_exception_handlers(app)

# app.include_router(health.router, prefix="/api/v1")
# app.include_router(agents.router, prefix="/api/v1")
# app.include_router(hitl.router, prefix="/api/v1")
# app.include_router(users.router, prefix="/api/v1")

# @app.on_event("startup")
# async def startup():
#     init_db(settings.DB_URL)

"""Main FastAPI application with multi-tenancy"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import register_exception_handlers
from app.core.database import check_db_connection

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
        "http://localhost:3000",   # React admin
        "http://localhost:5173",   # Vite alt
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

#ag-ui-routers

app.include_router(create_agui_router(), tags=["AG-UI"])

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
async def startup_event():
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

    logger.info("✓ Platform startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
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