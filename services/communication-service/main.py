"""
Communication Service - Notifications + Messaging
Port: 8003
"""
import os
import httpx
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import time
import psutil
import logging

# Add logging for debugging
logger = logging.getLogger(__name__)

# Service configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "communication-service")
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 8003))
IDENTITY_SERVICE_URL = os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8001")
start_time = time.time()

# JWT Authentication setup
security = HTTPBearer()

app = FastAPI(
    title=f"{SERVICE_NAME.title().replace('-', ' ')} API",
    description="Microservice for notifications, messaging, and multi-channel delivery",
    version=SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware - configured for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Token Validation Function
async def validate_jwt_token(token: str = Depends(security)):
    """
    Validate JWT token with Identity Service.
    
    Args:
        token: Bearer token from Authorization header
        
    Returns:
        dict: User data from Identity Service
        
    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    try:
        # Call Identity Service to validate token
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{IDENTITY_SERVICE_URL}/auth/validate",
                headers={"Authorization": f"Bearer {token.credentials}"},
                timeout=5.0
            )
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Token validated for user: {user_data.get('user_id', 'unknown')}")
                return user_data
            
            elif response.status_code == 401:
                logger.warning("Invalid or expired token provided")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            else:
                logger.error(f"Identity service returned unexpected status: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token validation failed",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
    except httpx.TimeoutException:
        logger.error("Timeout calling Identity Service for token validation")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable"
        )
    except httpx.RequestError as e:
        logger.error(f"Network error calling Identity Service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Pydantic models
class NotificationRequest(BaseModel):
    type: str  # email, sms, push, in_app
    to: str
    subject: Optional[str] = None
    message: str
    template_id: Optional[str] = None
    variables: Optional[dict] = {}

class MessageRequest(BaseModel):
    conversation_id: Optional[str] = None
    to_user_id: str
    message: str
    message_type: str = "text"

# Helper functions for health check
def get_uptime():
    """Get service uptime in seconds"""
    return int(time.time() - start_time)

def get_memory_usage():
    """Get memory usage in MB"""
    process = psutil.Process(os.getpid())
    return round(process.memory_info().rss / 1024 / 1024, 2)

def get_active_connections():
    """Get active connection count (placeholder)"""
    return 0  # TODO: Implement actual connection tracking

# Standard health check endpoint
@app.get("/health")
async def health_check():
    """Standard health check following service integration patterns"""
    health_status = {
        "service": SERVICE_NAME,
        "status": "healthy",
        "version": SERVICE_VERSION,
        "port": SERVICE_PORT,
        "dependencies": {},
        "metrics": {
            "uptime_seconds": get_uptime(),
            "active_connections": get_active_connections(),
            "memory_usage_mb": get_memory_usage()
        }
    }
    
    # Check Redis connection
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6382/0")
        redis_client = redis.from_url(redis_url)
        await redis_client.ping()
        await redis_client.close()
        health_status["dependencies"]["redis"] = "healthy"
    except Exception:
        health_status["dependencies"]["redis"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Identity Service
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{IDENTITY_SERVICE_URL}/health")
            if response.status_code == 200:
                health_status["dependencies"]["identity-service"] = "healthy"
            else:
                raise Exception("Identity service returned non-200")
    except Exception:
        health_status["dependencies"]["identity-service"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Celery workers (placeholder)
    try:
        # TODO: Implement actual Celery worker health check
        health_status["dependencies"]["celery-workers"] = "not-implemented"
    except Exception:
        health_status["dependencies"]["celery-workers"] = "unhealthy"
        health_status["status"] = "degraded"
    
    return health_status

# Notification endpoints
@app.post("/api/v1/notifications")
async def send_notification(
    notification: NotificationRequest,
    current_user: dict = Depends(validate_jwt_token)
):
    """Send a notification via email, SMS, push, or in-app"""
    from tasks.notification_tasks import send_notification as send_notification_task
    from models import Notification as DBNotification, NotificationChannel, NotificationStatus as DBNotificationStatus
    import uuid
    from datetime import datetime
    
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    
    try:
        # Validate notification channel
        try:
            channel = NotificationChannel(notification.type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid notification type: {notification.type}"
            )
        
        # Create notification record in database
        async with get_db_session() as session:
            db_notification = DBNotification(
                user_id=uuid.UUID(user_id),
                channel=channel,
                subject=notification.subject,
                content=notification.message,
                recipient=notification.to,
                template_id=uuid.UUID(notification.template_id) if notification.template_id else None,
                data=notification.variables or {},
                status=DBNotificationStatus.PENDING,
                priority="normal"
            )
            
            session.add(db_notification)
            await session.commit()
            await session.refresh(db_notification)
            
            notification_id = str(db_notification.id)
        
        # Send notification via Celery task
        task_result = send_notification_task.apply_async(
            args=(
                notification.type,
                notification.to,
                notification.message,
                notification.subject,
                notification.template_id,
                notification.variables,
                {"sent_by": user_id, "organization_id": organization_id},
                notification_id
            )
        )
        
        return {
            "notification_id": notification_id,
            "task_id": task_result.id,
            "status": "queued",
            "channel": notification.type,
            "recipient": notification.to,
            "sent_by": user_id,
            "organization": organization_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/notifications/unread")
async def get_unread_notifications(
    current_user: dict = Depends(validate_jwt_token),
    limit: int = 50
):
    """Get unread notifications for the authenticated user"""
    from providers.in_app import InAppProvider
    
    user_id = current_user["user_id"]
    
    try:
        # Use in-app provider to get unread notifications
        in_app_provider = InAppProvider({"enabled": True})
        notifications = await in_app_provider.get_unread_notifications(user_id, limit)
        unread_count = await in_app_provider.get_unread_count(user_id)
        
        return {
            "notifications": notifications,
            "unread_count": unread_count,
            "user_id": user_id,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Failed to get unread notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Additional notification endpoints
@app.put("/api/v1/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(validate_jwt_token)
):
    """Mark a notification as read"""
    from providers.in_app import InAppProvider
    
    user_id = current_user["user_id"]
    
    try:
        in_app_provider = InAppProvider({"enabled": True})
        success = await in_app_provider.mark_as_read(notification_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"status": "success", "notification_id": notification_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to mark notification as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/notifications/read-all")
async def mark_all_notifications_read(
    current_user: dict = Depends(validate_jwt_token)
):
    """Mark all notifications as read for the user"""
    from providers.in_app import InAppProvider
    
    user_id = current_user["user_id"]
    
    try:
        in_app_provider = InAppProvider({"enabled": True})
        marked_count = await in_app_provider.mark_all_as_read(user_id)
        
        return {
            "status": "success",
            "marked_count": marked_count,
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"Failed to mark all notifications as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/notifications/history")
async def get_notification_history(
    current_user: dict = Depends(validate_jwt_token),
    page: int = 1,
    limit: int = 20
):
    """Get notification history for the user"""
    user_id = current_user["user_id"]
    
    try:
        async with get_db_session() as session:
            offset = (page - 1) * limit
            
            result = await session.execute(
                """
                SELECT id, channel, subject, content, status, created_at, sent_at, is_read
                FROM notifications
                WHERE user_id = :user_id
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
                """,
                {"user_id": user_id, "limit": limit, "offset": offset}
            )
            
            notifications = []
            for row in result.fetchall():
                notifications.append({
                    "id": str(row.id),
                    "channel": row.channel,
                    "subject": row.subject,
                    "content": row.content[:200] + "..." if len(row.content) > 200 else row.content,
                    "status": row.status,
                    "created_at": row.created_at.isoformat(),
                    "sent_at": row.sent_at.isoformat() if row.sent_at else None,
                    "is_read": row.is_read
                })
            
            return {
                "notifications": notifications,
                "page": page,
                "limit": limit,
                "user_id": user_id
            }
            
    except Exception as e:
        logger.error(f"Failed to get notification history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/notifications/bulk")
async def send_bulk_notifications(
    notifications: List[NotificationRequest],
    current_user: dict = Depends(validate_jwt_token)
):
    """Send multiple notifications in bulk"""
    from tasks.notification_tasks import send_bulk_notifications as send_bulk_task
    
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    
    try:
        # Validate bulk request size
        if len(notifications) > 1000:
            raise HTTPException(
                status_code=400,
                detail="Maximum 1000 notifications allowed per bulk request"
            )
        
        # Prepare notification data for Celery task
        notification_data = []
        for notification in notifications:
            notification_data.append({
                "channel": notification.type,
                "recipient": notification.to,
                "content": notification.message,
                "subject": notification.subject,
                "template_id": notification.template_id,
                "template_data": notification.variables,
                "metadata": {"sent_by": user_id, "organization_id": organization_id}
            })
        
        # Send bulk notifications
        task_result = send_bulk_task.apply_async(args=(notification_data,))
        
        return {
            "task_id": task_result.id,
            "status": "queued",
            "notification_count": len(notifications),
            "sent_by": user_id,
            "organization": organization_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send bulk notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Messaging endpoints
@app.post("/api/v1/messages")
async def send_message(
    message: MessageRequest,
    current_user: dict = Depends(validate_jwt_token)
):
    """Send a message in a conversation"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    
    # TODO: Implement message sending with conversation management
    return {
        "message": "Message sending endpoint - TODO: implement",
        "conversation_id": message.conversation_id,
        "recipient": message.to_user_id,
        "sender": user_id,
        "organization": organization_id
    }

@app.get("/api/v1/conversations")
async def list_conversations(
    current_user: dict = Depends(validate_jwt_token)
):
    """List conversations for the authenticated user"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    
    # TODO: Implement conversation listing
    return {
        "message": f"Conversations for user {user_id} - TODO: implement",
        "user_id": user_id,
        "organization": organization_id
    }

@app.get("/api/v1/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(validate_jwt_token)
):
    """Get conversation history"""
    user_id = current_user["user_id"]
    user_roles = current_user.get("roles", [])
    
    # TODO: Implement conversation history retrieval with access control
    return {
        "message": f"Conversation {conversation_id} history - TODO: implement",
        "conversation_id": conversation_id,
        "requested_by": user_id,
        "user_roles": user_roles
    }

# Template management
@app.post("/api/v1/templates")
async def create_template(
    template_data: dict,
    current_user: dict = Depends(validate_jwt_token)
):
    """Create a notification template"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    user_roles = current_user.get("roles", [])
    
    # TODO: Implement template creation and management with role checks
    return {
        "message": "Template creation endpoint - TODO: implement",
        "created_by": user_id,
        "organization": organization_id,
        "user_roles": user_roles
    }

@app.get("/api/v1/templates")
async def list_templates(
    current_user: dict = Depends(validate_jwt_token),
    category_id: Optional[str] = None,
    channel: Optional[str] = None,
    language: Optional[str] = "en"
):
    """List available notification templates"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    
    try:
        async with get_db_session() as session:
            query = """
                SELECT t.id, t.name, t.subject, t.channel, t.language, t.version, t.is_active,
                       c.name as category_name, t.created_at, t.updated_at
                FROM notification_templates t
                LEFT JOIN notification_categories c ON t.category_id = c.id
                WHERE t.is_active = true
            """
            params = {}
            
            if category_id:
                query += " AND t.category_id = :category_id"
                params["category_id"] = category_id
            
            if channel:
                query += " AND t.channel = :channel"
                params["channel"] = channel
            
            if language:
                query += " AND t.language = :language"
                params["language"] = language
            
            query += " ORDER BY t.name, t.version DESC"
            
            result = await session.execute(query, params)
            
            templates = []
            for row in result.fetchall():
                templates.append({
                    "id": str(row.id),
                    "name": row.name,
                    "subject": row.subject,
                    "channel": row.channel,
                    "language": row.language,
                    "version": row.version,
                    "category": row.category_name,
                    "is_active": row.is_active,
                    "created_at": row.created_at.isoformat(),
                    "updated_at": row.updated_at.isoformat()
                })
            
            return {
                "templates": templates,
                "total": len(templates),
                "filters": {
                    "category_id": category_id,
                    "channel": channel,
                    "language": language
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/templates/{template_id}")
async def get_template(
    template_id: str,
    current_user: dict = Depends(validate_jwt_token)
):
    """Get specific template details"""
    try:
        async with get_db_session() as session:
            result = await session.execute(
                """
                SELECT t.id, t.name, t.subject, t.content, t.channel, t.language, 
                       t.variables, t.version, t.is_active, c.name as category_name,
                       t.created_at, t.updated_at
                FROM notification_templates t
                LEFT JOIN notification_categories c ON t.category_id = c.id
                WHERE t.id = :template_id
                """,
                {"template_id": template_id}
            )
            
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Template not found")
            
            return {
                "id": str(row.id),
                "name": row.name,
                "subject": row.subject,
                "content": row.content,
                "channel": row.channel,
                "language": row.language,
                "variables": row.variables or {},
                "version": row.version,
                "category": row.category_name,
                "is_active": row.is_active,
                "created_at": row.created_at.isoformat(),
                "updated_at": row.updated_at.isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/templates/render")
async def render_template(
    template_id: str,
    variables: Dict[str, Any],
    channel: Optional[str] = None,
    current_user: dict = Depends(validate_jwt_token)
):
    """Render template with provided variables"""
    from template_engine import template_engine
    from models import NotificationChannel
    
    try:
        channel_enum = NotificationChannel(channel) if channel else None
        
        result = await template_engine.render_template(
            template_id,
            variables,
            channel_enum
        )
        
        return {
            "template_id": template_id,
            "rendered": result,
            "variables_used": variables,
            "channel": channel
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to render template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/templates/preview")
async def preview_template(
    template_content: str,
    subject: str,
    variables: Dict[str, Any],
    channel: Optional[str] = None,
    current_user: dict = Depends(validate_jwt_token)
):
    """Preview template rendering without saving"""
    from template_engine import template_engine
    from models import NotificationChannel
    
    try:
        channel_enum = NotificationChannel(channel) if channel else None
        
        result = await template_engine.preview_template(
            template_content,
            subject,
            variables,
            channel_enum
        )
        
        return {
            "preview": result,
            "variables_used": variables,
            "channel": channel
        }
        
    except Exception as e:
        logger.error(f"Failed to preview template: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/templates/categories")
async def list_template_categories(
    current_user: dict = Depends(validate_jwt_token)
):
    """List all notification categories"""
    try:
        async with get_db_session() as session:
            result = await session.execute(
                """
                SELECT id, name, description, default_enabled, created_at
                FROM notification_categories
                ORDER BY name
                """
            )
            
            categories = []
            for row in result.fetchall():
                categories.append({
                    "id": str(row.id),
                    "name": row.name,
                    "description": row.description,
                    "default_enabled": row.default_enabled,
                    "created_at": row.created_at.isoformat()
                })
            
            return {"categories": categories}
            
    except Exception as e:
        logger.error(f"Failed to list categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Queue status
@app.get("/api/v1/queue/status")
async def queue_status(
    current_user: dict = Depends(validate_jwt_token)
):
    """Get background job queue status"""
    user_id = current_user["user_id"]
    user_roles = current_user.get("roles", [])
    
    # TODO: Implement Celery queue monitoring with admin role check
    return {
        "message": "Queue status endpoint - TODO: implement",
        "requested_by": user_id,
        "user_roles": user_roles
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=os.getenv("DEBUG") == "true",
        log_level="info"
    )