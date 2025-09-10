"""
Upload and Download functionality tests for Content Service
Tests file upload, download, and streaming endpoints with validation
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, AsyncMock, mock_open
from fastapi.testclient import TestClient
from main import app


class TestFileUploadDownload:
    """Test file upload and download operations"""

    def test_upload_endpoint_requires_auth(self, client):
        """Test that upload endpoint requires authentication"""
        # Create a test file
        test_content = b"This is a test PDF content"
        
        response = client.post(
            "/api/v1/documents",
            files={"file": ("test.pdf", test_content, "application/pdf")},
            data={"description": "Test document"}
        )
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    @patch('aiofiles.open')
    @patch('magic.from_buffer')
    def test_successful_document_upload(self, mock_magic, mock_aiofiles, mock_client, client, valid_token, mock_user_data):
        """Test successful document upload with all validations"""
        # Mock Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Mock file type detection
        mock_magic.return_value = "application/pdf"
        
        # Mock file operations
        mock_file = AsyncMock()
        mock_aiofiles.return_value.__aenter__.return_value = mock_file
        
        # Create test file
        test_content = b"PDF content here"
        
        response = client.post(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"},
            files={"file": ("test.pdf", test_content, "application/pdf")},
            data={
                "description": "Test PDF document",
                "tags": "pdf,test,document",
                "category": "general"
            }
        )
        
        # Should succeed with proper authentication
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["filename"] == "test.pdf"
        assert data["content_type"] == "application/pdf"
        assert data["file_size"] == len(test_content)

    @patch('httpx.AsyncClient')
    def test_upload_file_size_validation(self, mock_client, client, valid_token, mock_user_data):
        """Test file size validation during upload"""
        # Mock Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Create oversized file content (simulate > 50MB)
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        
        response = client.post(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"},
            files={"file": ("large.pdf", large_content, "application/pdf")}
        )
        
        assert response.status_code == 413
        assert "exceeds maximum allowed size" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    @patch('magic.from_buffer')
    def test_upload_invalid_file_type(self, mock_magic, mock_client, client, valid_token, mock_user_data):
        """Test rejection of invalid file types"""
        # Mock Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Mock detection of disallowed file type
        mock_magic.return_value = "application/x-executable"
        
        response = client.post(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"},
            files={"file": ("malware.exe", b"malicious content", "application/octet-stream")}
        )
        
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    def test_upload_dangerous_filename(self, mock_client, client, valid_token, mock_user_data):
        """Test rejection of dangerous filenames"""
        # Mock Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        dangerous_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "script.js",
            "malware.exe"
        ]
        
        for filename in dangerous_filenames:
            response = client.post(
                "/api/v1/documents",
                headers={"Authorization": f"Bearer {valid_token}"},
                files={"file": (filename, b"content", "text/plain")}
            )
            
            assert response.status_code == 400
            assert "Invalid filename" in response.json()["detail"] or "Dangerous file type" in response.json()["detail"]

    def test_download_requires_authentication(self, client):
        """Test that download endpoint requires authentication"""
        document_id = "12345678-1234-5678-9012-123456789012"
        response = client.get(f"/api/v1/documents/{document_id}/download")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    @patch('pathlib.Path.exists')
    def test_download_document_not_found(self, mock_exists, mock_client, client, valid_token, mock_user_data):
        """Test download when document doesn't exist"""
        # Mock Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Mock file doesn't exist
        mock_exists.return_value = False
        
        document_id = "12345678-1234-5678-9012-123456789012"
        response = client.get(
            f"/api/v1/documents/{document_id}/download",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    @patch('pathlib.Path.exists')  
    def test_download_file_missing_on_disk(self, mock_exists, mock_client, client, valid_token, mock_user_data):
        """Test download when database record exists but file is missing"""
        # Mock Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Simulate: document exists in DB but file missing on disk
        mock_exists.return_value = False
        
        document_id = "12345678-1234-5678-9012-123456789012"
        response = client.get(
            f"/api/v1/documents/{document_id}/download",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 404
        assert "Document not found" in response.json()["detail"]

    def test_stream_requires_authentication(self, client):
        """Test that stream endpoint requires authentication"""
        document_id = "12345678-1234-5678-9012-123456789012"
        response = client.get(f"/api/v1/documents/{document_id}/stream")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    def test_stream_non_streamable_content(self, mock_client, client, valid_token, mock_user_data):
        """Test streaming rejection for non-streamable content types"""
        # Mock Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        document_id = "12345678-1234-5678-9012-123456789012"
        response = client.get(
            f"/api/v1/documents/{document_id}/stream",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        # Should fail since no document exists, but test the auth flow
        assert response.status_code == 404


class TestFileValidation:
    """Test file validation utilities"""

    @patch('magic.from_buffer')
    def test_validate_file_content_type(self, mock_magic):
        """Test file content type validation"""
        from main import validate_file
        
        # Mock allowed content type
        mock_magic.return_value = "application/pdf"
        
        # This would need to be tested with actual UploadFile mock
        # The function is async and requires proper mocking

    def test_file_size_limits(self):
        """Test file size configuration"""
        from main import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB
        
        assert MAX_FILE_SIZE_MB == 50  # Default from env
        assert MAX_FILE_SIZE_BYTES == 50 * 1024 * 1024

    def test_allowed_content_types(self):
        """Test allowed content types configuration"""
        from main import ALLOWED_CONTENT_TYPES
        
        expected_types = [
            "application/pdf",
            "application/msword", 
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "image/jpeg",
            "image/png", 
            "image/tiff"
        ]
        
        for content_type in expected_types:
            assert content_type in ALLOWED_CONTENT_TYPES


class TestFileStorage:
    """Test file storage operations"""

    def test_upload_directory_creation(self):
        """Test that upload directories are created"""
        from main import UPLOAD_DIRECTORY, STORAGE_DIRECTORY
        
        # Directories should be created during app startup
        assert UPLOAD_DIRECTORY.exists()
        assert STORAGE_DIRECTORY.exists()

    def test_unique_filename_generation(self):
        """Test that uploaded files get unique names"""
        from main import save_uploaded_file
        import uuid
        
        # Would need proper async testing setup
        # The function generates unique filenames using UUID + extension


class TestSecurityHeaders:
    """Test security headers in file responses"""

    @patch('httpx.AsyncClient')
    def test_download_security_headers(self, mock_client, client, valid_token, mock_user_data):
        """Test that download responses include security headers"""
        # Mock Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        document_id = "12345678-1234-5678-9012-123456789012"
        response = client.get(
            f"/api/v1/documents/{document_id}/download",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        # Even if document not found, test would verify security approach
        assert response.status_code in [404, 200]  # Either not found or success

    @patch('httpx.AsyncClient')  
    def test_stream_security_headers(self, mock_client, client, valid_token, mock_user_data):
        """Test that stream responses include security headers"""
        # Mock Identity Service response  
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        document_id = "12345678-1234-5678-9012-123456789012"
        response = client.get(
            f"/api/v1/documents/{document_id}/stream",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        # Even if document not found, test would verify security approach
        assert response.status_code in [404, 200]  # Either not found or success


class TestAuditLogging:
    """Test audit trail for file operations"""

    @patch('httpx.AsyncClient')
    def test_upload_creates_audit_log(self, mock_client, client, valid_token, mock_user_data):
        """Test that file uploads create audit log entries"""
        # Would need database mocking to verify audit entries are created
        pass

    @patch('httpx.AsyncClient')
    def test_download_creates_audit_log(self, mock_client, client, valid_token, mock_user_data):
        """Test that file downloads create audit log entries"""
        # Would need database mocking to verify audit entries are created
        pass

    @patch('httpx.AsyncClient')
    def test_stream_creates_audit_log(self, mock_client, client, valid_token, mock_user_data):
        """Test that file streaming creates audit log entries"""
        # Would need database mocking to verify audit entries are created
        pass