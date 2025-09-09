"""
Permission model for document access control.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..database.connection import Base


class DocumentPermission(Base):
    """Document permissions for users and roles."""
    
    __tablename__ = "document_permissions"
    
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
        doc="ID of the document"
    )
    
    # Permission target (either user or role, not both)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        doc="User ID (if permission is for a specific user)"
    )
    role_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Role name (if permission is for a role)"
    )
    
    # Permission flags
    can_read: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False,
        doc="Permission to read/view the document"
    )
    can_write: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False,
        doc="Permission to modify the document"
    )
    can_delete: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False,
        doc="Permission to delete the document"
    )
    can_share: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False,
        doc="Permission to share the document with others"
    )
    can_admin: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False,
        doc="Administrative permissions (manage permissions, etc.)"
    )
    
    # Permission metadata
    granted_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), 
        nullable=False,
        doc="User ID who granted this permission"
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        default=func.now(),
        doc="When the permission was granted"
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When the permission expires (null = never expires)"
    )
    
    # Inheritance and source tracking
    inherited: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=False,
        doc="Whether this permission is inherited from a parent resource"
    )
    source_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Source of inherited permission (folder, organization, etc.)"
    )
    source_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=True,
        doc="ID of the source resource for inherited permissions"
    )
    
    # Relationship
    document: Mapped["Document"] = relationship(
        "Document",
        back_populates="permissions"
    )
    
    # Table constraints and indexes
    __table_args__ = (
        # Ensure either user_id or role_name is specified, but not both
        CheckConstraint(
            "(user_id IS NOT NULL AND role_name IS NULL) OR "
            "(user_id IS NULL AND role_name IS NOT NULL)",
            name="permission_target_check"
        ),
        
        # Ensure at least one permission is granted
        CheckConstraint(
            "can_read OR can_write OR can_delete OR can_share OR can_admin",
            name="permission_granted_check"
        ),
        
        # Ensure expires_at is in the future if specified
        CheckConstraint(
            "expires_at IS NULL OR expires_at > granted_at",
            name="valid_expiration_check"
        ),
        
        # Indexes for performance
        Index("idx_permissions_document", "document_id"),
        Index("idx_permissions_user", "user_id"),
        Index("idx_permissions_role", "role_name"),
        Index("idx_permissions_granted_by", "granted_by"),
        Index("idx_permissions_expires", "expires_at"),
        Index("idx_permissions_source", "source_type", "source_id"),
        
        # Unique constraint to prevent duplicate permissions
        Index(
            "idx_permissions_unique_user", 
            "document_id", "user_id", 
            unique=True,
            postgresql_where="user_id IS NOT NULL"
        ),
        Index(
            "idx_permissions_unique_role", 
            "document_id", "role_name", 
            unique=True,
            postgresql_where="role_name IS NOT NULL"
        ),
    )
    
    def __repr__(self) -> str:
        target = self.user_id or self.role_name
        return (
            f"<DocumentPermission(id={self.id}, document_id={self.document_id}, "
            f"target={target}, read={self.can_read}, write={self.can_write})>"
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if the permission has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at.replace(tzinfo=None)
    
    @property
    def target_identifier(self) -> str:
        """Get the target identifier (user ID or role name)."""
        return str(self.user_id) if self.user_id else self.role_name
    
    @property
    def permission_level(self) -> int:
        """Get numeric permission level for comparison."""
        if self.can_admin:
            return 5
        elif self.can_delete:
            return 4
        elif self.can_share:
            return 3
        elif self.can_write:
            return 2
        elif self.can_read:
            return 1
        else:
            return 0
    
    def has_permission(self, permission: str) -> bool:
        """Check if a specific permission is granted."""
        permission_map = {
            "read": self.can_read,
            "write": self.can_write,
            "delete": self.can_delete,
            "share": self.can_share,
            "admin": self.can_admin
        }
        return permission_map.get(permission.lower(), False)
    
    def grant_permission(self, permission: str) -> None:
        """Grant a specific permission."""
        if permission.lower() == "read":
            self.can_read = True
        elif permission.lower() == "write":
            self.can_write = True
            self.can_read = True  # Write implies read
        elif permission.lower() == "delete":
            self.can_delete = True
            self.can_write = True
            self.can_read = True  # Delete implies write and read
        elif permission.lower() == "share":
            self.can_share = True
        elif permission.lower() == "admin":
            self.can_admin = True
            self.can_share = True
            self.can_delete = True
            self.can_write = True
            self.can_read = True  # Admin implies all permissions
    
    def revoke_permission(self, permission: str) -> None:
        """Revoke a specific permission."""
        if permission.lower() == "admin":
            self.can_admin = False
        elif permission.lower() == "share":
            self.can_share = False
        elif permission.lower() == "delete":
            self.can_delete = False
        elif permission.lower() == "write":
            self.can_write = False
            self.can_delete = False  # Revoke higher permissions too
        elif permission.lower() == "read":
            self.can_read = False
            self.can_write = False
            self.can_delete = False
            self.can_admin = False  # Revoke all higher permissions
    
    @classmethod
    def create_user_permission(
        cls,
        document_id: UUID,
        user_id: UUID,
        granted_by: UUID,
        permissions: list[str],
        expires_at: Optional[datetime] = None
    ) -> "DocumentPermission":
        """Create a new user permission."""
        perm = cls(
            document_id=document_id,
            user_id=user_id,
            granted_by=granted_by,
            expires_at=expires_at
        )
        
        for permission in permissions:
            perm.grant_permission(permission)
        
        return perm
    
    @classmethod
    def create_role_permission(
        cls,
        document_id: UUID,
        role_name: str,
        granted_by: UUID,
        permissions: list[str],
        expires_at: Optional[datetime] = None
    ) -> "DocumentPermission":
        """Create a new role permission."""
        perm = cls(
            document_id=document_id,
            role_name=role_name,
            granted_by=granted_by,
            expires_at=expires_at
        )
        
        for permission in permissions:
            perm.grant_permission(permission)
        
        return perm