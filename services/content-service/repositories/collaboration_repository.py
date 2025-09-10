"""
Repository for collaboration features.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .base import BaseRepository
from models.collaboration import (
    DocumentShare, DocumentComment, DocumentActivity, DocumentWorkspace
)


class CollaborationRepository(BaseRepository[DocumentShare]):
    """Repository for collaboration operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, DocumentShare)
    
    async def create_share_notification(
        self,
        document_id: UUID,
        permission_id: UUID,
        shared_by: UUID,
        shared_with_type: str,
        shared_with_id: str,
        share_message: Optional[str] = None,
        access_level: str = "read",
        expires_at: Optional[datetime] = None
    ) -> DocumentShare:
        """Create a share notification record."""
        share = DocumentShare(
            document_id=document_id,
            permission_id=permission_id,
            shared_by=shared_by,
            shared_with_type=shared_with_type,
            shared_with_id=shared_with_id,
            share_message=share_message,
            access_level=access_level,
            expires_at=expires_at
        )
        
        return await self.create_instance(share)
    
    async def get_user_shared_documents(
        self,
        user_id: UUID,
        organization_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[DocumentShare]:
        """Get documents shared with a specific user."""
        stmt = (
            select(DocumentShare)
            .join(DocumentShare.document)
            .where(
                and_(
                    DocumentShare.shared_with_type == "user",
                    DocumentShare.shared_with_id == str(user_id),
                    DocumentShare.document.organization_id == organization_id,
                    or_(
                        DocumentShare.expires_at.is_(None),
                        DocumentShare.expires_at > func.now()
                    )
                )
            )
            .options(selectinload(DocumentShare.document))
            .order_by(desc(DocumentShare.shared_at))
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def mark_notification_read(
        self,
        share_id: UUID,
        user_id: UUID
    ) -> Optional[DocumentShare]:
        """Mark a share notification as read."""
        share = await self.get_by_id(share_id)
        if share and share.shared_with_id == str(user_id):
            share.mark_notification_read()
            await self.session.flush()
            return share
        return None
    
    async def get_document_shares(
        self,
        document_id: UUID,
        include_expired: bool = False
    ) -> List[DocumentShare]:
        """Get all shares for a document."""
        conditions = [DocumentShare.document_id == document_id]
        
        if not include_expired:
            conditions.append(
                or_(
                    DocumentShare.expires_at.is_(None),
                    DocumentShare.expires_at > func.now()
                )
            )
        
        stmt = (
            select(DocumentShare)
            .where(and_(*conditions))
            .order_by(desc(DocumentShare.shared_at))
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def create_instance(self, share: DocumentShare) -> DocumentShare:
        """Helper method to create a share instance."""
        self.session.add(share)
        await self.session.flush()
        await self.session.refresh(share)
        return share


class CommentRepository(BaseRepository[DocumentComment]):
    """Repository for document comments."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, DocumentComment)
    
    async def create_comment(
        self,
        document_id: UUID,
        author_id: UUID,
        content: str,
        parent_comment_id: Optional[UUID] = None,
        page_number: Optional[int] = None,
        position_data: Optional[Dict[str, Any]] = None
    ) -> DocumentComment:
        """Create a new comment."""
        comment = DocumentComment(
            document_id=document_id,
            author_id=author_id,
            content=content,
            parent_comment_id=parent_comment_id,
            page_number=page_number,
            position_data=position_data or {}
        )
        
        return await self.create_instance(comment)
    
    async def get_document_comments(
        self,
        document_id: UUID,
        include_resolved: bool = True,
        page_number: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[DocumentComment]:
        """Get comments for a document."""
        conditions = [
            DocumentComment.document_id == document_id,
            DocumentComment.status != "deleted"
        ]
        
        if not include_resolved:
            conditions.append(DocumentComment.status != "resolved")
        
        if page_number is not None:
            conditions.append(DocumentComment.page_number == page_number)
        
        stmt = (
            select(DocumentComment)
            .where(and_(*conditions))
            .options(selectinload(DocumentComment.replies))
            .order_by(DocumentComment.created_at)
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_comment_thread(
        self,
        comment_id: UUID
    ) -> List[DocumentComment]:
        """Get a comment and all its replies."""
        # Get the root comment
        root_comment = await self.get_by_id(comment_id)
        if not root_comment:
            return []
        
        # If it's a reply, get the parent
        if root_comment.parent_comment_id:
            root_comment = await self.get_by_id(root_comment.parent_comment_id)
            if not root_comment:
                return []
        
        # Get all replies in the thread
        stmt = (
            select(DocumentComment)
            .where(
                or_(
                    DocumentComment.id == root_comment.id,
                    DocumentComment.parent_comment_id == root_comment.id
                )
            )
            .order_by(DocumentComment.created_at)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def resolve_comment(
        self,
        comment_id: UUID,
        resolved_by: UUID
    ) -> Optional[DocumentComment]:
        """Mark a comment as resolved."""
        comment = await self.get_by_id(comment_id)
        if comment:
            comment.resolve(resolved_by)
            await self.session.flush()
            return comment
        return None
    
    async def unresolve_comment(
        self,
        comment_id: UUID
    ) -> Optional[DocumentComment]:
        """Mark a comment as unresolved."""
        comment = await self.get_by_id(comment_id)
        if comment:
            comment.unresolve()
            await self.session.flush()
            return comment
        return None
    
    async def delete_comment(
        self,
        comment_id: UUID,
        user_id: UUID
    ) -> Optional[DocumentComment]:
        """Soft delete a comment."""
        comment = await self.get_by_id(comment_id)
        if comment and comment.author_id == user_id:
            comment.status = "deleted"
            await self.session.flush()
            return comment
        return None
    
    async def get_user_comments(
        self,
        user_id: UUID,
        organization_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[DocumentComment]:
        """Get comments by a specific user."""
        stmt = (
            select(DocumentComment)
            .join(DocumentComment.document)
            .where(
                and_(
                    DocumentComment.author_id == user_id,
                    DocumentComment.document.organization_id == organization_id,
                    DocumentComment.status != "deleted"
                )
            )
            .order_by(desc(DocumentComment.created_at))
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def create_instance(self, comment: DocumentComment) -> DocumentComment:
        """Helper method to create a comment instance."""
        self.session.add(comment)
        await self.session.flush()
        await self.session.refresh(comment)
        return comment


class ActivityRepository(BaseRepository[DocumentActivity]):
    """Repository for document activities."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, DocumentActivity)
    
    async def log_activity(
        self,
        document_id: UUID,
        user_id: UUID,
        activity_type: str,
        activity_description: str,
        target_user_id: Optional[UUID] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentActivity:
        """Log a document activity."""
        activity = DocumentActivity(
            document_id=document_id,
            user_id=user_id,
            activity_type=activity_type,
            activity_description=activity_description,
            target_user_id=target_user_id,
            metadata=metadata or {}
        )
        
        return await self.create_instance(activity)
    
    async def get_document_activities(
        self,
        document_id: UUID,
        limit: int = 100,
        offset: int = 0,
        activity_types: Optional[List[str]] = None
    ) -> List[DocumentActivity]:
        """Get activities for a document."""
        conditions = [DocumentActivity.document_id == document_id]
        
        if activity_types:
            conditions.append(DocumentActivity.activity_type.in_(activity_types))
        
        stmt = (
            select(DocumentActivity)
            .where(and_(*conditions))
            .order_by(desc(DocumentActivity.created_at))
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_user_activities(
        self,
        user_id: UUID,
        organization_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[DocumentActivity]:
        """Get activities by a specific user."""
        stmt = (
            select(DocumentActivity)
            .join(DocumentActivity.document)
            .where(
                and_(
                    DocumentActivity.user_id == user_id,
                    DocumentActivity.document.organization_id == organization_id
                )
            )
            .order_by(desc(DocumentActivity.created_at))
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_recent_activities(
        self,
        organization_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[DocumentActivity]:
        """Get recent activities across the organization."""
        stmt = (
            select(DocumentActivity)
            .join(DocumentActivity.document)
            .where(DocumentActivity.document.organization_id == organization_id)
            .order_by(desc(DocumentActivity.created_at))
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def create_instance(self, activity: DocumentActivity) -> DocumentActivity:
        """Helper method to create an activity instance."""
        self.session.add(activity)
        await self.session.flush()
        await self.session.refresh(activity)
        return activity


class WorkspaceRepository(BaseRepository[DocumentWorkspace]):
    """Repository for document workspaces."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, DocumentWorkspace)
    
    async def create_workspace(
        self,
        name: str,
        organization_id: UUID,
        created_by: UUID,
        description: Optional[str] = None,
        is_public: bool = False,
        settings: Optional[Dict[str, Any]] = None
    ) -> DocumentWorkspace:
        """Create a new workspace."""
        workspace = DocumentWorkspace(
            name=name,
            organization_id=organization_id,
            created_by=created_by,
            description=description,
            is_public=is_public,
            settings=settings or {}
        )
        
        return await self.create_instance(workspace)
    
    async def get_organization_workspaces(
        self,
        organization_id: UUID,
        include_private: bool = True,
        user_id: Optional[UUID] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[DocumentWorkspace]:
        """Get workspaces for an organization."""
        conditions = [
            DocumentWorkspace.organization_id == organization_id,
            DocumentWorkspace.status == "active"
        ]
        
        if not include_private and user_id:
            # Show public workspaces or workspaces created by the user
            conditions.append(
                or_(
                    DocumentWorkspace.is_public == True,
                    DocumentWorkspace.created_by == user_id
                )
            )
        
        stmt = (
            select(DocumentWorkspace)
            .where(and_(*conditions))
            .order_by(desc(DocumentWorkspace.created_at))
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_user_workspaces(
        self,
        user_id: UUID,
        organization_id: UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[DocumentWorkspace]:
        """Get workspaces created by a specific user."""
        stmt = (
            select(DocumentWorkspace)
            .where(
                and_(
                    DocumentWorkspace.created_by == user_id,
                    DocumentWorkspace.organization_id == organization_id,
                    DocumentWorkspace.status == "active"
                )
            )
            .order_by(desc(DocumentWorkspace.created_at))
            .offset(offset)
            .limit(limit)
        )
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def update_workspace_settings(
        self,
        workspace_id: UUID,
        settings: Dict[str, Any]
    ) -> Optional[DocumentWorkspace]:
        """Update workspace settings."""
        workspace = await self.get_by_id(workspace_id)
        if workspace:
            workspace.settings = settings
            await self.session.flush()
            return workspace
        return None
    
    async def archive_workspace(
        self,
        workspace_id: UUID,
        user_id: UUID
    ) -> Optional[DocumentWorkspace]:
        """Archive a workspace."""
        workspace = await self.get_by_id(workspace_id)
        if workspace and workspace.created_by == user_id:
            workspace.status = "archived"
            await self.session.flush()
            return workspace
        return None
    
    async def create_instance(self, workspace: DocumentWorkspace) -> DocumentWorkspace:
        """Helper method to create a workspace instance."""
        self.session.add(workspace)
        await self.session.flush()
        await self.session.refresh(workspace)
        return workspace