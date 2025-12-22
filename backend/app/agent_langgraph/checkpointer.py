# """
# LangGraph Checkpointer
# State persistence for graph execution
# """

# import logging
# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.checkpoint.postgres import PostgresSaver
# from app.core.config import settings

# logger = logging.getLogger(__name__)


# def get_checkpointer():
#     """
#     Get appropriate checkpointer based on configuration
    
#     Returns:
#         Checkpointer instance (Memory or Postgres)
#     """
#     use_postgres = getattr(settings, 'LANGGRAPH_USE_POSTGRES', False)
    
#     if use_postgres:
#         logger.info("Using PostgreSQL checkpointer for LangGraph")
#         try:
#             return PostgresSaver.from_conn_string(settings.DB_URL)
#         except Exception as e:
#             logger.warning(f"Failed to initialize PostgreSQL checkpointer: {e}")
#             logger.warning("Falling back to MemorySaver")
#             return MemorySaver()
#     else:
#         logger.info("Using MemorySaver checkpointer for LangGraph")
#         return MemorySaver()

"""
LangGraph Checkpointer
State persistence for graph execution
"""

import logging
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger(__name__)


def get_checkpointer():
    """
    Get appropriate checkpointer based on configuration
    
    Returns:
        Checkpointer instance (Memory or Postgres)
    """
    from app.core.config import settings
    
    use_postgres = getattr(settings, 'LANGGRAPH_USE_POSTGRES', False)
    
    if use_postgres:
        logger.info("Using PostgreSQL checkpointer for LangGraph")
        try:
            # Import PostgresSaver only when needed
            from langgraph.checkpoint.postgres import PostgresSaver
            return PostgresSaver.from_conn_string(settings.DB_URL)
        except ImportError:
            logger.warning("langgraph-checkpoint-postgres not installed")
            logger.warning("Install with: pip install langgraph-checkpoint-postgres")
            logger.warning("Falling back to MemorySaver")
            return MemorySaver()
        except Exception as e:
            logger.warning(f"Failed to initialize PostgreSQL checkpointer: {e}")
            logger.warning("Falling back to MemorySaver")
            return MemorySaver()
    else:
        logger.info("Using MemorySaver checkpointer for LangGraph")
        return MemorySaver()