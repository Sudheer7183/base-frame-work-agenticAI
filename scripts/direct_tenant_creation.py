"""
Test: Create a schema directly and see if it persists
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine, text, pool
import time

DB_URL = "postgresql://postgres:postgres@localhost:5433/agenticbase2"

print("=" * 60)
print("DIRECT SCHEMA CREATION TEST")
print("=" * 60)

# Method 1: Using NullPool + AUTOCOMMIT (same as your code)
print("\n[Test 1] Creating schema with NullPool + AUTOCOMMIT...")
schema_name = "test_direct_schema"

ddl_engine = create_engine(
    DB_URL,
    poolclass=pool.NullPool,
    isolation_level="AUTOCOMMIT"
)

try:
    with ddl_engine.connect() as conn:
        # Create schema
        print(f"Executing: CREATE SCHEMA IF NOT EXISTS \"{schema_name}\"")
        conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        print(f"✓ CREATE SCHEMA executed")
        
        # Verify immediately
        result = conn.execute(
            text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema"),
            {"schema": schema_name}
        )
        if result.fetchone():
            print(f"✅ Schema exists in same connection")
        else:
            print(f"❌ Schema NOT found in same connection")
            
finally:
    ddl_engine.dispose()
    print(f"✓ DDL engine disposed")

# Wait a moment
print("\nWaiting 200ms...")
time.sleep(0.2)

# Verify with new engine
print("\n[Verification] Checking with new engine...")
verify_engine = create_engine(DB_URL)

try:
    with verify_engine.connect() as conn:
        result = conn.execute(
            text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema"),
            {"schema": schema_name}
        )
        if result.fetchone():
            print(f"✅ Schema STILL EXISTS in new connection")
        else:
            print(f"❌ Schema DISAPPEARED in new connection")
            
        # List all schemas
        result = conn.execute(
            text("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'te%' ORDER BY schema_name")
        )
        schemas = [row[0] for row in result]
        print(f"\nAll 'te%' schemas: {schemas}")
        
finally:
    verify_engine.dispose()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
print("\nNow check in psql:")
print(f"  psql {DB_URL} -c \"\\\\dn\"")
print(f"  Should see: {schema_name}")