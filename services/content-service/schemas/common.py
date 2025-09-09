"""
Common schemas and base models for the content service API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class BaseResponse(BaseModel):
    """Base response model with common fields."""
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True
    )


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    limit: int = Field(default=20, ge=1, le=100, description="Number of items per page")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
    

class PaginationInfo(BaseModel):
    """Pagination information in responses."""
    limit: int = Field(description="Items per page")
    offset: int = Field(description="Items skipped")
    total: int = Field(description="Total number of items")
    has_next: bool = Field(description="Whether there are more items")
    has_prev: bool = Field(description="Whether there are previous items")


class SuccessResponse(BaseResponse):
    """Generic success response."""
    success: bool = Field(default=True)
    message: str = Field(description="Success message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Additional data")


class ErrorResponse(BaseResponse):
    """Generic error response."""
    success: bool = Field(default=False)
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracking")


class HealthStatus(BaseResponse):
    """Service health check response."""
    service: str = Field(description="Service name")
    status: str = Field(description="Overall health status")
    version: str = Field(description="Service version")
    port: int = Field(description="Service port")
    dependencies: Dict[str, str] = Field(description="Dependency health status")
    metrics: Dict[str, Union[int, float]] = Field(description="Service metrics")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FileMetadata(BaseModel):
    """File metadata structure."""
    title: Optional[str] = Field(default=None, description="Document title")
    description: Optional[str] = Field(default=None, description="Document description")
    tags: List[str] = Field(default_factory=list, description="Document tags")
    classification: str = Field(
        default="internal",
        pattern="^(public|internal|confidential|restricted)$",
        description="Security classification"
    )
    author: Optional[str] = Field(default=None, description="Document author")
    department: Optional[str] = Field(default=None, description="Originating department")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata fields")


class AuditInfo(BaseModel):
    """Audit trail information."""
    created_at: datetime = Field(description="Creation timestamp")
    created_by: UUID = Field(description="Creator user ID")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    updated_by: Optional[UUID] = Field(default=None, description="Last updater user ID")
    version: int = Field(default=1, description="Document version number")


class ProcessingInfo(BaseModel):
    """Document processing information."""
    status: str = Field(description="Processing status")
    ocr_completed: bool = Field(default=False, description="Whether OCR is complete")
    thumbnail_generated: bool = Field(default=False, description="Whether thumbnail exists")
    text_extracted: bool = Field(default=False, description="Whether text is extracted")
    classification_completed: bool = Field(default=False, description="Whether classification is done")
    last_processed: Optional[datetime] = Field(default=None, description="Last processing timestamp")
    processing_errors: List[str] = Field(default_factory=list, description="Processing errors")