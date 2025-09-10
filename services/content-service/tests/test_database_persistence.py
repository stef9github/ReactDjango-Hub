"""
Database persistence and integration tests for content service.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from models import (
    Document, DocumentVersion, DocumentPermission, DocumentShare,
    DocumentComment, DocumentActivity, DocumentAudit
)
from repositories import DocumentRepository, PermissionRepository, AuditRepository


@pytest.mark.database
@pytest.mark.asyncio
class TestDocumentPersistence:
    """Test document model persistence."""
    
    async def test_create_document(self, db_session, mock_user_data):
        """Test creating and persisting a document."""
        document = Document(
            filename="test_document.pdf",
            original_filename="test_document.pdf",
            content_type="application/pdf",
            file_size=2048,
            file_hash="sha256hash123",
            storage_path="/storage/test_document.pdf",
            created_by=uuid.UUID(mock_user_data["user_id"]),
            organization_id=uuid.UUID(mock_user_data["organization_id"])
        )
        
        db_session.add(document)
        await db_session.commit()
        await db_session.refresh(document)
        
        # Verify document was saved
        assert document.id is not None
        assert document.filename == "test_document.pdf"
        assert document.status == "active"
        assert document.processing_status == "pending"
        assert document.created_at is not None
        assert document.updated_at is not None
    
    async def test_document_constraints(self, db_session, mock_user_data):
        """Test document model constraints."""
        # Test positive file size constraint
        document = Document(
            filename="test.pdf",
            original_filename="test.pdf",
            content_type="application/pdf",
            file_size=-100,  # Invalid: negative size
            file_hash="hash123",
            storage_path="/path/test.pdf",
            created_by=uuid.UUID(mock_user_data["user_id"]),
            organization_id=uuid.UUID(mock_user_data["organization_id"])
        )
        
        db_session.add(document)
        
        with pytest.raises(Exception):  # Should violate check constraint
            await db_session.commit()
        
        await db_session.rollback()
    
    async def test_document_unique_hash(self, db_session, mock_user_data):
        """Test document hash uniqueness constraint."""
        # Create first document
        doc1 = Document(
            filename="doc1.pdf",
            original_filename="doc1.pdf",
            content_type="application/pdf",
            file_size=1024,
            file_hash="duplicate_hash",
            storage_path="/path/doc1.pdf",
            created_by=uuid.UUID(mock_user_data["user_id"]),
            organization_id=uuid.UUID(mock_user_data["organization_id"])
        )
        
        db_session.add(doc1)
        await db_session.commit()
        
        # Try to create second document with same hash
        doc2 = Document(
            filename="doc2.pdf",
            original_filename="doc2.pdf",
            content_type="application/pdf",
            file_size=2048,
            file_hash="duplicate_hash",  # Same hash
            storage_path="/path/doc2.pdf",
            created_by=uuid.UUID(mock_user_data["user_id"]),
            organization_id=uuid.UUID(mock_user_data["organization_id"])
        )
        
        db_session.add(doc2)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
        
        await db_session.rollback()
    
    async def test_document_metadata_json(self, db_session, mock_user_data):
        """Test document metadata JSONB field."""
        metadata = {
            "author": "Test Author",
            "keywords": ["test", "document"],
            "pages": 10,
            "extraction_info": {
                "method": "OCR",
                "confidence": 0.95
            }
        }
        
        document = Document(
            filename="metadata_test.pdf",
            original_filename="metadata_test.pdf",
            content_type="application/pdf",
            file_size=1024,
            file_hash="metadata_hash",
            storage_path="/path/metadata_test.pdf",
            created_by=uuid.UUID(mock_user_data["user_id"]),
            organization_id=uuid.UUID(mock_user_data["organization_id"]),
            metadata=metadata
        )
        
        db_session.add(document)
        await db_session.commit()
        await db_session.refresh(document)
        
        # Verify metadata was stored and retrieved correctly
        assert document.metadata["author"] == "Test Author"
        assert document.metadata["pages"] == 10
        assert document.metadata["extraction_info"]["confidence"] == 0.95
        
        # Test metadata update
        document.metadata["pages"] = 15
        document.metadata["new_field"] = "new_value"
        await db_session.commit()
        await db_session.refresh(document)
        
        assert document.metadata["pages"] == 15
        assert document.metadata["new_field"] == "new_value"
    
    async def test_document_version_relationship(self, db_session, sample_document):
        """Test document-version relationship."""
        # Create document version
        version = DocumentVersion(
            document_id=sample_document.id,
            version_number=2,
            filename="test_document_v2.pdf",
            storage_path="/storage/test_document_v2.pdf",
            file_size=2048,
            file_hash="version2_hash",
            created_by=sample_document.created_by,
            change_summary="Updated content"
        )
        
        db_session.add(version)
        await db_session.commit()
        await db_session.refresh(version)
        
        # Verify relationship
        await db_session.refresh(sample_document)
        assert len(sample_document.versions) == 1
        assert sample_document.versions[0].version_number == 2
        assert sample_document.current_version == 2
    
    async def test_document_cascade_delete(self, db_session, sample_document):
        """Test cascade delete of related entities."""
        # Create related entities
        version = DocumentVersion(
            document_id=sample_document.id,
            version_number=2,
            filename="test_v2.pdf",
            storage_path="/path/v2.pdf",
            file_size=1024,
            file_hash="v2_hash",
            created_by=sample_document.created_by
        )
        
        permission = DocumentPermission.create_user_permission(
            document_id=sample_document.id,
            user_id=sample_document.created_by,
            granted_by=sample_document.created_by,
            permissions=["read"]
        )
        
        db_session.add(version)
        db_session.add(permission)
        await db_session.commit()
        
        # Delete document
        await db_session.delete(sample_document)
        await db_session.commit()
        
        # Verify cascaded deletions
        version_count = await db_session.scalar(
            select(func.count(DocumentVersion.id)).where(
                DocumentVersion.document_id == sample_document.id
            )
        )
        permission_count = await db_session.scalar(
            select(func.count(DocumentPermission.id)).where(
                DocumentPermission.document_id == sample_document.id
            )
        )
        
        assert version_count == 0
        assert permission_count == 0


@pytest.mark.database
@pytest.mark.asyncio
class TestPermissionPersistence:
    """Test permission model persistence."""
    
    async def test_create_user_permission(self, db_session, sample_document, mock_user_data):
        """Test creating user permission."""
        permission = DocumentPermission.create_user_permission(
            document_id=sample_document.id,
            user_id=uuid.UUID(mock_user_data["user_id"]),
            granted_by=sample_document.created_by,
            permissions=["read", "write", "share"]
        )
        
        db_session.add(permission)
        await db_session.commit()
        await db_session.refresh(permission)
        
        assert permission.id is not None
        assert permission.user_id == uuid.UUID(mock_user_data["user_id"])
        assert permission.role_name is None
        assert permission.can_read is True
        assert permission.can_write is True
        assert permission.can_share is True
        assert permission.can_delete is False
        assert permission.can_admin is False
    
    async def test_create_role_permission(self, db_session, sample_document):
        """Test creating role permission."""
        permission = DocumentPermission.create_role_permission(
            document_id=sample_document.id,
            role_name="editor",
            granted_by=sample_document.created_by,
            permissions=["read", "write", "delete"]
        )
        
        db_session.add(permission)
        await db_session.commit()
        await db_session.refresh(permission)
        
        assert permission.id is not None
        assert permission.user_id is None
        assert permission.role_name == "editor"
        assert permission.can_read is True
        assert permission.can_write is True
        assert permission.can_delete is True
        assert permission.can_share is False
    
    async def test_permission_constraints(self, db_session, sample_document):
        """Test permission model constraints."""
        # Test constraint: either user_id or role_name, not both
        permission = DocumentPermission(
            document_id=sample_document.id,
            user_id=uuid.uuid4(),
            role_name="editor",  # Both set - should fail
            granted_by=sample_document.created_by,
            can_read=True
        )
        
        db_session.add(permission)
        
        with pytest.raises(Exception):  # Should violate check constraint
            await db_session.commit()
        
        await db_session.rollback()
    
    async def test_permission_expiration(self, db_session, sample_document, mock_user_data):
        """Test permission expiration functionality."""
        # Create permission with future expiration
        future_expiration = datetime.utcnow() + timedelta(hours=1)
        permission = DocumentPermission.create_user_permission(
            document_id=sample_document.id,
            user_id=uuid.UUID(mock_user_data["user_id"]),
            granted_by=sample_document.created_by,
            permissions=["read"],
            expires_at=future_expiration
        )
        
        db_session.add(permission)
        await db_session.commit()
        await db_session.refresh(permission)
        
        # Should not be expired
        assert permission.is_expired is False
        
        # Create permission with past expiration
        past_expiration = datetime.utcnow() - timedelta(hours=1)
        expired_permission = DocumentPermission.create_user_permission(
            document_id=sample_document.id,
            user_id=uuid.uuid4(),
            granted_by=sample_document.created_by,
            permissions=["read"],
            expires_at=past_expiration
        )
        
        db_session.add(expired_permission)
        await db_session.commit()
        await db_session.refresh(expired_permission)
        
        # Should be expired
        assert expired_permission.is_expired is True
    
    async def test_permission_unique_constraints(self, db_session, sample_document, mock_user_data):
        """Test permission unique constraints."""
        user_id = uuid.UUID(mock_user_data["user_id"])
        
        # Create first permission for user
        perm1 = DocumentPermission.create_user_permission(
            document_id=sample_document.id,
            user_id=user_id,
            granted_by=sample_document.created_by,
            permissions=["read"]
        )
        
        db_session.add(perm1)
        await db_session.commit()
        
        # Try to create second permission for same user/document
        perm2 = DocumentPermission.create_user_permission(
            document_id=sample_document.id,
            user_id=user_id,  # Same user/document combination
            granted_by=sample_document.created_by,
            permissions=["write"]
        )
        
        db_session.add(perm2)
        
        with pytest.raises(IntegrityError):  # Should violate unique constraint
            await db_session.commit()
        
        await db_session.rollback()


@pytest.mark.database
@pytest.mark.asyncio
class TestCollaborationPersistence:
    """Test collaboration model persistence."""
    
    async def test_create_comment(self, db_session, sample_document, mock_user_data):
        """Test creating document comment."""
        comment = DocumentComment(
            document_id=sample_document.id,
            author_id=uuid.UUID(mock_user_data["user_id"]),
            content="This is a test comment with detailed feedback.",
            page_number=5,
            position_data={
                "x": 100,
                "y": 200,
                "width": 150,
                "height": 50,
                "selection_text": "highlighted text"
            }
        )
        
        db_session.add(comment)
        await db_session.commit()
        await db_session.refresh(comment)
        
        assert comment.id is not None
        assert comment.content == "This is a test comment with detailed feedback."
        assert comment.page_number == 5
        assert comment.position_data["x"] == 100
        assert comment.status == "active"
        assert comment.is_resolved is False
    
    async def test_comment_threading(self, db_session, sample_document, mock_user_data):
        """Test comment threading (parent-child relationship)."""
        # Create parent comment
        parent_comment = DocumentComment(
            document_id=sample_document.id,
            author_id=uuid.UUID(mock_user_data["user_id"]),
            content="Parent comment"
        )
        
        db_session.add(parent_comment)
        await db_session.commit()
        await db_session.refresh(parent_comment)
        
        # Create reply comment
        reply_comment = DocumentComment(
            document_id=sample_document.id,
            author_id=uuid.UUID(mock_user_data["user_id"]),
            content="Reply to parent comment",
            parent_comment_id=parent_comment.id
        )
        
        db_session.add(reply_comment)
        await db_session.commit()
        await db_session.refresh(reply_comment)
        await db_session.refresh(parent_comment)
        
        # Verify relationship
        assert reply_comment.parent_comment_id == parent_comment.id
        assert len(parent_comment.replies) == 1
        assert parent_comment.replies[0].id == reply_comment.id
    
    async def test_comment_resolution(self, db_session, sample_document, mock_user_data):
        """Test comment resolution functionality."""
        comment = DocumentComment(
            document_id=sample_document.id,
            author_id=uuid.UUID(mock_user_data["user_id"]),
            content="Issue to be resolved"
        )
        
        db_session.add(comment)
        await db_session.commit()
        await db_session.refresh(comment)
        
        # Resolve comment
        resolver_id = uuid.uuid4()
        comment.resolve(resolver_id)
        await db_session.commit()
        await db_session.refresh(comment)
        
        assert comment.is_resolved is True
        assert comment.resolved_by == resolver_id
        assert comment.resolved_at is not None
        assert comment.status == "resolved"
        
        # Unresolve comment
        comment.unresolve()
        await db_session.commit()
        await db_session.refresh(comment)
        
        assert comment.is_resolved is False
        assert comment.resolved_by is None
        assert comment.resolved_at is None
        assert comment.status == "active"
    
    async def test_document_activity_logging(self, db_session, sample_document, mock_user_data):
        """Test document activity persistence."""
        activity = DocumentActivity(
            document_id=sample_document.id,
            user_id=uuid.UUID(mock_user_data["user_id"]),
            activity_type="comment",
            activity_description="User added a comment to the document",
            target_user_id=uuid.uuid4(),
            metadata={
                "comment_id": str(uuid.uuid4()),
                "page_number": 3,
                "word_count": 25
            }
        )
        
        db_session.add(activity)
        await db_session.commit()
        await db_session.refresh(activity)
        
        assert activity.id is not None
        assert activity.activity_type == "comment"
        assert activity.metadata["page_number"] == 3
        assert activity.created_at is not None
    
    async def test_document_share_notification(self, db_session, sample_document, sample_permission, mock_user_data):
        """Test document share notification persistence."""
        share = DocumentShare(
            document_id=sample_document.id,
            permission_id=sample_permission.id,
            shared_by=sample_document.created_by,
            shared_with_type="user",
            shared_with_id=mock_user_data["user_id"],
            share_message="Please review this document",
            access_level="read",
            expires_at=datetime.utcnow() + timedelta(days=7),
            metadata={"urgency": "high", "context": "project_alpha"}
        )
        
        db_session.add(share)
        await db_session.commit()
        await db_session.refresh(share)
        
        assert share.id is not None
        assert share.shared_with_type == "user"
        assert share.notification_status.value == "pending"
        assert share.metadata["urgency"] == "high"
        
        # Test notification status update
        share.mark_notification_sent()
        await db_session.commit()
        await db_session.refresh(share)
        
        assert share.notification_status.value == "sent"
        assert share.notification_sent_at is not None


@pytest.mark.database
@pytest.mark.asyncio
class TestRepositoryIntegration:
    """Integration tests for repositories with real database."""
    
    async def test_document_repository_integration(self, db_session, mock_user_data):
        """Test document repository with real database operations."""
        repo = DocumentRepository(db_session)
        
        # Create document
        document = await repo.create_document(
            filename="integration_test.pdf",
            original_filename="integration_test.pdf",
            content_type="application/pdf",
            file_size=4096,
            file_hash="integration_hash",
            storage_path="/storage/integration_test.pdf",
            created_by=uuid.UUID(mock_user_data["user_id"]),
            organization_id=uuid.UUID(mock_user_data["organization_id"])
        )
        
        assert document.id is not None
        
        # Find by hash
        found_doc = await repo.find_by_hash("integration_hash")
        assert found_doc.id == document.id
        
        # Get by organization
        org_docs = await repo.find_by_organization(
            organization_id=uuid.UUID(mock_user_data["organization_id"]),
            limit=10
        )
        assert len(org_docs) >= 1
        assert document.id in [doc.id for doc in org_docs]
        
        # Update processing status
        updated_doc = await repo.update_processing_status(
            document_id=document.id,
            processing_status="completed",
            ocr_completed=True,
            extracted_text="Sample extracted text content"
        )
        
        assert updated_doc.processing_status == "completed"
        assert updated_doc.ocr_completed is True
        assert updated_doc.extracted_text == "Sample extracted text content"
        
        # Get organization stats
        stats = await repo.get_organization_stats(
            uuid.UUID(mock_user_data["organization_id"])
        )
        
        assert stats["total_documents"] >= 1
        assert stats["total_size"] >= 4096
        assert "application/pdf" in str(stats["documents_by_type"])
    
    async def test_permission_repository_integration(self, db_session, sample_document, mock_user_data):
        """Test permission repository with real database operations."""
        repo = PermissionRepository(db_session)
        
        user_id = uuid.UUID(mock_user_data["user_id"])
        other_user_id = uuid.uuid4()
        
        # Grant user permission
        permission = await repo.grant_user_permission(
            document_id=sample_document.id,
            user_id=other_user_id,
            permissions=["read", "write"],
            granted_by=user_id
        )
        
        assert permission.id is not None
        assert permission.can_read is True
        assert permission.can_write is True
        
        # Check permission
        has_read = await repo.check_user_permission(
            document_id=sample_document.id,
            user_id=other_user_id,
            user_roles=[],
            permission_type="read"
        )
        
        assert has_read is True
        
        # Grant role permission
        role_permission = await repo.grant_role_permission(
            document_id=sample_document.id,
            role_name="editor",
            permissions=["read", "write", "share"],
            granted_by=user_id
        )
        
        assert role_permission.role_name == "editor"
        assert role_permission.can_share is True
        
        # Check role-based permission
        has_share = await repo.check_user_permission(
            document_id=sample_document.id,
            user_id=uuid.uuid4(),  # Different user
            user_roles=["editor"],
            permission_type="share"
        )
        
        assert has_share is True
        
        # Get effective permissions
        effective_perms = await repo.get_user_effective_permissions(
            document_id=sample_document.id,
            user_id=other_user_id,
            user_roles=["editor"]
        )
        
        assert effective_perms["read"] is True
        assert effective_perms["write"] is True
        assert effective_perms["share"] is True  # From role
        
        # Get permission summary
        summary = await repo.get_permission_summary(sample_document.id)
        
        assert summary["total_permissions"] >= 2
        assert len(summary["user_permissions"]) >= 1
        assert len(summary["role_permissions"]) >= 1
    
    async def test_audit_repository_integration(self, db_session, sample_document, mock_user_data):
        """Test audit repository with real database operations."""
        repo = AuditRepository(db_session)
        
        user_id = uuid.UUID(mock_user_data["user_id"])
        org_id = uuid.UUID(mock_user_data["organization_id"])
        
        # Log audit actions
        audit1 = await repo.log_action(
            action="upload",
            user_id=user_id,
            organization_id=org_id,
            document_id=sample_document.id,
            details={"filename": "test.pdf", "size": 1024}
        )
        
        audit2 = await repo.log_action(
            action="download",
            user_id=user_id,
            organization_id=org_id,
            document_id=sample_document.id,
            details={"ip_address": "192.168.1.1"}
        )
        
        assert audit1.id is not None
        assert audit2.id is not None
        
        # Get document audit trail
        trail = await repo.get_document_audit_trail(
            document_id=sample_document.id,
            limit=10
        )
        
        assert len(trail) >= 2
        actions = [audit.action for audit in trail]
        assert "upload" in actions
        assert "download" in actions
        
        # Get user audit trail
        user_trail = await repo.get_user_audit_trail(
            user_id=user_id,
            organization_id=org_id,
            limit=50
        )
        
        assert len(user_trail) >= 2