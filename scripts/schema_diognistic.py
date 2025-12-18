"""
Schema diagnostics tool

Helps debug multi-tenant schema issues by showing:
- All schemas in the database
- Tables in each schema
- Alembic version for each schema
- Tenant registry information
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import text
from app.tenancy.db import init_db, get_session
from app.tenancy.models import Tenant
# from app.core.config import settings


def print_section(title):
    """Print a section header"""
    print("\n" + "="*80)
    print(title)
    print("="*80)


def show_all_schemas(db):
    """Show all schemas in the database"""
    print_section("ALL SCHEMAS IN DATABASE")
    
    query = text("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY schema_name
    """)
    
    result = db.execute(query)
    schemas = [row[0] for row in result]
    
    print(f"Found {len(schemas)} schema(s):")
    for schema in schemas:
        print(f"  - {schema}")
    
    return schemas


def show_schema_tables(db, schema_name):
    """Show all tables in a specific schema"""
    print(f"\nTables in schema '{schema_name}':")
    
    query = text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = :schema
        ORDER BY table_name
    """)
    
    result = db.execute(query, {"schema": schema_name})
    tables = [row[0] for row in result]
    
    if tables:
        print(f"  Found {len(tables)} table(s):")
        for table in tables:
            # Get row count
            try:
                count_query = text(f'SELECT COUNT(*) FROM "{schema_name}"."{table}"')
                count_result = db.execute(count_query)
                count = count_result.scalar()
                print(f"    - {table} ({count} rows)")
            except:
                print(f"    - {table}")
    else:
        print(f"  ⚠ No tables found")


def show_alembic_version(db, schema_name):
    """Show alembic version for a schema"""
    try:
        query = text(f'SELECT version_num FROM "{schema_name}".alembic_version')
        result = db.execute(query)
        version = result.scalar()
        
        if version:
            print(f"  Alembic version: {version}")
        else:
            print(f"  Alembic version: (none)")
    except Exception as e:
        print(f"  Alembic version: Not initialized")


def show_tenants(db):
    """Show all tenants from registry"""
    print_section("TENANT REGISTRY")
    
    try:
        tenants = db.query(Tenant).all()
        
        if not tenants:
            print("⚠ No tenants found in registry")
            return
        
        print(f"Found {len(tenants)} tenant(s):\n")
        
        for tenant in tenants:
            print(f"Slug: {tenant.slug}")
            print(f"  Name: {tenant.name}")
            print(f"  Schema: {tenant.schema_name}")
            print(f"  Status: {tenant.status}")
            print(f"  Created: {tenant.created_at}")
            
            # Check if schema exists
            check_query = text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.schemata 
                    WHERE schema_name = :schema
                )
            """)
            result = db.execute(check_query, {"schema": tenant.schema_name})
            exists = result.scalar()
            
            if exists:
                print(f"  Schema exists: ✓")
            else:
                print(f"  Schema exists: ✗ (ERROR: Schema missing!)")
            
            print()
            
    except Exception as e:
        print(f"❌ Error reading tenant registry: {e}")


def check_search_path(db):
    """Show current search path"""
    print_section("CURRENT DATABASE CONFIGURATION")
    
    result = db.execute(text("SHOW search_path"))
    search_path = result.scalar()
    print(f"Search path: {search_path}")
    
    result = db.execute(text("SELECT current_database()"))
    database = result.scalar()
    print(f"Database: {database}")
    
    result = db.execute(text("SELECT current_user"))
    user = result.scalar()
    print(f"User: {user}")


def run_diagnostics():
    """Run full diagnostics"""
    print("="*80)
    print("MULTI-TENANT SCHEMA DIAGNOSTICS")
    print("="*80)
    
    # Initialize database
    # init_db(settings.DB_URL)
    init_db("postgresql://postgres:postgres@localhost:5433/agenticbase2")
    db = get_session()
    
    try:
        # Show database config
        check_search_path(db)
        
        # Show all schemas
        schemas = show_all_schemas(db)
        
        # Show tenant registry
        show_tenants(db)
        
        # Show details for each schema
        print_section("DETAILED SCHEMA INFORMATION")
        
        for schema in schemas:
            print(f"\nSchema: {schema}")
            print("-" * 40)
            show_schema_tables(db, schema)
            show_alembic_version(db, schema)
        
        print("\n" + "="*80)
        print("DIAGNOSTICS COMPLETE")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error during diagnostics: {e}")
        raise
        
    finally:
        db.close()


if __name__ == "__main__":
    run_diagnostics()