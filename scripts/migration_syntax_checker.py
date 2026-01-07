#!/usr/bin/env python3
"""
Test each migration file individually to find syntax/import errors
"""

import sys
from pathlib import Path
import importlib.util

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# List of migration files to test
migration_files = [
    "c1d684656a7d_initial_schema.py",
    "a93ad6fadec3_add_tenant_schema_tables.py",
    "14eb31fb242b_add_audit_logs_table.py",
    "514d33145663_add_notifications_table.py",
    "4d9384a7e82e_p3_features.py",
    "cc968bca1084_add_invitation_fields.py",
    "202501_pub_4e59fcf96752_add_agent_builder_module.py",  # This might be wrong
    "c054fec142af_202502_tenant_specific_tables.py",
    "57ec5ea850a8_computational_audit_tables.py",
]

versions_dir = backend_dir / "alembic" / "versions"

print("=" * 70)
print("TESTING MIGRATION FILES FOR SYNTAX/IMPORT ERRORS")
print("=" * 70)

# First, list actual files
print("\nActual files in versions directory:")
actual_files = sorted([f.name for f in versions_dir.glob("*.py") if f.name != "__pycache__"])
for f in actual_files:
    print(f"  - {f}")

print("\n" + "=" * 70)
print("TESTING EACH FILE")
print("=" * 70)

failed_files = []

for filename in actual_files:
    filepath = versions_dir / filename
    
    print(f"\nTesting: {filename}")
    print("-" * 70)
    
    try:
        # Try to compile the file
        with open(filepath, 'r') as f:
            code = f.read()
        
        compile(code, str(filepath), 'exec')
        print(f"  ✓ Syntax OK")
        
        # Try to import it
        spec = importlib.util.spec_from_file_location(filename[:-3], filepath)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"  ✓ Import OK")
        
        # Check for required functions
        if hasattr(module, 'upgrade'):
            print(f"  ✓ upgrade() function exists")
        else:
            print(f"  ⚠ WARNING: No upgrade() function found")
        
        if hasattr(module, 'downgrade'):
            print(f"  ✓ downgrade() function exists")
        else:
            print(f"  ⚠ WARNING: No downgrade() function found")
        
        print(f"  ✅ {filename} - ALL CHECKS PASSED")
        
    except SyntaxError as e:
        print(f"  ❌ SYNTAX ERROR at line {e.lineno}: {e.msg}")
        print(f"     {e.text}")
        failed_files.append((filename, f"Syntax error: {e.msg}"))
        
    except ImportError as e:
        print(f"  ❌ IMPORT ERROR: {e}")
        failed_files.append((filename, f"Import error: {e}"))
        
    except NameError as e:
        print(f"  ❌ NAME ERROR: {e}")
        failed_files.append((filename, f"Name error: {e}"))
        
    except Exception as e:
        print(f"  ❌ ERROR: {type(e).__name__}: {e}")
        failed_files.append((filename, f"{type(e).__name__}: {e}"))

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

if failed_files:
    print(f"\n❌ {len(failed_files)} file(s) failed:")
    for filename, error in failed_files:
        print(f"  - {filename}")
        print(f"    Error: {error}")
    print("\nFIX THESE FILES FIRST!")
else:
    print("\n✅ All migration files are syntactically correct!")
    print("\nIf migrations still hang, the issue is likely in:")
    print("  1. Alembic configuration (alembic.ini or env.py)")
    print("  2. Database connection")
    print("  3. Runtime logic inside upgrade() functions")

sys.exit(1 if failed_files else 0)