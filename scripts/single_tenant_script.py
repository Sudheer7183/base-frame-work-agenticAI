"""
Migrate a single tenant schema

Usage:
    python scripts/migrate_single_tenant.py <tenant_slug>
    
Example:
    python scripts/migrate_single_tenant.py demo
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
from app.tenancy.models import Tenant
from app.core.config import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate_tenant(tenant_slug: str):
    """
    Run migrations for a specific tenant
    
    Args:
        tenant_slug: The tenant slug (e.g., 'demo', 'acme')
    """
    logger.info("="*80)
    logger.info(f"MIGRATING TENANT: {tenant_slug}")
    logger.info("="*80)
    
    # Initialize database
    init_db(settings.DB_URL)
    db = get_session()
    
    try:
        # Get tenant
        tenant = db.query(Tenant).filter(Tenant.slug == tenant_slug).first()
        
        if not tenant:
            logger.error(f"❌ Tenant '{tenant_slug}' not found")
            sys.exit(1)
        
        logger.info(f"Found tenant:")
        logger.info(f"  Slug: {tenant.slug}")
        logger.info(f"  Name: {tenant.name}")
        logger.info(f"  Schema: {tenant.schema_name}")
        logger.info(f"  Status: {tenant.status}")
        
        # Check if schema exists
        schema_check = text("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.schemata 
                WHERE schema_name = :schema
            )
        """)
        
        result = db.execute(schema_check, {"schema": tenant.schema_name})
        schema_exists = result.scalar()
        
        if not schema_exists:
            logger.error(f"❌ Schema '{tenant.schema_name}' does not exist!")
            logger.info(f"Create it first using: python scripts/create_tenant.py {tenant_slug}")
            sys.exit(1)
        
        logger.info(f"✓ Schema exists: {tenant.schema_name}")
        
        # Show current search path
        result = db.execute(text("SHOW search_path"))
        current_path = result.scalar()
        logger.info(f"Current search_path: {current_path}")
        
        # Run migration
        logger.info(f"\nRunning migration for schema: {tenant.schema_name}")
        
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("schema", tenant.schema_name)
        
        # Verify config
        verify_schema = alembic_cfg.get_main_option("schema")
        logger.info(f"Alembic config schema: {verify_schema}")
        
        # Run upgrade
        command.upgrade(alembic_cfg, "head")
        
        logger.info(f"✅ Migration completed for {tenant.schema_name}")
        
        # Verify tables were created
        logger.info(f"\nVerifying tables in {tenant.schema_name}:")
        
        query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = :schema
            ORDER BY table_name
        """)
        
        result = db.execute(query, {"schema": tenant.schema_name})
        tables = [row[0] for row in result]
        
        if tables:
            logger.info(f"✓ Found {len(tables)} table(s):")
            for table in tables:
                logger.info(f"  - {table}")
        else:
            logger.warning(f"⚠ No tables found in {tenant.schema_name}")
        
        # Show alembic version
        version_query = text(f"""
            SELECT version_num 
            FROM "{tenant.schema_name}".alembic_version
        """)
        
        try:
            result = db.execute(version_query)
            version = result.scalar()
            logger.info(f"\nCurrent migration version: {version}")
        except:
            logger.info(f"\nNo alembic_version table found (this is normal for first run)")
        
        logger.info("\n" + "="*80)
        logger.info("✅ SUCCESS")
        logger.info("="*80)
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)
        
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/migrate_single_tenant.py <tenant_slug>")
        print("Example: python scripts/migrate_single_tenant.py demo")
        sys.exit(1)
    
    tenant_slug = sys.argv[1]
    migrate_tenant(tenant_slug)