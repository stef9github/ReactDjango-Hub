"""
Document-related schemas for the content service API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, validator

from .common import BaseResponse, FileMetadata, AuditInfo, ProcessingInfo, PaginationInfo


class DocumentBase(BaseModel):
    """Base document model with common fields."""
    filename: str = Field(min_length=1, max_length=255, description="Document filename")
    content_type: str = Field(description="MIME type of the document")
    metadata: FileMetadata = Field(default_factory=FileMetadata, description="Document metadata")


class DocumentCreate(DocumentBase):
    """Schema for document creation requests."""
    pass


class DocumentUpdate(BaseModel):
    """Schema for document update requests."""
    metadata: Optional[FileMetadata] = Field(default=None, description="Updated metadata")
    
    @validator('metadata', pre=True)
    def validate_metadata_not_empty(cls, v):
        if v is not None and not any(v.dict().values()):
            raise ValueError("Metadata cannot be empty when provided")
        return v


class DocumentResponse(BaseResponse):
    """Basic document response schema."""
    id: UUID = Field(description="Document unique identifier")
    filename: str = Field(description="Document filename")
    original_filename: str = Field(description="Original filename when uploaded")
    content_type: str = Field(description="MIME type")
    file_size: int = Field(description="File size in bytes")
    file_hash: str = Field(description="SHA-256 hash of the file")
    organization_id: UUID = Field(description="Organization ID")
    status: str = Field(description="Document status")
    document_type: Optional[str] = Field(default=None, description="Detected document type")
    metadata: FileMetadata = Field(description="Document metadata")
    audit: AuditInfo = Field(description="Audit information")
    processing: ProcessingInfo = Field(description="Processing status")
    
    # URLs for accessing the document
    download_url: Optional[str] = Field(default=None, description="Document download URL")
    thumbnail_url: Optional[str] = Field(default=None, description="Thumbnail URL")
    preview_url: Optional[str] = Field(default=None, description="Preview URL")


class DocumentDetailResponse(DocumentResponse):
    """Detailed document response with additional information."""
    extracted_text: Optional[str] = Field(default=None, description="Extracted text content")
    text_preview: Optional[str] = Field(default=None, description="First 500 characters of text")
    page_count: Optional[int] = Field(default=None, description="Number of pages (for documents)")
    word_count: Optional[int] = Field(default=None, description="Word count")
    character_count: Optional[int] = Field(default=None, description="Character count")
    
    # Processing details
    ocr_confidence: Optional[float] = Field(default=None, description="OCR confidence score")
    classification_confidence: Optional[float] = Field(default=None, description="Classification confidence")
    
    # Version information
    current_version: int = Field(description="Current version number")
    version_count: int = Field(description="Total number of versions")
    
    # Permissions
    permissions: Dict[str, bool] = Field(description="User permissions for this document")


class DocumentListItem(BaseResponse):
    """Simplified document item for list responses."""
    id: UUID = Field(description="Document unique identifier")
    filename: str = Field(description="Document filename")
    content_type: str = Field(description="MIME type")
    file_size: int = Field(description="File size in bytes")
    document_type: Optional[str] = Field(default=None, description="Document type")
    created_at: datetime = Field(description="Creation timestamp")
    created_by: UUID = Field(description="Creator user ID")
    status: str = Field(description="Document status")
    
    # Quick metadata
    title: Optional[str] = Field(default=None, description="Document title")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    classification: str = Field(description="Security classification")
    
    # Processing status
    processing_complete: bool = Field(description="Whether processing is complete")
    has_thumbnail: bool = Field(description="Whether thumbnail is available")
    
    # Quick access URLs
    thumbnail_url: Optional[str] = Field(default=None, description="Thumbnail URL")


class DocumentListResponse(BaseResponse):
    """Response for document list endpoints."""
    documents: List[DocumentListItem] = Field(description="List of documents")
    pagination: PaginationInfo = Field(description="Pagination information")
    filters_applied: Dict[str, Any] = Field(description="Applied filters")
    total_size: int = Field(description="Total size of all documents in bytes")


class DocumentUploadResponse(BaseResponse):
    """Response for document upload."""
    document: DocumentResponse = Field(description="Created document")
    upload_info: Dict[str, Any] = Field(description="Upload processing information")
    processing_jobs: List[str] = Field(description="Initiated processing job IDs")


class DocumentVersionResponse(BaseResponse):
    """Document version information."""
    id: UUID = Field(description="Version ID")
    document_id: UUID = Field(description="Parent document ID")
    version_number: int = Field(description="Version number")
    filename: str = Field(description="Version filename")
    file_size: int = Field(description="File size in bytes")
    created_at: datetime = Field(description="Version creation timestamp")
    created_by: UUID = Field(description="Version creator")
    change_summary: Optional[str] = Field(default=None, description="Summary of changes")
    is_current: bool = Field(description="Whether this is the current version")


class DocumentVersionListResponse(BaseResponse):
    """List of document versions."""
    document_id: UUID = Field(description="Document ID")
    versions: List[DocumentVersionResponse] = Field(description="Document versions")
    current_version: int = Field(description="Current version number")


class BulkOperationRequest(BaseModel):
    """Request for bulk operations on documents."""
    document_ids: List[UUID] = Field(min_items=1, max_items=100, description="Document IDs")
    operation: str = Field(description="Operation to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")


class BulkOperationResponse(BaseResponse):
    """Response for bulk operations."""
    total_requested: int = Field(description="Total documents requested")
    successful: int = Field(description="Successfully processed documents")
    failed: int = Field(description="Failed document operations")
    results: List[Dict[str, Any]] = Field(description="Detailed results per document")
    errors: List[Dict[str, Any]] = Field(description="Error details for failed operations")


class DocumentStatsResponse(BaseResponse):
    """Document statistics response."""
    total_documents: int = Field(description="Total number of documents")
    total_size: int = Field(description="Total size in bytes")
    documents_by_type: Dict[str, int] = Field(description="Document count by type")
    documents_by_status: Dict[str, int] = Field(description="Document count by status")
    recent_uploads: List[DocumentListItem] = Field(description="Recently uploaded documents")
    processing_queue_size: int = Field(description="Number of documents in processing queue")