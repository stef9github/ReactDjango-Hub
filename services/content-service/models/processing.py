"""
Processing job models for document processing tasks.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, Text, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, ENUM
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..database.connection import Base


# Enums for type safety
class ProcessingJobType(str, Enum):
    """Types of processing jobs."""
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


class ProcessingJob(Base):
    """Processing jobs for document operations."""
    
    __tablename__ = "processing_jobs"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4
    )
    
    # Foreign key to document
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        doc="ID of the document to process"
    )
    
    # Job details
    job_type: Mapped[ProcessingJobType] = mapped_column(
        ENUM(ProcessingJobType, name="processing_job_type"),
        nullable=False,
        doc="Type of processing job"
    )
    status: Mapped[JobStatus] = mapped_column(
        ENUM(JobStatus, name="job_status"),
        nullable=False,
        default=JobStatus.PENDING,
        doc="Current status of the job"
    )
    priority: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=5,
        doc="Job priority (1=highest, 10=lowest)"
    )
    
    # Processing configuration
    processor_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Name of the processor handling this job"
    )
    processor_version: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Version of the processor"
    )
    config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, 
        nullable=False, 
        default=dict,
        doc="Job configuration parameters"
    )
    
    # Results and errors
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Processing results"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Error message if job failed"
    )
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Detailed error information"
    )
    
    # Timing information
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        default=func.now(),
        doc="Job creation timestamp"
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Job start timestamp"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Job completion timestamp"
    )
    
    # Retry logic
    retry_count: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=0,
        doc="Number of retry attempts"
    )
    max_retries: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=3,
        doc="Maximum number of retry attempts"
    )
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When to retry the job if it failed"
    )
    
    # Webhook configuration
    webhook_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Webhook URL to call on completion"
    )
    webhook_headers: Mapped[Optional[Dict[str, str]]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Additional headers for webhook callback"
    )
    
    # Relationship
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="processing_jobs"
    )
    
    # Table constraints and indexes
    __table_args__ = (
        CheckConstraint("priority >= 1 AND priority <= 10", name="valid_priority"),
        CheckConstraint("retry_count >= 0", name="non_negative_retry_count"),
        CheckConstraint("max_retries >= 0", name="non_negative_max_retries"),
        
        # Indexes for job queue operations
        Index("idx_jobs_document", "document_id"),
        Index("idx_jobs_status", "status", "priority", "created_at"),
        Index("idx_jobs_retry", "next_retry_at", "status"),
        Index("idx_jobs_type", "job_type", "status"),
        Index("idx_jobs_created", "created_at"),
        Index("idx_jobs_webhook", "webhook_url"),
        Index("idx_jobs_config", "config", postgresql_using="gin"),
        Index("idx_jobs_result", "result", postgresql_using="gin"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<ProcessingJob(id={self.id}, type='{self.job_type}', "
            f"status='{self.status}', document_id={self.document_id})>"
        )
    
    @property
    def duration_ms(self) -> Optional[int]:
        """Calculate job duration in milliseconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None
    
    @property
    def is_terminal_state(self) -> bool:
        """Check if the job is in a terminal state."""
        return self.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)
    
    @property
    def can_retry(self) -> bool:
        """Check if the job can be retried."""
        return (
            self.status == JobStatus.FAILED and
            self.retry_count < self.max_retries
        )
    
    def mark_started(self) -> None:
        """Mark the job as started."""
        self.status = JobStatus.RUNNING
        self.started_at = func.now()
    
    def mark_completed(self, result: Dict[str, Any]) -> None:
        """Mark the job as completed with results."""
        self.status = JobStatus.COMPLETED
        self.completed_at = func.now()
        self.result = result
        self.error_message = None
        self.error_details = None
    
    def mark_failed(
        self, 
        error_message: str, 
        error_details: Optional[Dict[str, Any]] = None,
        schedule_retry: bool = True
    ) -> None:
        """Mark the job as failed with error information."""
        self.status = JobStatus.FAILED
        self.completed_at = func.now()
        self.error_message = error_message
        self.error_details = error_details or {}
        
        if schedule_retry and self.can_retry:
            self.retry_count += 1
            # Exponential backoff: 2^retry_count minutes
            backoff_minutes = 2 ** self.retry_count
            self.next_retry_at = func.now() + timedelta(minutes=backoff_minutes)
    
    def mark_cancelled(self) -> None:
        """Mark the job as cancelled."""
        self.status = JobStatus.CANCELLED
        self.completed_at = func.now()
    
    def reset_for_retry(self) -> None:
        """Reset job for retry."""
        self.status = JobStatus.PENDING
        self.started_at = None
        self.completed_at = None
        self.next_retry_at = None
    
    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default) if self.config else default
    
    def set_config_value(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        if self.config is None:
            self.config = {}
        self.config[key] = value
    
    def get_result_value(self, key: str, default: Any = None) -> Any:
        """Get a result value."""
        return self.result.get(key, default) if self.result else default
    
    def add_result_data(self, data: Dict[str, Any]) -> None:
        """Add data to the result."""
        if self.result is None:
            self.result = {}
        self.result.update(data)