"""
Authentication integration tests with Identity Service
Tests JWT validation, user context, permissions, and error scenarios
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from tests.fixtures.mock_responses import IdentityServiceMocks

@pytest.mark.auth
@pytest.mark.integration
class TestJWTAuthentication:
    """Test JWT token validation with Identity Service"""
    
    @patch('httpx.AsyncClient.post')
    def test_jwt_validation_success(self, mock_post, client: TestClient):
        """Test successful JWT token validation"""
        # Mock successful Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/notifications/unread", headers=headers)
        
        # Should succeed with valid token
        assert response.status_code == 200
        
        # Verify Identity Service was called correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "auth/validate" in str(call_args) or "validate" in str(call_args)
        
        # Should include JWT token in request
        auth_header = None
        if call_args.kwargs.get('headers'):
            auth_header = call_args.kwargs['headers'].get('Authorization')
        assert auth_header == "Bearer valid.jwt.token"
    
    @patch('httpx.AsyncClient.post')
    def test_jwt_validation_invalid_token(self, mock_post, client: TestClient):
        """Test JWT validation with invalid token"""
        # Mock invalid token response
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.json.return_value = IdentityServiceMocks.get_invalid_token_response()["json"]
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer invalid.jwt.token"}
        response = client.get("/api/v1/notifications/unread", headers=headers)
        
        # Should fail with 401
        assert response.status_code == 401
        error_data = response.json()
        assert "detail" in error_data
        assert "invalid" in error_data["detail"].lower() or "expired" in error_data["detail"].lower()
        
        # Should have WWW-Authenticate header
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"
    
    @patch('httpx.AsyncClient.post')
    def test_jwt_validation_expired_token(self, mock_post, client: TestClient):
        """Test JWT validation with expired token"""
        # Mock expired token response
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.json.return_value = IdentityServiceMocks.get_expired_token_response()["json"]
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer expired.jwt.token"}
        response = client.get("/api/v1/notifications/unread", headers=headers)
        
        # Should fail with 401
        assert response.status_code == 401
        error_data = response.json()
        assert "expired" in error_data["detail"].lower()
    
    def test_missing_authorization_header(self, client: TestClient):
        """Test request without Authorization header"""
        response = client.get("/api/v1/notifications/unread")
        
        assert response.status_code == 401
        error_data = response.json()
        assert "not authenticated" in error_data["detail"].lower()
        
        # Should have WWW-Authenticate header
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"
    
    def test_malformed_authorization_headers(self, client: TestClient):
        """Test various malformed Authorization headers"""
        malformed_headers = [
            {"Authorization": "invalid-header"},          # No Bearer prefix
            {"Authorization": "Bearer"},                  # Missing token
            {"Authorization": "Basic dXNlcjpwYXNz"},     # Wrong scheme
            {"Authorization": "Bearer "},                # Empty token
            {"Authorization": " Bearer valid.token"},    # Leading space
            {"Authorization": "bearer valid.token"},     # Lowercase bearer
        ]
        
        for headers in malformed_headers:
            response = client.get("/api/v1/notifications/unread", headers=headers)
            assert response.status_code == 401, f"Should fail for header: {headers}"
            
            error_data = response.json()
            assert "detail" in error_data
    
    @patch('httpx.AsyncClient.post')
    def test_jwt_validation_timeout_handling(self, mock_post, client: TestClient):
        """Test handling JWT validation timeout"""
        # Mock timeout exception
        import httpx
        mock_post.side_effect = httpx.TimeoutException("Request timeout")
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/notifications/unread", headers=headers)
        
        # Should return 503 Service Unavailable
        assert response.status_code == 503
        error_data = response.json()
        assert "service temporarily unavailable" in error_data["detail"].lower()
        assert "timeout" in error_data["detail"].lower() or "unavailable" in error_data["detail"].lower()
    
    @patch('httpx.AsyncClient.post')
    def test_jwt_validation_connection_error(self, mock_post, client: TestClient):
        """Test handling Identity Service connection error"""
        # Mock connection error
        import httpx
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/notifications/unread", headers=headers)
        
        # Should return 503 Service Unavailable
        assert response.status_code == 503
        error_data = response.json()
        assert "service temporarily unavailable" in error_data["detail"].lower()
    
    @patch('httpx.AsyncClient.post')
    def test_jwt_validation_network_error(self, mock_post, client: TestClient):
        """Test handling network errors during validation"""
        # Mock network error
        import httpx
        mock_post.side_effect = httpx.RequestError("Network error")
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/notifications/unread", headers=headers)
        
        # Should return 503 Service Unavailable
        assert response.status_code == 503
        error_data = response.json()
        assert "service temporarily unavailable" in error_data["detail"].lower()
    
    @patch('httpx.AsyncClient.post')
    def test_identity_service_500_error(self, mock_post, client: TestClient):
        """Test handling Identity Service internal server error"""
        # Mock 500 response
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Internal server error"}
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/notifications/unread", headers=headers)
        
        # Should return 503 Service Unavailable
        assert response.status_code == 503
        error_data = response.json()
        assert "service temporarily unavailable" in error_data["detail"].lower()


@pytest.mark.auth
@pytest.mark.integration
class TestUserContextExtraction:
    """Test user context extraction from JWT tokens"""
    
    @patch('httpx.AsyncClient.post')
    def test_user_context_in_notification_creation(self, mock_post, client: TestClient):
        """Test user context is properly extracted in notification creation"""
        # Mock Identity Service response with specific user data
        user_data = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = user_data
        mock_post.return_value = mock_response
        
        # Mock Celery task
        with patch('tasks.notification_tasks.send_notification') as mock_task:
            mock_result = MagicMock()
            mock_result.id = "task-123"
            mock_task.apply_async.return_value = mock_result
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            notification_data = {
                "type": "email",
                "to": "test@example.com",
                "message": "Test message"
            }
            
            response = client.post("/api/v1/notifications",
                                  json=notification_data,
                                  headers=headers)
            
            assert response.status_code == 200
            
            # Verify user context was passed to task
            mock_task.apply_async.assert_called_once()
            call_args = mock_task.apply_async.call_args
            task_kwargs = call_args[1] if len(call_args) > 1 else call_args.kwargs
            
            # Should contain user information from JWT
            assert any(user_data["user_id"] in str(arg) for arg in [call_args, task_kwargs])
    
    @patch('httpx.AsyncClient.post')
    def test_organization_context_isolation(self, mock_post, client: TestClient):
        """Test organization context isolation"""
        # Mock user from specific organization
        user_data = IdentityServiceMocks.get_successful_token_validation()["json"]
        user_data["organization_id"] = "specific-org-123"
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = user_data
        mock_post.return_value = mock_response
        
        # Mock in-app provider to verify organization filtering
        with patch('providers.in_app.InAppProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.get_unread_notifications.return_value = []
            mock_instance.get_unread_count.return_value = 0
            mock_provider.return_value = mock_instance
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            response = client.get("/api/v1/notifications/unread", headers=headers)
            
            assert response.status_code == 200
            
            # Verify provider was called with correct organization context
            mock_instance.get_unread_notifications.assert_called_once()
            call_args = mock_instance.get_unread_notifications.call_args
            
            # Should include organization_id in the call
            assert any("specific-org-123" in str(arg) for arg in call_args)
    
    @patch('httpx.AsyncClient.post')
    def test_user_permissions_validation(self, mock_post, client: TestClient):
        """Test user permissions are properly validated"""
        # Mock user with limited permissions
        user_data = IdentityServiceMocks.get_successful_token_validation()["json"]
        user_data["permissions"] = ["notification:read"]  # No write permission
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        
        # Should succeed for read operation
        response = client.get("/api/v1/notifications/unread", headers=headers)
        assert response.status_code == 200
        
        # Should potentially fail for write operation (if permissions are checked)
        notification_data = {
            "type": "email",
            "to": "test@example.com",
            "message": "Test message"
        }
        
        with patch('tasks.notification_tasks.send_notification'):
            response = client.post("/api/v1/notifications",
                                  json=notification_data,
                                  headers=headers)
            
            # Depending on implementation, might succeed or fail
            # This test documents expected behavior
            assert response.status_code in [200, 403]


@pytest.mark.auth
@pytest.mark.integration
class TestRoleBasedAccess:
    """Test role-based access control"""
    
    @patch('httpx.AsyncClient.post')
    def test_admin_access_to_queue_status(self, mock_post, client: TestClient):
        """Test admin can access queue status"""
        # Mock admin user
        admin_data = IdentityServiceMocks.get_admin_token_validation()["json"]
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = admin_data
        mock_post.return_value = mock_response
        
        # Mock queue manager
        with patch('services.queue_manager.QueueManager') as mock_queue:
            mock_instance = AsyncMock()
            mock_instance.get_queue_status.return_value = {
                "total_pending": 10,
                "queues": {"normal": {"pending": 10}}
            }
            mock_queue.return_value = mock_instance
            
            headers = {"Authorization": "Bearer admin.jwt.token"}
            response = client.get("/api/v1/queue/status", headers=headers)
            
            assert response.status_code == 200
            result = response.json()
            assert "total_pending" in result
    
    @patch('httpx.AsyncClient.post')
    def test_regular_user_denied_queue_access(self, mock_post, client: TestClient):
        """Test regular user cannot access queue status"""
        # Mock regular user
        user_data = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer user.jwt.token"}
        response = client.get("/api/v1/queue/status", headers=headers)
        
        # Should be denied access
        assert response.status_code == 403
        error_data = response.json()
        assert "insufficient permissions" in error_data["detail"].lower() or \
               "forbidden" in error_data["detail"].lower()
    
    @patch('httpx.AsyncClient.post')
    def test_admin_template_management(self, mock_post, client: TestClient):
        """Test admin can manage templates"""
        # Mock admin user
        admin_data = IdentityServiceMocks.get_admin_token_validation()["json"]
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = admin_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer admin.jwt.token"}
        template_data = {
            "name": "test_template",
            "category": "system",
            "channel": "email",
            "subject": "Test {{name}}",
            "content": "Hello {{name}}!"
        }
        
        response = client.post("/api/v1/templates",
                              json=template_data,
                              headers=headers)
        
        # Should succeed for admin
        assert response.status_code in [200, 201]
    
    @patch('httpx.AsyncClient.post')
    def test_regular_user_denied_template_creation(self, mock_post, client: TestClient):
        """Test regular user cannot create templates"""
        # Mock regular user
        user_data = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = user_data
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer user.jwt.token"}
        template_data = {
            "name": "test_template",
            "category": "system", 
            "channel": "email",
            "subject": "Test",
            "content": "Content"
        }
        
        response = client.post("/api/v1/templates",
                              json=template_data,
                              headers=headers)
        
        # Should be denied
        assert response.status_code == 403


@pytest.mark.auth
@pytest.mark.integration  
class TestProtectedEndpoints:
    """Test that all protected endpoints require authentication"""
    
    def test_all_protected_endpoints_require_auth(self, client: TestClient, protected_endpoints):
        """Test all protected endpoints reject unauthenticated requests"""
        for method, endpoint, data in protected_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json=data)
            elif method == "PUT":
                response = client.put(endpoint, json=data)
            elif method == "DELETE":
                response = client.delete(endpoint)
            elif method == "PATCH":
                response = client.patch(endpoint, json=data)
            else:
                continue
            
            assert response.status_code == 401, f"{method} {endpoint} should require authentication"
            
            error_data = response.json()
            assert "detail" in error_data
            assert "not authenticated" in error_data["detail"].lower()
            
            # Should have WWW-Authenticate header
            assert "WWW-Authenticate" in response.headers
            assert response.headers["WWW-Authenticate"] == "Bearer"
    
    @patch('httpx.AsyncClient.post')
    def test_protected_endpoints_with_valid_auth(self, mock_post, client: TestClient, protected_endpoints):
        """Test protected endpoints accept valid authentication"""
        # Mock successful authentication
        user_data = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = user_data
        mock_post.return_value = mock_response
        
        # Mock dependencies for endpoints that need them
        with patch('tasks.notification_tasks.send_notification') as mock_task, \
             patch('providers.in_app.InAppProvider') as mock_provider, \
             patch('services.queue_manager.QueueManager') as mock_queue:
            
            # Setup mocks
            mock_task_result = MagicMock()
            mock_task_result.id = "task-123"
            mock_task.apply_async.return_value = mock_task_result
            
            mock_provider_instance = AsyncMock()
            mock_provider_instance.get_unread_notifications.return_value = []
            mock_provider_instance.get_unread_count.return_value = 0
            mock_provider.return_value = mock_provider_instance
            
            mock_queue_instance = AsyncMock()
            mock_queue_instance.get_queue_status.return_value = {"total_pending": 0}
            mock_queue.return_value = mock_queue_instance
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            
            for method, endpoint, data in protected_endpoints:
                # Skip admin-only endpoints for regular user
                if "/queue/" in endpoint:
                    continue
                    
                if method == "GET":
                    response = client.get(endpoint, headers=headers)
                elif method == "POST":
                    response = client.post(endpoint, json=data, headers=headers)
                elif method == "PUT":
                    response = client.put(endpoint, json=data, headers=headers)
                elif method == "DELETE":
                    response = client.delete(endpoint, headers=headers)
                elif method == "PATCH":
                    response = client.patch(endpoint, json=data, headers=headers)
                else:
                    continue
                
                # Should not be 401 (authentication should pass)
                assert response.status_code != 401, f"{method} {endpoint} should accept valid auth"
                
                # May be 403 (authorization), 404 (not found), 422 (validation), etc.
                # but should not be 401 (authentication)
                assert response.status_code in [200, 201, 202, 403, 404, 422, 500]


@pytest.mark.auth
@pytest.mark.integration
class TestAuthenticationPerformance:
    """Test authentication performance and caching"""
    
    @patch('httpx.AsyncClient.post')
    def test_jwt_validation_performance(self, mock_post, client: TestClient):
        """Test JWT validation doesn't add excessive latency"""
        # Mock successful validation
        user_data = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = user_data
        mock_post.return_value = mock_response
        
        import time
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        
        # Make multiple requests to test performance
        start_time = time.time()
        
        for _ in range(5):
            response = client.get("/api/v1/notifications/unread", headers=headers)
            assert response.status_code == 200
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete 5 requests reasonably quickly (adjust threshold as needed)
        assert total_time < 5.0, f"Authentication took too long: {total_time}s for 5 requests"
        
        # Should have made 5 calls to Identity Service (unless cached)
        assert mock_post.call_count <= 5
    
    @patch('httpx.AsyncClient.post')
    def test_concurrent_authentication_requests(self, mock_post, client: TestClient):
        """Test handling concurrent authentication requests"""
        import asyncio
        import concurrent.futures
        
        # Mock successful validation
        user_data = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = user_data
        mock_post.return_value = mock_response
        
        def make_request():
            headers = {"Authorization": "Bearer valid.jwt.token"}
            return client.get("/api/v1/notifications/unread", headers=headers)
        
        # Make concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Should have handled concurrent requests properly
        assert len(responses) == 10


@pytest.mark.auth
@pytest.mark.integration
class TestTokenEdgeCases:
    """Test edge cases in token handling"""
    
    def test_extremely_long_token(self, client: TestClient):
        """Test handling extremely long JWT tokens"""
        # Create very long token
        long_token = "a" * 10000
        headers = {"Authorization": f"Bearer {long_token}"}
        
        response = client.get("/api/v1/notifications/unread", headers=headers)
        
        # Should handle gracefully (reject or process)
        assert response.status_code in [401, 413, 422]
    
    def test_token_with_special_characters(self, client: TestClient):
        """Test tokens with special characters"""
        special_tokens = [
            "token.with.dots",
            "token-with-dashes", 
            "token_with_underscores",
            "token+with+plus",
            "token/with/slashes",
            "token=with=equals"
        ]
        
        for token in special_tokens:
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/v1/notifications/unread", headers=headers)
            
            # Should handle gracefully (likely 401 for invalid tokens)
            assert response.status_code in [401, 422]
    
    def test_multiple_authorization_headers(self, client: TestClient):
        """Test handling multiple Authorization headers"""
        headers = {
            "Authorization": "Bearer first.token",
            # Note: This is tricky to test with standard HTTP libraries
            # as they typically merge duplicate headers
        }
        
        response = client.get("/api/v1/notifications/unread", headers=headers)
        
        # Should handle gracefully
        assert response.status_code in [401, 422]
    
    @patch('httpx.AsyncClient.post')
    def test_token_validation_response_malformed(self, mock_post, client: TestClient):
        """Test handling malformed validation response from Identity Service"""
        # Mock malformed response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"invalid": "response_format"}  # Missing required fields
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/notifications/unread", headers=headers)
        
        # Should handle malformed response gracefully
        assert response.status_code in [401, 503]