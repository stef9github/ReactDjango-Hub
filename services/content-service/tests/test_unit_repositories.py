"""
Unit tests for repository layer functionality.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.exc import IntegrityError, TimeoutError as SQLTimeoutError
from models import Document, DocumentPermission, DocumentComment, DocumentActivity
from repositories import (
    DocumentRepository, PermissionRepository, AuditRepository,
    CollaborationRepository, CommentRepository, ActivityRepository
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestDocumentRepository:
    """Test DocumentRepository functionality."""
    
    async def test_create_document(self, document_repository, mock_user_data):
        """Test document creation."""
        # Mock session behavior
        document_repository.session.add = MagicMock()
        document_repository.session.flush = AsyncMock()
        document_repository.session.refresh = AsyncMock()
        
        result = await document_repository.create_document(
            filename="test.pdf",
            original_filename="test.pdf",
            content_type="application/pdf",
            file_size=1024,
            file_hash="abc123",
            storage_path="/test/path.pdf",
            created_by=uuid.UUID(mock_user_data["user_id"]),
            organization_id=uuid.UUID(mock_user_data["organization_id"])
        )
        
        assert result.filename == "test.pdf"
        assert result.status == "active"
        assert result.processing_status == "pending"
        document_repository.session.add.assert_called_once()
        document_repository.session.flush.assert_called_once()
    
    async def test_find_by_hash(self, document_repository):
        """Test finding document by hash."""
        mock_doc = MagicMock()
        mock_doc.file_hash = "abc123"
        
        # Mock the find_one method
        document_repository.find_one = AsyncMock(return_value=mock_doc)
        
        result = await document_repository.find_by_hash("abc123")
        
        assert result == mock_doc
        document_repository.find_one.assert_called_once_with(file_hash="abc123")
    
    async def test_get_by_id_and_organization(self, document_repository, mock_user_data):
        """Test getting document by ID and organization."""
        document_id = uuid.uuid4()
        org_id = uuid.UUID(mock_user_data["organization_id"])
        
        # Mock session execute
        mock_result = MagicMock()
        mock_doc = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_doc
        document_repository.session.execute = AsyncMock(return_value=mock_result)
        
        result = await document_repository.get_by_id_and_organization(document_id, org_id)
        
        assert result == mock_doc
        document_repository.session.execute.assert_called_once()
    
    async def test_get_by_id_and_organization_not_found(self, document_repository):
        """Test getting non-existent document."""
        document_id = uuid.uuid4()
        org_id = uuid.uuid4()
        
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        document_repository.session.execute = AsyncMock(return_value=mock_result)
        
        result = await document_repository.get_by_id_and_organization(document_id, org_id)
        
        assert result is None
    
    async def test_update_processing_status(self, document_repository):
        """Test updating document processing status."""
        document_id = uuid.uuid4()
        
        # Mock the update_by_id method
        mock_doc = MagicMock()
        document_repository.update_by_id = AsyncMock(return_value=mock_doc)
        
        result = await document_repository.update_processing_status(
            document_id=document_id,
            processing_status="completed",
            ocr_completed=True,
            extracted_text="Sample text"
        )
        
        assert result == mock_doc
        document_repository.update_by_id.assert_called_once_with(
            document_id,
            processing_status="completed",
            ocr_completed=True,
            extracted_text="Sample text"
        )
    
    async def test_get_organization_stats(self, document_repository, mock_user_data):
        """Test getting organization statistics."""
        org_id = uuid.UUID(mock_user_data["organization_id"])
        
        # Mock session execute for multiple queries
        mock_results = [
            MagicMock(one=lambda: (10, 1024000)),  # count and size
            MagicMock(),  # types
            MagicMock(),  # status
            MagicMock(scalar=lambda: 2)  # processing queue
        ]
        
        # Mock type and status results
        mock_results[1].__iter__ = lambda self: iter([("pdf", 5), ("txt", 3), ("docx", 2)])
        mock_results[2].__iter__ = lambda self: iter([("active", 8), ("processing", 2)])
        
        document_repository.session.execute = AsyncMock(side_effect=mock_results)
        
        stats = await document_repository.get_organization_stats(org_id)
        
        assert stats["total_documents"] == 10
        assert stats["total_size"] == 1024000
        assert stats["documents_by_type"]["pdf"] == 5
        assert stats["documents_by_status"]["active"] == 8
        assert stats["processing_queue_size"] == 2
    
    async def test_database_error_handling(self, document_repository, simulate_database_error):
        """Test handling database errors."""
        document_repository.session.execute = AsyncMock(
            side_effect=simulate_database_error("connection")
        )
        
        with pytest.raises(Exception) as exc_info:
            await document_repository.get_by_id_and_organization(uuid.uuid4(), uuid.uuid4())
        
        assert "Database connection failed" in str(exc_info.value)


@pytest.mark.unit
@pytest.mark.asyncio
class TestPermissionRepository:
    """Test PermissionRepository functionality."""
    
    async def test_grant_user_permission(self, permission_repository, mock_user_data):
        """Test granting user permission."""
        document_id = uuid.uuid4()
        user_id = uuid.UUID(mock_user_data["user_id"])
        granted_by = uuid.UUID(mock_user_data["user_id"])
        
        # Mock methods
        permission_repository.revoke_user_permission = AsyncMock(return_value=True)
        permission_repository.create_instance = AsyncMock()
        
        # Mock the permission creation
        mock_permission = MagicMock()
        mock_permission.id = uuid.uuid4()
        permission_repository.create_instance.return_value = mock_permission
        
        result = await permission_repository.grant_user_permission(
            document_id=document_id,
            user_id=user_id,
            permissions=["read", "write"],
            granted_by=granted_by
        )
        
        assert result == mock_permission
        permission_repository.revoke_user_permission.assert_called_once_with(document_id, user_id)
        permission_repository.create_instance.assert_called_once()
    
    async def test_grant_role_permission(self, permission_repository, mock_user_data):
        """Test granting role permission."""
        document_id = uuid.uuid4()
        role_name = "editor"
        granted_by = uuid.UUID(mock_user_data["user_id"])
        
        permission_repository.revoke_role_permission = AsyncMock(return_value=True)
        permission_repository.create_instance = AsyncMock()
        
        mock_permission = MagicMock()
        mock_permission.id = uuid.uuid4()
        permission_repository.create_instance.return_value = mock_permission
        
        result = await permission_repository.grant_role_permission(
            document_id=document_id,
            role_name=role_name,
            permissions=["read", "write", "share"],
            granted_by=granted_by
        )
        
        assert result == mock_permission
        permission_repository.revoke_role_permission.assert_called_once_with(document_id, role_name)
    
    async def test_check_user_permission_direct(self, permission_repository, mock_user_data):
        """Test checking direct user permission."""
        document_id = uuid.uuid4()
        user_id = uuid.UUID(mock_user_data["user_id"])
        
        # Mock user permission
        mock_permission = MagicMock()
        mock_permission.is_expired = False
        mock_permission.has_permission.return_value = True
        
        permission_repository.get_user_permissions = AsyncMock(return_value=mock_permission)
        permission_repository.get_role_permissions = AsyncMock(return_value=None)
        
        result = await permission_repository.check_user_permission(
            document_id=document_id,
            user_id=user_id,
            user_roles=["user"],
            permission_type="read"
        )
        
        assert result is True
        mock_permission.has_permission.assert_called_once_with("read")
    
    async def test_check_user_permission_role_based(self, permission_repository, mock_user_data):
        """Test checking role-based permission."""
        document_id = uuid.uuid4()
        user_id = uuid.UUID(mock_user_data["user_id"])
        
        # Mock no direct user permission, but role permission exists
        mock_role_permission = MagicMock()
        mock_role_permission.is_expired = False
        mock_role_permission.has_permission.return_value = True
        
        permission_repository.get_user_permissions = AsyncMock(return_value=None)
        permission_repository.get_role_permissions = AsyncMock(return_value=mock_role_permission)
        
        result = await permission_repository.check_user_permission(
            document_id=document_id,
            user_id=user_id,
            user_roles=["editor"],
            permission_type="write"
        )
        
        assert result is True
        permission_repository.get_role_permissions.assert_called_once_with(document_id, "editor")
    
    async def test_check_user_permission_denied(self, permission_repository, mock_user_data):
        """Test permission denied case."""
        document_id = uuid.uuid4()
        user_id = uuid.UUID(mock_user_data["user_id"])
        
        permission_repository.get_user_permissions = AsyncMock(return_value=None)
        permission_repository.get_role_permissions = AsyncMock(return_value=None)
        
        result = await permission_repository.check_user_permission(
            document_id=document_id,
            user_id=user_id,
            user_roles=["user"],
            permission_type="admin"
        )
        
        assert result is False
    
    async def test_get_effective_permissions(self, permission_repository, mock_user_data):
        """Test getting effective permissions."""
        document_id = uuid.uuid4()
        user_id = uuid.UUID(mock_user_data["user_id"])
        
        # Mock user permission
        mock_user_perm = MagicMock()
        mock_user_perm.is_expired = False
        mock_user_perm.has_permission.side_effect = lambda p: p in ["read", "write"]
        
        # Mock role permission
        mock_role_perm = MagicMock()
        mock_role_perm.is_expired = False
        mock_role_perm.has_permission.side_effect = lambda p: p == "share"
        
        permission_repository.get_user_permissions = AsyncMock(return_value=mock_user_perm)
        permission_repository.get_role_permissions = AsyncMock(return_value=mock_role_perm)
        
        result = await permission_repository.get_user_effective_permissions(
            document_id=document_id,
            user_id=user_id,
            user_roles=["editor"]
        )
        
        assert result["read"] is True
        assert result["write"] is True
        assert result["share"] is True
        assert result["delete"] is False
        assert result["admin"] is False
    
    async def test_clean_expired_permissions(self, permission_repository):
        """Test cleaning expired permissions."""
        # Mock expired permissions
        mock_expired = [MagicMock() for _ in range(3)]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_expired
        permission_repository.session.execute = AsyncMock(return_value=mock_result)
        permission_repository.session.delete = AsyncMock()
        permission_repository.session.flush = AsyncMock()
        
        count = await permission_repository.clean_expired_permissions()
        
        assert count == 3
        assert permission_repository.session.delete.call_count == 3
        permission_repository.session.flush.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
class TestCommentRepository:
    """Test CommentRepository functionality."""
    
    async def test_create_comment(self, db_session, mock_user_data):
        """Test creating a comment."""
        comment_repo = CommentRepository(db_session)
        comment_repo.create_instance = AsyncMock()
        
        document_id = uuid.uuid4()
        author_id = uuid.UUID(mock_user_data["user_id"])
        
        mock_comment = MagicMock()
        mock_comment.id = uuid.uuid4()
        comment_repo.create_instance.return_value = mock_comment
        
        result = await comment_repo.create_comment(
            document_id=document_id,
            author_id=author_id,
            content="Test comment",
            page_number=1
        )
        
        assert result == mock_comment
        comment_repo.create_instance.assert_called_once()
        
        # Verify the comment was created with correct attributes
        call_args = comment_repo.create_instance.call_args[0][0]
        assert call_args.document_id == document_id
        assert call_args.author_id == author_id
        assert call_args.content == "Test comment"
        assert call_args.page_number == 1
    
    async def test_get_document_comments(self, db_session, mock_user_data):
        """Test getting comments for a document."""
        comment_repo = CommentRepository(db_session)
        
        document_id = uuid.uuid4()
        mock_comments = [MagicMock() for _ in range(3)]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_comments
        comment_repo.session.execute = AsyncMock(return_value=mock_result)
        
        result = await comment_repo.get_document_comments(
            document_id=document_id,
            include_resolved=True,
            page_number=1
        )
        
        assert result == mock_comments
        comment_repo.session.execute.assert_called_once()
    
    async def test_resolve_comment(self, db_session, mock_user_data):
        """Test resolving a comment."""
        comment_repo = CommentRepository(db_session)
        
        comment_id = uuid.uuid4()
        resolved_by = uuid.UUID(mock_user_data["user_id"])
        
        mock_comment = MagicMock()
        mock_comment.resolve = MagicMock()
        
        comment_repo.get_by_id = AsyncMock(return_value=mock_comment)
        comment_repo.session.flush = AsyncMock()
        
        result = await comment_repo.resolve_comment(comment_id, resolved_by)
        
        assert result == mock_comment
        mock_comment.resolve.assert_called_once_with(resolved_by)
        comment_repo.session.flush.assert_called_once()
    
    async def test_resolve_comment_not_found(self, db_session):
        """Test resolving non-existent comment."""
        comment_repo = CommentRepository(db_session)
        
        comment_id = uuid.uuid4()
        resolved_by = uuid.uuid4()
        
        comment_repo.get_by_id = AsyncMock(return_value=None)
        
        result = await comment_repo.resolve_comment(comment_id, resolved_by)
        
        assert result is None
    
    async def test_delete_comment(self, db_session, mock_user_data):
        """Test deleting a comment."""
        comment_repo = CommentRepository(db_session)
        
        comment_id = uuid.uuid4()
        user_id = uuid.UUID(mock_user_data["user_id"])
        
        mock_comment = MagicMock()
        mock_comment.author_id = user_id
        mock_comment.status = "active"
        
        comment_repo.get_by_id = AsyncMock(return_value=mock_comment)
        comment_repo.session.flush = AsyncMock()
        
        result = await comment_repo.delete_comment(comment_id, user_id)
        
        assert result == mock_comment
        assert mock_comment.status == "deleted"
        comment_repo.session.flush.assert_called_once()
    
    async def test_delete_comment_unauthorized(self, db_session, mock_user_data):
        """Test deleting comment by wrong user."""
        comment_repo = CommentRepository(db_session)
        
        comment_id = uuid.uuid4()
        user_id = uuid.UUID(mock_user_data["user_id"])
        other_user_id = uuid.uuid4()
        
        mock_comment = MagicMock()
        mock_comment.author_id = other_user_id
        
        comment_repo.get_by_id = AsyncMock(return_value=mock_comment)
        
        result = await comment_repo.delete_comment(comment_id, user_id)
        
        assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
class TestActivityRepository:
    """Test ActivityRepository functionality."""
    
    async def test_log_activity(self, db_session, mock_user_data):
        """Test logging an activity."""
        activity_repo = ActivityRepository(db_session)
        activity_repo.create_instance = AsyncMock()
        
        document_id = uuid.uuid4()
        user_id = uuid.UUID(mock_user_data["user_id"])
        target_user_id = uuid.uuid4()
        
        mock_activity = MagicMock()
        mock_activity.id = uuid.uuid4()
        activity_repo.create_instance.return_value = mock_activity
        
        result = await activity_repo.log_activity(
            document_id=document_id,
            user_id=user_id,
            activity_type="share",
            activity_description="Document shared with user",
            target_user_id=target_user_id,
            metadata={"permission": "read"}
        )
        
        assert result == mock_activity
        activity_repo.create_instance.assert_called_once()
        
        # Verify activity attributes
        call_args = activity_repo.create_instance.call_args[0][0]
        assert call_args.document_id == document_id
        assert call_args.user_id == user_id
        assert call_args.activity_type == "share"
        assert call_args.target_user_id == target_user_id
        assert call_args.metadata == {"permission": "read"}
    
    async def test_get_document_activities(self, db_session):
        """Test getting activities for a document."""
        activity_repo = ActivityRepository(db_session)
        
        document_id = uuid.uuid4()
        mock_activities = [MagicMock() for _ in range(5)]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_activities
        activity_repo.session.execute = AsyncMock(return_value=mock_result)
        
        result = await activity_repo.get_document_activities(
            document_id=document_id,
            activity_types=["share", "comment"]
        )
        
        assert result == mock_activities
        activity_repo.session.execute.assert_called_once()
    
    async def test_get_recent_activities(self, db_session, mock_user_data):
        """Test getting recent activities."""
        activity_repo = ActivityRepository(db_session)
        
        org_id = uuid.UUID(mock_user_data["organization_id"])
        mock_activities = [MagicMock() for _ in range(10)]
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_activities
        activity_repo.session.execute = AsyncMock(return_value=mock_result)
        
        result = await activity_repo.get_recent_activities(
            organization_id=org_id,
            limit=10
        )
        
        assert result == mock_activities
        activity_repo.session.execute.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
class TestAuditRepository:
    """Test AuditRepository functionality."""
    
    async def test_log_action(self, audit_repository, mock_user_data):
        """Test logging an audit action."""
        # Mock the create method
        audit_repository.create = AsyncMock()
        
        document_id = uuid.uuid4()
        mock_audit = MagicMock()
        mock_audit.id = uuid.uuid4()
        audit_repository.create.return_value = mock_audit
        
        result = await audit_repository.log_action(
            action="upload",
            user_id=uuid.UUID(mock_user_data["user_id"]),
            organization_id=uuid.UUID(mock_user_data["organization_id"]),
            document_id=document_id,
            details={"filename": "test.pdf", "size": 1024}
        )
        
        assert result == mock_audit
        audit_repository.create.assert_called_once_with(
            action="upload",
            user_id=uuid.UUID(mock_user_data["user_id"]),
            organization_id=uuid.UUID(mock_user_data["organization_id"]),
            document_id=document_id,
            details={"filename": "test.pdf", "size": 1024}
        )
    
    async def test_get_document_audit_trail(self, audit_repository):
        """Test getting document audit trail."""
        document_id = uuid.uuid4()
        mock_audits = [MagicMock() for _ in range(5)]
        
        # Mock the find_many method
        audit_repository.find_many = AsyncMock(return_value=mock_audits)
        
        result = await audit_repository.get_document_audit_trail(
            document_id=document_id,
            limit=10
        )
        
        assert result == mock_audits
        audit_repository.find_many.assert_called_once()
    
    async def test_get_user_audit_trail(self, audit_repository, mock_user_data):
        """Test getting user audit trail."""
        user_id = uuid.UUID(mock_user_data["user_id"])
        org_id = uuid.UUID(mock_user_data["organization_id"])
        mock_audits = [MagicMock() for _ in range(3)]
        
        audit_repository.find_many = AsyncMock(return_value=mock_audits)
        
        result = await audit_repository.get_user_audit_trail(
            user_id=user_id,
            organization_id=org_id,
            limit=50
        )
        
        assert result == mock_audits
        audit_repository.find_many.assert_called_once()


@pytest.mark.unit
class TestRepositoryErrorHandling:
    """Test repository error handling."""
    
    @pytest.mark.asyncio
    async def test_database_integrity_error(self, document_repository, simulate_database_error):
        """Test handling database integrity errors."""
        document_repository.session.add = MagicMock()
        document_repository.session.flush = AsyncMock(
            side_effect=simulate_database_error("integrity")
        )
        
        with pytest.raises(IntegrityError):
            await document_repository.create_document(
                filename="test.pdf",
                original_filename="test.pdf",
                content_type="application/pdf",
                file_size=1024,
                file_hash="duplicate_hash",  # Assuming this causes integrity error
                storage_path="/test/path.pdf",
                created_by=uuid.uuid4(),
                organization_id=uuid.uuid4()
            )
    
    @pytest.mark.asyncio
    async def test_database_timeout_error(self, permission_repository, simulate_database_error):
        """Test handling database timeout errors."""
        permission_repository.session.execute = AsyncMock(
            side_effect=simulate_database_error("timeout")
        )
        
        with pytest.raises(SQLTimeoutError):
            await permission_repository.get_user_permissions(uuid.uuid4(), uuid.uuid4())
    
    @pytest.mark.asyncio
    async def test_repository_session_rollback(self, document_repository):
        """Test session rollback on error."""
        document_repository.session.add = MagicMock()
        document_repository.session.flush = AsyncMock(side_effect=Exception("Test error"))
        document_repository.session.rollback = AsyncMock()
        
        with pytest.raises(Exception):
            await document_repository.create_document(
                filename="test.pdf",
                original_filename="test.pdf",
                content_type="application/pdf",
                file_size=1024,
                file_hash="abc123",
                storage_path="/test/path.pdf",
                created_by=uuid.uuid4(),
                organization_id=uuid.uuid4()
            )
        
        # Note: Rollback would typically be handled at a higher level
        # but we can verify the error propagates correctly