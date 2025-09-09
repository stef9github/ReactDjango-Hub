"""
Cleanup and Maintenance Celery Tasks
Background tasks for database and cache maintenance
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

from ..celery_app import celery_app
from ..database import get_db_session
from ..redis_client import get_redis_client

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def cleanup_old_notifications(self, retention_days: int = 30):
    """
    Clean up old notifications from database
    
    Args:
        retention_days: Number of days to retain notifications (default: 30)
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        async def perform_cleanup():
            async with get_db_session() as session:
                # Delete old read notifications
                read_result = await session.execute(
                    """
                    DELETE FROM notifications 
                    WHERE created_at < :cutoff_date 
                    AND is_read = true 
                    AND status IN ('delivered', 'sent')
                    """,
                    {"cutoff_date": cutoff_date}
                )
                
                # Delete very old unread notifications (90 days)
                old_cutoff_date = datetime.utcnow() - timedelta(days=90)
                unread_result = await session.execute(
                    """
                    DELETE FROM notifications 
                    WHERE created_at < :old_cutoff_date
                    """,
                    {"old_cutoff_date": old_cutoff_date}
                )
                
                await session.commit()
                
                return {
                    "deleted_read": read_result.rowcount,
                    "deleted_unread": unread_result.rowcount
                }
        
        result = asyncio.run(perform_cleanup())
        
        logger.info(f"Cleaned up {result['deleted_read']} read and {result['deleted_unread']} old unread notifications")
        
        return {
            "status": "completed",
            "deleted_read_notifications": result["deleted_read"],
            "deleted_unread_notifications": result["deleted_unread"],
            "retention_days": retention_days,
            "cleaned_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Notification cleanup failed: {exc}")
        raise


@celery_app.task(bind=True)
def cleanup_failed_notifications(self, max_age_hours: int = 24):
    """
    Clean up failed notifications older than specified hours
    
    Args:
        max_age_hours: Maximum age in hours for failed notifications (default: 24)
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        async def perform_cleanup():
            async with get_db_session() as session:
                result = await session.execute(
                    """
                    DELETE FROM notifications 
                    WHERE status = 'failed' 
                    AND updated_at < :cutoff_date
                    """,
                    {"cutoff_date": cutoff_date}
                )
                
                await session.commit()
                return result.rowcount
        
        deleted_count = asyncio.run(perform_cleanup())
        
        logger.info(f"Cleaned up {deleted_count} failed notifications")
        
        return {
            "status": "completed",
            "deleted_failed_notifications": deleted_count,
            "max_age_hours": max_age_hours,
            "cleaned_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Failed notification cleanup failed: {exc}")
        raise


@celery_app.task(bind=True)
def cleanup_expired_cache(self):
    """Clean up expired cache entries"""
    try:
        async def perform_cleanup():
            redis_client = await get_redis_client()
            
            # Get all cache keys
            cache_patterns = [
                "template_cache:*",
                "notification_cache:*",
                "user_preferences:*"
            ]
            
            total_cleaned = 0
            
            for pattern in cache_patterns:
                keys = await redis_client.keys(pattern)
                
                # Check TTL and delete expired keys
                for key in keys:
                    ttl = await redis_client.ttl(key)
                    if ttl == -2:  # Key doesn't exist
                        continue
                    elif ttl == -1:  # Key exists but no expiration
                        # Set a default expiration (24 hours) for keys without TTL
                        await redis_client.expire(key, 86400)
                
                total_cleaned += len([k for k in keys if await redis_client.ttl(k) == -2])
            
            return total_cleaned
        
        cleaned_count = asyncio.run(perform_cleanup())
        
        return {
            "status": "completed",
            "cleaned_cache_entries": cleaned_count,
            "cleaned_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Cache cleanup failed: {exc}")
        raise


@celery_app.task(bind=True)
def cleanup_old_templates(self, retention_days: int = 365):
    """
    Clean up old inactive template versions
    
    Args:
        retention_days: Days to retain inactive templates (default: 365)
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        async def perform_cleanup():
            async with get_db_session() as session:
                # Delete old inactive template versions
                result = await session.execute(
                    """
                    DELETE FROM notification_templates 
                    WHERE is_active = false 
                    AND updated_at < :cutoff_date
                    """,
                    {"cutoff_date": cutoff_date}
                )
                
                await session.commit()
                return result.rowcount
        
        deleted_count = asyncio.run(perform_cleanup())
        
        logger.info(f"Cleaned up {deleted_count} old template versions")
        
        return {
            "status": "completed",
            "deleted_templates": deleted_count,
            "retention_days": retention_days,
            "cleaned_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Template cleanup failed: {exc}")
        raise


@celery_app.task(bind=True)
def optimize_database(self):
    """Optimize database performance"""
    try:
        async def perform_optimization():
            async with get_db_session() as session:
                # Analyze table statistics
                await session.execute("ANALYZE notifications")
                await session.execute("ANALYZE notification_templates")
                await session.execute("ANALYZE notification_categories")
                
                # Vacuum if using PostgreSQL
                # Note: VACUUM cannot run inside a transaction
                # This would need to be handled differently in production
                
                return True
        
        asyncio.run(perform_optimization())
        
        return {
            "status": "completed",
            "optimized_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Database optimization failed: {exc}")
        raise


@celery_app.task(bind=True)
def cleanup_celery_results(self, max_age_hours: int = 24):
    """
    Clean up old Celery task results
    
    Args:
        max_age_hours: Maximum age in hours for task results (default: 24)
    """
    try:
        async def perform_cleanup():
            redis_client = await get_redis_client()
            
            # Get all celery result keys
            result_keys = await redis_client.keys("celery-task-meta-*")
            
            cleaned_count = 0
            cutoff_timestamp = (datetime.utcnow() - timedelta(hours=max_age_hours)).timestamp()
            
            for key in result_keys:
                # Check if result is old
                result_data = await redis_client.get(key)
                if result_data:
                    try:
                        import json
                        data = json.loads(result_data)
                        
                        # Check date_done timestamp
                        if data.get("date_done"):
                            date_done = datetime.fromisoformat(data["date_done"].replace("Z", "+00:00"))
                            if date_done.timestamp() < cutoff_timestamp:
                                await redis_client.delete(key)
                                cleaned_count += 1
                    except (json.JSONDecodeError, ValueError):
                        # Delete malformed results
                        await redis_client.delete(key)
                        cleaned_count += 1
            
            return cleaned_count
        
        cleaned_count = asyncio.run(perform_cleanup())
        
        return {
            "status": "completed",
            "cleaned_results": cleaned_count,
            "max_age_hours": max_age_hours,
            "cleaned_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Celery results cleanup failed: {exc}")
        raise


@celery_app.task(bind=True)
def comprehensive_cleanup(self):
    """Run all cleanup tasks in sequence"""
    try:
        results = {}
        
        # Run individual cleanup tasks
        tasks = [
            ("notifications", cleanup_old_notifications.apply_async()),
            ("failed_notifications", cleanup_failed_notifications.apply_async()),
            ("expired_cache", cleanup_expired_cache.apply_async()),
            ("old_templates", cleanup_old_templates.apply_async()),
            ("celery_results", cleanup_celery_results.apply_async()),
        ]
        
        # Wait for all tasks to complete
        for task_name, task_result in tasks:
            try:
                result = task_result.get(timeout=300)  # 5 minute timeout
                results[task_name] = {
                    "status": "completed",
                    "result": result
                }
            except Exception as e:
                results[task_name] = {
                    "status": "failed",
                    "error": str(e)
                }
        
        # Run database optimization last
        try:
            optimization_result = optimize_database.apply_async().get(timeout=300)
            results["database_optimization"] = {
                "status": "completed",
                "result": optimization_result
            }
        except Exception as e:
            results["database_optimization"] = {
                "status": "failed",
                "error": str(e)
            }
        
        return {
            "status": "completed",
            "individual_results": results,
            "completed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Comprehensive cleanup failed: {exc}")
        raise