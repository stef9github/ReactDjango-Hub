"""
Content Service - Document Management, Search & Audit
Port: 8002
"""
import os
import time
import logging
import psutil
import httpx
from contextlib import asynccontextmanager
from typing import List
from uuid import UUID

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

# Import database and models
from database import (
    db, get_db_session, init_database, close_database, check_database_health
)
from models import Document
from repositories import DocumentRepository, AuditRepository
from schemas import (
    DocumentCreate, DocumentResponse, DocumentListResponse, 
    DocumentDetailResponse, ErrorResponse, PaginationParams
)

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Service configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "content-service")
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 8002))
IDENTITY_SERVICE_URL = os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8001")
start_time = time.time()

# JWT Authentication setup
security = HTTPBearer()


# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info(f"Starting {SERVICE_NAME} v{SERVICE_VERSION}")
    
    # Initialize database
    try:
        await init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down service")
    await close_database()


# Standard FastAPI app configuration
app = FastAPI(
    title=f"{SERVICE_NAME.title().replace('-', ' ')} API",
    description="Microservice for document management, search, and audit",
    version=SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS middleware - configured for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper functions for health check
def get_uptime():
    return int(time.time() - start_time)

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return round(process.memory_info().rss / 1024 / 1024, 2)

def get_active_connections():
    return 0  # TODO: Implement actual connection tracking

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
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6381/0")
        import redis.asyncio as redis
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

    # Check Database
    try:
        db_healthy = await check_database_health()
        health_status["dependencies"]["database"] = "healthy" if db_healthy else "unhealthy"
        if not db_healthy:
            health_status["status"] = "degraded"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["dependencies"]["database"] = "unhealthy"
        health_status["status"] = "degraded"

    return health_status


async def validate_jwt_token(token: HTTPBearer = Depends(security)):
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


async def get_current_user(current_user: dict = Depends(validate_jwt_token)):
    """Get current authenticated user from JWT token."""
    return {
        "id": UUID(current_user["user_id"]),  # Convert string UUID to UUID object
        "organization_id": UUID(current_user["organization_id"]),
        "email": current_user.get("email"),
        "roles": current_user.get("roles", [])
    }


# Document management endpoints
@app.get("/api/v1/documents", response_model=DocumentListResponse)
async def list_documents(
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """List documents with pagination and filtering."""
    try:
        doc_repo = DocumentRepository(session)
        audit_repo = AuditRepository(session)
        
        # Get documents for the user's organization
        documents = await doc_repo.find_by_organization(
            organization_id=current_user["organization_id"],
            limit=pagination.limit,
            offset=pagination.offset,
            status="active"
        )
        
        # Get total count for pagination
        total_count = await doc_repo.count(
            organization_id=current_user["organization_id"],
            status="active"
        )
        
        # Log the access
        await audit_repo.log_action(
            action="read",
            user_id=current_user["id"],
            organization_id=current_user["organization_id"],
            details={"endpoint": "/api/v1/documents", "count": len(documents)}
        )
        
        # Convert to response format
        document_items = []
        for doc in documents:
            document_items.append({
                "id": doc.id,
                "filename": doc.filename,
                "content_type": doc.content_type,
                "file_size": doc.file_size,
                "document_type": doc.document_type,
                "created_at": doc.created_at,
                "created_by": doc.created_by,
                "status": doc.status,
                "title": doc.get_metadata_value("title"),
                "tags": doc.get_metadata_value("tags", []),
                "classification": doc.classification,
                "processing_complete": doc.is_processing_complete(),
                "has_thumbnail": doc.thumbnail_generated,
                "thumbnail_url": f"/api/v1/documents/{doc.id}/thumbnail" if doc.thumbnail_generated else None
            })
        
        return DocumentListResponse(
            documents=document_items,
            pagination={
                "limit": pagination.limit,
                "offset": pagination.offset,
                "total": total_count,
                "has_next": (pagination.offset + pagination.limit) < total_count,
                "has_prev": pagination.offset > 0
            },
            filters_applied={"status": "active"},
            total_size=sum(doc["file_size"] for doc in document_items)
        )
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )


@app.get("/api/v1/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Get detailed document information."""
    try:
        doc_repo = DocumentRepository(session)
        audit_repo = AuditRepository(session)
        
        # Get document with versions
        document = await doc_repo.get_document_with_versions(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check organization access
        if document.organization_id != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Log the access
        await audit_repo.log_action(
            action="read",
            user_id=current_user["id"],
            organization_id=current_user["organization_id"],
            document_id=document.id,
            details={"endpoint": f"/api/v1/documents/{document_id}"}
        )
        
        # Build response
        return DocumentDetailResponse(
            id=document.id,
            filename=document.filename,
            original_filename=document.original_filename,
            content_type=document.content_type,
            file_size=document.file_size,
            file_hash=document.file_hash,
            organization_id=document.organization_id,
            status=document.status,
            document_type=document.document_type,
            metadata={
                "title": document.get_metadata_value("title"),
                "description": document.get_metadata_value("description"),
                "tags": document.get_metadata_value("tags", []),
                "classification": document.classification,
                "author": document.get_metadata_value("author"),
                "department": document.get_metadata_value("department"),
                "custom_fields": document.get_metadata_value("custom_fields", {})
            },
            audit={
                "created_at": document.created_at,
                "created_by": document.created_by,
                "updated_at": document.updated_at,
                "updated_by": document.created_by,  # TODO: track actual updater
                "version": document.current_version
            },
            processing={
                "status": document.processing_status,
                "ocr_completed": document.ocr_completed,
                "thumbnail_generated": document.thumbnail_generated,
                "text_extracted": bool(document.extracted_text),
                "classification_completed": bool(document.document_type),
                "last_processed": None,  # TODO: implement
                "processing_errors": []
            },
            download_url=f"/api/v1/documents/{document.id}/download",
            thumbnail_url=f"/api/v1/documents/{document.id}/thumbnail" if document.thumbnail_generated else None,
            preview_url=f"/api/v1/documents/{document.id}/preview",
            extracted_text=document.extracted_text,
            text_preview=document.extracted_text[:500] + "..." if document.extracted_text and len(document.extracted_text) > 500 else document.extracted_text,
            current_version=document.current_version,
            version_count=len(document.versions),
            permissions={
                "read": True,
                "write": True,  # TODO: implement proper permissions
                "delete": True,
                "share": True,
                "admin": True
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document"
        )


@app.delete("/api/v1/documents/{document_id}")
async def delete_document(
    document_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Soft delete a document."""
    try:
        doc_repo = DocumentRepository(session)
        audit_repo = AuditRepository(session)
        
        # Get document first to verify access
        document = await doc_repo.get_by_id(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check organization access
        if document.organization_id != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Soft delete
        deleted_document = await doc_repo.mark_as_deleted(document_id)
        
        if not deleted_document:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document"
            )
        
        # Log the deletion
        await audit_repo.log_action(
            action="delete",
            user_id=current_user["id"],
            organization_id=current_user["organization_id"],
            document_id=document.id,
            details={
                "filename": document.filename,
                "file_size": document.file_size,
                "soft_delete": True
            }
        )
        
        return {"success": True, "message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


@app.get("/api/v1/documents/{document_id}/audit")
async def get_document_audit_trail(
    document_id: UUID,
    pagination: PaginationParams = Depends(),
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Get audit trail for a document."""
    try:
        doc_repo = DocumentRepository(session)
        audit_repo = AuditRepository(session)
        
        # Verify document exists and user has access
        document = await doc_repo.get_by_id(document_id)
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        if document.organization_id != current_user["organization_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get audit trail
        audit_entries = await audit_repo.get_document_audit_trail(
            document_id=document_id,
            limit=pagination.limit,
            offset=pagination.offset
        )
        
        # Convert to response format
        audit_data = []
        for entry in audit_entries:
            audit_data.append({
                "id": entry.id,
                "action": entry.action,
                "user_id": entry.user_id,
                "created_at": entry.created_at,
                "details": entry.details,
                "ip_address": str(entry.ip_address) if entry.ip_address else None,
                "user_agent": entry.user_agent,
                "execution_time_ms": entry.execution_time_ms
            })
        
        return {
            "document_id": document_id,
            "audit_entries": audit_data,
            "pagination": {
                "limit": pagination.limit,
                "offset": pagination.offset,
                "total": await audit_repo.count(document_id=document_id),
                "has_next": len(audit_entries) == pagination.limit,
                "has_prev": pagination.offset > 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving audit trail for document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit trail"
        )


@app.get("/api/v1/documents/stats")
async def get_document_statistics(
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Get document statistics for the organization."""
    try:
        doc_repo = DocumentRepository(session)
        
        # Get organization statistics
        stats = await doc_repo.get_organization_stats(current_user["organization_id"])
        
        # Get recent documents
        recent_documents = await doc_repo.get_recent_documents(
            organization_id=current_user["organization_id"],
            limit=5
        )
        
        # Convert recent documents to response format
        recent_docs_data = []
        for doc in recent_documents:
            recent_docs_data.append({
                "id": doc.id,
                "filename": doc.filename,
                "content_type": doc.content_type,
                "file_size": doc.file_size,
                "created_at": doc.created_at,
                "created_by": doc.created_by,
                "status": doc.status,
                "title": doc.get_metadata_value("title"),
                "tags": doc.get_metadata_value("tags", []),
                "classification": doc.classification,
                "processing_complete": doc.is_processing_complete(),
                "has_thumbnail": doc.thumbnail_generated,
                "thumbnail_url": f"/api/v1/documents/{doc.id}/thumbnail" if doc.thumbnail_generated else None
            })
        
        return {
            **stats,
            "recent_uploads": recent_docs_data
        }
        
    except Exception as e:
        logger.error(f"Error retrieving document statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


# Placeholder endpoints for future implementation
@app.post("/api/v1/documents")
async def upload_document():
    return {"message": "Document upload endpoint - will be implemented in Week 2"}

@app.post("/api/v1/documents/{doc_id}/process")
async def process_document(doc_id: UUID):
    return {"message": f"Document {doc_id} processing - will be implemented in Week 3"}

@app.get("/api/v1/search")
async def search_documents(q: str):
    return {"message": f"Search '{q}' - will be implemented in Week 3"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=os.getenv("DEBUG") == "true",
        log_level="info"
    )