"""
Celery Tasks Package
Background tasks for notification processing
"""

from .notification_tasks import (
    send_notification,
    send_bulk_notifications,
    send_scheduled_notification,
    send_urgent_notification,
    process_scheduled_notifications,
)

from .template_tasks import (
    render_template,
    validate_template,
    clear_expired_cache,
)

from .cleanup_tasks import (
    cleanup_old_notifications,
    cleanup_failed_notifications,
    cleanup_expired_cache,
)

from .monitoring_tasks import (
    update_notification_statistics,
    check_provider_health,
    generate_daily_report,
)

__all__ = [
    # Notification tasks
    'send_notification',
    'send_bulk_notifications',
    'send_scheduled_notification',
    'send_urgent_notification',
    'process_scheduled_notifications',
    
    # Template tasks
    'render_template',
    'validate_template',
    'clear_expired_cache',
    
    # Cleanup tasks
    'cleanup_old_notifications',
    'cleanup_failed_notifications',
    'cleanup_expired_cache',
    
    # Monitoring tasks
    'update_notification_statistics',
    'check_provider_health',
    'generate_daily_report',
]