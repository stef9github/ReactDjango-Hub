"""
Core Authentication Services
"""

import bcrypt
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload

from app.models.enhanced_models import User, Role, Permission, UserRole, EmailVerification, PasswordReset
from app.services.email_service import EmailService
from app.core.config import settings


@dataclass
class AuthResult:
    """Authentication result"""
    success: bool
    user: Optional[User] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None
    error: Optional[str] = None


class TokenService:
    """JWT token management service"""
    
    def __init__(self):
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = "HS256"
        self.access_token_expire = timedelta(hours=1)
        self.refresh_token_expire = timedelta(days=7)
    
    def generate_tokens(self, user: User) -> Dict[str, Any]:
        """Generate access and refresh tokens for user"""
        now = datetime.utcnow()
        access_expires = now + self.access_token_expire
        refresh_expires = now + self.refresh_token_expire
        
        # Access token payload
        access_payload = {
            "sub": str(user.id),
            "email": user.email,
            "exp": access_expires,
            "iat": now,
            "type": "access",
            "tenant_id": str(user.organization_id) if user.organization_id else None
        }
        
        # Refresh token payload
        refresh_payload = {
            "sub": str(user.id),
            "exp": refresh_expires,
            "iat": now,
            "type": "refresh"
        }
        
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",
            "expires_in": int(self.access_token_expire.total_seconds()),
            "user_id": str(user.id),
            "tenant_id": str(user.organization_id) if user.organization_id else None
        }
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


class RateLimiter:
    """Redis-based rate limiter"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def check_limit(self, key: str, limit: int = 5, window: int = 300) -> bool:
        """Check if request is within rate limit"""
        try:
            current = await self.redis.get(key)
            if current is None:
                await self.redis.setex(key, window, 1)
                return True
            elif int(current) < limit:
                await self.redis.incr(key)
                return True
            else:
                return False
        except:
            # If Redis is down, allow the request
            return True


class AuthService:
    """Main authentication service"""
    
    def __init__(self, db_session: AsyncSession, redis_client: redis.Redis):
        self.db = db_session
        self.redis = redis_client
        self.token_service = TokenService()
        self.email_service = EmailService(db_session)
    
    async def register_with_verification(
        self,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register user with email verification requirement"""
        try:
            # Check if user already exists
            stmt = select(User).where(User.email == email)
            result = await self.db.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                raise Exception("User with this email already exists")
            
            # Hash password
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Create user in pending verification status
            user = User(
                email=email,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                display_name=f"{first_name} {last_name}" if first_name and last_name else email,
                status="pending_verification",
                is_verified=False,
                organization_id=tenant_id
            )
            
            self.db.add(user)
            await self.db.flush()  # Get the user ID
            
            await self.db.commit()
            
            return {
                "user_id": str(user.id),
                "email": user.email,
                "status": user.status,
                "created_at": user.created_at.isoformat()
            }
            
        except Exception as e:
            await self.db.rollback()
            raise e
    
    async def send_verification_email(self, email: str) -> Dict[str, Any]:
        """Send verification email to user"""
        try:
            # Find user
            stmt = select(User).where(User.email == email)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                # Don't reveal if email exists
                return {
                    "success": True,
                    "message": "If this email exists, a verification email has been sent."
                }
            
            # Send verification email
            result = await self.email_service.send_verification_email(
                str(user.id), 
                user.email, 
                user.first_name
            )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error sending verification email: {str(e)}"
            }
    
    async def verify_email(self, token: str, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Verify email with token"""
        return await self.email_service.verify_email(token, ip_address)
    
    async def resend_verification_email(self, email: str) -> Dict[str, Any]:
        """Resend verification email"""
        return await self.email_service.resend_verification_email(email)
    
    async def check_user_verification_status(self, email: str) -> Dict[str, Any]:
        """Check if user exists and is verified"""
        try:
            stmt = select(User).where(User.email == email)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return {
                    "exists": False,
                    "email_verified": False
                }
            
            return {
                "exists": True,
                "email_verified": user.is_verified,
                "status": user.status,
                "user_id": str(user.id)
            }
            
        except Exception as e:
            return {
                "exists": False,
                "email_verified": False,
                "error": str(e)
            }
    
    async def authenticate(
        self,
        email: str,
        password: str,
        tenant_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Authenticate user and return tokens"""
        try:
            # Find user
            stmt = select(User).where(User.email == email)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                raise Exception("Invalid credentials")
            
            # Check if email is verified
            if not user.is_verified:
                raise Exception("Email verification required")
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                # Increment failed login attempts
                user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                await self.db.commit()
                raise Exception("Invalid credentials")
            
            # Reset failed attempts on successful login
            user.failed_login_attempts = 0
            user.last_login_at = datetime.utcnow()
            user.last_login_ip = ip_address
            
            await self.db.commit()
            
            # Generate tokens
            token_data = self.token_service.generate_tokens(user)
            token_data["timestamp"] = datetime.utcnow().isoformat()
            
            return token_data
            
        except Exception as e:
            await self.db.rollback()
            raise e
    
    async def validate_token(self, token: str) -> Optional[User]:
        """Validate JWT token and return user"""
        try:
            payload = self.token_service.verify_token(token)
            if not payload:
                return None
            
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            # Get user from database
            stmt = select(User).where(User.id == user_id)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user or not user.is_verified or user.status != "active":
                return None
            
            return user
            
        except Exception:
            return None
    
    async def validate_token_details(self, token: str) -> Dict[str, Any]:
        """Validate token and return detailed info"""
        try:
            payload = self.token_service.verify_token(token)
            if not payload:
                return {"valid": False}
            
            user_id = payload.get("sub")
            stmt = select(User).where(User.id == user_id)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return {"valid": False}
            
            # Get user roles and permissions
            roles = await self.get_user_roles(str(user.id))
            permissions = await self.get_user_permissions(str(user.id))
            
            return {
                "valid": True,
                "user_id": str(user.id),
                "email": user.email,
                "tenant_id": str(user.organization_id) if user.organization_id else None,
                "roles": roles,
                "permissions": permissions,
                "expires_at": payload.get("exp")
            }
            
        except Exception:
            return {"valid": False}
    
    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh access token"""
        try:
            payload = self.token_service.verify_token(refresh_token)
            if not payload or payload.get("type") != "refresh":
                return None
            
            user_id = payload.get("sub")
            stmt = select(User).where(User.id == user_id)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user or not user.is_verified:
                return None
            
            return self.token_service.generate_tokens(user)
            
        except Exception:
            return None
    
    async def logout(self, token: str, user_id: str) -> bool:
        """Logout user (invalidate token in Redis)"""
        try:
            # In a more sophisticated system, we'd maintain a blacklist of tokens
            # For now, we'll just log the logout event
            return True
        except Exception:
            return False
    
    async def get_user_roles(self, user_id: str) -> List[str]:
        """Get user roles"""
        try:
            stmt = select(UserRole).where(UserRole.user_id == user_id).options(selectinload(UserRole.role))
            result = await self.db.execute(stmt)
            user_roles = result.scalars().all()
            
            return [user_role.role.name for user_role in user_roles if user_role.role]
        except Exception:
            return []
    
    async def get_user_permissions(self, user_id: str) -> List[str]:
        """Get user permissions through roles"""
        try:
            # This would be more complex in a real system
            # For now, return basic permissions based on verification status
            stmt = select(User).where(User.id == user_id)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user or not user.is_verified:
                return []
            
            # Basic permissions for verified users
            permissions = ["read:profile", "write:profile"]
            
            # Add organization permissions if user is in an organization
            if user.organization_id:
                permissions.extend(["read:organization", "write:organization"])
            
            return permissions
        except Exception:
            return []
    
    async def check_permission(
        self, 
        user_id: str, 
        resource: str, 
        action: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if user has permission for resource/action"""
        try:
            permissions = await self.get_user_permissions(user_id)
            required_permission = f"{action}:{resource}"
            return required_permission in permissions
        except Exception:
            return False
    
    async def get_user_sessions(self, user_id: str) -> Dict[str, Any]:
        """Get user's active sessions"""
        # This would query a sessions table in a real implementation
        # For now, return a mock response
        return {
            "sessions": [],
            "current_session_id": "mock-session-id",
            "total_count": 0
        }
    
    async def revoke_session(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Revoke specific session"""
        # This would revoke a session in a real implementation
        return {
            "success": True,
            "session_id": session_id
        }
    
    async def initiate_password_reset(self, email: str) -> Dict[str, Any]:
        """Initiate password reset process"""
        try:
            # Find user
            stmt = select(User).where(User.email == email)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                # Don't reveal if email exists
                return {
                    "success": True,
                    "message": "If this email exists, a reset link has been sent."
                }
            
            # Send password reset email
            result = await self.email_service.send_password_reset_email(
                str(user.id),
                user.email,
                user.first_name
            )
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error initiating password reset: {str(e)}"
            }
    
    async def reset_password(self, token: str, new_password: str) -> Dict[str, Any]:
        """Reset password with token"""
        try:
            # Hash the provided token
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            
            # Find password reset record
            stmt = select(PasswordReset).where(
                PasswordReset.token_hash == token_hash,
                PasswordReset.is_used == False,
                PasswordReset.expires_at > datetime.utcnow()
            )
            result = await self.db.execute(stmt)
            reset_record = result.scalar_one_or_none()
            
            if not reset_record:
                raise Exception("Invalid or expired reset token")
            
            # Update user's password
            password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            stmt = update(User).where(User.id == reset_record.user_id).values(
                password_hash=password_hash,
                password_changed_at=datetime.utcnow(),
                failed_login_attempts=0,
                updated_at=datetime.utcnow()
            )
            await self.db.execute(stmt)
            
            # Mark reset token as used
            reset_record.is_used = True
            reset_record.used_at = datetime.utcnow()
            
            await self.db.commit()
            
            return {
                "success": True,
                "message": "Password reset successfully",
                "user_id": str(reset_record.user_id)
            }
            
        except Exception as e:
            await self.db.rollback()
            raise e