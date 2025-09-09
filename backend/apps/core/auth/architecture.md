# Flexible Authentication System Architecture

## 🎯 System Overview

A modern, extensible authentication system supporting multiple authentication methods, flexible role-based access control (RBAC), and multi-tenant isolation.

### Core Principles
- **Extensibility**: Easy to add new authentication methods
- **Flexibility**: Dynamic roles and permissions
- **Security**: Defense in depth with multiple security layers
- **Scalability**: Stateless JWT tokens with refresh mechanism
- **Multi-tenancy**: Tenant-aware authentication and authorization

## 🏗️ Architecture Components

```
┌─────────────────────────────────────────────────────────┐
│                    API Gateway                           │
│                 (Authentication Layer)                   │
└─────────────┬───────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│                  Core Auth Service                       │
├───────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Identity  │  │    Access   │  │   Session   │     │
│  │  Management │  │   Control   │  │  Management │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │    Token    │  │     MFA     │  │    Audit    │     │
│  │  Management │  │   Support   │  │   Logging   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│                    Data Layer                            │
│         (PostgreSQL + Redis Cache + Audit DB)           │
└─────────────────────────────────────────────────────────┘
```

## 📊 Data Models

### User Model (Extended Django User)
```python
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
import uuid

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    
    # Profile fields
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    
    # Status fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
    # Multi-tenant support
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Security
    password_changed_at = models.DateTimeField(null=True)
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'auth_users'
        indexes = [
            models.Index(fields=['email', 'tenant']),
            models.Index(fields=['is_active', 'tenant']),
        ]
```

### Dynamic Role System
```python
class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=100)
    code = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Hierarchical roles
    parent_role = models.ForeignKey('self', null=True, blank=True, 
                                   on_delete=models.SET_NULL,
                                   related_name='child_roles')
    
    # Multi-tenant support
    tenant = models.ForeignKey('Tenant', on_delete=models.CASCADE, null=True)
    is_system_role = models.BooleanField(default=False)  # System vs custom roles
    
    # Metadata
    priority = models.IntegerField(default=0)  # For role hierarchy
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_roles'
        unique_together = [['code', 'tenant']]
        ordering = ['priority', 'name']
```

### Granular Permission System
```python
class Permission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=100, unique=True)
    resource = models.CharField(max_length=100)  # e.g., 'user', 'billing', 'report'
    action = models.CharField(max_length=50)     # e.g., 'create', 'read', 'update', 'delete'
    
    # Conditions for attribute-based access control (ABAC)
    conditions = models.JSONField(default=dict, blank=True)
    
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'auth_permissions'
        unique_together = [['resource', 'action']]
        indexes = [
            models.Index(fields=['resource', 'action']),
        ]
```

### User-Role-Permission Relationships
```python
class UserRole(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    
    # Temporal roles
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    # Assignment metadata
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, 
                                   null=True, related_name='role_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'auth_user_roles'
        unique_together = [['user', 'role']]
        indexes = [
            models.Index(fields=['user', 'valid_from', 'valid_until']),
        ]

class RolePermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, 
                            related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    
    # Override capability
    is_granted = models.BooleanField(default=True)  # Can be used to explicitly deny
    
    class Meta:
        db_table = 'auth_role_permissions'
        unique_together = [['role', 'permission']]
```

## 🔐 Authentication Flow

### JWT Token Strategy
```python
# Token payload structure
{
    "token_type": "access",
    "user_id": "uuid",
    "email": "user@example.com",
    "tenant_id": "uuid",
    "roles": ["admin", "user"],
    "permissions": ["user.read", "user.write"],
    "exp": 1234567890,
    "iat": 1234567890,
    "jti": "unique-token-id",
    "session_id": "session-uuid"
}
```

### Authentication Service Implementation
```python
from datetime import timedelta
from typing import Optional, Dict, Any
import jwt
from django.conf import settings
from django.core.cache import cache

class AuthenticationService:
    def __init__(self):
        self.access_token_lifetime = timedelta(minutes=15)
        self.refresh_token_lifetime = timedelta(days=7)
        
    def authenticate(self, email: str, password: str, 
                     tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Main authentication method"""
        # User lookup with tenant isolation
        user = self._get_user(email, tenant_id)
        
        # Check account status
        if not user.is_active:
            raise AuthenticationError("Account is disabled")
            
        if user.locked_until and user.locked_until > timezone.now():
            raise AuthenticationError("Account is temporarily locked")
        
        # Verify password
        if not user.check_password(password):
            self._handle_failed_login(user)
            raise AuthenticationError("Invalid credentials")
        
        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.last_login = timezone.now()
        user.save(update_fields=['failed_login_attempts', 'last_login'])
        
        # Generate tokens
        tokens = self._generate_tokens(user)
        
        # Create session
        session = self._create_session(user, tokens)
        
        # Audit log
        self._audit_log('login.success', user)
        
        return {
            'access_token': tokens['access'],
            'refresh_token': tokens['refresh'],
            'user': self._serialize_user(user),
            'expires_in': self.access_token_lifetime.total_seconds()
        }
    
    def _generate_tokens(self, user: User) -> Dict[str, str]:
        """Generate JWT tokens with user context"""
        # Fetch user permissions
        permissions = self._get_user_permissions(user)
        roles = self._get_user_roles(user)
        
        # Access token payload
        access_payload = {
            'token_type': 'access',
            'user_id': str(user.id),
            'email': user.email,
            'tenant_id': str(user.tenant_id) if user.tenant_id else None,
            'roles': [role.code for role in roles],
            'permissions': list(permissions),
            'exp': timezone.now() + self.access_token_lifetime,
            'iat': timezone.now(),
            'jti': str(uuid.uuid4()),
        }
        
        # Refresh token payload (minimal)
        refresh_payload = {
            'token_type': 'refresh',
            'user_id': str(user.id),
            'exp': timezone.now() + self.refresh_token_lifetime,
            'iat': timezone.now(),
            'jti': str(uuid.uuid4()),
        }
        
        return {
            'access': jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256'),
            'refresh': jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')
        }
```

## 🔑 Multi-Factor Authentication

### MFA Models
```python
class MFAMethod(models.Model):
    METHOD_CHOICES = [
        ('totp', 'Time-based OTP'),
        ('sms', 'SMS Code'),
        ('email', 'Email Code'),
        ('backup', 'Backup Codes'),
        ('webauthn', 'WebAuthn/Passkey'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE, 
                            related_name='mfa_methods')
    method_type = models.CharField(max_length=20, choices=METHOD_CHOICES)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Method-specific data
    secret = models.CharField(max_length=255, blank=True)  # Encrypted
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    
    # Metadata
    verified_at = models.DateTimeField(null=True)
    last_used_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auth_mfa_methods'
        unique_together = [['user', 'method_type', 'phone_number'],
                          ['user', 'method_type', 'email']]
```

## 🛡️ Security Features

### Session Management
```python
class SessionManager:
    def create_session(self, user: User, tokens: Dict[str, str]) -> Session:
        """Create and track user session"""
        session = Session.objects.create(
            user=user,
            token_jti=tokens['jti'],
            ip_address=self.get_client_ip(),
            user_agent=self.get_user_agent(),
            expires_at=timezone.now() + self.session_lifetime
        )
        
        # Cache session for quick validation
        cache.set(f"session:{session.id}", session, timeout=3600)
        
        return session
    
    def validate_session(self, token: str) -> bool:
        """Validate token belongs to active session"""
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        session_id = payload.get('session_id')
        
        # Check cache first
        session = cache.get(f"session:{session_id}")
        if not session:
            session = Session.objects.filter(
                id=session_id,
                is_active=True,
                expires_at__gt=timezone.now()
            ).first()
            
        return session is not None
```

### Rate Limiting
```python
class RateLimiter:
    def check_rate_limit(self, key: str, limit: int = 5, 
                        window: int = 300) -> bool:
        """Check if rate limit exceeded"""
        current = cache.get(f"rate_limit:{key}", 0)
        if current >= limit:
            return False
            
        cache.set(f"rate_limit:{key}", current + 1, timeout=window)
        return True
```

## 🔌 API Endpoints

### Authentication Endpoints (Django Ninja)
```python
from ninja import Router, Schema
from typing import Optional

router = Router(tags=["authentication"])

class LoginSchema(Schema):
    email: str
    password: str
    tenant_id: Optional[str] = None
    mfa_code: Optional[str] = None

class TokenResponseSchema(Schema):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserSchema

@router.post("/login", response=TokenResponseSchema)
def login(request, payload: LoginSchema):
    """Authenticate user and return tokens"""
    service = AuthenticationService()
    
    # Rate limiting
    if not RateLimiter().check_rate_limit(f"login:{payload.email}"):
        return 429, {"error": "Too many login attempts"}
    
    try:
        result = service.authenticate(
            email=payload.email,
            password=payload.password,
            tenant_id=payload.tenant_id
        )
        
        # Check MFA if required
        if service.requires_mfa(result['user']):
            if not payload.mfa_code:
                return 403, {"error": "MFA required", "mfa_methods": [...]}
            
            if not service.verify_mfa(result['user'], payload.mfa_code):
                return 403, {"error": "Invalid MFA code"}
        
        return result
        
    except AuthenticationError as e:
        return 401, {"error": str(e)}

@router.post("/refresh")
def refresh_token(request, refresh_token: str):
    """Refresh access token"""
    service = AuthenticationService()
    return service.refresh_token(refresh_token)

@router.post("/logout")
def logout(request):
    """Invalidate user session"""
    service = AuthenticationService()
    return service.logout(request.auth.token)

@router.post("/register")
def register(request, payload: RegisterSchema):
    """Register new user"""
    service = RegistrationService()
    return service.register(payload)

@router.post("/verify-email/{token}")
def verify_email(request, token: str):
    """Verify email address"""
    service = RegistrationService()
    return service.verify_email(token)

@router.post("/forgot-password")
def forgot_password(request, email: str):
    """Initiate password reset"""
    service = PasswordResetService()
    return service.initiate_reset(email)

@router.post("/reset-password")
def reset_password(request, token: str, new_password: str):
    """Reset password with token"""
    service = PasswordResetService()
    return service.reset_password(token, new_password)
```

## 🎯 Authorization Middleware

```python
from functools import wraps
from typing import List, Optional

class AuthorizationMiddleware:
    def require_permission(self, *permissions: str):
        """Decorator for permission-based access control"""
        def decorator(func):
            @wraps(func)
            def wrapper(request, *args, **kwargs):
                user = request.auth.user
                
                if not user or not user.is_authenticated:
                    return 401, {"error": "Authentication required"}
                
                user_permissions = self.get_user_permissions(user)
                
                if not any(perm in user_permissions for perm in permissions):
                    return 403, {"error": "Insufficient permissions"}
                
                return func(request, *args, **kwargs)
            return wrapper
        return decorator
    
    def require_role(self, *roles: str):
        """Decorator for role-based access control"""
        def decorator(func):
            @wraps(func)
            def wrapper(request, *args, **kwargs):
                user = request.auth.user
                
                if not user or not user.is_authenticated:
                    return 401, {"error": "Authentication required"}
                
                user_roles = self.get_user_roles(user)
                
                if not any(role in user_roles for role in roles):
                    return 403, {"error": "Insufficient role privileges"}
                
                return func(request, *args, **kwargs)
            return wrapper
        return decorator

# Usage example
@router.get("/admin/users")
@AuthorizationMiddleware().require_permission("user.read", "user.list")
def list_users(request):
    """List all users (requires permission)"""
    return UserService().list_users()
```

## 🔄 Extension Points

### Custom Authentication Providers
```python
class AuthProvider(ABC):
    @abstractmethod
    def authenticate(self, credentials: Dict) -> Optional[User]:
        pass
    
    @abstractmethod
    def get_user_info(self, token: str) -> Dict:
        pass

class LDAPProvider(AuthProvider):
    """LDAP authentication provider"""
    pass

class OAuth2Provider(AuthProvider):
    """OAuth2/OIDC provider"""
    pass

class SAMLProvider(AuthProvider):
    """SAML 2.0 provider"""
    pass
```

### Plugin System for Custom Rules
```python
class AuthorizationPlugin(ABC):
    @abstractmethod
    def check_access(self, user: User, resource: str, 
                    action: str, context: Dict) -> bool:
        pass

class TenantIsolationPlugin(AuthorizationPlugin):
    """Ensure tenant isolation"""
    def check_access(self, user, resource, action, context):
        if 'tenant_id' in context:
            return user.tenant_id == context['tenant_id']
        return True

class TimeBasedAccessPlugin(AuthorizationPlugin):
    """Time-based access control"""
    def check_access(self, user, resource, action, context):
        # Check if access is within allowed time window
        pass
```

## 📊 Usage Examples

### Creating Custom Roles
```python
# Create a custom role with permissions
role = Role.objects.create(
    name="Data Analyst",
    code="data_analyst",
    description="Can view and analyze data",
    tenant=tenant
)

# Assign permissions
permissions = [
    Permission.objects.get(code="report.read"),
    Permission.objects.get(code="analytics.read"),
    Permission.objects.get(code="export.create"),
]

for permission in permissions:
    RolePermission.objects.create(role=role, permission=permission)

# Assign role to user
UserRole.objects.create(
    user=user,
    role=role,
    assigned_by=admin_user,
    reason="New data analyst hire"
)
```

### Dynamic Permission Checking
```python
def has_permission(user: User, resource: str, action: str, 
                   context: Optional[Dict] = None) -> bool:
    """Check if user has permission for resource/action"""
    
    # Get all user permissions (including from roles)
    permissions = get_user_permissions(user)
    
    # Check direct permission
    permission_code = f"{resource}.{action}"
    if permission_code in permissions:
        # Check ABAC conditions if any
        if context:
            return evaluate_conditions(permission, context)
        return True
    
    # Check wildcard permissions
    if f"{resource}.*" in permissions or "*.*" in permissions:
        return True
    
    return False

# Usage
if has_permission(user, "billing", "update", {"tenant_id": tenant.id}):
    # Allow billing update
    pass
```

## 🚀 Implementation Roadmap

1. **Phase 1: Core Authentication**
   - User model and basic authentication
   - JWT token generation and validation
   - Session management

2. **Phase 2: Authorization System**
   - Role and permission models
   - RBAC implementation
   - Authorization middleware

3. **Phase 3: Advanced Security**
   - Multi-factor authentication
   - Rate limiting and brute force protection
   - Audit logging

4. **Phase 4: Extensions**
   - OAuth2/OIDC support
   - SAML integration
   - Custom authentication providers

5. **Phase 5: Advanced Features**
   - Attribute-based access control (ABAC)
   - Delegated administration
   - Zero-trust security model

---

This architecture provides a robust, extensible authentication system that can grow with your application needs while maintaining security and performance.