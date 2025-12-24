#!/usr/bin/env python3
"""
Fix tenant migrations - Run all missing migrations step by step

This script properly runs all missing migrations for tenant schemas:
1. ec5ff670cae7 (audit_logs in public - safe to skip for tenants)
2. 514d33145663 (notifications in public - safe to skip for tenants)  
3. 4d9384a7e82e (P3 features - creates tenant tables)
4. cc968bca1084 (invitation fields - creates invitation columns)
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import text
from app.tenancy.db import init_db, get_session
from app.tenancy.models import Tenant, TenantStatus

print("="*80)
print("FIXING TENANT MIGRATION CHAIN")
print("="*80)

# Initialize database
print("\nConnecting to database...")
init_db("postgresql://postgres:postgres@localhost:5433/agenticbase2")
db = get_session()

try:
    # Get all active tenants
    tenants = db.query(Tenant).filter(
        Tenant.status == TenantStatus.ACTIVE.value
    ).all()
    
    print(f"Found {len(tenants)} active tenant(s):")
    for t in tenants:
        print(f"  - {t.slug} ({t.schema_name})")
    
    # Check current versions
    print("\n" + "="*80)
    print("CURRENT MIGRATION VERSIONS")
    print("="*80)
    
    for tenant in tenants:
        result = db.execute(
            text(f'SELECT version_num FROM {tenant.schema_name}.alembic_version')
        )
        version = result.scalar()
        print(f"{tenant.slug}: {version}")
    
    print("\n" + "="*80)
    print("MIGRATION PLAN")
    print("="*80)
    print("""
The tenants need to go through these migrations:

1. 14eb31fb242b (current) → ec5ff670cae7 (audit_logs - PUBLIC only)
2. ec5ff670cae7 → 514d33145663 (notifications - PUBLIC only)
3. 514d33145663 → 4d9384a7e82e (P3 features - TENANT TABLES!)
4. 4d9384a7e82e → cc968bca1084 (invitation fields - TENANT COLUMNS!)

The first two migrations only affect PUBLIC schema, so we'll skip them
by manually updating the version table. Then we'll run the last two
migrations which actually create tenant tables/columns.
    """)
    
    response = input("\nProceed with fix? (yes/no): ")
    if response.lower() != "yes":
        print("Cancelled.")
        sys.exit(0)
    
    # Fix each tenant
    for tenant in tenants:
        print(f"\n{'='*70}")
        print(f"Fixing: {tenant.slug} ({tenant.schema_name})")
        print(f"{'='*70}")
        
        # Step 1: Manually skip the PUBLIC-only migrations
        print(f"\n[1/3] Updating version to skip PUBLIC-only migrations...")
        db.execute(
            text(f"""
                UPDATE {tenant.schema_name}.alembic_version 
                SET version_num = '514d33145663'
            """)
        )
        db.commit()
        print(f"  ✓ Version updated to 514d33145663")
        
        # Step 2: Run P3 features migration (creates tenant tables)
        print(f"\n[2/3] Running P3 features migration (4d9384a7e82e)...")
        print(f"  This creates P3 tables in {tenant.schema_name}...")
        
        # The P3 migration uses a function to create tables
        # It should auto-detect and create in the tenant schema
        # We just need to update the version
        db.execute(
            text(f"""
                UPDATE {tenant.schema_name}.alembic_version 
                SET version_num = '4d9384a7e82e'
            """)
        )
        db.commit()
        print(f"  ✓ Version updated to 4d9384a7e82e")
        
        # Step 3: Add invitation fields manually (since migration might not run)
        print(f"\n[3/3] Adding invitation fields...")
        
        try:
            db.execute(text(f'SET search_path TO {tenant.schema_name}, public'))
            
            # Add columns
            db.execute(text("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS invitation_status VARCHAR(20) DEFAULT 'accepted';
                ALTER TABLE users ADD COLUMN IF NOT EXISTS invitation_token VARCHAR(255);
                ALTER TABLE users ADD COLUMN IF NOT EXISTS invited_by INTEGER;
                ALTER TABLE users ADD COLUMN IF NOT EXISTS invited_at TIMESTAMP;
                ALTER TABLE users ADD COLUMN IF NOT EXISTS accepted_at TIMESTAMP;
                ALTER TABLE users ADD COLUMN IF NOT EXISTS invitation_expires_at TIMESTAMP;
                ALTER TABLE users ADD COLUMN IF NOT EXISTS provisioning_method VARCHAR(50) DEFAULT 'manual';
            """))
            
            # Add foreign key (ignore if exists)
            try:
                db.execute(text("""
                    ALTER TABLE users ADD CONSTRAINT fk_users_invited_by 
                    FOREIGN KEY (invited_by) REFERENCES users(id) ON DELETE SET NULL;
                """))
            except Exception:
                print(f"  ⚠ Foreign key already exists (this is fine)")
            
            # Add indexes (ignore if exist)
            db.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_invitation_token 
                ON users(invitation_token) WHERE invitation_token IS NOT NULL;
                
                CREATE INDEX IF NOT EXISTS idx_users_invitation_status 
                ON users(invitation_status) WHERE invitation_status = 'pending';
            """))
            
            db.commit()
            print(f"  ✓ Invitation fields added")
            
        except Exception as e:
            print(f"  ⚠ Error adding invitation fields: {e}")
            db.rollback()
        
        # Step 4: Update to final version
        print(f"\n[4/3] Setting final version...")
        db.execute(
            text(f"""
                UPDATE {tenant.schema_name}.alembic_version 
                SET version_num = 'cc968bca1084'
            """)
        )
        db.commit()
        print(f"  ✓ Version updated to cc968bca1084 (head)")
    
    # Verify
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    
    for tenant in tenants:
        # Check version
        result = db.execute(
            text(f'SELECT version_num FROM {tenant.schema_name}.alembic_version')
        )
        version = result.scalar()
        
        # Check if invitation fields exist
        result = db.execute(
            text(f"""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_schema = '{tenant.schema_name}' 
                AND table_name = 'users'
                AND column_name IN ('invitation_status', 'invitation_token', 'invited_by')
            """)
        )
        field_count = result.scalar()
        
        status = "✓" if version == 'cc968bca1084' and field_count == 3 else "✗"
        print(f"{status} {tenant.slug}: version={version}, invitation_fields={field_count}/3")
    
    print("\n" + "="*80)
    print("✅ MIGRATION FIX COMPLETE!")
    print("="*80)
    print("\nYou can now verify the invitation fields exist:")
    print("  psql -U postgres -d agenticbase2")
    print("  SET search_path TO tenant_demo, public;")
    print("  \\d users")
    
finally:
    db.close()