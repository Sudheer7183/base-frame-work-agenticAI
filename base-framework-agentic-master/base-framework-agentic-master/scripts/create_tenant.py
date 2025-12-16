"""Script to create a new tenant from command line"""

import sys
from pathlib import Path
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.tenancy.db import init_db, get_session
from app.tenancy.service import TenantService
# from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_tenant(slug: str, name: str, email: str = None):
    """Create a new tenant"""
    
    # Initialize database
    # init_db(settings.TEST_DB_URL)
    init_db("postgresql://postgres:postgres@localhost:5433/agenticbase")
    db = get_session()
    
    try:
        service = TenantService(db)
        
        logger.info(f"Creating tenant: {slug}")
        tenant = service.create_tenant(
            slug=slug,
            name=name,
            admin_email=email
        )
        
        logger.info(f"Tenant created successfully!")
        logger.info(f"  Slug: {tenant.slug}")
        logger.info(f"  Schema: {tenant.schema_name}")
        logger.info(f"  Status: {tenant.status}")
        
    except Exception as e:
        logger.error(f"Failed to create tenant: {e}")
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new tenant")
    parser.add_argument("slug", help="Tenant slug (unique identifier)")
    parser.add_argument("name", help="Tenant display name")
    parser.add_argument("--email", help="Admin email address")
    
    args = parser.parse_args()
    create_tenant(args.slug, args.name, args.email)