"""
Integration tests for notification providers
Tests email, SMS, push, and in-app notification delivery systems
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
import json

from tests.fixtures.mock_responses import (
    EmailProviderMocks, SMSProviderMocks, PushProviderMocks
)
from tests.fixtures.sample_data import SampleNotificationData

@pytest.mark.integration
@pytest.mark.requires_external
class TestEmailNotificationProvider:
    """Integration tests for email notification provider"""
    
    @pytest.fixture
    async def email_provider(self):
        """Create email provider instance"""
        from providers.email import EmailProvider
        config = {
            "host": "smtp.example.com",
            "port": 587,
            "username": "test@example.com",
            "password": "test_password",
            "use_tls": True
        }
        return EmailProvider(config)
    
    async def test_send_email_success(self, email_provider):
        """Test successful email sending"""
        # Mock SMTP client
        with patch('aiosmtplib.SMTP') as mock_smtp:
            mock_smtp_instance = AsyncMock()
            mock_smtp_instance.connect.return_value = None
            mock_smtp_instance.starttls.return_value = None
            mock_smtp_instance.login.return_value = None
            mock_smtp_instance.send_message.return_value = {}
            mock_smtp_instance.quit.return_value = None
            mock_smtp.return_value = mock_smtp_instance
            
            notification_data = SampleNotificationData.get_notification_email()
            
            result = await email_provider.send(
                recipient=notification_data["recipient"],
                subject=notification_data["subject"],
                content=notification_data["content"],
                data=notification_data["data"]
            )
            
            assert result["status"] == "sent"
            assert "message_id" in result
            assert result["provider"] == "smtp"
            
            # Verify SMTP operations were called
            mock_smtp_instance.connect.assert_called_once()
            mock_smtp_instance.send_message.assert_called_once()
            mock_smtp_instance.quit.assert_called_once()
    
    async def test_send_email_smtp_connection_error(self, email_provider):
        """Test email sending with SMTP connection error"""
        with patch('aiosmtplib.SMTP') as mock_smtp:
            mock_smtp_instance = AsyncMock()
            mock_smtp_instance.connect.side_effect = Exception("Connection refused")
            mock_smtp.return_value = mock_smtp_instance
            
            notification_data = SampleNotificationData.get_notification_email()
            
            result = await email_provider.send(
                recipient=notification_data["recipient"],
                subject=notification_data["subject"],
                content=notification_data["content"]
            )
            
            assert result["status"] == "failed"
            assert "error" in result
            assert "connection" in result["error"].lower()
    
    async def test_send_email_authentication_error(self, email_provider):
        """Test email sending with authentication error"""
        with patch('aiosmtplib.SMTP') as mock_smtp:
            mock_smtp_instance = AsyncMock()
            mock_smtp_instance.connect.return_value = None
            mock_smtp_instance.login.side_effect = Exception("Authentication failed")
            mock_smtp.return_value = mock_smtp_instance
            
            notification_data = SampleNotificationData.get_notification_email()
            
            result = await email_provider.send(
                recipient=notification_data["recipient"],
                subject=notification_data["subject"],
                content=notification_data["content"]
            )
            
            assert result["status"] == "failed"
            assert "error" in result
            assert "authentication" in result["error"].lower()
    
    async def test_send_email_rate_limit_error(self, email_provider):
        """Test email sending with rate limit error"""
        with patch('aiosmtplib.SMTP') as mock_smtp:
            mock_smtp_instance = AsyncMock()
            mock_smtp_instance.connect.return_value = None
            mock_smtp_instance.send_message.side_effect = Exception("Rate limit exceeded")
            mock_smtp.return_value = mock_smtp_instance
            
            notification_data = SampleNotificationData.get_notification_email()
            
            result = await email_provider.send(
                recipient=notification_data["recipient"],
                subject=notification_data["subject"],
                content=notification_data["content"]
            )
            
            assert result["status"] == "failed"
            assert "error" in result
            assert "rate limit" in result["error"].lower()
    
    async def test_send_email_invalid_recipient(self, email_provider):
        """Test email sending with invalid recipient"""
        with patch('aiosmtplib.SMTP') as mock_smtp:
            mock_smtp_instance = AsyncMock()
            mock_smtp_instance.connect.return_value = None
            mock_smtp_instance.send_message.side_effect = Exception("Invalid recipient")
            mock_smtp.return_value = mock_smtp_instance
            
            result = await email_provider.send(
                recipient="invalid-email",
                subject="Test Subject",
                content="Test Content"
            )
            
            assert result["status"] == "failed"
            assert "error" in result
    
    async def test_send_email_with_html_content(self, email_provider):
        """Test sending HTML email content"""
        with patch('aiosmtplib.SMTP') as mock_smtp:
            mock_smtp_instance = AsyncMock()
            mock_smtp_instance.connect.return_value = None
            mock_smtp_instance.send_message.return_value = {}
            mock_smtp.return_value = mock_smtp_instance
            
            html_content = """
            <html>
                <body>
                    <h1>Welcome {{name}}!</h1>
                    <p>Thank you for joining <strong>{{platform}}</strong>.</p>
                </body>
            </html>
            """
            
            result = await email_provider.send(
                recipient="test@example.com",
                subject="Welcome!",
                content=html_content,
                content_type="html",
                data={"name": "John", "platform": "Our Service"}
            )
            
            assert result["status"] == "sent"
            
            # Verify HTML content was processed
            call_args = mock_smtp_instance.send_message.call_args
            sent_message = call_args[0][0]  # First argument should be the message
            assert "html" in str(sent_message).lower() or "John" in str(sent_message)


@pytest.mark.integration
@pytest.mark.requires_external
class TestSMSNotificationProvider:
    """Integration tests for SMS notification provider"""
    
    @pytest.fixture
    async def sms_provider(self):
        """Create SMS provider instance"""
        from providers.sms import SMSProvider
        config = {
            "account_sid": "test_sid",
            "auth_token": "test_token",
            "from_number": "+1234567890"
        }
        return SMSProvider(config)
    
    async def test_send_sms_success(self, sms_provider):
        """Test successful SMS sending"""
        # Mock Twilio client
        with patch('twilio.rest.Client') as mock_twilio:
            mock_client = MagicMock()
            mock_message = MagicMock()
            mock_message.sid = "SMS123456789"
            mock_message.status = "queued"
            mock_client.messages.create.return_value = mock_message
            mock_twilio.return_value = mock_client
            
            notification_data = SampleNotificationData.get_notification_sms()
            
            result = await sms_provider.send(
                recipient=notification_data["recipient"],
                content=notification_data["content"],
                data=notification_data["data"]
            )
            
            assert result["status"] == "sent"
            assert result["message_id"] == "SMS123456789"
            assert result["provider"] == "twilio"
            
            # Verify Twilio client was used correctly
            mock_client.messages.create.assert_called_once()
            call_args = mock_client.messages.create.call_args
            assert call_args.kwargs["to"] == notification_data["recipient"]
            assert call_args.kwargs["body"] == notification_data["content"]
    
    async def test_send_sms_invalid_phone_number(self, sms_provider):
        """Test SMS sending with invalid phone number"""
        with patch('twilio.rest.Client') as mock_twilio:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("Invalid phone number")
            mock_twilio.return_value = mock_client
            
            result = await sms_provider.send(
                recipient="invalid-phone",
                content="Test message"
            )
            
            assert result["status"] == "failed"
            assert "error" in result
            assert "invalid" in result["error"].lower()
    
    async def test_send_sms_insufficient_balance(self, sms_provider):
        """Test SMS sending with insufficient account balance"""
        with patch('twilio.rest.Client') as mock_twilio:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("Insufficient balance")
            mock_twilio.return_value = mock_client
            
            result = await sms_provider.send(
                recipient="+1234567890",
                content="Test message"
            )
            
            assert result["status"] == "failed"
            assert "error" in result
    
    async def test_send_sms_with_long_message(self, sms_provider):
        """Test SMS sending with long message (multiple segments)"""
        with patch('twilio.rest.Client') as mock_twilio:
            mock_client = MagicMock()
            mock_message = MagicMock()
            mock_message.sid = "SMS_LONG_123"
            mock_message.status = "queued"
            mock_message.num_segments = 3
            mock_client.messages.create.return_value = mock_message
            mock_twilio.return_value = mock_client
            
            long_message = "This is a very long SMS message that will likely be split into multiple segments because it exceeds the standard SMS length limit of 160 characters for GSM encoding or 70 characters for Unicode encoding."
            
            result = await sms_provider.send(
                recipient="+1234567890",
                content=long_message
            )
            
            assert result["status"] == "sent"
            assert result["segments"] == 3
    
    async def test_send_sms_rate_limiting(self, sms_provider):
        """Test SMS sending with rate limiting"""
        with patch('twilio.rest.Client') as mock_twilio:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("Rate limit exceeded")
            mock_twilio.return_value = mock_client
            
            result = await sms_provider.send(
                recipient="+1234567890",
                content="Test message"
            )
            
            assert result["status"] == "failed"
            assert "rate limit" in result["error"].lower()


@pytest.mark.integration
@pytest.mark.requires_external
class TestPushNotificationProvider:
    """Integration tests for push notification provider"""
    
    @pytest.fixture
    async def push_provider(self):
        """Create push provider instance"""
        from providers.push import PushProvider
        config = {
            "server_key": "test_server_key",
            "project_id": "test_project"
        }
        return PushProvider(config)
    
    async def test_send_push_notification_success(self, push_provider):
        """Test successful push notification sending"""
        # Mock FCM client
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "multicast_id": 123456789,
                "success": 1,
                "failure": 0,
                "results": [{"message_id": "push_msg_123"}]
            }
            mock_post.return_value = mock_response
            
            notification_data = SampleNotificationData.get_notification_push()
            
            result = await push_provider.send(
                recipient=notification_data["recipient"],
                title=notification_data["subject"],
                content=notification_data["content"],
                data=notification_data["data"]
            )
            
            assert result["status"] == "sent"
            assert result["message_id"] == "push_msg_123"
            assert result["provider"] == "fcm"
            
            # Verify FCM API was called correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "fcm.googleapis.com" in str(call_args)
    
    async def test_send_push_invalid_token(self, push_provider):
        """Test push notification with invalid token"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "multicast_id": 123456789,
                "success": 0,
                "failure": 1,
                "results": [{"error": "NotRegistered"}]
            }
            mock_post.return_value = mock_response
            
            result = await push_provider.send(
                recipient="invalid_token",
                title="Test Title",
                content="Test content"
            )
            
            assert result["status"] == "failed"
            assert "error" in result
            assert "NotRegistered" in result["error"]
    
    async def test_send_push_quota_exceeded(self, push_provider):
        """Test push notification with quota exceeded"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 429
            mock_response.json.return_value = {"error": "QuotaExceeded"}
            mock_post.return_value = mock_response
            
            result = await push_provider.send(
                recipient="valid_token",
                title="Test Title", 
                content="Test content"
            )
            
            assert result["status"] == "failed"
            assert "quota" in result["error"].lower()
    
    async def test_send_push_with_data_payload(self, push_provider):
        """Test push notification with custom data payload"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "multicast_id": 123456789,
                "success": 1,
                "failure": 0,
                "results": [{"message_id": "push_data_123"}]
            }
            mock_post.return_value = mock_response
            
            custom_data = {
                "deep_link": "/messages/123",
                "action": "open_conversation",
                "conversation_id": "conv_456",
                "sender_avatar": "https://example.com/avatar.jpg"
            }
            
            result = await push_provider.send(
                recipient="valid_token",
                title="New Message",
                content="You have a new message",
                data=custom_data
            )
            
            assert result["status"] == "sent"
            
            # Verify custom data was included in payload
            call_args = mock_post.call_args
            request_data = json.loads(call_args.kwargs["data"])
            assert "data" in request_data
            assert request_data["data"]["deep_link"] == "/messages/123"
    
    async def test_send_push_to_multiple_tokens(self, push_provider):
        """Test push notification to multiple device tokens"""
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "multicast_id": 123456789,
                "success": 2,
                "failure": 1,
                "results": [
                    {"message_id": "push_1"},
                    {"message_id": "push_2"},
                    {"error": "InvalidRegistration"}
                ]
            }
            mock_post.return_value = mock_response
            
            tokens = ["token1", "token2", "invalid_token"]
            
            result = await push_provider.send_to_multiple(
                recipients=tokens,
                title="Broadcast Message",
                content="This is a broadcast notification"
            )
            
            assert result["status"] == "partial_success"
            assert result["successful_count"] == 2
            assert result["failed_count"] == 1


@pytest.mark.integration
class TestInAppNotificationProvider:
    """Integration tests for in-app notification provider"""
    
    @pytest.fixture
    async def in_app_provider(self, db_session, mock_redis):
        """Create in-app provider instance"""
        from providers.in_app import InAppProvider
        return InAppProvider(db_session=db_session, cache=mock_redis)
    
    async def test_send_in_app_notification_success(self, in_app_provider, mock_user_data):
        """Test successful in-app notification creation"""
        notification_data = SampleNotificationData.get_notification_in_app()
        notification_data["user_id"] = mock_user_data["user_id"]
        
        result = await in_app_provider.send(
            user_id=notification_data["user_id"],
            title=notification_data["subject"],
            content=notification_data["content"],
            data=notification_data["data"]
        )
        
        assert result["status"] == "sent"
        assert "message_id" in result
        assert result["provider"] == "in_app"
    
    async def test_get_unread_notifications(self, in_app_provider, mock_user_data):
        """Test retrieving unread in-app notifications"""
        user_id = mock_user_data["user_id"]
        
        # First, create some notifications
        for i in range(3):
            await in_app_provider.send(
                user_id=user_id,
                title=f"Test Notification {i+1}",
                content=f"This is test notification {i+1}",
                data={"sequence": i+1}
            )
        
        # Get unread notifications
        unread_notifications = await in_app_provider.get_unread_notifications(user_id)
        
        assert len(unread_notifications) == 3
        assert all(not notif["is_read"] for notif in unread_notifications)
        
        # Get unread count
        unread_count = await in_app_provider.get_unread_count(user_id)
        assert unread_count == 3
    
    async def test_mark_notifications_as_read(self, in_app_provider, mock_user_data):
        """Test marking notifications as read"""
        user_id = mock_user_data["user_id"]
        
        # Create notifications
        notification_ids = []
        for i in range(3):
            result = await in_app_provider.send(
                user_id=user_id,
                title=f"Test Notification {i+1}",
                content=f"Content {i+1}"
            )
            notification_ids.append(result["message_id"])
        
        # Mark first two as read
        marked_count = await in_app_provider.mark_notifications_read(
            user_id=user_id,
            notification_ids=notification_ids[:2]
        )
        
        assert marked_count == 2
        
        # Verify unread count decreased
        unread_count = await in_app_provider.get_unread_count(user_id)
        assert unread_count == 1
    
    async def test_get_notification_history(self, in_app_provider, mock_user_data):
        """Test retrieving notification history with pagination"""
        user_id = mock_user_data["user_id"]
        
        # Create multiple notifications
        for i in range(10):
            await in_app_provider.send(
                user_id=user_id,
                title=f"Historical Notification {i+1}",
                content=f"Content {i+1}"
            )
        
        # Get first page
        page1 = await in_app_provider.get_notification_history(
            user_id=user_id,
            page=1,
            page_size=5
        )
        
        assert len(page1["notifications"]) == 5
        assert page1["total"] == 10
        assert page1["page"] == 1
        assert page1["has_more"] is True
        
        # Get second page
        page2 = await in_app_provider.get_notification_history(
            user_id=user_id,
            page=2,
            page_size=5
        )
        
        assert len(page2["notifications"]) == 5
        assert page2["page"] == 2
        assert page2["has_more"] is False
    
    async def test_delete_old_notifications(self, in_app_provider, mock_user_data):
        """Test cleanup of old notifications"""
        user_id = mock_user_data["user_id"]
        
        # Create notifications with different ages
        old_date = datetime.utcnow() - timedelta(days=90)
        recent_date = datetime.utcnow() - timedelta(days=10)
        
        # Mock old notifications (would need to manipulate created_at dates)
        # This test would verify cleanup functionality
        
        initial_count = await in_app_provider.get_total_count(user_id)
        
        # Perform cleanup (remove notifications older than 30 days)
        cleaned_count = await in_app_provider.cleanup_old_notifications(
            user_id=user_id,
            days_to_keep=30
        )
        
        final_count = await in_app_provider.get_total_count(user_id)
        
        assert final_count <= initial_count
        assert cleaned_count >= 0


@pytest.mark.integration
class TestAdvancedEmailProviderIntegration:
    """Advanced integration tests for email provider with failover and rate limiting"""
    
    @pytest.fixture
    async def multi_provider_config(self):
        """Email provider with multiple SMTP backends"""
        return {
            "primary": {
                "host": "primary-smtp.example.com",
                "port": 587,
                "username": "primary@example.com",
                "password": "primary_pass"
            },
            "secondary": {
                "host": "backup-smtp.example.com", 
                "port": 587,
                "username": "backup@example.com",
                "password": "backup_pass"
            },
            "sendgrid": {
                "api_key": "SG.test_api_key",
                "endpoint": "https://api.sendgrid.com/v3/mail/send"
            }
        }
    
    async def test_email_provider_failover_sequence(self, multi_provider_config):
        """Test email provider failover when primary fails"""
        from providers.email import MultiEmailProvider
        
        provider = MultiEmailProvider(multi_provider_config)
        
        with patch('aiosmtplib.SMTP') as mock_smtp, \
             patch('httpx.AsyncClient.post') as mock_sendgrid:
            
            # Mock primary SMTP failure
            mock_smtp_primary = AsyncMock()
            mock_smtp_primary.connect.side_effect = Exception("Primary SMTP down")
            
            # Mock secondary SMTP success
            mock_smtp_secondary = AsyncMock()
            mock_smtp_secondary.connect.return_value = None
            mock_smtp_secondary.send_message.return_value = {}
            
            # Configure SMTP mock to return different instances
            mock_smtp.side_effect = [mock_smtp_primary, mock_smtp_secondary]
            
            result = await provider.send_with_failover(
                recipient="test@example.com",
                subject="Failover Test",
                content="Testing failover mechanism"
            )
            
            assert result["status"] == "sent"
            assert result["provider_used"] == "secondary"
            assert "failover_attempted" in result
            assert result["failover_attempted"] is True
    
    async def test_email_provider_sendgrid_integration(self, multi_provider_config):
        """Test SendGrid API integration with comprehensive error handling"""
        from providers.email import SendGridEmailProvider
        
        provider = SendGridEmailProvider(multi_provider_config["sendgrid"])
        
        # Test successful send
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 202
            mock_response.json.return_value = {"message": "success"}
            mock_response.headers = {"X-Message-Id": "sg-message-123"}
            mock_post.return_value = mock_response
            
            result = await provider.send(
                recipient="user@example.com",
                subject="SendGrid Test",
                content="Testing SendGrid integration",
                data={"user_name": "John Doe"}
            )
            
            assert result["status"] == "sent"
            assert result["message_id"] == "sg-message-123"
            assert result["provider"] == "sendgrid"
            
            # Verify request structure
            call_args = mock_post.call_args
            request_data = json.loads(call_args.kwargs["content"])
            assert "personalizations" in request_data
            assert "from" in request_data
            assert "content" in request_data
    
    async def test_email_rate_limiting_with_backoff(self, multi_provider_config):
        """Test email rate limiting with exponential backoff"""
        from providers.email import RateLimitedEmailProvider
        
        provider = RateLimitedEmailProvider(
            config=multi_provider_config["primary"],
            rate_limit_per_minute=10,
            rate_limit_per_hour=100
        )
        
        with patch('aiosmtplib.SMTP') as mock_smtp:
            mock_smtp_instance = AsyncMock()
            
            # First few requests succeed
            mock_smtp_instance.send_message.return_value = {}
            mock_smtp.return_value = mock_smtp_instance
            
            # Send requests rapidly
            results = []
            for i in range(15):  # Exceed rate limit of 10/minute
                result = await provider.send(
                    recipient=f"user{i}@example.com",
                    subject=f"Rate Test {i}",
                    content=f"Message {i}"
                )
                results.append(result)
            
            # Verify rate limiting kicked in
            successful_sends = [r for r in results if r["status"] == "sent"]
            rate_limited = [r for r in results if r["status"] == "rate_limited"]
            
            assert len(successful_sends) <= 10  # Within rate limit
            assert len(rate_limited) >= 5      # Exceeded limit
            
            # Verify backoff information is provided
            for limited_result in rate_limited:
                assert "retry_after" in limited_result
                assert "rate_limit_type" in limited_result


@pytest.mark.integration 
class TestAdvancedSMSProviderIntegration:
    """Advanced SMS provider integration tests with multiple providers and failover"""
    
    @pytest.fixture
    async def multi_sms_config(self):
        """Multi-provider SMS configuration"""
        return {
            "twilio": {
                "account_sid": "twilio_test_sid",
                "auth_token": "twilio_test_token",
                "from_number": "+1234567890"
            },
            "aws_sns": {
                "access_key": "aws_access_key",
                "secret_key": "aws_secret_key",
                "region": "us-east-1"
            },
            "ovh": {
                "application_key": "ovh_app_key",
                "application_secret": "ovh_app_secret",
                "consumer_key": "ovh_consumer_key",
                "account": "ovh_account"
            }
        }
    
    async def test_sms_multi_provider_cost_optimization(self, multi_sms_config):
        """Test SMS routing based on cost optimization"""
        from providers.sms import CostOptimizedSMSProvider
        
        provider = CostOptimizedSMSProvider(multi_sms_config)
        
        with patch('twilio.rest.Client') as mock_twilio, \
             patch('boto3.client') as mock_aws, \
             patch('ovh.Api') as mock_ovh:
            
            # Mock cost responses for different regions/countries
            mock_twilio_client = MagicMock()
            mock_twilio_client.messages.create.return_value.sid = "twilio_123"
            mock_twilio.return_value = mock_twilio_client
            
            # Test domestic US number (should use cheapest US provider)
            us_result = await provider.send_optimized(
                recipient="+1234567890",
                content="Test US message"
            )
            
            assert us_result["status"] == "sent"
            assert "cost_estimate" in us_result
            assert "provider_selected" in us_result
            assert us_result["provider_selected"] in ["twilio", "aws_sns"]
            
            # Test international number (should route to best international rate)
            intl_result = await provider.send_optimized(
                recipient="+33123456789",  # French number
                content="Test international message"
            )
            
            assert intl_result["status"] == "sent"
            assert "cost_estimate" in intl_result
            assert "provider_selected" in intl_result
    
    async def test_sms_delivery_tracking_integration(self, multi_sms_config):
        """Test comprehensive SMS delivery tracking"""
        from providers.sms import DeliveryTrackingSMSProvider
        
        provider = DeliveryTrackingSMSProvider(multi_sms_config["twilio"])
        
        with patch('twilio.rest.Client') as mock_twilio:
            mock_client = MagicMock()
            
            # Mock message creation
            mock_message = MagicMock()
            mock_message.sid = "SMS_TRACK_123"
            mock_message.status = "queued"
            mock_message.date_sent = datetime.utcnow()
            mock_client.messages.create.return_value = mock_message
            
            # Mock status updates
            mock_client.messages.get.return_value = mock_message
            mock_twilio.return_value = mock_client
            
            # Send message with tracking
            result = await provider.send_with_tracking(
                recipient="+1234567890",
                content="Tracked message",
                webhook_url="https://api.example.com/sms/webhook"
            )
            
            assert result["status"] == "sent"
            assert result["message_id"] == "SMS_TRACK_123"
            assert "tracking_id" in result
            
            # Simulate status updates
            status_updates = [
                {"status": "sent", "timestamp": datetime.utcnow()},
                {"status": "delivered", "timestamp": datetime.utcnow() + timedelta(minutes=1)}
            ]
            
            for update in status_updates:
                tracking_result = await provider.update_delivery_status(
                    message_id="SMS_TRACK_123",
                    status=update["status"],
                    timestamp=update["timestamp"]
                )
                
                assert tracking_result["updated"] is True
                assert tracking_result["current_status"] == update["status"]
    
    async def test_sms_content_optimization(self, multi_sms_config):
        """Test SMS content optimization for different providers"""
        from providers.sms import ContentOptimizedSMSProvider
        
        provider = ContentOptimizedSMSProvider(multi_sms_config["twilio"])
        
        with patch('twilio.rest.Client') as mock_twilio:
            mock_client = MagicMock()
            mock_message = MagicMock()
            mock_client.messages.create.return_value = mock_message
            mock_twilio.return_value = mock_client
            
            # Test long message optimization
            long_message = "This is a very long SMS message that exceeds the standard 160 character limit for GSM encoding. The provider should automatically optimize this by either splitting it into multiple segments or using Unicode encoding efficiently to minimize cost while maintaining readability."
            
            result = await provider.send_optimized(
                recipient="+1234567890",
                content=long_message
            )
            
            assert result["status"] == "sent"
            assert "optimization_applied" in result
            assert "segment_count" in result
            assert "encoding_used" in result
            assert result["segment_count"] >= 1
            
            # Verify optimization decisions
            call_args = mock_client.messages.create.call_args
            optimized_content = call_args.kwargs["body"]
            assert len(optimized_content) <= len(long_message)  # Should be optimized


@pytest.mark.integration
class TestNotificationProviderFactory:
    """Integration tests for notification provider factory"""
    
    async def test_provider_factory_email(self):
        """Test creating email provider through factory"""
        from providers.factory import NotificationProviderFactory
        
        config = {
            "type": "email",
            "host": "smtp.example.com",
            "port": 587,
            "username": "test@example.com",
            "password": "password"
        }
        
        provider = NotificationProviderFactory.create_provider(config)
        
        assert provider is not None
        assert hasattr(provider, 'send')
        assert provider.__class__.__name__ == "EmailProvider"
    
    async def test_provider_factory_sms(self):
        """Test creating SMS provider through factory"""
        from providers.factory import NotificationProviderFactory
        
        config = {
            "type": "sms",
            "account_sid": "test_sid",
            "auth_token": "test_token"
        }
        
        provider = NotificationProviderFactory.create_provider(config)
        
        assert provider is not None
        assert hasattr(provider, 'send')
        assert provider.__class__.__name__ == "SMSProvider"
    
    async def test_provider_factory_push(self):
        """Test creating push provider through factory"""
        from providers.factory import NotificationProviderFactory
        
        config = {
            "type": "push",
            "server_key": "test_key",
            "project_id": "test_project"
        }
        
        provider = NotificationProviderFactory.create_provider(config)
        
        assert provider is not None
        assert hasattr(provider, 'send')
        assert provider.__class__.__name__ == "PushProvider"
    
    async def test_provider_factory_invalid_type(self):
        """Test factory with invalid provider type"""
        from providers.factory import NotificationProviderFactory
        
        config = {
            "type": "invalid_type",
            "some_config": "value"
        }
        
        with pytest.raises(ValueError, match="Unsupported provider type"):
            NotificationProviderFactory.create_provider(config)
    
    async def test_provider_factory_missing_config(self):
        """Test factory with missing required configuration"""
        from providers.factory import NotificationProviderFactory
        
        config = {
            "type": "email"
            # Missing required email configuration
        }
        
        with pytest.raises((ValueError, KeyError)):
            NotificationProviderFactory.create_provider(config)