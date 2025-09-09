"""
Authentication API endpoints using Django Ninja.
Provides RESTful API for authentication, authorization, and user management.
"""

from typing import Optional, List
from datetime import timedelta

from ninja import Router, Schema, Field
from ninja.security import HttpBearer
from django.shortcuts import get_object_or_404
from django.db import transaction
from pydantic import EmailStr, validator

from .services import (
    AuthenticationService, AuthorizationService, 
    TokenService, RateLimiter, AuthenticationError
)
from .models import User, Role, Permission, UserRole


# API Router
router = Router(tags=["Authentication"])


# Request/Response Schemas
class LoginRequest(Schema):
    email: EmailStr
    password: str
    tenant_id: Optional[str] = None
    mfa_code: Optional[str] = None
    remember_me: bool = False


class RegisterRequest(Schema):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    tenant_id: Optional[str] = None
    language_code: str = "en"
    timezone: str = "UTC"
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


class RefreshTokenRequest(Schema):
    refresh_token: str


class UserResponse(Schema):
    id: str
    email: str
    username: Optional[str]
    first_name: str
    last_name: str
    display_name: str
    avatar_url: Optional[str]
    language_code: str
    timezone: str
    is_verified: bool
    tenant_id: Optional[str]
    created_at: str


class TokenResponse(Schema):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserResponse
    session_id: str
    requires_mfa: bool = False
    requires_password_change: bool = False


class RefreshTokenResponse(Schema):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class MessageResponse(Schema):
    message: str
    success: bool = True


class ErrorResponse(Schema):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class PasswordResetRequest(Schema):
    email: EmailStr
    tenant_id: Optional[str] = None


class PasswordResetConfirmRequest(Schema):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class ChangePasswordRequest(Schema):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class RoleResponse(Schema):
    id: str
    name: str
    code: str
    description: str
    is_system_role: bool
    permissions_count: int


class PermissionResponse(Schema):
    id: str
    name: str
    code: str
    resource: str
    action: str
    description: str


# Authentication Bearer
class AuthBearer(HttpBearer):
    """JWT authentication bearer"""
    
    def authenticate(self, request, token):
        token_service = TokenService()
        payload = token_service.verify_token(token)
        
        if not payload:
            return None
        
        try:
            user = User.objects.get(id=payload['user_id'])
            request.auth = type('Auth', (), {
                'user': user,
                'token': token,
                'payload': payload,
                'permissions': payload.get('permissions', []),
                'roles': payload.get('roles', [])
            })()
            return token
        except User.DoesNotExist:
            return None


auth = AuthBearer()


# Helper function to get client info
def get_client_info(request):
    """Extract client information from request"""
    return {
        'ip_address': request.META.get('REMOTE_ADDR'),
        'user_agent': request.META.get('HTTP_USER_AGENT', '')
    }


# Public endpoints (no authentication required)
@router.post("/login", response={200: TokenResponse, 401: ErrorResponse, 429: ErrorResponse})
def login(request, payload: LoginRequest):
    """
    Authenticate user and return JWT tokens.
    
    Rate limited to prevent brute force attacks.
    """
    # Rate limiting
    rate_limiter = RateLimiter()
    allowed, remaining = rate_limiter.check_limit(
        f"login:{payload.email}",
        limit=5,
        window=300
    )
    
    if not allowed:
        return 429, ErrorResponse(
            error="Too many login attempts",
            detail="Please try again later",
            code="RATE_LIMIT_EXCEEDED"
        )
    
    # Get client info
    client_info = get_client_info(request)
    
    # Authenticate
    auth_service = AuthenticationService()
    
    try:
        result = auth_service.authenticate(
            email=payload.email,
            password=payload.password,
            tenant_id=payload.tenant_id,
            ip_address=client_info['ip_address'],
            user_agent=client_info['user_agent']
        )
        
        # Handle MFA if required
        if result['requires_mfa'] and not payload.mfa_code:
            return 401, ErrorResponse(
                error="MFA required",
                detail="Please provide MFA code",
                code="MFA_REQUIRED"
            )
        
        # Reset rate limit on successful login
        rate_limiter.reset_limit(f"login:{payload.email}")
        
        return 200, TokenResponse(**result)
        
    except AuthenticationError as e:
        return 401, ErrorResponse(
            error=str(e),
            code="AUTHENTICATION_FAILED"
        )


@router.post("/register", response={201: TokenResponse, 400: ErrorResponse})
@transaction.atomic
def register(request, payload: RegisterRequest):
    """
    Register a new user account.
    
    Creates user and returns JWT tokens for immediate login.
    """
    # Check if email already exists
    if User.objects.filter(email__iexact=payload.email).exists():
        return 400, ErrorResponse(
            error="Email already registered",
            code="EMAIL_EXISTS"
        )
    
    # Create user
    user = User.objects.create_user(
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name,
        last_name=payload.last_name,
        tenant_id=payload.tenant_id,
        language_code=payload.language_code,
        timezone=payload.timezone
    )
    
    # Assign default role
    try:
        default_role = Role.objects.get(code='user', is_system_role=True)
        UserRole.objects.create(user=user, role=default_role)
    except Role.DoesNotExist:
        pass  # No default role configured
    
    # Auto-login after registration
    client_info = get_client_info(request)
    auth_service = AuthenticationService()
    
    result = auth_service.authenticate(
        email=payload.email,
        password=payload.password,
        tenant_id=payload.tenant_id,
        ip_address=client_info['ip_address'],
        user_agent=client_info['user_agent']
    )
    
    return 201, TokenResponse(**result)


@router.post("/refresh", response={200: RefreshTokenResponse, 401: ErrorResponse})
def refresh_token(request, payload: RefreshTokenRequest):
    """
    Refresh access token using refresh token.
    
    Returns new access token with same permissions.
    """
    token_service = TokenService()
    result = token_service.refresh_access_token(payload.refresh_token)
    
    if not result:
        return 401, ErrorResponse(
            error="Invalid or expired refresh token",
            code="INVALID_REFRESH_TOKEN"
        )
    
    return 200, RefreshTokenResponse(**result)


@router.post("/forgot-password", response={200: MessageResponse, 429: ErrorResponse})
def forgot_password(request, payload: PasswordResetRequest):
    """
    Initiate password reset process.
    
    Sends password reset email to user.
    """
    # Rate limiting
    rate_limiter = RateLimiter()
    allowed, _ = rate_limiter.check_limit(
        f"password_reset:{payload.email}",
        limit=3,
        window=3600  # 1 hour
    )
    
    if not allowed:
        return 429, ErrorResponse(
            error="Too many password reset requests",
            detail="Please try again later",
            code="RATE_LIMIT_EXCEEDED"
        )
    
    # Find user (don't reveal if email exists)
    user = User.objects.filter(
        email__iexact=payload.email,
        tenant_id=payload.tenant_id if payload.tenant_id else None
    ).first()
    
    if user:
        # TODO: Send password reset email
        # For now, just log the action
        from .models import AuditLog
        AuditLog.objects.create(
            user=user,
            action='password.reset',
            success=True,
            ip_address=get_client_info(request)['ip_address']
        )
    
    # Always return success to prevent email enumeration
    return 200, MessageResponse(
        message="If an account exists with this email, a password reset link has been sent."
    )


@router.post("/reset-password", response={200: MessageResponse, 400: ErrorResponse})
def reset_password(request, payload: PasswordResetConfirmRequest):
    """
    Reset password using reset token.
    
    Validates token and updates user password.
    """
    # TODO: Implement token validation and password reset
    # For now, return not implemented
    return 400, ErrorResponse(
        error="Password reset not yet implemented",
        code="NOT_IMPLEMENTED"
    )


# Authenticated endpoints
@router.post("/logout", auth=auth, response={200: MessageResponse})
def logout(request):
    """
    Logout current user.
    
    Revokes current token and session.
    """
    auth_service = AuthenticationService()
    success = auth_service.logout(request.auth.token)
    
    return MessageResponse(
        message="Logged out successfully" if success else "Logout failed",
        success=success
    )


@router.get("/me", auth=auth, response=UserResponse)
def get_current_user(request):
    """
    Get current authenticated user.
    
    Returns user profile information.
    """
    user = request.auth.user
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        display_name=user.get_full_name(),
        avatar_url=user.avatar_url,
        language_code=user.language_code,
        timezone=user.timezone,
        is_verified=user.is_verified,
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
        created_at=user.created_at.isoformat()
    )


@router.patch("/me", auth=auth, response=UserResponse)
def update_current_user(request, 
                        first_name: Optional[str] = None,
                        last_name: Optional[str] = None,
                        display_name: Optional[str] = None,
                        language_code: Optional[str] = None,
                        timezone: Optional[str] = None):
    """
    Update current user profile.
    
    Allows updating non-sensitive user fields.
    """
    user = request.auth.user
    
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if display_name is not None:
        user.display_name = display_name
    if language_code is not None:
        user.language_code = language_code
    if timezone is not None:
        user.timezone = timezone
    
    user.save()
    
    return UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        display_name=user.get_full_name(),
        avatar_url=user.avatar_url,
        language_code=user.language_code,
        timezone=user.timezone,
        is_verified=user.is_verified,
        tenant_id=str(user.tenant_id) if user.tenant_id else None,
        created_at=user.created_at.isoformat()
    )


@router.post("/change-password", auth=auth, response={200: MessageResponse, 400: ErrorResponse})
def change_password(request, payload: ChangePasswordRequest):
    """
    Change current user's password.
    
    Requires current password for verification.
    """
    user = request.auth.user
    
    # Verify current password
    if not user.check_password(payload.current_password):
        return 400, ErrorResponse(
            error="Current password is incorrect",
            code="INVALID_PASSWORD"
        )
    
    # Update password
    user.set_password(payload.new_password)
    user.password_changed_at = timezone.now()
    user.requires_password_change = False
    user.save()
    
    # Log password change
    from .models import AuditLog
    AuditLog.objects.create(
        user=user,
        action='password.changed',
        success=True,
        ip_address=get_client_info(request)['ip_address']
    )
    
    # Revoke all existing sessions except current
    from .models import Session
    Session.objects.filter(
        user=user,
        is_active=True
    ).exclude(
        id=request.auth.payload.get('session_id')
    ).update(
        is_active=False,
        revoked_at=timezone.now(),
        revoked_reason="Password changed"
    )
    
    return MessageResponse(message="Password changed successfully")


@router.get("/roles", auth=auth, response=List[RoleResponse])
def get_user_roles(request):
    """
    Get current user's roles.
    
    Returns list of assigned roles with permissions count.
    """
    user = request.auth.user
    user_roles = UserRole.objects.filter(
        user=user,
        role__is_active=True
    ).select_related('role')
    
    roles = []
    for ur in user_roles:
        if ur.is_valid():
            role = ur.role
            permissions_count = role.role_permissions.filter(
                is_granted=True,
                permission__is_active=True
            ).count()
            
            roles.append(RoleResponse(
                id=str(role.id),
                name=role.name,
                code=role.code,
                description=role.description,
                is_system_role=role.is_system_role,
                permissions_count=permissions_count
            ))
    
    return roles


@router.get("/permissions", auth=auth, response=List[str])
def get_user_permissions(request):
    """
    Get current user's permissions.
    
    Returns list of permission codes (resource.action format).
    """
    return request.auth.permissions


@router.post("/check-permission", auth=auth, response={200: dict})
def check_permission(request, resource: str, action: str, 
                    context: Optional[dict] = None):
    """
    Check if user has specific permission.
    
    Supports context-based permission checking (ABAC).
    """
    auth_service = AuthorizationService()
    has_permission = auth_service.has_permission(
        request.auth.user,
        resource,
        action,
        context
    )
    
    return {
        "has_permission": has_permission,
        "resource": resource,
        "action": action
    }


@router.get("/sessions", auth=auth, response=List[dict])
def get_user_sessions(request):
    """
    Get user's active sessions.
    
    Returns list of active sessions with device information.
    """
    user = request.auth.user
    from .models import Session
    
    sessions = Session.objects.filter(
        user=user,
        is_active=True,
        expires_at__gt=timezone.now()
    ).order_by('-last_activity')
    
    return [
        {
            "id": str(session.id),
            "ip_address": session.ip_address,
            "user_agent": session.user_agent,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat(),
            "is_current": str(session.id) == request.auth.payload.get('session_id')
        }
        for session in sessions
    ]


@router.delete("/sessions/{session_id}", auth=auth, response={200: MessageResponse, 404: ErrorResponse})
def revoke_session(request, session_id: str):
    """
    Revoke a specific session.
    
    Allows users to logout other devices.
    """
    user = request.auth.user
    from .models import Session
    
    try:
        session = Session.objects.get(
            id=session_id,
            user=user,
            is_active=True
        )
        
        # Don't allow revoking current session via this endpoint
        if str(session.id) == request.auth.payload.get('session_id'):
            return 400, ErrorResponse(
                error="Cannot revoke current session",
                detail="Use /logout endpoint instead",
                code="INVALID_SESSION"
            )
        
        session.revoke("Revoked by user")
        
        return MessageResponse(message="Session revoked successfully")
        
    except Session.DoesNotExist:
        return 404, ErrorResponse(
            error="Session not found",
            code="SESSION_NOT_FOUND"
        )