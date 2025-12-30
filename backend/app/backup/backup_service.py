"""
Database Backup Service for Multi-Tenant Agentic AI Platform
Supports automated backups, restoration, and backup management
"""

import os
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict
import json
import shutil
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class BackupStatus(str, Enum):
    """Backup status enum"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class BackupType(str, Enum):
    """Backup type enum"""
    FULL = "full"  # All schemas including public
    TENANT = "tenant"  # Single tenant schema
    PUBLIC = "public"  # Only public schema (tenant registry)


@dataclass
class BackupMetadata:
    """Backup metadata for tracking"""
    backup_id: str
    backup_type: BackupType
    timestamp: datetime
    status: BackupStatus
    schemas: List[str]
    size_bytes: int
    file_path: str
    error_message: Optional[str] = None
    duration_seconds: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['backup_type'] = self.backup_type.value
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BackupMetadata':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['backup_type'] = BackupType(data['backup_type'])
        data['status'] = BackupStatus(data['status'])
        return cls(**data)


class DatabaseBackupService:
    """
    Database backup service for multi-tenant PostgreSQL
    
    Features:
    - Full database backups (all schemas)
    - Individual tenant schema backups
    - Automated backup scheduling
    - Backup retention management
    - Point-in-time recovery support
    - Backup verification
    """
    
    def __init__(
        self,
        db_host: str,
        db_port: int,
        db_name: str,
        db_user: str,
        db_password: str,
        backup_dir: str = "/backups",
        retention_days: int = 30,
        max_backups: int = 50
    ):
        """
        Initialize backup service
        
        Args:
            db_host: Database host
            db_port: Database port
            db_name: Database name
            db_user: Database user
            db_password: Database password
            backup_dir: Directory to store backups
            retention_days: Days to retain backups
            max_backups: Maximum number of backups to keep
        """
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days
        self.max_backups = max_backups
        
        # Create backup directory
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir = self.backup_dir / "metadata"
        self.metadata_dir.mkdir(exist_ok=True)
        
        # Set PGPASSWORD for pg_dump
        os.environ['PGPASSWORD'] = db_password
        
        logger.info(f"Backup service initialized: {backup_dir}")
    
    def create_full_backup(self) -> BackupMetadata:
        """
        Create full database backup (all schemas)
        
        Returns:
            BackupMetadata: Backup metadata
        """
        backup_id = f"full_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        filename = f"{backup_id}.sql"
        filepath = self.backup_dir / filename
        
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=BackupType.FULL,
            timestamp=datetime.utcnow(),
            status=BackupStatus.IN_PROGRESS,
            schemas=["*"],  # All schemas
            size_bytes=0,
            file_path=str(filepath)
        )
        
        logger.info(f"Starting full backup: {backup_id}")
        start_time = datetime.utcnow()
        
        try:
            # Run pg_dump for full database
            cmd = [
                "pg_dump",
                "-h", self.db_host,
                "-p", str(self.db_port),
                "-U", self.db_user,
                "-d", self.db_name,
                "-F", "c",  # Custom format (compressed)
                "-f", str(filepath),
                "--verbose"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Update metadata
            metadata.status = BackupStatus.COMPLETED
            metadata.size_bytes = filepath.stat().st_size
            metadata.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
            
            # Save metadata
            self._save_metadata(metadata)
            
            logger.info(
                f"Full backup completed: {backup_id} "
                f"({metadata.size_bytes / 1024 / 1024:.2f} MB)"
            )
            
            # Clean old backups
            self._cleanup_old_backups()
            
            return metadata
            
        except subprocess.CalledProcessError as e:
            metadata.status = BackupStatus.FAILED
            metadata.error_message = e.stderr
            metadata.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
            
            self._save_metadata(metadata)
            logger.error(f"Backup failed: {e.stderr}")
            raise
    
    def create_tenant_backup(self, schema_name: str) -> BackupMetadata:
        """
        Create backup of single tenant schema
        
        Args:
            schema_name: Name of tenant schema
            
        Returns:
            BackupMetadata: Backup metadata
        """
        backup_id = f"tenant_{schema_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        filename = f"{backup_id}.sql"
        filepath = self.backup_dir / filename
        
        metadata = BackupMetadata(
            backup_id=backup_id,
            backup_type=BackupType.TENANT,
            timestamp=datetime.utcnow(),
            status=BackupStatus.IN_PROGRESS,
            schemas=[schema_name],
            size_bytes=0,
            file_path=str(filepath)
        )
        
        logger.info(f"Starting tenant backup: {schema_name}")
        start_time = datetime.utcnow()
        
        try:
            # Run pg_dump for specific schema
            cmd = [
                "pg_dump",
                "-h", self.db_host,
                "-p", str(self.db_port),
                "-U", self.db_user,
                "-d", self.db_name,
                "-n", schema_name,  # Only this schema
                "-F", "c",  # Custom format
                "-f", str(filepath),
                "--verbose"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Update metadata
            metadata.status = BackupStatus.COMPLETED
            metadata.size_bytes = filepath.stat().st_size
            metadata.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
            
            self._save_metadata(metadata)
            
            logger.info(
                f"Tenant backup completed: {schema_name} "
                f"({metadata.size_bytes / 1024 / 1024:.2f} MB)"
            )
            
            return metadata
            
        except subprocess.CalledProcessError as e:
            metadata.status = BackupStatus.FAILED
            metadata.error_message = e.stderr
            metadata.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
            
            self._save_metadata(metadata)
            logger.error(f"Tenant backup failed: {e.stderr}")
            raise
    
    def restore_backup(
        self,
        backup_id: str,
        target_schema: Optional[str] = None,
        clean: bool = False
    ) -> None:
        """
        Restore database from backup
        
        Args:
            backup_id: Backup ID to restore
            target_schema: Target schema (for tenant backups)
            clean: Whether to drop existing objects first
        """
        metadata = self._load_metadata(backup_id)
        if not metadata:
            raise ValueError(f"Backup not found: {backup_id}")
        
        if metadata.status != BackupStatus.COMPLETED:
            raise ValueError(f"Cannot restore incomplete backup: {backup_id}")
        
        filepath = Path(metadata.file_path)
        if not filepath.exists():
            raise FileNotFoundError(f"Backup file not found: {filepath}")
        
        logger.info(f"Starting restore: {backup_id}")
        
        try:
            cmd = [
                "pg_restore",
                "-h", self.db_host,
                "-p", str(self.db_port),
                "-U", self.db_user,
                "-d", self.db_name,
                "--verbose"
            ]
            
            if clean:
                cmd.append("--clean")
            
            if target_schema and metadata.backup_type == BackupType.TENANT:
                cmd.extend(["-n", target_schema])
            
            cmd.append(str(filepath))
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Restore completed: {backup_id}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Restore failed: {e.stderr}")
            raise
    
    def list_backups(
        self,
        backup_type: Optional[BackupType] = None,
        schema: Optional[str] = None,
        limit: int = 50
    ) -> List[BackupMetadata]:
        """
        List available backups
        
        Args:
            backup_type: Filter by backup type
            schema: Filter by schema name
            limit: Maximum number of results
            
        Returns:
            List of backup metadata
        """
        backups = []
        
        for metadata_file in self.metadata_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    data = json.load(f)
                    metadata = BackupMetadata.from_dict(data)
                    
                    # Apply filters
                    if backup_type and metadata.backup_type != backup_type:
                        continue
                    
                    if schema and schema not in metadata.schemas:
                        continue
                    
                    backups.append(metadata)
                    
            except Exception as e:
                logger.warning(f"Failed to load metadata {metadata_file}: {e}")
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x.timestamp, reverse=True)
        
        return backups[:limit]
    
    def delete_backup(self, backup_id: str) -> None:
        """
        Delete a backup
        
        Args:
            backup_id: Backup ID to delete
        """
        metadata = self._load_metadata(backup_id)
        if not metadata:
            raise ValueError(f"Backup not found: {backup_id}")
        
        # Delete backup file
        filepath = Path(metadata.file_path)
        if filepath.exists():
            filepath.unlink()
        
        # Delete metadata
        metadata_file = self.metadata_dir / f"{backup_id}.json"
        if metadata_file.exists():
            metadata_file.unlink()
        
        logger.info(f"Backup deleted: {backup_id}")
    
    def verify_backup(self, backup_id: str) -> bool:
        """
        Verify backup integrity
        
        Args:
            backup_id: Backup ID to verify
            
        Returns:
            True if backup is valid
        """
        metadata = self._load_metadata(backup_id)
        if not metadata:
            return False
        
        filepath = Path(metadata.file_path)
        if not filepath.exists():
            return False
        
        # Verify file size matches
        if filepath.stat().st_size != metadata.size_bytes:
            logger.warning(f"Backup size mismatch: {backup_id}")
            return False
        
        # Test restore (dry run)
        try:
            cmd = [
                "pg_restore",
                "-l",  # List contents only
                str(filepath)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"Backup verified: {backup_id}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Backup verification failed: {e.stderr}")
            return False
    
    def get_backup_stats(self) -> Dict:
        """
        Get backup statistics
        
        Returns:
            Dictionary with backup stats
        """
        backups = self.list_backups(limit=1000)
        
        total_size = sum(b.size_bytes for b in backups)
        completed = sum(1 for b in backups if b.status == BackupStatus.COMPLETED)
        failed = sum(1 for b in backups if b.status == BackupStatus.FAILED)
        
        return {
            "total_backups": len(backups),
            "completed_backups": completed,
            "failed_backups": failed,
            "total_size_mb": total_size / 1024 / 1024,
            "oldest_backup": backups[-1].timestamp.isoformat() if backups else None,
            "newest_backup": backups[0].timestamp.isoformat() if backups else None,
            "retention_days": self.retention_days,
            "max_backups": self.max_backups
        }
    
    def _save_metadata(self, metadata: BackupMetadata) -> None:
        """Save backup metadata"""
        metadata_file = self.metadata_dir / f"{metadata.backup_id}.json"
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata.to_dict(), f, indent=2)
    
    def _load_metadata(self, backup_id: str) -> Optional[BackupMetadata]:
        """Load backup metadata"""
        metadata_file = self.metadata_dir / f"{backup_id}.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r') as f:
                data = json.load(f)
                return BackupMetadata.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return None
    
    def _cleanup_old_backups(self) -> None:
        """Clean up old backups based on retention policy"""
        backups = self.list_backups(limit=1000)
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        deleted = 0
        
        # Delete by age
        for backup in backups:
            if backup.timestamp < cutoff_date:
                try:
                    self.delete_backup(backup.backup_id)
                    deleted += 1
                except Exception as e:
                    logger.warning(f"Failed to delete old backup: {e}")
        
        # Delete excess backups (keep only max_backups)
        if len(backups) > self.max_backups:
            excess = sorted(backups, key=lambda x: x.timestamp)[:-self.max_backups]
            for backup in excess:
                try:
                    self.delete_backup(backup.backup_id)
                    deleted += 1
                except Exception as e:
                    logger.warning(f"Failed to delete excess backup: {e}")
        
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old backups")
