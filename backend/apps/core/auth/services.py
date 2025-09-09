"""
Authentication and authorization services for ReactDjango Hub.
Handles JWT tokens, authentication, and permission checking.
"""

import uuid
import secrets
from datetime import timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

import jwt
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.db.models import Q, Prefetch

from .models import (
    User, Role, Permission, UserRole, RolePermission,
    Session, AuditLog, Tenant
)


@dataclass
class TokenPayload:
    """JWT token payload structure"""
    token_type: str
    user_id: str
    email: str
    tenant_id: Optional[str]
    roles: List[str]
    permissions: List[str]
    session_id: str
    jti: str
    exp: int
    iat: int


class TokenService:
    """JWT token management service"""
    
    def __init__(self):
        self.access_token_lifetime = timedelta(minutes=15)
        self.refresh_token_lifetime = timedelta(days=7)
        self.algorithm = 'HS256'
        self.secret_key = settings.SECRET_KEY
    
    def generate_tokens(self, user: User, session: Session) -> Dict[str, str]:
        """Generate access and refresh tokens for user"""
        # Get user roles and permissions
        roles = self._get_user_roles(user)
        permissions = self._get_user_permissions(user)
        
        # Generate unique token IDs
        access_jti = str(uuid.uuid4())
        refresh_jti = str(uuid.uuid4())
        
        # Create access token
        access_token = self._create_access_token(
            user=user,
            roles=roles,
            permissions=permissions,
            session_id=str(session.id),
            jti=access_jti
        )
        
        # Create refresh token
        refresh_token = self._create_refresh_token(
            user=user,
            session_id=str(session.id),
            jti=refresh_jti
        )
        
        # Update session with token JTIs
        session.token_jti = access_jti
        session.refresh_token_jti = refresh_jti
        session.save(update_fields=['token_jti', 'refresh_token_jti'])
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': int(self.access_token_lifetime.total_seconds())
        }
    
    def _create_access_token(self, user: User, roles: List[Role], 
                           permissions: List[str], session_id: str, 
                           jti: str) -> str:
        """Create JWT access token"""
        now = timezone.now()
        exp = now + self.access_token_lifetime
        
        payload = {
            'token_type': 'access',
            'user_id': str(user.id),
            'email': user.email,
            'tenant_id': str(user.tenant_id) if user.tenant_id else None,
            'roles': [role.code for role in roles],
            'permissions': permissions,
            'session_id': session_id,
            'jti': jti,
            'exp': int(exp.timestamp()),
            'iat': int(now.timestamp()),
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def _create_refresh_token(self, user: User, session_id: str, jti: str) -> str:
        """Create JWT refresh token"""
        now = timezone.now()
        exp = now + self.refresh_token_lifetime
        
        payload = {
            'token_type': 'refresh',
            'user_id': str(user.id),
            'session_id': session_id,
            'jti': jti,
            'exp': int(exp.timestamp()),
            'iat': int(now.timestamp()),
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = 'access') -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Verify token type
            if payload.get('token_type') != token_type:
                return None
            
            # Check if token is blacklisted
            if self._is_token_blacklisted(payload['jti']):
                return None
            
            # Verify session is still active
            if not self._is_session_active(payload.get('session_id')):
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Generate new access token from refresh token"""
        payload = self.verify_token(refresh_token, token_type='refresh')
        if not payload:
            return None
        
        # Get user and session
        try:
            user = User.objects.get(id=payload['user_id'])
            session = Session.objects.get(id=payload['session_id'])
        except (User.DoesNotExist, Session.DoesNotExist):
            return None
        
        # Check if user is still active
        if not user.is_active or user.is_locked():
            return None
        
        # Generate new access token
        roles = self._get_user_roles(user)
        permissions = self._get_user_permissions(user)
        access_jti = str(uuid.uuid4())
        
        access_token = self._create_access_token(
            user=user,
            roles=roles,
            permissions=permissions,
            session_id=str(session.id),
            jti=access_jti
        )
        
        # Update session
        session.token_jti = access_jti
        session.last_activity = timezone.now()
        session.save(update_fields=['token_jti', 'last_activity'])
        
        return {
            'access_token': access_token,
            'token_type': 'Bearer',
            'expires_in': int(self.access_token_lifetime.total_seconds())
        }
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token by blacklisting its JTI"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}  # Allow expired tokens to be revoked
            )
            
            jti = payload.get('jti')
            if jti:
                # Add to blacklist with TTL until original expiration
                ttl = payload.get('exp', 0) - int(timezone.now().timestamp())
                if ttl > 0:
                    cache.set(f"blacklist:{jti}", True, timeout=ttl)
                return True
                
        except jwt.InvalidTokenError:
            pass
        
        return False
    
    def _get_user_roles(self, user: User) -> List[Role]:
        """Get all active roles for user"""
        now = timezone.now()
        
        user_roles = UserRole.objects.filter(
            user=user,
            role__is_active=True,
            valid_from__lte=now
        ).filter(
            Q(valid_until__isnull=True) | Q(valid_until__gte=now)
        ).select_related('role')
        
        return [ur.role for ur in user_roles]
    
    def _get_user_permissions(self, user: User) -> List[str]:
        """Get all permissions for user including role permissions"""
        permissions = set()
        
        # Get permissions from roles
        roles = self._get_user_roles(user)
        for role in roles:
            role_permissions = RolePermission.objects.filter(
                role=role,
                permission__is_active=True,
                is_granted=True
            ).select_related('permission')
            
            for rp in role_permissions:
                permissions.add(f"{rp.permission.resource}.{rp.permission.action}")
        
        # Add superuser permissions
        if user.is_superuser:
            permissions.add("*.*")
        
        return list(permissions)
    
    def _is_token_blacklisted(self, jti: str) -> bool:
        """Check if token JTI is blacklisted"""
        return cache.get(f"blacklist:{jti}") is not None
    
    def _is_session_active(self, session_id: str) -> bool:
        """Check if session is still active"""
        if not session_id:
            return True  # Allow tokens without session tracking
        
        # Check cache first
        cache_key = f"session:active:{session_id}"
        is_active = cache.get(cache_key)
        
        if is_active is not None:
            return is_active
        
        # Check database
        try:
            session = Session.objects.get(
                id=session_id,
                is_active=True,
                expires_at__gt=timezone.now()
            )
            # Cache result for 60 seconds
            cache.set(cache_key, True, timeout=60)
            return True
        except Session.DoesNotExist:
            cache.set(cache_key, False, timeout=60)
            return False


class AuthenticationService:
    """Main authentication service"""
    
    def __init__(self):
        self.token_service = TokenService()
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
    
    @transaction.atomic
    def authenticate(self, email: str, password: str, 
                    tenant_id: Optional[str] = None,
                    ip_address: Optional[str] = None,
                    user_agent: Optional[str] = None) -> Dict[str, Any]:
        """Authenticate user and generate tokens"""
        
        # Find user
        user = self._find_user(email, tenant_id)
        if not user:
            self._log_failed_login(email, ip_address, "User not found")
            raise AuthenticationError("Invalid credentials")
        
        # Check if account is locked
        if user.is_locked():
            self._log_failed_login(email, ip_address, "Account locked", user)
            raise AuthenticationError("Account is temporarily locked")
        
        # Check if account is active
        if not user.is_active:
            self._log_failed_login(email, ip_address, "Account inactive", user)
            raise AuthenticationError("Account is disabled")
        
        # Verify password
        if not check_password(password, user.password):
            user.record_failed_login()
            self._log_failed_login(email, ip_address, "Invalid password", user)
            
            if user.is_locked():
                raise AuthenticationError("Account locked due to multiple failed attempts")
            else:
                raise AuthenticationError("Invalid credentials")
        
        # Reset failed attempts on successful authentication
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.save(update_fields=['failed_login_attempts'])
        
        # Create session
        session = self._create_session(user, ip_address, user_agent)
        
        # Generate tokens
        tokens = self.token_service.generate_tokens(user, session)
        
        # Update last login
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Log successful login
        self._log_successful_login(user, ip_address)
        
        return {
            **tokens,
            'user': self._serialize_user(user),
            'session_id': str(session.id),
            'requires_mfa': self._requires_mfa(user),
            'requires_password_change': user.requires_password_change
        }
    
    def logout(self, token: str) -> bool:
        """Logout user by revoking token and session"""
        payload = self.token_service.verify_token(token)
        if not payload:
            return False
        
        # Revoke token
        self.token_service.revoke_token(token)
        
        # Revoke session
        session_id = payload.get('session_id')
        if session_id:
            try:
                session = Session.objects.get(id=session_id)
                session.revoke("User logout")
                
                # Log logout
                user = User.objects.get(id=payload['user_id'])
                self._log_audit(user, 'logout', True)
                
            except (Session.DoesNotExist, User.DoesNotExist):
                pass
        
        return True
    
    def _find_user(self, email: str, tenant_id: Optional[str]) -> Optional[User]:
        """Find user by email and optional tenant"""
        query = User.objects.filter(email__iexact=email)
        
        if tenant_id:
            query = query.filter(tenant_id=tenant_id)
        
        return query.first()
    
    def _create_session(self, user: User, ip_address: Optional[str], 
                       user_agent: Optional[str]) -> Session:
        """Create new user session"""
        session = Session.objects.create(
            user=user,
            token_jti='',  # Will be updated when token is generated
            ip_address=ip_address or '0.0.0.0',
            user_agent=user_agent or '',
            expires_at=timezone.now() + timedelta(days=7)
        )
        return session
    
    def _serialize_user(self, user: User) -> Dict[str, Any]:
        """Serialize user for response"""
        return {
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'display_name': user.get_full_name(),
            'avatar_url': user.avatar_url,
            'language_code': user.language_code,
            'timezone': user.timezone,
            'is_verified': user.is_verified,
            'tenant_id': str(user.tenant_id) if user.tenant_id else None,
            'created_at': user.created_at.isoformat()
        }
    
    def _requires_mfa(self, user: User) -> bool:
        """Check if user requires MFA"""
        # Check user preference
        if user.preferences.get('mfa_enabled'):
            return True
        
        # Check tenant requirement
        if user.tenant and user.tenant.settings.get('require_mfa'):
            return True
        
        # Check role requirement
        roles = self.token_service._get_user_roles(user)
        for role in roles:
            if role.code in ['admin', 'superuser']:
                return True
        
        return False
    
    def _log_audit(self, user: Optional[User], action: str, success: bool,
                  ip_address: Optional[str] = None, 
                  details: Optional[Dict] = None) -> None:
        """Log authentication audit event"""
        AuditLog.objects.create(
            user=user,
            action=action,
            success=success,
            ip_address=ip_address,
            details=details or {},
            tenant=user.tenant if user else None
        )
    
    def _log_successful_login(self, user: User, ip_address: Optional[str]) -> None:
        """Log successful login"""
        self._log_audit(user, 'login.success', True, ip_address)
    
    def _log_failed_login(self, email: str, ip_address: Optional[str], 
                         reason: str, user: Optional[User] = None) -> None:
        """Log failed login attempt"""
        self._log_audit(
            user,
            'login.failed',
            False,
            ip_address,
            {'email': email, 'reason': reason}
        )


class AuthorizationService:
    """Authorization and permission checking service"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes
    
    def has_permission(self, user: User, resource: str, action: str,
                      context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if user has permission for resource/action"""
        
        # Superuser bypass
        if user.is_superuser:
            return True
        
        # Check cache
        cache_key = f"perm:{user.id}:{resource}:{action}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Get user permissions
        permissions = self._get_user_permissions(user)
        
        # Check exact permission
        if f"{resource}.{action}" in permissions:
            result = True
        # Check wildcard permissions
        elif f"{resource}.*" in permissions or "*.*" in permissions:
            result = True
        else:
            result = False
        
        # Apply ABAC conditions if context provided
        if result and context:
            result = self._check_conditions(user, resource, action, context)
        
        # Cache result
        cache.set(cache_key, result, timeout=self.cache_timeout)
        
        return result
    
    def has_any_permission(self, user: User, 
                          permissions: List[Tuple[str, str]]) -> bool:
        """Check if user has any of the specified permissions"""
        for resource, action in permissions:
            if self.has_permission(user, resource, action):
                return True
        return False
    
    def has_all_permissions(self, user: User,
                           permissions: List[Tuple[str, str]]) -> bool:
        """Check if user has all specified permissions"""
        for resource, action in permissions:
            if not self.has_permission(user, resource, action):
                return False
        return True
    
    def has_role(self, user: User, role_code: str) -> bool:
        """Check if user has specific role"""
        
        # Check cache
        cache_key = f"role:{user.id}:{role_code}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Check database
        now = timezone.now()
        has_role = UserRole.objects.filter(
            user=user,
            role__code=role_code,
            role__is_active=True,
            valid_from__lte=now
        ).filter(
            Q(valid_until__isnull=True) | Q(valid_until__gte=now)
        ).exists()
        
        # Cache result
        cache.set(cache_key, has_role, timeout=self.cache_timeout)
        
        return has_role
    
    def has_any_role(self, user: User, role_codes: List[str]) -> bool:
        """Check if user has any of the specified roles"""
        for role_code in role_codes:
            if self.has_role(user, role_code):
                return True
        return False
    
    def _get_user_permissions(self, user: User) -> set:
        """Get all permissions for user"""
        # Use TokenService method for consistency
        token_service = TokenService()
        return set(token_service._get_user_permissions(user))
    
    def _check_conditions(self, user: User, resource: str, action: str,
                         context: Dict[str, Any]) -> bool:
        """Check ABAC conditions for permission"""
        
        # Get permission with conditions
        try:
            permission = Permission.objects.get(
                resource=resource,
                action=action,
                is_active=True
            )
        except Permission.DoesNotExist:
            return True  # No conditions if permission doesn't exist
        
        # Check tenant isolation
        if 'tenant_id' in context and user.tenant_id:
            if str(user.tenant_id) != str(context['tenant_id']):
                return False
        
        # Check permission conditions
        return permission.check_conditions(context)


class RateLimiter:
    """Rate limiting service"""
    
    def __init__(self):
        self.default_limit = 10
        self.default_window = 300  # 5 minutes
    
    def check_limit(self, key: str, limit: Optional[int] = None,
                   window: Optional[int] = None) -> Tuple[bool, int]:
        """Check if rate limit exceeded, returns (allowed, remaining)"""
        limit = limit or self.default_limit
        window = window or self.default_window
        
        cache_key = f"rate_limit:{key}"
        current = cache.get(cache_key, 0)
        
        if current >= limit:
            return False, 0
        
        # Increment counter
        new_value = current + 1
        cache.set(cache_key, new_value, timeout=window)
        
        return True, limit - new_value
    
    def reset_limit(self, key: str) -> None:
        """Reset rate limit for key"""
        cache_key = f"rate_limit:{key}"
        cache.delete(cache_key)


class AuthenticationError(Exception):
    """Authentication error exception"""
    pass