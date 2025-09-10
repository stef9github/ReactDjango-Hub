"""
Content Service - Document Management, Search & Audit
Port: 8002
"""
import os
import time
import logging
import psutil
import httpx
import aiofiles
import magic
import uuid as uuid_lib
from contextlib import asynccontextmanager
from typing import List, Optional
from uuid import UUID
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

# Import database and models
from database import (
    db, get_db_session, init_database, close_database, check_database_health
)
from models import Document
from repositories import DocumentRepository, AuditRepository, PermissionRepository
from schemas import (
    DocumentCreate, DocumentResponse, DocumentListResponse, 
    DocumentDetailResponse, ErrorResponse, PaginationParams,
    GrantUserPermissionRequest, GrantRolePermissionRequest,
    ShareDocumentRequest, ShareDocumentResponse,
    DocumentPermissionSummary, EffectivePermissionsResponse,
    DocumentAccessCheckRequest, DocumentAccessCheckResponse
)

# Import missing dependencies
import aiofiles.os

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

# File upload configuration
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 50))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
UPLOAD_DIRECTORY = Path(os.getenv("UPLOAD_DIRECTORY", "./uploads"))
STORAGE_DIRECTORY = Path(os.getenv("STORAGE_DIRECTORY", "./storage"))
ALLOWED_CONTENT_TYPES = os.getenv(
    "ALLOWED_CONTENT_TYPES", 
    "application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,image/jpeg,image/png,image/tiff"
).split(",")

# Ensure directories exist
UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
STORAGE_DIRECTORY.mkdir(parents=True, exist_ok=True)

start_time = time.time()

# Connection tracking
_active_connections = 0

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

# Connection tracking middleware
@app.middleware("http")
async def track_connections(request, call_next):
    """Track active connections for health metrics."""
    global _active_connections
    _active_connections += 1
    
    try:
        response = await call_next(request)
        return response
    finally:
        _active_connections -= 1

# Helper functions for health check
def get_uptime():
    return int(time.time() - start_time)

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return round(process.memory_info().rss / 1024 / 1024, 2)

def get_active_connections():
    """Get current active connection count."""
    # Try to get actual FastAPI connection count
    if hasattr(app, '_connection_count'):
        return getattr(app, '_connection_count', 0)
    
    # Fallback to global tracking
    global _active_connections
    return _active_connections

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
        redis_password = os.getenv("REDIS_PASSWORD")
        import redis.asyncio as redis
        
        if redis_password:
            redis_client = redis.from_url(redis_url, password=redis_password)
        else:
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


# =============================================================================
# PERMISSION HELPER FUNCTIONS
# =============================================================================

async def _get_user_permissions(document: Document, current_user: dict, session: AsyncSession) -> dict:
    """Get user's effective permissions for a document."""
    try:
        perm_repo = PermissionRepository(session)
        
        # Owner has all permissions
        if document.created_by == current_user["id"]:
            return {
                "read": True,
                "write": True,
                "delete": True,
                "share": True,
                "admin": True
            }
        
        # Get user roles
        user_roles = current_user.get("roles", [])
        
        # Get effective permissions from database
        effective_perms = await perm_repo.get_user_effective_permissions(
            document_id=document.id,
            user_id=current_user["id"],
            user_roles=user_roles
        )
        
        return effective_perms
        
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        # Default to minimal permissions on error
        return {
            "read": False,
            "write": False,
            "delete": False,
            "share": False,
            "admin": False
        }


# =============================================================================
# DOCUMENT MANAGEMENT ENDPOINTS
# =============================================================================
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
            permissions=await _get_user_permissions(document, current_user, session)
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


# File validation utilities
async def validate_file(file: UploadFile) -> str:
    """Validate uploaded file for security and compliance"""
    # Check file size
    if file.size and file.size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File size ({file.size} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE_MB}MB)"
        )
    
    # Read file content for validation (without loading entire file)
    content_start = await file.read(1024)  # Read first 1KB
    await file.seek(0)  # Reset file pointer
    
    # Validate MIME type using python-magic
    mime_type = magic.from_buffer(content_start, mime=True)
    if mime_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{mime_type}' not allowed. Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
        )
    
    # Basic security checks
    if file.filename:
        # Prevent path traversal
        if ".." in file.filename or "/" in file.filename or "\\" in file.filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Check for dangerous extensions
        dangerous_extensions = [".exe", ".bat", ".cmd", ".scr", ".vbs", ".js"]
        if any(file.filename.lower().endswith(ext) for ext in dangerous_extensions):
            raise HTTPException(status_code=400, detail="Dangerous file type not allowed")
    
    return mime_type


async def save_uploaded_file(file: UploadFile, document_id: UUID) -> tuple[Path, int]:
    """Save uploaded file to storage and return file path and size"""
    # Generate unique filename
    file_extension = Path(file.filename or "unknown").suffix.lower()
    unique_filename = f"{document_id}{file_extension}"
    file_path = STORAGE_DIRECTORY / unique_filename
    
    # Save file
    total_size = 0
    async with aiofiles.open(file_path, 'wb') as f:
        while chunk := await file.read(8192):  # Read in 8KB chunks
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE_BYTES:
                await aiofiles.os.remove(file_path)  # Clean up partial file
                raise HTTPException(
                    status_code=413, 
                    detail=f"File size exceeds maximum allowed size ({MAX_FILE_SIZE_MB}MB)"
                )
            await f.write(chunk)
    
    return file_path, total_size


# Document upload and download endpoints
@app.post("/api/v1/documents")
async def upload_document(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Upload a new document with validation and metadata extraction"""
    try:
        # Validate file
        mime_type = await validate_file(file)
        
        # Generate document ID
        document_id = uuid_lib.uuid4()
        
        # Save file to storage
        file_path, file_size = await save_uploaded_file(file, document_id)
        
        # Generate file hash for duplicate detection
        import hashlib
        file_hash = hashlib.sha256()
        await file.seek(0)  # Reset file pointer
        while chunk := await file.read(8192):
            file_hash.update(chunk)
        await file.seek(0)  # Reset again for saving
        
        file_hash_hex = file_hash.hexdigest()
        
        # Save to database using repository method
        doc_repo = DocumentRepository(db)
        document = await doc_repo.create_document(
            filename=file.filename or "unknown",
            original_filename=file.filename or "unknown", 
            content_type=mime_type,
            file_size=file_size,
            file_hash=file_hash_hex,
            storage_path=str(file_path),
            created_by=current_user["user_id"],
            organization_id=current_user["organization_id"],
            metadata={
                "description": description,
                "tags": [tag.strip() for tag in tags.split(",")] if tags else [],
                "category": category,
                "upload_source": "api"
            }
        )
        
        # Log audit trail
        audit_repo = AuditRepository(db)
        await audit_repo.log_action(
            action="uploaded",
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"],
            document_id=document.id,
            details={
                "filename": file.filename,
                "content_type": mime_type,
                "file_size": file_size
            }
        )
        
        logger.info(f"Document {document.id} uploaded successfully by user {current_user['user_id']}")
        
        return {
            "id": str(document.id),
            "filename": document.filename,
            "original_filename": document.original_filename,
            "content_type": document.content_type,
            "file_size": document.file_size,
            "file_hash": document.file_hash,
            "status": document.status,
            "document_type": document.document_type,
            "metadata": document.metadata or {},
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat(),
            "organization_id": str(document.organization_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        # Clean up file if it was created
        if 'file_path' in locals():
            try:
                await aiofiles.os.remove(file_path)
            except:
                pass
        raise HTTPException(status_code=500, detail="Failed to upload document")


@app.get("/api/v1/documents/{document_id}/download")
async def download_document(
    document_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Download a document with security checks"""
    try:
        doc_repo = DocumentRepository(db)
        document = await doc_repo.get_by_id_and_organization(
            document_id, current_user["organization_id"]
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check file exists on disk
        file_path = Path(document.file_path)
        if not file_path.exists():
            logger.error(f"Document file missing: {file_path}")
            raise HTTPException(status_code=404, detail="Document file not found")
        
        # Log audit trail
        audit_repo = AuditRepository(db)
        await audit_repo.log_action(
            action="downloaded",
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"],
            document_id=document.id,
            details={
                "filename": document.filename,
                "file_size": document.file_size
            }
        )
        
        # Return file response with proper headers
        return FileResponse(
            path=str(file_path),
            filename=document.original_filename or document.filename,
            media_type=document.content_type,
            headers={
                "Content-Disposition": f"attachment; filename=\"{document.original_filename or document.filename}\"",
                "Content-Length": str(document.file_size),
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to download document")


@app.get("/api/v1/documents/{document_id}/stream")
async def stream_document(
    document_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Stream a document for browser viewing (PDFs, images)"""
    try:
        doc_repo = DocumentRepository(db)
        document = await doc_repo.get_by_id_and_organization(
            document_id, current_user["organization_id"]
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        file_path = Path(document.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document file not found")
        
        # Only allow streaming of safe content types
        streamable_types = [
            "application/pdf", 
            "image/jpeg", "image/png", "image/gif", "image/tiff",
            "text/plain"
        ]
        
        if document.content_type not in streamable_types:
            raise HTTPException(
                status_code=400, 
                detail="Document type not suitable for streaming. Use download instead."
            )
        
        # Create streaming response
        async def file_streamer():
            async with aiofiles.open(file_path, 'rb') as file:
                while chunk := await file.read(8192):
                    yield chunk
        
        # Log audit trail
        audit_repo = AuditRepository(db)
        await audit_repo.log_action(
            action="viewed",
            user_id=current_user["user_id"],
            organization_id=current_user["organization_id"],
            document_id=document.id,
            details={
                "filename": document.filename,
                "view_type": "stream"
            }
        )
        
        return StreamingResponse(
            file_streamer(),
            media_type=document.content_type,
            headers={
                "Content-Length": str(document.file_size),
                "Content-Disposition": f"inline; filename=\"{document.filename}\"",
                "Cache-Control": "private, no-cache",
                "X-Content-Type-Options": "nosniff"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stream document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to stream document")


# Document processing endpoints
@app.post("/api/v1/documents/{document_id}/process")
async def process_document(
    document_id: UUID,
    processing_type: str = "metadata_extraction",  # metadata_extraction, ocr, content_analysis
    priority: int = 5,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Queue document for background processing"""
    try:
        # Get document with organization check
        doc_repo = DocumentRepository(db)
        document = await doc_repo.get_by_id_and_organization(
            document_id, current_user["organization_id"]
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if document file exists
        file_path = Path(document.storage_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Document file not found on disk")
        
        # Check if already processing
        if document.processing_status == "processing":
            raise HTTPException(status_code=409, detail="Document is already being processed")
        
        # Validate processing type
        valid_types = ["metadata_extraction", "ocr", "content_analysis"]
        if processing_type not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid processing type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Import processing components
        from processing.queue_manager import ProcessingQueueManager, ProcessingTask
        
        # Create queue manager
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        queue_manager = ProcessingQueueManager(redis_url)
        await queue_manager.connect()
        
        try:
            # Create processing task
            task = ProcessingTask(
                id=str(uuid_lib.uuid4()),
                document_id=str(document_id),
                organization_id=str(current_user["organization_id"]),
                user_id=str(current_user["user_id"]),
                task_type=processing_type,
                priority=max(1, min(10, priority)),  # Clamp priority between 1-10
                file_path=str(file_path),
                mime_type=document.content_type,
                parameters={
                    "filename": document.filename,
                    "original_filename": document.original_filename,
                    "file_size": document.file_size
                }
            )
            
            # Enqueue task
            success = await queue_manager.enqueue_task(task)
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to queue processing task")
            
            # Update document processing status
            await doc_repo.update_by_id(document_id, processing_status="pending")
            
            # Log audit trail
            audit_repo = AuditRepository(db)
            await audit_repo.log_action(
                action="processing_queued",
                user_id=current_user["user_id"],
                organization_id=current_user["organization_id"],
                document_id=document_id,
                details={
                    "task_id": task.id,
                    "processing_type": processing_type,
                    "priority": priority,
                    "filename": document.filename
                }
            )
            
            logger.info(f"Queued {processing_type} task {task.id} for document {document_id}")
            
            return {
                "task_id": task.id,
                "document_id": str(document_id),
                "processing_type": processing_type,
                "status": "queued",
                "priority": priority,
                "estimated_duration_seconds": 120,  # Default estimate
                "message": f"Document queued for {processing_type.replace('_', ' ')}"
            }
            
        finally:
            await queue_manager.disconnect()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue processing for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue document processing")


@app.get("/api/v1/documents/{document_id}/processing-status")
async def get_processing_status(
    document_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get document processing status"""
    try:
        # Get document with organization check
        doc_repo = DocumentRepository(db)
        document = await doc_repo.get_by_id_and_organization(
            document_id, current_user["organization_id"]
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get processing tasks from queue
        from processing.queue_manager import ProcessingQueueManager
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        queue_manager = ProcessingQueueManager(redis_url)
        await queue_manager.connect()
        
        try:
            # Get queue stats for this document (simplified)
            queue_stats = await queue_manager.get_queue_stats()
            
            return {
                "document_id": str(document_id),
                "processing_status": document.processing_status,
                "ocr_completed": document.ocr_completed,
                "text_extraction_confidence": document.text_extraction_confidence,
                "last_processed": document.updated_at.isoformat(),
                "has_extracted_text": bool(document.extracted_text),
                "word_count": document.word_count,
                "language": document.language,
                "queue_stats": {
                    "total_pending": sum([
                        queue_stats.get("queue_high_length", 0),
                        queue_stats.get("queue_normal_length", 0),
                        queue_stats.get("queue_low_length", 0)
                    ]),
                    "currently_processing": queue_stats.get("processing_count", 0)
                }
            }
            
        finally:
            await queue_manager.disconnect()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get processing status for document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing status")


@app.get("/api/v1/processing/queue-stats")
async def get_queue_statistics(
    current_user: dict = Depends(get_current_user)
):
    """Get processing queue statistics"""
    try:
        from processing.queue_manager import ProcessingQueueManager
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        queue_manager = ProcessingQueueManager(redis_url)
        await queue_manager.connect()
        
        try:
            stats = await queue_manager.get_queue_stats()
            
            return {
                "queue_stats": stats,
                "organization_id": str(current_user["organization_id"]),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        finally:
            await queue_manager.disconnect()
            
    except Exception as e:
        logger.error(f"Failed to get queue statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get queue statistics")

# =============================================================================
# DOCUMENT PERMISSION ENDPOINTS
# =============================================================================

@app.post("/api/v1/documents/{document_id}/permissions/users")
async def grant_user_permission(
    document_id: UUID,
    request: GrantUserPermissionRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Grant permissions to a user for a document."""
    try:
        doc_repo = DocumentRepository(session)
        perm_repo = PermissionRepository(session)
        audit_repo = AuditRepository(session)
        
        # Verify document exists and user has admin access
        document = await doc_repo.get_by_id_and_organization(
            document_id, current_user["organization_id"]
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if current user has admin permission or is owner
        if document.created_by != current_user["id"]:
            # TODO: Check admin permissions when role system is complete
            pass
        
        # Grant permission
        permission = await perm_repo.grant_user_permission(
            document_id=document_id,
            user_id=request.user_id,
            permissions=request.permissions,
            granted_by=current_user["id"],
            expires_at=request.expires_at
        )
        
        # Log the action
        await audit_repo.log_action(
            action="grant_user_permission",
            user_id=current_user["id"],
            organization_id=current_user["organization_id"],
            document_id=document_id,
            details={
                "target_user_id": str(request.user_id),
                "permissions": request.permissions,
                "expires_at": request.expires_at.isoformat() if request.expires_at else None
            }
        )
        
        await session.commit()
        
        return {
            "success": True,
            "message": "User permission granted successfully",
            "permission_id": str(permission.id),
            "user_id": str(request.user_id),
            "permissions": request.permissions,
            "expires_at": request.expires_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error granting user permission: {e}")
        raise HTTPException(status_code=500, detail="Failed to grant permission")


@app.post("/api/v1/documents/{document_id}/permissions/roles")
async def grant_role_permission(
    document_id: UUID,
    request: GrantRolePermissionRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Grant permissions to a role for a document."""
    try:
        doc_repo = DocumentRepository(session)
        perm_repo = PermissionRepository(session)
        audit_repo = AuditRepository(session)
        
        # Verify document exists and user has admin access
        document = await doc_repo.get_by_id_and_organization(
            document_id, current_user["organization_id"]
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if current user has admin permission or is owner
        if document.created_by != current_user["id"]:
            # TODO: Check admin permissions when role system is complete
            pass
        
        # Grant permission
        permission = await perm_repo.grant_role_permission(
            document_id=document_id,
            role_name=request.role_name,
            permissions=request.permissions,
            granted_by=current_user["id"],
            expires_at=request.expires_at
        )
        
        # Log the action
        await audit_repo.log_action(
            action="grant_role_permission",
            user_id=current_user["id"],
            organization_id=current_user["organization_id"],
            document_id=document_id,
            details={
                "target_role": request.role_name,
                "permissions": request.permissions,
                "expires_at": request.expires_at.isoformat() if request.expires_at else None
            }
        )
        
        await session.commit()
        
        return {
            "success": True,
            "message": "Role permission granted successfully",
            "permission_id": str(permission.id),
            "role_name": request.role_name,
            "permissions": request.permissions,
            "expires_at": request.expires_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error granting role permission: {e}")
        raise HTTPException(status_code=500, detail="Failed to grant permission")


@app.get("/api/v1/documents/{document_id}/permissions")
async def get_document_permissions(
    document_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> DocumentPermissionSummary:
    """Get all permissions for a document."""
    try:
        doc_repo = DocumentRepository(session)
        perm_repo = PermissionRepository(session)
        
        # Verify document exists and user has access
        document = await doc_repo.get_by_id_and_organization(
            document_id, current_user["organization_id"]
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get permission summary
        summary = await perm_repo.get_permission_summary(document_id)
        
        return DocumentPermissionSummary(**summary)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document permissions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get permissions")


@app.get("/api/v1/documents/{document_id}/permissions/effective")
async def get_effective_permissions(
    document_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> EffectivePermissionsResponse:
    """Get effective permissions for the current user."""
    try:
        doc_repo = DocumentRepository(session)
        perm_repo = PermissionRepository(session)
        
        # Verify document exists and user has access
        document = await doc_repo.get_by_id_and_organization(
            document_id, current_user["organization_id"]
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get user roles from current_user context
        user_roles = current_user.get("roles", [])
        
        # Get effective permissions
        effective_perms = await perm_repo.get_user_effective_permissions(
            document_id=document_id,
            user_id=current_user["id"],
            user_roles=user_roles
        )
        
        # Determine sources
        sources = []
        if document.created_by == current_user["id"]:
            sources.append("owner")
            effective_perms = {perm: True for perm in effective_perms}  # Owner has all permissions
        
        # Check for direct user permissions
        user_perm = await perm_repo.get_user_permissions(document_id, current_user["id"])
        if user_perm and not user_perm.is_expired:
            sources.append("direct")
        
        # Check role permissions
        for role in user_roles:
            role_perm = await perm_repo.get_role_permissions(document_id, role)
            if role_perm and not role_perm.is_expired:
                sources.append(f"role:{role}")
        
        return EffectivePermissionsResponse(
            user_id=current_user["id"],
            document_id=document_id,
            permissions=effective_perms,
            sources=sources
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting effective permissions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get effective permissions")


@app.post("/api/v1/documents/{document_id}/share")
async def share_document(
    document_id: UUID,
    request: ShareDocumentRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> ShareDocumentResponse:
    """Share a document with a user or role."""
    try:
        doc_repo = DocumentRepository(session)
        perm_repo = PermissionRepository(session)
        audit_repo = AuditRepository(session)
        
        # Verify document exists and user has share permission
        document = await doc_repo.get_by_id_and_organization(
            document_id, current_user["organization_id"]
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if user can share (owner or has share permission)
        can_share = document.created_by == current_user["id"]
        if not can_share:
            user_roles = current_user.get("roles", [])
            can_share = await perm_repo.check_user_permission(
                document_id, current_user["id"], user_roles, "share"
            )
        
        if not can_share:
            raise HTTPException(status_code=403, detail="No permission to share this document")
        
        # Share the document
        if request.share_type == "user":
            permission = await perm_repo.grant_user_permission(
                document_id=document_id,
                user_id=UUID(request.target_id),
                permissions=request.permissions,
                granted_by=current_user["id"],
                expires_at=request.expires_at
            )
        else:  # role
            permission = await perm_repo.grant_role_permission(
                document_id=document_id,
                role_name=request.target_id,
                permissions=request.permissions,
                granted_by=current_user["id"],
                expires_at=request.expires_at
            )
        
        # Log the share action
        await audit_repo.log_action(
            action="share_document",
            user_id=current_user["id"],
            organization_id=current_user["organization_id"],
            document_id=document_id,
            details={
                "share_type": request.share_type,
                "target_id": request.target_id,
                "permissions": request.permissions,
                "message": request.message,
                "expires_at": request.expires_at.isoformat() if request.expires_at else None
            }
        )
        
        await session.commit()
        
        return ShareDocumentResponse(
            success=True,
            message=f"Document shared with {request.share_type} successfully",
            permission_id=permission.id,
            shared_with=request.target_id,
            permissions_granted=request.permissions,
            expires_at=request.expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error sharing document: {e}")
        raise HTTPException(status_code=500, detail="Failed to share document")


@app.delete("/api/v1/documents/{document_id}/permissions/users/{user_id}")
async def revoke_user_permission(
    document_id: UUID,
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Revoke user permissions for a document."""
    try:
        doc_repo = DocumentRepository(session)
        perm_repo = PermissionRepository(session)
        audit_repo = AuditRepository(session)
        
        # Verify document exists and user has admin access
        document = await doc_repo.get_by_id_and_organization(
            document_id, current_user["organization_id"]
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if current user has admin permission or is owner
        if document.created_by != current_user["id"]:
            # TODO: Check admin permissions when role system is complete
            pass
        
        # Revoke permission
        revoked = await perm_repo.revoke_user_permission(document_id, user_id)
        
        if not revoked:
            raise HTTPException(status_code=404, detail="Permission not found")
        
        # Log the action
        await audit_repo.log_action(
            action="revoke_user_permission",
            user_id=current_user["id"],
            organization_id=current_user["organization_id"],
            document_id=document_id,
            details={"target_user_id": str(user_id)}
        )
        
        await session.commit()
        
        return {"success": True, "message": "User permission revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error revoking user permission: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke permission")


@app.delete("/api/v1/documents/{document_id}/permissions/roles/{role_name}")
async def revoke_role_permission(
    document_id: UUID,
    role_name: str,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Revoke role permissions for a document."""
    try:
        doc_repo = DocumentRepository(session)
        perm_repo = PermissionRepository(session)
        audit_repo = AuditRepository(session)
        
        # Verify document exists and user has admin access
        document = await doc_repo.get_by_id_and_organization(
            document_id, current_user["organization_id"]
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if current user has admin permission or is owner
        if document.created_by != current_user["id"]:
            # TODO: Check admin permissions when role system is complete
            pass
        
        # Revoke permission
        revoked = await perm_repo.revoke_role_permission(document_id, role_name)
        
        if not revoked:
            raise HTTPException(status_code=404, detail="Permission not found")
        
        # Log the action
        await audit_repo.log_action(
            action="revoke_role_permission",
            user_id=current_user["id"],
            organization_id=current_user["organization_id"],
            document_id=document_id,
            details={"target_role": role_name}
        )
        
        await session.commit()
        
        return {"success": True, "message": "Role permission revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error revoking role permission: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke permission")


@app.post("/api/v1/documents/{document_id}/access-check")
async def check_document_access(
    document_id: UUID,
    request: DocumentAccessCheckRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> DocumentAccessCheckResponse:
    """Check if a user has access to a document."""
    try:
        doc_repo = DocumentRepository(session)
        perm_repo = PermissionRepository(session)
        
        # Verify document exists
        document = await doc_repo.get_by_id_and_organization(
            document_id, current_user["organization_id"]
        )
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check access
        has_access = await perm_repo.check_user_permission(
            document_id=document_id,
            user_id=request.user_id,
            user_roles=request.user_roles,
            permission_type=request.permission_type
        )
        
        # Determine access source
        access_source = None
        if has_access:
            if document.created_by == request.user_id:
                access_source = "owner"
            else:
                # Check for direct permission
                user_perm = await perm_repo.get_user_permissions(document_id, request.user_id)
                if user_perm and not user_perm.is_expired:
                    access_source = "direct"
                else:
                    # Check role permissions
                    for role in request.user_roles:
                        role_perm = await perm_repo.get_role_permissions(document_id, role)
                        if role_perm and not role_perm.is_expired:
                            access_source = f"role:{role}"
                            break
        
        # Get effective permissions
        effective_perms = await perm_repo.get_user_effective_permissions(
            document_id=document_id,
            user_id=request.user_id,
            user_roles=request.user_roles
        )
        
        # Owner has all permissions
        if document.created_by == request.user_id:
            effective_perms = {perm: True for perm in effective_perms}
        
        return DocumentAccessCheckResponse(
            user_id=request.user_id,
            document_id=document_id,
            has_access=has_access,
            permission_type=request.permission_type,
            access_source=access_source,
            effective_permissions=effective_perms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking document access: {e}")
        raise HTTPException(status_code=500, detail="Failed to check access")


@app.get("/api/v1/users/{user_id}/accessible-documents")
async def get_user_accessible_documents(
    user_id: UUID,
    user_roles: List[str] = [],
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Get documents accessible to a user based on permissions."""
    try:
        perm_repo = PermissionRepository(session)
        
        # Get accessible documents
        documents = await perm_repo.get_user_accessible_documents(
            user_id=user_id,
            user_roles=user_roles,
            organization_id=current_user["organization_id"],
            limit=limit,
            offset=offset
        )
        
        # Convert to response format
        document_list = []
        for doc in documents:
            document_list.append({
                "id": str(doc.id),
                "filename": doc.filename,
                "content_type": doc.content_type,
                "file_size": doc.file_size,
                "created_at": doc.created_at.isoformat(),
                "created_by": str(doc.created_by),
                "status": doc.status
            })
        
        return {
            "total_count": len(document_list),
            "documents": document_list,
            "page": offset // limit + 1,
            "limit": limit,
            "has_more": len(documents) == limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting accessible documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to get accessible documents")


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