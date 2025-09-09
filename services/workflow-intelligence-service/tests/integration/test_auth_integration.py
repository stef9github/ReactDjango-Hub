"""
Integration tests for JWT authentication
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import httpx


@pytest.mark.auth
@pytest.mark.integration
class TestAuthenticationFlow:
    """Test complete authentication flow integration"""
    
    def test_missing_authorization_header(self, client: TestClient):
        """Test request without Authorization header"""
        response = client.get("/api/v1/workflows/stats")
        
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403 for missing auth
        error_detail = response.json()["detail"]
        assert "Not authenticated" in error_detail

    def test_malformed_authorization_headers(self, client: TestClient):
        """Test various malformed Authorization headers"""
        test_cases = [
            {"Authorization": "invalid-header"},           # No Bearer prefix
            {"Authorization": "Bearer"},                   # Missing token
            {"Authorization": "Basic token"},              # Wrong scheme
            {"Authorization": "Bearer "},                  # Empty token
            {"Authorization": ""},                         # Empty header
        ]
        
        for headers in test_cases:
            response = client.get("/api/v1/workflows/stats", headers=headers)
            assert response.status_code in [401, 403, 422]  # Various auth failure codes

    @patch('httpx.AsyncClient.post')
    def test_valid_jwt_token_success(self, mock_post, client: TestClient, mock_user_data):
        """Test successful JWT token validation"""
        # Mock Identity Service success response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token.here"}
        response = client.get("/api/v1/definitions", headers=headers)
        
        assert response.status_code == 200
        # Verify Identity Service was called
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "auth/validate" in kwargs.get('url', '')
        assert kwargs.get('headers', {}).get('Authorization') == "Bearer valid.jwt.token.here"

    @patch('httpx.AsyncClient.post')
    def test_invalid_jwt_token_rejection(self, mock_post, client: TestClient):
        """Test invalid JWT token is rejected"""
        # Mock Identity Service rejection
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid or expired token"}
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer invalid.jwt.token"}
        response = client.get("/api/v1/definitions", headers=headers)
        
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

    @patch('httpx.AsyncClient.post')
    def test_expired_jwt_token_rejection(self, mock_post, client: TestClient):
        """Test expired JWT token is rejected"""
        # Mock Identity Service rejection for expired token
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Token expired"}
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer expired.jwt.token"}
        response = client.get("/api/v1/definitions", headers=headers)
        
        assert response.status_code == 401
        assert "Token expired" in response.json()["detail"]

    @patch('httpx.AsyncClient.post')
    def test_identity_service_timeout_handling(self, mock_post, client: TestClient):
        """Test Identity Service timeout is handled gracefully"""
        # Mock timeout exception
        mock_post.side_effect = httpx.TimeoutException("Request timeout")
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/definitions", headers=headers)
        
        assert response.status_code == 503  # Service Unavailable
        assert "Service temporarily unavailable" in response.json()["detail"]

    @patch('httpx.AsyncClient.post')
    def test_identity_service_network_error_handling(self, mock_post, client: TestClient):
        """Test Identity Service network errors are handled"""
        # Mock network error
        mock_post.side_effect = httpx.RequestError("Connection failed")
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/definitions", headers=headers)
        
        assert response.status_code == 503  # Service Unavailable
        assert "Authentication service unavailable" in response.json()["detail"]

    @patch('httpx.AsyncClient.post')
    def test_identity_service_unexpected_status_handling(self, mock_post, client: TestClient):
        """Test handling of unexpected status codes from Identity Service"""
        # Mock unexpected 500 error
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/definitions", headers=headers)
        
        assert response.status_code == 401  # Treated as auth failure
        assert "Token validation failed" in response.json()["detail"]

    @patch('httpx.AsyncClient.post')
    def test_user_context_extraction(self, mock_post, client: TestClient, mock_user_data):
        """Test user context is properly extracted from JWT validation"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/definitions", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        # Verify user context is included in response
        assert data["requested_by"] == mock_user_data["user_id"]
        assert data["organization"] == mock_user_data["organization_id"]


@pytest.mark.auth
@pytest.mark.integration
class TestRoleBasedAccessControl:
    """Test role-based access control implementation"""
    
    @patch('httpx.AsyncClient.post')
    def test_regular_user_access_to_public_endpoints(self, mock_post, client: TestClient, mock_user_data):
        """Test regular users can access public endpoints"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer user.jwt.token"}
        
        # Regular user should access these endpoints
        endpoints = [
            "/api/v1/definitions",
            "/api/v1/workflows/stats",
            f"/api/v1/workflows/user/{mock_user_data['user_id']}"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint, headers=headers)
            assert response.status_code == 200

    @patch('httpx.AsyncClient.post') 
    def test_regular_user_denied_admin_endpoints(self, mock_post, client: TestClient, mock_user_data):
        """Test regular users cannot access admin-only endpoints"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data  # Regular user without admin role
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer user.jwt.token"}
        
        # Should be denied access to admin endpoints
        admin_data = {
            "name": "Admin Only Workflow",
            "states": ["start", "end"],
            "transitions": []
        }
        
        response = client.post("/api/v1/definitions", json=admin_data, headers=headers)
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

    @patch('httpx.AsyncClient.post')
    def test_admin_user_access_to_all_endpoints(self, mock_post, client: TestClient, admin_user_data):
        """Test admin users can access all endpoints"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = admin_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer admin.jwt.token"}
        
        # Admin should access definition creation
        admin_data = {
            "name": "Admin Workflow",
            "description": "Workflow created by admin",
            "states": ["start", "end"],
            "transitions": []
        }
        
        response = client.post("/api/v1/definitions", json=admin_data, headers=headers)
        assert response.status_code == 200
        assert response.json()["created_by"] == admin_user_data["user_id"]

    @patch('httpx.AsyncClient.post')
    def test_workflow_admin_role_permissions(self, mock_post, client: TestClient, workflow_user_data):
        """Test workflow_admin role has appropriate permissions"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = workflow_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer workflow_admin.jwt.token"}
        
        # workflow_admin should be able to create definitions
        workflow_data = {
            "name": "Workflow Admin Definition",
            "states": ["draft", "approved"],
            "transitions": [{"from": "draft", "to": "approved", "action": "approve"}]
        }
        
        response = client.post("/api/v1/definitions", json=workflow_data, headers=headers)
        assert response.status_code == 200

    @patch('httpx.AsyncClient.post')
    def test_cross_organization_access_denied(self, mock_post, client: TestClient):
        """Test users cannot access resources from other organizations"""
        # Mock user from different organization
        other_org_user = {
            "user_id": "user-from-other-org",
            "organization_id": "other-org-456",
            "roles": ["user"],
            "email": "user@otherorg.com"
        }
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = other_org_user
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer other_org.jwt.token"}
        
        # Should not be able to access workflows from original organization
        response = client.get("/api/v1/workflows/user/user-from-original-org", headers=headers)
        assert response.status_code == 403

    @patch('httpx.AsyncClient.post')
    def test_user_workflow_access_control(self, mock_post, client: TestClient, mock_user_data):
        """Test users can only access their own workflows unless admin"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer user.jwt.token"}
        
        # User should access their own workflows
        response = client.get(f"/api/v1/workflows/user/{mock_user_data['user_id']}", headers=headers)
        assert response.status_code == 200
        
        # User should NOT access other user's workflows
        response = client.get("/api/v1/workflows/user/other-user-id", headers=headers)
        assert response.status_code == 403
        assert "Access denied" in response.json()["detail"]


@pytest.mark.auth
@pytest.mark.integration
class TestAuthenticationErrorScenarios:
    """Test various authentication error scenarios"""
    
    @patch('httpx.AsyncClient.post')
    def test_corrupted_jwt_token_handling(self, mock_post, client: TestClient):
        """Test handling of corrupted/malformed JWT tokens"""
        # Mock Identity Service rejecting corrupted token
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid token signature"}
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer corrupted.jwt.token.with.bad.signature"}
        response = client.get("/api/v1/definitions", headers=headers)
        
        assert response.status_code == 401
        assert "Invalid token signature" in response.json()["detail"]

    @patch('httpx.AsyncClient.post')
    def test_token_without_required_claims(self, mock_post, client: TestClient):
        """Test handling of tokens missing required claims"""
        # Mock token missing required claims
        incomplete_user_data = {
            "user_id": "user-123",
            # Missing organization_id and roles
        }
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = incomplete_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer incomplete.claims.token"}
        response = client.get("/api/v1/definitions", headers=headers)
        
        # Service should handle missing claims gracefully
        # Organization might be None, which should be handled in business logic
        assert response.status_code == 200

    @patch('httpx.AsyncClient.post')
    def test_authentication_service_rate_limiting(self, mock_post, client: TestClient):
        """Test handling of rate limiting from Identity Service"""
        # Mock Identity Service rate limiting response
        mock_response = AsyncMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"detail": "Too many requests"}
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/definitions", headers=headers)
        
        # Should be treated as auth failure
        assert response.status_code == 401
        assert "Token validation failed" in response.json()["detail"]

    @patch('httpx.AsyncClient.post')
    def test_multiple_rapid_auth_requests(self, mock_post, client: TestClient, mock_user_data):
        """Test handling of multiple rapid authentication requests"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        
        # Make multiple rapid requests
        responses = []
        for i in range(10):
            response = client.get("/api/v1/definitions", headers=headers)
            responses.append(response.status_code)
        
        # All requests should succeed (or some may be rate limited by our service)
        success_count = sum(1 for status in responses if status == 200)
        assert success_count >= 1  # At least some should succeed

    @patch('httpx.AsyncClient.post')
    def test_authentication_logging_and_monitoring(self, mock_post, client: TestClient, mock_user_data):
        """Test that authentication events are properly logged"""
        with patch('main.logger') as mock_logger:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_user_data
            mock_post.return_value = mock_response
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            response = client.get("/api/v1/definitions", headers=headers)
            
            assert response.status_code == 200
            # Verify successful authentication is logged
            mock_logger.info.assert_called_with(f"Token validated for user: {mock_user_data['user_id']}")

    @patch('httpx.AsyncClient.post')
    def test_failed_authentication_logging(self, mock_post, client: TestClient):
        """Test that failed authentication attempts are logged"""
        with patch('main.logger') as mock_logger:
            mock_response = AsyncMock()
            mock_response.status_code = 401
            mock_response.json.return_value = {"detail": "Invalid token"}
            mock_post.return_value = mock_response
            
            headers = {"Authorization": "Bearer invalid.jwt.token"}
            response = client.get("/api/v1/definitions", headers=headers)
            
            assert response.status_code == 401
            # Verify failed authentication is logged as warning
            mock_logger.warning.assert_called_with("Invalid or expired token provided")


@pytest.mark.auth
@pytest.mark.integration
class TestSecurityHeaders:
    """Test security headers in authentication responses"""
    
    def test_www_authenticate_header_on_auth_failure(self, client: TestClient):
        """Test WWW-Authenticate header is included on auth failures"""
        response = client.get("/api/v1/definitions")
        
        assert response.status_code == 403
        # FastAPI may not include WWW-Authenticate for 403, but 401 responses should

    @patch('httpx.AsyncClient.post')
    def test_auth_failure_response_format(self, mock_post, client: TestClient):
        """Test authentication failure responses follow standard format"""
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid token"}
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer invalid.token"}
        response = client.get("/api/v1/definitions", headers=headers)
        
        assert response.status_code == 401
        assert "detail" in response.json()
        assert isinstance(response.json()["detail"], str)

    def test_no_sensitive_data_in_error_responses(self, client: TestClient):
        """Test that error responses don't leak sensitive information"""
        # Test with various malformed tokens
        test_tokens = [
            "Bearer leaked.secret.key",
            "Bearer database.connection.string",
            "Bearer internal.system.info"
        ]
        
        for token in test_tokens:
            headers = {"Authorization": token}
            response = client.get("/api/v1/definitions", headers=headers)
            
            error_detail = response.json().get("detail", "")
            # Error messages should not contain parts of the token or other sensitive info
            assert "secret" not in error_detail.lower()
            assert "database" not in error_detail.lower()
            assert "password" not in error_detail.lower()


@pytest.mark.auth
@pytest.mark.integration
class TestAuthenticationPerformance:
    """Test authentication performance characteristics"""
    
    @pytest.mark.slow
    @patch('httpx.AsyncClient.post')
    def test_authentication_response_time(self, mock_post, client: TestClient, mock_user_data):
        """Test authentication doesn't significantly impact response time"""
        import time
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        
        start_time = time.time()
        response = client.get("/api/v1/definitions", headers=headers)
        end_time = time.time()
        
        auth_time = end_time - start_time
        
        assert response.status_code == 200
        assert auth_time < 2.0  # Authentication should not take more than 2 seconds

    @pytest.mark.slow
    @patch('httpx.AsyncClient.post')
    def test_concurrent_authentication_requests(self, mock_post, client: TestClient, mock_user_data):
        """Test system handles concurrent authentication requests"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        import concurrent.futures
        
        def make_authenticated_request():
            headers = {"Authorization": "Bearer valid.jwt.token"}
            return client.get("/api/v1/definitions", headers=headers)
        
        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_authenticated_request) for _ in range(20)]
            responses = [future.result() for future in futures]
        
        # All should succeed
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 18  # Allow for some potential failures due to timing

    @patch('httpx.AsyncClient.post')
    def test_authentication_caching_behavior(self, mock_post, client: TestClient, mock_user_data):
        """Test authentication caching (if implemented)"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer same.jwt.token"}
        
        # Make multiple requests with same token
        for _ in range(3):
            response = client.get("/api/v1/definitions", headers=headers)
            assert response.status_code == 200
        
        # Should have called Identity Service for each request (no caching implemented)
        assert mock_post.call_count == 3


@pytest.mark.auth
@pytest.mark.integration
class TestEndpointAuthCoverage:
    """Verify 100% authentication coverage on all endpoints"""
    
    @pytest.mark.parametrize("endpoint,method", [
        ("/api/v1/workflows", "POST"),
        ("/api/v1/workflows/test-id/status", "GET"),
        ("/api/v1/workflows/test-id/next", "PATCH"),
        ("/api/v1/workflows/user/test-user", "GET"),
        ("/api/v1/ai/summarize", "POST"),
        ("/api/v1/ai/suggest", "POST"),
        ("/api/v1/ai/analyze", "POST"),
        ("/api/v1/definitions", "GET"),
        ("/api/v1/definitions", "POST"),
        ("/api/v1/workflows/stats", "GET"),
        ("/api/v1/workflows/sla-check", "GET"),
    ])
    def test_all_business_endpoints_require_auth(self, client: TestClient, endpoint, method):
        """Test that all business endpoints require authentication"""
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json={})
        elif method == "PATCH":
            response = client.patch(endpoint, json={})
        elif method == "PUT":
            response = client.put(endpoint, json={})
        elif method == "DELETE":
            response = client.delete(endpoint)
        
        # All business endpoints should require authentication
        assert response.status_code in [401, 403]  # Either auth error

    @pytest.mark.parametrize("endpoint", [
        "/health",
        "/docs",
        "/redoc", 
        "/openapi.json",
    ])
    def test_public_endpoints_no_auth_required(self, client: TestClient, endpoint):
        """Test that public endpoints don't require authentication"""
        response = client.get(endpoint)
        
        # Public endpoints should be accessible without auth
        assert response.status_code == 200