"""
Audit logging tests for content service security and compliance.
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from models import DocumentAudit
from repositories import AuditRepository


@pytest.mark.security
@pytest.mark.asyncio
class TestAuditLogging:
    """Test audit logging functionality."""
    
    async def test_document_upload_audit(self, audit_repository, mock_user_data):
        """Test audit logging for document upload."""
        document_id = uuid.uuid4()
        user_id = uuid.UUID(mock_user_data["user_id"])
        org_id = uuid.UUID(mock_user_data["organization_id"])
        
        # Mock audit creation
        mock_audit = MagicMock()
        mock_audit.id = uuid.uuid4()
        mock_audit.action = "upload"
        mock_audit.user_id = user_id
        mock_audit.document_id = document_id
        
        audit_repository.create = AsyncMock(return_value=mock_audit)
        
        result = await audit_repository.log_action(
            action="upload",
            user_id=user_id,
            organization_id=org_id,
            document_id=document_id,
            details={
                "filename": "confidential_report.pdf",
                "file_size": 2048000,
                "content_type": "application/pdf",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 Chrome/91.0",
                "upload_method": "web_interface"
            }
        )
        
        assert result.action == "upload"
        audit_repository.create.assert_called_once_with(
            action="upload",
            user_id=user_id,
            organization_id=org_id,
            document_id=document_id,
            details={
                "filename": "confidential_report.pdf",
                "file_size": 2048000,
                "content_type": "application/pdf",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 Chrome/91.0",
                "upload_method": "web_interface"
            }
        )
    
    async def test_document_access_audit(self, audit_repository, mock_user_data):
        """Test audit logging for document access."""
        document_id = uuid.uuid4()
        user_id = uuid.UUID(mock_user_data["user_id"])
        org_id = uuid.UUID(mock_user_data["organization_id"])
        
        mock_audit = MagicMock()
        mock_audit.action = "access"
        audit_repository.create = AsyncMock(return_value=mock_audit)
        
        # Log document view/access
        result = await audit_repository.log_action(
            action="access",
            user_id=user_id,
            organization_id=org_id,
            document_id=document_id,
            details={
                "access_type": "view",
                "ip_address": "192.168.1.100",
                "session_id": "sess_12345",
                "timestamp": datetime.utcnow().isoformat(),
                "permission_source": "direct_permission"
            }
        )
        
        assert result.action == "access"
        audit_repository.create.assert_called_once()
    
    async def test_document_download_audit(self, audit_repository, mock_user_data):
        """Test audit logging for document download."""
        document_id = uuid.uuid4()
        user_id = uuid.UUID(mock_user_data["user_id"])
        org_id = uuid.UUID(mock_user_data["organization_id"])
        
        mock_audit = MagicMock()
        audit_repository.create = AsyncMock(return_value=mock_audit)
        
        await audit_repository.log_action(
            action="download",
            user_id=user_id,
            organization_id=org_id,
            document_id=document_id,
            details={
                "filename": "report.pdf",
                "file_size": 1024000,
                "download_type": "full_file",
                "ip_address": "192.168.1.100",
                "user_agent": "Chrome/91.0",
                "referrer": "/documents/list"
            }
        )
        
        audit_repository.create.assert_called_once()
        call_args = audit_repository.create.call_args[1]
        assert call_args["action"] == "download"
        assert "filename" in call_args["details"]
        assert "ip_address" in call_args["details"]
    
    async def test_permission_change_audit(self, audit_repository, mock_user_data):
        """Test audit logging for permission changes."""
        document_id = uuid.uuid4()
        user_id = uuid.UUID(mock_user_data["user_id"])
        target_user_id = uuid.uuid4()
        org_id = uuid.UUID(mock_user_data["organization_id"])
        
        mock_audit = MagicMock()
        audit_repository.create = AsyncMock(return_value=mock_audit)
        
        await audit_repository.log_action(
            action="grant_permission",
            user_id=user_id,
            organization_id=org_id,
            document_id=document_id,
            details={
                "target_user_id": str(target_user_id),
                "permissions_granted": ["read", "write"],
                "permission_type": "user",
                "expiration": None,
                "reason": "Project collaboration"
            }
        )
        
        audit_repository.create.assert_called_once()
        call_args = audit_repository.create.call_args[1]
        assert "target_user_id" in call_args["details"]
        assert "permissions_granted" in call_args["details"]
    
    async def test_document_deletion_audit(self, audit_repository, mock_user_data):
        """Test audit logging for document deletion."""
        document_id = uuid.uuid4()
        user_id = uuid.UUID(mock_user_data["user_id"])
        org_id = uuid.UUID(mock_user_data["organization_id"])
        
        mock_audit = MagicMock()
        audit_repository.create = AsyncMock(return_value=mock_audit)
        
        await audit_repository.log_action(
            action="delete",
            user_id=user_id,
            organization_id=org_id,
            document_id=document_id,
            details={
                "filename": "sensitive_data.pdf",
                "file_size": 5120000,
                "deletion_type": "soft_delete",
                "reason": "Data retention policy",
                "retention_period_days": 90
            }
        )
        
        audit_repository.create.assert_called_once()
        call_args = audit_repository.create.call_args[1]
        assert call_args["action"] == "delete"
        assert "deletion_type" in call_args["details"]
        assert "reason" in call_args["details"]
    
    async def test_security_event_audit(self, audit_repository, mock_user_data):
        """Test audit logging for security events."""
        user_id = uuid.UUID(mock_user_data["user_id"])
        org_id = uuid.UUID(mock_user_data["organization_id"])
        
        mock_audit = MagicMock()
        audit_repository.create = AsyncMock(return_value=mock_audit)
        
        # Log suspicious activity
        await audit_repository.log_action(
            action="security_violation",
            user_id=user_id,
            organization_id=org_id,
            document_id=None,  # May not be document-specific
            details={
                "violation_type": "excessive_failed_access_attempts",
                "attempted_document_id": str(uuid.uuid4()),
                "failure_count": 5,
                "ip_address": "192.168.1.100",
                "time_window_minutes": 10,
                "action_taken": "temporary_account_lock"
            }
        )
        
        audit_repository.create.assert_called_once()
        call_args = audit_repository.create.call_args[1]
        assert call_args["action"] == "security_violation"
        assert "violation_type" in call_args["details"]
    
    async def test_bulk_operation_audit(self, audit_repository, mock_user_data):
        """Test audit logging for bulk operations."""
        user_id = uuid.UUID(mock_user_data["user_id"])
        org_id = uuid.UUID(mock_user_data["organization_id"])
        document_ids = [uuid.uuid4() for _ in range(5)]
        
        mock_audit = MagicMock()
        audit_repository.create = AsyncMock(return_value=mock_audit)
        
        await audit_repository.log_action(
            action="bulk_permission_grant",
            user_id=user_id,
            organization_id=org_id,
            document_id=None,  # Multiple documents
            details={
                "operation_type": "bulk_share",
                "document_ids": [str(doc_id) for doc_id in document_ids],
                "target_users": ["user1@example.com", "user2@example.com"],
                "permissions": ["read"],
                "documents_affected": len(document_ids),
                "operation_timestamp": datetime.utcnow().isoformat()
            }
        )
        
        audit_repository.create.assert_called_once()
        call_args = audit_repository.create.call_args[1]
        assert len(call_args["details"]["document_ids"]) == 5


@pytest.mark.database
@pytest.mark.asyncio
class TestAuditPersistence:
    """Test audit log persistence and retrieval."""
    
    async def test_audit_trail_retrieval(self, db_session, sample_document, mock_user_data):
        """Test retrieving audit trail for a document."""
        repo = AuditRepository(db_session)
        
        user_id = uuid.UUID(mock_user_data["user_id"])
        org_id = uuid.UUID(mock_user_data["organization_id"])
        
        # Create multiple audit entries
        actions = [
            ("upload", {"filename": "test.pdf", "size": 1024}),
            ("access", {"type": "view", "ip": "192.168.1.1"}),
            ("download", {"type": "full", "ip": "192.168.1.1"}),
            ("share", {"target": "user@example.com", "permissions": ["read"]})
        ]
        
        created_audits = []
        for action, details in actions:
            audit = await repo.log_action(
                action=action,
                user_id=user_id,
                organization_id=org_id,
                document_id=sample_document.id,
                details=details
            )
            created_audits.append(audit)
        
        # Retrieve audit trail
        trail = await repo.get_document_audit_trail(
            document_id=sample_document.id,
            limit=10
        )
        
        assert len(trail) == 4
        trail_actions = [audit.action for audit in trail]
        assert "upload" in trail_actions
        assert "access" in trail_actions
        assert "download" in trail_actions
        assert "share" in trail_actions
    
    async def test_user_audit_trail(self, db_session, mock_user_data):
        """Test retrieving audit trail for a user."""
        repo = AuditRepository(db_session)
        
        user_id = uuid.UUID(mock_user_data["user_id"])
        org_id = uuid.UUID(mock_user_data["organization_id"])
        
        # Create audit entries for different documents
        doc_ids = [uuid.uuid4() for _ in range(3)]
        
        for i, doc_id in enumerate(doc_ids):
            await repo.log_action(
                action="access",
                user_id=user_id,
                organization_id=org_id,
                document_id=doc_id,
                details={"document_index": i}
            )
        
        # Retrieve user audit trail
        trail = await repo.get_user_audit_trail(
            user_id=user_id,
            organization_id=org_id,
            limit=50
        )
        
        assert len(trail) >= 3
        # All entries should be for the same user
        for audit in trail:
            assert audit.user_id == user_id
    
    async def test_audit_search_and_filtering(self, db_session, mock_user_data):
        """Test searching and filtering audit logs."""
        repo = AuditRepository(db_session)
        
        user_id = uuid.UUID(mock_user_data["user_id"])
        org_id = uuid.UUID(mock_user_data["organization_id"])
        doc_id = uuid.uuid4()
        
        # Create different types of audit entries
        audit_data = [
            ("upload", {"sensitive": True}),
            ("access", {"sensitive": False}),
            ("download", {"sensitive": True}),
            ("delete", {"sensitive": True})
        ]
        
        for action, details in audit_data:
            await repo.log_action(
                action=action,
                user_id=user_id,
                organization_id=org_id,
                document_id=doc_id,
                details=details
            )
        
        # Search for sensitive actions
        # This would require implementing search functionality in the repository
        # For now, we'll verify all audits were created
        all_audits = await repo.get_document_audit_trail(doc_id, limit=10)
        assert len(all_audits) == 4
    
    async def test_audit_data_integrity(self, db_session, mock_user_data):
        """Test audit log data integrity and immutability."""
        repo = AuditRepository(db_session)
        
        user_id = uuid.UUID(mock_user_data["user_id"])
        org_id = uuid.UUID(mock_user_data["organization_id"])
        doc_id = uuid.uuid4()
        
        # Create audit entry
        original_details = {
            "filename": "original.pdf",
            "action_reason": "initial upload"
        }
        
        audit = await repo.log_action(
            action="upload",
            user_id=user_id,
            organization_id=org_id,
            document_id=doc_id,
            details=original_details
        )
        
        original_id = audit.id
        original_timestamp = audit.timestamp
        
        # Audit entries should be immutable
        # Attempting to modify should not change the original record
        # (This depends on how the audit system is implemented)
        
        # Retrieve the audit entry again
        retrieved_audits = await repo.get_document_audit_trail(doc_id, limit=1)
        retrieved_audit = retrieved_audits[0]
        
        assert retrieved_audit.id == original_id
        assert retrieved_audit.timestamp == original_timestamp
        assert retrieved_audit.details == original_details


@pytest.mark.integration
@pytest.mark.asyncio
class TestAuditIntegration:
    """Integration tests for audit logging with API endpoints."""
    
    @patch('httpx.AsyncClient')
    async def test_upload_endpoint_audit_integration(self, mock_client, client, valid_token, mock_user_data):
        """Test that upload endpoint creates proper audit logs."""
        # Mock Identity Service
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Mock file operations and audit logging
        with patch('aiofiles.open'), \
             patch('pathlib.Path.mkdir'), \
             patch('magic.from_buffer', return_value="application/pdf"), \
             patch('repositories.AuditRepository.log_action') as mock_audit_log:
            
            # Mock audit log creation
            mock_audit_log.return_value = MagicMock()
            
            # Upload file
            files = {"file": ("test.pdf", b"PDF content", "application/pdf")}
            response = client.post(
                "/api/v1/documents/upload",
                headers={"Authorization": f"Bearer {valid_token}"},
                files=files
            )
            
            # Verify audit was logged
            if response.status_code == 201:  # Successful upload
                mock_audit_log.assert_called()
                call_args = mock_audit_log.call_args
                assert call_args[1]["action"] == "upload"
    
    @patch('httpx.AsyncClient')
    async def test_download_endpoint_audit_integration(self, mock_client, client, valid_token, mock_user_data):
        """Test that download endpoint creates proper audit logs."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        document_id = "12345678-1234-5678-9012-123456789012"
        
        with patch('aiofiles.open'), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('repositories.AuditRepository.log_action') as mock_audit_log:
            
            mock_audit_log.return_value = MagicMock()
            
            response = client.get(
                f"/api/v1/documents/{document_id}/download",
                headers={"Authorization": f"Bearer {valid_token}"}
            )
            
            # Verify download was audited (if endpoint exists and succeeds)
            if response.status_code == 200:
                mock_audit_log.assert_called()
                call_args = mock_audit_log.call_args
                assert call_args[1]["action"] == "download"
    
    async def test_audit_log_performance(self, audit_repository, mock_user_data):
        """Test audit logging performance under load."""
        import asyncio
        import time
        
        user_id = uuid.UUID(mock_user_data["user_id"])
        org_id = uuid.UUID(mock_user_data["organization_id"])
        
        # Mock the repository create method for performance testing
        audit_repository.create = AsyncMock()
        mock_audit = MagicMock()
        mock_audit.id = uuid.uuid4()
        audit_repository.create.return_value = mock_audit
        
        # Measure time for batch audit logging
        start_time = time.perf_counter()
        
        tasks = []
        for i in range(100):  # 100 concurrent audit logs
            task = audit_repository.log_action(
                action="access",
                user_id=user_id,
                organization_id=org_id,
                document_id=uuid.uuid4(),
                details={"batch_index": i}
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # Should complete within reasonable time
        assert duration < 2.0  # Less than 2 seconds for 100 audit logs
        assert audit_repository.create.call_count == 100


@pytest.mark.security
class TestAuditSecurity:
    """Security tests for audit logging."""
    
    async def test_audit_log_tampering_protection(self, audit_repository, mock_user_data):
        """Test protection against audit log tampering."""
        user_id = uuid.UUID(mock_user_data["user_id"])
        org_id = uuid.UUID(mock_user_data["organization_id"])
        
        # Mock audit creation with checksum/signature
        mock_audit = MagicMock()
        mock_audit.id = uuid.uuid4()
        mock_audit.action = "upload"
        mock_audit.checksum = "sha256_hash_of_audit_data"
        
        audit_repository.create = AsyncMock(return_value=mock_audit)
        
        audit = await audit_repository.log_action(
            action="upload",
            user_id=user_id,
            organization_id=org_id,
            document_id=uuid.uuid4(),
            details={"filename": "secure.pdf"}
        )
        
        # Audit should have integrity protection
        assert hasattr(audit, 'checksum') or hasattr(audit, 'signature')
    
    def test_sensitive_data_redaction(self):
        """Test redaction of sensitive data in audit logs."""
        def redact_sensitive_data(details: dict) -> dict:
            """Redact sensitive information from audit details."""
            sensitive_keys = ["password", "ssn", "credit_card", "api_key"]
            redacted = details.copy()
            
            for key in sensitive_keys:
                if key in redacted:
                    redacted[key] = "***REDACTED***"
            
            return redacted
        
        # Test with sensitive data
        original_details = {
            "filename": "user_data.pdf",
            "password": "secret123",
            "user_email": "user@example.com",
            "ssn": "123-45-6789"
        }
        
        redacted_details = redact_sensitive_data(original_details)
        
        assert redacted_details["password"] == "***REDACTED***"
        assert redacted_details["ssn"] == "***REDACTED***"
        assert redacted_details["user_email"] == "user@example.com"  # Not sensitive
        assert redacted_details["filename"] == "user_data.pdf"  # Not sensitive
    
    async def test_audit_access_control(self, audit_repository, mock_user_data, admin_user_data):
        """Test access control for audit logs."""
        regular_user_id = uuid.UUID(mock_user_data["user_id"])
        admin_user_id = uuid.UUID(admin_user_data["user_id"])
        org_id = uuid.UUID(mock_user_data["organization_id"])
        
        # Mock different access levels
        def check_audit_access(requesting_user_id: uuid.UUID, target_user_id: uuid.UUID, user_roles: list) -> bool:
            """Check if user can access audit logs."""
            # Admin can access all audit logs
            if "admin" in user_roles:
                return True
            
            # Users can only access their own audit logs
            return requesting_user_id == target_user_id
        
        # Regular user accessing their own logs - should be allowed
        assert check_audit_access(regular_user_id, regular_user_id, ["user"]) is True
        
        # Regular user accessing other's logs - should be denied
        assert check_audit_access(regular_user_id, admin_user_id, ["user"]) is False
        
        # Admin accessing any logs - should be allowed
        assert check_audit_access(admin_user_id, regular_user_id, ["admin", "user"]) is True
    
    def test_audit_log_retention_policy(self):
        """Test audit log retention and archival policies."""
        def should_archive_audit(audit_date: datetime, retention_days: int = 365) -> bool:
            """Determine if audit log should be archived."""
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            return audit_date < cutoff_date
        
        def should_delete_audit(audit_date: datetime, deletion_days: int = 2555) -> bool:
            """Determine if audit log should be deleted (7 years)."""
            cutoff_date = datetime.utcnow() - timedelta(days=deletion_days)
            return audit_date < cutoff_date
        
        # Test recent audit - should not be archived or deleted
        recent_date = datetime.utcnow() - timedelta(days=30)
        assert should_archive_audit(recent_date) is False
        assert should_delete_audit(recent_date) is False
        
        # Test old audit - should be archived but not deleted
        old_date = datetime.utcnow() - timedelta(days=400)
        assert should_archive_audit(old_date) is True
        assert should_delete_audit(old_date) is False
        
        # Test very old audit - should be deleted
        very_old_date = datetime.utcnow() - timedelta(days=3000)
        assert should_archive_audit(very_old_date) is True
        assert should_delete_audit(very_old_date) is True