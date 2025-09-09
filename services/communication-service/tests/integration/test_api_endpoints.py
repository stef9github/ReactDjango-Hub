"""
Integration tests for notification API endpoints
Tests complete API workflows with database and authentication
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from tests.fixtures.sample_data import SampleNotificationData, SampleAPIData
from tests.fixtures.mock_responses import IdentityServiceMocks, EmailProviderMocks

@pytest.mark.integration
class TestNotificationEndpoints:
    """Integration tests for notification API endpoints"""
    
    def test_health_endpoint_no_auth_required(self, client: TestClient):
        """Test health endpoint is accessible without authentication"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "status" in data
        assert data["service"] == "communication-service"
        assert data["status"] in ["healthy", "degraded"]
    
    def test_metrics_endpoint_no_auth_required(self, client: TestClient):
        """Test metrics endpoint is accessible without authentication"""
        response = client.get("/metrics")
        
        assert response.status_code == 200
        # Should return Prometheus metrics format
        assert response.headers["content-type"].startswith("text/plain")
    
    @patch('httpx.AsyncClient.post')
    def test_send_email_notification_success(self, mock_post, client: TestClient):
        """Test sending email notification successfully"""
        # Mock Identity Service validation
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_post.return_value = mock_response
        
        # Mock Celery task
        with patch('tasks.notification_tasks.send_notification') as mock_task:
            mock_result = MagicMock()
            mock_result.id = "task-123-456-789"
            mock_task.apply_async.return_value = mock_result
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            notification_data = {
                "type": "email",
                "to": "test@example.com",
                "subject": "Test Email",
                "message": "This is a test email notification",
                "priority": "normal",
                "data": {"user_name": "Test User"}
            }
            
            response = client.post("/api/v1/notifications",
                                  json=notification_data,
                                  headers=headers)
            
            assert response.status_code == 200
            result = response.json()
            assert "notification_id" in result
            assert "task_id" in result
            assert result["status"] == "queued"
            assert result["task_id"] == "task-123-456-789"
    
    @patch('httpx.AsyncClient.post')
    def test_send_sms_notification_success(self, mock_post, client: TestClient):
        """Test sending SMS notification successfully"""
        # Mock Identity Service validation
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_post.return_value = mock_response
        
        # Mock Celery task
        with patch('tasks.notification_tasks.send_notification') as mock_task:
            mock_result = MagicMock()
            mock_result.id = "task-sms-123"
            mock_task.apply_async.return_value = mock_result
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            notification_data = {
                "type": "sms",
                "to": "+1234567890",
                "message": "Your verification code is 123456",
                "priority": "high",
                "data": {"code": "123456"}
            }
            
            response = client.post("/api/v1/notifications",
                                  json=notification_data,
                                  headers=headers)
            
            assert response.status_code == 200
            result = response.json()
            assert "notification_id" in result
            assert "task_id" in result
            assert result["status"] == "queued"
    
    @patch('httpx.AsyncClient.post')
    def test_send_push_notification_success(self, mock_post, client: TestClient):
        """Test sending push notification successfully"""
        # Mock Identity Service validation
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_post.return_value = mock_response
        
        # Mock Celery task
        with patch('tasks.notification_tasks.send_notification') as mock_task:
            mock_result = MagicMock()
            mock_result.id = "task-push-123"
            mock_task.apply_async.return_value = mock_result
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            notification_data = {
                "type": "push",
                "to": "push-token-123456",
                "title": "New Message",
                "message": "You have received a new message",
                "data": {"deep_link": "/messages/123"}
            }
            
            response = client.post("/api/v1/notifications",
                                  json=notification_data,
                                  headers=headers)
            
            assert response.status_code == 200
            result = response.json()
            assert "notification_id" in result
            assert "task_id" in result
            assert result["status"] == "queued"
    
    @patch('httpx.AsyncClient.post')
    def test_send_notification_with_template(self, mock_post, client: TestClient, sample_notification_template):
        """Test sending notification using template"""
        # Mock Identity Service validation
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_post.return_value = mock_response
        
        # Mock Celery task and template rendering
        with patch('tasks.notification_tasks.send_notification') as mock_task, \
             patch('services.template_engine.TemplateEngine') as mock_engine:
            
            mock_result = MagicMock()
            mock_result.id = "task-template-123"
            mock_task.apply_async.return_value = mock_result
            
            # Mock template engine
            mock_engine_instance = MagicMock()
            mock_engine_instance.render.return_value = "Hello Test User, this is a test notification."
            mock_engine.return_value = mock_engine_instance
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            notification_data = {
                "type": "email",
                "to": "test@example.com",
                "template_id": sample_notification_template.id,
                "data": {"name": "Test User", "action": "test"}
            }
            
            response = client.post("/api/v1/notifications",
                                  json=notification_data,
                                  headers=headers)
            
            assert response.status_code == 200
            result = response.json()
            assert "notification_id" in result
            assert "task_id" in result
            assert result["status"] == "queued"
    
    def test_send_notification_without_auth(self, client: TestClient):
        """Test sending notification without authentication fails"""
        notification_data = {
            "type": "email",
            "to": "test@example.com",
            "message": "Test message"
        }
        
        response = client.post("/api/v1/notifications", json=notification_data)
        
        assert response.status_code == 401
        assert "detail" in response.json()
        assert "Not authenticated" in response.json()["detail"]
    
    @patch('httpx.AsyncClient.post')
    def test_send_notification_invalid_token(self, mock_post, client: TestClient):
        """Test sending notification with invalid token"""
        # Mock Identity Service failure
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.json.return_value = IdentityServiceMocks.get_invalid_token_response()["json"]
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer invalid.jwt.token"}
        notification_data = {
            "type": "email",
            "to": "test@example.com",
            "message": "Test message"
        }
        
        response = client.post("/api/v1/notifications",
                              json=notification_data,
                              headers=headers)
        
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]
    
    def test_send_notification_validation_errors(self, client: TestClient):
        """Test send notification endpoint validation"""
        # Mock valid authentication but test validation
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
            mock_post.return_value = mock_response
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            
            # Test cases for validation errors
            test_cases = [
                # Missing required fields
                ({}, "type"),
                ({"type": "email"}, "to"),
                ({"type": "email", "to": "test@example.com"}, "message"),
                
                # Invalid field values
                ({"type": "invalid", "to": "test@example.com", "message": "test"}, "type"),
                ({"type": "email", "to": "invalid-email", "message": "test"}, "to"),
                ({"type": "sms", "to": "invalid-phone", "message": "test"}, "to"),
            ]
            
            for invalid_data, expected_field in test_cases:
                response = client.post("/api/v1/notifications",
                                      json=invalid_data,
                                      headers=headers)
                
                assert response.status_code == 422, f"Should fail validation for {expected_field}"
                error_details = response.json()
                assert "detail" in error_details
    
    @patch('httpx.AsyncClient.post')
    def test_get_unread_notifications_success(self, mock_post, client: TestClient):
        """Test getting unread notifications successfully"""
        # Mock Identity Service validation
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_post.return_value = mock_response
        
        # Mock in-app provider
        with patch('providers.in_app.InAppProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.get_unread_notifications.return_value = [
                {
                    "id": "notif-1",
                    "subject": "Welcome!",
                    "content": "Welcome to our platform",
                    "created_at": datetime.utcnow().isoformat(),
                    "is_read": False
                }
            ]
            mock_instance.get_unread_count.return_value = 1
            mock_provider.return_value = mock_instance
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            response = client.get("/api/v1/notifications/unread", headers=headers)
            
            assert response.status_code == 200
            result = response.json()
            assert "unread_count" in result
            assert "notifications" in result
            assert result["unread_count"] == 1
            assert len(result["notifications"]) == 1
    
    def test_get_unread_notifications_without_auth(self, client: TestClient):
        """Test getting unread notifications without authentication"""
        response = client.get("/api/v1/notifications/unread")
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    @patch('httpx.AsyncClient.post')
    def test_mark_notifications_read_success(self, mock_post, client: TestClient):
        """Test marking notifications as read"""
        # Mock Identity Service validation
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_post.return_value = mock_response
        
        # Mock in-app provider
        with patch('providers.in_app.InAppProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.mark_notifications_read.return_value = 3  # 3 notifications marked as read
            mock_provider.return_value = mock_instance
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            request_data = {
                "notification_ids": ["notif-1", "notif-2", "notif-3"]
            }
            
            response = client.post("/api/v1/notifications/mark-read",
                                  json=request_data,
                                  headers=headers)
            
            assert response.status_code == 200
            result = response.json()
            assert "marked_count" in result
            assert result["marked_count"] == 3
    
    @patch('httpx.AsyncClient.post')
    def test_get_notification_status_success(self, mock_post, client: TestClient, sample_notification):
        """Test getting notification status"""
        # Mock Identity Service validation
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get(f"/api/v1/notifications/{sample_notification.id}/status",
                             headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        assert "notification_id" in result
        assert "status" in result
        assert "channel" in result
        assert result["notification_id"] == str(sample_notification.id)
        assert result["status"] == sample_notification.status.value
        assert result["channel"] == sample_notification.channel.value
    
    @patch('httpx.AsyncClient.post')
    def test_get_notification_status_not_found(self, mock_post, client: TestClient):
        """Test getting status for non-existent notification"""
        # Mock Identity Service validation
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_post.return_value = mock_response
        
        import uuid
        fake_id = uuid.uuid4()
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get(f"/api/v1/notifications/{fake_id}/status",
                             headers=headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    @patch('httpx.AsyncClient.post')
    def test_cancel_notification_success(self, mock_post, client: TestClient, sample_notification):
        """Test canceling a pending notification"""
        # Mock Identity Service validation
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_post.return_value = mock_response
        
        # Mock queue manager
        with patch('services.queue_manager.QueueManager') as mock_queue:
            mock_instance = AsyncMock()
            mock_instance.cancel_notification.return_value = True
            mock_queue.return_value = mock_instance
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            response = client.delete(f"/api/v1/notifications/{sample_notification.id}",
                                    headers=headers)
            
            assert response.status_code == 200
            result = response.json()
            assert "message" in result
            assert "cancelled" in result["message"].lower()
    
    @patch('httpx.AsyncClient.post')
    def test_retry_failed_notification_success(self, mock_post, client: TestClient, sample_notification):
        """Test retrying a failed notification"""
        # Mock Identity Service validation
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_post.return_value = mock_response
        
        # Update notification to failed status
        sample_notification.status = "failed"
        sample_notification.error_message = "SMTP server unavailable"
        
        # Mock Celery task
        with patch('tasks.notification_tasks.send_notification') as mock_task:
            mock_result = MagicMock()
            mock_result.id = "retry-task-123"
            mock_task.apply_async.return_value = mock_result
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            response = client.post(f"/api/v1/notifications/{sample_notification.id}/retry",
                                  headers=headers)
            
            assert response.status_code == 200
            result = response.json()
            assert "task_id" in result
            assert "status" in result
            assert result["status"] == "queued"
            assert result["task_id"] == "retry-task-123"


@pytest.mark.integration
class TestTemplateEndpoints:
    """Integration tests for template management endpoints"""
    
    @patch('httpx.AsyncClient.post')
    def test_create_template_success(self, mock_post, client: TestClient):
        """Test creating notification template"""
        # Mock admin user validation
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_admin_token_validation()["json"]
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer admin.jwt.token"}
        template_data = SampleAPIData.get_template_create_request()
        
        response = client.post("/api/v1/templates",
                              json=template_data,
                              headers=headers)
        
        assert response.status_code == 201
        result = response.json()
        assert "template_id" in result
        assert "name" in result
        assert result["name"] == template_data["name"]
        assert result["channel"] == template_data["channel"]
    
    @patch('httpx.AsyncClient.post')
    def test_create_template_insufficient_permissions(self, mock_post, client: TestClient):
        """Test creating template with insufficient permissions"""
        # Mock regular user validation
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer user.jwt.token"}
        template_data = SampleAPIData.get_template_create_request()
        
        response = client.post("/api/v1/templates",
                              json=template_data,
                              headers=headers)
        
        assert response.status_code == 403
        assert "insufficient permissions" in response.json()["detail"].lower()
    
    @patch('httpx.AsyncClient.post')
    def test_get_templates_success(self, mock_post, client: TestClient):
        """Test getting templates list"""
        # Mock user validation
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        response = client.get("/api/v1/templates", headers=headers)
        
        assert response.status_code == 200
        result = response.json()
        assert "templates" in result
        assert isinstance(result["templates"], list)
        assert "total" in result
        assert "page" in result


@pytest.mark.integration 
class TestQueueEndpoints:
    """Integration tests for queue management endpoints"""
    
    @patch('httpx.AsyncClient.post')
    def test_get_queue_status_success(self, mock_post, client: TestClient):
        """Test getting queue status"""
        # Mock admin user validation
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_admin_token_validation()["json"]
        mock_post.return_value = mock_response
        
        # Mock queue manager
        with patch('services.queue_manager.QueueManager') as mock_queue:
            mock_instance = AsyncMock()
            mock_instance.get_queue_status.return_value = SampleAPIData.get_queue_status_response()
            mock_queue.return_value = mock_instance
            
            headers = {"Authorization": "Bearer admin.jwt.token"}
            response = client.get("/api/v1/queue/status", headers=headers)
            
            assert response.status_code == 200
            result = response.json()
            assert "total_pending" in result
            assert "queues" in result
            assert "workers" in result
    
    @patch('httpx.AsyncClient.post')
    def test_get_queue_status_insufficient_permissions(self, mock_post, client: TestClient):
        """Test getting queue status with insufficient permissions"""
        # Mock regular user validation
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_post.return_value = mock_response
        
        headers = {"Authorization": "Bearer user.jwt.token"}
        response = client.get("/api/v1/queue/status", headers=headers)
        
        assert response.status_code == 403
        assert "insufficient permissions" in response.json()["detail"].lower()


@pytest.mark.integration
class TestErrorHandling:
    """Integration tests for error handling scenarios"""
    
    @patch('httpx.AsyncClient.post')
    def test_identity_service_timeout(self, mock_post, client: TestClient):
        """Test handling Identity Service timeout"""
        # Mock timeout exception
        import httpx
        mock_post.side_effect = httpx.TimeoutException("Request timeout")
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        notification_data = {
            "type": "email",
            "to": "test@example.com",
            "message": "Test message"
        }
        
        response = client.post("/api/v1/notifications",
                              json=notification_data,
                              headers=headers)
        
        assert response.status_code == 503
        assert "service temporarily unavailable" in response.json()["detail"].lower()
    
    @patch('httpx.AsyncClient.post')
    def test_identity_service_connection_error(self, mock_post, client: TestClient):
        """Test handling Identity Service connection error"""
        # Mock connection error
        import httpx
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        notification_data = {
            "type": "email",
            "to": "test@example.com",
            "message": "Test message"
        }
        
        response = client.post("/api/v1/notifications",
                              json=notification_data,
                              headers=headers)
        
        assert response.status_code == 503
        assert "service temporarily unavailable" in response.json()["detail"].lower()
    
    @patch('httpx.AsyncClient.post')
    def test_celery_task_failure(self, mock_post, client: TestClient):
        """Test handling Celery task submission failure"""
        # Mock Identity Service validation
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_post.return_value = mock_response
        
        # Mock Celery task failure
        with patch('tasks.notification_tasks.send_notification') as mock_task:
            mock_task.apply_async.side_effect = Exception("Celery connection failed")
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            notification_data = {
                "type": "email",
                "to": "test@example.com",
                "message": "Test message"
            }
            
            response = client.post("/api/v1/notifications",
                                  json=notification_data,
                                  headers=headers)
            
            assert response.status_code == 500
            assert "internal server error" in response.json()["detail"].lower()
    
    def test_invalid_json_request(self, client: TestClient):
        """Test handling invalid JSON in request"""
        headers = {
            "Authorization": "Bearer valid.jwt.token",
            "Content-Type": "application/json"
        }
        
        # Send invalid JSON
        response = client.post("/api/v1/notifications",
                              data="invalid json content",
                              headers=headers)
        
        assert response.status_code == 422
    
    def test_request_too_large(self, client: TestClient):
        """Test handling requests that are too large"""
        headers = {
            "Authorization": "Bearer valid.jwt.token",
            "Content-Type": "application/json"
        }
        
        # Create a very large request
        large_data = {
            "type": "email",
            "to": "test@example.com",
            "message": "x" * 100000,  # Very large message
            "data": {"large_field": "y" * 100000}
        }
        
        response = client.post("/api/v1/notifications",
                              json=large_data,
                              headers=headers)
        
        # Should either reject as too large or handle gracefully
        assert response.status_code in [413, 422, 400]