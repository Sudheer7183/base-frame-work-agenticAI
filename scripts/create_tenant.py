"""Script to create a new tenant from command line - FIXED VERSION"""

import sys
from pathlib import Path
import argparse
import logging

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.tenancy.db import init_db, get_session
from app.tenancy.service import TenantService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tenant(slug: str, name: str, email: str = None):
    """Create a new tenant with proper transaction handling"""
    
    init_db("postgresql://postgres:postgres@localhost:5433/agenticbase2")
    db = get_session()

    try:
        service = TenantService(db)

        logger.info(f"Creating tenant: {slug}")
        
        # CRITICAL: The service handles its own commits
        # Don't interfere with the transaction
        tenant = service.create_tenant(
            slug=slug,
            name=name,
            admin_email=email
        )

        # After service completes, tenant is already committed
        # Just log the result
        logger.info("=" * 60)
        logger.info("✅ TENANT CREATED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info(f"Slug   : {tenant.slug}")
        logger.info(f"Schema : {tenant.schema_name}")
        logger.info(f"Status : {tenant.status}")
        logger.info(f"Name   : {tenant.name}")
        
        # CRITICAL FIX: Explicitly commit any pending changes in this session
        # This ensures the session is clean before closing
        db.commit()
        
        return tenant

    except Exception as e:
        logger.error("=" * 60)
        logger.error("❌ TENANT CREATION FAILED")
        logger.error("=" * 60)
        logger.exception("Error details:")
        
        # Rollback this session's transaction
        db.rollback()
        sys.exit(1)
        
    finally:
        # Close the session
        db.close()
        logger.info("Database session closed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new tenant")
    parser.add_argument("slug", help="Tenant slug (unique identifier)")
    parser.add_argument("name", help="Tenant display name")
    parser.add_argument("--email", help="Admin email address")

    args = parser.parse_args()
    create_tenant(args.slug, args.name, args.email)