"""
Core Authentication Services
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
import bcrypt
import jwt
from config import settings
from simple_models import (
    User, UserStatus, EmailVerification, UserSession, 
    UserActivity
)

class AuthService:
    """Core authentication service"""
    
    def __init__(self, db_session: AsyncSession):
        self.db = db_session
    
    async def register_with_verification(
        self, 
        email: str, 
        password: str, 
        first_name: str, 
        last_name: str,
        phone_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register user with email verification requirement"""
        
        # Check if user already exists
        stmt = select(User).where(User.email == email)
        existing_user = await self.db.execute(stmt)
        if existing_user.scalar_one_or_none():
            raise ValueError("Email already registered")
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user in pending verification status
        user = User(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            is_verified=settings.skip_email_verification,  # Skip verification in test mode
            status=UserStatus.ACTIVE if settings.skip_email_verification else UserStatus.PENDING_VERIFICATION
        )
        
        self.db.add(user)
        await self.db.flush()  # Get user ID
        
        # Create email verification token if needed
        verification_token = None
        if not settings.skip_email_verification:
            verification_token = await self._create_email_verification(user.id, email)
        
        # Log user creation
        await self._log_user_activity(
            user.id,
            "user_registered",
            f"User account created for {email}"
        )
        
        await self.db.commit()
        
        return {
            "user_id": str(user.id),
            "email": email,
            "verification_required": not settings.skip_email_verification,
            "verification_token": verification_token,
            "message": "Account created successfully" + (
                " (auto-verified for testing)" if settings.skip_email_verification 
                else ". Please check your email to verify your account."
            )
        }
    
    async def login(self, email: str, password: str, device_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """Authenticate user and create session"""
        
        # Get user
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise ValueError("Invalid email or password")
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise ValueError(f"Account locked until {user.locked_until}")
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            # Increment failed attempts
            await self._handle_failed_login(user.id)
            raise ValueError("Invalid email or password")
        
        # Check verification status
        if not user.is_verified:
            raise ValueError("Email verification required. Please verify your account before logging in.")
        
        # Check user status
        if user.status != UserStatus.ACTIVE:
            raise ValueError(f"Account is {user.status}")
        
        # Reset failed login attempts
        if user.failed_login_attempts > 0:
            await self._reset_failed_login_attempts(user.id)
        
        # Create session
        session_data = await self._create_user_session(user.id, device_info or {})
        
        # Update last login
        await self.db.execute(
            update(User)
            .where(User.id == user.id)
            .values(last_login_at=datetime.utcnow())
        )
        
        # Log successful login
        await self._log_user_activity(
            user.id,
            "user_login",
            f"Successful login from {device_info.get('ip_address', 'unknown')}"
        )
        
        await self.db.commit()
        
        return {
            "access_token": session_data["access_token"],
            "refresh_token": session_data["refresh_token"],
            "token_type": "Bearer",
            "expires_in": settings.jwt_access_token_expire_minutes * 60,
            "user_id": str(user.id),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_verified": user.is_verified,
                "status": user.status
            }
        }
    
    async def verify_email(self, token: str) -> Dict[str, Any]:
        """Verify email with token"""
        
        # Hash the token to match database
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Find verification record
        stmt = select(EmailVerification).where(
            EmailVerification.token_hash == token_hash,
            EmailVerification.is_verified == False,
            EmailVerification.expires_at > datetime.utcnow()
        )
        result = await self.db.execute(stmt)
        verification = result.scalar_one_or_none()
        
        if not verification:
            raise ValueError("Invalid or expired verification token")
        
        # Mark verification as completed
        verification.is_verified = True
        verification.verified_at = datetime.utcnow()
        
        # Update user status
        await self.db.execute(
            update(User)
            .where(User.id == verification.user_id)
            .values(
                is_verified=True,
                status=UserStatus.ACTIVE
            )
        )
        
        # Log email verification
        await self._log_user_activity(
            verification.user_id,
            "email_verified",
            f"Email {verification.email} successfully verified"
        )
        
        await self.db.commit()
        
        return {
            "message": "Email successfully verified",
            "user_id": str(verification.user_id),
            "email": verification.email,
            "verified_at": verification.verified_at.isoformat()
        }
    
    async def send_verification_email(self, email: str) -> Dict[str, Any]:
        """Send verification email (resend)"""
        
        # Find user
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            # Don't reveal if email exists or not for security
            return {"message": "If the email exists, verification email has been sent"}
        
        if user.is_verified:
            raise ValueError("Email is already verified")
        
        # Create new verification token
        verification_token = await self._create_email_verification(user.id, email)
        
        await self.db.commit()
        
        return {
            "message": "Verification email sent",
            "verification_token": verification_token  # In real app, this would be sent via email
        }
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        return {
            "id": str(user.id),
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "bio": user.bio,
            "avatar_url": user.avatar_url,
            "timezone": user.timezone,
            "language": user.language,
            "is_verified": user.is_verified,
            "status": user.status,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        }
    
    async def _create_email_verification(self, user_id: str, email: str) -> str:
        """Create email verification token"""
        
        # Generate secure token
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Create verification record
        verification = EmailVerification(
            user_id=user_id,
            email=email,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(hours=settings.email_verification_expire_hours)
        )
        
        self.db.add(verification)
        await self.db.flush()
        
        return token
    
    async def _create_user_session(self, user_id: str, device_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create user session with JWT tokens"""
        
        # Create JWT payload
        now = datetime.utcnow()
        access_expires = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        refresh_expires = now + timedelta(days=settings.jwt_refresh_token_expire_days)
        
        access_payload = {
            "user_id": str(user_id),
            "type": "access",
            "exp": access_expires,
            "iat": now
        }
        
        refresh_payload = {
            "user_id": str(user_id),
            "type": "refresh",
            "exp": refresh_expires,
            "iat": now
        }
        
        # Generate tokens
        access_token = jwt.encode(access_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        refresh_token = jwt.encode(refresh_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
        
        # Create session record
        session = UserSession(
            user_id=user_id,
            session_token=hashlib.sha256(access_token.encode()).hexdigest(),
            refresh_token=hashlib.sha256(refresh_token.encode()).hexdigest(),
            device_name=device_info.get("device_name"),
            device_type=device_info.get("device_type", "web"),
            user_agent=device_info.get("user_agent"),
            ip_address=device_info.get("ip_address"),
            expires_at=refresh_expires
        )
        
        self.db.add(session)
        await self.db.flush()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "session_id": str(session.id)
        }
    
    async def _handle_failed_login(self, user_id: str):
        """Handle failed login attempt"""
        
        # Increment failed attempts
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if user:
            failed_attempts = user.failed_login_attempts + 1
            locked_until = None
            
            # Lock account after 5 failed attempts
            if failed_attempts >= 5:
                locked_until = datetime.utcnow() + timedelta(hours=1)
            
            await self.db.execute(
                update(User)
                .where(User.id == user_id)
                .values(
                    failed_login_attempts=failed_attempts,
                    locked_until=locked_until
                )
            )
            
            # Log failed login
            await self._log_user_activity(
                user_id,
                "login_failed",
                f"Failed login attempt ({failed_attempts}/5)"
            )
    
    async def _reset_failed_login_attempts(self, user_id: str):
        """Reset failed login attempts"""
        
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                failed_login_attempts=0,
                locked_until=None
            )
        )
    
    async def _log_user_activity(self, user_id: str, activity_type: str, description: str):
        """Log user activity"""
        
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            description=description
        )
        
        self.db.add(activity)
        await self.db.flush()

class TokenService:
    """JWT token management service"""
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token, 
                settings.jwt_secret_key, 
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.JWTError:
            raise ValueError("Invalid token")