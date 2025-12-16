# """
# Alembic environment configuration with proper connection handling.
# """
# from logging.config import fileConfig
# from sqlalchemy import engine_from_config, pool
# from alembic import context
# import os
# import sys

# # Add parent directory to path for imports
# sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# from app.core.config import settings
# from app.core.database import Base

# # Import all models to ensure they're registered with Base
# from app.models.agent import AgentConfig  # noqa: F401
# from app.models.hitl import HITLRecord  # noqa: F401
# from app.models.user import User  # noqa: F401

# # this is the Alembic Config object
# config = context.config

# # Interpret the config file for Python logging.
# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)

# # Set database URL from settings
# config.set_main_option("sqlalchemy.url", settings.DB_URL)

# # add your model's MetaData object here for 'autogenerate' support
# target_metadata = Base.metadata


# def run_migrations_offline() -> None:
#     """
#     Run migrations in 'offline' mode.
    
#     This configures the context with just a URL
#     and not an Engine, though an Engine is acceptable
#     here as well. By skipping the Engine creation
#     we don't even need a DBAPI to be available.
    
#     Calls to context.execute() here emit the given string to the
#     script output.
#     """
#     url = config.get_main_option("sqlalchemy.url")
#     context.configure(
#         url=url,
#         target_metadata=target_metadata,
#         literal_binds=True,
#         dialect_opts={"paramstyle": "named"},
#         compare_type=True,
#         compare_server_default=True,
#     )

#     with context.begin_transaction():
#         context.run_migrations()


# def run_migrations_online() -> None:
#     """
#     Run migrations in 'online' mode.
    
#     In this scenario we need to create an Engine
#     and associate a connection with the context.
#     """
#     # Get configuration from alembic.ini
#     configuration = config.get_section(config.config_ini_section)
#     configuration["sqlalchemy.url"] = settings.DB_URL
    
#     connectable = engine_from_config(
#         configuration,
#         prefix="sqlalchemy.",
#         poolclass=pool.NullPool,  # Don't pool connections for migrations
#     )

#     with connectable.connect() as connection:
#         context.configure(
#             connection=connection,
#             target_metadata=target_metadata,
#             compare_type=True,
#             compare_server_default=True,
#             # Include schemas if using multiple schemas
#             # include_schemas=True,
#         )

#         with context.begin_transaction():
#             context.run_migrations()


# if context.is_offline_mode():
#     run_migrations_offline()
# else:
#     run_migrations_online()


"""Alembic environment configuration for multi-tenancy"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context
from app.core.config import settings
from app.tenancy.models import Base

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    
    # Get schema from config (set when running migrations)
    schema = config.get_main_option("schema", "public")
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Set search path to target schema
        connection.execute(text(f'SET search_path TO "{schema}", public'))
        
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=schema
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
