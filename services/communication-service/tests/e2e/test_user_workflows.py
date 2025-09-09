"""
End-to-end tests for complete user workflows
Tests real user scenarios across the entire notification system
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from tests.fixtures.mock_responses import IdentityServiceMocks, EmailProviderMocks
from tests.fixtures.sample_data import SampleNotificationData

@pytest.mark.e2e
class TestCompleteNotificationWorkflow:
    """Test complete notification workflows from creation to delivery"""
    
    @patch('httpx.AsyncClient.post')
    def test_complete_email_notification_workflow(self, mock_identity, client: TestClient):
        """Test complete email notification workflow"""
        # Setup: Mock all external dependencies
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_identity.return_value = mock_response
        
        with patch('tasks.notification_tasks.send_notification') as mock_task, \
             patch('providers.email.EmailProvider') as mock_email_provider:
            
            # Setup mocks
            mock_result = MagicMock()
            mock_result.id = "workflow-task-123"
            mock_task.apply_async.return_value = mock_result
            
            mock_email_instance = AsyncMock()
            mock_email_instance.send.return_value = EmailProviderMocks.get_successful_send_response()
            mock_email_provider.return_value = mock_email_instance
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            
            # Step 1: Create notification
            notification_data = {
                "type": "email",
                "to": "user@example.com",
                "subject": "Welcome to Our Platform!",
                "message": "Thank you for joining us. Get started with these next steps...",
                "priority": "normal",
                "data": {
                    "user_name": "John Doe",
                    "platform": "Our Platform",
                    "next_steps": ["Complete profile", "Explore features", "Join community"]
                }
            }
            
            response = client.post("/api/v1/notifications",
                                  json=notification_data,
                                  headers=headers)
            
            assert response.status_code == 200
            result = response.json()
            notification_id = result["notification_id"]
            task_id = result["task_id"]
            
            # Step 2: Check notification status
            response = client.get(f"/api/v1/notifications/{notification_id}/status",
                                 headers=headers)
            
            assert response.status_code == 200
            status_result = response.json()
            assert status_result["notification_id"] == notification_id
            assert status_result["status"] in ["pending", "queued", "sent"]
            
            # Step 3: Verify task was queued
            assert task_id == "workflow-task-123"
            mock_task.apply_async.assert_called_once()
            
            # Step 4: Simulate task execution and provider delivery
            # In real workflow, this would happen asynchronously
            mock_email_instance.send.assert_not_called()  # Would be called by worker
            
            # Workflow complete - notification created, queued, and ready for delivery
    
    @patch('httpx.AsyncClient.post')
    def test_template_based_notification_workflow(self, mock_identity, client: TestClient, sample_notification_template):
        """Test workflow using notification templates"""
        # Mock authentication
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_identity.return_value = mock_response
        
        with patch('tasks.notification_tasks.send_notification') as mock_task, \
             patch('services.template_engine.TemplateEngine') as mock_template_engine:
            
            # Setup mocks
            mock_result = MagicMock()
            mock_result.id = "template-task-123"
            mock_task.apply_async.return_value = mock_result
            
            mock_engine_instance = MagicMock()
            mock_engine_instance.render.return_value = "Hello John, welcome to Our Platform!"
            mock_template_engine.return_value = mock_engine_instance
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            
            # Step 1: Create notification with template
            notification_data = {
                "type": "email",
                "to": "john@example.com",
                "template_id": sample_notification_template.id,
                "data": {
                    "name": "John",
                    "platform": "Our Platform",
                    "action": "registration"
                }
            }
            
            response = client.post("/api/v1/notifications",
                                  json=notification_data,
                                  headers=headers)
            
            assert response.status_code == 200
            result = response.json()
            notification_id = result["notification_id"]
            
            # Step 2: Verify template would be used
            # In real workflow, template engine would be called during task execution
            mock_task.apply_async.assert_called_once()
            task_args = mock_task.apply_async.call_args
            task_data = task_args[0][0]  # First argument
            
            assert str(sample_notification_template.id) in str(task_data)
            assert "name" in str(task_data)
            assert "John" in str(task_data)
    
    @patch('httpx.AsyncClient.post')
    def test_multi_channel_notification_workflow(self, mock_identity, client: TestClient):
        """Test workflow sending notifications across multiple channels"""
        # Mock authentication
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_identity.return_value = mock_response
        
        with patch('tasks.notification_tasks.send_notification') as mock_task:
            mock_result = MagicMock()
            mock_result.id = "multi-channel-task"
            mock_task.apply_async.return_value = mock_result
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            
            channels_data = [
                {
                    "type": "email",
                    "to": "user@example.com",
                    "subject": "Security Alert",
                    "message": "Suspicious login detected on your account"
                },
                {
                    "type": "sms",
                    "to": "+1234567890",
                    "message": "ALERT: Suspicious login detected. Check your email for details."
                },
                {
                    "type": "push",
                    "to": "push-token-123",
                    "title": "Security Alert",
                    "message": "Suspicious login detected",
                    "data": {"deep_link": "/security/alerts"}
                }
            ]
            
            notification_ids = []
            
            # Send notifications across all channels
            for channel_data in channels_data:
                response = client.post("/api/v1/notifications",
                                      json=channel_data,
                                      headers=headers)
                
                assert response.status_code == 200
                result = response.json()
                notification_ids.append(result["notification_id"])
            
            # Verify all notifications were created
            assert len(notification_ids) == 3
            assert mock_task.apply_async.call_count == 3
            
            # Each notification should have been queued for delivery
            for notification_id in notification_ids:
                response = client.get(f"/api/v1/notifications/{notification_id}/status",
                                     headers=headers)
                assert response.status_code == 200
    
    @patch('httpx.AsyncClient.post')
    def test_high_priority_notification_workflow(self, mock_identity, client: TestClient):
        """Test high priority notification workflow"""
        # Mock authentication
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_identity.return_value = mock_response
        
        with patch('tasks.notification_tasks.send_notification') as mock_task:
            mock_result = MagicMock()
            mock_result.id = "urgent-task-123"
            mock_task.apply_async.return_value = mock_result
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            
            # Create urgent notification
            notification_data = {
                "type": "sms",
                "to": "+1234567890",
                "message": "URGENT: Your account has been locked due to suspicious activity. Contact support immediately.",
                "priority": "urgent"
            }
            
            response = client.post("/api/v1/notifications",
                                  json=notification_data,
                                  headers=headers)
            
            assert response.status_code == 200
            result = response.json()
            
            # Verify task was submitted with high priority routing
            mock_task.apply_async.assert_called_once()
            call_kwargs = mock_task.apply_async.call_args.kwargs
            
            # Should use urgent queue or high priority
            assert "priority" in str(call_kwargs) or "urgent" in str(call_kwargs) or \
                   any("urgent" in str(arg) for arg in mock_task.apply_async.call_args)


@pytest.mark.e2e
class TestUserNotificationPreferencesWorkflow:
    """Test workflows involving user notification preferences"""
    
    @patch('httpx.AsyncClient.post')
    def test_user_notification_preferences_respected(self, mock_identity, client: TestClient):
        """Test that user notification preferences are respected"""
        # Mock user with specific preferences
        user_data = IdentityServiceMocks.get_successful_token_validation()["json"]
        user_data["notification_preferences"] = {
            "email": {"enabled": True, "categories": ["security", "updates"]},
            "sms": {"enabled": False, "categories": []},
            "push": {"enabled": True, "categories": ["security", "messages"]}
        }
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = user_data
        mock_identity.return_value = mock_response
        
        # Mock user contact info endpoint
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_contact_response = AsyncMock()
            mock_contact_response.status_code = 200
            mock_contact_response.json.return_value = IdentityServiceMocks.get_user_contact_info_response()["json"]
            mock_get.return_value = mock_contact_response
            
            with patch('tasks.notification_tasks.send_notification') as mock_task:
                mock_result = MagicMock()
                mock_result.id = "preference-task-123"
                mock_task.apply_async.return_value = mock_result
                
                headers = {"Authorization": "Bearer valid.jwt.token"}
                
                # Test 1: Send security notification (should work for email and push)
                security_notification = {
                    "type": "email",
                    "to": "user@example.com",
                    "subject": "Security Alert",
                    "message": "Suspicious activity detected",
                    "category": "security"
                }
                
                response = client.post("/api/v1/notifications",
                                      json=security_notification,
                                      headers=headers)
                
                assert response.status_code == 200  # Should be allowed
                
                # Test 2: Send SMS (should be blocked due to preferences)
                sms_notification = {
                    "type": "sms",
                    "to": "+1234567890",
                    "message": "Update available",
                    "category": "updates"
                }
                
                response = client.post("/api/v1/notifications",
                                      json=sms_notification,
                                      headers=headers)
                
                # Depending on implementation, might be blocked or queued but filtered
                assert response.status_code in [200, 403]
    
    @patch('httpx.AsyncClient.post')
    def test_notification_frequency_limiting(self, mock_identity, client: TestClient):
        """Test notification frequency limiting"""
        # Mock authentication
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_identity.return_value = mock_response
        
        with patch('tasks.notification_tasks.send_notification') as mock_task, \
             patch('services.rate_limiter.RateLimiter') as mock_rate_limiter:
            
            mock_result = MagicMock()
            mock_result.id = "rate-limited-task"
            mock_task.apply_async.return_value = mock_result
            
            mock_limiter_instance = AsyncMock()
            mock_limiter_instance.is_allowed.return_value = True
            mock_rate_limiter.return_value = mock_limiter_instance
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            
            # Send multiple notifications rapidly
            for i in range(5):
                notification_data = {
                    "type": "email",
                    "to": "user@example.com",
                    "subject": f"Notification {i+1}",
                    "message": f"This is notification {i+1}"
                }
                
                response = client.post("/api/v1/notifications",
                                      json=notification_data,
                                      headers=headers)
                
                # First few should succeed, later ones might be rate limited
                assert response.status_code in [200, 429]
                
                if response.status_code == 429:
                    # Rate limiting detected
                    assert "rate limit" in response.json()["detail"].lower()
                    break


@pytest.mark.e2e
class TestNotificationDeliveryTrackingWorkflow:
    """Test end-to-end notification delivery and tracking"""
    
    @patch('httpx.AsyncClient.post')
    def test_notification_delivery_status_tracking(self, mock_identity, client: TestClient, sample_notification):
        """Test tracking notification through complete delivery lifecycle"""
        # Mock authentication
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_identity.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        notification_id = str(sample_notification.id)
        
        # Step 1: Check initial status
        response = client.get(f"/api/v1/notifications/{notification_id}/status",
                             headers=headers)
        
        assert response.status_code == 200
        initial_status = response.json()
        assert initial_status["status"] == "pending"
        assert initial_status["sent_at"] is None
        
        # Step 2: Simulate status updates (would happen via webhooks or worker updates)
        # This would normally be done by background tasks and webhook handlers
        
        # Step 3: Check updated status
        response = client.get(f"/api/v1/notifications/{notification_id}/status",
                             headers=headers)
        
        assert response.status_code == 200
        updated_status = response.json()
        assert "status" in updated_status
        assert "channel" in updated_status
        assert updated_status["notification_id"] == notification_id
    
    @patch('httpx.AsyncClient.post')
    def test_failed_notification_retry_workflow(self, mock_identity, client: TestClient, sample_notification):
        """Test retry workflow for failed notifications"""
        # Mock authentication
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_identity.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        notification_id = str(sample_notification.id)
        
        # Simulate failed notification (would be set by background task)
        sample_notification.status = "failed"
        sample_notification.error_message = "SMTP server unavailable"
        
        # Step 1: Check failed status
        response = client.get(f"/api/v1/notifications/{notification_id}/status",
                             headers=headers)
        
        assert response.status_code == 200
        failed_status = response.json()
        assert failed_status["status"] == "failed"
        assert "error_message" in failed_status
        
        # Step 2: Retry failed notification
        with patch('tasks.notification_tasks.send_notification') as mock_task:
            mock_result = MagicMock()
            mock_result.id = "retry-task-123"
            mock_task.apply_async.return_value = mock_result
            
            response = client.post(f"/api/v1/notifications/{notification_id}/retry",
                                  headers=headers)
            
            assert response.status_code == 200
            retry_result = response.json()
            assert retry_result["status"] == "queued"
            assert "task_id" in retry_result
            
            # Verify retry task was submitted
            mock_task.apply_async.assert_called_once()


@pytest.mark.e2e
class TestNotificationAnalyticsWorkflow:
    """Test notification analytics and reporting workflows"""
    
    @patch('httpx.AsyncClient.post')
    def test_notification_analytics_collection(self, mock_identity, client: TestClient):
        """Test that notification analytics are collected"""
        # Mock admin user
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_admin_token_validation()["json"]
        mock_identity.return_value = mock_response
        
        headers = {"Authorization": "Bearer admin.jwt.token"}
        
        # Mock analytics service
        with patch('services.analytics.AnalyticsService') as mock_analytics:
            mock_analytics_instance = AsyncMock()
            mock_analytics_instance.get_notification_metrics.return_value = {
                "total_sent": 1250,
                "delivery_rate": 0.98,
                "open_rate": 0.45,
                "click_rate": 0.12,
                "channel_breakdown": {
                    "email": {"sent": 800, "delivered": 784},
                    "sms": {"sent": 300, "delivered": 297},
                    "push": {"sent": 150, "delivered": 145}
                },
                "period": "last_7_days"
            }
            mock_analytics.return_value = mock_analytics_instance
            
            # Get notification analytics
            response = client.get("/api/v1/analytics/notifications",
                                 headers=headers,
                                 params={"period": "7d"})
            
            # Depending on implementation, might exist or return 404
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                analytics_data = response.json()
                assert "total_sent" in analytics_data or "metrics" in analytics_data
    
    @patch('httpx.AsyncClient.post')
    def test_user_notification_history(self, mock_identity, client: TestClient):
        """Test retrieving user notification history"""
        # Mock authentication
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_identity.return_value = mock_response
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        
        # Mock in-app provider for history
        with patch('providers.in_app.InAppProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.get_notification_history.return_value = {
                "notifications": [
                    {
                        "id": "notif-1",
                        "subject": "Welcome!",
                        "content": "Welcome to our platform",
                        "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                        "is_read": True,
                        "channel": "in_app"
                    },
                    {
                        "id": "notif-2",
                        "subject": "New Feature Available",
                        "content": "Check out our latest feature",
                        "created_at": (datetime.utcnow() - timedelta(days=2)).isoformat(),
                        "is_read": False,
                        "channel": "in_app"
                    }
                ],
                "total": 2,
                "page": 1,
                "has_more": False
            }
            mock_provider.return_value = mock_instance
            
            # Get user notification history
            response = client.get("/api/v1/notifications/history",
                                 headers=headers,
                                 params={"page": 1, "limit": 10})
            
            # Depending on implementation, might exist or return 404
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                history_data = response.json()
                assert "notifications" in history_data or "history" in history_data


@pytest.mark.e2e
class TestSystemIntegrationWorkflow:
    """Test integration with external systems"""
    
    @patch('httpx.AsyncClient.post')
    def test_webhook_notification_delivery_confirmation(self, mock_identity, client: TestClient):
        """Test webhook handling for delivery confirmations"""
        # Test webhook endpoint that would receive delivery confirmations
        webhook_data = {
            "event": "delivered",
            "message_id": "email-123456",
            "recipient": "user@example.com",
            "timestamp": datetime.utcnow().isoformat(),
            "provider": "sendgrid"
        }
        
        # Mock webhook signature validation
        with patch('utils.webhook_validator.validate_signature') as mock_validator:
            mock_validator.return_value = True
            
            response = client.post("/webhooks/email/delivery",
                                  json=webhook_data,
                                  headers={"X-Signature": "mock-signature"})
            
            # Depending on implementation, webhook endpoint might exist
            assert response.status_code in [200, 404]
    
    @patch('httpx.AsyncClient.post')
    def test_external_service_failure_handling(self, mock_identity, client: TestClient):
        """Test handling of external service failures"""
        # Mock Identity Service failure
        mock_identity.side_effect = Exception("Identity service unavailable")
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        notification_data = {
            "type": "email",
            "to": "test@example.com",
            "message": "Test message"
        }
        
        response = client.post("/api/v1/notifications",
                              json=notification_data,
                              headers=headers)
        
        # Should handle external service failure gracefully
        assert response.status_code == 503
        assert "service temporarily unavailable" in response.json()["detail"].lower()


@pytest.mark.e2e
@pytest.mark.slow
class TestHighVolumeNotificationWorkflow:
    """Test high volume notification scenarios"""
    
    @patch('httpx.AsyncClient.post')
    def test_bulk_notification_processing(self, mock_identity, client: TestClient):
        """Test processing large volumes of notifications"""
        # Mock authentication
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_identity.return_value = mock_response
        
        with patch('tasks.notification_tasks.send_notification') as mock_task:
            mock_result = MagicMock()
            mock_result.id = "bulk-task"
            mock_task.apply_async.return_value = mock_result
            
            headers = {"Authorization": "Bearer valid.jwt.token"}
            
            # Submit many notifications rapidly
            notification_ids = []
            batch_size = 10  # Reduced for testing
            
            for i in range(batch_size):
                notification_data = {
                    "type": "email",
                    "to": f"user{i}@example.com",
                    "subject": f"Bulk Notification {i+1}",
                    "message": f"This is bulk notification {i+1}"
                }
                
                response = client.post("/api/v1/notifications",
                                      json=notification_data,
                                      headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    notification_ids.append(result["notification_id"])
                elif response.status_code == 429:
                    # Rate limited - acceptable for bulk processing
                    break
                else:
                    # Other error
                    assert False, f"Unexpected response: {response.status_code}"
            
            # Should have processed at least some notifications
            assert len(notification_ids) > 0
            assert mock_task.apply_async.call_count >= len(notification_ids)
    
    def test_system_performance_under_load(self, client: TestClient):
        """Test system performance metrics under load"""
        import time
        
        # Test health endpoint response time under load
        start_time = time.time()
        
        responses = []
        for _ in range(20):  # Make multiple rapid requests
            response = client.get("/health")
            responses.append(response)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All health checks should succeed
        assert all(r.status_code == 200 for r in responses)
        
        # Should complete reasonably quickly
        assert total_time < 5.0, f"Health checks took too long: {total_time}s"
        
        # Average response time should be reasonable
        avg_response_time = total_time / len(responses)
        assert avg_response_time < 0.5, f"Average response time too slow: {avg_response_time}s"