"""
Tests for Communication Service database models
"""
import pytest
import uuid
from datetime import datetime
from sqlalchemy.exc import IntegrityError

from models import (
    NotificationCategory, NotificationTemplate, Notification, 
    NotificationPreference, Conversation, ConversationParticipant, Message,
    NotificationStatus, NotificationChannel, ConversationType, MessageType, 
    ParticipantRole, create_notification, get_user_notification_preferences
)

class TestNotificationCategory:
    """Test NotificationCategory model"""
    
    def test_create_category(self, db_session):
        """Test creating a notification category"""
        category = NotificationCategory(
            name="test_category",
            description="Test category",
            default_enabled=True
        )
        db_session.add(category)
        db_session.commit()
        
        assert category.id is not None
        assert category.name == "test_category"
        assert category.description == "Test category"
        assert category.default_enabled is True
        assert category.created_at is not None
        assert category.updated_at is not None
    
    def test_category_unique_name(self, db_session):
        """Test that category names must be unique"""
        category1 = NotificationCategory(name="unique_name")
        category2 = NotificationCategory(name="unique_name")
        
        db_session.add(category1)
        db_session.commit()
        
        db_session.add(category2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_category_str_representation(self, db_session):
        """Test string representation of category"""
        category = NotificationCategory(name="test_repr")
        assert "test_repr" in str(category)

class TestNotificationTemplate:
    """Test NotificationTemplate model"""
    
    def test_create_template(self, db_session, sample_notification_category):
        """Test creating a notification template"""
        template = NotificationTemplate(
            name="test_template",
            category_id=sample_notification_category.id,
            channel=NotificationChannel.EMAIL,
            language="en",
            subject="Test Subject",
            content="Hello {{name}}",
            variables={"name": "string"}
        )
        db_session.add(template)
        db_session.commit()
        
        assert template.id is not None
        assert template.name == "test_template"
        assert template.channel == NotificationChannel.EMAIL
        assert template.language == "en"
        assert template.subject == "Test Subject"
        assert template.content == "Hello {{name}}"
        assert template.variables == {"name": "string"}
        assert template.version == 1
        assert template.is_active is True
    
    def test_template_category_relationship(self, db_session, sample_notification_template):
        """Test template-category relationship"""
        assert sample_notification_template.category is not None
        assert sample_notification_template.category.name == "test_category"

class TestNotification:
    """Test Notification model"""
    
    def test_create_notification(self, db_session, sample_notification_category):
        """Test creating a notification"""
        user_id = uuid.uuid4()
        notification = Notification(
            user_id=user_id,
            category_id=sample_notification_category.id,
            channel=NotificationChannel.EMAIL,
            subject="Test",
            content="Test notification",
            recipient="test@example.com",
            status=NotificationStatus.PENDING
        )
        db_session.add(notification)
        db_session.commit()
        
        assert notification.id is not None
        assert notification.user_id == user_id
        assert notification.channel == NotificationChannel.EMAIL
        assert notification.status == NotificationStatus.PENDING
        assert notification.recipient == "test@example.com"
        assert notification.retry_count == 0
        assert notification.max_retries == 3
    
    def test_notification_helper_function(self, db_session):
        """Test create_notification helper function"""
        user_id = uuid.uuid4()
        notification = create_notification(
            db_session=db_session,
            user_id=user_id,
            channel=NotificationChannel.EMAIL,
            content="Test content",
            recipient="test@example.com",
            category_name="system"
        )
        
        assert notification.user_id == user_id
        assert notification.channel == NotificationChannel.EMAIL
        assert notification.content == "Test content"
        assert notification.recipient == "test@example.com"
        assert notification.category.name == "system"

class TestNotificationPreference:
    """Test NotificationPreference model"""
    
    def test_create_preference(self, db_session, sample_notification_category):
        """Test creating notification preferences"""
        user_id = uuid.uuid4()
        preference = NotificationPreference(
            user_id=user_id,
            category_id=sample_notification_category.id,
            email_enabled=True,
            sms_enabled=False,
            push_enabled=True,
            in_app_enabled=True,
            email_address="user@example.com",
            phone_number="+1234567890",
            timezone="US/Pacific"
        )
        db_session.add(preference)
        db_session.commit()
        
        assert preference.id is not None
        assert preference.user_id == user_id
        assert preference.email_enabled is True
        assert preference.sms_enabled is False
        assert preference.email_address == "user@example.com"
        assert preference.phone_number == "+1234567890"
        assert preference.timezone == "US/Pacific"
    
    def test_get_user_preferences_helper(self, db_session):
        """Test get_user_notification_preferences helper function"""
        user_id = uuid.uuid4()
        
        # Create category and preference
        category = NotificationCategory(name="test_pref_category")
        db_session.add(category)
        db_session.flush()
        
        preference = NotificationPreference(
            user_id=user_id,
            category_id=category.id,
            email_enabled=True
        )
        db_session.add(preference)
        db_session.commit()
        
        preferences = get_user_notification_preferences(db_session, user_id)
        assert "test_pref_category" in preferences
        assert preferences["test_pref_category"].email_enabled is True

class TestConversation:
    """Test Conversation model"""
    
    def test_create_conversation(self, db_session):
        """Test creating a conversation"""
        conversation = Conversation(
            type=ConversationType.DIRECT,
            subject="Test conversation",
            metadata={"priority": "high"}
        )
        db_session.add(conversation)
        db_session.commit()
        
        assert conversation.id is not None
        assert conversation.type == ConversationType.DIRECT
        assert conversation.subject == "Test conversation"
        assert conversation.metadata == {"priority": "high"}
        assert conversation.is_active is True
        assert conversation.is_archived is False

class TestConversationParticipant:
    """Test ConversationParticipant model"""
    
    def test_create_participant(self, db_session):
        """Test creating a conversation participant"""
        # Create conversation first
        conversation = Conversation(type=ConversationType.GROUP)
        db_session.add(conversation)
        db_session.flush()
        
        user_id = uuid.uuid4()
        participant = ConversationParticipant(
            conversation_id=conversation.id,
            user_id=user_id,
            role=ParticipantRole.ADMIN,
            notifications_enabled=True
        )
        db_session.add(participant)
        db_session.commit()
        
        assert participant.id is not None
        assert participant.conversation_id == conversation.id
        assert participant.user_id == user_id
        assert participant.role == ParticipantRole.ADMIN
        assert participant.is_active is True
        assert participant.notifications_enabled is True
    
    def test_participant_conversation_relationship(self, db_session):
        """Test participant-conversation relationship"""
        conversation = Conversation(type=ConversationType.GROUP)
        user_id = uuid.uuid4()
        participant = ConversationParticipant(
            conversation=conversation,
            user_id=user_id,
            role=ParticipantRole.MEMBER
        )
        
        db_session.add(conversation)
        db_session.add(participant)
        db_session.commit()
        
        assert participant.conversation == conversation
        assert conversation.participants[0] == participant

class TestMessage:
    """Test Message model"""
    
    def test_create_message(self, db_session):
        """Test creating a message"""
        # Create conversation and participant
        conversation = Conversation(type=ConversationType.DIRECT)
        db_session.add(conversation)
        db_session.flush()
        
        user_id = uuid.uuid4()
        participant = ConversationParticipant(
            conversation_id=conversation.id,
            user_id=user_id,
            role=ParticipantRole.MEMBER
        )
        db_session.add(participant)
        db_session.flush()
        
        # Create message
        message = Message(
            conversation_id=conversation.id,
            sender_id=participant.id,
            content="Test message",
            message_type=MessageType.TEXT,
            metadata={"formatted": True}
        )
        db_session.add(message)
        db_session.commit()
        
        assert message.id is not None
        assert message.conversation_id == conversation.id
        assert message.sender_id == participant.id
        assert message.content == "Test message"
        assert message.message_type == MessageType.TEXT
        assert message.metadata == {"formatted": True}
        assert message.is_edited is False
        assert message.is_deleted is False
    
    def test_message_relationships(self, db_session):
        """Test message relationships"""
        conversation = Conversation(type=ConversationType.DIRECT)
        user_id = uuid.uuid4()
        participant = ConversationParticipant(
            conversation=conversation,
            user_id=user_id,
            role=ParticipantRole.MEMBER
        )
        message = Message(
            conversation=conversation,
            sender=participant,
            content="Test message",
            message_type=MessageType.TEXT
        )
        
        db_session.add(conversation)
        db_session.add(participant)
        db_session.add(message)
        db_session.commit()
        
        assert message.conversation == conversation
        assert message.sender == participant
        assert conversation.messages[0] == message
        assert participant.messages[0] == message

class TestModelEnums:
    """Test model enums"""
    
    def test_notification_status_enum(self):
        """Test NotificationStatus enum values"""
        assert NotificationStatus.PENDING.value == "pending"
        assert NotificationStatus.QUEUED.value == "queued"
        assert NotificationStatus.SENT.value == "sent"
        assert NotificationStatus.DELIVERED.value == "delivered"
        assert NotificationStatus.FAILED.value == "failed"
        assert NotificationStatus.CANCELLED.value == "cancelled"
    
    def test_notification_channel_enum(self):
        """Test NotificationChannel enum values"""
        assert NotificationChannel.EMAIL.value == "email"
        assert NotificationChannel.SMS.value == "sms"
        assert NotificationChannel.PUSH.value == "push"
        assert NotificationChannel.IN_APP.value == "in_app"
    
    def test_conversation_type_enum(self):
        """Test ConversationType enum values"""
        assert ConversationType.DIRECT.value == "direct"
        assert ConversationType.GROUP.value == "group"
        assert ConversationType.SUPPORT.value == "support"
        assert ConversationType.SYSTEM.value == "system"
    
    def test_message_type_enum(self):
        """Test MessageType enum values"""
        assert MessageType.TEXT.value == "text"
        assert MessageType.HTML.value == "html"
        assert MessageType.MARKDOWN.value == "markdown"
        assert MessageType.FILE.value == "file"
        assert MessageType.IMAGE.value == "image"
        assert MessageType.SYSTEM.value == "system"
    
    def test_participant_role_enum(self):
        """Test ParticipantRole enum values"""
        assert ParticipantRole.MEMBER.value == "member"
        assert ParticipantRole.ADMIN.value == "admin"
        assert ParticipantRole.MODERATOR.value == "moderator"
        assert ParticipantRole.READONLY.value == "readonly"