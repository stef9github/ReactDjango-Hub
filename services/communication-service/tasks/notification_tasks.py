"""
Notification Celery Tasks
Background processing for notification delivery
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import uuid
import logging
from celery import Task
from celery.exceptions import Retry, MaxRetriesExceededError

from ..celery_app import celery_app
from ..providers.base import NotificationPayload, NotificationStatus
from ..providers import create_email_provider, create_sms_provider, create_push_provider
from ..providers.in_app import InAppProvider
from ..template_engine import template_engine
from ..database import get_db_session
from ..models import Notification, NotificationChannel, NotificationStatus as DBNotificationStatus

logger = logging.getLogger(__name__)


class NotificationTask(Task):
    """Base task class with notification-specific error handling"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure"""
        logger.error(f"Notification task {task_id} failed: {exc}")
        
        # Update notification status in database if notification_id provided
        notification_id = kwargs.get('notification_id') or (args[0] if args else None)
        if notification_id:
            asyncio.run(self._update_notification_status(
                notification_id, 
                DBNotificationStatus.FAILED,
                error_message=str(exc)
            ))
    
    async def _update_notification_status(
        self, 
        notification_id: str, 
        status: DBNotificationStatus,
        error_message: Optional[str] = None
    ):
        """Update notification status in database"""
        try:
            async with get_db_session() as session:
                notification = await session.get(Notification, uuid.UUID(notification_id))
                if notification:
                    notification.status = status
                    if error_message:
                        notification.error_message = error_message
                    if status == DBNotificationStatus.SENT:
                        notification.sent_at = datetime.utcnow()
                    elif status == DBNotificationStatus.DELIVERED:
                        notification.delivered_at = datetime.utcnow()
                    
                    await session.commit()
                    
        except Exception as e:
            logger.error(f"Failed to update notification status: {e}")


@celery_app.task(bind=True, base=NotificationTask, max_retries=3, default_retry_delay=60)
def send_notification(
    self,
    channel: str,
    recipient: str,
    content: str,
    subject: Optional[str] = None,
    template_id: Optional[str] = None,
    template_data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    notification_id: Optional[str] = None,
    priority: str = "normal"
):
    """
    Send a single notification via specified channel
    
    Args:
        channel: Notification channel (email, sms, push, in_app)
        recipient: Recipient address/ID
        content: Notification content
        subject: Notification subject (for email/push)
        template_id: Optional template ID for rendering
        template_data: Data for template rendering
        metadata: Additional metadata
        notification_id: Database notification ID
        priority: Notification priority (low, normal, high, urgent)
    """
    try:
        # Create notification payload
        payload = NotificationPayload(
            recipient=recipient,
            content=content,
            subject=subject,
            template_id=template_id,
            template_data=template_data or {},
            metadata=metadata or {},
            priority=priority
        )
        
        # Render template if template_id provided
        if template_id:
            rendered = asyncio.run(template_engine.render_template(
                template_id,
                template_data or {},
                NotificationChannel(channel)
            ))
            payload.subject = rendered.get("subject") or payload.subject
            payload.content = rendered.get("content") or payload.content
        
        # Get provider and send notification
        provider = _get_provider(channel, metadata or {})
        result = asyncio.run(provider.send(payload))
        
        # Update database with result
        if notification_id:
            status_mapping = {
                NotificationStatus.SENT: DBNotificationStatus.SENT,
                NotificationStatus.QUEUED: DBNotificationStatus.QUEUED,
                NotificationStatus.DELIVERED: DBNotificationStatus.DELIVERED,
                NotificationStatus.FAILED: DBNotificationStatus.FAILED,
                NotificationStatus.REJECTED: DBNotificationStatus.FAILED,
            }
            
            asyncio.run(self._update_notification_status(
                notification_id,
                status_mapping.get(result.status, DBNotificationStatus.FAILED),
                result.error_message
            ))
        
        if result.status == NotificationStatus.FAILED:
            raise Exception(f"Notification delivery failed: {result.error_message}")
        
        return {
            "status": result.status.value,
            "provider_id": result.provider_id,
            "notification_id": result.id,
            "sent_at": result.sent_at.isoformat() if result.sent_at else None,
            "cost": result.cost
        }
        
    except Exception as exc:
        logger.error(f"Notification task failed: {exc}")
        
        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            countdown = (2 ** self.request.retries) * 60  # 1, 2, 4 minutes
            raise self.retry(exc=exc, countdown=countdown)
        
        raise MaxRetriesExceededError(f"Max retries exceeded: {exc}")


@celery_app.task(bind=True, base=NotificationTask)
def send_urgent_notification(
    self,
    channel: str,
    recipient: str,
    content: str,
    subject: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Send urgent notification with highest priority"""
    return send_notification.apply_async(
        args=(channel, recipient, content, subject, None, None, metadata, None, "urgent"),
        priority=9,
        countdown=0
    )


@celery_app.task(bind=True, base=NotificationTask)
def send_bulk_notifications(
    self,
    notifications: List[Dict[str, Any]],
    batch_size: int = 50,
    delay_between_batches: int = 5
):
    """
    Send bulk notifications in batches
    
    Args:
        notifications: List of notification dicts with keys: channel, recipient, content, etc.
        batch_size: Number of notifications per batch
        delay_between_batches: Delay in seconds between batches
    """
    try:
        total_notifications = len(notifications)
        batches = [notifications[i:i + batch_size] for i in range(0, total_notifications, batch_size)]
        results = []
        
        logger.info(f"Processing {total_notifications} notifications in {len(batches)} batches")
        
        for batch_idx, batch in enumerate(batches):
            batch_results = []
            
            # Process batch
            for notification in batch:
                task_result = send_notification.apply_async(
                    args=(
                        notification["channel"],
                        notification["recipient"],
                        notification["content"],
                        notification.get("subject"),
                        notification.get("template_id"),
                        notification.get("template_data"),
                        notification.get("metadata"),
                        notification.get("notification_id"),
                        notification.get("priority", "normal")
                    ),
                    priority=2  # Lower priority for bulk
                )
                batch_results.append(task_result.id)
            
            results.extend(batch_results)
            
            # Delay between batches (except last batch)
            if batch_idx < len(batches) - 1:
                import time
                time.sleep(delay_between_batches)
        
        return {
            "total_notifications": total_notifications,
            "batches": len(batches),
            "task_ids": results
        }
        
    except Exception as exc:
        logger.error(f"Bulk notification task failed: {exc}")
        raise


@celery_app.task(bind=True, base=NotificationTask, max_retries=1)
def send_scheduled_notification(self, notification_id: str):
    """
    Send a scheduled notification
    
    Args:
        notification_id: Database notification ID to send
    """
    try:
        # Get notification from database
        async def get_notification():
            async with get_db_session() as session:
                return await session.get(Notification, uuid.UUID(notification_id))
        
        notification = asyncio.run(get_notification())
        
        if not notification:
            raise ValueError(f"Notification {notification_id} not found")
        
        if notification.status != DBNotificationStatus.PENDING:
            logger.warning(f"Notification {notification_id} already processed (status: {notification.status})")
            return {"status": "already_processed"}
        
        # Check if it's time to send
        if notification.scheduled_at and notification.scheduled_at > datetime.utcnow():
            logger.warning(f"Notification {notification_id} not yet due (scheduled: {notification.scheduled_at})")
            return {"status": "not_due"}
        
        # Send notification
        result = send_notification.apply_async(
            args=(
                notification.channel.value,
                notification.recipient,
                notification.content,
                notification.subject,
                str(notification.template_id) if notification.template_id else None,
                notification.data,
                {"notification_id": notification_id},
                notification_id,
                notification.priority or "normal"
            )
        )
        
        return {
            "status": "sent",
            "task_id": result.id,
            "notification_id": notification_id
        }
        
    except Exception as exc:
        logger.error(f"Scheduled notification task failed: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=300)  # Retry in 5 minutes
        raise


@celery_app.task
def process_scheduled_notifications():
    """Process notifications that are due to be sent"""
    try:
        async def get_due_notifications():
            async with get_db_session() as session:
                result = await session.execute(
                    """
                    SELECT id FROM notifications 
                    WHERE status = 'pending' 
                    AND scheduled_at IS NOT NULL 
                    AND scheduled_at <= :now
                    AND (expires_at IS NULL OR expires_at > :now)
                    ORDER BY scheduled_at ASC
                    LIMIT 100
                    """,
                    {"now": datetime.utcnow()}
                )
                return [str(row.id) for row in result.fetchall()]
        
        due_notifications = asyncio.run(get_due_notifications())
        
        if not due_notifications:
            return {"processed": 0}
        
        logger.info(f"Processing {len(due_notifications)} scheduled notifications")
        
        # Send scheduled notifications
        for notification_id in due_notifications:
            send_scheduled_notification.apply_async(args=(notification_id,))
        
        return {
            "processed": len(due_notifications),
            "notification_ids": due_notifications
        }
        
    except Exception as exc:
        logger.error(f"Process scheduled notifications failed: {exc}")
        raise


def _get_provider(channel: str, config: Dict[str, Any]):
    """Get notification provider for channel"""
    if channel == "email":
        return create_email_provider("smtp", {
            "smtp_host": config.get("smtp_host", "localhost"),
            "smtp_port": config.get("smtp_port", 587),
            "smtp_username": config.get("smtp_username"),
            "smtp_password": config.get("smtp_password"),
            "from_email": config.get("from_email", "noreply@example.com"),
            "use_tls": config.get("use_tls", True),
            "enabled": True
        })
    
    elif channel == "sms":
        return create_sms_provider("twilio", {
            "account_sid": config.get("twilio_account_sid"),
            "auth_token": config.get("twilio_auth_token"),
            "from_number": config.get("twilio_from_number"),
            "enabled": True
        })
    
    elif channel == "push":
        return create_push_provider("firebase", {
            "project_id": config.get("firebase_project_id"),
            "private_key": config.get("firebase_private_key"),
            "client_email": config.get("firebase_client_email"),
            "enabled": True
        })
    
    elif channel == "in_app":
        return InAppProvider({"enabled": True})
    
    else:
        raise ValueError(f"Unknown notification channel: {channel}")