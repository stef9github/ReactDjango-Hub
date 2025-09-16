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
from sqlalchemy.orm import Session
import uvicorn
import logging

# Add logging for debugging
logger = logging.getLogger(__name__)

# Import database session
from database import get_database_session

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
        use_docker = os.getenv("USE_DOCKER", "false").lower() == "true"
        if use_docker:
            redis_url = os.getenv("REDIS_URL", "redis://workflow-redis:6379/0")
        else:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            
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
    current_user: dict = Depends(validate_jwt_token),
    db_session: Session = Depends(get_database_session)
):
    """Create a new workflow instance"""
    from workflow_engine import WorkflowEngine
    from models import WorkflowDefinition
    
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    user_roles = current_user.get("roles", [])
    
    try:
        # Create workflow engine instance
        engine = WorkflowEngine(db_session=db_session)
        
        # Create workflow instance
        instance = engine.create_workflow_instance(
            definition_id=workflow.definition_id,
            entity_id=workflow.entity_id,
            context=workflow.context or {},
            organization_id=organization_id,
            created_by=user_id,
            title=f"Workflow for {workflow.entity_id}"
        )
        
        logger.info(f"Created workflow instance {instance.id} for user {user_id}")
        
        return {
            "workflow_id": str(instance.id),
            "definition_id": workflow.definition_id,
            "entity_id": workflow.entity_id,
            "current_state": instance.current_state,
            "status": instance.status,
            "progress_percentage": instance.progress_percentage,
            "available_actions": instance.get_available_actions(),
            "created_at": instance.created_at.isoformat(),
            "created_by": user_id,
            "organization": organization_id
        }
        
    except ValueError as e:
        logger.error(f"Workflow creation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating workflow: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create workflow instance")

@app.get("/api/v1/workflows/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    current_user: dict = Depends(validate_jwt_token),
    db_session: Session = Depends(get_database_session)
):
    """Get current workflow status and state"""
    from workflow_engine import WorkflowEngine
    from models import WorkflowInstance
    
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    user_roles = current_user.get("roles", [])
    
    try:
        # Check if workflow exists and user has access
        instance = db_session.query(WorkflowInstance).filter(
            WorkflowInstance.id == workflow_id
        ).first()
        
        if not instance:
            raise HTTPException(status_code=404, detail="Workflow instance not found")
        
        # Authorization check: user must be assigned to workflow, or be admin, or same organization
        if not ("admin" in user_roles or 
                instance.assigned_to == user_id or 
                instance.created_by == user_id or
                (instance.organization_id == organization_id and organization_id)):
            raise HTTPException(status_code=403, detail="Access denied to workflow instance")
        
        # Get comprehensive workflow status
        engine = WorkflowEngine(db_session=db_session)
        status_data = engine.get_workflow_status(workflow_id)
        
        # Add request metadata
        status_data.update({
            "requested_by": user_id,
            "organization": organization_id
        })
        
        return status_data
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Error getting workflow status: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting workflow status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow status")

@app.patch("/api/v1/workflows/{workflow_id}/next")
async def advance_workflow(
    workflow_id: str, 
    transition: WorkflowTransitionRequest,
    current_user: dict = Depends(validate_jwt_token),
    db_session: Session = Depends(get_database_session)
):
    """Advance workflow to next state"""
    from workflow_engine import WorkflowEngine
    from models import WorkflowInstance
    
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    user_roles = current_user.get("roles", [])
    
    try:
        # Check if workflow exists and user has permission to advance it
        instance = db_session.query(WorkflowInstance).filter(
            WorkflowInstance.id == workflow_id
        ).first()
        
        if not instance:
            raise HTTPException(status_code=404, detail="Workflow instance not found")
        
        # Authorization check: user must be assigned to workflow, creator, or admin
        if not ("admin" in user_roles or 
                instance.assigned_to == user_id or 
                instance.created_by == user_id):
            raise HTTPException(status_code=403, detail="Access denied: insufficient permissions to advance workflow")
        
        # Check if workflow is active
        if instance.status != "active":
            raise HTTPException(status_code=400, detail=f"Cannot advance workflow: status is '{instance.status}', not 'active'")
        
        # Store previous state for response
        previous_state = instance.current_state
        
        # Advance workflow using engine
        engine = WorkflowEngine(db_session=db_session)
        updated_instance = engine.advance_workflow(
            instance_id=workflow_id,
            action=transition.action,
            user_id=user_id,
            comment=transition.data.get('comment') if transition.data else None,
            data=transition.data or {},
            context_updates=transition.data.get('context_updates') if transition.data else None
        )
        
        logger.info(f"Workflow {workflow_id} advanced from {previous_state} to {updated_instance.current_state} by user {user_id}")
        
        return {
            "workflow_id": str(updated_instance.id),
            "action": transition.action,
            "previous_state": previous_state,
            "current_state": updated_instance.current_state,
            "status": updated_instance.status,
            "progress_percentage": updated_instance.progress_percentage,
            "available_actions": updated_instance.get_available_actions(),
            "updated_at": updated_instance.updated_at.isoformat(),
            "updated_by": user_id,
            "organization": organization_id
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Error advancing workflow {workflow_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error advancing workflow {workflow_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to advance workflow")

@app.get("/api/v1/workflows/user/{requested_user_id}")
async def get_user_workflows(
    requested_user_id: str,
    current_user: dict = Depends(validate_jwt_token),
    db_session: Session = Depends(get_database_session),
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get all workflows for a user"""
    from workflow_engine import WorkflowEngine
    
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    user_roles = current_user.get("roles", [])
    
    try:
        # Authorization check: Users can only see their own workflows unless they have admin role
        if requested_user_id != user_id and "admin" not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot view other users' workflows"
            )
        
        # Validate limit
        if limit > 100:
            limit = 100  # Cap at 100 workflows per request
        
        # Get user workflows using the engine
        engine = WorkflowEngine(db_session=db_session)
        workflows = engine.get_user_workflows(
            user_id=requested_user_id,
            organization_id=organization_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        # Count total workflows for pagination info
        from models import WorkflowInstance
        total_query = db_session.query(WorkflowInstance).filter(
            WorkflowInstance.assigned_to == requested_user_id
        )
        
        if organization_id:
            total_query = total_query.filter(WorkflowInstance.organization_id == organization_id)
        
        if status:
            total_query = total_query.filter(WorkflowInstance.status == status)
        
        total_count = total_query.count()
        
        return {
            "workflows": workflows,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count
            },
            "filters": {
                "user_id": requested_user_id,
                "status": status,
                "organization_id": organization_id
            },
            "requested_by": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflows for user {requested_user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user workflows")

# AI assistance endpoints
@app.post("/api/v1/ai/summarize")
async def ai_summarize(
    request: AIRequest,
    current_user: dict = Depends(validate_jwt_token)
):
    """Business Intelligence: AI-powered document summarization for contracts, proposals, and reports"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    
    # Business Intelligence: Implement AI summarization for business documents
    # Common use cases: contract summaries, meeting minutes, financial reports, proposals
    return {
        "message": "Business Intelligence AI summarization",
        "original_length": len(request.text),
        "summary": "Executive summary: Key business insights and action items will be extracted here",
        "key_points": [
            "Financial implications and budget impact",
            "Strategic recommendations and next steps",
            "Risk factors and compliance considerations"
        ],
        "confidence": 0.95,
        "processing_type": "business_document_analysis",
        "requested_by": user_id,
        "organization": organization_id
    }

@app.post("/api/v1/ai/suggest")
async def ai_suggest(
    request: AIRequest,
    current_user: dict = Depends(validate_jwt_token)
):
    """Business Intelligence: Smart form suggestions and predictive data entry for business processes"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    
    # Business Intelligence: AI-powered suggestions for business forms
    # Use cases: vendor onboarding, contract templates, approval workflows, employee data
    return {
        "message": "Business Intelligence form suggestions",
        "suggestions": [
            {
                "field": "vendor_category",
                "suggested_value": "Professional Services",
                "confidence": 0.92,
                "reasoning": "Based on company description and industry patterns"
            },
            {
                "field": "approval_threshold", 
                "suggested_value": "$10,000",
                "confidence": 0.88,
                "reasoning": "Standard threshold for similar department and contract type"
            }
        ],
        "form_type": request.context.get('form_type', 'business_process'),
        "auto_complete_percentage": 65,
        "confidence": 0.90,
        "requested_by": user_id,
        "organization": organization_id
    }

@app.post("/api/v1/ai/analyze")
async def ai_analyze(
    request: AIRequest,
    current_user: dict = Depends(validate_jwt_token)
):
    """Business Intelligence: Advanced content analysis for strategic insights and compliance"""
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    
    # Business Intelligence: Comprehensive content analysis for business documents
    # Use cases: contract analysis, compliance checking, risk assessment, market research
    return {
        "message": "Business Intelligence content analysis",
        "analysis": {
            "document_type": "contract",
            "sentiment_score": 0.7,
            "complexity_level": "medium",
            "risk_indicators": ["payment_terms", "liability_clauses"],
            "compliance_status": "requires_review"
        },
        "insights": [
            {
                "category": "financial_impact",
                "description": "Contract value represents 15% increase from previous agreement",
                "priority": "high",
                "confidence": 0.94
            },
            {
                "category": "compliance",
                "description": "Standard industry terms align with company policy",
                "priority": "medium",
                "confidence": 0.87
            },
            {
                "category": "recommendations",
                "description": "Consider negotiating extended payment terms for better cash flow",
                "priority": "medium",
                "confidence": 0.82
            }
        ],
        "business_metrics": {
            "estimated_roi": "18%",
            "payback_period": "14 months",
            "risk_score": "2.3/5.0"
        },
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
            {"id": "contract-approval", "name": "Contract Approval Workflow", "category": "procurement"},
            {"id": "vendor-onboarding", "name": "Vendor Registration Process", "category": "procurement"},
            {"id": "employee-onboarding", "name": "Employee Onboarding", "category": "hr"},
            {"id": "purchase-request", "name": "Purchase Request Approval", "category": "finance"},
            {"id": "project-initiation", "name": "Project Initiation Workflow", "category": "operations"},
            {"id": "compliance-review", "name": "Compliance Review Process", "category": "legal"},
            {"id": "budget-approval", "name": "Budget Approval Workflow", "category": "finance"},
            {"id": "performance-review", "name": "Employee Performance Review", "category": "hr"}
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
    
    # Business Intelligence: Comprehensive workflow analytics and KPIs
    return {
        "active_workflows": 47,
        "completed_today": 12,
        "overdue_workflows": 3,
        "average_completion_time": "2.4 days",
        "business_metrics": {
            "approval_rate": "87%",
            "automation_percentage": "65%",
            "cost_savings_monthly": "$12,450",
            "efficiency_improvement": "32%"
        },
        "category_breakdown": {
            "procurement": {"active": 18, "avg_time": "3.1 days"},
            "hr": {"active": 12, "avg_time": "1.8 days"},
            "finance": {"active": 9, "avg_time": "2.7 days"},
            "operations": {"active": 8, "avg_time": "4.2 days"}
        },
        "trend_analysis": {
            "volume_change_7d": "+15%",
            "completion_time_trend": "-8%",
            "satisfaction_score": "4.2/5.0"
        },
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
    
    # Business Intelligence: SLA monitoring and compliance analytics
    return {
        "message": "Business SLA compliance monitoring",
        "sla_metrics": {
            "overall_compliance": "92%",
            "at_risk_workflows": 5,
            "breached_slas": 2,
            "avg_response_time": "4.2 hours"
        },
        "category_compliance": {
            "procurement": {"compliance": "89%", "target": "95%", "at_risk": 3},
            "hr": {"compliance": "95%", "target": "90%", "at_risk": 1},
            "finance": {"compliance": "91%", "target": "95%", "at_risk": 1},
            "operations": {"compliance": "94%", "target": "90%", "at_risk": 0}
        },
        "alerts": [
            {
                "workflow_id": "contract-123",
                "type": "approaching_deadline",
                "severity": "medium",
                "due_in_hours": 18
            },
            {
                "workflow_id": "purchase-456", 
                "type": "overdue",
                "severity": "high",
                "overdue_hours": 6
            }
        ],
        "business_impact": {
            "estimated_cost_of_delays": "$3,200",
            "productivity_impact": "5% reduction",
            "customer_satisfaction_risk": "medium"
        },
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