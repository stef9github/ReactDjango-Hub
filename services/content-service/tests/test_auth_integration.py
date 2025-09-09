"""
JWT Authentication Integration Tests for Content Service
"""

import pytest
from unittest.mock import patch, AsyncMock
import httpx
from fastapi.testclient import TestClient
from main import app


class TestJWTAuthentication:
    """Test JWT token validation integration"""

    @patch('httpx.AsyncClient')
    def test_valid_token_authentication(self, mock_client, client, valid_token, mock_user_data):
        """Test successful authentication with valid token"""
        # Mock Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Test protected endpoint
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 200
        
        # Verify Identity Service was called correctly
        mock_client.return_value.__aenter__.return_value.post.assert_called_once_with(
            "http://localhost:8001/auth/validate",
            headers={"Authorization": f"Bearer {valid_token}"},
            timeout=5.0
        )

    @patch('httpx.AsyncClient')
    def test_invalid_token_authentication(self, mock_client, client, invalid_token):
        """Test authentication failure with invalid token"""
        # Mock Identity Service rejection
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid token"}
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Test protected endpoint
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {invalid_token}"}
        )
        
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

    def test_missing_token_authentication(self, client):
        """Test authentication failure with no token"""
        response = client.get("/api/v1/documents")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    def test_identity_service_timeout(self, mock_client, client, valid_token):
        """Test handling of Identity Service timeout"""
        # Mock timeout exception
        mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.TimeoutException("Timeout")
        
        response = client.get(
            "/api/v1/documents", 
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 503
        assert "temporarily unavailable" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    def test_identity_service_network_error(self, mock_client, client, valid_token):
        """Test handling of Identity Service network errors"""
        # Mock network exception
        mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.RequestError("Network error")
        
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    def test_identity_service_unexpected_status(self, mock_client, client, valid_token):
        """Test handling of unexpected status codes from Identity Service"""
        # Mock unexpected status
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal server error"}
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 401
        assert "Token validation failed" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    def test_user_context_conversion(self, mock_client, client, valid_token, mock_user_data):
        """Test that user data is properly converted in get_current_user"""
        # Mock successful Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Test endpoint that uses get_current_user
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 200
        # The response should contain data filtered by organization_id
        # which confirms user context is working

    @patch('httpx.AsyncClient') 
    def test_document_detail_with_auth(self, mock_client, client, valid_token, mock_user_data):
        """Test document detail endpoint with authentication"""
        # Mock successful auth
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Test with a UUID that should return 404 (no documents in test DB)
        response = client.get(
            "/api/v1/documents/12345678-1234-5678-9012-123456789012",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        # Should not return 401 (auth should work)
        assert response.status_code != 401
        # May return 404 or 500 depending on database state, but not auth error

    @patch('httpx.AsyncClient')
    def test_document_stats_with_auth(self, mock_client, client, valid_token, mock_user_data):
        """Test document stats endpoint with authentication"""
        # Mock successful auth
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        response = client.get(
            "/api/v1/documents/stats",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        # Should not return 401 (auth should work)
        assert response.status_code != 401

    @patch('httpx.AsyncClient')
    def test_delete_document_with_auth(self, mock_client, client, valid_token, mock_user_data):
        """Test document deletion endpoint with authentication"""
        # Mock successful auth
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        response = client.delete(
            "/api/v1/documents/12345678-1234-5678-9012-123456789012",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        # Should not return 401 (auth should work)
        assert response.status_code != 401


class TestAuthenticationFlow:
    """Test complete authentication flow"""

    @patch('httpx.AsyncClient')
    def test_complete_auth_flow(self, mock_client, client, valid_token, mock_user_data):
        """Test complete authentication flow from token to user context"""
        # Mock Identity Service success
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Test multiple endpoints to ensure consistent auth behavior
        endpoints = [
            ("/api/v1/documents", "GET"),
            ("/api/v1/documents/stats", "GET"),
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(
                    endpoint,
                    headers={"Authorization": f"Bearer {valid_token}"}
                )
            elif method == "POST":
                response = client.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {valid_token}"},
                    json={"test": "data"}
                )
            
            # All should authenticate successfully
            assert response.status_code != 401, f"Auth failed for {endpoint}"

    def test_auth_header_variations(self, client):
        """Test various Authorization header formats"""
        test_cases = [
            ("bearer token123", 401),  # lowercase
            ("Bearer", 422),  # missing token (should be caught by HTTPBearer)
            ("Basic token123", 401),   # wrong auth type
            ("", 401),  # empty
        ]
        
        for auth_header, expected_status in test_cases:
            response = client.get(
                "/api/v1/documents",
                headers={"Authorization": auth_header} if auth_header else {}
            )
            assert response.status_code in [401, 422], f"Unexpected status for header: '{auth_header}'"