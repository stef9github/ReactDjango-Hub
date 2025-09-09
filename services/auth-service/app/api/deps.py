"""FastAPI dependencies for the auth service"""

from typing import AsyncGenerator, Optional
from fastapi import HTTPException, Depends, status, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.config import settings
from app.services.auth_service import AuthService, TokenService
from app.services.user_service import UserManagementService
from app.services.mfa_service import MFAService
from app.services.email_service import EmailService
from app.utils.messaging import EventPublisher

# Security dependency
security = HTTPBearer()

# Rate limiter (placeholder - implement with Redis)
class RateLimiter:
    async def __call__(self, request: Request) -> bool:
        # Implementation would use Redis to track request rates
        return True

rate_limiter = RateLimiter()


async def get_auth_service(
    session: AsyncSession = Depends(get_session)
) -> AuthService:
    """Get AuthService instance with database session"""
    return AuthService(session)


async def get_token_service() -> TokenService:
    """Get TokenService instance"""
    return TokenService()


async def get_user_service(
    session: AsyncSession = Depends(get_session)
) -> UserManagementService:
    """Get UserManagementService instance with database session"""
    return UserManagementService(session)


async def get_mfa_service(
    session: AsyncSession = Depends(get_session)
) -> MFAService:
    """Get MFAService instance with database session"""
    return MFAService(session)


async def get_email_service() -> EmailService:
    """Get EmailService instance"""
    return EmailService()


async def get_event_publisher() -> EventPublisher:
    """Get EventPublisher instance"""
    return EventPublisher()


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    token_service: TokenService = Depends(get_token_service)
) -> dict:
    """Verify JWT token and return user data"""
    try:
        token_data = await token_service.verify_token(credentials.credentials)
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return token_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed"
        )


async def get_current_user(
    token_data: dict = Depends(verify_token),
    session: AsyncSession = Depends(get_session)
) -> dict:
    """Get current user from token"""
    user_id = token_data.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: no user ID"
        )
    
    # In a real implementation, you'd fetch user from database
    return {
        "user_id": user_id,
        "email": token_data.get("email"),
        "tenant_id": token_data.get("tenant_id"),
        "roles": token_data.get("roles", []),
        "permissions": token_data.get("permissions", [])
    }


async def require_permission(
    permission: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Require specific permission"""
    user_permissions = current_user.get("permissions", [])
    if permission not in user_permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required permission: {permission}"
        )
    return current_user


async def require_role(
    role: str,
    current_user: dict = Depends(get_current_user)
) -> dict:
    """Require specific role"""
    user_roles = current_user.get("roles", [])
    if role not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required role: {role}"
        )
    return current_user


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    token_service: TokenService = Depends(get_token_service)
) -> Optional[dict]:
    """Get user from token if present, otherwise None"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    try:
        token = authorization.split(" ")[1]
        token_data = await token_service.verify_token(token)
        return token_data
    except:
        return None