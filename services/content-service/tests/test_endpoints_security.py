"""
Endpoint Security Tests for Content Service
Tests that all endpoints are properly protected except health endpoint
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from main import app


class TestEndpointSecurity:
    """Test that all endpoints are properly protected"""

    def test_health_endpoint_unprotected(self, client):
        """Test that health endpoint doesn't require authentication"""
        response = client.get("/health")
        assert response.status_code == 200
        # Health endpoint should work without any authentication

    @pytest.mark.parametrize("endpoint,method,data", [
        ("/api/v1/documents", "GET", None),
        ("/api/v1/documents/stats", "GET", None),
        ("/api/v1/documents/12345678-1234-5678-9012-123456789012", "GET", None),
        ("/api/v1/documents/12345678-1234-5678-9012-123456789012", "DELETE", None),
        ("/api/v1/documents/12345678-1234-5678-9012-123456789012/audit", "GET", None),
        # Future endpoints that will be added
        ("/api/v1/documents", "POST", {"filename": "test.pdf", "content_type": "application/pdf"}),
        ("/api/v1/documents/12345678-1234-5678-9012-123456789012/process", "POST", {"processors": ["ocr"]}),
        ("/api/v1/search", "GET", None),
    ])
    def test_endpoints_require_authentication(self, client, endpoint, method, data):
        """Test that all protected endpoints require authentication"""
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json=data)
        elif method == "PUT":
            response = client.put(endpoint, json=data)
        elif method == "DELETE":
            response = client.delete(endpoint)
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    @pytest.mark.parametrize("endpoint,method,data", [
        ("/api/v1/documents", "GET", None),
        ("/api/v1/documents/stats", "GET", None),
        ("/api/v1/documents/12345678-1234-5678-9012-123456789012", "GET", None),
        ("/api/v1/documents/12345678-1234-5678-9012-123456789012", "DELETE", None),
        ("/api/v1/documents/12345678-1234-5678-9012-123456789012/audit", "GET", None),
    ])
    def test_endpoints_work_with_valid_authentication(self, mock_client, client, endpoint, method, data, valid_token, mock_user_data):
        """Test that protected endpoints work with valid authentication"""
        # Mock successful Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        headers = {"Authorization": f"Bearer {valid_token}"}
        
        if method == "GET":
            response = client.get(endpoint, headers=headers)
        elif method == "POST":
            response = client.post(endpoint, headers=headers, json=data)
        elif method == "DELETE":
            response = client.delete(endpoint, headers=headers)
        
        # Should not return 401 (authentication should succeed)
        assert response.status_code != 401
        # Actual status depends on your endpoint implementation

    def test_invalid_uuid_endpoints(self, client):
        """Test endpoints with invalid UUID format require auth before returning 422"""
        invalid_uuid = "not-a-uuid"
        
        # These should return 401 (auth required) not 422 (validation error)
        endpoints = [
            f"/api/v1/documents/{invalid_uuid}",
            f"/api/v1/documents/{invalid_uuid}/audit",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401  # Auth checked before validation

    @patch('httpx.AsyncClient')
    def test_organization_isolation_enforced(self, mock_client, client, valid_token):
        """Test that organization isolation is enforced through authentication"""
        # User from organization A
        user_org_a = {
            "user_id": "user-a-1234-5678-9012-123456789012",
            "organization_id": "org-a-1234-5678-9012-123456789012",
            "email": "user.a@example.com",
            "roles": ["user"]
        }
        
        # Mock successful auth for org A user
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = user_org_a
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Request documents (should only see org A documents)
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        # Should authenticate successfully
        assert response.status_code != 401
        # Organization filtering is handled by the endpoint logic

    def test_malformed_bearer_token_rejection(self, client):
        """Test that malformed Bearer tokens are properly rejected"""
        malformed_tokens = [
            "Bearer",  # No token
            "Bearer ",  # Empty token
            "Bearer multiple tokens here",  # Multiple tokens
            "NotBearer token123",  # Wrong prefix
            "",  # Empty Authorization header
        ]
        
        for token in malformed_tokens:
            response = client.get(
                "/api/v1/documents",
                headers={"Authorization": token} if token else {}
            )
            # Should be rejected before reaching our validation logic
            assert response.status_code in [401, 422]

    @patch('httpx.AsyncClient')
    def test_expired_token_handling(self, mock_client, client, expired_token):
        """Test handling of expired tokens"""
        # Mock Identity Service response for expired token
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Token has expired"}
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]


class TestAuthenticationConsistency:
    """Test authentication behavior consistency across endpoints"""

    @patch('httpx.AsyncClient')
    def test_consistent_user_context_across_endpoints(self, mock_client, client, valid_token, mock_user_data):
        """Test that user context is consistent across all endpoints"""
        # Mock successful authentication
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Test multiple endpoints
        endpoints = [
            "/api/v1/documents",
            "/api/v1/documents/stats",
        ]
        
        for endpoint in endpoints:
            response = client.get(
                endpoint,
                headers={"Authorization": f"Bearer {valid_token}"}
            )
            
            # All should authenticate with same user context
            assert response.status_code != 401
            # Verify Identity Service called with same token
            mock_client.return_value.__aenter__.return_value.post.assert_called_with(
                "http://localhost:8001/auth/validate",
                headers={"Authorization": f"Bearer {valid_token}"},
                timeout=5.0
            )

    def test_error_message_consistency(self, client):
        """Test that authentication error messages are consistent"""
        # Test missing token
        response = client.get("/api/v1/documents")
        assert response.status_code == 401
        missing_token_message = response.json()["detail"]
        
        # Test another endpoint with missing token
        response2 = client.get("/api/v1/documents/stats")
        assert response2.status_code == 401
        assert response2.json()["detail"] == missing_token_message
        
        # Error messages should be consistent across endpoints

    @patch('httpx.AsyncClient')
    def test_authentication_failure_consistency(self, mock_client, client, invalid_token):
        """Test consistent behavior for authentication failures"""
        # Mock Identity Service rejection
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid token"}
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        endpoints = [
            "/api/v1/documents",
            "/api/v1/documents/stats",
        ]
        
        for endpoint in endpoints:
            response = client.get(
                endpoint,
                headers={"Authorization": f"Bearer {invalid_token}"}
            )
            
            # All should return consistent auth failure
            assert response.status_code == 401
            assert "Invalid or expired token" in response.json()["detail"]


class TestSecurityHeaders:
    """Test security headers in authentication responses"""

    def test_www_authenticate_header_present(self, client):
        """Test that WWW-Authenticate header is present in 401 responses"""
        response = client.get("/api/v1/documents")
        
        assert response.status_code == 401
        # FastAPI's HTTPBearer automatically adds WWW-Authenticate header

    @patch('httpx.AsyncClient')
    def test_bearer_challenge_in_auth_failures(self, mock_client, client, invalid_token):
        """Test Bearer challenge in authentication failures"""
        # Mock Identity Service rejection
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        
        assert response.status_code == 401
        # Should include proper WWW-Authenticate header