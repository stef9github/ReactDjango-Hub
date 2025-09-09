"""
Simplified Database Models for Auth Service - Working Version
Core functionality without complex relationships
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

# User Status Enum
class UserStatus:
    PENDING_VERIFICATION = "pending_verification"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"

# Core Models
class User(Base):
    __tablename__ = "users_simple"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    status = Column(String(30), default=UserStatus.PENDING_VERIFICATION)
    
    # Personal Information
    first_name = Column(String(150))
    last_name = Column(String(150))
    phone_number = Column(String(20))
    
    # Profile Information
    bio = Column(Text)
    avatar_url = Column(String(500))
    timezone = Column(String(50), default='UTC')
    language = Column(String(10), default='en')
    
    # Account Management
    last_login_at = Column(DateTime)
    password_changed_at = Column(DateTime, default=datetime.utcnow)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)
    
    # Simple relationships
    email_verifications = relationship("EmailVerification", back_populates="user", cascade="all, delete-orphan")
    user_sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    user_activities = relationship("UserActivity", back_populates="user", cascade="all, delete-orphan")

class EmailVerification(Base):
    __tablename__ = "email_verifications_simple"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users_simple.id"), nullable=False)
    email = Column(String(255), nullable=False)
    
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    verification_type = Column(String(30), default='account_verification')
    
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="email_verifications")

class UserSession(Base):
    __tablename__ = "user_sessions_simple"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users_simple.id"), nullable=False)
    
    # Session Information
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Device Information
    device_name = Column(String(255))
    device_type = Column(String(50))  
    user_agent = Column(Text)
    ip_address = Column(String(45))
    
    # Location (approximate)
    country = Column(String(100))
    region = Column(String(100))
    city = Column(String(100))
    
    # Session Status
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="user_sessions")

class UserActivity(Base):
    __tablename__ = "user_activities_simple"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users_simple.id"), nullable=False)
    
    # Activity Information
    activity_type = Column(String(50), nullable=False)
    description = Column(Text)
    
    # Context
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Metadata (JSON)
    activity_metadata = Column(Text)  # JSON string for additional data
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_activities")