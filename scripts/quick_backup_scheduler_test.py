#!/usr/bin/env python3
"""
Quick Backup Scheduler Test - Fixed Version
Tests the scheduler with a quick interval for immediate feedback
"""

import sys
import os
from pathlib import Path
import time
from datetime import datetime

# Add backend to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

# Load .env
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from app.core.config import settings
from app.backup.backup_service import DatabaseBackupService

print("=" * 80)
print("QUICK BACKUP SCHEDULER TEST")
print("=" * 80)
print()
print("This test will create backups every 1 minute for 3 minutes")
print("to demonstrate automatic backup functionality.")
print()

# Get backup directory
backup_dir = os.getenv('BACKUP_DIR') or str(PROJECT_ROOT / "backups")

# Initialize backup service
print("Initializing backup service...")
backup_service = DatabaseBackupService(
    db_host=settings.DB_HOST,
    db_port=settings.DB_PORT,
    db_name=settings.DB_NAME,
    db_user=settings.DB_USER,
    db_password=settings.DB_PASSWORD,
    backup_dir=backup_dir,
    retention_days=1,  # Short retention for testing
    max_backups=10
)
print(f"✓ Backup service ready")
print(f"  Directory: {backup_dir}")
print()

# Count initial backups
initial_backups = backup_service.list_backups()
print(f"Initial backup count: {len(initial_backups)}")
print()

# Import APScheduler
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Create scheduler
scheduler = BlockingScheduler()

backup_count = 0
start_time = time.time()

def backup_job():
    """Backup job that runs every minute"""
    global backup_count
    backup_count += 1
    
    elapsed = int(time.time() - start_time)
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ⏰ Backup Job #{backup_count} triggered (after {elapsed}s)")
    print("-" * 80)
    
    try:
        # Create backup
        print("Creating backup...")
        metadata = backup_service.create_full_backup()
        
        print(f"✓ Backup completed!")
        print(f"  ID: {metadata.backup_id}")
        print(f"  Size: {metadata.size_bytes / 1024 / 1024:.2f} MB")
        print(f"  Duration: {metadata.duration_seconds:.2f}s")
        
        # Show current stats
        stats = backup_service.get_backup_stats()
        print(f"  Total backups now: {stats['total_backups']}")
        print()
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        import traceback
        traceback.print_exc()

def cleanup_job():
    """Cleanup job that runs every 2 minutes"""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🧹 Cleanup Job triggered")
    print("-" * 80)
    
    try:
        before_count = len(backup_service.list_backups())
        backup_service._cleanup_old_backups()
        after_count = len(backup_service.list_backups())
        
        deleted = before_count - after_count
        if deleted > 0:
            print(f"✓ Cleaned up {deleted} old backup(s)")
        else:
            print(f"✓ No old backups to clean up")
            print(f"  Current: {after_count} backups")
        print()
        
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")

def status_job():
    """Status check every 30 seconds"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📊 Status: {backup_count} backups created so far...", end='\r')

# Add jobs to scheduler
scheduler.add_job(
    backup_job,
    IntervalTrigger(minutes=1),
    id="test_backup",
    name="Test Backup Job (every 1 min)"
)

scheduler.add_job(
    cleanup_job,
    IntervalTrigger(minutes=2, start_date=datetime.now()),
    id="test_cleanup",
    name="Test Cleanup Job (every 2 min)"
)

scheduler.add_job(
    status_job,
    IntervalTrigger(seconds=30),
    id="test_status",
    name="Status Check (every 30 sec)"
)

# Show configuration
print("=" * 80)
print("SCHEDULER CONFIGURATION")
print("=" * 80)
print()
print("Scheduled Jobs:")
for job in scheduler.get_jobs():
    print(f"  ✓ {job.name}")
print()
print("Test Duration: 3 minutes")
print("Press Ctrl+C to stop early")
print()
print("-" * 80)
print()

# Schedule a shutdown after 3 minutes
def shutdown_scheduler():
    """Shutdown the scheduler after test completes"""
    print(f"\n\n[{datetime.now().strftime('%H:%M:%S')}] ⏱️  Test duration completed (3 minutes)")
    print("-" * 80)
    print()
    scheduler.shutdown()

scheduler.add_job(
    shutdown_scheduler,
    'date',
    run_date=datetime.now().replace(second=0, microsecond=0) + \
             __import__('datetime').timedelta(minutes=3, seconds=10),
    id="shutdown"
)

# Start scheduler
print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Starting scheduler...")
print()

try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    print("\n\n⚠️  Test stopped by user")
    print()

# Final statistics
print()
print("=" * 80)
print("TEST RESULTS")
print("=" * 80)
print()

final_backups = backup_service.list_backups()
new_backups = len(final_backups) - len(initial_backups)

stats = backup_service.get_backup_stats()

print(f"Test Summary:")
print(f"  Duration: ~3 minutes")
print(f"  Backup jobs executed: {backup_count}")
print(f"  New backups created: {new_backups}")
print(f"  Total backups now: {stats['total_backups']}")
print(f"  Total storage: {stats['total_size_mb']:.2f} MB")
print()

if new_backups > 0:
    print("✅ SUCCESS! Scheduler is working correctly!")
    print()
    print("Recent backups:")
    for backup in final_backups[:min(3, len(final_backups))]:
        timestamp = backup.timestamp.strftime('%H:%M:%S')
        print(f"  - {backup.backup_id} ({backup.size_bytes / 1024 / 1024:.2f} MB) at {timestamp}")
else:
    print("⚠️  No new backups were created during the test")
    print("Check the error messages above for issues")

print()
print("=" * 80)
print("PRODUCTION CONFIGURATION")
print("=" * 80)
print()
print("In production, the scheduler runs automatically when you start the app:")
print("  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
print()
print("Schedule settings from .env:")
print(f"  Full backups: {getattr(settings, 'BACKUP_FULL_SCHEDULE', '0 2 * * *')}")
print(f"  (Default: Daily at 2:00 AM)")
print()
print("To test with your app running, change in .env:")
print('  BACKUP_FULL_SCHEDULE="*/5 * * * *"  # Every 5 minutes')
print("Then restart your app")
print()