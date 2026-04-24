
from logging.config import fileConfig
from sqlalchemy import pool, text, create_engine
from alembic import context
import os
 
config = context.config
 
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
 
target_metadata = None  # DDL is written explicitly in 001_all_tables.py
 
 
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
 
def get_database_url() -> str:
    return (
        config.get_main_option("sqlalchemy.url")
        or os.environ.get("DATABASE_URL", "")
    )
 
 
def get_all_tenant_schemas(connection) -> list:
    """
    Returns all schema_names from public.tenants (active tenants only).
    Returns [] gracefully if the tenants table doesn't exist yet.
    """
    try:
        result = connection.execute(
            text("SELECT schema_name FROM public.tenants WHERE status = 'active' ORDER BY schema_name")
        )
        schemas = [row[0] for row in result]
        print(f"[env.py] Found {len(schemas)} tenant schema(s): {schemas}")
        return schemas
    except Exception:
        print("[env.py] tenants table not found yet — first run, public schema only")
        return []
 
 
def run_migrations_for_schema(connection, schema: str) -> None:
    """Run 001_all_tables migration against a specific schema."""
    print(f"[env.py] ── Migrating schema: {schema}")
 
    # Ensure schema exists
    connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"'))
    connection.execute(text(f'SET search_path TO "{schema}", public'))
    connection.commit()
 
    # Ensure alembic_version table exists in this schema
    connection.execute(text(f"""
        CREATE TABLE IF NOT EXISTS "{schema}".alembic_version (
            version_num VARCHAR(32) NOT NULL,
            CONSTRAINT pk_{schema[:30]}_alembic PRIMARY KEY (version_num)
        )
    """))
    connection.commit()
 
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table="alembic_version",
        version_table_schema=schema,
        include_schemas=True,
        compare_type=True,
    )
 
    with context.begin_transaction():
        context.run_migrations()
 
    print(f"[env.py] ✅ Schema '{schema}' done")
 
 
# ---------------------------------------------------------------------------
# Offline mode
# ---------------------------------------------------------------------------
 
def run_migrations_offline() -> None:
    context.configure(
        url=get_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
 
 
# ---------------------------------------------------------------------------
# Online mode
# ---------------------------------------------------------------------------
 
def run_migrations_online() -> None:
    db_url = get_database_url()
    engine = create_engine(db_url, poolclass=pool.NullPool)
 
    # Check if this is a targeted single-schema call (from tenant_registration.py)
    target_schema = config.get_main_option("target_schema") or None
 
    with engine.connect() as connection:
        if target_schema:
            # ── Single schema mode (new tenant just registered) ──────────
            print(f"[env.py] Single-schema mode: migrating '{target_schema}' only")
            run_migrations_for_schema(connection, target_schema)
        else:
            # ── Full mode: public + all tenants ──────────────────────────
            print("[env.py] Full migration mode: public + all tenants")
 
            # Always migrate public first (creates tenants table)
            run_migrations_for_schema(connection, "public")
 
            # Then discover and migrate all tenant schemas
            tenant_schemas = get_all_tenant_schemas(connection)
            for schema in tenant_schemas:
                run_migrations_for_schema(connection, schema)
 
            print(f"\n[env.py] ✅ All {1 + len(tenant_schemas)} schema(s) migrated.")
 
 
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()