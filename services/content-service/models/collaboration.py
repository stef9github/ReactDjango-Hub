"""
Collaboration models for document sharing and team work.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy import (
    Column, String, DateTime, Boolean, Text, ForeignKey, Index, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from database.connection import Base


class ShareNotificationStatus(str, Enum):
    """Status of share notifications."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class DocumentShare(Base):
    """Document sharing records with notifications."""
    
    __tablename__ = "document_shares"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4
    )
    
    # Document and permission reference
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False
    )
    permission_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("document_permissions.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Sharing details
    shared_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        doc="User who shared the document"
    )
    shared_with_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        doc="Type of recipient: 'user' or 'role'"
    )
    shared_with_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="User ID or role name"
    )
    
    # Message and metadata
    share_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Optional message from the sharer"
    )
    access_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="read",
        doc="Primary access level granted"
    )
    
    # Timestamps
    shared_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now()
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the share expires"
    )
    
    # Notification status
    notification_status: Mapped[ShareNotificationStatus] = mapped_column(
        SQLEnum(ShareNotificationStatus),
        nullable=False,
        default=ShareNotificationStatus.PENDING
    )
    notification_sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    notification_read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Additional metadata
    share_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Additional sharing metadata"
    )
    
    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="shares"
    )
    
    # Table constraints and indexes
    __table_args__ = (
        Index("idx_shares_document", "document_id"),
        Index("idx_shares_shared_by", "shared_by"),
        Index("idx_shares_shared_with", "shared_with_type", "shared_with_id"),
        Index("idx_shares_notification_status", "notification_status"),
        Index("idx_shares_expires", "expires_at"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<DocumentShare(id={self.id}, document_id={self.document_id}, "
            f"shared_with={self.shared_with_type}:{self.shared_with_id})>"
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if the share has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)
    
    def mark_notification_sent(self) -> None:
        """Mark notification as sent."""
        self.notification_status = ShareNotificationStatus.SENT
        self.notification_sent_at = datetime.utcnow()
    
    def mark_notification_read(self) -> None:
        """Mark notification as read."""
        if self.notification_status in [ShareNotificationStatus.SENT, ShareNotificationStatus.DELIVERED]:
            self.notification_status = ShareNotificationStatus.READ
            self.notification_read_at = datetime.utcnow()


class DocumentComment(Base):
    """Comments on documents for collaboration."""
    
    __tablename__ = "document_comments"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    # Document reference
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Comment details
    author_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        doc="User who created the comment"
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Comment content"
    )
    
    # Threading support
    parent_comment_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("document_comments.id", ondelete="CASCADE"),
        nullable=True,
        doc="Parent comment for threaded discussions"
    )
    
    # Position in document (for annotations)
    page_number: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        doc="Page number for PDF annotations"
    )
    position_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
        doc="Position/selection data for annotations"
    )
    
    # Status and visibility
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        doc="Comment status: active, resolved, deleted"
    )
    is_resolved: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether the comment/issue is resolved"
    )
    resolved_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        doc="User who resolved the comment"
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="comments"
    )
    parent_comment: Mapped[Optional["DocumentComment"]] = relationship(
        "DocumentComment",
        remote_side=[id],
        back_populates="replies"
    )
    replies: Mapped[List["DocumentComment"]] = relationship(
        "DocumentComment",
        back_populates="parent_comment",
        cascade="all, delete-orphan"
    )
    
    # Table constraints and indexes
    __table_args__ = (
        Index("idx_comments_document", "document_id"),
        Index("idx_comments_author", "author_id"),
        Index("idx_comments_parent", "parent_comment_id"),
        Index("idx_comments_status", "status"),
        Index("idx_comments_created", "created_at"),
        Index("idx_comments_position", "page_number"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<DocumentComment(id={self.id}, document_id={self.document_id}, "
            f"author_id={self.author_id}, status={self.status})>"
        )
    
    def resolve(self, resolved_by: UUID) -> None:
        """Mark comment as resolved."""
        self.is_resolved = True
        self.resolved_by = resolved_by
        self.resolved_at = datetime.utcnow()
        self.status = "resolved"
    
    def unresolve(self) -> None:
        """Mark comment as unresolved."""
        self.is_resolved = False
        self.resolved_by = None
        self.resolved_at = None
        self.status = "active"


class DocumentActivity(Base):
    """Activity log for document collaboration."""
    
    __tablename__ = "document_activities"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    # Document reference
    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Activity details
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        doc="User who performed the activity"
    )
    activity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Type of activity: shared, commented, viewed, downloaded, etc."
    )
    activity_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Human-readable description of the activity"
    )
    
    # Activity context
    target_user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        doc="Target user for activities like sharing"
    )
    activity_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Additional activity metadata"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now()
    )
    
    # Relationships
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="activities"
    )
    
    # Table constraints and indexes
    __table_args__ = (
        Index("idx_activities_document", "document_id"),
        Index("idx_activities_user", "user_id"),
        Index("idx_activities_type", "activity_type"),
        Index("idx_activities_created", "created_at"),
        Index("idx_activities_target", "target_user_id"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<DocumentActivity(id={self.id}, document_id={self.document_id}, "
            f"user_id={self.user_id}, type={self.activity_type})>"
        )


class DocumentWorkspace(Base):
    """Shared workspaces for document collaboration."""
    
    __tablename__ = "document_workspaces"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4
    )
    
    # Workspace details
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Workspace name"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Workspace description"
    )
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        doc="Organization that owns the workspace"
    )
    
    # Access control
    created_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
        doc="User who created the workspace"
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether workspace is public within organization"
    )
    
    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        doc="Workspace status: active, archived, deleted"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now()
    )
    
    # Settings
    settings: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        doc="Workspace settings and preferences"
    )
    
    # Table constraints and indexes
    __table_args__ = (
        Index("idx_workspaces_org", "organization_id"),
        Index("idx_workspaces_created_by", "created_by"),
        Index("idx_workspaces_status", "status"),
        Index("idx_workspaces_name", "name"),
    )
    
    def __repr__(self) -> str:
        return (
            f"<DocumentWorkspace(id={self.id}, name='{self.name}', "
            f"organization_id={self.organization_id})>"
        )