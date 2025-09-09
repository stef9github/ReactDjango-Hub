"""
Tests for JWT Authentication Integration
Following the JWT_AUTHENTICATION_INTEGRATION_GUIDE.md
"""
import pytest
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app

class TestJWTAuthentication:
    """Test JWT token validation integration"""

    @patch('main.httpx.AsyncClient')
    def test_valid_token_authentication(self, mock_client):
        """Test successful authentication with valid token"""
        # Mock user data
        mock_user_data = {
            "user_id": "12345678-1234-5678-9012-123456789012",
            "organization_id": "87654321-4321-8765-2109-876543210987",
            "email": "test@example.com",
            "roles": ["user"],
            "permissions": ["read", "write"],
            "is_verified": True,
            "expires_at": "2025-12-31T23:59:59Z"
        }
        
        # Mock Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        client = TestClient(app)
        valid_token = "valid.jwt.token"
        
        # Test protected endpoint
        response = client.post(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "type": "email",
                "to": "test@example.com",
                "message": "Test notification"
            }
        )
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["sent_by"] == mock_user_data["user_id"]
        assert response_data["organization"] == mock_user_data["organization_id"]
        
        # Verify Identity Service was called correctly
        mock_client.return_value.__aenter__.return_value.post.assert_called_once_with(
            "http://localhost:8001/auth/validate",
            headers={"Authorization": f"Bearer {valid_token}"},
            timeout=5.0
        )

    @patch('main.httpx.AsyncClient')
    def test_invalid_token_authentication(self, mock_client):
        """Test authentication failure with invalid token"""
        # Mock Identity Service rejection
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid token"}
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        client = TestClient(app)
        invalid_token = "invalid.jwt.token"
        
        # Test protected endpoint
        response = client.post(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {invalid_token}"},
            json={
                "type": "email",
                "to": "test@example.com",
                "message": "Test notification"
            }
        )
        
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"

    def test_missing_token_authentication(self):
        """Test authentication failure with no token"""
        client = TestClient(app)
        
        response = client.post(
            "/api/v1/notifications",
            json={
                "type": "email",
                "to": "test@example.com",
                "message": "Test notification"
            }
        )
        
        assert response.status_code in [401, 403]  # FastAPI HTTPBearer returns 403 for missing auth
        assert "Not authenticated" in response.json()["detail"]

    @patch('main.httpx.AsyncClient')
    def test_identity_service_timeout(self, mock_client):
        """Test handling of Identity Service timeout"""
        # Mock timeout exception
        mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.TimeoutException("Timeout")
        
        client = TestClient(app)
        valid_token = "valid.jwt.token"
        
        response = client.post(
            "/api/v1/notifications", 
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "type": "email",
                "to": "test@example.com",
                "message": "Test notification"
            }
        )
        
        assert response.status_code == 503
        assert "temporarily unavailable" in response.json()["detail"]

    @patch('main.httpx.AsyncClient')
    def test_identity_service_network_error(self, mock_client):
        """Test handling of Identity Service network errors"""
        # Mock network exception
        mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.RequestError("Network error")
        
        client = TestClient(app)
        valid_token = "valid.jwt.token"
        
        response = client.post(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "type": "email", 
                "to": "test@example.com",
                "message": "Test notification"
            }
        )
        
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"]

    @patch('main.httpx.AsyncClient')
    def test_identity_service_unexpected_status(self, mock_client):
        """Test handling of unexpected status codes from Identity Service"""
        # Mock unexpected status code
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        client = TestClient(app)
        valid_token = "valid.jwt.token"
        
        response = client.post(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "type": "email",
                "to": "test@example.com", 
                "message": "Test notification"
            }
        )
        
        assert response.status_code == 401
        assert "Token validation failed" in response.json()["detail"]

    @patch('main.httpx.AsyncClient')
    def test_general_exception_handling(self, mock_client):
        """Test handling of general exceptions during token validation"""
        # Mock general exception
        mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Unexpected error")
        
        client = TestClient(app)
        valid_token = "valid.jwt.token"
        
        response = client.post(
            "/api/v1/notifications",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={
                "type": "email",
                "to": "test@example.com",
                "message": "Test notification"
            }
        )
        
        assert response.status_code == 401
        assert "Token validation failed" in response.json()["detail"]

    @patch('main.httpx.AsyncClient')  
    def test_user_context_in_endpoints(self, mock_client):
        """Test that user context is properly available in endpoints"""
        # Mock user data
        mock_user_data = {
            "user_id": "user-123",
            "organization_id": "org-456", 
            "email": "test@example.com",
            "roles": ["admin", "user"],
            "permissions": ["read", "write", "admin"]
        }
        
        # Mock successful auth
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        client = TestClient(app)
        valid_token = "valid.jwt.token"
        
        # Test different endpoints to verify user context
        endpoints_to_test = [
            ("/api/v1/notifications/unread", "GET", None),
            ("/api/v1/conversations", "GET", None),
            ("/api/v1/templates", "GET", None),
            ("/api/v1/queue/status", "GET", None),
        ]
        
        for endpoint, method, data in endpoints_to_test:
            if method == "GET":
                response = client.get(
                    endpoint,
                    headers={"Authorization": f"Bearer {valid_token}"}
                )
            elif method == "POST":
                response = client.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {valid_token}"},
                    json=data
                )
            
            # Should not be authentication error
            assert response.status_code != 401
            
            # Verify user context is included in response
            response_data = response.json()
            if "user_id" in response_data:
                assert response_data["user_id"] == mock_user_data["user_id"]
            if "organization" in response_data:
                assert response_data["organization"] == mock_user_data["organization_id"]
            if "user_roles" in response_data:
                assert response_data["user_roles"] == mock_user_data["roles"]

class TestAuthenticationLogging:
    """Test authentication logging behavior"""
    
    @patch('main.httpx.AsyncClient')
    @patch('main.logger')
    def test_successful_authentication_logging(self, mock_logger, mock_client):
        """Test that successful authentication is logged"""
        # Mock user data
        mock_user_data = {
            "user_id": "test-user-123",
            "email": "test@example.com"
        }
        
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        client = TestClient(app)
        response = client.get(
            "/api/v1/templates",
            headers={"Authorization": "Bearer valid.token"}
        )
        
        # Verify logging was called
        mock_logger.info.assert_called_with("Token validated for user: test-user-123")
    
    @patch('main.httpx.AsyncClient')
    @patch('main.logger') 
    def test_authentication_failure_logging(self, mock_logger, mock_client):
        """Test that authentication failures are logged"""
        # Mock rejection response
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        client = TestClient(app)
        response = client.get(
            "/api/v1/templates",
            headers={"Authorization": "Bearer invalid.token"}
        )
        
        # Verify warning was logged
        mock_logger.warning.assert_called_with("Invalid or expired token provided")

class TestAuthenticationPerformance:
    """Test authentication performance"""
    
    @patch('main.httpx.AsyncClient')
    def test_auth_response_time(self, mock_client):
        """Test that authentication doesn't add excessive latency"""
        import time
        
        # Mock fast Identity Service response
        mock_user_data = {
            "user_id": "user-123",
            "organization_id": "org-456"
        }
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        client = TestClient(app)
        
        start_time = time.time()
        response = client.get(
            "/api/v1/notifications/unread",
            headers={"Authorization": "Bearer valid.jwt.token"}
        )
        end_time = time.time()
        
        # Authentication should add minimal overhead (< 1 second in test environment)
        assert (end_time - start_time) < 1.0
        assert response.status_code != 401

class TestAuthenticationConfiguration:
    """Test authentication configuration"""
    
    @patch.dict('os.environ', {'IDENTITY_SERVICE_URL': 'http://custom-identity:9001'})
    @patch('main.httpx.AsyncClient')
    def test_custom_identity_service_url(self, mock_client):
        """Test that custom Identity Service URL is used"""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user_id": "test"}
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Import main after setting environment variable
        from importlib import reload
        import main
        reload(main)
        
        client = TestClient(main.app)
        response = client.get(
            "/api/v1/templates",
            headers={"Authorization": "Bearer test.token"}
        )
        
        # Verify custom URL was used
        mock_client.return_value.__aenter__.return_value.post.assert_called_with(
            "http://custom-identity:9001/auth/validate",
            headers={"Authorization": "Bearer test.token"},
            timeout=5.0
        )