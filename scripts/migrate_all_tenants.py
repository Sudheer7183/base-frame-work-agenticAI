"""Script to run migrations for all active tenants"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy.orm import Session
from alembic import command
from alembic.config import Config
from app.tenancy.db import init_db, get_session
from app.tenancy.models import Tenant, TenantStatus
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_all_tenants():
    """Run migrations for all active tenants"""
    
    # Initialize database
    init_db(settings.DATABASE_URL)
    db = get_session()
    
    try:
        # First, migrate public schema (tenant registry)
        logger.info("Migrating public schema...")
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("schema", "public")
        command.upgrade(alembic_cfg, "head")
        logger.info("Public schema migrated successfully")
        
        # Get all active tenants
        tenants = Tenant.get_all_active(db)
        logger.info(f"Found {len(tenants)} active tenants")
        
        # Migrate each tenant schema
        for tenant in tenants:
            logger.info(f"Migrating tenant: {tenant.slug} ({tenant.schema_name})")
            
            try:
                alembic_cfg = Config("alembic.ini")
                alembic_cfg.set_main_option("schema", tenant.schema_name)
                command.upgrade(alembic_cfg, "head")
                logger.info(f"Successfully migrated: {tenant.slug}")
                
            except Exception as e:
                logger.error(f"Failed to migrate {tenant.slug}: {e}")
                continue
        
        logger.info("All migrations completed")
        
    finally:
        db.close()


if __name__ == "__main__":
    migrate_all_tenants()
