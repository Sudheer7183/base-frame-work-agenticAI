#!/usr/bin/env python3
"""
Database Backup CLI Tool
Manual backup operations from command line

Usage:
    python backup_cli.py create --type full
    python backup_cli.py create --type tenant --schema tenant_acme
    python backup_cli.py list
    python backup_cli.py restore --backup-id full_20250101_020000
    python backup_cli.py verify --backup-id full_20250101_020000
    python backup_cli.py delete --backup-id full_20250101_020000
    python backup_cli.py stats
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add backend to path
# sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


from app.core.config import settings
from app.backup.backup_service import (
    DatabaseBackupService,
    BackupType,
    BackupStatus
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_backup_service() -> DatabaseBackupService:
    """Initialize backup service"""
    return DatabaseBackupService(
        db_host=settings.DB_HOST,
        db_port=settings.DB_PORT,
        db_name=settings.DB_NAME,
        db_user=settings.DB_USER,
        db_password=settings.DB_PASSWORD,
        backup_dir=getattr(settings, 'BACKUP_DIR', 'D:/sudheer/new-base-platform-agentiai/backups'),
        retention_days=getattr(settings, 'BACKUP_RETENTION_DAYS', 30),
        max_backups=getattr(settings, 'BACKUP_MAX_COUNT', 50)
    )


def cmd_create(args):
    """Create a backup"""
    service = get_backup_service()
    
    try:
        if args.type == 'full':
            logger.info("Creating full database backup...")
            metadata = service.create_full_backup()
            
        elif args.type == 'tenant':
            if not args.schema:
                logger.error("--schema required for tenant backups")
                sys.exit(1)
            
            logger.info(f"Creating tenant backup: {args.schema}")
            metadata = service.create_tenant_backup(args.schema)
            
        else:
            logger.error(f"Unknown backup type: {args.type}")
            sys.exit(1)
        
        logger.info(f"✓ Backup created successfully")
        logger.info(f"  ID: {metadata.backup_id}")
        logger.info(f"  Size: {metadata.size_bytes / 1024 / 1024:.2f} MB")
        logger.info(f"  Duration: {metadata.duration_seconds:.2f}s")
        logger.info(f"  Path: {metadata.file_path}")
        
    except Exception as e:
        logger.error(f"✗ Backup failed: {e}")
        sys.exit(1)


def cmd_list(args):
    """List backups"""
    service = get_backup_service()
    
    backup_type = BackupType(args.type) if args.type else None
    backups = service.list_backups(
        backup_type=backup_type,
        schema=args.schema,
        limit=args.limit
    )
    
    if not backups:
        logger.info("No backups found")
        return
    
    logger.info(f"Found {len(backups)} backup(s):\n")
    
    # Print table header
    print(f"{'Backup ID':<40} {'Type':<10} {'Status':<12} {'Size (MB)':<12} {'Timestamp':<20}")
    print("-" * 100)
    
    # Print backups
    for backup in backups:
        size_mb = backup.size_bytes / 1024 / 1024
        timestamp = backup.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        print(
            f"{backup.backup_id:<40} "
            f"{backup.backup_type.value:<10} "
            f"{backup.status.value:<12} "
            f"{size_mb:<12.2f} "
            f"{timestamp:<20}"
        )
        
        if args.verbose and backup.schemas and backup.schemas[0] != "*":
            print(f"  Schemas: {', '.join(backup.schemas)}")
        
        if backup.error_message:
            print(f"  Error: {backup.error_message}")
        
        print()


def cmd_restore(args):
    """Restore a backup"""
    service = get_backup_service()
    
    if not args.confirm:
        logger.warning("⚠️  WARNING: This will restore the database!")
        logger.warning("   Use --confirm to proceed")
        sys.exit(1)
    
    try:
        logger.info(f"Restoring backup: {args.backup_id}")
        
        service.restore_backup(
            backup_id=args.backup_id,
            target_schema=args.target_schema,
            clean=args.clean
        )
        
        logger.info("✓ Restore completed successfully")
        
    except Exception as e:
        logger.error(f"✗ Restore failed: {e}")
        sys.exit(1)


def cmd_verify(args):
    """Verify a backup"""
    service = get_backup_service()
    
    try:
        logger.info(f"Verifying backup: {args.backup_id}")
        
        is_valid = service.verify_backup(args.backup_id)
        
        if is_valid:
            logger.info("✓ Backup is valid")
        else:
            logger.error("✗ Backup verification failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"✗ Verification failed: {e}")
        sys.exit(1)


def cmd_delete(args):
    """Delete a backup"""
    service = get_backup_service()
    
    if not args.confirm:
        logger.warning("⚠️  WARNING: This will permanently delete the backup!")
        logger.warning("   Use --confirm to proceed")
        sys.exit(1)
    
    try:
        logger.info(f"Deleting backup: {args.backup_id}")
        
        service.delete_backup(args.backup_id)
        
        logger.info("✓ Backup deleted successfully")
        
    except Exception as e:
        logger.error(f"✗ Deletion failed: {e}")
        sys.exit(1)


def cmd_stats(args):
    """Show backup statistics"""
    service = get_backup_service()
    
    try:
        stats = service.get_backup_stats()
        
        logger.info("Backup Statistics:\n")
        print(f"Total Backups:     {stats['total_backups']}")
        print(f"Completed:         {stats['completed_backups']}")
        print(f"Failed:            {stats['failed_backups']}")
        print(f"Total Size:        {stats['total_size_mb']:.2f} MB")
        print(f"Oldest Backup:     {stats['oldest_backup'] or 'N/A'}")
        print(f"Newest Backup:     {stats['newest_backup'] or 'N/A'}")
        print(f"Retention Policy:  {stats['retention_days']} days")
        print(f"Max Backups:       {stats['max_backups']}")
        
    except Exception as e:
        logger.error(f"✗ Failed to get stats: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Database Backup CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a backup')
    create_parser.add_argument(
        '--type',
        choices=['full', 'tenant'],
        required=True,
        help='Backup type'
    )
    create_parser.add_argument(
        '--schema',
        help='Schema name (required for tenant backups)'
    )
    
    # List command
    list_parser = subparsers.add_parser('list', help='List backups')
    list_parser.add_argument(
        '--type',
        choices=['full', 'tenant', 'public'],
        help='Filter by backup type'
    )
    list_parser.add_argument(
        '--schema',
        help='Filter by schema name'
    )
    list_parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Maximum results (default: 50)'
    )
    list_parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Show detailed information'
    )
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore a backup')
    restore_parser.add_argument(
        '--backup-id',
        required=True,
        help='Backup ID to restore'
    )
    restore_parser.add_argument(
        '--target-schema',
        help='Target schema (for tenant backups)'
    )
    restore_parser.add_argument(
        '--clean',
        action='store_true',
        help='Drop existing objects first'
    )
    restore_parser.add_argument(
        '--confirm',
        action='store_true',
        help='Confirm restoration'
    )
    
    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify a backup')
    verify_parser.add_argument(
        '--backup-id',
        required=True,
        help='Backup ID to verify'
    )
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a backup')
    delete_parser.add_argument(
        '--backup-id',
        required=True,
        help='Backup ID to delete'
    )
    delete_parser.add_argument(
        '--confirm',
        action='store_true',
        help='Confirm deletion'
    )
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show backup statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    commands = {
        'create': cmd_create,
        'list': cmd_list,
        'restore': cmd_restore,
        'verify': cmd_verify,
        'delete': cmd_delete,
        'stats': cmd_stats
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
