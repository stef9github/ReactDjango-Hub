"""
Enhanced Database Models for Auth Service
Complete implementation with User Management, Organization Management, MFA, and Security
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

# Core Authentication Models
class User(Base):
    __tablename__ = "users"

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
    
    # Relationships
    user_sessions = relationship("UserSession", back_populates="user")
    user_roles = relationship("UserRole", back_populates="user")
    user_organizations = relationship("UserOrganization", back_populates="user")
    mfa_methods = relationship("MFAMethod", back_populates="user")
    email_verifications = relationship("EmailVerification", back_populates="user")
    user_activities = relationship("UserActivity", back_populates="user")

class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200))
    description = Column(Text)
    is_system = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user_roles = relationship("UserRole", back_populates="role")
    role_permissions = relationship("RolePermission", back_populates="role")

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200))
    description = Column(Text)
    resource = Column(String(100))  # e.g., 'user', 'organization', 'billing'
    action = Column(String(50))     # e.g., 'create', 'read', 'update', 'delete'
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission")

class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="user_roles", foreign_keys=[user_id])
    role = relationship("Role", back_populates="user_roles")
    organization = relationship("Organization", foreign_keys=[organization_id])
    granted_by_user = relationship("User", foreign_keys=[granted_by], post_update=True)

class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")

# Organization Management Models
class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    display_name = Column(String(255))
    description = Column(Text)
    website = Column(String(500))
    
    # Contact Information
    email = Column(String(255))
    phone = Column(String(20))
    
    # Address
    address_line1 = Column(String(255))
    address_line2 = Column(String(255))
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    postal_code = Column(String(20))
    
    # Settings
    timezone = Column(String(50), default='UTC')
    currency = Column(String(10), default='USD')
    language = Column(String(10), default='en')
    
    # Status
    status = Column(String(30), default='active')  # active, suspended, inactive
    subscription_tier = Column(String(50), default='basic')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)
    
    # Relationships
    user_organizations = relationship("UserOrganization", back_populates="organization")

class UserOrganization(Base):
    __tablename__ = "user_organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    role = Column(String(50), default='member')  # owner, admin, member
    status = Column(String(30), default='active')  # active, invited, suspended
    
    joined_at = Column(DateTime, default=datetime.utcnow)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Relationships
    user = relationship("User", back_populates="user_organizations", foreign_keys=[user_id])
    organization = relationship("Organization", back_populates="user_organizations")
    invited_by_user = relationship("User", foreign_keys=[invited_by], post_update=True)

# Enhanced Session Management
class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Session Information
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Device Information
    device_name = Column(String(255))
    device_type = Column(String(50))  # web, mobile, desktop
    user_agent = Column(Text)
    ip_address = Column(String(45))  # Supports IPv6
    
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

# Multi-Factor Authentication
class MFAMethod(Base):
    __tablename__ = "mfa_methods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    method_type = Column(String(20), nullable=False)  # email, sms, totp, backup_codes
    identifier = Column(String(255))  # email address, phone number, or TOTP secret
    is_verified = Column(Boolean, default=False)
    is_primary = Column(Boolean, default=False)
    
    # TOTP specific
    secret_key = Column(String(255))  # Base32 encoded secret for TOTP
    
    # Backup codes
    backup_codes = Column(Text)  # JSON array of backup codes
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="mfa_methods")

class MFAChallenge(Base):
    __tablename__ = "mfa_challenges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    challenge_type = Column(String(20), nullable=False)  # email, sms, totp
    code_hash = Column(String(255), nullable=False)  # Hashed verification code
    
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    # Metadata
    ip_address = Column(String(45))
    user_agent = Column(Text)

# Email Verification
class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    email = Column(String(255), nullable=False)
    
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    verification_type = Column(String(30), default='account_verification')  # account_verification, password_reset
    
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="email_verifications")

# User Activity Tracking
class UserActivity(Base):
    __tablename__ = "user_activities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Activity Information
    activity_type = Column(String(50), nullable=False)  # login, logout, password_change, profile_update
    description = Column(Text)
    
    # Context
    ip_address = Column(String(45))
    user_agent = Column(Text)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    
    # Metadata (JSON)
    activity_metadata = Column(Text)  # JSON string for additional data
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_activities")
    organization = relationship("Organization", foreign_keys=[organization_id])

# Audit Log
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Actor Information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"))
    
    # Event Information
    event_type = Column(String(50), nullable=False)
    resource_type = Column(String(50))  # user, organization, role, permission
    resource_id = Column(UUID(as_uuid=True))
    
    # Changes
    action = Column(String(20), nullable=False)  # create, update, delete, access
    old_values = Column(Text)  # JSON string of old values
    new_values = Column(Text)  # JSON string of new values
    
    # Context
    ip_address = Column(String(45))
    user_agent = Column(Text)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    
    # Security
    risk_score = Column(Integer, default=0)  # 0-100, higher = more suspicious
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    session = relationship("UserSession", foreign_keys=[session_id])
    organization = relationship("Organization", foreign_keys=[organization_id])