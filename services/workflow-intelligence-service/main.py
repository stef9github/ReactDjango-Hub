"""
Workflow & Intelligence Service - Process Automation + AI
Port: 8004
"""
import os
import time
import psutil
import httpx
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import logging

# Add logging for debugging
logger = logging.getLogger(__name__)

# Service configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "workflow-intelligence-service")
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 8004))
IDENTITY_SERVICE_URL = os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8001")
start_time = time.time()

# JWT Authentication setup
security = HTTPBearer()

app = FastAPI(
    title=f"{SERVICE_NAME.title().replace('-', ' ')} API",
    description="Microservice for business process automation with AI-powered insights",
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

# Pydantic models
class WorkflowCreateRequest(BaseModel):
    definition_id: str  # e.g., "approval-workflow", "onboarding-process"
    entity_id: str      # e.g., "request-123", "employee-456"
    context: Optional[Dict[str, Any]] = {}

class WorkflowTransitionRequest(BaseModel):
    action: str
    data: Optional[Dict[str, Any]] = {}

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
class WorkflowCreateRequest(BaseModel):
    definition_id: str  # e.g., "approval-workflow", "onboarding-process"
    entity_id: str      # e.g., "request-123", "employee-456"
    context: Optional[Dict[str, Any]] = {}

class WorkflowTransitionRequest(BaseModel):
    action: str
    data: Optional[Dict[str, Any]] = {}

class AIRequest(BaseModel):
    text: str
    task_type: str  # "summarize", "suggest", "analyze"
    context: Optional[Dict[str, Any]] = {}

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

async def check_ai_service_status():
    """Check AI service availability"""
    ai_status = {}
    
    # Check OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {openai_key}"}
                )
                ai_status["openai"] = "healthy" if response.status_code == 200 else "unhealthy"
        except Exception:
            ai_status["openai"] = "unhealthy"
    else:
        ai_status["openai"] = "not-configured"
    
    # Check Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            # Anthropic doesn't have a simple health endpoint, so we just check if key exists
            ai_status["anthropic"] = "configured" if anthropic_key.startswith("sk-") else "invalid-key"
        except Exception:
            ai_status["anthropic"] = "unhealthy"
    else:
        ai_status["anthropic"] = "not-configured"
    
    return ai_status

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
    
    # Check database connection
    try:
        from database import get_database_info
        db_info = get_database_info()
        health_status["dependencies"]["database"] = db_info
        
        if db_info.get("status") != "healthy":
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["dependencies"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Check Redis connection
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6383/0")
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
    
    # Check AI services
    try:
        ai_status = await check_ai_service_status()
        health_status["dependencies"]["ai-services"] = ai_status
        
        # If no AI services are configured or healthy, mark as degraded
        if all(status in ["not-configured", "unhealthy"] for status in ai_status.values()):
            health_status["status"] = "degraded"
    except Exception:
        health_status["dependencies"]["ai-services"] = {"error": "health-check-failed"}
        health_status["status"] = "degraded"
    
    return health_status

# Workflow management endpoints
@app.post("/api/v1/workflows")
async def create_workflow(
    workflow: WorkflowCreateRequest,
    current_user: dict = Depends(validate_jwt_token)
):
    """Create a new workflow instance"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    user_roles = current_user.get("roles", [])
    
    # TODO: Implement workflow instance creation
    return {
        "message": "Workflow creation endpoint - TODO: implement",
        "definition_id": workflow.definition_id,
        "entity_id": workflow.entity_id,
        "workflow_id": "generated-uuid",  # TODO: generate actual UUID
        "created_by": user_id,
        "organization": organization_id
    }

@app.get("/api/v1/workflows/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    current_user: dict = Depends(validate_jwt_token)
):
    """Get current workflow status and state"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    
    # TODO: Implement workflow status retrieval
    return {
        "message": f"Workflow {workflow_id} status - TODO: implement",
        "current_state": "pending",
        "next_actions": [],
        "requested_by": user_id,
        "organization": organization_id
    }

@app.patch("/api/v1/workflows/{workflow_id}/next")
async def advance_workflow(
    workflow_id: str, 
    transition: WorkflowTransitionRequest,
    current_user: dict = Depends(validate_jwt_token)
):
    """Advance workflow to next state"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    user_roles = current_user.get("roles", [])
    
    # TODO: Implement state machine transition logic
    return {
        "message": f"Advance workflow {workflow_id} - TODO: implement",
        "action": transition.action,
        "previous_state": "current",
        "new_state": "next",
        "updated_by": user_id,
        "organization": organization_id
    }

@app.get("/api/v1/workflows/user/{requested_user_id}")
async def get_user_workflows(
    requested_user_id: str,
    current_user: dict = Depends(validate_jwt_token)
):
    """Get all workflows for a user"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    user_roles = current_user.get("roles", [])
    
    # TODO: Implement user workflow listing with authorization checks
    # Users can only see their own workflows unless they have admin role
    if requested_user_id != user_id and "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Cannot view other users' workflows"
        )
    
    return {
        "message": f"Workflows for user {requested_user_id} - TODO: implement",
        "requested_by": user_id,
        "organization": organization_id
    }

# AI assistance endpoints
@app.post("/api/v1/ai/summarize")
async def ai_summarize(
    request: AIRequest,
    current_user: dict = Depends(validate_jwt_token)
):
    """AI-powered text summarization"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    
    # TODO: Implement AI summarization using Claude/OpenAI
    return {
        "message": "AI summarization endpoint - TODO: implement",
        "original_length": len(request.text),
        "summary": "AI-generated summary will be here",
        "confidence": 0.95,
        "requested_by": user_id,
        "organization": organization_id
    }

@app.post("/api/v1/ai/suggest")
async def ai_suggest(
    request: AIRequest,
    current_user: dict = Depends(validate_jwt_token)
):
    """Smart form suggestions and pre-filling"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    
    # TODO: Implement AI-powered form suggestions
    return {
        "message": "AI suggestions endpoint - TODO: implement",
        "suggestions": [],
        "confidence": 0.90,
        "requested_by": user_id,
        "organization": organization_id
    }

@app.post("/api/v1/ai/analyze")
async def ai_analyze(
    request: AIRequest,
    current_user: dict = Depends(validate_jwt_token)
):
    """AI-powered content analysis"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    
    # TODO: Implement AI content analysis
    return {
        "message": "AI analysis endpoint - TODO: implement",
        "analysis": {},
        "insights": [],
        "requested_by": user_id,
        "organization": organization_id
    }

# Workflow definitions
@app.get("/api/v1/definitions")
async def list_workflow_definitions(
    current_user: dict = Depends(validate_jwt_token)
):
    """List available workflow definitions"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    
    # TODO: Implement workflow definition listing with organization filtering
    return {
        "message": "Workflow definitions - TODO: implement",
        "definitions": [
            {"id": "approval-workflow", "name": "Document Approval Process"},
            {"id": "onboarding-process", "name": "Employee Onboarding"},
            {"id": "project-lifecycle", "name": "Project Management Workflow"}
        ],
        "requested_by": user_id,
        "organization": organization_id
    }

@app.post("/api/v1/definitions")
async def create_workflow_definition(
    definition: dict,
    current_user: dict = Depends(validate_jwt_token)
):
    """Create a new workflow definition"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    user_roles = current_user.get("roles", [])
    
    # TODO: Implement workflow definition creation with admin role check
    if "admin" not in user_roles and "workflow_admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Insufficient permissions to create workflow definitions"
        )
    
    return {
        "message": "Create workflow definition - TODO: implement",
        "created_by": user_id,
        "organization": organization_id
    }

# SLA and monitoring
@app.get("/api/v1/workflows/stats")
async def workflow_stats(
    current_user: dict = Depends(validate_jwt_token)
):
    """Get workflow system statistics"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    user_roles = current_user.get("roles", [])
    
    # TODO: Implement workflow statistics with organization filtering
    return {
        "active_workflows": 0,
        "completed_today": 0,
        "overdue_workflows": 0,
        "average_completion_time": "0 hours",
        "requested_by": user_id,
        "organization": organization_id
    }

@app.get("/api/v1/workflows/sla-check")
async def sla_compliance_check(
    current_user: dict = Depends(validate_jwt_token)
):
    """Check SLA compliance for active workflows"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    user_roles = current_user.get("roles", [])
    
    # TODO: Implement SLA monitoring with organization filtering
    return {
        "message": "SLA compliance check - TODO: implement",
        "requested_by": user_id,
        "organization": organization_id,
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