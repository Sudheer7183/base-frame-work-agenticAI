"""
Secrets Audit Logger

Logs all secrets access and modifications for security auditing.

File: backend/app/core/secrets/audit.py
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)


class SecretsAuditLogger:
    """
    Audit logger for secrets access and modifications
    
    Logs to a separate file with rotation and structured format.
    """
    
    def __init__(
        self,
        log_file: str = "logs/secrets_audit.log",
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 10
    ):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create dedicated logger for audit
        self.audit_logger = logging.getLogger("secrets_audit")
        self.audit_logger.setLevel(logging.INFO)
        self.audit_logger.propagate = False  # Don't propagate to root logger
        
        # Add rotating file handler
        handler = RotatingFileHandler(
            self.log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        
        # Structured JSON format
        formatter = logging.Formatter(
            '%(message)s'  # We'll format as JSON ourselves
        )
        handler.setFormatter(formatter)
        
        self.audit_logger.addHandler(handler)
        logger.info(f"Secrets audit logging to: {self.log_file}")
    
    def _log_event(
        self,
        event_type: str,
        key: str,
        action: str,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a secrets event in structured JSON format"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "key": key,
            "action": action,
            "success": success,
            "user": os.getenv("USER", "unknown"),
            "environment": os.getenv("ENVIRONMENT", "unknown"),
            "hostname": os.getenv("HOSTNAME", "unknown"),
        }
        
        if error:
            event["error"] = error
        
        if metadata:
            event["metadata"] = metadata
        
        self.audit_logger.info(json.dumps(event))
    
    def log_access(
        self,
        key: str,
        action: str,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a secret access event"""
        self._log_event("access", key, action, success, error, metadata)
    
    def log_modification(
        self,
        key: str,
        action: str,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a secret modification event"""
        self._log_event("modification", key, action, success, error, metadata)
    
    def log_rotation(
        self,
        key: str,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a secret rotation event"""
        self._log_event("rotation", key, "rotate", success, error, metadata)
    
    def get_audit_trail(
        self,
        key: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> list[Dict[str, Any]]:
        """
        Retrieve audit trail for analysis
        
        Args:
            key: Filter by specific key
            event_type: Filter by event type
            limit: Maximum number of events to return
            
        Returns:
            List of audit events
        """
        events = []
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        
                        # Apply filters
                        if key and event.get("key") != key:
                            continue
                        
                        if event_type and event.get("event_type") != event_type:
                            continue
                        
                        events.append(event)
                        
                        if len(events) >= limit:
                            break
                            
                    except json.JSONDecodeError:
                        continue
            
            # Return most recent first
            return list(reversed(events))
            
        except FileNotFoundError:
            logger.warning(f"Audit log file not found: {self.log_file}")
            return []
        except Exception as e:
            logger.error(f"Error reading audit trail: {e}")
            return []
    
    def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get audit statistics for the last N hours
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Dictionary with statistics
        """
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        stats = {
            "total_events": 0,
            "access_events": 0,
            "modification_events": 0,
            "rotation_events": 0,
            "failed_events": 0,
            "unique_keys": set(),
            "actions": {},
            "period_hours": hours
        }
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        event_time = datetime.fromisoformat(event["timestamp"])
                        
                        if event_time < cutoff:
                            continue
                        
                        stats["total_events"] += 1
                        
                        # Count by event type
                        event_type = event.get("event_type")
                        if event_type == "access":
                            stats["access_events"] += 1
                        elif event_type == "modification":
                            stats["modification_events"] += 1
                        elif event_type == "rotation":
                            stats["rotation_events"] += 1
                        
                        # Count failures
                        if not event.get("success", True):
                            stats["failed_events"] += 1
                        
                        # Track unique keys
                        stats["unique_keys"].add(event.get("key", "unknown"))
                        
                        # Track actions
                        action = event.get("action", "unknown")
                        stats["actions"][action] = stats["actions"].get(action, 0) + 1
                        
                    except (json.JSONDecodeError, KeyError):
                        continue
            
            # Convert set to count
            stats["unique_keys"] = len(stats["unique_keys"])
            
            return stats
            
        except FileNotFoundError:
            logger.warning(f"Audit log file not found: {self.log_file}")
            return stats
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return stats
    
    def alert_on_suspicious_activity(self, threshold: int = 10):
        """
        Check for suspicious activity patterns
        
        Args:
            threshold: Number of failed attempts to trigger alert
            
        Returns:
            List of alerts
        """
        alerts = []
        
        # Get recent statistics
        stats = self.get_statistics(hours=1)
        
        # Check for excessive failures
        if stats["failed_events"] > threshold:
            alerts.append({
                "severity": "high",
                "type": "excessive_failures",
                "message": f"Detected {stats['failed_events']} failed secret access attempts in last hour",
                "threshold": threshold
            })
        
        # Check for unusual access patterns
        if stats["access_events"] > 1000:
            alerts.append({
                "severity": "medium",
                "type": "high_access_volume",
                "message": f"Detected {stats['access_events']} secret access events in last hour",
                "threshold": 1000
            })
        
        return alerts