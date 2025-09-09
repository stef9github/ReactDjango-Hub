"""
Unit tests for notification services
Tests business logic, service methods, and external integrations
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

# Import services to test
from services.notification_service import NotificationService
from services.template_engine import TemplateEngine
from services.queue_manager import QueueManager

# Import models and enums
from models import (
    Notification, NotificationCategory, NotificationTemplate,
    NotificationChannel, NotificationStatus, NotificationPriority
)

@pytest.mark.unit
@pytest.mark.asyncio
class TestNotificationService:
    """Unit tests for NotificationService"""
    
    @pytest.fixture
    async def notification_service(self, db_session: AsyncSession, mock_redis):
        """Create NotificationService instance with mocked dependencies"""
        with patch('services.notification_service.CacheManager') as mock_cache:
            mock_cache_instance = AsyncMock()
            mock_cache.return_value = mock_cache_instance
            
            service = NotificationService(
                db_session=db_session,
                cache=mock_cache_instance
            )
            yield service
    
    @pytest.fixture
    async def sample_category(self, db_session: AsyncSession):
        """Create sample notification category"""
        category = NotificationCategory(
            name="test_service_category",
            description="Category for service tests",
            default_enabled=True
        )
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)
        return category
    
    @pytest.fixture
    async def sample_template(self, db_session: AsyncSession, sample_category):
        """Create sample notification template"""
        template = NotificationTemplate(
            name="test_service_template",
            category_id=sample_category.id,
            channel=NotificationChannel.EMAIL,
            language="en",
            subject="Welcome {{name}}!",
            content="Hello {{name}}, your {{action}} was successful.",
            variables={"name": "string", "action": "string"}
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)
        return template
    
    async def test_create_notification_with_template(
        self, 
        notification_service: NotificationService, 
        sample_template: NotificationTemplate
    ):
        """Test creating notification using template"""
        user_id = uuid.uuid4()
        recipient = "test@example.com"
        template_data = {
            "name": "John Doe",
            "action": "account registration"
        }
        
        notification = await notification_service.create_notification(
            user_id=user_id,
            template_id=sample_template.id,
            recipient=recipient,
            data=template_data
        )
        
        assert notification is not None
        assert notification.user_id == user_id
        assert notification.template_id == sample_template.id
        assert notification.recipient == recipient
        assert notification.channel == NotificationChannel.EMAIL
        assert notification.status == NotificationStatus.PENDING
        assert notification.data == template_data
        # Template should be rendered
        assert "John Doe" in notification.subject
        assert "account registration" in notification.content
    
    async def test_create_notification_without_template(
        self, 
        notification_service: NotificationService,
        sample_category: NotificationCategory
    ):
        """Test creating notification without template"""
        user_id = uuid.uuid4()
        recipient = "test@example.com"
        
        notification = await notification_service.create_notification(
            user_id=user_id,
            category_id=sample_category.id,
            channel=NotificationChannel.SMS,
            subject="Direct SMS",
            content="This is a direct SMS message",
            recipient=recipient
        )
        
        assert notification is not None
        assert notification.user_id == user_id
        assert notification.category_id == sample_category.id
        assert notification.template_id is None
        assert notification.channel == NotificationChannel.SMS
        assert notification.subject == "Direct SMS"
        assert notification.content == "This is a direct SMS message"
        assert notification.recipient == recipient
        assert notification.status == NotificationStatus.PENDING
    
    async def test_get_notification_by_id(
        self, 
        notification_service: NotificationService,
        sample_template: NotificationTemplate
    ):
        """Test retrieving notification by ID"""
        # Create notification first
        notification = await notification_service.create_notification(
            user_id=uuid.uuid4(),
            template_id=sample_template.id,
            recipient="test@example.com",
            data={"name": "Test User", "action": "test"}
        )
        
        # Retrieve by ID
        found_notification = await notification_service.get_notification_by_id(notification.id)
        
        assert found_notification is not None
        assert found_notification.id == notification.id
        assert found_notification.user_id == notification.user_id
        assert found_notification.template_id == sample_template.id
    
    async def test_get_nonexistent_notification(
        self, 
        notification_service: NotificationService
    ):
        """Test retrieving non-existent notification"""
        non_existent_id = uuid.uuid4()
        
        notification = await notification_service.get_notification_by_id(non_existent_id)
        
        assert notification is None
    
    async def test_get_user_notifications(
        self, 
        notification_service: NotificationService,
        sample_template: NotificationTemplate
    ):
        """Test retrieving notifications for a user"""
        user_id = uuid.uuid4()
        
        # Create multiple notifications for the user
        for i in range(3):
            await notification_service.create_notification(
                user_id=user_id,
                template_id=sample_template.id,
                recipient=f"test{i}@example.com",
                data={"name": f"Test User {i}", "action": "test"}
            )
        
        # Create notification for different user
        different_user_id = uuid.uuid4()
        await notification_service.create_notification(
            user_id=different_user_id,
            template_id=sample_template.id,
            recipient="other@example.com",
            data={"name": "Other User", "action": "test"}
        )
        
        # Get notifications for the first user
        user_notifications = await notification_service.get_user_notifications(
            user_id=user_id
        )
        
        assert len(user_notifications) == 3
        assert all(n.user_id == user_id for n in user_notifications)
    
    async def test_get_user_notifications_by_channel(
        self, 
        notification_service: NotificationService,
        sample_category: NotificationCategory
    ):
        """Test retrieving user notifications filtered by channel"""
        user_id = uuid.uuid4()
        
        # Create notifications with different channels
        await notification_service.create_notification(
            user_id=user_id,
            category_id=sample_category.id,
            channel=NotificationChannel.EMAIL,
            subject="Email notification",
            content="Test email",
            recipient="test@example.com"
        )
        
        await notification_service.create_notification(
            user_id=user_id,
            category_id=sample_category.id,
            channel=NotificationChannel.SMS,
            subject="SMS notification",
            content="Test SMS",
            recipient="+1234567890"
        )
        
        await notification_service.create_notification(
            user_id=user_id,
            category_id=sample_category.id,
            channel=NotificationChannel.PUSH,
            subject="Push notification",
            content="Test push",
            recipient="push-token-123"
        )
        
        # Get only email notifications
        email_notifications = await notification_service.get_user_notifications(
            user_id=user_id,
            channel=NotificationChannel.EMAIL
        )
        
        assert len(email_notifications) == 1
        assert email_notifications[0].channel == NotificationChannel.EMAIL
        assert email_notifications[0].subject == "Email notification"
    
    async def test_update_notification_status(
        self, 
        notification_service: NotificationService,
        sample_template: NotificationTemplate
    ):
        """Test updating notification status"""
        # Create notification
        notification = await notification_service.create_notification(
            user_id=uuid.uuid4(),
            template_id=sample_template.id,
            recipient="test@example.com",
            data={"name": "Test User", "action": "test"}
        )
        
        assert notification.status == NotificationStatus.PENDING
        assert notification.sent_at is None
        
        # Update to sent
        updated_notification = await notification_service.update_notification_status(
            notification_id=notification.id,
            status=NotificationStatus.SENT,
            message_id="external-msg-123"
        )
        
        assert updated_notification.status == NotificationStatus.SENT
        assert updated_notification.sent_at is not None
        assert updated_notification.external_message_id == "external-msg-123"
        assert isinstance(updated_notification.sent_at, datetime)
    
    async def test_update_notification_status_with_error(
        self, 
        notification_service: NotificationService,
        sample_template: NotificationTemplate
    ):
        """Test updating notification status with error"""
        # Create notification
        notification = await notification_service.create_notification(
            user_id=uuid.uuid4(),
            template_id=sample_template.id,
            recipient="test@example.com",
            data={"name": "Test User", "action": "test"}
        )
        
        # Update to failed with error message
        error_message = "SMTP server unavailable"
        updated_notification = await notification_service.update_notification_status(
            notification_id=notification.id,
            status=NotificationStatus.FAILED,
            error_message=error_message
        )
        
        assert updated_notification.status == NotificationStatus.FAILED
        assert updated_notification.error_message == error_message
        assert updated_notification.sent_at is None  # Should not be set for failed
    
    async def test_get_unread_notifications_count(
        self, 
        notification_service: NotificationService,
        sample_category: NotificationCategory
    ):
        """Test getting unread notifications count for user"""
        user_id = uuid.uuid4()
        
        # Create multiple notifications
        for i in range(5):
            await notification_service.create_notification(
                user_id=user_id,
                category_id=sample_category.id,
                channel=NotificationChannel.IN_APP,
                subject=f"Notification {i}",
                content=f"Test notification {i}",
                recipient="in-app"
            )
        
        # Mark some as read
        notifications = await notification_service.get_user_notifications(user_id)
        for i in range(2):  # Mark first 2 as read
            await notification_service.update_notification_status(
                notification_id=notifications[i].id,
                status=NotificationStatus.READ
            )
        
        # Get unread count
        unread_count = await notification_service.get_unread_notifications_count(user_id)
        
        assert unread_count == 3  # 5 total - 2 read = 3 unread
    
    async def test_mark_notifications_as_read(
        self, 
        notification_service: NotificationService,
        sample_category: NotificationCategory
    ):
        """Test marking multiple notifications as read"""
        user_id = uuid.uuid4()
        
        # Create notifications
        notification_ids = []
        for i in range(3):
            notification = await notification_service.create_notification(
                user_id=user_id,
                category_id=sample_category.id,
                channel=NotificationChannel.IN_APP,
                subject=f"Notification {i}",
                content=f"Test notification {i}",
                recipient="in-app"
            )
            notification_ids.append(notification.id)
        
        # Mark all as read
        marked_count = await notification_service.mark_notifications_as_read(
            user_id=user_id,
            notification_ids=notification_ids
        )
        
        assert marked_count == 3
        
        # Verify they are marked as read
        for notification_id in notification_ids:
            notification = await notification_service.get_notification_by_id(notification_id)
            assert notification.status == NotificationStatus.READ
    
    @patch('services.notification_service.TemplateEngine')
    async def test_template_rendering_error_handling(
        self, 
        mock_template_engine,
        notification_service: NotificationService,
        sample_template: NotificationTemplate
    ):
        """Test handling template rendering errors"""
        # Mock template engine to raise error
        mock_engine_instance = MagicMock()
        mock_engine_instance.render.side_effect = Exception("Template rendering failed")
        mock_template_engine.return_value = mock_engine_instance
        
        # Should handle template error gracefully
        with pytest.raises(Exception, match="Template rendering failed"):
            await notification_service.create_notification(
                user_id=uuid.uuid4(),
                template_id=sample_template.id,
                recipient="test@example.com",
                data={"name": "Test User", "action": "test"}
            )


@pytest.mark.unit
@pytest.mark.asyncio
class TestTemplateEngine:
    """Unit tests for TemplateEngine"""
    
    @pytest.fixture
    def template_engine(self):
        """Create TemplateEngine instance"""
        return TemplateEngine()
    
    def test_render_simple_template(self, template_engine: TemplateEngine):
        """Test rendering simple template"""
        template = "Hello {{name}}, welcome to {{platform}}!"
        variables = {"name": "John", "platform": "Our Service"}
        
        result = template_engine.render(template, variables)
        
        assert result == "Hello John, welcome to Our Service!"
    
    def test_render_template_with_missing_variable(self, template_engine: TemplateEngine):
        """Test rendering template with missing variable"""
        template = "Hello {{name}}, your {{action}} was successful."
        variables = {"name": "John"}  # Missing 'action' variable
        
        # Should handle missing variable gracefully
        result = template_engine.render(template, variables)
        
        # Result should contain the placeholder or empty string
        assert "John" in result
        assert "{{action}}" not in result or result.count("{{") == 0
    
    def test_render_template_with_nested_objects(self, template_engine: TemplateEngine):
        """Test rendering template with nested object variables"""
        template = "Hello {{user.name}}, you have {{stats.unread}} unread messages."
        variables = {
            "user": {"name": "John Doe", "email": "john@example.com"},
            "stats": {"unread": 5, "total": 20}
        }
        
        result = template_engine.render(template, variables)
        
        assert "John Doe" in result
        assert "5" in result or "5 unread" in result
    
    def test_validate_template_syntax(self, template_engine: TemplateEngine):
        """Test template syntax validation"""
        valid_template = "Hello {{name}}, welcome!"
        invalid_template = "Hello {{name}, welcome!"  # Missing closing brace
        
        assert template_engine.validate_template(valid_template) is True
        assert template_engine.validate_template(invalid_template) is False
    
    def test_extract_template_variables(self, template_engine: TemplateEngine):
        """Test extracting variables from template"""
        template = "Hello {{name}}, your {{action}} was successful. Visit {{url}}."
        
        variables = template_engine.extract_variables(template)
        
        expected_variables = ["name", "action", "url"]
        assert set(variables) == set(expected_variables)
    
    def test_render_conditional_template(self, template_engine: TemplateEngine):
        """Test rendering template with conditional logic"""
        template = "Hello {{name}}{% if urgent %}, URGENT: {% endif %}{{message}}"
        
        # With urgent flag
        variables_urgent = {"name": "John", "urgent": True, "message": "Action required"}
        result_urgent = template_engine.render(template, variables_urgent)
        assert "URGENT" in result_urgent
        
        # Without urgent flag
        variables_normal = {"name": "John", "urgent": False, "message": "Info message"}
        result_normal = template_engine.render(template, variables_normal)
        assert "URGENT" not in result_normal


@pytest.mark.unit
@pytest.mark.asyncio  
class TestQueueManager:
    """Unit tests for QueueManager"""
    
    @pytest.fixture
    def queue_manager(self, mock_redis):
        """Create QueueManager instance with mocked Redis"""
        return QueueManager(redis_client=mock_redis)
    
    async def test_queue_notification(self, queue_manager: QueueManager, mock_redis):
        """Test queuing notification for processing"""
        notification_data = {
            "notification_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "channel": "email",
            "priority": "normal"
        }
        
        # Mock Redis lpush to return success
        mock_redis.lpush.return_value = 1
        
        result = await queue_manager.queue_notification(notification_data)
        
        assert result is True
        mock_redis.lpush.assert_called_once()
        # Verify the correct queue was used based on priority
        call_args = mock_redis.lpush.call_args
        assert "normal" in str(call_args) or "notifications" in str(call_args)
    
    async def test_queue_high_priority_notification(
        self, 
        queue_manager: QueueManager, 
        mock_redis
    ):
        """Test queuing high priority notification"""
        notification_data = {
            "notification_id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "channel": "sms",
            "priority": "high"
        }
        
        mock_redis.lpush.return_value = 1
        
        result = await queue_manager.queue_notification(notification_data)
        
        assert result is True
        mock_redis.lpush.assert_called_once()
        # High priority should use priority queue
        call_args = mock_redis.lpush.call_args
        assert "high" in str(call_args) or "priority" in str(call_args)
    
    async def test_get_queue_status(self, queue_manager: QueueManager, mock_redis):
        """Test getting queue status"""
        # Mock Redis llen to return queue lengths
        mock_redis.llen.side_effect = [5, 2, 1]  # normal, high, urgent queues
        
        status = await queue_manager.get_queue_status()
        
        assert "normal" in status or "pending" in status
        assert isinstance(status, dict)
        # Should have called llen multiple times for different queues
        assert mock_redis.llen.call_count >= 1
    
    async def test_dequeue_notification(self, queue_manager: QueueManager, mock_redis):
        """Test dequeuing notification from queue"""
        notification_data = {
            "notification_id": str(uuid.uuid4()),
            "channel": "email"
        }
        
        # Mock Redis brpop to return notification data
        mock_redis.brpop.return_value = ("queue_name", str(notification_data).encode())
        
        result = await queue_manager.dequeue_notification()
        
        assert result is not None
        mock_redis.brpop.assert_called_once()
    
    async def test_queue_redis_error_handling(
        self, 
        queue_manager: QueueManager, 
        mock_redis
    ):
        """Test queue error handling when Redis fails"""
        notification_data = {
            "notification_id": str(uuid.uuid4()),
            "channel": "email"
        }
        
        # Mock Redis to raise connection error
        mock_redis.lpush.side_effect = Exception("Redis connection failed")
        
        result = await queue_manager.queue_notification(notification_data)
        
        assert result is False  # Should return False on error
    
    async def test_queue_notification_with_delay(
        self, 
        queue_manager: QueueManager, 
        mock_redis
    ):
        """Test queuing notification with delay"""
        notification_data = {
            "notification_id": str(uuid.uuid4()),
            "channel": "email",
            "delay": 300  # 5 minutes delay
        }
        
        mock_redis.zadd.return_value = 1  # For delayed queue (sorted set)
        
        result = await queue_manager.queue_notification_with_delay(
            notification_data, 
            delay=300
        )
        
        assert result is True
        mock_redis.zadd.assert_called_once()


@pytest.mark.unit
class TestServiceUtilities:
    """Test utility functions and helpers"""
    
    def test_notification_priority_ordering(self):
        """Test notification priority enum ordering"""
        priorities = [
            NotificationPriority.LOW,
            NotificationPriority.NORMAL, 
            NotificationPriority.HIGH,
            NotificationPriority.URGENT
        ]
        
        # Verify priority values can be compared
        assert NotificationPriority.LOW.value == "low"
        assert NotificationPriority.URGENT.value == "urgent"
        
        # Test that we can sort by priority (if implemented)
        priority_values = [p.value for p in priorities]
        assert "low" in priority_values
        assert "urgent" in priority_values
    
    def test_notification_channel_types(self):
        """Test all notification channel types"""
        channels = [
            NotificationChannel.EMAIL,
            NotificationChannel.SMS,
            NotificationChannel.PUSH,
            NotificationChannel.IN_APP
        ]
        
        channel_values = [c.value for c in channels]
        expected_channels = ["email", "sms", "push", "in_app"]
        
        assert set(channel_values) == set(expected_channels)
    
    def test_notification_status_workflow(self):
        """Test notification status workflow"""
        # Define expected status flow
        status_flow = [
            NotificationStatus.PENDING,
            NotificationStatus.SENT,
            NotificationStatus.DELIVERED,
            NotificationStatus.READ
        ]
        
        # Alternative flow to FAILED
        failed_flow = [
            NotificationStatus.PENDING,
            NotificationStatus.FAILED
        ]
        
        # Verify all statuses exist
        for status in status_flow + failed_flow:
            assert hasattr(NotificationStatus, status.name)
            assert isinstance(status.value, str)
    
    @pytest.mark.asyncio
    async def test_service_error_handling_patterns(self):
        """Test common service error handling patterns"""
        # Test with None parameters
        service = NotificationService(db_session=None, cache=None)
        
        # Should handle gracefully or raise appropriate exceptions
        with pytest.raises((AttributeError, TypeError, ValueError)):
            await service.get_notification_by_id(None)