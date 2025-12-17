#!/usr/bin/env python3
"""
Reset Alembic migrations to a clean state
Run from project root: python scripts/reset_migrations.py
"""

import sys
from pathlib import Path
from sqlalchemy import create_engine, text
import shutil
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

DB_URL = "postgresql://postgres:postgres@localhost:5433/agenticbase"

def reset_migrations():
    """Reset migrations to clean state"""
    
    backend_dir = Path(__file__).parent.parent / "backend"
    versions_dir = backend_dir / "alembic" / "versions"
    
    print("🔄 Resetting Alembic migrations...")
    
    # 1. Backup existing migrations
    backup_dir = backend_dir.parent / "migrations_backup" / datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📦 Backing up to: {backup_dir}")
    for file in versions_dir.glob("*.py"):
        if file.name != "__pycache__":
            shutil.copy2(file, backup_dir)
    
    # 2. Drop alembic_version table
    print("🗑️  Dropping alembic_version table...")
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS public.alembic_version CASCADE"))
        conn.commit()
    
    # 3. Delete all migration files
    print("🗑️  Removing migration files...")
    for file in versions_dir.glob("*.py"):
        if file.name != "__pycache__":
            file.unlink()
    
    # 4. Create new initial migration
    print("📝 Creating fresh initial migration...")
    print("\nNext steps:")
    print("1. cd backend")
    print("2. alembic revision --autogenerate -m 'initial_schema'")
    print("3. alembic upgrade head")
    print("4. python ../scripts/create_tenant.py test 'Test Tenant'")
    
    print("\n✅ Reset complete!")

if __name__ == "__main__":
    response = input("⚠️  This will DELETE all migrations and reset Alembic. Continue? (yes/no): ")
    if response.lower() == "yes":
        reset_migrations()
    else:
        print("❌ Cancelled")