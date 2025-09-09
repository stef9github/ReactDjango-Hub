"""
Template Processing Celery Tasks
Background tasks for template rendering and management
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import uuid
import logging

from ..celery_app import celery_app
from ..template_engine import template_engine
from ..models import NotificationChannel
from ..redis_client import get_redis_client

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def render_template(
    self,
    template_id: str,
    variables: Dict[str, Any],
    channel: Optional[str] = None
):
    """
    Render template with variables in background
    
    Args:
        template_id: UUID of template to render
        variables: Template variables
        channel: Optional notification channel
        
    Returns:
        Dict with rendered subject and content
    """
    try:
        channel_enum = NotificationChannel(channel) if channel else None
        
        result = asyncio.run(template_engine.render_template(
            template_id,
            variables,
            channel_enum
        ))
        
        return {
            "template_id": template_id,
            "channel": channel,
            "subject": result["subject"],
            "content": result["content"],
            "rendered_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Template rendering failed: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=30)
        
        raise


@celery_app.task
def validate_template(template_content: str, subject: str = ""):
    """
    Validate template syntax in background
    
    Args:
        template_content: Template content to validate
        subject: Subject template to validate
        
    Returns:
        Dict with validation results
    """
    try:
        result = asyncio.run(template_engine.validate_template_syntax(
            template_content,
            subject
        ))
        
        return {
            "valid": result["valid"],
            "errors": result["errors"],
            "warnings": result["warnings"],
            "validated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Template validation failed: {exc}")
        return {
            "valid": False,
            "errors": [str(exc)],
            "warnings": [],
            "validated_at": datetime.utcnow().isoformat()
        }


@celery_app.task
def render_template_preview(
    template_content: str,
    subject: str,
    variables: Dict[str, Any],
    channel: Optional[str] = None
):
    """
    Render template preview in background
    
    Args:
        template_content: Template content string
        subject: Subject template string
        variables: Template variables
        channel: Optional notification channel
        
    Returns:
        Dict with rendered preview
    """
    try:
        channel_enum = NotificationChannel(channel) if channel else None
        
        result = asyncio.run(template_engine.preview_template(
            template_content,
            subject,
            variables,
            channel_enum
        ))
        
        return {
            "subject": result["subject"],
            "content": result["content"],
            "channel": channel,
            "previewed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Template preview failed: {exc}")
        return {
            "subject": "",
            "content": f"Preview failed: {str(exc)}",
            "channel": channel,
            "previewed_at": datetime.utcnow().isoformat(),
            "error": str(exc)
        }


@celery_app.task
def batch_render_templates(templates_data: List[Dict[str, Any]]):
    """
    Render multiple templates in batch
    
    Args:
        templates_data: List of dicts with keys: template_id, variables, channel
        
    Returns:
        List of rendered template results
    """
    try:
        results = []
        
        for template_data in templates_data:
            try:
                result = render_template.apply_async(
                    args=(
                        template_data["template_id"],
                        template_data.get("variables", {}),
                        template_data.get("channel")
                    )
                )
                
                results.append({
                    "template_id": template_data["template_id"],
                    "task_id": result.id,
                    "status": "queued"
                })
                
            except Exception as e:
                results.append({
                    "template_id": template_data.get("template_id", "unknown"),
                    "status": "failed",
                    "error": str(e)
                })
        
        return {
            "total_templates": len(templates_data),
            "results": results,
            "batch_created_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Batch template rendering failed: {exc}")
        raise


@celery_app.task
def clear_expired_cache():
    """Clear expired template cache entries"""
    try:
        result = asyncio.run(template_engine.clear_cache())
        
        return {
            "status": "completed",
            "cleared_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Cache clearing failed: {exc}")
        raise


@celery_app.task
def warm_template_cache(template_ids: List[str], sample_variables: Dict[str, Any]):
    """
    Warm template cache with sample data
    
    Args:
        template_ids: List of template IDs to warm up
        sample_variables: Sample variables to use for rendering
    """
    try:
        warmed_count = 0
        errors = []
        
        for template_id in template_ids:
            try:
                # Render template for each channel to warm cache
                for channel in ["email", "sms", "push", "in_app"]:
                    render_template.apply_async(
                        args=(template_id, sample_variables, channel)
                    )
                
                warmed_count += 1
                
            except Exception as e:
                errors.append({
                    "template_id": template_id,
                    "error": str(e)
                })
        
        return {
            "templates_processed": warmed_count,
            "errors": errors,
            "warmed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Cache warming failed: {exc}")
        raise


@celery_app.task
def extract_template_variables(template_content: str):
    """
    Extract variables from template content
    
    Args:
        template_content: Template content to analyze
        
    Returns:
        List of variable names found in template
    """
    try:
        variables = asyncio.run(template_engine.get_template_variables(template_content))
        
        return {
            "variables": variables,
            "variable_count": len(variables),
            "extracted_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Variable extraction failed: {exc}")
        return {
            "variables": [],
            "variable_count": 0,
            "extracted_at": datetime.utcnow().isoformat(),
            "error": str(exc)
        }


@celery_app.task
def optimize_template_performance():
    """Optimize template performance by analyzing usage patterns"""
    try:
        # This would analyze template usage patterns and optimize caching
        # Placeholder for future implementation
        
        return {
            "status": "completed",
            "optimizations_applied": [],
            "optimized_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Template optimization failed: {exc}")
        raise


@celery_app.task
def generate_template_usage_report():
    """Generate template usage statistics"""
    try:
        async def get_template_stats():
            try:
                redis_client = await get_redis_client()
                
                # Get cache statistics
                cache_keys = await redis_client.keys("template_cache:*")
                cache_stats = {
                    "total_cached_templates": len(cache_keys),
                    "cache_hit_rate": 0.0,  # Would need to track hits/misses
                }
                
                return cache_stats
                
            except Exception as e:
                logger.error(f"Failed to get template stats: {e}")
                return {}
        
        stats = asyncio.run(get_template_stats())
        
        return {
            "cache_statistics": stats,
            "report_generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Template usage report failed: {exc}")
        raise