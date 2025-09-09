"""
Sample test data fixtures
Provides reusable test data for various test scenarios
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any

class SampleNotificationData:
    """Sample notification data for testing"""
    
    @staticmethod
    def get_user_data() -> Dict[str, Any]:
        """Get sample user data"""
        return {
            "user_id": "12345678-1234-5678-9012-123456789012",
            "organization_id": "87654321-4321-8765-2109-876543210987",
            "email": "test@example.com",
            "name": "Test User",
            "phone": "+1234567890",
            "roles": ["user"],
            "permissions": ["notification:read", "notification:write"],
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
        }
    
    @staticmethod
    def get_admin_user_data() -> Dict[str, Any]:
        """Get sample admin user data"""
        return {
            "user_id": "admin-123-456-789",
            "organization_id": "org-admin-987-654",
            "email": "admin@example.com",
            "name": "Admin User",
            "phone": "+1987654321",
            "roles": ["admin", "user"],
            "permissions": ["notification:read", "notification:write", "notification:delete", "admin"],
            "is_active": True,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=2)).isoformat()
        }
    
    @staticmethod
    def get_notification_category() -> Dict[str, Any]:
        """Get sample notification category"""
        return {
            "id": str(uuid.uuid4()),
            "name": "system",
            "description": "System notifications for important updates",
            "default_enabled": True,
            "color": "#007bff",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    @staticmethod
    def get_notification_template_email() -> Dict[str, Any]:
        """Get sample email notification template"""
        return {
            "id": str(uuid.uuid4()),
            "name": "welcome_email",
            "category_id": str(uuid.uuid4()),
            "channel": "email",
            "language": "en",
            "subject": "Welcome to {{platform_name}}, {{user_name}}!",
            "content": """
            Hello {{user_name}},
            
            Welcome to {{platform_name}}! We're excited to have you on board.
            
            Your account details:
            - Email: {{user_email}}
            - Account created: {{created_date}}
            - Organization: {{organization_name}}
            
            To get started:
            1. Complete your profile setup
            2. Explore our features
            3. Join our community
            
            If you have any questions, feel free to reach out to our support team.
            
            Best regards,
            The {{platform_name}} Team
            """,
            "variables": {
                "user_name": "string",
                "user_email": "string", 
                "platform_name": "string",
                "created_date": "string",
                "organization_name": "string"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    @staticmethod
    def get_notification_template_sms() -> Dict[str, Any]:
        """Get sample SMS notification template"""
        return {
            "id": str(uuid.uuid4()),
            "name": "verification_sms",
            "category_id": str(uuid.uuid4()),
            "channel": "sms",
            "language": "en",
            "subject": "Verification Code",
            "content": "Your verification code is: {{verification_code}}. Valid for {{expiry_minutes}} minutes. Do not share this code.",
            "variables": {
                "verification_code": "string",
                "expiry_minutes": "integer"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    @staticmethod
    def get_notification_template_push() -> Dict[str, Any]:
        """Get sample push notification template"""
        return {
            "id": str(uuid.uuid4()),
            "name": "new_message_push",
            "category_id": str(uuid.uuid4()),
            "channel": "push",
            "language": "en",
            "subject": "New message from {{sender_name}}",
            "content": "{{message_preview}}",
            "variables": {
                "sender_name": "string",
                "message_preview": "string",
                "deep_link": "string"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    
    @staticmethod
    def get_notification_email() -> Dict[str, Any]:
        """Get sample email notification"""
        return {
            "id": str(uuid.uuid4()),
            "user_id": "12345678-1234-5678-9012-123456789012",
            "category_id": str(uuid.uuid4()),
            "template_id": str(uuid.uuid4()),
            "channel": "email",
            "subject": "Welcome to Our Platform, John!",
            "content": "Hello John, welcome to Our Platform! We're excited to have you on board.",
            "recipient": "john@example.com",
            "priority": "normal",
            "status": "pending",
            "data": {
                "user_name": "John",
                "user_email": "john@example.com",
                "platform_name": "Our Platform",
                "created_date": "2024-01-15",
                "organization_name": "Test Organization"
            },
            "created_at": datetime.utcnow(),
            "sent_at": None,
            "external_message_id": None,
            "error_message": None
        }
    
    @staticmethod
    def get_notification_sms() -> Dict[str, Any]:
        """Get sample SMS notification"""
        return {
            "id": str(uuid.uuid4()),
            "user_id": "12345678-1234-5678-9012-123456789012",
            "category_id": str(uuid.uuid4()),
            "template_id": str(uuid.uuid4()),
            "channel": "sms",
            "subject": "Verification Code",
            "content": "Your verification code is: 123456. Valid for 10 minutes. Do not share this code.",
            "recipient": "+1234567890",
            "priority": "high",
            "status": "pending",
            "data": {
                "verification_code": "123456",
                "expiry_minutes": 10
            },
            "created_at": datetime.utcnow(),
            "sent_at": None,
            "external_message_id": None,
            "error_message": None
        }
    
    @staticmethod
    def get_notification_push() -> Dict[str, Any]:
        """Get sample push notification"""
        return {
            "id": str(uuid.uuid4()),
            "user_id": "12345678-1234-5678-9012-123456789012",
            "category_id": str(uuid.uuid4()),
            "template_id": str(uuid.uuid4()),
            "channel": "push",
            "subject": "New message from Alice",
            "content": "Hey there! How are you doing?",
            "recipient": "push-token-abcdef123456",
            "priority": "normal",
            "status": "pending",
            "data": {
                "sender_name": "Alice",
                "message_preview": "Hey there! How are you doing?",
                "deep_link": "/messages/conversation/123"
            },
            "created_at": datetime.utcnow(),
            "sent_at": None,
            "external_message_id": None,
            "error_message": None
        }
    
    @staticmethod
    def get_notification_in_app() -> Dict[str, Any]:
        """Get sample in-app notification"""
        return {
            "id": str(uuid.uuid4()),
            "user_id": "12345678-1234-5678-9012-123456789012",
            "category_id": str(uuid.uuid4()),
            "template_id": None,
            "channel": "in_app",
            "subject": "System Maintenance Scheduled",
            "content": "System maintenance is scheduled for tonight at 2:00 AM UTC. Expected downtime: 30 minutes.",
            "recipient": "in-app",
            "priority": "normal",
            "status": "pending",
            "data": {
                "maintenance_start": "2024-01-16T02:00:00Z",
                "expected_duration": "30 minutes",
                "affected_services": ["api", "web_app"]
            },
            "created_at": datetime.utcnow(),
            "sent_at": None,
            "external_message_id": None,
            "error_message": None
        }
    
    @staticmethod
    def get_multiple_notifications(count: int = 5) -> List[Dict[str, Any]]:
        """Get multiple sample notifications"""
        notifications = []
        channels = ["email", "sms", "push", "in_app"]
        priorities = ["low", "normal", "high", "urgent"]
        
        for i in range(count):
            notification = {
                "id": str(uuid.uuid4()),
                "user_id": "12345678-1234-5678-9012-123456789012",
                "category_id": str(uuid.uuid4()),
                "template_id": str(uuid.uuid4()) if i % 2 == 0 else None,
                "channel": channels[i % len(channels)],
                "subject": f"Test Notification #{i+1}",
                "content": f"This is test notification number {i+1}",
                "recipient": f"recipient{i+1}@example.com",
                "priority": priorities[i % len(priorities)],
                "status": "pending",
                "data": {
                    "sequence_number": i+1,
                    "test_data": f"value_{i+1}"
                },
                "created_at": datetime.utcnow() - timedelta(minutes=i*5),
                "sent_at": None,
                "external_message_id": None,
                "error_message": None
            }
            notifications.append(notification)
        
        return notifications


class SampleAPIData:
    """Sample API request/response data for testing"""
    
    @staticmethod
    def get_send_notification_request() -> Dict[str, Any]:
        """Get sample send notification API request"""
        return {
            "type": "email",
            "to": "user@example.com",
            "subject": "Test Notification",
            "message": "This is a test notification message",
            "priority": "normal",
            "template_id": None,
            "data": {
                "user_name": "Test User",
                "action": "test_action"
            }
        }
    
    @staticmethod
    def get_send_notification_response() -> Dict[str, Any]:
        """Get sample send notification API response"""
        return {
            "notification_id": str(uuid.uuid4()),
            "status": "queued",
            "message": "Notification queued for delivery",
            "task_id": "task-123-456-789",
            "estimated_delivery": (datetime.utcnow() + timedelta(minutes=1)).isoformat()
        }
    
    @staticmethod
    def get_notification_status_response() -> Dict[str, Any]:
        """Get sample notification status API response"""
        return {
            "notification_id": str(uuid.uuid4()),
            "status": "sent",
            "channel": "email",
            "recipient": "user@example.com",
            "sent_at": datetime.utcnow().isoformat(),
            "delivered_at": None,
            "read_at": None,
            "external_message_id": "msg-ext-123456",
            "error_message": None,
            "retry_count": 0
        }
    
    @staticmethod
    def get_unread_notifications_response() -> Dict[str, Any]:
        """Get sample unread notifications API response"""
        return {
            "unread_count": 3,
            "notifications": [
                {
                    "id": str(uuid.uuid4()),
                    "subject": "Welcome to our platform!",
                    "content": "Thank you for joining us...",
                    "channel": "in_app",
                    "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "is_read": False,
                    "priority": "normal"
                },
                {
                    "id": str(uuid.uuid4()),
                    "subject": "New message received",
                    "content": "You have a new message from...",
                    "channel": "in_app",
                    "created_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                    "is_read": False,
                    "priority": "high"
                },
                {
                    "id": str(uuid.uuid4()),
                    "subject": "System maintenance notice",
                    "content": "Scheduled maintenance tonight...",
                    "channel": "in_app",
                    "created_at": (datetime.utcnow() - timedelta(minutes=30)).isoformat(),
                    "is_read": False,
                    "priority": "normal"
                }
            ],
            "has_more": False,
            "next_page": None
        }
    
    @staticmethod
    def get_template_create_request() -> Dict[str, Any]:
        """Get sample template creation request"""
        return {
            "name": "user_welcome_email",
            "category": "user_onboarding",
            "channel": "email",
            "language": "en",
            "subject": "Welcome {{user_name}} to {{platform_name}}!",
            "content": "Hello {{user_name}},\n\nWelcome to {{platform_name}}!",
            "variables": {
                "user_name": {
                    "type": "string",
                    "required": True,
                    "description": "User's display name"
                },
                "platform_name": {
                    "type": "string", 
                    "required": True,
                    "description": "Platform name"
                }
            },
            "is_active": True
        }
    
    @staticmethod
    def get_queue_status_response() -> Dict[str, Any]:
        """Get sample queue status API response"""
        return {
            "total_pending": 47,
            "queues": {
                "urgent": {
                    "pending": 2,
                    "processing": 1,
                    "failed": 0
                },
                "high": {
                    "pending": 5,
                    "processing": 2,
                    "failed": 1
                },
                "normal": {
                    "pending": 35,
                    "processing": 3,
                    "failed": 2
                },
                "low": {
                    "pending": 5,
                    "processing": 0,
                    "failed": 1
                }
            },
            "workers": {
                "active": 6,
                "total": 10,
                "last_heartbeat": datetime.utcnow().isoformat()
            },
            "processing_rate": {
                "last_minute": 12,
                "last_hour": 450,
                "last_day": 8500
            }
        }


class SampleErrorData:
    """Sample error data for testing error scenarios"""
    
    @staticmethod
    def get_validation_error() -> Dict[str, Any]:
        """Get sample validation error"""
        return {
            "error": "validation_error",
            "message": "Invalid request data",
            "details": [
                {
                    "field": "email",
                    "message": "Invalid email format",
                    "code": "INVALID_EMAIL"
                },
                {
                    "field": "message",
                    "message": "Message content is required",
                    "code": "REQUIRED_FIELD"
                }
            ]
        }
    
    @staticmethod
    def get_authentication_error() -> Dict[str, Any]:
        """Get sample authentication error"""
        return {
            "error": "authentication_error",
            "message": "Invalid or expired token",
            "code": "INVALID_TOKEN",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def get_rate_limit_error() -> Dict[str, Any]:
        """Get sample rate limit error"""
        return {
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "code": "RATE_LIMIT_EXCEEDED",
            "retry_after": 60,
            "limit": 100,
            "remaining": 0,
            "reset_time": (datetime.utcnow() + timedelta(minutes=1)).isoformat()
        }
    
    @staticmethod
    def get_service_unavailable_error() -> Dict[str, Any]:
        """Get sample service unavailable error"""
        return {
            "error": "service_unavailable",
            "message": "Identity service is temporarily unavailable",
            "code": "SERVICE_UNAVAILABLE",
            "retry_after": 30,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def get_notification_delivery_error() -> Dict[str, Any]:
        """Get sample notification delivery error"""
        return {
            "error": "delivery_failed",
            "message": "Failed to deliver notification",
            "code": "DELIVERY_FAILED",
            "details": {
                "provider": "smtp",
                "provider_code": "550",
                "provider_message": "User mailbox unavailable",
                "retry_possible": False
            },
            "notification_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }


class SampleProviderData:
    """Sample data for notification provider testing"""
    
    @staticmethod
    def get_email_provider_config() -> Dict[str, Any]:
        """Get sample email provider configuration"""
        return {
            "provider": "smtp",
            "settings": {
                "host": "smtp.example.com",
                "port": 587,
                "username": "notifications@example.com",
                "password": "secure_password",
                "use_tls": True,
                "timeout": 30
            },
            "rate_limits": {
                "per_second": 10,
                "per_minute": 100,
                "per_hour": 1000
            },
            "retry_config": {
                "max_attempts": 3,
                "base_delay": 60,
                "max_delay": 3600
            }
        }
    
    @staticmethod
    def get_sms_provider_config() -> Dict[str, Any]:
        """Get sample SMS provider configuration"""
        return {
            "provider": "twilio",
            "settings": {
                "account_sid": "ACxxxxx",
                "auth_token": "secret_token",
                "from_number": "+1234567890",
                "webhook_url": "https://api.example.com/webhooks/sms"
            },
            "rate_limits": {
                "per_second": 5,
                "per_minute": 50,
                "per_hour": 1000
            }
        }
    
    @staticmethod
    def get_push_provider_config() -> Dict[str, Any]:
        """Get sample push notification provider configuration"""
        return {
            "provider": "fcm",
            "settings": {
                "server_key": "firebase_server_key",
                "project_id": "firebase_project_id",
                "endpoint": "https://fcm.googleapis.com/fcm/send"
            },
            "rate_limits": {
                "per_second": 20,
                "per_minute": 1000,
                "per_hour": 50000
            }
        }