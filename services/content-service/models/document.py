"""
Document model and related database tables.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Integer, BigInteger, DateTime, Boolean, Text,
    ForeignKey, CheckConstraint, Index, event
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from database.connection import Base


class Document(Base):
    """Main document table storing document metadata and content information."""
    
    __tablename__ = "documents"
    
    # Primary key and identifiers
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4,
        doc="Document unique identifier"
    )
    
    # File information
    filename: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        doc="Current filename of the document"
    )
    original_filename: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        doc="Original filename when uploaded"
    )
    content_type: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        doc="MIME type of the document"
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger, 
        nullable=False,
        doc="File size in bytes"
    )
    file_hash: Mapped[str] = mapped_column(
        String(64), 
        nullable=False, 
        unique=True,
        doc="SHA-256 hash of the file content"
    )
    storage_path: Mapped[str] = mapped_column(
        Text, 
        nullable=False,
        doc="Path to the file in storage system"
    )
    
    # Ownership and organization
    created_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        nullable=False,
        doc="User ID who created the document"
    )
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        nullable=False,
        doc="Organization ID that owns the document"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        default=func.now(),
        doc="Document creation timestamp"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        default=func.now(),
        onupdate=func.now(),
        doc="Last update timestamp"
    )
    
    # Status and classification
    status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default="active",
        doc="Document status (active, processing, error, archived, deleted)"
    )
    document_type: Mapped[Optional[str]] = mapped_column(
        String(50), 
        nullable=True,
        doc="Detected or assigned document type"
    )
    classification: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default="internal",
        doc="Security classification (public, internal, confidential, restricted)"
    )
    
    # Content and search
    extracted_text: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        doc="Full extracted text content from the document"
    )
    
    # Metadata storage
    file_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, 
        nullable=False, 
        default=dict,
        doc="Document metadata as JSON"
    )
    
    # Processing information
    processing_status: Mapped[str] = mapped_column(
        String(20), 
        nullable=False, 
        default="pending",
        doc="Processing status (pending, processing, completed, failed)"
    )
    ocr_completed: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False,
        doc="Whether OCR processing is complete"
    )
    thumbnail_generated: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False,
        doc="Whether thumbnail has been generated"
    )
    
    # Relationships
    versions: Mapped[List["DocumentVersion"]] = relationship(
        "DocumentVersion",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentVersion.version_number.desc()"
    )
    
    audit_entries: Mapped[List["DocumentAudit"]] = relationship(
        "DocumentAudit",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    
    processing_jobs: Mapped[List["ProcessingJob"]] = relationship(
        "ProcessingJob",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    
    permissions: Mapped[List["DocumentPermission"]] = relationship(
        "DocumentPermission",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    
    shares: Mapped[List["DocumentShare"]] = relationship(
        "DocumentShare",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    
    comments: Mapped[List["DocumentComment"]] = relationship(
        "DocumentComment",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    
    activities: Mapped[List["DocumentActivity"]] = relationship(
        "DocumentActivity",
        back_populates="document",
        cascade="all, delete-orphan"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint("file_size > 0", name="positive_file_size"),
        CheckConstraint(
            "status IN ('active', 'processing', 'error', 'archived', 'deleted')",
            name="valid_status"
        ),
        CheckConstraint(
            "classification IN ('public', 'internal', 'confidential', 'restricted')",
            name="valid_classification"
        ),
        CheckConstraint(
            "processing_status IN ('pending', 'processing', 'completed', 'failed')",
            name="valid_processing_status"
        ),
        # Indexes for performance
        Index("idx_documents_org_created", "organization_id", "created_at"),
        Index("idx_documents_created_by", "created_by"),
        Index("idx_documents_type", "document_type"),
        Index("idx_documents_status", "status"),
        Index("idx_documents_hash", "file_hash"),
        Index("idx_documents_metadata", "file_metadata", postgresql_using="gin"),
        Index("idx_documents_text", "extracted_text"),
    )
    
    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}')>"
    
    @property
    def current_version(self) -> int:
        """Get the current version number."""
        if self.versions:
            return max(version.version_number for version in self.versions)
        return 1
    
    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """Get a value from the metadata JSON."""
        return self.file_metadata.get(key, default)
    
    def set_metadata_value(self, key: str, value: Any) -> None:
        """Set a value in the metadata JSON."""
        if self.file_metadata is None:
            self.file_metadata = {}
        self.file_metadata[key] = value
    
    def is_processing_complete(self) -> bool:
        """Check if all processing is complete."""
        return (
            self.processing_status == "completed" and
            self.ocr_completed and
            self.thumbnail_generated
        )


class DocumentVersion(Base):
    """Document version history table."""
    
    __tablename__ = "document_versions"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4
    )
    
    # Foreign key to parent document
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Version information
    version_number: Mapped[int] = mapped_column(
        Integer, 
        nullable=False,
        doc="Version number (1, 2, 3, ...)"
    )
    
    # File information for this version
    filename: Mapped[str] = mapped_column(
        String(255), 
        nullable=False,
        doc="Filename for this version"
    )
    storage_path: Mapped[str] = mapped_column(
        Text, 
        nullable=False,
        doc="Storage path for this version"
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger, 
        nullable=False,
        doc="File size for this version"
    )
    file_hash: Mapped[str] = mapped_column(
        String(64), 
        nullable=False,
        doc="File hash for this version"
    )
    
    # Version metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        default=func.now()
    )
    created_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        nullable=False
    )
    change_summary: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        doc="Summary of changes in this version"
    )
    version_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, 
        nullable=False, 
        default=dict,
        doc="Version-specific metadata"
    )
    
    # Relationship
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="versions"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint("file_size > 0", name="version_positive_file_size"),
        CheckConstraint("version_number > 0", name="positive_version_number"),
        Index("idx_versions_document", "document_id", "version_number"),
        Index("idx_versions_created", "created_at"),
        # Unique constraint on document + version
        Index("idx_versions_unique", "document_id", "version_number", unique=True),
    )
    
    def __repr__(self) -> str:
        return f"<DocumentVersion(id={self.id}, document_id={self.document_id}, version={self.version_number})>"


# Event listeners for automatic updates
@event.listens_for(Document, "before_update")
def update_document_timestamp(mapper, connection, target):
    """Update the updated_at timestamp before each update."""
    target.updated_at = func.now()


@event.listens_for(Document.file_metadata, "set")
def validate_metadata(target, value, oldvalue, initiator):
    """Validate metadata structure."""
    if value is not None and not isinstance(value, dict):
        raise ValueError("Metadata must be a dictionary")
    return value