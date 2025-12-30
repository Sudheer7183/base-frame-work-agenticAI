"""
Automated Backup Scheduler for Agentic AI Platform
Supports scheduled backups and monitoring
"""

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Optional, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .backup_service import DatabaseBackupService, BackupType

logger = logging.getLogger(__name__)


class BackupScheduler:
    """
    Automated backup scheduler
    
    Features:
    - Scheduled full backups (daily, weekly)
    - Scheduled tenant backups
    - Automatic cleanup
    - Backup monitoring
    - Failure notifications
    """
    
    def __init__(
        self,
        backup_service: DatabaseBackupService,
        full_backup_schedule: str = "0 2 * * *",  # Daily at 2 AM
        tenant_backup_interval_hours: int = 12,
        enable_monitoring: bool = True
    ):
        """
        Initialize backup scheduler
        
        Args:
            backup_service: Database backup service instance
            full_backup_schedule: Cron schedule for full backups (default: daily at 2 AM)
            tenant_backup_interval_hours: Hours between tenant backups
            enable_monitoring: Enable backup monitoring
        """
        self.backup_service = backup_service
        self.full_backup_schedule = full_backup_schedule
        self.tenant_backup_interval_hours = tenant_backup_interval_hours
        self.enable_monitoring = enable_monitoring
        
        # Initialize scheduler
        self.scheduler = AsyncIOScheduler()
        self._setup_jobs()
        
        logger.info("Backup scheduler initialized")
    
    def _setup_jobs(self) -> None:
        """Setup scheduled jobs"""
        
        # Full backup job
        self.scheduler.add_job(
            self._run_full_backup,
            CronTrigger.from_crontab(self.full_backup_schedule),
            id="full_backup",
            name="Full Database Backup",
            replace_existing=True
        )
        
        # Cleanup job (daily at 3 AM)
        self.scheduler.add_job(
            self._run_cleanup,
            CronTrigger(hour=3, minute=0),
            id="backup_cleanup",
            name="Backup Cleanup",
            replace_existing=True
        )
        
        # Monitoring job (every hour)
        if self.enable_monitoring:
            self.scheduler.add_job(
                self._run_monitoring,
                IntervalTrigger(hours=1),
                id="backup_monitoring",
                name="Backup Monitoring",
                replace_existing=True
            )
        
        logger.info("Backup jobs configured")
    
    async def _run_full_backup(self) -> None:
        """Run scheduled full backup"""
        logger.info("Starting scheduled full backup")
        
        try:
            metadata = self.backup_service.create_full_backup()
            logger.info(
                f"Scheduled full backup completed: {metadata.backup_id} "
                f"({metadata.size_bytes / 1024 / 1024:.2f} MB)"
            )
            
            # Send success notification
            await self._send_notification(
                "success",
                f"Full backup completed: {metadata.backup_id}",
                metadata.to_dict()
            )
            
        except Exception as e:
            logger.error(f"Scheduled full backup failed: {e}")
            
            # Send failure notification
            await self._send_notification(
                "error",
                f"Full backup failed: {str(e)}",
                {"error": str(e)}
            )
    
    async def _run_tenant_backup(self, schema_name: str) -> None:
        """Run scheduled tenant backup"""
        logger.info(f"Starting scheduled tenant backup: {schema_name}")
        
        try:
            metadata = self.backup_service.create_tenant_backup(schema_name)
            logger.info(
                f"Scheduled tenant backup completed: {schema_name} "
                f"({metadata.size_bytes / 1024 / 1024:.2f} MB)"
            )
            
        except Exception as e:
            logger.error(f"Scheduled tenant backup failed for {schema_name}: {e}")
            
            await self._send_notification(
                "error",
                f"Tenant backup failed: {schema_name}",
                {"schema": schema_name, "error": str(e)}
            )
    
    async def _run_cleanup(self) -> None:
        """Run backup cleanup"""
        logger.info("Starting backup cleanup")
        
        try:
            # Cleanup is handled automatically in backup service
            stats = self.backup_service.get_backup_stats()
            logger.info(f"Backup cleanup completed. Stats: {stats}")
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
    
    async def _run_monitoring(self) -> None:
        """Monitor backup health"""
        logger.info("Running backup monitoring")
        
        try:
            stats = self.backup_service.get_backup_stats()
            
            # Check for recent backups
            if stats.get('newest_backup'):
                newest = datetime.fromisoformat(stats['newest_backup'])
                hours_old = (datetime.utcnow() - newest).total_seconds() / 3600
                
                # Alert if no backup in 48 hours
                if hours_old > 48:
                    await self._send_notification(
                        "warning",
                        f"No backup in {hours_old:.1f} hours",
                        stats
                    )
            
            # Check disk space
            total_size_gb = stats['total_size_mb'] / 1024
            if total_size_gb > 100:  # Alert if >100GB
                await self._send_notification(
                    "warning",
                    f"Backup storage high: {total_size_gb:.1f} GB",
                    stats
                )
            
            # Check failed backups
            if stats['failed_backups'] > 0:
                await self._send_notification(
                    "warning",
                    f"{stats['failed_backups']} failed backups",
                    stats
                )
            
        except Exception as e:
            logger.error(f"Backup monitoring failed: {e}")
    
    async def _send_notification(
        self,
        level: str,
        message: str,
        data: dict
    ) -> None:
        """
        Send backup notification
        
        Override this method to implement actual notifications
        (email, Slack, PagerDuty, etc.)
        """
        logger.info(f"Backup notification [{level}]: {message}")
        # TODO: Implement actual notification system
        pass
    
    def schedule_tenant_backup(
        self,
        schema_name: str,
        schedule: Optional[str] = None
    ) -> None:
        """
        Schedule regular backups for a tenant
        
        Args:
            schema_name: Tenant schema name
            schedule: Cron schedule (optional, uses interval if not provided)
        """
        job_id = f"tenant_backup_{schema_name}"
        
        if schedule:
            trigger = CronTrigger.from_crontab(schedule)
        else:
            trigger = IntervalTrigger(hours=self.tenant_backup_interval_hours)
        
        self.scheduler.add_job(
            self._run_tenant_backup,
            trigger,
            args=[schema_name],
            id=job_id,
            name=f"Tenant Backup: {schema_name}",
            replace_existing=True
        )
        
        logger.info(f"Scheduled tenant backup: {schema_name}")
    
    def unschedule_tenant_backup(self, schema_name: str) -> None:
        """
        Remove scheduled backup for a tenant
        
        Args:
            schema_name: Tenant schema name
        """
        job_id = f"tenant_backup_{schema_name}"
        
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Unscheduled tenant backup: {schema_name}")
        except Exception as e:
            logger.warning(f"Failed to unschedule tenant backup: {e}")
    
    def start(self) -> None:
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Backup scheduler started")
    
    def stop(self) -> None:
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Backup scheduler stopped")
    
    def get_jobs(self) -> List[dict]:
        """Get all scheduled jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        return jobs
