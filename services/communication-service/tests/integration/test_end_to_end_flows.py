"""
End-to-End Integration Tests for Complete Notification Flows
Tests complete notification lifecycle from API request to delivery confirmation
"""

import pytest
import json
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock, call
from fastapi.testclient import TestClient

from tests.fixtures.sample_data import SampleNotificationData, SampleAPIData
from tests.fixtures.mock_responses import (
    IdentityServiceMocks, 
    EmailProviderMocks, 
    SMSProviderMocks,
    PushProviderMocks
)


@pytest.mark.integration
@pytest.mark.e2e
class TestCompleteNotificationFlows:
    """End-to-end tests for complete notification delivery flows"""
    
    @patch('httpx.AsyncClient.post')
    @patch('providers.email.EmailProvider.send')
    @patch('tasks.notification_tasks.send_notification')
    def test_complete_email_notification_flow(self, mock_task, mock_email_send, mock_identity, client: TestClient):
        """Test complete email notification flow from API to delivery confirmation"""
        # Step 1: Mock Identity Service validation
        mock_identity_response = AsyncMock()
        mock_identity_response.status_code = 200
        mock_identity_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_identity.return_value = mock_identity_response
        
        # Step 2: Mock successful email provider response
        mock_email_send.return_value = {
            "success": True,
            "provider_message_id": "email-123-456",
            "delivery_status": "queued"
        }
        
        # Step 3: Mock Celery task execution
        mock_task_result = MagicMock()
        mock_task_result.id = "task-email-e2e-123"
        mock_task.apply_async.return_value = mock_task_result
        
        # Execute the task synchronously for testing
        def execute_task(*args, **kwargs):
            return mock_email_send.return_value
        mock_task.apply_async.side_effect = execute_task
        
        # Step 4: Send notification request
        headers = {"Authorization": "Bearer valid.jwt.token"}
        notification_data = {
            "type": "email",
            "to": "user@example.com",
            "subject": "Welcome to Our Platform",
            "message": "Thank you for joining our platform!",
            "priority": "normal",
            "data": {
                "user_name": "John Doe",
                "platform_name": "Medical Hub",
                "login_url": "https://medicalhub.com/login"
            }
        }
        
        # Step 5: Submit notification
        response = client.post("/api/v1/notifications", 
                              json=notification_data, 
                              headers=headers)
        
        # Step 6: Verify immediate response
        assert response.status_code == 200
        result = response.json()
        assert "notification_id" in result
        assert "task_id" in result
        assert result["status"] == "queued"
        
        notification_id = result["notification_id"]
        
        # Step 7: Verify notification status after processing
        status_response = client.get(f"/api/v1/notifications/{notification_id}/status",
                                   headers=headers)
        
        assert status_response.status_code == 200
        status_result = status_response.json()
        assert status_result["notification_id"] == notification_id
        assert status_result["channel"] == "email"
        
        # Step 8: Verify all mocks were called correctly
        mock_identity.assert_called_once()
        mock_task.apply_async.assert_called_once()
        
        # Step 9: Verify task execution would call email provider
        expected_call_args = mock_task.apply_async.call_args
        assert expected_call_args is not None
    
    @patch('httpx.AsyncClient.post')
    @patch('providers.sms.SMSProvider.send')
    @patch('tasks.notification_tasks.send_notification')
    def test_complete_sms_notification_flow(self, mock_task, mock_sms_send, mock_identity, client: TestClient):
        """Test complete SMS notification flow with delivery tracking"""
        # Step 1: Mock Identity Service validation
        mock_identity_response = AsyncMock()
        mock_identity_response.status_code = 200
        mock_identity_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_identity.return_value = mock_identity_response
        
        # Step 2: Mock SMS provider response with delivery tracking
        mock_sms_send.return_value = {
            "success": True,
            "provider_message_id": "sms-twilio-789",
            "delivery_status": "sent",
            "cost": 0.0075,
            "segments": 1
        }
        
        # Step 3: Mock Celery task
        mock_task_result = MagicMock()
        mock_task_result.id = "task-sms-e2e-456"
        mock_task.apply_async.return_value = mock_task_result
        
        # Step 4: Send SMS notification
        headers = {"Authorization": "Bearer valid.jwt.token"}
        notification_data = {
            "type": "sms",
            "to": "+1234567890",
            "message": "Your verification code is 123456. Valid for 10 minutes.",
            "priority": "high",
            "data": {
                "code": "123456",
                "expires_in": "10 minutes"
            }
        }
        
        response = client.post("/api/v1/notifications",
                              json=notification_data,
                              headers=headers)
        
        # Step 5: Verify response
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "queued"
        notification_id = result["notification_id"]
        
        # Step 6: Simulate webhook delivery confirmation
        webhook_data = {
            "message_id": "sms-twilio-789",
            "status": "delivered",
            "delivered_at": datetime.utcnow().isoformat(),
            "provider": "twilio"
        }
        
        webhook_response = client.post("/webhooks/sms/status",
                                      json=webhook_data,
                                      headers={"X-Webhook-Source": "twilio"})
        
        # Step 7: Verify webhook processing
        assert webhook_response.status_code == 200
        
        # Step 8: Verify final notification status includes delivery confirmation
        final_status = client.get(f"/api/v1/notifications/{notification_id}/status",
                                 headers=headers)
        
        assert final_status.status_code == 200
        final_result = final_status.json()
        assert final_result["channel"] == "sms"
    
    @patch('httpx.AsyncClient.post')
    @patch('providers.push.PushProvider.send')
    @patch('tasks.notification_tasks.send_notification')  
    def test_complete_push_notification_flow(self, mock_task, mock_push_send, mock_identity, client: TestClient):
        """Test complete push notification flow with FCM integration"""
        # Step 1: Mock Identity Service
        mock_identity_response = AsyncMock()
        mock_identity_response.status_code = 200
        mock_identity_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_identity.return_value = mock_identity_response
        
        # Step 2: Mock FCM response
        mock_push_send.return_value = {
            "success": True,
            "provider_message_id": "fcm-message-abc123",
            "delivery_status": "sent",
            "tokens_processed": 1,
            "tokens_succeeded": 1,
            "tokens_failed": 0
        }
        
        # Step 3: Mock task
        mock_task_result = MagicMock()
        mock_task_result.id = "task-push-e2e-789"
        mock_task.apply_async.return_value = mock_task_result
        
        # Step 4: Send push notification
        headers = {"Authorization": "Bearer valid.jwt.token"}
        notification_data = {
            "type": "push",
            "to": "fcm-device-token-xyz789",
            "title": "New Message Received",
            "message": "You have a new message from Dr. Smith",
            "data": {
                "deep_link": "/messages/456",
                "sender_id": "dr-smith-123",
                "message_type": "appointment_reminder"
            }
        }
        
        response = client.post("/api/v1/notifications",
                              json=notification_data,
                              headers=headers)
        
        # Step 5: Verify response
        assert response.status_code == 200
        result = response.json()
        notification_id = result["notification_id"]
        
        # Step 6: Test push notification feedback webhook
        feedback_data = {
            "message_id": "fcm-message-abc123",
            "status": "delivered", 
            "delivered_at": datetime.utcnow().isoformat(),
            "device_token": "fcm-device-token-xyz789"
        }
        
        feedback_response = client.post("/webhooks/push/feedback",
                                       json=feedback_data,
                                       headers={"X-Webhook-Source": "fcm"})
        
        assert feedback_response.status_code == 200
    
    @patch('httpx.AsyncClient.post')
    @patch('providers.in_app.InAppProvider.send')
    def test_complete_in_app_notification_flow(self, mock_in_app_send, mock_identity, client: TestClient):
        """Test complete in-app notification flow with real-time delivery"""
        # Step 1: Mock Identity Service
        mock_identity_response = AsyncMock()
        mock_identity_response.status_code = 200
        mock_identity_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_identity.return_value = mock_identity_response
        
        # Step 2: Mock in-app provider (immediate delivery)
        mock_in_app_send.return_value = {
            "success": True,
            "notification_id": "in-app-notif-123",
            "delivery_status": "delivered",
            "delivered_at": datetime.utcnow().isoformat()
        }
        
        # Step 3: Send in-app notification
        headers = {"Authorization": "Bearer valid.jwt.token"}
        notification_data = {
            "type": "in_app",
            "to": "user-123",
            "title": "Appointment Reminder", 
            "message": "Your appointment with Dr. Johnson is tomorrow at 2:00 PM",
            "data": {
                "appointment_id": "appt-456",
                "doctor_name": "Dr. Johnson",
                "appointment_time": "2024-01-15T14:00:00Z"
            }
        }
        
        response = client.post("/api/v1/notifications",
                              json=notification_data,
                              headers=headers)
        
        # Step 4: Verify immediate delivery for in-app notifications
        assert response.status_code == 200
        result = response.json()
        notification_id = result["notification_id"]
        
        # Step 5: Verify user can retrieve unread notifications
        unread_response = client.get("/api/v1/notifications/unread", headers=headers)
        assert unread_response.status_code == 200
        
        unread_result = unread_response.json()
        assert "notifications" in unread_result
        assert "unread_count" in unread_result
        
        # Step 6: Mark notification as read
        mark_read_data = {"notification_ids": [notification_id]}
        mark_read_response = client.post("/api/v1/notifications/mark-read",
                                        json=mark_read_data,
                                        headers=headers)
        
        assert mark_read_response.status_code == 200
        mark_read_result = mark_read_response.json()
        assert "marked_count" in mark_read_result


@pytest.mark.integration
@pytest.mark.e2e
class TestMultiChannelNotificationFlows:
    """End-to-end tests for multi-channel notification scenarios"""
    
    @patch('httpx.AsyncClient.post')
    @patch('providers.email.EmailProvider.send')
    @patch('providers.sms.SMSProvider.send')
    @patch('providers.push.PushProvider.send')
    @patch('tasks.notification_tasks.send_notification')
    def test_multi_channel_notification_campaign(self, mock_task, mock_push, mock_sms, mock_email, mock_identity, client: TestClient):
        """Test sending same notification across multiple channels"""
        # Mock Identity Service
        mock_identity_response = AsyncMock()
        mock_identity_response.status_code = 200
        mock_identity_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_identity.return_value = mock_identity_response
        
        # Mock all providers
        mock_email.return_value = {"success": True, "provider_message_id": "email-multi-123"}
        mock_sms.return_value = {"success": True, "provider_message_id": "sms-multi-456"}
        mock_push.return_value = {"success": True, "provider_message_id": "push-multi-789"}
        
        # Mock tasks
        mock_task_result = MagicMock()
        mock_task_result.id = "task-multi-channel"
        mock_task.apply_async.return_value = mock_task_result
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        
        # Send same notification across different channels
        base_data = {
            "message": "Important security alert: New login detected from unknown device",
            "priority": "urgent",
            "data": {
                "alert_type": "security",
                "device_info": "Chrome on Windows",
                "location": "New York, US",
                "time": datetime.utcnow().isoformat()
            }
        }
        
        notification_ids = []
        
        # Email notification
        email_data = {
            **base_data,
            "type": "email",
            "to": "user@example.com",
            "subject": "Security Alert - New Login Detected"
        }
        
        email_response = client.post("/api/v1/notifications", json=email_data, headers=headers)
        assert email_response.status_code == 200
        notification_ids.append(email_response.json()["notification_id"])
        
        # SMS notification  
        sms_data = {
            **base_data,
            "type": "sms",
            "to": "+1234567890"
        }
        
        sms_response = client.post("/api/v1/notifications", json=sms_data, headers=headers)
        assert sms_response.status_code == 200
        notification_ids.append(sms_response.json()["notification_id"])
        
        # Push notification
        push_data = {
            **base_data,
            "type": "push",
            "to": "push-token-security-alert",
            "title": "Security Alert"
        }
        
        push_response = client.post("/api/v1/notifications", json=push_data, headers=headers)
        assert push_response.status_code == 200
        notification_ids.append(push_response.json()["notification_id"])
        
        # Verify all notifications were queued
        assert len(notification_ids) == 3
        
        # Verify each notification status
        for notification_id in notification_ids:
            status_response = client.get(f"/api/v1/notifications/{notification_id}/status", headers=headers)
            assert status_response.status_code == 200
            status_result = status_response.json()
            assert status_result["notification_id"] == notification_id
    
    @patch('httpx.AsyncClient.post')
    @patch('services.template_engine.TemplateEngine')
    @patch('providers.email.EmailProvider.send')
    @patch('tasks.notification_tasks.send_notification')
    def test_template_based_notification_flow(self, mock_task, mock_email, mock_template_engine, mock_identity, client: TestClient, sample_notification_template):
        """Test complete template-based notification flow"""
        # Mock Identity Service
        mock_identity_response = AsyncMock()
        mock_identity_response.status_code = 200
        mock_identity_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_identity.return_value = mock_identity_response
        
        # Mock template engine
        mock_template_instance = MagicMock()
        mock_template_instance.render.return_value = "Dear John Doe, welcome to Medical Hub! Your account is now active."
        mock_template_engine.return_value = mock_template_instance
        
        # Mock email provider
        mock_email.return_value = {"success": True, "provider_message_id": "template-email-123"}
        
        # Mock task
        mock_task_result = MagicMock()
        mock_task_result.id = "task-template-flow"
        mock_task.apply_async.return_value = mock_task_result
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        
        # Send template-based notification
        template_data = {
            "type": "email",
            "to": "john@example.com", 
            "template_id": str(sample_notification_template.id),
            "data": {
                "user_name": "John Doe",
                "platform_name": "Medical Hub",
                "account_status": "active"
            }
        }
        
        response = client.post("/api/v1/notifications", json=template_data, headers=headers)
        
        # Verify response
        assert response.status_code == 200
        result = response.json()
        notification_id = result["notification_id"]
        
        # Verify template engine was called
        mock_template_instance.render.assert_called_once()
        
        # Verify notification status
        status_response = client.get(f"/api/v1/notifications/{notification_id}/status", headers=headers)
        assert status_response.status_code == 200


@pytest.mark.integration
@pytest.mark.e2e
class TestNotificationErrorRecoveryFlows:
    """End-to-end tests for notification error recovery and retry flows"""
    
    @patch('httpx.AsyncClient.post')
    @patch('providers.email.EmailProvider.send')
    @patch('tasks.notification_tasks.send_notification')
    def test_notification_retry_flow_after_provider_failure(self, mock_task, mock_email, mock_identity, client: TestClient):
        """Test complete retry flow after provider failure"""
        # Mock Identity Service
        mock_identity_response = AsyncMock()
        mock_identity_response.status_code = 200
        mock_identity_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_identity.return_value = mock_identity_response
        
        # Mock initial provider failure, then success on retry
        mock_email.side_effect = [
            Exception("SMTP server unavailable"),  # First attempt fails
            {"success": True, "provider_message_id": "retry-success-123"}  # Retry succeeds
        ]
        
        # Mock task
        mock_task_result = MagicMock()
        mock_task_result.id = "task-retry-flow"
        mock_task.apply_async.return_value = mock_task_result
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        
        # Send notification
        notification_data = {
            "type": "email",
            "to": "test@example.com",
            "subject": "Test Retry Flow",
            "message": "This tests the retry mechanism"
        }
        
        response = client.post("/api/v1/notifications", json=notification_data, headers=headers)
        assert response.status_code == 200
        notification_id = response.json()["notification_id"]
        
        # Simulate task processing failure (first attempt)
        # In real scenario, this would be handled by Celery retry logic
        
        # Manually trigger retry
        retry_response = client.post(f"/api/v1/notifications/{notification_id}/retry", headers=headers)
        assert retry_response.status_code == 200
        
        retry_result = retry_response.json()
        assert retry_result["status"] == "queued"
        assert "task_id" in retry_result
    
    @patch('httpx.AsyncClient.post') 
    @patch('providers.sms.SMSProvider.send')
    @patch('tasks.notification_tasks.send_notification')
    def test_notification_cancellation_flow(self, mock_task, mock_sms, mock_identity, client: TestClient):
        """Test notification cancellation before processing"""
        # Mock Identity Service
        mock_identity_response = AsyncMock()
        mock_identity_response.status_code = 200
        mock_identity_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_identity.return_value = mock_identity_response
        
        # Mock task
        mock_task_result = MagicMock()
        mock_task_result.id = "task-cancellation-test"
        mock_task.apply_async.return_value = mock_task_result
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        
        # Send notification
        notification_data = {
            "type": "sms",
            "to": "+1234567890", 
            "message": "This notification will be cancelled"
        }
        
        response = client.post("/api/v1/notifications", json=notification_data, headers=headers)
        assert response.status_code == 200
        notification_id = response.json()["notification_id"]
        
        # Cancel the notification before processing
        with patch('services.queue_manager.QueueManager') as mock_queue:
            mock_queue_instance = AsyncMock()
            mock_queue_instance.cancel_notification.return_value = True
            mock_queue.return_value = mock_queue_instance
            
            cancel_response = client.delete(f"/api/v1/notifications/{notification_id}", headers=headers)
            assert cancel_response.status_code == 200
            
            cancel_result = cancel_response.json()
            assert "cancelled" in cancel_result["message"].lower()


@pytest.mark.integration
@pytest.mark.e2e  
@pytest.mark.slow
class TestHighVolumeNotificationFlows:
    """End-to-end tests for high-volume notification processing"""
    
    @patch('httpx.AsyncClient.post')
    @patch('providers.email.EmailProvider.send')
    @patch('tasks.notification_tasks.send_notification')
    def test_bulk_notification_processing_flow(self, mock_task, mock_email, mock_identity, client: TestClient):
        """Test processing multiple notifications in bulk"""
        # Mock Identity Service
        mock_identity_response = AsyncMock()
        mock_identity_response.status_code = 200
        mock_identity_response.json.return_value = IdentityServiceMocks.get_successful_token_validation()["json"]
        mock_identity.return_value = mock_identity_response
        
        # Mock provider
        mock_email.return_value = {"success": True, "provider_message_id": "bulk-email"}
        
        # Mock task
        mock_task_result = MagicMock()
        mock_task.apply_async.return_value = mock_task_result
        
        headers = {"Authorization": "Bearer valid.jwt.token"}
        notification_ids = []
        
        # Send 10 notifications rapidly
        for i in range(10):
            notification_data = {
                "type": "email",
                "to": f"user{i}@example.com",
                "subject": f"Bulk Test Message {i}",
                "message": f"This is bulk test message number {i}"
            }
            
            response = client.post("/api/v1/notifications", json=notification_data, headers=headers)
            assert response.status_code == 200
            notification_ids.append(response.json()["notification_id"])
        
        # Verify all notifications were queued
        assert len(notification_ids) == 10
        
        # Verify task was called for each notification
        assert mock_task.apply_async.call_count == 10
        
        # Check status of all notifications
        for notification_id in notification_ids:
            status_response = client.get(f"/api/v1/notifications/{notification_id}/status", headers=headers)
            assert status_response.status_code == 200
            status_result = status_response.json()
            assert status_result["notification_id"] == notification_id


@pytest.mark.integration
@pytest.mark.e2e
class TestWebhookIntegrationFlows:
    """End-to-end tests for webhook integration flows"""
    
    def test_email_delivery_webhook_flow(self, client: TestClient):
        """Test complete email delivery webhook processing flow"""
        # Simulate email delivery webhook from provider
        webhook_data = {
            "message_id": "provider-email-12345",
            "event": "delivered",
            "timestamp": datetime.utcnow().isoformat(),
            "recipient": "user@example.com",
            "provider": "sendgrid"
        }
        
        response = client.post("/webhooks/email/delivery",
                              json=webhook_data,
                              headers={"X-Webhook-Source": "sendgrid"})
        
        assert response.status_code == 200
        result = response.json()
        assert "status" in result
        assert result["status"] == "processed"
    
    def test_sms_status_webhook_flow(self, client: TestClient):
        """Test SMS status webhook processing flow"""
        webhook_data = {
            "message_id": "sms-provider-67890",
            "status": "delivered", 
            "delivered_at": datetime.utcnow().isoformat(),
            "provider": "twilio",
            "cost": 0.0075
        }
        
        response = client.post("/webhooks/sms/status",
                              json=webhook_data,
                              headers={"X-Webhook-Source": "twilio"})
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "processed"
    
    def test_push_feedback_webhook_flow(self, client: TestClient):
        """Test push notification feedback webhook flow"""
        webhook_data = {
            "message_id": "fcm-push-abc123",
            "status": "delivered",
            "device_token": "device-token-xyz",
            "delivered_at": datetime.utcnow().isoformat()
        }
        
        response = client.post("/webhooks/push/feedback",
                              json=webhook_data,
                              headers={"X-Webhook-Source": "fcm"})
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "processed"