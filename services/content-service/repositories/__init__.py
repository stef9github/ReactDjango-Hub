"""
Repository layer for data access patterns.
"""

from .base import BaseRepository
from .document_repository import DocumentRepository
from .processing_repository import ProcessingJobRepository
from .audit_repository import AuditRepository
from .permission_repository import PermissionRepository
from .collaboration_repository import (
    CollaborationRepository, CommentRepository, 
    ActivityRepository, WorkspaceRepository
)

__all__ = [
    "BaseRepository",
    "DocumentRepository", 
    "ProcessingJobRepository",
    "AuditRepository",
    "PermissionRepository",
    "CollaborationRepository",
    "CommentRepository",
    "ActivityRepository", 
    "WorkspaceRepository"
]