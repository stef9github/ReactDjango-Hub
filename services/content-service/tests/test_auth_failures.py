"""
Authentication Error Handling Tests for Content Service
Tests various authentication failure scenarios and error handling
"""

import pytest
from unittest.mock import patch, AsyncMock
import httpx
from fastapi.testclient import TestClient
from main import app


class TestAuthenticationErrorHandling:
    """Test various authentication error scenarios"""

    @patch('httpx.AsyncClient')
    def test_malformed_token_handling(self, mock_client, client):
        """Test handling of malformed Bearer token"""
        # Mock Identity Service to simulate malformed token processing
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Malformed token"}
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": "Bearer malformed.token.here"},
        )
        
        # Should handle gracefully and return 401
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    def test_identity_service_500_error(self, mock_client, client, valid_token):
        """Test handling when Identity Service returns 500"""
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal server error"}
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 401  # Should treat as auth failure
        assert "Token validation failed" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    def test_identity_service_404_error(self, mock_client, client, valid_token):
        """Test handling when Identity Service returns 404"""
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Endpoint not found"}
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 401  # Should treat as auth failure
        assert "Token validation failed" in response.json()["detail"]

    def test_authorization_header_variations(self, client):
        """Test various Authorization header formats"""
        test_cases = [
            ("bearer token123", 401),  # lowercase (should be rejected by HTTPBearer)
            ("Bearer", 422),  # missing token (HTTPBearer validation)
            ("Basic token123", 401),   # wrong auth type
            ("", 401),  # empty
            ("Bearer  ", 422),  # empty token with spaces
        ]
        
        for auth_header, expected_status in test_cases:
            response = client.get(
                "/api/v1/documents",
                headers={"Authorization": auth_header} if auth_header else {}
            )
            assert response.status_code in [expected_status, 401, 422], f"Unexpected status for header: '{auth_header}'"

    @patch('httpx.AsyncClient')
    def test_identity_service_connection_refused(self, mock_client, client, valid_token):
        """Test handling when Identity Service connection is refused"""
        # Mock connection refused
        mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.ConnectError("Connection refused")
        
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    def test_identity_service_read_timeout(self, mock_client, client, valid_token):
        """Test handling of Identity Service read timeout"""
        # Mock read timeout
        mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.ReadTimeout("Read timeout")
        
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 503
        assert "temporarily unavailable" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    def test_identity_service_connection_timeout(self, mock_client, client, valid_token):
        """Test handling of Identity Service connection timeout"""
        # Mock connection timeout
        mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.ConnectTimeout("Connection timeout")
        
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 503
        assert "temporarily unavailable" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    def test_user_context_availability(self, mock_client, client, valid_token, mock_user_data):
        """Test that user context is properly passed to endpoints"""
        # Mock successful auth
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Test endpoint that uses user context
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        # Verify user context was used (no auth error)
        assert response.status_code != 401
        # The response should be filtered by organization_id from user context

    @patch('httpx.AsyncClient')
    def test_invalid_json_from_identity_service(self, mock_client, client, valid_token):
        """Test handling of invalid JSON response from Identity Service"""
        # Mock response with invalid JSON
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        assert response.status_code == 401
        assert "Token validation failed" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    def test_empty_response_from_identity_service(self, mock_client, client, valid_token):
        """Test handling of empty response from Identity Service"""
        # Mock empty successful response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        # Should handle missing user_id gracefully
        # This depends on how your get_current_user handles missing fields
        assert response.status_code in [401, 500]

    def test_missing_authorization_header(self, client):
        """Test behavior when Authorization header is completely missing"""
        response = client.get("/api/v1/documents")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    def test_multiple_bearer_tokens(self, mock_client, client):
        """Test handling of multiple Bearer tokens in header"""
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": "Bearer token1 token2 token3"}
        )
        
        # HTTPBearer should handle this by taking the first token
        # But it might be rejected as malformed
        assert response.status_code in [401, 422]

    @patch('httpx.AsyncClient')
    def test_very_long_token(self, mock_client, client):
        """Test handling of extremely long tokens"""
        # Create a very long token (>8KB)
        very_long_token = "x" * 10000
        
        # Mock Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid token"}
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {very_long_token}"}
        )
        
        # Should handle gracefully
        assert response.status_code == 401

    @patch('httpx.AsyncClient')
    def test_special_characters_in_token(self, mock_client, client):
        """Test handling of tokens with special characters"""
        special_token = "token.with-special_characters=123+456/789"
        
        # Mock Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid token"}
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {special_token}"}
        )
        
        assert response.status_code == 401


class TestAuthenticationPerformance:
    """Test authentication performance characteristics"""

    @patch('httpx.AsyncClient')
    def test_auth_response_time(self, mock_client, client, valid_token, mock_user_data):
        """Test that authentication doesn't add excessive latency"""
        import time
        
        # Mock fast Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        start_time = time.time()
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        end_time = time.time()
        
        # Authentication should add minimal overhead
        # In test environment, should be very fast
        assert (end_time - start_time) < 1.0  # Less than 1 second
        assert response.status_code != 401

    @patch('httpx.AsyncClient')
    def test_concurrent_auth_requests(self, mock_client, client, valid_token, mock_user_data):
        """Test handling of concurrent authentication requests"""
        # Mock successful auth
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Make multiple concurrent requests (simulated)
        responses = []
        for _ in range(5):
            response = client.get(
                "/api/v1/documents",
                headers={"Authorization": f"Bearer {valid_token}"}
            )
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code != 401


class TestEdgeCases:
    """Test edge cases and unusual scenarios"""

    def test_case_sensitive_bearer(self, client):
        """Test case sensitivity of Bearer keyword"""
        test_cases = [
            "bearer token123",  # lowercase
            "BEARER token123",  # uppercase
            "Bearer token123",  # proper case
        ]
        
        for auth_header in test_cases:
            response = client.get(
                "/api/v1/documents",
                headers={"Authorization": auth_header}
            )
            # HTTPBearer is case-sensitive and expects "Bearer"
            if auth_header.startswith("Bearer "):
                assert response.status_code == 401  # Invalid token, but format accepted
            else:
                assert response.status_code in [401, 422]  # Format rejected

    @patch('httpx.AsyncClient')
    def test_user_id_uuid_conversion(self, mock_client, client, valid_token):
        """Test UUID conversion in get_current_user"""
        # Mock user data with string UUIDs
        mock_user_data = {
            "user_id": "12345678-1234-5678-9012-123456789012",
            "organization_id": "87654321-4321-8765-2109-876543210987",
            "email": "test@example.com",
            "roles": ["user"]
        }
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        # Should handle UUID conversion properly
        assert response.status_code != 401
        # If UUID conversion fails, it would cause a 500 error

    @patch('httpx.AsyncClient')
    def test_invalid_uuid_in_user_data(self, mock_client, client, valid_token):
        """Test handling of invalid UUIDs in user data from Identity Service"""
        # Mock user data with invalid UUIDs
        mock_user_data = {
            "user_id": "not-a-valid-uuid",
            "organization_id": "also-not-a-uuid",
            "email": "test@example.com",
            "roles": ["user"]
        }
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        response = client.get(
            "/api/v1/documents",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        # Should handle UUID conversion error gracefully
        assert response.status_code in [401, 500]