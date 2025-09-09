"""
Monitoring and Statistics Celery Tasks
Background tasks for system monitoring and reporting
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

from ..celery_app import celery_app
from ..database import get_db_session
from ..redis_client import get_redis_client
from ..providers import create_email_provider, create_sms_provider, create_push_provider
from ..providers.in_app import InAppProvider

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def update_notification_statistics(self):
    """Update notification delivery statistics"""
    try:
        async def collect_stats():
            async with get_db_session() as session:
                # Get statistics for the last 24 hours
                yesterday = datetime.utcnow() - timedelta(days=1)
                
                # Overall statistics
                total_result = await session.execute(
                    "SELECT COUNT(*) FROM notifications WHERE created_at >= :yesterday",
                    {"yesterday": yesterday}
                )
                total_notifications = total_result.scalar()
                
                # Statistics by status
                status_result = await session.execute(
                    """
                    SELECT status, COUNT(*) as count 
                    FROM notifications 
                    WHERE created_at >= :yesterday 
                    GROUP BY status
                    """,
                    {"yesterday": yesterday}
                )
                status_stats = {row.status: row.count for row in status_result.fetchall()}
                
                # Statistics by channel
                channel_result = await session.execute(
                    """
                    SELECT channel, COUNT(*) as count 
                    FROM notifications 
                    WHERE created_at >= :yesterday 
                    GROUP BY channel
                    """,
                    {"yesterday": yesterday}
                )
                channel_stats = {row.channel: row.count for row in channel_result.fetchall()}
                
                # Error statistics
                error_result = await session.execute(
                    """
                    SELECT error_message, COUNT(*) as count 
                    FROM notifications 
                    WHERE created_at >= :yesterday 
                    AND status = 'failed' 
                    AND error_message IS NOT NULL
                    GROUP BY error_message 
                    ORDER BY count DESC 
                    LIMIT 10
                    """,
                    {"yesterday": yesterday}
                )
                error_stats = {row.error_message: row.count for row in error_result.fetchall()}
                
                return {
                    "total_notifications": total_notifications,
                    "status_breakdown": status_stats,
                    "channel_breakdown": channel_stats,
                    "top_errors": error_stats
                }
        
        stats = asyncio.run(collect_stats())
        
        # Store stats in Redis for quick access
        async def store_stats():
            redis_client = await get_redis_client()
            stats_key = f"notification_stats:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
            
            await redis_client.setex(
                stats_key,
                3600,  # 1 hour TTL
                str(stats)  # Would use JSON in production
            )
        
        asyncio.run(store_stats())
        
        return {
            "status": "completed",
            "statistics": stats,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Statistics update failed: {exc}")
        raise


@celery_app.task(bind=True)
def check_provider_health(self):
    """Check health of all notification providers"""
    try:
        async def check_all_providers():
            health_results = {}
            
            # Check email provider
            try:
                email_provider = create_email_provider("smtp", {
                    "smtp_host": "localhost",
                    "smtp_port": 587,
                    "enabled": True
                })
                health_results["email"] = await email_provider.health_check()
            except Exception as e:
                health_results["email"] = False
                logger.warning(f"Email provider health check failed: {e}")
            
            # Check SMS provider (if configured)
            try:
                sms_provider = create_sms_provider("twilio", {
                    "account_sid": "test",
                    "auth_token": "test",
                    "from_number": "+1234567890",
                    "enabled": True
                })
                health_results["sms"] = await sms_provider.health_check()
            except Exception as e:
                health_results["sms"] = False
                logger.warning(f"SMS provider health check failed: {e}")
            
            # Check push provider (if configured)
            try:
                push_provider = create_push_provider("firebase", {
                    "project_id": "test",
                    "private_key": "test",
                    "client_email": "test@example.com",
                    "enabled": True
                })
                health_results["push"] = await push_provider.health_check()
            except Exception as e:
                health_results["push"] = False
                logger.warning(f"Push provider health check failed: {e}")
            
            # Check in-app provider
            try:
                in_app_provider = InAppProvider({"enabled": True})
                health_results["in_app"] = await in_app_provider.health_check()
            except Exception as e:
                health_results["in_app"] = False
                logger.warning(f"In-app provider health check failed: {e}")
            
            return health_results
        
        health_status = asyncio.run(check_all_providers())
        
        # Store health status in Redis
        async def store_health_status():
            redis_client = await get_redis_client()
            await redis_client.setex(
                "provider_health_status",
                300,  # 5 minute TTL
                str(health_status)
            )
        
        asyncio.run(store_health_status())
        
        # Count healthy vs unhealthy providers
        healthy_count = sum(1 for status in health_status.values() if status)
        total_count = len(health_status)
        
        return {
            "status": "completed",
            "provider_health": health_status,
            "healthy_providers": healthy_count,
            "total_providers": total_count,
            "all_healthy": healthy_count == total_count,
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Provider health check failed: {exc}")
        raise


@celery_app.task(bind=True)
def generate_daily_report(self, date: str = None):
    """
    Generate daily notification report
    
    Args:
        date: Date in YYYY-MM-DD format (defaults to yesterday)
    """
    try:
        if date:
            report_date = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            report_date = (datetime.utcnow() - timedelta(days=1)).date()
        
        async def generate_report():
            async with get_db_session() as session:
                start_date = datetime.combine(report_date, datetime.min.time())
                end_date = start_date + timedelta(days=1)
                
                # Total notifications
                total_result = await session.execute(
                    """
                    SELECT COUNT(*) FROM notifications 
                    WHERE created_at >= :start_date AND created_at < :end_date
                    """,
                    {"start_date": start_date, "end_date": end_date}
                )
                total_notifications = total_result.scalar()
                
                # Success rate
                success_result = await session.execute(
                    """
                    SELECT COUNT(*) FROM notifications 
                    WHERE created_at >= :start_date AND created_at < :end_date
                    AND status IN ('sent', 'delivered')
                    """,
                    {"start_date": start_date, "end_date": end_date}
                )
                successful_notifications = success_result.scalar()
                
                # Channel breakdown
                channel_result = await session.execute(
                    """
                    SELECT channel, COUNT(*) as count,
                           SUM(CASE WHEN status IN ('sent', 'delivered') THEN 1 ELSE 0 END) as successful
                    FROM notifications 
                    WHERE created_at >= :start_date AND created_at < :end_date
                    GROUP BY channel
                    """,
                    {"start_date": start_date, "end_date": end_date}
                )
                
                channel_breakdown = {}
                for row in channel_result.fetchall():
                    channel_breakdown[row.channel] = {
                        "total": row.count,
                        "successful": row.successful,
                        "success_rate": (row.successful / row.count * 100) if row.count > 0 else 0
                    }
                
                # Hourly distribution
                hourly_result = await session.execute(
                    """
                    SELECT EXTRACT(hour FROM created_at) as hour, COUNT(*) as count
                    FROM notifications 
                    WHERE created_at >= :start_date AND created_at < :end_date
                    GROUP BY EXTRACT(hour FROM created_at)
                    ORDER BY hour
                    """,
                    {"start_date": start_date, "end_date": end_date}
                )
                
                hourly_distribution = {int(row.hour): row.count for row in hourly_result.fetchall()}
                
                # Top failure reasons
                failure_result = await session.execute(
                    """
                    SELECT error_message, COUNT(*) as count
                    FROM notifications 
                    WHERE created_at >= :start_date AND created_at < :end_date
                    AND status = 'failed'
                    AND error_message IS NOT NULL
                    GROUP BY error_message
                    ORDER BY count DESC
                    LIMIT 5
                    """,
                    {"start_date": start_date, "end_date": end_date}
                )
                
                top_failures = {row.error_message: row.count for row in failure_result.fetchall()}
                
                return {
                    "date": report_date.isoformat(),
                    "total_notifications": total_notifications,
                    "successful_notifications": successful_notifications,
                    "success_rate": (successful_notifications / total_notifications * 100) if total_notifications > 0 else 0,
                    "channel_breakdown": channel_breakdown,
                    "hourly_distribution": hourly_distribution,
                    "top_failure_reasons": top_failures
                }
        
        report = asyncio.run(generate_report())
        
        # Store report in Redis
        async def store_report():
            redis_client = await get_redis_client()
            report_key = f"daily_report:{report_date.isoformat()}"
            
            await redis_client.setex(
                report_key,
                86400 * 7,  # Keep for 7 days
                str(report)
            )
        
        asyncio.run(store_report())
        
        return {
            "status": "completed",
            "report": report,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Daily report generation failed: {exc}")
        raise


@celery_app.task(bind=True)
def monitor_queue_health(self):
    """Monitor Celery queue health and performance"""
    try:
        from celery import current_app
        
        # Get queue statistics
        inspect = current_app.control.inspect()
        
        # Active tasks
        active_tasks = inspect.active()
        active_count = sum(len(tasks) for tasks in (active_tasks or {}).values())
        
        # Reserved tasks
        reserved_tasks = inspect.reserved()
        reserved_count = sum(len(tasks) for tasks in (reserved_tasks or {}).values())
        
        # Queue lengths (approximate)
        async def get_queue_lengths():
            redis_client = await get_redis_client()
            
            queues = ["notifications", "bulk", "scheduled", "templates", "maintenance", "monitoring"]
            queue_lengths = {}
            
            for queue in queues:
                length = await redis_client.llen(f"celery:{queue}")
                queue_lengths[queue] = length
            
            return queue_lengths
        
        queue_lengths = asyncio.run(get_queue_lengths())
        
        # Calculate queue health score
        total_queued = sum(queue_lengths.values())
        health_score = 100
        
        if total_queued > 1000:
            health_score -= 30
        elif total_queued > 500:
            health_score -= 20
        elif total_queued > 100:
            health_score -= 10
        
        if active_count > 50:
            health_score -= 20
        elif active_count > 20:
            health_score -= 10
        
        return {
            "status": "completed",
            "queue_health": {
                "health_score": health_score,
                "active_tasks": active_count,
                "reserved_tasks": reserved_count,
                "queue_lengths": queue_lengths,
                "total_queued": total_queued
            },
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Queue health monitoring failed: {exc}")
        raise


@celery_app.task(bind=True)
def alert_on_high_failure_rate(self, threshold: float = 10.0):
    """
    Alert if notification failure rate exceeds threshold
    
    Args:
        threshold: Failure rate threshold percentage (default: 10%)
    """
    try:
        async def check_failure_rate():
            async with get_db_session() as session:
                # Check failure rate in last hour
                last_hour = datetime.utcnow() - timedelta(hours=1)
                
                total_result = await session.execute(
                    "SELECT COUNT(*) FROM notifications WHERE created_at >= :last_hour",
                    {"last_hour": last_hour}
                )
                total_notifications = total_result.scalar()
                
                if total_notifications == 0:
                    return {"failure_rate": 0, "total": 0, "failed": 0, "alert": False}
                
                failed_result = await session.execute(
                    """
                    SELECT COUNT(*) FROM notifications 
                    WHERE created_at >= :last_hour AND status = 'failed'
                    """,
                    {"last_hour": last_hour}
                )
                failed_notifications = failed_result.scalar()
                
                failure_rate = (failed_notifications / total_notifications) * 100
                
                return {
                    "failure_rate": failure_rate,
                    "total": total_notifications,
                    "failed": failed_notifications,
                    "alert": failure_rate > threshold
                }
        
        result = asyncio.run(check_failure_rate())
        
        if result["alert"]:
            logger.warning(
                f"High failure rate alert: {result['failure_rate']:.2f}% "
                f"({result['failed']}/{result['total']}) in the last hour"
            )
            
            # In production, this would send an alert notification
            # to administrators via email, Slack, etc.
        
        return {
            "status": "completed",
            "failure_rate_check": result,
            "threshold": threshold,
            "checked_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Failure rate monitoring failed: {exc}")
        raise