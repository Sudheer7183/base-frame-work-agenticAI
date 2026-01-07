"""
Test if Alembic migrations complete or hang
"""
import sys
from pathlib import Path
import time
import signal

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import create_engine, text, pool
from alembic.config import Config
from alembic import command

DB_URL = "postgresql://postgres:postgres@localhost:5433/agenticbase2"
schema_name = "test_migration_hang2"

print("=" * 60)
print("TESTING IF MIGRATIONS COMPLETE OR HANG")
print("=" * 60)

# Create schema first
print("\n[Step 1] Creating test schema...")
ddl_engine = create_engine(DB_URL, poolclass=pool.NullPool, isolation_level="AUTOCOMMIT")
with ddl_engine.connect() as conn:
    conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
    print(f"✓ Schema created: {schema_name}")
ddl_engine.dispose()

# Set timeout
def timeout_handler(signum, frame):
    print("\n❌ TIMEOUT! Migrations are hanging!")
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)  # 30 second timeout

try:
    print("\n[Step 2] Running migrations...")
    print(f"Start time: {time.time()}")
    
    backend_dir = Path(__file__).parent.parent / "backend"
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    alembic_cfg.set_main_option("schema", schema_name)
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    
    command.upgrade(alembic_cfg, "head")
    
    print(f"End time: {time.time()}")
    print("✅ Migrations completed!")
    
    signal.alarm(0)  # Cancel timeout
    
except Exception as e:
    signal.alarm(0)
    print(f"\n❌ Migration failed: {e}")
    import traceback
    traceback.print_exc()

# Cleanup
print("\n[Step 3] Cleaning up...")
ddl_engine = create_engine(DB_URL, poolclass=pool.NullPool, isolation_level="AUTOCOMMIT")
with ddl_engine.connect() as conn:
    conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
    print(f"✓ Schema dropped: {schema_name}")
ddl_engine.dispose()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)