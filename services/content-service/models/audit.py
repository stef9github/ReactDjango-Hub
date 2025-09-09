"""
Audit trail model for tracking document operations.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, Text, Integer, Index
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, INET
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..database.connection import Base


class DocumentAudit(Base):
    """Audit trail for document operations."""
    
    __tablename__ = "document_audit"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4
    )
    
    # Foreign key to document (nullable for operations like bulk deletes)
    document_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        doc="ID of the affected document"
    )
    
    # Action details
    action: Mapped[str] = mapped_column(
        String(50), 
        nullable=False,
        doc="Action performed (create, read, update, delete, share, process, etc.)"
    )
    resource_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default="document",
        doc="Type of resource affected"
    )
    resource_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        doc="ID of the affected resource"
    )
    
    # User context
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        nullable=False,
        doc="ID of the user who performed the action"
    )
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        nullable=False,
        doc="Organization context for the action"
    )
    session_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="User session identifier"
    )
    
    # Request context
    ip_address: Mapped[Optional[str]] = mapped_column(
        INET,
        nullable=True,
        doc="IP address of the client"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="User agent string from the request"
    )
    request_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        doc="Request ID for correlation"
    )
    
    # Event details
    details: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, 
        nullable=False, 
        default=dict,
        doc="Additional details about the action"
    )
    
    # Timing
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        default=func.now(),
        doc="Timestamp when the action occurred"
    )
    
    # Performance tracking
    execution_time_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        doc="Execution time in milliseconds"
    )
    
    # Relationship
    document: Mapped[Optional["Document"]] = relationship(
        "Document",
        back_populates="audit_entries"
    )
    
    # Table constraints and indexes
    __table_args__ = (
        # Indexes for common query patterns
        Index("idx_audit_document", "document_id", "created_at"),
        Index("idx_audit_user", "user_id", "created_at"),
        Index("idx_audit_org", "organization_id", "created_at"),
        Index("idx_audit_action", "action", "created_at"),
        Index("idx_audit_session", "session_id"),
        Index("idx_audit_request", "request_id"),
        Index("idx_audit_details", "details", postgresql_using="gin"),
        
        # Partitioning hint - would be implemented at database level
        # Partition by month for better performance with large datasets
    )
    
    def __repr__(self) -> str:
        return (
            f"<DocumentAudit(id={self.id}, action='{self.action}', "
            f"document_id={self.document_id}, user_id={self.user_id})>"
        )
    
    @classmethod
    def create_audit_entry(
        cls,
        action: str,
        user_id: UUID,
        organization_id: UUID,
        document_id: Optional[UUID] = None,
        resource_type: str = "document",
        resource_id: Optional[UUID] = None,
        details: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[UUID] = None,
        execution_time_ms: Optional[int] = None
    ) -> "DocumentAudit":
        """Create a new audit entry."""
        return cls(
            action=action,
            document_id=document_id,
            resource_type=resource_type,
            resource_id=resource_id or document_id,
            user_id=user_id,
            organization_id=organization_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            details=details or {},
            execution_time_ms=execution_time_ms
        )
    
    def add_detail(self, key: str, value: Any) -> None:
        """Add a detail to the audit entry."""
        if self.details is None:
            self.details = {}
        self.details[key] = value
    
    def get_detail(self, key: str, default: Any = None) -> Any:
        """Get a detail from the audit entry."""
        if self.details is None:
            return default
        return self.details.get(key, default)