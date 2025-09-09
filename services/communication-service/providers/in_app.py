"""
In-App Notification Provider
WebSocket and database-based real-time notification delivery
"""
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
import uuid
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_

from .base import NotificationProvider, NotificationPayload, NotificationResult, NotificationStatus
from ..database import get_db_session
from ..models import Notification, NotificationChannel, NotificationStatus as DBNotificationStatus
from ..redis_client import get_redis_client

logger = logging.getLogger(__name__)


class InAppProvider(NotificationProvider):
    """In-app notification provider using WebSocket and database storage"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.redis_client = None
        self.websocket_connections: Dict[str, Set[Any]] = {}  # user_id -> set of websocket connections
        self.notification_ttl_hours = config.get("notification_ttl_hours", 720)  # 30 days
        self.max_unread_notifications = config.get("max_unread_notifications", 100)
        
    async def _get_redis_client(self):
        """Get Redis client for pub/sub"""
        if not self.redis_client:
            self.redis_client = await get_redis_client()
        return self.redis_client
    
    def get_provider_info(self) -> Dict[str, Any]:
        info = super().get_provider_info()
        info.update({
            "supports_real_time": True,
            "supports_persistence": True,
            "supports_read_status": True,
            "supports_rich_content": True,
            "notification_ttl_hours": self.notification_ttl_hours,
            "max_unread_notifications": self.max_unread_notifications,
        })
        return info
    
    async def validate_recipient(self, recipient: str) -> bool:
        """Validate user ID format (UUID)"""
        try:
            uuid.UUID(recipient)
            return True
        except ValueError:
            return False
    
    async def send(self, payload: NotificationPayload) -> NotificationResult:
        """Send in-app notification"""
        try:
            # Validate recipient (user_id)
            if not await self.validate_recipient(payload.recipient):
                return NotificationResult(
                    id="",
                    status=NotificationStatus.REJECTED,
                    error_message=f"Invalid user ID: {payload.recipient}"
                )
            
            # Store notification in database
            notification_id = await self._store_notification(payload)
            
            # Send real-time notification via WebSocket/Redis
            await self._send_realtime_notification(payload, notification_id)
            
            return NotificationResult(
                id=notification_id,
                status=NotificationStatus.DELIVERED,
                provider_id=self.provider_name,
                sent_at=datetime.utcnow(),
                delivered_at=datetime.utcnow(),
                metadata={
                    "user_id": payload.recipient,
                    "title": payload.subject,
                    "stored_in_db": True,
                    "sent_realtime": True
                }
            )
            
        except Exception as e:
            logger.error(f"In-app notification failed: {str(e)}")
            return NotificationResult(
                id="",
                status=NotificationStatus.FAILED,
                error_message=str(e)
            )
    
    async def _store_notification(self, payload: NotificationPayload) -> str:
        """Store notification in database"""
        try:
            async with get_db_session() as session:
                # Create notification record
                notification = Notification(
                    user_id=uuid.UUID(payload.recipient),
                    channel=NotificationChannel.IN_APP,
                    subject=payload.subject or "Notification",
                    content=payload.content,
                    data=payload.template_data or {},
                    status=DBNotificationStatus.DELIVERED,
                    recipient=payload.recipient,
                    scheduled_at=payload.scheduled_at,
                    expires_at=payload.expires_at or datetime.utcnow() + timedelta(hours=self.notification_ttl_hours),
                    priority=payload.priority,
                    template_id=uuid.UUID(payload.template_id) if payload.template_id else None,
                    is_read=False,
                    read_at=None
                )
                
                session.add(notification)
                await session.commit()
                await session.refresh(notification)
                
                # Clean up old notifications for this user
                await self._cleanup_old_notifications(session, payload.recipient)
                
                return str(notification.id)
                
        except Exception as e:
            logger.error(f"Failed to store in-app notification: {e}")
            raise
    
    async def _cleanup_old_notifications(self, session: Session, user_id: str):
        """Clean up old notifications to prevent inbox overflow"""
        try:
            # Count unread notifications for user
            unread_count = await session.execute(
                """
                SELECT COUNT(*) FROM notifications 
                WHERE user_id = :user_id AND channel = 'in_app' AND is_read = false
                """,
                {"user_id": user_id}
            )
            count = unread_count.scalar()
            
            if count > self.max_unread_notifications:
                # Mark oldest notifications as read
                overflow = count - self.max_unread_notifications
                await session.execute(
                    """
                    UPDATE notifications 
                    SET is_read = true, read_at = :read_at
                    WHERE id IN (
                        SELECT id FROM notifications 
                        WHERE user_id = :user_id AND channel = 'in_app' AND is_read = false 
                        ORDER BY created_at ASC 
                        LIMIT :limit
                    )
                    """,
                    {
                        "user_id": user_id,
                        "read_at": datetime.utcnow(),
                        "limit": overflow
                    }
                )
            
            # Delete expired notifications
            await session.execute(
                """
                DELETE FROM notifications 
                WHERE user_id = :user_id AND channel = 'in_app' 
                AND expires_at < :now AND is_read = true
                """,
                {
                    "user_id": user_id,
                    "now": datetime.utcnow()
                }
            )
            
            await session.commit()
            
        except Exception as e:
            logger.warning(f"Failed to cleanup notifications for user {user_id}: {e}")
    
    async def _send_realtime_notification(self, payload: NotificationPayload, notification_id: str):
        """Send real-time notification via Redis pub/sub"""
        try:
            redis_client = await self._get_redis_client()
            
            # Prepare notification message
            message = {
                "id": notification_id,
                "user_id": payload.recipient,
                "type": "notification",
                "title": payload.subject,
                "body": payload.content,
                "data": payload.template_data or {},
                "priority": payload.priority,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": payload.metadata or {}
            }
            
            # Publish to user-specific channel
            channel = f"notifications:user:{payload.recipient}"
            await redis_client.publish(channel, json.dumps(message))
            
            # Also publish to general notifications channel for admin dashboards
            await redis_client.publish("notifications:all", json.dumps(message))
            
        except Exception as e:
            logger.warning(f"Failed to send real-time notification: {e}")
            # Don't fail the whole notification if real-time delivery fails
    
    async def get_unread_notifications(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get unread notifications for a user"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    """
                    SELECT id, subject, content, data, priority, created_at, expires_at
                    FROM notifications 
                    WHERE user_id = :user_id AND channel = 'in_app' AND is_read = false
                    AND (expires_at IS NULL OR expires_at > :now)
                    ORDER BY created_at DESC 
                    LIMIT :limit
                    """,
                    {
                        "user_id": user_id,
                        "now": datetime.utcnow(),
                        "limit": limit
                    }
                )
                
                notifications = []
                for row in result.fetchall():
                    notifications.append({
                        "id": str(row.id),
                        "title": row.subject,
                        "body": row.content,
                        "data": row.data or {},
                        "priority": row.priority,
                        "created_at": row.created_at.isoformat(),
                        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
                    })
                
                return notifications
                
        except Exception as e:
            logger.error(f"Failed to get unread notifications for user {user_id}: {e}")
            return []
    
    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark notification as read"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    """
                    UPDATE notifications 
                    SET is_read = true, read_at = :read_at
                    WHERE id = :notification_id AND user_id = :user_id AND channel = 'in_app'
                    """,
                    {
                        "notification_id": notification_id,
                        "user_id": user_id,
                        "read_at": datetime.utcnow()
                    }
                )
                
                await session.commit()
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to mark notification {notification_id} as read: {e}")
            return False
    
    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    """
                    UPDATE notifications 
                    SET is_read = true, read_at = :read_at
                    WHERE user_id = :user_id AND channel = 'in_app' AND is_read = false
                    """,
                    {
                        "user_id": user_id,
                        "read_at": datetime.utcnow()
                    }
                )
                
                await session.commit()
                return result.rowcount
                
        except Exception as e:
            logger.error(f"Failed to mark all notifications as read for user {user_id}: {e}")
            return 0
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    """
                    SELECT COUNT(*) FROM notifications 
                    WHERE user_id = :user_id AND channel = 'in_app' AND is_read = false
                    AND (expires_at IS NULL OR expires_at > :now)
                    """,
                    {
                        "user_id": user_id,
                        "now": datetime.utcnow()
                    }
                )
                
                return result.scalar()
                
        except Exception as e:
            logger.error(f"Failed to get unread count for user {user_id}: {e}")
            return 0
    
    async def get_delivery_status(self, notification_id: str) -> NotificationStatus:
        """Get notification delivery status"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    """
                    SELECT status, is_read, read_at FROM notifications 
                    WHERE id = :notification_id AND channel = 'in_app'
                    """,
                    {"notification_id": notification_id}
                )
                
                row = result.fetchone()
                if not row:
                    return NotificationStatus.FAILED
                
                # Map database status to provider status
                if row.is_read:
                    return NotificationStatus.DELIVERED
                else:
                    return NotificationStatus.SENT
                    
        except Exception as e:
            logger.error(f"Failed to get delivery status for {notification_id}: {e}")
            return NotificationStatus.FAILED
    
    async def cancel_notification(self, notification_id: str) -> bool:
        """Delete notification (cancel)"""
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    """
                    DELETE FROM notifications 
                    WHERE id = :notification_id AND channel = 'in_app'
                    """,
                    {"notification_id": notification_id}
                )
                
                await session.commit()
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to cancel notification {notification_id}: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check database and Redis connectivity"""
        if not self.is_enabled:
            return False
            
        try:
            # Test database connection
            async with get_db_session() as session:
                await session.execute("SELECT 1")
            
            # Test Redis connection
            redis_client = await self._get_redis_client()
            await redis_client.ping()
            
            return True
            
        except Exception as e:
            logger.warning(f"In-app provider health check failed: {e}")
            return False


# WebSocket connection manager (placeholder for future WebSocket integration)
class WebSocketManager:
    """Manage WebSocket connections for real-time notifications"""
    
    def __init__(self):
        self.active_connections: Dict[str, List[Any]] = {}
    
    async def connect(self, websocket, user_id: str):
        """Connect user WebSocket"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
    
    def disconnect(self, websocket, user_id: str):
        """Disconnect user WebSocket"""
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: str, user_id: str):
        """Send message to specific user's WebSocket connections"""
        if user_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(message)
                except:
                    disconnected.append(websocket)
            
            # Clean up disconnected sockets
            for websocket in disconnected:
                self.active_connections[user_id].remove(websocket)
    
    async def broadcast(self, message: str):
        """Broadcast message to all connected users"""
        for user_id in self.active_connections:
            await self.send_personal_message(message, user_id)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()