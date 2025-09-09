"""
Unit tests for notification models
Tests model creation, validation, relationships, and methods
"""

import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from models import (
    NotificationCategory, NotificationTemplate, Notification,
    NotificationChannel, NotificationStatus, NotificationPriority
)

@pytest.mark.unit
@pytest.mark.asyncio
class TestNotificationCategory:
    """Unit tests for NotificationCategory model"""
    
    async def test_create_notification_category(self, db_session: AsyncSession):
        """Test creating a notification category"""
        category_data = {
            "name": "test_category",
            "description": "Test category for notifications",
            "default_enabled": True,
            "color": "#FF0000"
        }
        
        category = NotificationCategory(**category_data)
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)
        
        assert category.id is not None
        assert category.name == "test_category"
        assert category.description == "Test category for notifications"
        assert category.default_enabled is True
        assert category.color == "#FF0000"
        assert category.created_at is not None
        assert isinstance(category.created_at, datetime)
        assert category.updated_at is not None
    
    async def test_category_name_uniqueness(self, db_session: AsyncSession):
        """Test that category names must be unique"""
        # Create first category
        category1 = NotificationCategory(
            name="unique_category",
            description="First category"
        )
        db_session.add(category1)
        await db_session.commit()
        
        # Try to create second category with same name
        category2 = NotificationCategory(
            name="unique_category",
            description="Second category"
        )
        db_session.add(category2)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    async def test_category_default_values(self, db_session: AsyncSession):
        """Test default values for category"""
        category = NotificationCategory(
            name="default_test",
            description="Test default values"
        )
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)
        
        assert category.default_enabled is True  # Default should be True
        assert category.color is None  # Default should be None


@pytest.mark.unit
@pytest.mark.asyncio
class TestNotificationTemplate:
    """Unit tests for NotificationTemplate model"""
    
    @pytest.fixture
    async def test_category(self, db_session: AsyncSession):
        """Create a test category for templates"""
        category = NotificationCategory(
            name="template_test_category",
            description="Category for template tests"
        )
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)
        return category
    
    async def test_create_notification_template(self, db_session: AsyncSession, test_category):
        """Test creating a notification template"""
        template_data = {
            "name": "welcome_email",
            "category_id": test_category.id,
            "channel": NotificationChannel.EMAIL,
            "language": "en",
            "subject": "Welcome {{name}}!",
            "content": "Hello {{name}}, welcome to our platform!",
            "variables": {"name": "string", "email": "string"}
        }
        
        template = NotificationTemplate(**template_data)
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)
        
        assert template.id is not None
        assert template.name == "welcome_email"
        assert template.category_id == test_category.id
        assert template.channel == NotificationChannel.EMAIL
        assert template.language == "en"
        assert template.subject == "Welcome {{name}}!"
        assert template.content == "Hello {{name}}, welcome to our platform!"
        assert template.variables == {"name": "string", "email": "string"}
        assert template.created_at is not None
    
    async def test_template_category_relationship(self, db_session: AsyncSession, test_category):
        """Test template-category relationship"""
        template = NotificationTemplate(
            name="relationship_test",
            category_id=test_category.id,
            channel=NotificationChannel.SMS,
            language="en",
            content="Test message"
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)
        
        # Test relationship
        assert template.category is not None
        assert template.category.id == test_category.id
        assert template.category.name == "template_test_category"
    
    async def test_template_channel_validation(self, db_session: AsyncSession, test_category):
        """Test that template channel is properly validated"""
        template = NotificationTemplate(
            name="channel_test",
            category_id=test_category.id,
            channel=NotificationChannel.PUSH,
            language="en",
            content="Test notification"
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)
        
        assert template.channel == NotificationChannel.PUSH
        assert isinstance(template.channel, NotificationChannel)


@pytest.mark.unit
@pytest.mark.asyncio
class TestNotification:
    """Unit tests for Notification model"""
    
    @pytest.fixture
    async def test_setup(self, db_session: AsyncSession):
        """Setup test category and template"""
        category = NotificationCategory(
            name="notification_test_category",
            description="Category for notification tests"
        )
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)
        
        template = NotificationTemplate(
            name="test_template",
            category_id=category.id,
            channel=NotificationChannel.EMAIL,
            language="en",
            subject="Test Subject",
            content="Test content with {{name}}"
        )
        db_session.add(template)
        await db_session.commit()
        await db_session.refresh(template)
        
        return {"category": category, "template": template}
    
    async def test_create_notification(self, db_session: AsyncSession, test_setup):
        """Test creating a notification"""
        notification_data = {
            "user_id": uuid.uuid4(),
            "category_id": test_setup["category"].id,
            "template_id": test_setup["template"].id,
            "channel": NotificationChannel.EMAIL,
            "subject": "Welcome John!",
            "content": "Hello John, welcome to our platform!",
            "recipient": "john@example.com",
            "data": {"name": "John", "action": "welcome"},
            "priority": NotificationPriority.NORMAL,
            "status": NotificationStatus.PENDING
        }
        
        notification = Notification(**notification_data)
        db_session.add(notification)
        await db_session.commit()
        await db_session.refresh(notification)
        
        assert notification.id is not None
        assert notification.user_id == notification_data["user_id"]
        assert notification.category_id == test_setup["category"].id
        assert notification.template_id == test_setup["template"].id
        assert notification.channel == NotificationChannel.EMAIL
        assert notification.subject == "Welcome John!"
        assert notification.content == "Hello John, welcome to our platform!"
        assert notification.recipient == "john@example.com"
        assert notification.data == {"name": "John", "action": "welcome"}
        assert notification.priority == NotificationPriority.NORMAL
        assert notification.status == NotificationStatus.PENDING
        assert notification.created_at is not None
    
    async def test_notification_relationships(self, db_session: AsyncSession, test_setup):
        """Test notification relationships"""
        notification = Notification(
            user_id=uuid.uuid4(),
            category_id=test_setup["category"].id,
            template_id=test_setup["template"].id,
            channel=NotificationChannel.EMAIL,
            subject="Relationship Test",
            content="Test content",
            recipient="test@example.com",
            status=NotificationStatus.PENDING
        )
        db_session.add(notification)
        await db_session.commit()
        await db_session.refresh(notification)
        
        # Test category relationship
        assert notification.category is not None
        assert notification.category.id == test_setup["category"].id
        assert notification.category.name == "notification_test_category"
        
        # Test template relationship
        assert notification.template is not None
        assert notification.template.id == test_setup["template"].id
        assert notification.template.name == "test_template"
    
    async def test_notification_status_transitions(self, db_session: AsyncSession, test_setup):
        """Test notification status transitions"""
        notification = Notification(
            user_id=uuid.uuid4(),
            category_id=test_setup["category"].id,
            template_id=test_setup["template"].id,
            channel=NotificationChannel.EMAIL,
            subject="Status Test",
            content="Test content",
            recipient="test@example.com",
            status=NotificationStatus.PENDING
        )
        db_session.add(notification)
        await db_session.commit()
        await db_session.refresh(notification)
        
        # Test initial status
        assert notification.status == NotificationStatus.PENDING
        assert notification.sent_at is None
        
        # Update to sent
        notification.status = NotificationStatus.SENT
        notification.sent_at = datetime.utcnow()
        await db_session.commit()
        await db_session.refresh(notification)
        
        assert notification.status == NotificationStatus.SENT
        assert notification.sent_at is not None
        assert isinstance(notification.sent_at, datetime)
        
        # Update to failed
        notification.status = NotificationStatus.FAILED
        notification.error_message = "SMTP server unavailable"
        await db_session.commit()
        await db_session.refresh(notification)
        
        assert notification.status == NotificationStatus.FAILED
        assert notification.error_message == "SMTP server unavailable"
    
    async def test_notification_priority_levels(self, db_session: AsyncSession, test_setup):
        """Test different notification priority levels"""
        priorities = [
            NotificationPriority.LOW,
            NotificationPriority.NORMAL,
            NotificationPriority.HIGH,
            NotificationPriority.URGENT
        ]
        
        for priority in priorities:
            notification = Notification(
                user_id=uuid.uuid4(),
                category_id=test_setup["category"].id,
                template_id=test_setup["template"].id,
                channel=NotificationChannel.EMAIL,
                subject=f"Priority {priority.value} Test",
                content="Test content",
                recipient="test@example.com",
                priority=priority,
                status=NotificationStatus.PENDING
            )
            db_session.add(notification)
        
        await db_session.commit()
        
        # Verify all notifications were created with correct priorities
        from sqlalchemy import select
        result = await db_session.execute(
            select(Notification).where(Notification.subject.like("Priority % Test"))
        )
        notifications = result.scalars().all()
        
        assert len(notifications) == 4
        created_priorities = [n.priority for n in notifications]
        assert set(created_priorities) == set(priorities)
    
    async def test_notification_channel_validation(self, db_session: AsyncSession, test_setup):
        """Test notification channel validation"""
        channels = [
            NotificationChannel.EMAIL,
            NotificationChannel.SMS,
            NotificationChannel.PUSH,
            NotificationChannel.IN_APP
        ]
        
        for channel in channels:
            notification = Notification(
                user_id=uuid.uuid4(),
                category_id=test_setup["category"].id,
                template_id=test_setup["template"].id,
                channel=channel,
                subject=f"Channel {channel.value} Test",
                content="Test content",
                recipient="test@example.com",
                status=NotificationStatus.PENDING
            )
            db_session.add(notification)
        
        await db_session.commit()
        
        # Verify all notifications were created with correct channels
        from sqlalchemy import select
        result = await db_session.execute(
            select(Notification).where(Notification.subject.like("Channel % Test"))
        )
        notifications = result.scalars().all()
        
        assert len(notifications) == 4
        created_channels = [n.channel for n in notifications]
        assert set(created_channels) == set(channels)
    
    async def test_notification_data_json_field(self, db_session: AsyncSession, test_setup):
        """Test notification data JSON field storage and retrieval"""
        complex_data = {
            "user_info": {
                "name": "John Doe",
                "email": "john@example.com",
                "preferences": {
                    "language": "en",
                    "timezone": "UTC"
                }
            },
            "action_data": {
                "action_type": "purchase",
                "amount": 99.99,
                "currency": "USD",
                "items": ["item1", "item2", "item3"]
            },
            "metadata": {
                "source": "web_app",
                "version": "1.2.3",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
        
        notification = Notification(
            user_id=uuid.uuid4(),
            category_id=test_setup["category"].id,
            template_id=test_setup["template"].id,
            channel=NotificationChannel.EMAIL,
            subject="JSON Data Test",
            content="Test content",
            recipient="test@example.com",
            data=complex_data,
            status=NotificationStatus.PENDING
        )
        db_session.add(notification)
        await db_session.commit()
        await db_session.refresh(notification)
        
        # Verify JSON data is properly stored and retrieved
        assert notification.data == complex_data
        assert notification.data["user_info"]["name"] == "John Doe"
        assert notification.data["action_data"]["amount"] == 99.99
        assert notification.data["metadata"]["source"] == "web_app"
        assert len(notification.data["action_data"]["items"]) == 3


@pytest.mark.unit
class TestModelEnums:
    """Test model enum values"""
    
    def test_notification_channel_values(self):
        """Test NotificationChannel enum values"""
        assert NotificationChannel.EMAIL.value == "email"
        assert NotificationChannel.SMS.value == "sms"
        assert NotificationChannel.PUSH.value == "push"
        assert NotificationChannel.IN_APP.value == "in_app"
    
    def test_notification_status_values(self):
        """Test NotificationStatus enum values"""
        assert NotificationStatus.PENDING.value == "pending"
        assert NotificationStatus.SENT.value == "sent"
        assert NotificationStatus.DELIVERED.value == "delivered"
        assert NotificationStatus.FAILED.value == "failed"
        assert NotificationStatus.READ.value == "read"
    
    def test_notification_priority_values(self):
        """Test NotificationPriority enum values"""
        assert NotificationPriority.LOW.value == "low"
        assert NotificationPriority.NORMAL.value == "normal"
        assert NotificationPriority.HIGH.value == "high"
        assert NotificationPriority.URGENT.value == "urgent"


@pytest.mark.unit
@pytest.mark.asyncio
class TestModelEdgeCases:
    """Test edge cases and error conditions"""
    
    async def test_notification_without_template(self, db_session: AsyncSession):
        """Test creating notification without template"""
        category = NotificationCategory(
            name="no_template_category",
            description="Category for no template test"
        )
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)
        
        notification = Notification(
            user_id=uuid.uuid4(),
            category_id=category.id,
            template_id=None,  # No template
            channel=NotificationChannel.EMAIL,
            subject="No Template Test",
            content="Direct content without template",
            recipient="test@example.com",
            status=NotificationStatus.PENDING
        )
        db_session.add(notification)
        await db_session.commit()
        await db_session.refresh(notification)
        
        assert notification.template_id is None
        assert notification.template is None
        assert notification.subject == "No Template Test"
        assert notification.content == "Direct content without template"
    
    async def test_notification_large_data_field(self, db_session: AsyncSession):
        """Test notification with large data field"""
        category = NotificationCategory(
            name="large_data_category",
            description="Category for large data test"
        )
        db_session.add(category)
        await db_session.commit()
        await db_session.refresh(category)
        
        # Create large data object
        large_data = {
            "large_array": [f"item_{i}" for i in range(1000)],
            "nested_object": {
                f"key_{i}": f"value_{i}" for i in range(100)
            },
            "description": "A" * 1000  # 1000 character string
        }
        
        notification = Notification(
            user_id=uuid.uuid4(),
            category_id=category.id,
            template_id=None,
            channel=NotificationChannel.EMAIL,
            subject="Large Data Test",
            content="Test with large data",
            recipient="test@example.com",
            data=large_data,
            status=NotificationStatus.PENDING
        )
        db_session.add(notification)
        await db_session.commit()
        await db_session.refresh(notification)
        
        # Verify large data is properly stored
        assert len(notification.data["large_array"]) == 1000
        assert len(notification.data["nested_object"]) == 100
        assert len(notification.data["description"]) == 1000
        assert notification.data["large_array"][999] == "item_999"