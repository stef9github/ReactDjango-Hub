"""
Flexible authentication system models for ReactDjango Hub.
Supports multi-tenancy, dynamic roles, and extensible permissions.
"""

import uuid
from datetime import timedelta
from typing import Optional, List, Dict, Any

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError


class Tenant(models.Model):
    """Multi-tenant organization model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    domain = models.CharField(max_length=255, blank=True)
    
    # Configuration
    settings = models.JSONField(default=dict, blank=True)
    features = models.JSONField(default=list, blank=True)  # Enabled features
    
    # Status
    is_active = models.BooleanField(default=True)
    subscription_tier = models.CharField(max_length=50, default='free')
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_tenants'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email: str, password: Optional[str] = None, 
                   **extra_fields) -> 'User':
        """Create and save a regular user"""
        if not email:
            raise ValueError('Email address is required')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email: str, password: str, 
                        **extra_fields) -> 'User':
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Extended user model with multi-tenant support"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Authentication fields
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(
        max_length=150, 
        unique=True, 
        null=True, 
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Username may only contain letters, numbers, and @/./+/-/_ characters.'
            )
        ]
    )
    
    # Profile fields
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    display_name = models.CharField(max_length=255, blank=True)
    avatar_url = models.URLField(blank=True)
    phone_number = models.CharField(
        max_length=20, 
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Phone number must be entered in the format: +999999999'
            )
        ]
    )
    
    # Language and locale
    language_code = models.CharField(max_length=10, default='en')
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Status fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    # Multi-tenant support
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='users'
    )
    
    # Security fields
    password_changed_at = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    requires_password_change = models.BooleanField(default=False)
    
    # Verification
    email_verified_at = models.DateTimeField(null=True, blank=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)  # Soft delete
    
    # User preferences
    preferences = models.JSONField(default=dict, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'auth_users'
        indexes = [
            models.Index(fields=['email', 'tenant']),
            models.Index(fields=['is_active', 'tenant']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self) -> str:
        """Return user's full name"""
        if self.display_name:
            return self.display_name
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    def get_short_name(self) -> str:
        """Return user's short name"""
        return self.first_name or self.email.split('@')[0]
    
    def lock_account(self, duration_minutes: int = 30) -> None:
        """Lock account for specified duration"""
        self.locked_until = timezone.now() + timedelta(minutes=duration_minutes)
        self.save(update_fields=['locked_until'])
    
    def unlock_account(self) -> None:
        """Unlock account"""
        self.locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['locked_until', 'failed_login_attempts'])
    
    def is_locked(self) -> bool:
        """Check if account is locked"""
        if self.locked_until:
            if self.locked_until > timezone.now():
                return True
            # Auto-unlock if time has passed
            self.unlock_account()
        return False
    
    def record_failed_login(self) -> None:
        """Record failed login attempt"""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            self.lock_account(duration_minutes=30)
        else:
            self.save(update_fields=['failed_login_attempts'])


class Role(models.Model):
    """Dynamic role model with hierarchy support"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=100, db_index=True)
    description = models.TextField(blank=True)
    
    # Hierarchical roles
    parent_role = models.ForeignKey(
        'self', 
        null=True, 
        blank=True,
        on_delete=models.SET_NULL,
        related_name='child_roles'
    )
    
    # Multi-tenant support
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='roles'
    )
    is_system_role = models.BooleanField(default=False)  # System vs custom roles
    
    # Metadata
    priority = models.IntegerField(default=0)  # For role hierarchy
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_roles'
        unique_together = [['code', 'tenant']]
        ordering = ['priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    def get_all_permissions(self) -> List['Permission']:
        """Get all permissions including inherited from parent roles"""
        permissions = list(self.permissions.filter(
            role_permissions__is_granted=True
        ))
        
        if self.parent_role:
            permissions.extend(self.parent_role.get_all_permissions())
        
        return list(set(permissions))


class Permission(models.Model):
    """Granular permission model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, unique=True, db_index=True)
    
    # Resource-based permissions
    resource = models.CharField(max_length=100, db_index=True)
    action = models.CharField(max_length=50, db_index=True)
    
    # Conditions for attribute-based access control (ABAC)
    conditions = models.JSONField(default=dict, blank=True)
    
    # Metadata
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_permissions'
        unique_together = [['resource', 'action']]
        indexes = [
            models.Index(fields=['resource', 'action']),
            models.Index(fields=['code']),
        ]
        ordering = ['resource', 'action']
    
    def __str__(self):
        return f"{self.resource}.{self.action}"
    
    def check_conditions(self, context: Dict[str, Any]) -> bool:
        """Evaluate ABAC conditions against context"""
        if not self.conditions:
            return True
        
        # Implement condition evaluation logic
        for key, expected_value in self.conditions.items():
            if key not in context or context[key] != expected_value:
                return False
        
        return True


class UserRole(models.Model):
    """User-Role relationship with temporal support"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_roles'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_assignments'
    )
    
    # Temporal roles
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    # Assignment metadata
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='role_assignments_made'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'auth_user_roles'
        unique_together = [['user', 'role']]
        indexes = [
            models.Index(fields=['user', 'valid_from', 'valid_until']),
            models.Index(fields=['role', 'valid_from', 'valid_until']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.role.name}"
    
    def is_valid(self) -> bool:
        """Check if role assignment is currently valid"""
        now = timezone.now()
        
        if self.valid_from > now:
            return False
        
        if self.valid_until and self.valid_until < now:
            return False
        
        return True


class RolePermission(models.Model):
    """Role-Permission relationship with grant/deny capability"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='role_permissions'
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='permission_roles'
    )
    
    # Override capability
    is_granted = models.BooleanField(default=True)  # Can explicitly deny
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'auth_role_permissions'
        unique_together = [['role', 'permission']]
    
    def __str__(self):
        action = "grants" if self.is_granted else "denies"
        return f"{self.role.name} {action} {self.permission}"


class Session(models.Model):
    """User session tracking"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    
    # Session data
    token_jti = models.CharField(max_length=255, unique=True, db_index=True)
    refresh_token_jti = models.CharField(max_length=255, unique=True, null=True)
    
    # Client information
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    device_id = models.CharField(max_length=255, blank=True)
    
    # Session metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_reason = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'auth_sessions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['token_jti']),
            models.Index(fields=['expires_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Session for {self.user.email} from {self.ip_address}"
    
    def revoke(self, reason: str = "") -> None:
        """Revoke session"""
        self.is_active = False
        self.revoked_at = timezone.now()
        self.revoked_reason = reason
        self.save(update_fields=['is_active', 'revoked_at', 'revoked_reason'])


class AuditLog(models.Model):
    """Authentication audit log"""
    
    ACTION_CHOICES = [
        ('login.success', 'Successful Login'),
        ('login.failed', 'Failed Login'),
        ('logout', 'Logout'),
        ('password.changed', 'Password Changed'),
        ('password.reset', 'Password Reset'),
        ('mfa.enabled', 'MFA Enabled'),
        ('mfa.disabled', 'MFA Disabled'),
        ('mfa.verified', 'MFA Verified'),
        ('role.assigned', 'Role Assigned'),
        ('role.revoked', 'Role Revoked'),
        ('permission.granted', 'Permission Granted'),
        ('permission.revoked', 'Permission Revoked'),
        ('account.locked', 'Account Locked'),
        ('account.unlocked', 'Account Unlocked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=50, choices=ACTION_CHOICES, db_index=True)
    
    # Context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    
    # Result
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'auth_audit_logs'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'created_at']),
            models.Index(fields=['tenant', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} by {self.user.email if self.user else 'Unknown'}"