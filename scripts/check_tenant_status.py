"""
Check which database we're actually connected to during operations
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine, text

# Test both databases
databases = [
    "postgresql://postgres:postgres@localhost:5433/agenticbase",
    "postgresql://postgres:postgres@localhost:5433/agenticbase2"
]

for db_url in databases:
    print("=" * 60)
    print(f"Checking database: {db_url.split('/')[-1]}")
    print("=" * 60)
    
    try:
        engine = create_engine(db_url)
        conn = engine.connect()
        
        try:
            # Get current database
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"Connected to: {db_name}")
            
            # List schemas
            result = conn.execute(text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name LIKE 'tenant_%'
                ORDER BY schema_name
            """))
            schemas = [row[0] for row in result]
            print(f"\nTenant schemas ({len(schemas)}):")
            for schema in schemas:
                print(f"  - {schema}")
            
            # List tenants in public.tenants
            try:
                result = conn.execute(text("""
                    SELECT slug, schema_name, status 
                    FROM public.tenants 
                    ORDER BY created_at
                """))
                tenants = result.fetchall()
                print(f"\nTenant records ({len(tenants)}):")
                for t in tenants:
                    print(f"  - {t[0]}: {t[1]} (status: {t[2]})")
            except Exception as e:
                print(f"\n⚠️  No tenants table or error: {e}")
                
        finally:
            conn.close()
            engine.dispose()
            
    except Exception as e:
        print(f"❌ Could not connect: {e}")
    
    print()