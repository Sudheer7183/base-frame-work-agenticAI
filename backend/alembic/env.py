# from logging.config import fileConfig

# from sqlalchemy import engine_from_config
# from sqlalchemy import pool
# from sqlalchemy import text
# from alembic import context
# from app.tenancy.models import Base
# # this is the Alembic Config object, which provides
# # access to the values within the .ini file in use.
# config = context.config

# # Interpret the config file for Python logging.
# # This line sets up loggers basically.
# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)

# # add your model's MetaData object here
# # for 'autogenerate' support
# # from myapp import mymodel
# # target_metadata = mymodel.Base.metadata
# target_metadata = Base.metadata

# # other values from the config, defined by the needs of env.py,
# # can be acquired:
# # my_important_option = config.get_main_option("my_important_option")
# # ... etc.


# def run_migrations_offline() -> None:
#     """Run migrations in 'offline' mode.

#     This configures the context with just a URL
#     and not an Engine, though an Engine is acceptable
#     here as well.  By skipping the Engine creation
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
#     )

#     with context.begin_transaction():
#         context.run_migrations()


# def run_migrations_online() -> None:
#     connectable = engine_from_config(
#         config.get_section(config.config_ini_section, {}),
#         prefix="sqlalchemy.",
#         poolclass=pool.NullPool,
#     )

#     with connectable.connect() as connection:
#         schema = config.get_main_option("schema")

#         if schema:
#             connection.execute(text(f'SET search_path TO "{schema}", public'))

#             # 🔥 FORCE version table creation per tenant
#             connection.execute(
#                 text(
#                     f'''
#                     CREATE TABLE IF NOT EXISTS "{schema}".alembic_version (
#                         version_num VARCHAR(32) NOT NULL PRIMARY KEY
#                     )
#                     '''
#                 )
#             )

#         context.configure(
#             connection=connection,
#             target_metadata=target_metadata,
#             version_table="alembic_version",
#             version_table_schema=schema,
#             include_schemas=True,
#         )

#         with context.begin_transaction():
#             context.run_migrations()


# if context.is_offline_mode():
#     run_migrations_offline()
# else:
#     run_migrations_online()


"""
Alembic environment configuration for multi-tenancy
Supports running migrations in both public and tenant schemas
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, text
from alembic import context
import os

# Import your models
from app.tenancy.models import Base as TenantBase
from app.models.user import User
from app.models.agent import AgentConfig
from app.models.hitl import HITLRecord

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here
target_metadata = TenantBase.metadata


def get_schema_from_config():
    """
    Get the target schema from alembic config.
    This is set when running migrations via scripts.
    """
    schema = config.get_main_option("schema")
    if schema:
        print(f"[env.py] Using schema from config: {schema}")
    return schema or "public"


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    """
    schema = get_schema_from_config()
    
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=schema,
        include_schemas=True,
    )

    with context.begin_transaction():
        # Set search path for this schema
        context.execute(f'SET search_path TO "{schema}", public')
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.
    This is the main function that handles tenant schema migrations.
    """
    # Get target schema (could be 'public' or 'tenant_xxx')
    schema = get_schema_from_config()
    
    print(f"[env.py] Running migrations for schema: {schema}")
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # CRITICAL: Set search_path BEFORE configuring context
        print(f"[env.py] Setting search_path to: {schema}, public")
        connection.execute(text(f'SET search_path TO "{schema}", public'))
        connection.commit()
        
        # Configure context with schema-aware settings
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=schema,  # Store alembic_version in this schema
            include_schemas=True,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            # Double-check search path is set
            result = connection.execute(text("SHOW search_path"))
            current_path = result.scalar()
            print(f"[env.py] Current search_path: {current_path}")
            
            # Run the migrations
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()