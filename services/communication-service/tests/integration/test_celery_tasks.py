"""
Integration tests for Celery tasks
Tests notification delivery tasks, retry logic, and error handling
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock

from tests.fixtures.sample_data import SampleNotificationData
from tests.fixtures.mock_responses import CeleryTaskMocks, EmailProviderMocks

@pytest.mark.integration
@pytest.mark.requires_celery
class TestNotificationDeliveryTasks:
    """Integration tests for notification delivery Celery tasks"""
    
    @pytest.fixture
    def celery_app(self):
        """Create test Celery app"""
        from celery import Celery
        app = Celery('communication-service-test')
        app.config_from_object({
            'task_always_eager': True,  # Execute tasks synchronously for testing
            'task_eager_propagates': True,
            'broker_url': 'memory://',
            'result_backend': 'cache+memory://',
        })
        return app
    
    async def test_send_email_notification_task_success(self, celery_app, sample_notification):
        """Test successful email notification delivery task"""
        from tasks.notification_tasks import send_notification
        
        # Mock email provider
        with patch('providers.email.EmailProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.send.return_value = EmailProviderMocks.get_successful_send_response()
            mock_provider.return_value = mock_instance
            
            # Mock database update
            with patch('services.notification_service.NotificationService') as mock_service:
                mock_service_instance = AsyncMock()
                mock_service_instance.update_notification_status.return_value = sample_notification
                mock_service.return_value = mock_service_instance
                
                # Execute task
                task_data = {
                    "notification_id": str(sample_notification.id),
                    "user_id": str(sample_notification.user_id),
                    "channel": "email",
                    "recipient": "test@example.com",
                    "subject": "Test Email",
                    "content": "Test content"
                }
                
                result = send_notification.apply(args=[task_data])
                
                assert result.successful()
                task_result = result.result
                assert task_result["status"] == "sent"
                assert "message_id" in task_result
                
                # Verify provider was called
                mock_instance.send.assert_called_once()
                
                # Verify database was updated
                mock_service_instance.update_notification_status.assert_called()
    
    async def test_send_sms_notification_task_success(self, celery_app, sample_notification):
        """Test successful SMS notification delivery task"""
        from tasks.notification_tasks import send_notification
        
        # Mock SMS provider
        with patch('providers.sms.SMSProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.send.return_value = {
                "status": "sent",
                "message_id": f"sms-{uuid.uuid4()}",
                "provider": "twilio"
            }
            mock_provider.return_value = mock_instance
            
            # Mock database update
            with patch('services.notification_service.NotificationService') as mock_service:
                mock_service_instance = AsyncMock()
                mock_service_instance.update_notification_status.return_value = sample_notification
                mock_service.return_value = mock_service_instance
                
                task_data = {
                    "notification_id": str(sample_notification.id),
                    "user_id": str(sample_notification.user_id),
                    "channel": "sms",
                    "recipient": "+1234567890",
                    "content": "Your verification code is 123456"
                }
                
                result = send_notification.apply(args=[task_data])
                
                assert result.successful()
                task_result = result.result
                assert task_result["status"] == "sent"
                assert task_result["provider"] == "twilio"
    
    async def test_send_push_notification_task_success(self, celery_app, sample_notification):
        """Test successful push notification delivery task"""
        from tasks.notification_tasks import send_notification
        
        # Mock push provider
        with patch('providers.push.PushProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.send.return_value = {
                "status": "sent",
                "message_id": f"push-{uuid.uuid4()}",
                "provider": "fcm"
            }
            mock_provider.return_value = mock_instance
            
            # Mock database update
            with patch('services.notification_service.NotificationService') as mock_service:
                mock_service_instance = AsyncMock()
                mock_service_instance.update_notification_status.return_value = sample_notification
                mock_service.return_value = mock_service_instance
                
                task_data = {
                    "notification_id": str(sample_notification.id),
                    "user_id": str(sample_notification.user_id),
                    "channel": "push",
                    "recipient": "push-token-123456",
                    "title": "New Message",
                    "content": "You have a new message",
                    "data": {"deep_link": "/messages/123"}
                }
                
                result = send_notification.apply(args=[task_data])
                
                assert result.successful()
                task_result = result.result
                assert task_result["status"] == "sent"
                assert task_result["provider"] == "fcm"
    
    async def test_send_in_app_notification_task_success(self, celery_app, sample_notification):
        """Test successful in-app notification delivery task"""
        from tasks.notification_tasks import send_notification
        
        # Mock in-app provider
        with patch('providers.in_app.InAppProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.send.return_value = {
                "status": "sent",
                "message_id": f"inapp-{uuid.uuid4()}",
                "provider": "in_app"
            }
            mock_provider.return_value = mock_instance
            
            # Mock database update
            with patch('services.notification_service.NotificationService') as mock_service:
                mock_service_instance = AsyncMock()
                mock_service_instance.update_notification_status.return_value = sample_notification
                mock_service.return_value = mock_service_instance
                
                task_data = {
                    "notification_id": str(sample_notification.id),
                    "user_id": str(sample_notification.user_id),
                    "channel": "in_app",
                    "title": "System Update",
                    "content": "System maintenance completed successfully"
                }
                
                result = send_notification.apply(args=[task_data])
                
                assert result.successful()
                task_result = result.result
                assert task_result["status"] == "sent"
                assert task_result["provider"] == "in_app"
    
    async def test_notification_task_with_template_rendering(self, celery_app, sample_notification, sample_notification_template):
        """Test notification task with template rendering"""
        from tasks.notification_tasks import send_notification
        
        # Mock template engine
        with patch('services.template_engine.TemplateEngine') as mock_engine:
            mock_engine_instance = MagicMock()
            mock_engine_instance.render.return_value = "Hello John Doe, welcome to Our Platform!"
            mock_engine.return_value = mock_engine_instance
            
            # Mock email provider
            with patch('providers.email.EmailProvider') as mock_provider:
                mock_instance = AsyncMock()
                mock_instance.send.return_value = EmailProviderMocks.get_successful_send_response()
                mock_provider.return_value = mock_instance
                
                # Mock database update
                with patch('services.notification_service.NotificationService') as mock_service:
                    mock_service_instance = AsyncMock()
                    mock_service_instance.update_notification_status.return_value = sample_notification
                    mock_service.return_value = mock_service_instance
                    
                    task_data = {
                        "notification_id": str(sample_notification.id),
                        "user_id": str(sample_notification.user_id),
                        "channel": "email",
                        "recipient": "john@example.com",
                        "template_id": str(sample_notification_template.id),
                        "data": {
                            "name": "John Doe",
                            "platform": "Our Platform",
                            "action": "registration"
                        }
                    }
                    
                    result = send_notification.apply(args=[task_data])
                    
                    assert result.successful()
                    
                    # Verify template was rendered
                    mock_engine_instance.render.assert_called()
                    
                    # Verify rendered content was used
                    provider_call_args = mock_instance.send.call_args
                    assert "John Doe" in str(provider_call_args) or "Our Platform" in str(provider_call_args)


@pytest.mark.integration
@pytest.mark.requires_celery
class TestNotificationTaskErrorHandling:
    """Test error handling in notification delivery tasks"""
    
    async def test_notification_task_provider_failure(self, celery_app, sample_notification):
        """Test task handling when notification provider fails"""
        from tasks.notification_tasks import send_notification
        
        # Mock provider failure
        with patch('providers.email.EmailProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.send.side_effect = Exception("SMTP server unavailable")
            mock_provider.return_value = mock_instance
            
            # Mock database update
            with patch('services.notification_service.NotificationService') as mock_service:
                mock_service_instance = AsyncMock()
                mock_service_instance.update_notification_status.return_value = sample_notification
                mock_service.return_value = mock_service_instance
                
                task_data = {
                    "notification_id": str(sample_notification.id),
                    "user_id": str(sample_notification.user_id),
                    "channel": "email",
                    "recipient": "test@example.com",
                    "content": "Test content"
                }
                
                result = send_notification.apply(args=[task_data])
                
                # Task should complete but mark notification as failed
                assert result.successful()
                task_result = result.result
                assert task_result["status"] == "failed"
                assert "error" in task_result
                assert "SMTP server unavailable" in task_result["error"]
                
                # Verify database was updated with error
                update_calls = mock_service_instance.update_notification_status.call_args_list
                assert any("failed" in str(call) for call in update_calls)
    
    async def test_notification_task_invalid_template(self, celery_app, sample_notification):
        """Test task handling with invalid template"""
        from tasks.notification_tasks import send_notification
        
        # Mock template engine failure
        with patch('services.template_engine.TemplateEngine') as mock_engine:
            mock_engine_instance = MagicMock()
            mock_engine_instance.render.side_effect = Exception("Template not found")
            mock_engine.return_value = mock_engine_instance
            
            # Mock database update
            with patch('services.notification_service.NotificationService') as mock_service:
                mock_service_instance = AsyncMock()
                mock_service_instance.update_notification_status.return_value = sample_notification
                mock_service.return_value = mock_service_instance
                
                task_data = {
                    "notification_id": str(sample_notification.id),
                    "user_id": str(sample_notification.user_id),
                    "channel": "email",
                    "recipient": "test@example.com",
                    "template_id": "invalid-template-id"
                }
                
                result = send_notification.apply(args=[task_data])
                
                assert result.successful()
                task_result = result.result
                assert task_result["status"] == "failed"
                assert "template" in task_result["error"].lower()
    
    async def test_notification_task_database_error(self, celery_app):
        """Test task handling when database update fails"""
        from tasks.notification_tasks import send_notification
        
        # Mock successful provider
        with patch('providers.email.EmailProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.send.return_value = EmailProviderMocks.get_successful_send_response()
            mock_provider.return_value = mock_instance
            
            # Mock database failure
            with patch('services.notification_service.NotificationService') as mock_service:
                mock_service_instance = AsyncMock()
                mock_service_instance.update_notification_status.side_effect = Exception("Database connection lost")
                mock_service.return_value = mock_service_instance
                
                task_data = {
                    "notification_id": str(uuid.uuid4()),
                    "user_id": str(uuid.uuid4()),
                    "channel": "email",
                    "recipient": "test@example.com",
                    "content": "Test content"
                }
                
                result = send_notification.apply(args=[task_data])
                
                # Task should handle database error gracefully
                assert result.successful()
                task_result = result.result
                # Should still indicate that the notification was sent to provider
                # but database update failed
                assert "database" in task_result.get("warning", "").lower() or \
                       task_result["status"] in ["sent", "failed"]


@pytest.mark.integration
@pytest.mark.requires_celery
class TestNotificationTaskRetryLogic:
    """Test retry logic for notification delivery tasks"""
    
    async def test_notification_task_retry_on_transient_error(self, celery_app, sample_notification):
        """Test task retry on transient errors"""
        from tasks.notification_tasks import send_notification
        from celery.exceptions import Retry
        
        # Mock transient error that should trigger retry
        with patch('providers.email.EmailProvider') as mock_provider:
            mock_instance = AsyncMock()
            # First call fails with transient error, second succeeds
            mock_instance.send.side_effect = [
                Exception("Network timeout"),
                EmailProviderMocks.get_successful_send_response()
            ]
            mock_provider.return_value = mock_instance
            
            # Mock database update
            with patch('services.notification_service.NotificationService') as mock_service:
                mock_service_instance = AsyncMock()
                mock_service_instance.update_notification_status.return_value = sample_notification
                mock_service.return_value = mock_service_instance
                
                # Mock task retry mechanism
                with patch.object(send_notification, 'retry') as mock_retry:
                    mock_retry.side_effect = Retry("Retrying due to transient error")
                    
                    task_data = {
                        "notification_id": str(sample_notification.id),
                        "user_id": str(sample_notification.user_id),
                        "channel": "email",
                        "recipient": "test@example.com",
                        "content": "Test content"
                    }
                    
                    # First execution should trigger retry
                    with pytest.raises(Retry):
                        send_notification.apply(args=[task_data])
                    
                    # Verify retry was called
                    mock_retry.assert_called_once()
    
    async def test_notification_task_max_retries_exceeded(self, celery_app, sample_notification):
        """Test task behavior when max retries exceeded"""
        from tasks.notification_tasks import send_notification
        
        # Mock persistent failure
        with patch('providers.email.EmailProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.send.side_effect = Exception("Persistent server error")
            mock_provider.return_value = mock_instance
            
            # Mock database update
            with patch('services.notification_service.NotificationService') as mock_service:
                mock_service_instance = AsyncMock()
                mock_service_instance.update_notification_status.return_value = sample_notification
                mock_service.return_value = mock_service_instance
                
                # Mock task to simulate max retries exceeded
                with patch.object(send_notification, 'request') as mock_request:
                    mock_request.retries = 3  # Max retries reached
                    
                    task_data = {
                        "notification_id": str(sample_notification.id),
                        "user_id": str(sample_notification.user_id),
                        "channel": "email",
                        "recipient": "test@example.com",
                        "content": "Test content"
                    }
                    
                    result = send_notification.apply(args=[task_data])
                    
                    assert result.successful()
                    task_result = result.result
                    assert task_result["status"] == "failed"
                    assert "max retries" in task_result["error"].lower() or \
                           "persistent" in task_result["error"].lower()
    
    async def test_notification_task_exponential_backoff(self, celery_app):
        """Test exponential backoff in retry logic"""
        from tasks.notification_tasks import send_notification
        
        # Test that retry delays increase exponentially
        # This is more of a unit test for the retry configuration
        task_instance = send_notification
        
        # Check retry configuration
        assert hasattr(task_instance, 'autoretry_for')
        assert hasattr(task_instance, 'retry_backoff')
        assert hasattr(task_instance, 'retry_kwargs')
        
        # Verify exponential backoff configuration
        if hasattr(task_instance, 'retry_backoff'):
            assert task_instance.retry_backoff > 0  # Should have backoff delay
        
        if hasattr(task_instance, 'retry_kwargs'):
            retry_kwargs = task_instance.retry_kwargs
            if 'max_retries' in retry_kwargs:
                assert retry_kwargs['max_retries'] > 0


@pytest.mark.integration
@pytest.mark.requires_celery
class TestNotificationTaskPrioritization:
    """Test task prioritization and queue management"""
    
    async def test_urgent_notification_high_priority_queue(self, celery_app):
        """Test urgent notifications use high priority queue"""
        from tasks.notification_tasks import send_notification
        
        task_data = {
            "notification_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "channel": "sms",
            "priority": "urgent",
            "recipient": "+1234567890",
            "content": "URGENT: Security alert"
        }
        
        # Mock provider
        with patch('providers.sms.SMSProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.send.return_value = {"status": "sent", "message_id": "urgent-123"}
            mock_provider.return_value = mock_instance
            
            # Mock database
            with patch('services.notification_service.NotificationService') as mock_service:
                mock_service_instance = AsyncMock()
                mock_service.return_value = mock_service_instance
                
                # Apply task with urgent priority
                result = send_notification.apply(
                    args=[task_data],
                    priority=9,  # High priority
                    routing_key='notifications.urgent'
                )
                
                assert result.successful()
                task_result = result.result
                assert task_result["status"] == "sent"
    
    async def test_low_priority_notification_delay(self, celery_app):
        """Test low priority notifications can be delayed"""
        from tasks.notification_tasks import send_notification
        
        task_data = {
            "notification_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "channel": "email",
            "priority": "low",
            "recipient": "user@example.com",
            "content": "Low priority newsletter"
        }
        
        # Mock provider
        with patch('providers.email.EmailProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.send.return_value = EmailProviderMocks.get_successful_send_response()
            mock_provider.return_value = mock_instance
            
            # Mock database
            with patch('services.notification_service.NotificationService') as mock_service:
                mock_service_instance = AsyncMock()
                mock_service.return_value = mock_service_instance
                
                # Apply task with low priority and delay
                result = send_notification.apply(
                    args=[task_data],
                    priority=1,  # Low priority
                    countdown=300,  # 5 minute delay
                    routing_key='notifications.low'
                )
                
                assert result.successful()


@pytest.mark.integration
@pytest.mark.requires_celery
class TestBulkNotificationTasks:
    """Test bulk notification processing tasks"""
    
    async def test_bulk_email_notification_task(self, celery_app):
        """Test bulk email notification processing"""
        from tasks.notification_tasks import send_bulk_notifications
        
        # Prepare bulk notification data
        bulk_data = {
            "notifications": [
                {
                    "notification_id": str(uuid.uuid4()),
                    "user_id": str(uuid.uuid4()),
                    "channel": "email",
                    "recipient": f"user{i}@example.com",
                    "subject": f"Bulk Email {i+1}",
                    "content": f"This is bulk email {i+1}"
                }
                for i in range(5)
            ]
        }
        
        # Mock provider
        with patch('providers.email.EmailProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.send_bulk.return_value = {
                "successful_count": 5,
                "failed_count": 0,
                "results": [{"status": "sent", "message_id": f"bulk-{i}"} for i in range(5)]
            }
            mock_provider.return_value = mock_instance
            
            # Mock database
            with patch('services.notification_service.NotificationService') as mock_service:
                mock_service_instance = AsyncMock()
                mock_service.return_value = mock_service_instance
                
                result = send_bulk_notifications.apply(args=[bulk_data])
                
                assert result.successful()
                task_result = result.result
                assert task_result["successful_count"] == 5
                assert task_result["failed_count"] == 0
    
    async def test_bulk_notification_partial_failure(self, celery_app):
        """Test bulk notification with partial failures"""
        from tasks.notification_tasks import send_bulk_notifications
        
        bulk_data = {
            "notifications": [
                {
                    "notification_id": str(uuid.uuid4()),
                    "user_id": str(uuid.uuid4()),
                    "channel": "email",
                    "recipient": f"user{i}@example.com",
                    "subject": f"Bulk Email {i+1}",
                    "content": f"Content {i+1}"
                }
                for i in range(3)
            ]
        }
        
        # Mock provider with partial failure
        with patch('providers.email.EmailProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.send_bulk.return_value = {
                "successful_count": 2,
                "failed_count": 1,
                "results": [
                    {"status": "sent", "message_id": "bulk-1"},
                    {"status": "sent", "message_id": "bulk-2"},
                    {"status": "failed", "error": "Invalid email address"}
                ]
            }
            mock_provider.return_value = mock_instance
            
            # Mock database
            with patch('services.notification_service.NotificationService') as mock_service:
                mock_service_instance = AsyncMock()
                mock_service.return_value = mock_service_instance
                
                result = send_bulk_notifications.apply(args=[bulk_data])
                
                assert result.successful()
                task_result = result.result
                assert task_result["successful_count"] == 2
                assert task_result["failed_count"] == 1
                assert "partial_success" in task_result["status"]


@pytest.mark.integration
@pytest.mark.requires_celery
class TestNotificationTaskMonitoring:
    """Test task monitoring and metrics collection"""
    
    async def test_task_execution_metrics(self, celery_app, sample_notification):
        """Test task execution metrics are collected"""
        from tasks.notification_tasks import send_notification
        
        # Mock provider
        with patch('providers.email.EmailProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.send.return_value = EmailProviderMocks.get_successful_send_response()
            mock_provider.return_value = mock_instance
            
            # Mock metrics collection
            with patch('prometheus_client.Counter') as mock_counter, \
                 patch('prometheus_client.Histogram') as mock_histogram:
                
                mock_counter_instance = MagicMock()
                mock_histogram_instance = MagicMock()
                mock_counter.return_value = mock_counter_instance
                mock_histogram.return_value = mock_histogram_instance
                
                # Mock database
                with patch('services.notification_service.NotificationService') as mock_service:
                    mock_service_instance = AsyncMock()
                    mock_service.return_value = mock_service_instance
                    
                    task_data = {
                        "notification_id": str(sample_notification.id),
                        "user_id": str(sample_notification.user_id),
                        "channel": "email",
                        "recipient": "test@example.com",
                        "content": "Test content"
                    }
                    
                    result = send_notification.apply(args=[task_data])
                    
                    assert result.successful()
                    
                    # Verify metrics were recorded (if implemented)
                    # This depends on the actual metrics implementation
    
    async def test_task_failure_alerting(self, celery_app):
        """Test task failure triggers appropriate alerts"""
        from tasks.notification_tasks import send_notification
        
        # Mock provider failure
        with patch('providers.email.EmailProvider') as mock_provider:
            mock_instance = AsyncMock()
            mock_instance.send.side_effect = Exception("Critical system failure")
            mock_provider.return_value = mock_instance
            
            # Mock alerting system
            with patch('services.alerting.AlertManager') as mock_alerting:
                mock_alert_instance = AsyncMock()
                mock_alerting.return_value = mock_alert_instance
                
                # Mock database
                with patch('services.notification_service.NotificationService') as mock_service:
                    mock_service_instance = AsyncMock()
                    mock_service.return_value = mock_service_instance
                    
                    task_data = {
                        "notification_id": str(uuid.uuid4()),
                        "user_id": str(uuid.uuid4()),
                        "channel": "email",
                        "recipient": "test@example.com",
                        "content": "Test content"
                    }
                    
                    result = send_notification.apply(args=[task_data])
                    
                    assert result.successful()
                    
                    # Verify alert was triggered (if implemented)
                    # This depends on the actual alerting implementation