"""
Enhanced Auth Service Models
Includes user management and basic organizational features
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from enum import Enum

from sqlalchemy import Column, String, Boolean, DateTime, JSON, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING_VERIFICATION = "pending_verification"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class OrganizationType(str, Enum):
    """Organization/tenant types"""
    INDIVIDUAL = "individual"
    SMALL_BUSINESS = "small_business"
    ENTERPRISE = "enterprise"
    NON_PROFIT = "non_profit"


# Enhanced User Model with Profile Management
class User(Base):
    """Enhanced user model with profile and preference management"""
    __tablename__ = "users"
    
    # Core identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(150), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile information
    first_name = Column(String(150), nullable=True)
    last_name = Column(String(150), nullable=True)
    display_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Contact information
    phone_number = Column(String(20), nullable=True)
    secondary_email = Column(String(255), nullable=True)
    
    # Preferences and settings
    language_code = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    theme_preference = Column(String(20), default="light")  # light, dark, auto
    notification_preferences = Column(JSON, default=dict)
    privacy_settings = Column(JSON, default=dict)
    
    # Status and verification
    status = Column(String(30), default=UserStatus.PENDING_VERIFICATION)
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    last_login_at = Column(DateTime, nullable=True)
    last_login_ip = Column(String(45), nullable=True)  # IPv6 compatible
    
    # Organizational relationship
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    activity_logs = relationship("UserActivityLog", back_populates="user")


class Organization(Base):
    """Organization/Tenant management"""
    __tablename__ = "organizations"
    
    # Core identity
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    
    # Organization details
    description = Column(Text, nullable=True)
    website_url = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)
    
    # Contact information
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    
    # Address information
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state_province = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country_code = Column(String(2), nullable=True)  # ISO 3166-1 alpha-2
    
    # Organization metadata
    organization_type = Column(String(30), default=OrganizationType.INDIVIDUAL)
    industry = Column(String(100), nullable=True)
    employee_count_range = Column(String(20), nullable=True)  # "1-10", "11-50", etc.
    
    # Settings and configuration
    settings = Column(JSON, default=dict)
    features = Column(JSON, default=list)  # Enabled features
    customization = Column(JSON, default=dict)  # UI/UX customization
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Subscription/billing info (basic)
    subscription_tier = Column(String(50), default="free")
    trial_ends_at = Column(DateTime, nullable=True)
    billing_email = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="organization")


class UserProfile(Base):
    """Extended user profile information (separate for performance)"""
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    # Professional information
    job_title = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    manager_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Social links
    social_links = Column(JSON, default=dict)  # LinkedIn, Twitter, etc.
    
    # Emergency contact
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relationship = Column(String(100), nullable=True)
    
    # Skills and interests (for matching/recommendations)
    skills = Column(JSON, default=list)
    interests = Column(JSON, default=list)
    certifications = Column(JSON, default=list)
    
    # Activity preferences
    preferred_working_hours = Column(JSON, default=dict)  # {"start": "09:00", "end": "17:00"}
    preferred_communication_methods = Column(JSON, default=list)
    
    # Onboarding and engagement
    onboarding_completed = Column(Boolean, default=False)
    onboarding_step = Column(String(50), nullable=True)
    last_activity_at = Column(DateTime, nullable=True)
    engagement_score = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    manager = relationship("User", foreign_keys=[manager_user_id])


class UserActivityLog(Base):
    """User activity tracking for security and analytics"""
    __tablename__ = "user_activity_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Activity details
    action = Column(String(100), nullable=False, index=True)
    resource = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    
    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Additional context
    event_metadata = Column(JSON, default=dict)
    
    # Result
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="activity_logs")


class UserPreference(Base):
    """User-specific preferences and settings"""
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Preference details
    category = Column(String(50), nullable=False, index=True)  # "notification", "privacy", etc.
    key = Column(String(100), nullable=False, index=True)
    value = Column(JSON, nullable=True)
    
    # Metadata
    description = Column(String(255), nullable=True)
    is_system = Column(Boolean, default=False)  # System vs user-defined
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint
    __table_args__ = (
        {"extend_existing": True}
    )


class UserSession(Base):
    """Enhanced session management"""
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Session tokens
    access_token_jti = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token_jti = Column(String(255), unique=True, nullable=True)
    
    # Device/client information
    device_id = Column(String(255), nullable=True)
    device_name = Column(String(255), nullable=True)  # "iPhone 12", "Chrome on MacBook"
    device_type = Column(String(50), nullable=True)   # "mobile", "desktop", "tablet"
    
    # Location information
    ip_address = Column(String(45), nullable=False)
    country_code = Column(String(2), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Session metadata
    user_agent = Column(Text, nullable=True)
    browser = Column(String(100), nullable=True)
    operating_system = Column(String(100), nullable=True)
    
    # Session status
    is_active = Column(Boolean, default=True, index=True)
    revocation_reason = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")


# Multi-Factor Authentication Models
class MFAMethod(Base):
    """Multi-factor authentication methods"""
    __tablename__ = "mfa_methods"
    
    METHOD_CHOICES = [
        ('email', 'Email Verification'),
        ('sms', 'SMS Verification'),
        ('totp', 'Time-based OTP (Authenticator App)'),
        ('backup_codes', 'Backup Codes'),
        ('webauthn', 'WebAuthn/Passkey'),
    ]
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Method configuration
    method_type = Column(String(20), nullable=False, index=True)
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # Method-specific data (encrypted in production)
    secret = Column(String(255), nullable=True)  # TOTP secret, backup codes
    phone_number = Column(String(20), nullable=True)  # SMS destination
    email = Column(String(255), nullable=True)  # Email destination
    
    # WebAuthn/Passkey data (future)
    credential_id = Column(String(255), nullable=True)
    public_key = Column(Text, nullable=True)
    
    # Status and usage
    verified_at = Column(DateTime, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    failure_count = Column(Integer, default=0)
    
    # Metadata
    device_name = Column(String(255), nullable=True)  # "iPhone 12", "Google Authenticator"
    setup_metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="mfa_methods")
    
    # Constraints
    __table_args__ = (
        # User can have one method of each type
        {"extend_existing": True}
    )


class MFAChallenge(Base):
    """Temporary MFA challenges (email/SMS codes)"""
    __tablename__ = "mfa_challenges"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    mfa_method_id = Column(UUID(as_uuid=True), ForeignKey("mfa_methods.id"), nullable=False)
    
    # Challenge details
    challenge_type = Column(String(20), nullable=False)  # 'email', 'sms'
    destination = Column(String(255), nullable=False)  # Where code was sent
    code_hash = Column(String(255), nullable=False)  # Hashed verification code
    
    # Challenge status
    attempts_used = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    is_used = Column(Boolean, default=False)
    
    # Session context
    session_id = Column(UUID(as_uuid=True), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Expiry
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User")
    mfa_method = relationship("MFAMethod")


class PasswordReset(Base):
    """Password reset tokens and email verification"""
    __tablename__ = "password_resets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Reset details
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False)  # Email where reset was sent
    
    # Status
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    
    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Expiry
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationships
    user = relationship("User")


class EmailVerification(Base):
    """Email verification tokens"""
    __tablename__ = "email_verifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Verification details
    email = Column(String(255), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    verification_type = Column(String(30), default="account_verification")
    
    # Status
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    
    # Request context  
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Expiry
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationships
    user = relationship("User")


# Keep existing auth models (Role, Permission, etc.) from original models.py
# This extends rather than replaces the core authentication functionality