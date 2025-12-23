# """Database connection and schema management"""

# import logging
# import time
# from typing import Optional
# from sqlalchemy import create_engine, text, event, pool
# from sqlalchemy.engine import Engine
# from sqlalchemy.orm import sessionmaker, Session
# from .context import get_tenant
# from .validators import validate_schema_name
# from .exceptions import InvalidTenantError

# logger = logging.getLogger(__name__)

# # Global engine instance
# _engine: Optional[Engine] = None
# _SessionLocal: Optional[sessionmaker] = None


# def init_db(database_url: str, **engine_kwargs) -> Engine:
#     """
#     Initialize database engine with tenant support
    
#     Args:
#         database_url: PostgreSQL connection string
#         **engine_kwargs: Additional arguments for create_engine
        
#     Returns:
#         SQLAlchemy Engine
#     """
#     global _engine, _SessionLocal
    
#     if _engine is not None:
#         logger.warning("Database already initialized, returning existing engine")
#         return _engine
    
#     # Default engine configuration
#     default_config = {
#         "pool_pre_ping": True,
#         "pool_size": 20,
#         "max_overflow": 10,
#         "pool_recycle": 3600,
#         "echo": False,
#         "poolclass": pool.QueuePool,
#     }
    
#     # Merge with provided config
#     config = {**default_config, **engine_kwargs}
    
#     logger.info("Initializing database engine")
#     _engine = create_engine(database_url, **config)
    
#     # Set up search_path event listener
#     setup_search_path_listener(_engine)
    
#     # Create session factory
#     _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    
#     logger.info("Database engine initialized successfully")
#     return _engine


# def get_engine() -> Engine:
#     """Get the database engine"""
#     if _engine is None:
#         raise RuntimeError("Database not initialized. Call init_db() first.")
#     return _engine


# def get_session() -> Session:
#     """Get a new database session"""
#     if _SessionLocal is None:
#         raise RuntimeError("Database not initialized. Call init_db() first.")
#     return _SessionLocal()


# def setup_search_path_listener(engine: Engine) -> None:
#     """
#     Set up SQLAlchemy event listener to set search_path for each connection
    
#     This ensures all queries run in the correct tenant schema
#     """
    
#     # @event.listens_for(engine, "connect")
#     # def set_search_path(dbapi_conn, connection_record):
#     #     """Set search_path when connection is established"""
#     #     tenant_schema = get_tenant()
        
#     #     if not tenant_schema:
#     #         # No tenant in context - use public schema only
#     #         return
        
#     #     # Validate schema name before using it
#     #     try:
#     #         validate_schema_name(tenant_schema)
#     #     except InvalidTenantError as e:
#     #         logger.error(f"Invalid tenant schema in context: {tenant_schema}")
#     #         raise
        
#     #     # Measure performance
#     #     start_time = time.time()
        
#     #     # Set search_path using parameter binding for safety
#     #     cursor = dbapi_conn.cursor()
#     #     try:
#     #         # Use format with identifier quoting for safety
#     #         cursor.execute(
#     #             f'SET search_path TO "{tenant_schema}", public'
#     #         )
            
#     #         duration = time.time() - start_time
            
#     #         if duration > 0.1:
#     #             logger.warning(
#     #                 f"Slow search_path switch: {duration:.3f}s for tenant {tenant_schema}"
#     #             )
#     #         else:
#     #             logger.debug(
#     #                 f"Search path set to {tenant_schema} in {duration:.3f}s"
#     #             )
#     #     finally:
#     #         cursor.close()

#     @event.listens_for(engine, "connect")
#     def set_search_path(dbapi_conn, connection_record):
#         tenant_schema = get_tenant()

#         if not tenant_schema:
#             return

#         cursor = dbapi_conn.cursor()
#         cursor.execute(
#             f'SET search_path TO "{tenant_schema}", public'
#         )
    
#     @event.listens_for(engine, "checkin")
#     def reset_search_path(dbapi_conn, connection_record):
#         """Reset search_path when connection is returned to pool"""
#         cursor = dbapi_conn.cursor()
#         try:
#             cursor.execute("SET search_path TO public")
#         except Exception as e:
#             logger.warning(f"Failed to reset search_path: {e}")
#         finally:
#             cursor.close()


# def execute_in_schema(schema: str, sql: str, params: dict = None) -> None:
#     """
#     Execute SQL in a specific schema
    
#     Args:
#         schema: Schema name
#         sql: SQL statement
#         params: Query parameters
#     """
#     validate_schema_name(schema)
    
#     engine = get_engine()
#     with engine.connect() as conn:
#         # Set search path
#         conn.execute(text(f'SET search_path TO "{schema}", public'))
        
#         # Execute query
#         if params:
#             conn.execute(text(sql), params)
#         else:
#             conn.execute(text(sql))
        
#         conn.commit()


"""Database connection and schema management - ULTIMATE FIX"""

import logging
import time
from typing import Optional
from sqlalchemy import create_engine, text, event, pool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from .context import get_tenant
from .validators import validate_schema_name
from .exceptions import InvalidTenantError

logger = logging.getLogger(__name__)

# Global engine instance
_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def init_db(database_url: str, **engine_kwargs) -> Engine:
    """
    Initialize database engine with tenant support
    
    Args:
        database_url: PostgreSQL connection string
        **engine_kwargs: Additional arguments for create_engine
        
    Returns:
        SQLAlchemy Engine
    """
    global _engine, _SessionLocal
    
    if _engine is not None:
        logger.warning("Database already initialized, returning existing engine")
        return _engine
    
    # Default engine configuration
    # CRITICAL FIX: Disable pool_pre_ping to avoid transaction conflicts
    default_config = {
        "pool_pre_ping": False,  # ✅ DISABLED - causes transaction conflicts with psycopg2
        "pool_size": 20,
        "max_overflow": 10,
        "pool_recycle": 3600,  # Recycle connections every hour instead
        "echo": False,
        "poolclass": pool.QueuePool,
    }
    
    # Merge with provided config
    config = {**default_config, **engine_kwargs}
    
    logger.info("Initializing database engine with proper transaction support")
    _engine = create_engine(database_url, **config)
    
    # Set up search_path event listener
    setup_search_path_listener(_engine)
    
    # Create session factory with proper transaction handling
    _SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine
    )
    
    logger.info("Database engine initialized successfully")
    return _engine


def get_engine() -> Engine:
    """Get the database engine"""
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _engine


def get_session() -> Session:
    """Get a new database session"""
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _SessionLocal()


def setup_search_path_listener(engine: Engine) -> None:
    """
    Set up SQLAlchemy event listener to set search_path for each connection
    
    This ensures all queries run in the correct tenant schema
    """
    
    @event.listens_for(engine, "connect")
    def set_search_path(dbapi_conn, connection_record):
        """Set search_path when connection is established"""
        tenant_schema = get_tenant()
        
        if not tenant_schema:
            # No tenant in context - use public schema only
            return
        
        # Validate schema name before using it
        try:
            validate_schema_name(tenant_schema)
        except InvalidTenantError as e:
            logger.error(f"Invalid tenant schema in context: {tenant_schema}")
            raise
        
        # Check if connection is valid
        if dbapi_conn is None:
            logger.warning("Received None connection in set_search_path")
            return
        
        # Measure performance
        start_time = time.time()
        
        # Set search_path using raw connection
        cursor = None
        try:
            cursor = dbapi_conn.cursor()
            # Use identifier quoting for safety
            cursor.execute(
                f'SET search_path TO "{tenant_schema}", public'
            )
            # Don't commit - let SQLAlchemy handle transactions
            
            duration = time.time() - start_time
            
            if duration > 0.1:
                logger.warning(
                    f"Slow search_path switch: {duration:.3f}s for tenant {tenant_schema}"
                )
            else:
                logger.debug(
                    f"Search path set to {tenant_schema} in {duration:.3f}s"
                )
        except Exception as e:
            logger.error(f"Failed to set search_path: {e}")
            # Don't raise - allow connection to continue
        finally:
            if cursor is not None:
                cursor.close()
    
    @event.listens_for(engine, "checkin")
    def reset_search_path(dbapi_conn, connection_record):
        """Reset search_path when connection is returned to pool"""
        # Check if connection is valid (can be None on error)
        if dbapi_conn is None:
            logger.debug("Skipping search_path reset for None connection")
            return
        
        cursor = None
        try:
            cursor = dbapi_conn.cursor()
            cursor.execute("SET search_path TO public")
        except Exception as e:
            logger.warning(f"Failed to reset search_path: {e}")
            # Don't raise - connection might be in bad state
        finally:
            if cursor is not None:
                cursor.close()


def execute_in_schema(schema: str, sql: str, params: dict = None) -> None:
    """
    Execute SQL in a specific schema with proper transaction handling
    
    Args:
        schema: Schema name
        sql: SQL statement
        params: Query parameters
    """
    validate_schema_name(schema)
    
    engine = get_engine()
    
    # Use proper transaction context
    with engine.begin() as conn:
        # Set search path
        conn.execute(text(f'SET search_path TO "{schema}", public'))
        
        # Execute query
        if params:
            conn.execute(text(sql), params)
        else:
            conn.execute(text(sql))


def execute_raw_sql(sql: str, params: dict = None, autocommit: bool = False):
    """
    Execute raw SQL with optional autocommit for DDL operations
    
    Args:
        sql: SQL statement
        params: Query parameters
        autocommit: If True, execute outside transaction (for CREATE DATABASE, etc.)
    """
    engine = get_engine()
    
    if autocommit:
        # For DDL operations that require autocommit
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            if params:
                conn.execute(text(sql), params)
            else:
                conn.execute(text(sql))
    else:
        # For normal operations with transaction support
        with engine.begin() as conn:
            if params:
                conn.execute(text(sql), params)
            else:
                conn.execute(text(sql))