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
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    
    # TODO: Implement notification sending with Celery background tasks
    return {
        "message": "Notification sending endpoint - TODO: implement",
        "notification_type": notification.type,
        "recipient": notification.to,
        "template": notification.template_id,
        "sent_by": user_id,
        "organization": organization_id
    }

@app.get("/api/v1/notifications/unread")
async def get_unread_notifications(
    current_user: dict = Depends(validate_jwt_token)
):
    """Get unread notifications for the authenticated user"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    
    # TODO: Implement unread notifications retrieval
    return {
        "message": f"Unread notifications for user {user_id} - TODO: implement",
        "user_id": user_id,
        "organization": organization_id
    }

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
    current_user: dict = Depends(validate_jwt_token)
):
    """List available notification templates"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    
    # TODO: Implement template listing with organization filtering
    return {
        "message": "Template listing endpoint - TODO: implement",
        "requested_by": user_id,
        "organization": organization_id
    }

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