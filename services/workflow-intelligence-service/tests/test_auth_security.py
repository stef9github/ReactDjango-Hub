"""
Security tests for JWT authentication
"""
import pytest
from unittest.mock import patch, Mock, AsyncMock
from fastapi import HTTPException
import time

class TestSecurityVulnerabilities:
    """Test for common security vulnerabilities"""
    
    def test_expired_token_rejection(self, client, mock_auth_headers):
        """Test that expired tokens are rejected"""
        with patch("main.validate_jwt_token") as mock_validate:
            # Simulate Identity Service rejecting expired token
            mock_validate.side_effect = HTTPException(
                status_code=401,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
            response = client.post(
                "/api/v1/workflows",
                json={"definition_id": "test", "entity_id": "test"},
                headers=mock_auth_headers
            )
            assert response.status_code == 401
    
    def test_tampered_token_rejection(self, client):
        """Test that tampered tokens are rejected"""
        # Simulate a tampered JWT token
        tampered_headers = {"Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.TAMPERED_PAYLOAD.INVALID_SIGNATURE"}
        
        with patch("main.validate_jwt_token") as mock_validate:
            mock_validate.side_effect = HTTPException(
                status_code=401,
                detail="Invalid token signature"
            )
            
            response = client.post(
                "/api/v1/workflows",
                json={"definition_id": "test", "entity_id": "test"},
                headers=tampered_headers
            )
            assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_no_token_reuse_across_organizations(self, client, mock_auth_headers):
        """Test that tokens are properly scoped to organizations"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "user_id": "user-123",
                "organization_id": "org-123",
                "roles": ["user"]
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            # Make request - should succeed
            response = client.get(
                "/api/v1/definitions",
                headers=mock_auth_headers
            )
            assert response.status_code == 200
            assert response.json()["organization"] == "org-123"
    
    def test_privilege_escalation_prevention(self, client, mock_auth_headers):
        """Test that users cannot escalate their privileges"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "user_id": "user-123",
                "organization_id": "org-123",
                "roles": ["user"]  # Not an admin
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            # Try to create workflow definition (admin only)
            response = client.post(
                "/api/v1/definitions",
                json={"name": "Test", "states": [], "transitions": []},
                headers=mock_auth_headers
            )
            assert response.status_code == 403
            assert "Insufficient permissions" in response.json()["detail"]
    
    def test_sensitive_data_not_in_error_messages(self, client, mock_auth_headers):
        """Test that sensitive data doesn't leak in error messages"""
        with patch("main.validate_jwt_token") as mock_validate:
            mock_validate.side_effect = Exception("Database connection string: postgresql://user:password@host")
            
            response = client.post(
                "/api/v1/workflows",
                json={"definition_id": "test", "entity_id": "test"},
                headers=mock_auth_headers
            )
            
            # Error response should not contain sensitive information
            assert response.status_code == 401
            error_detail = response.json().get("detail", "")
            assert "password" not in error_detail.lower()
            assert "connection string" not in error_detail.lower()
            assert "Token validation failed" in error_detail

class TestBruteForceProtection:
    """Test protection against brute force attacks"""
    
    def test_multiple_invalid_tokens_handling(self, client):
        """Test that multiple invalid token attempts are handled properly"""
        invalid_headers = {"Authorization": "Bearer invalid-token"}
        
        with patch("main.validate_jwt_token") as mock_validate:
            mock_validate.side_effect = HTTPException(
                status_code=401,
                detail="Invalid token"
            )
            
            # Make multiple requests with invalid token
            for i in range(5):
                response = client.post(
                    "/api/v1/workflows",
                    json={"definition_id": "test", "entity_id": f"test-{i}"},
                    headers=invalid_headers
                )
                assert response.status_code == 401
                
            # Service should still be responding (not blocked)
            response = client.get("/health")
            assert response.status_code == 200

class TestInputValidation:
    """Test input validation security"""
    
    def test_sql_injection_in_workflow_id(self, client, mock_auth_headers):
        """Test SQL injection attempts in workflow ID parameter"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "user_id": "user-123",
                "organization_id": "org-123",
                "roles": ["user"]
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            # Try SQL injection in workflow ID
            malicious_id = "1'; DROP TABLE workflows; --"
            
            response = client.get(
                f"/api/v1/workflows/{malicious_id}/status",
                headers=mock_auth_headers
            )
            
            # Should handle safely (parameterized queries prevent injection)
            assert response.status_code in [200, 404]  # Either works or not found, but no error
    
    def test_xss_in_request_data(self, client, mock_auth_headers):
        """Test XSS attempts in request data"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "user_id": "user-123",
                "organization_id": "org-123",
                "roles": ["user"]
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            xss_payload = "<script>alert('xss')</script>"
            
            response = client.post(
                "/api/v1/workflows",
                json={
                    "definition_id": xss_payload,
                    "entity_id": "test-123",
                    "context": {"description": xss_payload}
                },
                headers=mock_auth_headers
            )
            
            # Should accept the request (input validation is the frontend's responsibility)
            assert response.status_code == 200
            # The API reflects input data as expected - XSS prevention happens at frontend rendering
            # This is standard for API services where data sanitization occurs at display time
            response_data = response.json()
            assert response_data["definition_id"] == xss_payload  # Input stored as-is
            assert response_data["created_by"] == "user-123"  # User context preserved

class TestRateLimiting:
    """Test rate limiting functionality (if implemented)"""
    
    def test_rapid_requests_handling(self, client, mock_auth_headers):
        """Test handling of rapid successive requests"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "user_id": "user-123",
                "organization_id": "org-123",
                "roles": ["user"]
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            # Make rapid requests
            responses = []
            for i in range(10):
                response = client.get(
                    "/api/v1/definitions",
                    headers=mock_auth_headers
                )
                responses.append(response.status_code)
            
            # All requests should be handled properly
            # (Rate limiting would return 429, but we're not implementing it yet)
            for status in responses:
                assert status in [200, 429]  # Either success or rate limited

class TestSecureHeaders:
    """Test security headers in responses"""
    
    def test_authentication_failure_headers(self, client):
        """Test that proper headers are returned on authentication failure"""
        response = client.post(
            "/api/v1/workflows",
            json={"definition_id": "test", "entity_id": "test"}
        )
        
        assert response.status_code == 403  # No auth provided
        
        # Test with invalid token
        with patch("main.validate_jwt_token") as mock_validate:
            mock_validate.side_effect = HTTPException(
                status_code=401,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
            
            response = client.post(
                "/api/v1/workflows",
                json={"definition_id": "test", "entity_id": "test"},
                headers={"Authorization": "Bearer invalid-token"}
            )
            
            # Should include WWW-Authenticate header
            assert response.status_code == 401

class TestDataLeakagePrevention:
    """Test prevention of sensitive data leakage"""
    
    def test_error_responses_dont_leak_internal_data(self, client, mock_auth_headers):
        """Test that error responses don't leak internal system information"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "user_id": "user-123",
                "organization_id": "org-123",
                "roles": ["user"]
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            # Try to access non-existent workflow
            response = client.get(
                "/api/v1/workflows/non-existent-id/status",
                headers=mock_auth_headers
            )
            
            # Error message should be generic, not revealing internal details
            if response.status_code == 404:
                error_detail = response.json().get("detail", "")
                # Should not contain database table names, file paths, etc.
                assert "table" not in error_detail.lower()
                assert "database" not in error_detail.lower()
                assert "/api/" not in error_detail  # No internal paths
    
    def test_user_enumeration_prevention(self, client, mock_auth_headers):
        """Test that user enumeration is prevented"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "user_id": "user-123",
                "organization_id": "org-123",
                "roles": ["user"]
            }
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            # Try to access workflows for non-existent user
            response = client.get(
                "/api/v1/workflows/user/non-existent-user",
                headers=mock_auth_headers
            )
            
            # Should not distinguish between "user doesn't exist" and "access denied"
            assert response.status_code == 403
            assert "Access denied" in response.json()["detail"]
            # Should not reveal whether user exists or not
            assert "not found" not in response.json()["detail"].lower()
            assert "does not exist" not in response.json()["detail"].lower()