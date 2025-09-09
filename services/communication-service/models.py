"""
Communication Service Database Models
SQLAlchemy models for notifications, messages, conversations, and templates
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, Integer, 
    ForeignKey, JSON, Enum, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum

Base = declarative_base()

class NotificationStatus(enum.Enum):
    """Notification delivery status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"

class NotificationChannel(enum.Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"

class ConversationType(enum.Enum):
    """Conversation types"""
    DIRECT = "direct"
    GROUP = "group"
    SUPPORT = "support"
    SYSTEM = "system"

class MessageType(enum.Enum):
    """Message content types"""
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"
    FILE = "file"
    IMAGE = "image"
    SYSTEM = "system"

class ParticipantRole(enum.Enum):
    """Participant roles in conversations"""
    MEMBER = "member"
    ADMIN = "admin"
    MODERATOR = "moderator"
    READONLY = "readonly"


class NotificationCategory(Base):
    """Categories for organizing notifications"""
    __tablename__ = "notification_categories"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    default_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    notifications = relationship("Notification", back_populates="category")
    templates = relationship("NotificationTemplate", back_populates="category")
    
    def __repr__(self):
        return f"<NotificationCategory(name='{self.name}')>"


class NotificationTemplate(Base):
    """Templates for notifications with variable substitution"""
    __tablename__ = "notification_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("notification_categories.id"))
    channel = Column(Enum(NotificationChannel), nullable=False)
    language = Column(String(10), default="en")
    
    # Template content
    subject = Column(String(500))  # For email/push notifications
    content = Column(Text, nullable=False)
    variables = Column(JSON, default=dict)  # Expected template variables
    
    # Metadata
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    template_metadata = Column(JSON, default=dict)  # Flexible metadata storage
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("NotificationCategory", back_populates="templates")
    notifications = relationship("Notification", back_populates="template")
    
    # Indexes
    __table_args__ = (
        Index("idx_template_category_channel", "category_id", "channel"),
        Index("idx_template_active", "is_active"),
    )
    
    def __repr__(self):
        return f"<NotificationTemplate(name='{self.name}', channel='{self.channel.value}')>"


class Notification(Base):
    """Individual notifications sent to users"""
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # From Identity Service
    
    # Notification details
    category_id = Column(UUID(as_uuid=True), ForeignKey("notification_categories.id"))
    template_id = Column(UUID(as_uuid=True), ForeignKey("notification_templates.id"), nullable=True)
    channel = Column(Enum(NotificationChannel), nullable=False)
    
    # Content
    subject = Column(String(500))
    content = Column(Text, nullable=False)
    data = Column(JSON, default=dict)  # Template variables and custom data
    
    # Delivery
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    recipient = Column(String(255), nullable=False)  # Email, phone, device token
    provider = Column(String(50))  # SendGrid, Twilio, Firebase, etc.
    provider_message_id = Column(String(255))  # External provider's message ID
    
    # Scheduling
    scheduled_at = Column(DateTime, nullable=True)  # For scheduled notifications
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)  # For in-app notifications
    
    # Error handling
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("NotificationCategory", back_populates="notifications")
    template = relationship("NotificationTemplate", back_populates="notifications")
    
    # Indexes
    __table_args__ = (
        Index("idx_notification_user_status", "user_id", "status"),
        Index("idx_notification_scheduled", "scheduled_at"),
        Index("idx_notification_channel", "channel"),
        Index("idx_notification_provider", "provider"),
    )
    
    def __repr__(self):
        return f"<Notification(user_id='{self.user_id}', status='{self.status.value}')>"


class NotificationPreference(Base):
    """User preferences for notification delivery"""
    __tablename__ = "notification_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("notification_categories.id"))
    
    # Channel preferences
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    
    # Contact information
    email_address = Column(String(255))
    phone_number = Column(String(50))
    push_token = Column(Text)  # Device push notification token
    
    # Settings
    quiet_hours_start = Column(String(5))  # HH:MM format
    quiet_hours_end = Column(String(5))  # HH:MM format
    timezone = Column(String(50), default="UTC")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship("NotificationCategory")
    
    # Indexes
    __table_args__ = (
        Index("idx_preference_user_category", "user_id", "category_id"),
    )
    
    def __repr__(self):
        return f"<NotificationPreference(user_id='{self.user_id}')>"


class Conversation(Base):
    """Conversations between users"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Enum(ConversationType), default=ConversationType.DIRECT)
    
    # Content
    subject = Column(String(500))  # Optional subject for group/support conversations
    notification_metadata = Column(JSON, default=dict)  # Flexible metadata (tags, priority, etc.)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_message_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    participants = relationship("ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_conversation_type", "type"),
        Index("idx_conversation_active", "is_active"),
        Index("idx_conversation_last_message", "last_message_at"),
    )
    
    def __repr__(self):
        return f"<Conversation(type='{self.type.value}')>"


class ConversationParticipant(Base):
    """Participants in conversations with roles and status"""
    __tablename__ = "conversation_participants"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # From Identity Service
    
    # Participant status
    role = Column(Enum(ParticipantRole), default=ParticipantRole.MEMBER)
    is_active = Column(Boolean, default=True)
    
    # Activity tracking
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_read_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    
    # Settings
    notifications_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="participants")
    messages = relationship("Message", back_populates="sender")
    
    # Indexes
    __table_args__ = (
        Index("idx_participant_conversation", "conversation_id"),
        Index("idx_participant_user", "user_id"),
        Index("idx_participant_active", "is_active"),
    )
    
    def __repr__(self):
        return f"<ConversationParticipant(user_id='{self.user_id}', role='{self.role.value}')>"


class Message(Base):
    """Messages within conversations"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("conversation_participants.id"), nullable=False)
    
    # Message content
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)
    message_metadata = Column(JSON, default=dict)  # File attachments, formatting, etc.
    
    # Message status
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    edited_at = Column(DateTime)
    deleted_at = Column(DateTime)
    
    # Delivery tracking
    sent_at = Column(DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("ConversationParticipant", back_populates="messages")
    
    # Indexes
    __table_args__ = (
        Index("idx_message_conversation", "conversation_id"),
        Index("idx_message_sender", "sender_id"),
        Index("idx_message_sent", "sent_at"),
        Index("idx_message_type", "message_type"),
    )
    
    def __repr__(self):
        return f"<Message(conversation_id='{self.conversation_id}', type='{self.message_type.value}')>"


# Utility functions for model operations
def create_default_categories():
    """Create default notification categories"""
    default_categories = [
        {"name": "system", "description": "System notifications and alerts", "default_enabled": True},
        {"name": "transactional", "description": "Transaction confirmations and receipts", "default_enabled": True},
        {"name": "marketing", "description": "Marketing campaigns and promotions", "default_enabled": False},
        {"name": "social", "description": "Social interactions and updates", "default_enabled": True},
        {"name": "security", "description": "Security alerts and notifications", "default_enabled": True},
    ]
    return [NotificationCategory(**cat) for cat in default_categories]


def get_user_notification_preferences(db_session, user_id: uuid.UUID) -> Dict[str, Any]:
    """Get user's notification preferences across all categories"""
    preferences = db_session.query(NotificationPreference).filter_by(user_id=user_id).all()
    return {pref.category.name: pref for pref in preferences}


def create_notification(
    db_session,
    user_id: uuid.UUID,
    channel: NotificationChannel,
    content: str,
    category_name: str = "system",
    recipient: Optional[str] = None,
    template_id: Optional[uuid.UUID] = None,
    subject: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    scheduled_at: Optional[datetime] = None
) -> Notification:
    """Create a new notification"""
    category = db_session.query(NotificationCategory).filter_by(name=category_name).first()
    if not category:
        category = NotificationCategory(name=category_name, description=f"{category_name} notifications")
        db_session.add(category)
        db_session.flush()
    
    notification = Notification(
        user_id=user_id,
        category_id=category.id,
        template_id=template_id,
        channel=channel,
        subject=subject,
        content=content,
        data=data or {},
        recipient=recipient,
        scheduled_at=scheduled_at
    )
    
    db_session.add(notification)
    return notification