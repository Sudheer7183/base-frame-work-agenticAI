#!/usr/bin/env python3
"""
Complete database reset - drops all schemas and recreates from scratch
DANGER: This will delete ALL data!
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_URL = "postgresql://postgres:postgres@localhost:5433/agenticbase"

def reset_database():
    """Drop and recreate all schemas"""
    
    engine = create_engine(DB_URL, isolation_level="AUTOCOMMIT")
    
    logger.info("🗑️  Dropping all schemas...")
    
    with engine.connect() as conn:
        # 1. Get all tenant schemas
        result = conn.execute(text("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name LIKE 'tenant_%'
        """))
        tenant_schemas = [row[0] for row in result]
        
        # 2. Drop all tenant schemas
        for schema in tenant_schemas:
            logger.info(f"  Dropping schema: {schema}")
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
        
        # 3. Drop all tables in public schema (except system tables)
        logger.info("  Dropping public schema tables...")
        conn.execute(text("""
            DROP TABLE IF EXISTS public.agent_execution_logs CASCADE;
            DROP TABLE IF EXISTS public.hitl_records CASCADE;
            DROP TABLE IF EXISTS public.agents CASCADE;
            DROP TABLE IF EXISTS public.users CASCADE;
            DROP TABLE IF EXISTS public.tenants CASCADE;
            DROP TABLE IF EXISTS public.alembic_version CASCADE;
        """))
        
        # 4. Drop any sequences
        result = conn.execute(text("""
            SELECT sequence_name 
            FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
        """))
        sequences = [row[0] for row in result]
        for seq in sequences:
            logger.info(f"  Dropping sequence: {seq}")
            conn.execute(text(f'DROP SEQUENCE IF EXISTS public."{seq}" CASCADE'))
    
    logger.info("✅ Database reset complete!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. cd backend")
    logger.info("2. alembic revision --autogenerate -m 'initial_schema'")
    logger.info("3. alembic upgrade head")
    logger.info("4. python ../scripts/create_tenant.py demo 'Demo Tenant'")


if __name__ == "__main__":
    print("⚠️  WARNING: This will DELETE ALL DATA in the database!")
    print(f"Database: {DB_URL}")
    response = input("\nType 'DELETE ALL DATA' to continue: ")
    
    if response == "DELETE ALL DATA":
        reset_database()
    else:
        print("❌ Cancelled")
        sys.exit(1)