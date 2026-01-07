#!/usr/bin/env python3
"""
Diagnostic script to identify why Alembic is hanging
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic.script import ScriptDirectory
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database URL
DB_URL = "postgresql://postgres:postgres@localhost:5433/agenticbase2"

def check_database_state():
    """Check current database state"""
    engine = create_engine(DB_URL)
    
    with engine.connect() as conn:
        logger.info("=" * 60)
        logger.info("1. CHECKING PUBLIC SCHEMA")
        logger.info("=" * 60)
        
        # Check if public.alembic_version exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'alembic_version'
            )
        """))
        public_has_version = result.scalar()
        logger.info(f"Public alembic_version exists: {public_has_version}")
        
        if public_has_version:
            result = conn.execute(text("SELECT version_num FROM public.alembic_version"))
            version = result.scalar()
            logger.info(f"Public at version: {version}")
        
        logger.info("\n" + "=" * 60)
        logger.info("2. CHECKING TENANT SCHEMAS")
        logger.info("=" * 60)
        
        # List all tenant schemas
        result = conn.execute(text("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name LIKE 'tenant_%'
            ORDER BY schema_name
        """))
        
        tenant_schemas = [row[0] for row in result]
        logger.info(f"Found {len(tenant_schemas)} tenant schemas:")
        for schema in tenant_schemas:
            logger.info(f"  - {schema}")
            
            # Check if this schema has alembic_version
            result = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = :schema
                    AND table_name = 'alembic_version'
                )
            """), {"schema": schema})
            has_version = result.scalar()
            
            if has_version:
                result = conn.execute(text(f"""
                    SELECT version_num FROM "{schema}".alembic_version
                """))
                version = result.scalar()
                logger.info(f"    Version: {version}")
            else:
                logger.info(f"    Version: [NONE - no alembic_version table]")


def check_migration_files():
    """Check Alembic migration files"""
    logger.info("\n" + "=" * 60)
    logger.info("3. CHECKING MIGRATION FILES")
    logger.info("=" * 60)
    
    backend_dir = Path(__file__).parent.parent / "backend"
    alembic_ini = backend_dir / "alembic.ini"
    
    if not alembic_ini.exists():
        logger.error(f"❌ alembic.ini not found at {alembic_ini}")
        return
    
    logger.info(f"✓ Found alembic.ini at {alembic_ini}")
    
    # Load Alembic config
    config = Config(str(alembic_ini))
    script = ScriptDirectory.from_config(config)
    
    # Get all revisions
    try:
        revisions = list(script.walk_revisions())
        logger.info(f"✓ Found {len(revisions)} migration files")
        
        logger.info("\nMigration chain:")
        for rev in reversed(revisions):
            logger.info(f"  {rev.revision[:12]} -> {rev.down_revision or 'HEAD'}: {rev.doc}")
        
        # Check for circular dependencies
        logger.info("\n" + "=" * 60)
        logger.info("4. CHECKING FOR CIRCULAR DEPENDENCIES")
        logger.info("=" * 60)
        
        revision_map = {}
        for rev in revisions:
            revision_map[rev.revision] = rev.down_revision
        
        visited = set()
        for rev in revisions:
            current = rev.revision
            path = [current]
            
            while current in revision_map and revision_map[current]:
                current = revision_map[current]
                if current in path:
                    logger.error(f"❌ CIRCULAR DEPENDENCY DETECTED: {' -> '.join(path + [current])}")
                    return
                path.append(current)
            
            visited.add(rev.revision)
        
        logger.info("✓ No circular dependencies found")
        
    except Exception as e:
        logger.error(f"❌ Error reading migration files: {e}")
        logger.exception("Full traceback:")


def check_specific_schema(schema_name: str):
    """Check what migrations need to run for a specific schema"""
    logger.info("\n" + "=" * 60)
    logger.info(f"5. CHECKING SCHEMA: {schema_name}")
    logger.info("=" * 60)
    
    engine = create_engine(DB_URL)
    
    with engine.connect() as conn:
        # Check if schema exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.schemata 
                WHERE schema_name = :schema
            )
        """), {"schema": schema_name})
        
        if not result.scalar():
            logger.error(f"❌ Schema {schema_name} does not exist")
            return
        
        logger.info(f"✓ Schema {schema_name} exists")
        
        # Check for alembic_version table
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = :schema
                AND table_name = 'alembic_version'
            )
        """), {"schema": schema_name})
        
        has_version = result.scalar()
        
        if has_version:
            result = conn.execute(text(f"""
                SELECT version_num FROM "{schema_name}".alembic_version
            """))
            current_version = result.scalar()
            logger.info(f"Current version: {current_version}")
        else:
            logger.info("No alembic_version table - this is a fresh schema")
            logger.info("Alembic will try to run ALL migrations from scratch")
            
            # Check what tables exist
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = :schema
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """), {"schema": schema_name})
            
            tables = [row[0] for row in result]
            if tables:
                logger.warning(f"⚠️  Schema has {len(tables)} tables but no alembic_version:")
                for table in tables:
                    logger.warning(f"    - {table}")
                logger.warning("This will cause migration conflicts!")
            else:
                logger.info("✓ Schema is empty - migrations can proceed cleanly")


def main():
    """Run all diagnostics"""
    logger.info("╔" + "═" * 58 + "╗")
    logger.info("║" + " " * 15 + "MIGRATION DIAGNOSTIC TOOL" + " " * 18 + "║")
    logger.info("╚" + "═" * 58 + "╝")
    
    try:
        check_database_state()
        check_migration_files()
        
        # Check specific problematic schema
        check_specific_schema("tenant_testingtesnant2")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ DIAGNOSTIC COMPLETE")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n❌ DIAGNOSTIC FAILED: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)


if __name__ == "__main__":
    main()