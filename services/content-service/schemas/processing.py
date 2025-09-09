"""
Processing-related schemas for the content service API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl

from .common import BaseResponse


class ProcessorType(str, Enum):
    """Available document processors."""
    OCR = "ocr"
    THUMBNAIL = "thumbnail"
    METADATA_EXTRACTION = "metadata_extraction"
    CLASSIFICATION = "classification"
    VIRUS_SCAN = "virus_scan"
    TEXT_EXTRACTION = "text_extraction"
    ENTITY_EXTRACTION = "entity_extraction"


class JobStatus(str, Enum):
    """Processing job statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class ProcessingJobRequest(BaseModel):
    """Request to start document processing."""
    processors: List[ProcessorType] = Field(
        min_items=1,
        description="List of processors to run"
    )
    priority: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Processing priority (1=highest, 10=lowest)"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Processor-specific configuration"
    )
    webhook_url: Optional[HttpUrl] = Field(
        default=None,
        description="Webhook URL for completion notification"
    )
    callback_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional headers for webhook callback"
    )


class ProcessingJobResponse(BaseResponse):
    """Response for processing job creation."""
    job_id: UUID = Field(description="Processing job ID")
    document_id: UUID = Field(description="Document being processed")
    processors: List[ProcessorType] = Field(description="Processors to run")
    status: JobStatus = Field(description="Current job status")
    priority: int = Field(description="Job priority")
    estimated_completion: Optional[datetime] = Field(
        default=None,
        description="Estimated completion time"
    )
    created_at: datetime = Field(description="Job creation timestamp")


class ProcessorResult(BaseModel):
    """Result from a specific processor."""
    processor: ProcessorType = Field(description="Processor type")
    status: JobStatus = Field(description="Processor status")
    started_at: Optional[datetime] = Field(default=None, description="Start time")
    completed_at: Optional[datetime] = Field(default=None, description="Completion time")
    duration_ms: Optional[int] = Field(default=None, description="Processing duration")
    
    # Results
    success: bool = Field(description="Whether processing succeeded")
    result: Dict[str, Any] = Field(default_factory=dict, description="Processor results")
    confidence: Optional[float] = Field(default=None, description="Result confidence score")
    
    # Error information
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    error_code: Optional[str] = Field(default=None, description="Error code")
    error_details: Dict[str, Any] = Field(default_factory=dict, description="Detailed error info")


class ProcessingStatusResponse(BaseResponse):
    """Detailed processing status for a document."""
    document_id: UUID = Field(description="Document ID")
    overall_status: JobStatus = Field(description="Overall processing status")
    progress_percentage: float = Field(ge=0, le=100, description="Overall progress percentage")
    
    # Job information
    active_jobs: List[ProcessingJobResponse] = Field(description="Currently active jobs")
    completed_jobs: List[ProcessingJobResponse] = Field(description="Completed jobs")
    failed_jobs: List[ProcessingJobResponse] = Field(description="Failed jobs")
    
    # Processor results
    processor_results: List[ProcessorResult] = Field(description="Results from each processor")
    
    # Timing
    started_at: Optional[datetime] = Field(default=None, description="Processing start time")
    completed_at: Optional[datetime] = Field(default=None, description="Processing completion time")
    total_duration_ms: Optional[int] = Field(default=None, description="Total processing time")
    
    # Queue information
    queue_position: Optional[int] = Field(default=None, description="Position in processing queue")
    estimated_start: Optional[datetime] = Field(default=None, description="Estimated start time")


class ProcessingQueueStatus(BaseResponse):
    """Processing queue status."""
    total_jobs: int = Field(description="Total jobs in queue")
    pending_jobs: int = Field(description="Pending jobs")
    running_jobs: int = Field(description="Currently running jobs")
    failed_jobs: int = Field(description="Failed jobs awaiting retry")
    
    # Queue health
    average_processing_time: float = Field(description="Average processing time in seconds")
    queue_throughput: float = Field(description="Jobs processed per minute")
    error_rate: float = Field(description="Processing error rate (0-1)")
    
    # Worker information
    active_workers: int = Field(description="Number of active worker processes")
    worker_capacity: int = Field(description="Maximum worker capacity")
    
    # Recent jobs
    recent_completions: List[ProcessingJobResponse] = Field(description="Recently completed jobs")


class OCRResult(BaseModel):
    """OCR processing results."""
    text: str = Field(description="Extracted text")
    confidence: float = Field(ge=0, le=1, description="Overall OCR confidence")
    language: str = Field(description="Detected language")
    page_count: int = Field(description="Number of pages processed")
    
    # Detailed results per page
    pages: List[Dict[str, Any]] = Field(description="Per-page OCR results")
    
    # Processing metadata
    processor_version: str = Field(description="OCR processor version")
    processing_time_ms: int = Field(description="Processing time in milliseconds")


class ClassificationResult(BaseModel):
    """Document classification results."""
    document_type: str = Field(description="Predicted document type")
    confidence: float = Field(ge=0, le=1, description="Classification confidence")
    categories: List[Dict[str, float]] = Field(description="All categories with scores")
    
    # Extracted entities
    entities: List[Dict[str, Any]] = Field(description="Named entities found")
    keywords: List[str] = Field(description="Key terms extracted")
    
    # Classification metadata
    model_version: str = Field(description="Classification model version")
    processing_time_ms: int = Field(description="Processing time in milliseconds")


class ThumbnailResult(BaseModel):
    """Thumbnail generation results."""
    thumbnail_path: str = Field(description="Path to generated thumbnail")
    thumbnail_size: tuple[int, int] = Field(description="Thumbnail dimensions (width, height)")
    file_size: int = Field(description="Thumbnail file size in bytes")
    format: str = Field(description="Thumbnail image format")
    
    # Generation metadata
    source_pages: List[int] = Field(description="Source pages used for thumbnail")
    processing_time_ms: int = Field(description="Generation time in milliseconds")


class ProcessingWebhookPayload(BaseModel):
    """Webhook payload sent on processing completion."""
    event_type: str = Field(description="Event type (processing_completed, processing_failed)")
    document_id: UUID = Field(description="Processed document ID")
    job_id: UUID = Field(description="Processing job ID")
    status: JobStatus = Field(description="Final processing status")
    
    # Processing results
    processor_results: List[ProcessorResult] = Field(description="Results from all processors")
    
    # Timing
    started_at: datetime = Field(description="Processing start time")
    completed_at: datetime = Field(description="Processing completion time")
    total_duration_ms: int = Field(description="Total processing duration")
    
    # Additional context
    organization_id: UUID = Field(description="Organization ID")
    user_id: UUID = Field(description="User who initiated processing")
    timestamp: datetime = Field(description="Webhook timestamp")