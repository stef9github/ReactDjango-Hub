"""Authentication API endpoints"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.api.deps import (
    get_auth_service, get_token_service, get_email_service,
    get_event_publisher, get_current_user, rate_limiter
)
from app.schemas.auth import (
    LoginRequest, LoginResponse, RegisterRequest, RefreshTokenRequest,
    RefreshTokenResponse, TokenValidationRequest, TokenValidationResponse,
    LogoutRequest, ForgotPasswordRequest, ResetPasswordRequest,
    VerifyEmailRequest, ServiceHealthResponse
)
from app.schemas.user import EnhancedUserResponse, UserSessionResponse
from app.services.auth_service import AuthService, TokenService
from app.services.email_service import EmailService
from app.utils.messaging import EventPublisher

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    http_request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    event_publisher: EventPublisher = Depends(get_event_publisher),
    _: bool = Depends(rate_limiter)
):
    """User login with enhanced security features"""
    try:
        result = await auth_service.authenticate_user(
            email=request.email,
            password=request.password,
            remember_me=request.remember_me,
            ip_address=http_request.client.host,
            user_agent=http_request.headers.get("user-agent", "")
        )
        
        # Publish login event
        await event_publisher.publish_event("user.login", {
            "user_id": result["user_id"],
            "email": request.email,
            "ip_address": http_request.client.host,
            "timestamp": result["timestamp"]
        })
        
        return LoginResponse(**result)
    except Exception as e:
        await event_publisher.publish_event("auth.login_failed", {
            "email": request.email,
            "ip_address": http_request.client.host,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@router.post("/register", response_model=LoginResponse)
async def register(
    request: RegisterRequest,
    http_request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    event_publisher: EventPublisher = Depends(get_event_publisher),
    _: bool = Depends(rate_limiter)
):
    """User registration with profile creation"""
    try:
        result = await auth_service.register_user(
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            tenant_id=request.tenant_id,
            ip_address=http_request.client.host
        )
        
        # Publish registration event
        await event_publisher.publish_event("user.registered", {
            "user_id": result["user_id"],
            "email": request.email,
            "tenant_id": request.tenant_id
        })
        
        return LoginResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    token_service: TokenService = Depends(get_token_service)
):
    """Refresh access token"""
    try:
        result = await token_service.refresh_token(request.refresh_token)
        return RefreshTokenResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def logout(
    request: LogoutRequest,
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
    event_publisher: EventPublisher = Depends(get_event_publisher)
):
    """User logout with session cleanup"""
    try:
        await auth_service.logout_user(
            user_id=current_user["user_id"],
            refresh_token=request.refresh_token
        )
        
        # Publish logout event
        await event_publisher.publish_event("user.logout", {
            "user_id": current_user["user_id"],
            "email": current_user["email"]
        })
        
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/validate", response_model=TokenValidationResponse)
async def validate_token(
    request: TokenValidationRequest,
    token_service: TokenService = Depends(get_token_service)
):
    """Validate JWT token for other services"""
    try:
        token_data = await token_service.verify_token(request.token)
        if not token_data:
            return TokenValidationResponse(valid=False)
        
        return TokenValidationResponse(
            valid=True,
            user_id=token_data.get("user_id"),
            email=token_data.get("email"),
            tenant_id=token_data.get("tenant_id"),
            roles=token_data.get("roles", []),
            permissions=token_data.get("permissions", []),
            expires_at=token_data.get("exp")
        )
    except Exception:
        return TokenValidationResponse(valid=False)


@router.post("/authorize")
async def authorize_user(
    permission: str,
    current_user: dict = Depends(get_current_user)
):
    """Check if user has specific permission"""
    user_permissions = current_user.get("permissions", [])
    has_permission = permission in user_permissions
    
    return {
        "authorized": has_permission,
        "user_id": current_user["user_id"],
        "permission": permission
    }


@router.get("/permissions/{user_id}")
async def get_user_permissions(
    user_id: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get user permissions for caching by other services"""
    try:
        permissions = await auth_service.get_user_permissions(user_id)
        return {"user_id": user_id, "permissions": permissions}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.get("/me", response_model=EnhancedUserResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Get current user's complete profile"""
    try:
        user_data = await auth_service.get_enhanced_user_profile(
            current_user["user_id"]
        )
        return EnhancedUserResponse(**user_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found"
        )


@router.get("/sessions", response_model=List[UserSessionResponse])
async def list_user_sessions(
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """List user's active sessions"""
    try:
        sessions = await auth_service.get_user_sessions(current_user["user_id"])
        return [UserSessionResponse(**session) for session in sessions]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve sessions"
        )


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Revoke a specific session"""
    try:
        await auth_service.revoke_session(
            user_id=current_user["user_id"],
            session_id=session_id
        )
        return {"message": "Session revoked successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not revoke session"
        )


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends(get_email_service)
):
    """Initiate password reset via email"""
    try:
        reset_token = await auth_service.create_password_reset_token(request.email)
        await email_service.send_password_reset_email(request.email, reset_token)
        return {"message": "Password reset email sent"}
    except Exception as e:
        # Don't reveal if email exists or not
        return {"message": "Password reset email sent"}


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Reset password with token"""
    try:
        await auth_service.reset_password(request.token, request.new_password)
        return {"message": "Password reset successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )


@router.post("/verify-email")
async def verify_email(
    request: VerifyEmailRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Verify email with token"""
    try:
        await auth_service.verify_email(request.token)
        return {"message": "Email verified successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )


@router.post("/resend-verification")
async def resend_verification(
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
    email_service: EmailService = Depends(get_email_service)
):
    """Resend email verification"""
    try:
        verification_token = await auth_service.create_email_verification_token(
            current_user["user_id"]
        )
        await email_service.send_verification_email(
            current_user["email"], 
            verification_token
        )
        return {"message": "Verification email sent"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not send verification email"
        )