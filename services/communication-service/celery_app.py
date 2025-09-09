"""
Celery Application Configuration
Background task processing for notification delivery
"""
import os
from celery import Celery
from celery.schedules import crontab
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery app configuration
celery_app = Celery(
    "communication_service",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
    include=[
        "tasks.notification_tasks",
        "tasks.template_tasks",
        "tasks.cleanup_tasks",
        "tasks.monitoring_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Task routing and priorities
    task_routes={
        "tasks.notification_tasks.send_notification": {"queue": "notifications"},
        "tasks.notification_tasks.send_bulk_notifications": {"queue": "bulk"},
        "tasks.notification_tasks.send_scheduled_notification": {"queue": "scheduled"},
        "tasks.template_tasks.*": {"queue": "templates"},
        "tasks.cleanup_tasks.*": {"queue": "maintenance"},
        "tasks.monitoring_tasks.*": {"queue": "monitoring"},
    },
    
    # Task priorities
    task_annotations={
        "tasks.notification_tasks.send_notification": {"priority": 5},
        "tasks.notification_tasks.send_urgent_notification": {"priority": 9},
        "tasks.notification_tasks.send_bulk_notifications": {"priority": 2},
        "tasks.cleanup_tasks.*": {"priority": 1},
    },
    
    # Result settings
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    
    # Retry settings
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Cleanup old notifications every day at 2 AM
        "cleanup-old-notifications": {
            "task": "tasks.cleanup_tasks.cleanup_old_notifications",
            "schedule": crontab(hour=2, minute=0),
        },
        
        # Process scheduled notifications every minute
        "process-scheduled-notifications": {
            "task": "tasks.notification_tasks.process_scheduled_notifications",
            "schedule": crontab(minute="*"),
        },
        
        # Update notification statistics every 15 minutes
        "update-notification-stats": {
            "task": "tasks.monitoring_tasks.update_notification_statistics",
            "schedule": crontab(minute="*/15"),
        },
        
        # Health check for notification providers every 5 minutes
        "provider-health-check": {
            "task": "tasks.monitoring_tasks.check_provider_health",
            "schedule": crontab(minute="*/5"),
        },
        
        # Clear template cache every hour
        "clear-template-cache": {
            "task": "tasks.template_tasks.clear_expired_cache",
            "schedule": crontab(minute=0),
        },
    },
)

# Error handling
@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration"""
    print(f"Request: {self.request!r}")
    return "Celery is working!"

# Task failure handler
@celery_app.task(bind=True)
def handle_task_failure(self, task_id, error, traceback):
    """Handle task failures"""
    logger.error(f"Task {task_id} failed: {error}")
    logger.error(f"Traceback: {traceback}")
    
    # Could send alert notification here
    # Could update failure statistics
    # Could trigger retry logic

if __name__ == "__main__":
    celery_app.start()