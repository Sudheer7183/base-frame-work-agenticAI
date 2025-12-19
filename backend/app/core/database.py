"""
Enhanced database configuration with connection pooling and health checks.
"""
from typing import Generator, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.exc import OperationalError, SQLAlchemyError
import logging
from fastapi import Request
from app.core.config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with optimized settings
engine = create_engine(
    settings.DB_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,  # Enable connection health checks
    echo=settings.DEBUG,
    future=True,
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


# Event listeners for connection monitoring
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log database connections."""
    logger.debug("Database connection established")


@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log connection checkouts from pool."""
    logger.debug("Connection checked out from pool")


@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Log connection returns to pool."""
    logger.debug("Connection returned to pool")


# def get_db() -> Generator[Session, None, None]:
#     """
#     Dependency for FastAPI routes to get database session.
    
#     Yields:
#         Session: SQLAlchemy database session
        
#     Example:
#         @app.get("/items")
#         def get_items(db: Session = Depends(get_db)):
#             return db.query(Item).all()
#     """
#     db = SessionLocal()
#     try:
#         yield db
#     except SQLAlchemyError as e:
#         logger.error(f"Database error: {e}")
#         db.rollback()
#         raise
#     finally:
#         db.close()

def get_db(request: Request) -> Generator[Session, None, None]:
    """
    Multi-tenant aware database dependency.
    Automatically sets search_path based on the resolved tenant.
    """
    # Extract tenant from request state (set by TenantMiddleware)
    tenant = getattr(request.state, "tenant", None)
    
    db = SessionLocal()
    try:
        if tenant and hasattr(tenant, "schema_name"):
            # Set the PostgreSQL search_path to the tenant's schema
            # This ensures queries look in the correct isolated table
            schema = tenant.schema_name
            db.execute(text(f'SET search_path TO "{schema}", public'))
            logger.debug(f"Database session switched to schema: {schema}")
        else:
            # Fallback to public if no tenant is found (e.g., global routes)
            db.execute(text('SET search_path TO public'))
            
        yield db
    except Exception as e:
        logger.error(f"Error in database session: {e}")
        raise
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions in non-FastAPI code.
    
    Example:
        with get_db_context() as db:
            items = db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.
    Should only be used in development or tests.
    In production, use Alembic migrations.
    """
    logger.info("Initializing database tables")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def check_db_connection() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        bool: True if connection is healthy, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except OperationalError as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def get_db_health() -> dict:
    """
    Get detailed database health information.
    
    Returns:
        dict: Health status with connection pool stats
    """
    try:
        # Check connection
        is_connected = check_db_connection()
        
        # Get pool statistics
        pool_status = {
            "size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "overflow": engine.pool.overflow(),
            "checked_out": engine.pool.size() - engine.pool.checkedin(),
        }
        
        return {
            "status": "healthy" if is_connected else "unhealthy",
            "connected": is_connected,
            "pool": pool_status,
            "url": settings.DB_URL.split("@")[-1],  # Hide credentials
        }
    except Exception as e:
        logger.error(f"Failed to get database health: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
        }


def close_db_connections() -> None:
    """
    Close all database connections.
    Should be called on application shutdown.
    """
    logger.info("Closing database connections")
    try:
        engine.dispose()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")


# Utility function for testing
def reset_db() -> None:
    """
    Drop and recreate all tables.
    WARNING: This will delete all data!
    Only use in development/testing.
    """
    if settings.is_production:
        raise RuntimeError("Cannot reset database in production")
    
    logger.warning("Resetting database - all data will be lost!")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Database reset complete")


# Transaction utilities
class TransactionManager:
    """
    Context manager for explicit transaction control.
    
    Example:
        with TransactionManager() as db:
            item = Item(name="test")
            db.add(item)
            # Transaction auto-commits on success
    """
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or SessionLocal()
        self.should_close = session is None
    
    def __enter__(self) -> Session:
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
            logger.error(f"Transaction rolled back due to: {exc_val}")
        else:
            try:
                self.session.commit()
            except SQLAlchemyError as e:
                self.session.rollback()
                logger.error(f"Transaction commit failed: {e}")
                raise
        
        if self.should_close:
            self.session.close()


# Async database support (optional, for async endpoints)
try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    
    async_engine = create_async_engine(
        settings.database_url_async,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=settings.DB_POOL_RECYCLE,
        echo=settings.DEBUG,
        future=True,
    )
    
    AsyncSessionLocal = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async def get_async_db() -> Generator[AsyncSession, None, None]:
        """Async database session dependency."""
        async with AsyncSessionLocal() as session:
            try:
                yield session
            except SQLAlchemyError as e:
                logger.error(f"Async database error: {e}")
                await session.rollback()
                raise
            finally:
                await session.close()
    
except ImportError:
    logger.warning("Async database support not available (asyncpg not installed)")
    async_engine = None
    AsyncSessionLocal = None
    get_async_db = None