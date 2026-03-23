# # """Script to run migrations for all active tenants"""

# # import sys
# # from pathlib import Path

# # # Add backend to path
# # sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# # from sqlalchemy.orm import Session
# # from alembic import command
# # from alembic.config import Config
# # from app.tenancy.db import init_db, get_session
# # from app.tenancy.models import Tenant, TenantStatus
# # # from app.core.config import settings
# # import logging

# # from pathlib import Path

# # BASE_DIR = Path(__file__).resolve().parent.parent  # adjust if needed
# # BACKEND_DIR = BASE_DIR / "backend"

# # logging.basicConfig(level=logging.INFO)
# # logger = logging.getLogger(__name__)


# # def migrate_all_tenants():
# #     """Run migrations for all active tenants"""
    
# #     # Initialize database
# #     # init_db(settings.DATABASE_URL)
# #     init_db("postgresql://postgres:postgres@localhost:5433/agenticbase")

# #     db = get_session()
    
# #     try:
# #         # First, migrate public schema (tenant registry)
# #         logger.info("Migrating public schema...")
# #         # alembic_cfg = Config("D:/sudheer/new-base-platform-agentiai/agentic-ai-platform-v1.3-complete/backend/alembic.ini")
# #         alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))

# #         alembic_cfg.set_main_option(
# #             "script_location",
# #             str(BACKEND_DIR / "alembic")
# #         )
# #         alembic_cfg.set_main_option("schema", "public")
# #         command.upgrade(alembic_cfg, "head")
# #         logger.info("Public schema migrated successfully")
        
# #         # Get all active tenants
# #         tenants = Tenant.get_all_active(db)
# #         logger.info(f"Found {len(tenants)} active tenants")
        
# #         # Migrate each tenant schema
# #         for tenant in tenants:
# #             logger.info(f"Migrating tenant: {tenant.slug} ({tenant.schema_name})")
            
# #             try:
# #                 # alembic_cfg = Config("D:/sudheer/new-base-platform-agentiai/agentic-ai-platform-v1.3-complete/backend/alembic.ini")
# #                 alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))

# #                 alembic_cfg.set_main_option(
# #                     "script_location",
# #                     str(BACKEND_DIR / "alembic")
# #                 )
# #                 alembic_cfg.set_main_option("schema", tenant.schema_name)
# #                 command.upgrade(alembic_cfg, "head")
# #                 logger.info(f"Successfully migrated: {tenant.slug}")
                
# #             except Exception as e:
# #                 logger.error(f"Failed to migrate {tenant.slug}: {e}")
# #                 continue
        
# #         logger.info("All migrations completed")
        
# #     finally:
# #         db.close()


# # if __name__ == "__main__":
# #     migrate_all_tenants()

# """Script to run migrations for all active tenants"""

# import sys
# import logging
# from pathlib import Path

# # Add backend to path
# sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# from sqlalchemy import text # <--- Import text
# from alembic import command
# from alembic.config import Config
# from app.tenancy.db import init_db, get_session
# from app.tenancy.models import Tenant

# BASE_DIR = Path(__file__).resolve().parent.parent
# BACKEND_DIR = BASE_DIR / "backend"

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# def migrate_all_tenants():
#     """Run migrations for all active tenants"""
    
#     # Initialize database connection
#     # Ensure this matches your actual DB URL
#     init_db("postgresql://postgres:postgres@localhost:5433/agenticbase")

#     db = get_session()
    
#     try:
#         # --- 1. Migrate Public Schema ---
#         logger.info("Migrating public schema...")
        # alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
        # alembic_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
        
#         # Explicitly set schema to public for the first run
#         alembic_cfg.set_main_option("schema", "public") 
#         command.upgrade(alembic_cfg, "head")
#         logger.info("Public schema migrated successfully")
        
#         # --- 2. Get Tenants ---
#         tenants = Tenant.get_all_active(db)
#         logger.info(f"Found {len(tenants)} active tenants")
        
#         # --- 3. Migrate Tenant Schemas ---
#         for tenant in tenants:
#             logger.info(f"Processing tenant: {tenant.slug} ({tenant.schema_name})")
            
#             try:
#                 # ---------------------------------------------------------
#                 # CRITICAL FIX: Create the Schema first!
#                 # ---------------------------------------------------------
#                 # We use the existing db session to create the schema if it's missing.
#                 # Without this, 'SET search_path' ignores the missing schema 
#                 # and defaults to public.
#                 db.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{tenant.schema_name}"'))
#                 db.commit() 
#                 # ---------------------------------------------------------

#                 # Now configure Alembic for this tenant
#                 alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
#                 alembic_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
                
#                 # Pass the schema name to env.py via config
#                 print("tenant schema name",tenant.schema_name)
#                 alembic_cfg.set_main_option("schema", tenant.schema_name)
                
#                 # Run the upgrade
#                 command.upgrade(alembic_cfg, "head")
                
#                 logger.info(f"Successfully migrated: {tenant.slug}")
                
#             except Exception as e:
#                 logger.error(f"Failed to migrate {tenant.slug}: {e}")
#                 # Rollback the session in case the schema creation failed (unlikely but safe)
#                 db.rollback()
#                 continue
        
#         logger.info("All migrations completed")
        
#     finally:
#         db.close()

# if __name__ == "__main__":
#     migrate_all_tenants()


# """
# Improved script to run migrations for all tenant schemas

# This script:
# 1. Runs migrations for public schema (tenant registry)
# 2. Discovers all active tenants
# 3. Runs migrations for each tenant schema
# 4. Provides detailed logging
# """

# import sys
# import logging
# from pathlib import Path

# # Add backend to path
# sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# from sqlalchemy import text
# from alembic import command
# from alembic.config import Config

# from app.tenancy.db import init_db, get_session
# from app.tenancy.models import Tenant, TenantStatus
# # from app.core.config import settings

# BASE_DIR = Path(__file__).resolve().parent.parent
# BACKEND_DIR = BASE_DIR / "backend"
# # Setup logging
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)


# def run_migration_for_schema(schema_name: str) -> bool:
#     """
#     Run migrations for a specific schema
    
#     Args:
#         schema_name: The PostgreSQL schema name
        
#     Returns:
#         True if successful, False otherwise
#     """
#     logger.info(f"{'='*60}")
#     logger.info(f"Running migrations for schema: {schema_name}")
#     logger.info(f"{'='*60}")
    
#     try:
#         # Create Alembic config
#         alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
#         alembic_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
#         # alembic_cfg = Config("alembic.ini")
        
#         # Set the schema in config
#         alembic_cfg.set_main_option("schema", schema_name)
        
#         # Verify the schema option was set
#         verify_schema = alembic_cfg.get_main_option("schema")
#         logger.info(f"Config schema set to: {verify_schema}")
        
#         # Run upgrade
#         command.upgrade(alembic_cfg, "head")
        
#         logger.info(f"✅ Successfully migrated schema: {schema_name}")
#         return True
        
#     except Exception as e:
#         logger.error(f"❌ Failed to migrate schema {schema_name}: {e}")
#         logger.exception("Full traceback:")
#         return False


# def verify_schema_tables(schema_name: str, db_session) -> None:
#     """
#     Verify that tables were created in the correct schema
#     """
#     logger.info(f"\nVerifying tables in schema: {schema_name}")
    
#     query = text("""
#         SELECT table_name 
#         FROM information_schema.tables 
#         WHERE table_schema = :schema
#         ORDER BY table_name
#     """)
    
#     result = db_session.execute(query, {"schema": schema_name})
#     tables = [row[0] for row in result]
    
#     if tables:
#         logger.info(f"✓ Found {len(tables)} tables in {schema_name}:")
#         for table in tables:
#             logger.info(f"  - {table}")
#     else:
#         logger.warning(f"⚠ No tables found in {schema_name}")


# def migrate_all_tenants():
#     """
#     Main function to migrate all tenant schemas
#     """
#     logger.info("="*80)
#     logger.info("MULTI-TENANT DATABASE MIGRATION")
#     logger.info("="*80)
    
#     # Initialize database
#     # logger.info(f"Connecting to database: {settings.DB_URL}")
#     # init_db(settings.DB_URL)
#     init_db("postgresql://postgres:postgres@localhost:5433/agenticbase2")
#     db = get_session()
    
#     try:
#         # Step 1: Migrate public schema (tenant registry)
#         logger.info("\n" + "="*80)
#         logger.info("STEP 1: Migrating PUBLIC schema (tenant registry)")
#         logger.info("="*80)
        
#         success = run_migration_for_schema("public")
        
#         if not success:
#             logger.error("❌ Failed to migrate public schema. Stopping.")
#             return
        
#         # Verify public schema
#         verify_schema_tables("public", db)
        
#         # Step 2: Get all active tenants
#         logger.info("\n" + "="*80)
#         logger.info("STEP 2: Discovering active tenants")
#         logger.info("="*80)
        
#         tenants = db.query(Tenant).filter(
#             Tenant.status == TenantStatus.ACTIVE.value
#         ).all()
        
#         if not tenants:
#             logger.warning("⚠ No active tenants found. Nothing to migrate.")
#             return
        
#         logger.info(f"Found {len(tenants)} active tenant(s):")
#         for tenant in tenants:
#             logger.info(f"  - {tenant.slug} ({tenant.schema_name})")
        
#         # Step 3: Migrate each tenant schema
#         logger.info("\n" + "="*80)
#         logger.info("STEP 3: Migrating tenant schemas")
#         logger.info("="*80)
        
#         successful_migrations = []
#         failed_migrations = []
        
#         for i, tenant in enumerate(tenants, 1):
#             logger.info(f"\n[{i}/{len(tenants)}] Processing tenant: {tenant.slug}")
            
#             # Check if schema exists
#             schema_check = text("""
#                 SELECT EXISTS (
#                     SELECT 1 
#                     FROM information_schema.schemata 
#                     WHERE schema_name = :schema
#                 )
#             """)
            
#             result = db.execute(schema_check, {"schema": tenant.schema_name})
#             schema_exists = result.scalar()
            
#             if not schema_exists:
#                 logger.error(f"❌ Schema {tenant.schema_name} does not exist!")
#                 failed_migrations.append(tenant.slug)
#                 continue
            
#             # Run migration
#             success = run_migration_for_schema(tenant.schema_name)
            
#             if success:
#                 successful_migrations.append(tenant.slug)
#                 # Verify tables were created
#                 verify_schema_tables(tenant.schema_name, db)
#             else:
#                 failed_migrations.append(tenant.slug)
        
#         # Step 4: Summary
#         logger.info("\n" + "="*80)
#         logger.info("MIGRATION SUMMARY")
#         logger.info("="*80)
        
#         logger.info(f"Total tenants: {len(tenants)}")
#         logger.info(f"Successful: {len(successful_migrations)}")
#         logger.info(f"Failed: {len(failed_migrations)}")
        
#         if successful_migrations:
#             logger.info("\n✅ Successfully migrated:")
#             for slug in successful_migrations:
#                 logger.info(f"  - {slug}")
        
#         if failed_migrations:
#             logger.error("\n❌ Failed migrations:")
#             for slug in failed_migrations:
#                 logger.error(f"  - {slug}")
        
#         logger.info("\n" + "="*80)
#         logger.info("MIGRATION COMPLETE")
#         logger.info("="*80)
        
#     except Exception as e:
#         logger.error(f"❌ Critical error during migration: {e}")
#         logger.exception("Full traceback:")
        
#     finally:
#         db.close()


# if __name__ == "__main__":
#     migrate_all_tenants()


"""
Improved script to run migrations for all tenant schemas

This script:
1. Runs migrations for public schema (tenant registry)
2. Discovers all active tenants
3. Runs migrations for each tenant schema
4. Provides detailed logging

FIX: With multiple Alembic heads (e.g. 202501_pub and ff795386972a),
     command.upgrade("head") hangs because the target is ambiguous.
     Solution:
       - Public schema  → upgrade to "heads" (applies ALL heads)
       - Tenant schemas → upgrade to TENANT_HEAD explicitly (ff795386972a)
         This skips public-only branches like 202501_pub that should
         never run inside a tenant schema.
"""

import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import text
from alembic import command
from alembic.config import Config

from app.tenancy.db import init_db, get_session
from app.tenancy.models import Tenant, TenantStatus

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTANT: Update this whenever you add a new tenant-facing migration.
# It must be the revision ID of the latest migration that tenants should run.
# Public-only migration branches (like 202501_pub) are intentionally excluded.
# ─────────────────────────────────────────────────────────────────────────────
TENANT_HEAD = "ff795386972a"   # ← wc_audit_tables (latest tenant migration)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def _make_alembic_cfg(schema_name: str) -> Config:
    """Build an Alembic Config object for the given schema."""
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("schema", schema_name)
    return cfg


def run_migration_for_public() -> bool:
    """
    Migrate the public schema to ALL heads.
    Public has its own branch (202501_pub) plus the shared tenant head,
    so we use 'heads' (plural) to ensure every branch is applied.
    """
    logger.info("=" * 60)
    logger.info("Running migrations for schema: public")
    logger.info("=" * 60)

    try:
        cfg = _make_alembic_cfg("public")
        logger.info("Config schema set to: public")
        command.upgrade(cfg, "heads")   # ← 'heads' applies ALL branch heads
        logger.info("✅ Successfully migrated schema: public")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to migrate public schema: {e}")
        logger.exception("Full traceback:")
        return False


def run_migration_for_tenant(schema_name: str) -> bool:
    """
    Migrate a tenant schema to the explicit TENANT_HEAD revision.
    We never use 'head' / 'heads' for tenants because public-only branches
    (like 202501_pub) must not run inside tenant schemas.
    """
    logger.info("=" * 60)
    logger.info(f"Running migrations for schema: {schema_name}")
    logger.info("=" * 60)

    try:
        cfg = _make_alembic_cfg(schema_name)
        logger.info(f"Config schema set to: {schema_name}")
        logger.info(f"Target revision: {TENANT_HEAD}")
        command.upgrade(cfg, TENANT_HEAD)   # ← explicit tenant head, not "head"
        logger.info(f"✅ Successfully migrated schema: {schema_name}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to migrate schema {schema_name}: {e}")
        logger.exception("Full traceback:")
        return False


def verify_schema_tables(schema_name: str, db_session) -> None:
    """Print all tables found in the given schema."""
    logger.info(f"\nVerifying tables in schema: {schema_name}")

    result = db_session.execute(
        text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = :schema
            ORDER BY table_name
        """),
        {"schema": schema_name},
    )
    tables = [row[0] for row in result]

    if tables:
        logger.info(f"✓ Found {len(tables)} tables in {schema_name}:")
        for t in tables:
            logger.info(f"  - {t}")
    else:
        logger.warning(f"⚠ No tables found in {schema_name}")


def migrate_all_tenants():
    """Main entry point — migrate public then all active tenant schemas."""
    logger.info("=" * 80)
    logger.info("MULTI-TENANT DATABASE MIGRATION")
    logger.info(f"Tenant head revision: {TENANT_HEAD}")
    logger.info("=" * 80)

    init_db("postgresql://postgres:postgres@localhost:5433/agenticbase2")
    db = get_session()

    try:
        # ── Step 1: public schema ──────────────────────────────────────────
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: Migrating PUBLIC schema")
        logger.info("=" * 80)

        if not run_migration_for_public():
            logger.error("❌ Failed to migrate public schema. Stopping.")
            return

        verify_schema_tables("public", db)

        # ── Step 2: discover tenants ───────────────────────────────────────
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: Discovering active tenants")
        logger.info("=" * 80)

        tenants = (
            db.query(Tenant)
            .filter(Tenant.status == TenantStatus.ACTIVE.value)
            .all()
        )

        if not tenants:
            logger.warning("⚠ No active tenants found. Nothing to migrate.")
            return

        logger.info(f"Found {len(tenants)} active tenant(s):")
        for t in tenants:
            logger.info(f"  - {t.slug} ({t.schema_name})")

        # ── Step 3: migrate each tenant ────────────────────────────────────
        logger.info("\n" + "=" * 80)
        logger.info("STEP 3: Migrating tenant schemas")
        logger.info("=" * 80)

        successful, failed = [], []

        for i, tenant in enumerate(tenants, 1):
            logger.info(f"\n[{i}/{len(tenants)}] Processing tenant: {tenant.slug}")

            # Confirm schema exists in DB
            exists = db.execute(
                text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.schemata
                        WHERE schema_name = :schema
                    )
                """),
                {"schema": tenant.schema_name},
            ).scalar()

            if not exists:
                logger.error(f"❌ Schema {tenant.schema_name} does not exist!")
                failed.append(tenant.slug)
                continue

            if run_migration_for_tenant(tenant.schema_name):
                successful.append(tenant.slug)
                verify_schema_tables(tenant.schema_name, db)
            else:
                failed.append(tenant.slug)

        # ── Step 4: summary ────────────────────────────────────────────────
        logger.info("\n" + "=" * 80)
        logger.info("MIGRATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total tenants : {len(tenants)}")
        logger.info(f"Successful    : {len(successful)}")
        logger.info(f"Failed        : {len(failed)}")

        if successful:
            logger.info("\n✅ Successfully migrated:")
            for slug in successful:
                logger.info(f"  - {slug}")

        if failed:
            logger.error("\n❌ Failed migrations:")
            for slug in failed:
                logger.error(f"  - {slug}")

        logger.info("\n" + "=" * 80)
        logger.info("MIGRATION COMPLETE")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"❌ Critical error during migration: {e}")
        logger.exception("Full traceback:")
    finally:
        db.close()


if __name__ == "__main__":
    migrate_all_tenants()