"""
Notification System - P1 Fix
Multi-channel notification system with email, WebSocket, and in-app notifications
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Text, Index
from sqlalchemy.orm import Session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template

from app.core.database import Base
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    """Notification types"""
    AGENT_EXECUTION_STARTED = "agent_execution_started"
    AGENT_EXECUTION_COMPLETED = "agent_execution_completed"
    AGENT_EXECUTION_FAILED = "agent_execution_failed"
    HITL_APPROVAL_REQUIRED = "hitl_approval_required"
    HITL_APPROVED = "hitl_approved"
    HITL_REJECTED = "hitl_rejected"
    HITL_ESCALATED = "hitl_escalated"
    SYSTEM_ALERT = "system_alert"
    USER_MENTIONED = "user_mentioned"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    WEBSOCKET = "websocket"
    IN_APP = "in_app"
    SMS = "sms"  # Future implementation


class Notification(Base):
    """Notification database model"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Recipient
    user_id = Column(Integer, nullable=False, index=True)
    
    # Content
    notification_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSON, nullable=True)  # Additional context data
    
    # Priority & Status
    priority = Column(String(20), nullable=False, default="normal", index=True)
    read = Column(Boolean, nullable=False, default=False, index=True)
    read_at = Column(DateTime, nullable=True)
    
    # Delivery
    channels = Column(JSON, nullable=True)  # List of channels to deliver on
    delivered_channels = Column(JSON, nullable=True)  # Channels successfully delivered
    
    # Metadata
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True)  # For time-sensitive notifications
    
    # Related resources
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(255), nullable=True)
    
    __table_args__ = (
        Index('idx_notification_user_unread', 'user_id', 'read'),
        Index('idx_notification_user_created', 'user_id', 'created_at'),
        Index('idx_notification_priority_read', 'priority', 'read'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "notification_type": self.notification_type,
            "title": self.title,
            "message": self.message,
            "data": self.data,
            "priority": self.priority,
            "read": self.read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "channels": self.channels,
            "delivered_channels": self.delivered_channels,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id
        }


class NotificationService:
    """
    Notification service
    
    Features:
    - Multi-channel delivery (email, WebSocket, in-app)
    - Priority-based handling
    - Template support
    - Async delivery
    - Delivery tracking
    """
    
    def __init__(self, db: Session = None):
        self.db = db
        self.websocket_connections: Dict[int, List[Any]] = {}  # user_id -> [websocket connections]
    
    async def send_async(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "normal",
        channels: Optional[List[str]] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> Notification:
        """
        Send notification asynchronously
        
        Args:
            user_id: Recipient user ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            data: Additional context data
            priority: Priority level
            channels: Delivery channels (defaults to all)
            resource_type: Related resource type
            resource_id: Related resource ID
            expires_at: Expiration time
            
        Returns:
            Created notification
        """
        # Default channels
        if not channels:
            channels = ["in_app", "email", "websocket"]
        
        # Create notification record
        if self.db:
            notification = Notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                data=data or {},
                priority=priority,
                channels=channels,
                delivered_channels=[],
                resource_type=resource_type,
                resource_id=resource_id,
                expires_at=expires_at
            )
            
            await asyncio.to_thread(self.db.add, notification)
            await asyncio.to_thread(self.db.commit)
            await asyncio.to_thread(self.db.refresh, notification)
        else:
            notification = None
        
        # Deliver through channels
        delivered = []
        
        # In-app delivery (database record)
        if "in_app" in channels and notification:
            delivered.append("in_app")
        
        # WebSocket delivery
        if "websocket" in channels:
            success = await self._deliver_websocket(user_id, notification.to_dict() if notification else {
                "title": title,
                "message": message,
                "type": notification_type,
                "priority": priority
            })
            if success:
                delivered.append("websocket")
        
        # Email delivery
        if "email" in channels:
            success = await self._deliver_email(user_id, title, message, data, priority)
            if success:
                delivered.append("email")
        
        # Update delivered channels
        if notification and self.db:
            notification.delivered_channels = delivered
            await asyncio.to_thread(self.db.commit)
        
        logger.info(f"Notification sent to user {user_id} via {delivered}")
        
        return notification
    
    def send(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        message: str,
        **kwargs
    ) -> Notification:
        """
        Send notification synchronously
        
        Wrapper around send_async for synchronous contexts
        """
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is running, create task
            task = asyncio.create_task(
                self.send_async(user_id, notification_type, title, message, **kwargs)
            )
            return None  # Can't wait for result in sync context with running loop
        else:
            # If loop not running, run until complete
            return loop.run_until_complete(
                self.send_async(user_id, notification_type, title, message, **kwargs)
            )
    
    async def _deliver_email(
        self,
        user_id: int,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "normal"
    ) -> bool:
        """
        Deliver notification via email
        
        Args:
            user_id: User ID
            title: Email subject
            message: Email body
            data: Additional context
            priority: Priority level
            
        Returns:
            Success status
        """
        try:
            # Get user email from database
            if not self.db:
                logger.warning("No database connection, skipping email delivery")
                return False
            
            # TODO: Query user email from database
            # For now, using placeholder
            user_email = f"user{user_id}@example.com"
            
            # Create email
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[{priority.upper()}] {title}"
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg["To"] = user_email
            
            # Plain text version
            text_body = f"{message}\n\nPriority: {priority}"
            
            # HTML version with template
            html_template = """
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4CAF50; color: white; padding: 10px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; }}
                    .priority-high {{ border-left: 4px solid #ff5722; }}
                    .priority-urgent {{ border-left: 4px solid #f44336; }}
                    .footer {{ text-align: center; padding: 10px; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>{{ title }}</h2>
                    </div>
                    <div class="content priority-{{ priority }}">
                        <p>{{ message }}</p>
                        {% if data %}
                        <h3>Details:</h3>
                        <ul>
                            {% for key, value in data.items() %}
                            <li><strong>{{ key }}:</strong> {{ value }}</li>
                            {% endfor %}
                        </ul>
                        {% endif %}
                    </div>
                    <div class="footer">
                        <p>This is an automated notification from Agentic AI Platform</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            template = Template(html_template)
            html_body = template.render(title=title, message=message, data=data or {}, priority=priority)
            
            # Attach parts
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            # Send email
            await asyncio.to_thread(self._send_smtp, msg)
            
            logger.info(f"Email notification sent to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}", exc_info=True)
            return False
    
    def _send_smtp(self, msg: MIMEMultipart):
        """Send email via SMTP"""
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            if settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
    
    async def _deliver_websocket(
        self,
        user_id: int,
        notification_data: Dict[str, Any]
    ) -> bool:
        """
        Deliver notification via WebSocket
        
        Args:
            user_id: User ID
            notification_data: Notification data to send
            
        Returns:
            Success status
        """
        if user_id not in self.websocket_connections:
            logger.debug(f"No WebSocket connections for user {user_id}")
            return False
        
        try:
            connections = self.websocket_connections[user_id]
            
            # Send to all user's active connections
            for ws in connections:
                try:
                    await ws.send_json({
                        "type": "notification",
                        "data": notification_data
                    })
                except Exception as e:
                    logger.error(f"Failed to send to WebSocket: {e}")
            
            logger.info(f"WebSocket notification sent to user {user_id} ({len(connections)} connections)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deliver WebSocket notification: {e}", exc_info=True)
            return False
    
    def register_websocket(self, user_id: int, websocket: Any):
        """Register a WebSocket connection for a user"""
        if user_id not in self.websocket_connections:
            self.websocket_connections[user_id] = []
        self.websocket_connections[user_id].append(websocket)
        logger.info(f"WebSocket registered for user {user_id}")
    
    def unregister_websocket(self, user_id: int, websocket: Any):
        """Unregister a WebSocket connection"""
        if user_id in self.websocket_connections:
            try:
                self.websocket_connections[user_id].remove(websocket)
                if not self.websocket_connections[user_id]:
                    del self.websocket_connections[user_id]
                logger.info(f"WebSocket unregistered for user {user_id}")
            except ValueError:
                pass
    
    async def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """
        Mark notification as read
        
        Args:
            notification_id: Notification ID
            user_id: User ID (for verification)
            
        Returns:
            Success status
        """
        if not self.db:
            return False
        
        notification = await asyncio.to_thread(
            self.db.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id
            ).first
        )
        
        if not notification:
            return False
        
        notification.read = True
        notification.read_at = datetime.utcnow()
        await asyncio.to_thread(self.db.commit)
        
        return True
    
    async def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """
        Get notifications for a user
        
        Args:
            user_id: User ID
            unread_only: Only return unread notifications
            limit: Maximum results
            offset: Result offset
            
        Returns:
            List of notifications
        """
        if not self.db:
            return []
        
        query = await asyncio.to_thread(
            lambda: self.db.query(Notification).filter(Notification.user_id == user_id)
        )
        
        if unread_only:
            query = query.filter(Notification.read == False)
        
        query = query.order_by(Notification.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return await asyncio.to_thread(query.all)
    
    async def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications for a user"""
        if not self.db:
            return 0
        
        count = await asyncio.to_thread(
            lambda: self.db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.read == False
            ).count()
        )
        
        return count
