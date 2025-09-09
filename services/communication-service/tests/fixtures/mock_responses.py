"""
Mock API responses for external services
Provides standardized mock responses for testing integrations
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List

class IdentityServiceMocks:
    """Mock responses for Identity Service API calls"""
    
    @staticmethod
    def get_successful_token_validation() -> Dict[str, Any]:
        """Mock successful JWT token validation response"""
        return {
            "status_code": 200,
            "json": {
                "user_id": "12345678-1234-5678-9012-123456789012",
                "organization_id": "87654321-4321-8765-2109-876543210987",
                "email": "test@example.com",
                "name": "Test User",
                "roles": ["user"],
                "permissions": ["notification:read", "notification:write"],
                "is_active": True,
                "is_verified": True,
                "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }
        }
    
    @staticmethod
    def get_admin_token_validation() -> Dict[str, Any]:
        """Mock successful admin token validation response"""
        return {
            "status_code": 200,
            "json": {
                "user_id": "admin-123-456-789",
                "organization_id": "org-admin-987-654",
                "email": "admin@example.com",
                "name": "Admin User",
                "roles": ["admin", "user"],
                "permissions": [
                    "notification:read", "notification:write", "notification:delete", 
                    "notification:admin", "admin"
                ],
                "is_active": True,
                "is_verified": True,
                "expires_at": (datetime.utcnow() + timedelta(hours=2)).isoformat()
            }
        }
    
    @staticmethod
    def get_invalid_token_response() -> Dict[str, Any]:
        """Mock invalid token response"""
        return {
            "status_code": 401,
            "json": {
                "detail": "Invalid or expired token",
                "error": "authentication_failed",
                "code": "INVALID_TOKEN"
            }
        }
    
    @staticmethod
    def get_expired_token_response() -> Dict[str, Any]:
        """Mock expired token response"""
        return {
            "status_code": 401,
            "json": {
                "detail": "Token has expired",
                "error": "token_expired",
                "code": "TOKEN_EXPIRED",
                "expired_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat()
            }
        }
    
    @staticmethod
    def get_insufficient_permissions_response() -> Dict[str, Any]:
        """Mock insufficient permissions response"""
        return {
            "status_code": 403,
            "json": {
                "detail": "Insufficient permissions for this operation",
                "error": "forbidden",
                "code": "INSUFFICIENT_PERMISSIONS",
                "required_permissions": ["notification:admin"]
            }
        }
    
    @staticmethod
    def get_user_profile_response() -> Dict[str, Any]:
        """Mock user profile response"""
        return {
            "status_code": 200,
            "json": {
                "user_id": "12345678-1234-5678-9012-123456789012",
                "email": "test@example.com",
                "name": "Test User",
                "avatar_url": "https://example.com/avatars/test-user.jpg",
                "timezone": "UTC",
                "language": "en",
                "phone": "+1234567890",
                "organization": {
                    "id": "87654321-4321-8765-2109-876543210987",
                    "name": "Test Organization",
                    "domain": "test.example.com"
                },
                "preferences": {
                    "email_notifications": True,
                    "sms_notifications": True,
                    "push_notifications": True
                },
                "created_at": "2024-01-01T00:00:00Z",
                "last_login": datetime.utcnow().isoformat()
            }
        }
    
    @staticmethod
    def get_user_contact_info_response() -> Dict[str, Any]:
        """Mock user contact information response"""
        return {
            "status_code": 200,
            "json": {
                "user_id": "12345678-1234-5678-9012-123456789012",
                "email": "test@example.com",
                "phone": "+1234567890",
                "push_tokens": [
                    {
                        "token": "push-token-123456",
                        "platform": "ios",
                        "device_id": "device-ios-123",
                        "created_at": "2024-01-01T00:00:00Z",
                        "is_active": True
                    },
                    {
                        "token": "push-token-789012",
                        "platform": "android",
                        "device_id": "device-android-456",
                        "created_at": "2024-01-02T00:00:00Z",
                        "is_active": True
                    }
                ],
                "notification_preferences": {
                    "email": {
                        "enabled": True,
                        "categories": ["system", "marketing", "security"]
                    },
                    "sms": {
                        "enabled": True,
                        "categories": ["security", "urgent"]
                    },
                    "push": {
                        "enabled": True,
                        "categories": ["system", "messages", "updates"]
                    }
                }
            }
        }
    
    @staticmethod
    def get_service_unavailable_response() -> Dict[str, Any]:
        """Mock service unavailable response"""
        return {
            "status_code": 503,
            "json": {
                "detail": "Identity service is temporarily unavailable",
                "error": "service_unavailable",
                "code": "SERVICE_UNAVAILABLE",
                "retry_after": 30
            }
        }
    
    @staticmethod
    def get_timeout_error() -> Exception:
        """Mock timeout exception"""
        import httpx
        return httpx.TimeoutException("Request timed out")
    
    @staticmethod
    def get_connection_error() -> Exception:
        """Mock connection error"""
        import httpx
        return httpx.ConnectError("Connection refused")


class EmailProviderMocks:
    """Mock responses for email notification providers"""
    
    @staticmethod
    def get_successful_send_response() -> Dict[str, Any]:
        """Mock successful email send response"""
        return {
            "status": "sent",
            "message_id": f"email-{uuid.uuid4()}",
            "provider": "smtp",
            "recipient": "test@example.com",
            "sent_at": datetime.utcnow().isoformat(),
            "tracking_url": "https://provider.com/track/email-123456"
        }
    
    @staticmethod
    def get_delivery_confirmation() -> Dict[str, Any]:
        """Mock email delivery confirmation"""
        return {
            "event": "delivered",
            "message_id": f"email-{uuid.uuid4()}",
            "recipient": "test@example.com",
            "delivered_at": datetime.utcnow().isoformat(),
            "provider_response": "250 Message delivered successfully"
        }
    
    @staticmethod
    def get_bounce_notification() -> Dict[str, Any]:
        """Mock email bounce notification"""
        return {
            "event": "bounced",
            "message_id": f"email-{uuid.uuid4()}",
            "recipient": "invalid@example.com",
            "bounced_at": datetime.utcnow().isoformat(),
            "bounce_type": "permanent",
            "reason": "User mailbox does not exist",
            "provider_code": "550"
        }
    
    @staticmethod
    def get_rate_limit_error() -> Dict[str, Any]:
        """Mock email provider rate limit error"""
        return {
            "error": "rate_limited",
            "message": "Daily sending quota exceeded",
            "retry_after": 3600,
            "quota_reset": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
    
    @staticmethod
    def get_smtp_authentication_error() -> Dict[str, Any]:
        """Mock SMTP authentication error"""
        return {
            "error": "authentication_failed",
            "message": "Invalid SMTP credentials",
            "provider_code": "535",
            "provider_message": "Authentication credentials invalid"
        }


class SMSProviderMocks:
    """Mock responses for SMS notification providers"""
    
    @staticmethod
    def get_successful_send_response() -> Dict[str, Any]:
        """Mock successful SMS send response"""
        return {
            "status": "sent",
            "message_id": f"sms-{uuid.uuid4()}",
            "provider": "twilio",
            "recipient": "+1234567890",
            "sent_at": datetime.utcnow().isoformat(),
            "cost": 0.0075,
            "segments": 1
        }
    
    @staticmethod
    def get_delivery_confirmation() -> Dict[str, Any]:
        """Mock SMS delivery confirmation"""
        return {
            "event": "delivered",
            "message_id": f"sms-{uuid.uuid4()}",
            "recipient": "+1234567890",
            "delivered_at": datetime.utcnow().isoformat(),
            "provider_status": "delivered"
        }
    
    @staticmethod
    def get_invalid_phone_error() -> Dict[str, Any]:
        """Mock invalid phone number error"""
        return {
            "error": "invalid_phone_number",
            "message": "Phone number is not valid",
            "recipient": "+invalid123",
            "provider_code": "21614",
            "provider_message": "Phone number is not a valid mobile number"
        }
    
    @staticmethod
    def get_unsubscribed_error() -> Dict[str, Any]:
        """Mock unsubscribed recipient error"""
        return {
            "error": "recipient_unsubscribed",
            "message": "Recipient has opted out of SMS messages",
            "recipient": "+1234567890",
            "unsubscribed_at": "2024-01-10T15:30:00Z"
        }


class PushProviderMocks:
    """Mock responses for push notification providers"""
    
    @staticmethod
    def get_successful_send_response() -> Dict[str, Any]:
        """Mock successful push notification send response"""
        return {
            "status": "sent",
            "message_id": f"push-{uuid.uuid4()}",
            "provider": "fcm",
            "recipient": "push-token-123456",
            "sent_at": datetime.utcnow().isoformat(),
            "multicast_id": 123456789,
            "success": 1,
            "failure": 0
        }
    
    @staticmethod
    def get_invalid_token_error() -> Dict[str, Any]:
        """Mock invalid push token error"""
        return {
            "error": "invalid_registration",
            "message": "Push token is no longer valid",
            "token": "invalid-push-token",
            "provider_error": "NotRegistered",
            "should_remove_token": True
        }
    
    @staticmethod
    def get_device_unregistered_error() -> Dict[str, Any]:
        """Mock device unregistered error"""
        return {
            "error": "device_unregistered",
            "message": "Device is no longer registered for push notifications",
            "token": "push-token-123456",
            "provider_error": "Unregistered",
            "should_remove_token": True
        }
    
    @staticmethod
    def get_quota_exceeded_error() -> Dict[str, Any]:
        """Mock quota exceeded error"""
        return {
            "error": "quota_exceeded",
            "message": "Push notification quota exceeded",
            "retry_after": 3600,
            "quota_reset": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }


class CeleryTaskMocks:
    """Mock responses for Celery task operations"""
    
    @staticmethod
    def get_successful_task_result() -> Dict[str, Any]:
        """Mock successful Celery task result"""
        return {
            "task_id": f"task-{uuid.uuid4()}",
            "status": "SUCCESS",
            "result": {
                "notification_id": str(uuid.uuid4()),
                "status": "sent",
                "message_id": f"msg-{uuid.uuid4()}",
                "provider": "smtp",
                "sent_at": datetime.utcnow().isoformat()
            },
            "started_at": (datetime.utcnow() - timedelta(seconds=30)).isoformat(),
            "completed_at": datetime.utcnow().isoformat(),
            "worker": "worker@localhost.1"
        }
    
    @staticmethod
    def get_pending_task_result() -> Dict[str, Any]:
        """Mock pending Celery task result"""
        return {
            "task_id": f"task-{uuid.uuid4()}",
            "status": "PENDING",
            "result": None,
            "queued_at": datetime.utcnow().isoformat(),
            "queue": "notifications_normal",
            "retries": 0
        }
    
    @staticmethod
    def get_failed_task_result() -> Dict[str, Any]:
        """Mock failed Celery task result"""
        return {
            "task_id": f"task-{uuid.uuid4()}",
            "status": "FAILURE",
            "result": {
                "error": "SMTP connection failed",
                "error_type": "ConnectionError",
                "retry_count": 2,
                "max_retries": 3,
                "next_retry": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
            },
            "started_at": (datetime.utcnow() - timedelta(minutes=2)).isoformat(),
            "failed_at": datetime.utcnow().isoformat(),
            "worker": "worker@localhost.1",
            "traceback": "Traceback (most recent call last):\n  File ...\nConnectionError: SMTP connection failed"
        }
    
    @staticmethod
    def get_retry_task_result() -> Dict[str, Any]:
        """Mock retry Celery task result"""
        return {
            "task_id": f"task-{uuid.uuid4()}",
            "status": "RETRY",
            "result": {
                "error": "Temporary network error",
                "retry_count": 1,
                "max_retries": 3,
                "next_retry": (datetime.utcnow() + timedelta(minutes=2)).isoformat(),
                "backoff": 120
            },
            "started_at": (datetime.utcnow() - timedelta(minutes=1)).isoformat(),
            "retried_at": datetime.utcnow().isoformat(),
            "worker": "worker@localhost.1"
        }
    
    @staticmethod
    def get_task_progress() -> Dict[str, Any]:
        """Mock Celery task progress"""
        return {
            "task_id": f"task-{uuid.uuid4()}",
            "status": "PROGRESS",
            "result": {
                "current_step": "Rendering template",
                "total_steps": 4,
                "progress": 50,
                "details": {
                    "template_rendered": True,
                    "recipient_validated": True,
                    "provider_selected": True,
                    "sending": False
                }
            },
            "started_at": (datetime.utcnow() - timedelta(seconds=10)).isoformat(),
            "worker": "worker@localhost.1"
        }


class RedisQueueMocks:
    """Mock responses for Redis queue operations"""
    
    @staticmethod
    def get_queue_status() -> Dict[str, Any]:
        """Mock Redis queue status"""
        return {
            "queues": {
                "notifications_urgent": {
                    "pending": 2,
                    "processing": 1,
                    "length": 3
                },
                "notifications_high": {
                    "pending": 8,
                    "processing": 2,
                    "length": 10
                },
                "notifications_normal": {
                    "pending": 45,
                    "processing": 5,
                    "length": 50
                },
                "notifications_low": {
                    "pending": 12,
                    "processing": 1,
                    "length": 13
                }
            },
            "total_pending": 67,
            "total_processing": 9,
            "workers_active": 6,
            "last_updated": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def get_queue_peek() -> List[Dict[str, Any]]:
        """Mock queue peek operation"""
        return [
            {
                "notification_id": str(uuid.uuid4()),
                "priority": "high",
                "channel": "email",
                "recipient": "user@example.com",
                "queued_at": datetime.utcnow().isoformat(),
                "attempts": 0
            },
            {
                "notification_id": str(uuid.uuid4()),
                "priority": "normal",
                "channel": "sms",
                "recipient": "+1234567890",
                "queued_at": (datetime.utcnow() - timedelta(minutes=2)).isoformat(),
                "attempts": 1
            }
        ]


class WebhookMocks:
    """Mock webhook responses from notification providers"""
    
    @staticmethod
    def get_email_delivered_webhook() -> Dict[str, Any]:
        """Mock email delivered webhook"""
        return {
            "event": "delivered",
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": f"email-{uuid.uuid4()}",
            "recipient": "test@example.com",
            "provider": "sendgrid",
            "smtp_response": "250 2.0.0 OK",
            "category": ["notification", "transactional"],
            "unique_args": {
                "notification_id": str(uuid.uuid4()),
                "user_id": "12345678-1234-5678-9012-123456789012"
            }
        }
    
    @staticmethod
    def get_email_bounced_webhook() -> Dict[str, Any]:
        """Mock email bounced webhook"""
        return {
            "event": "bounced",
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": f"email-{uuid.uuid4()}",
            "recipient": "bounce@example.com",
            "provider": "sendgrid",
            "reason": "550 5.1.1 User unknown",
            "type": "bounce",
            "bounce_classification": "hard_bounce",
            "unique_args": {
                "notification_id": str(uuid.uuid4()),
                "user_id": "12345678-1234-5678-9012-123456789012"
            }
        }
    
    @staticmethod
    def get_sms_delivered_webhook() -> Dict[str, Any]:
        """Mock SMS delivered webhook"""
        return {
            "MessageSid": f"sms-{uuid.uuid4()}",
            "MessageStatus": "delivered",
            "To": "+1234567890",
            "From": "+1987654321",
            "AccountSid": "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "ApiVersion": "2010-04-01",
            "EventType": "message-delivered",
            "Timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def get_push_feedback_webhook() -> Dict[str, Any]:
        """Mock push notification feedback webhook"""
        return {
            "results": [
                {
                    "message_id": f"push-{uuid.uuid4()}",
                    "registration_id": "push-token-123456",
                    "error": None
                }
            ],
            "canonical_ids": 0,
            "failure": 0,
            "success": 1,
            "multicast_id": 123456789012345,
            "timestamp": datetime.utcnow().isoformat()
        }