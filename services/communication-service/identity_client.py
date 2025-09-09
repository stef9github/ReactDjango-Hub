"""
Identity Service client for Communication Service
Handles authentication, user data retrieval, and service-to-service communication
"""
import os
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import httpx
import asyncio
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
import jwt
import logging

from redis_client import cache_manager

logger = logging.getLogger(__name__)

class IdentityServiceError(Exception):
    """Custom exception for Identity Service errors"""
    pass

class IdentityServiceClient:
    """Client for communicating with Identity Service"""
    
    def __init__(self):
        self.base_url = os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8001")
        self.service_name = "communication-service"
        self.timeout = int(os.getenv("IDENTITY_SERVICE_TIMEOUT", "30"))
        self.retry_count = int(os.getenv("IDENTITY_SERVICE_RETRY_COUNT", "3"))
        self.cache_ttl = int(os.getenv("IDENTITY_CACHE_TTL", "300"))  # 5 minutes
        
        # JWT configuration
        self.jwt_secret = os.getenv("JWT_SECRET_KEY")
        self.jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        
        if not self.jwt_secret:
            logger.warning("JWT_SECRET_KEY not set, JWT validation will fail")
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Identity Service with retry logic"""
        url = f"{self.base_url}{endpoint}"
        
        default_headers = {
            "Content-Type": "application/json",
            "X-Service-Name": self.service_name,
            "X-Trace-ID": str(uuid.uuid4())
        }
        
        if headers:
            default_headers.update(headers)
        
        if auth_token:
            default_headers["Authorization"] = f"Bearer {auth_token}"
        
        timeout = httpx.Timeout(self.timeout, connect=5.0)
        
        for attempt in range(self.retry_count):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        json=data,
                        headers=default_headers
                    )
                    
                    if response.status_code == 200:
                        return response.json()
                    elif response.status_code == 404:
                        raise IdentityServiceError(f"Resource not found: {endpoint}")
                    elif response.status_code == 401:
                        raise IdentityServiceError("Authentication failed")
                    elif response.status_code == 403:
                        raise IdentityServiceError("Authorization failed")
                    else:
                        response.raise_for_status()
                        
            except httpx.TimeoutException:
                logger.warning(f"Identity service timeout on attempt {attempt + 1}")
                if attempt == self.retry_count - 1:
                    raise IdentityServiceError("Identity service timeout")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Identity service HTTP error: {e.response.status_code}")
                if e.response.status_code >= 400 and e.response.status_code < 500:
                    # Client errors shouldn't be retried
                    raise IdentityServiceError(f"Client error: {e.response.status_code}")
                elif attempt == self.retry_count - 1:
                    raise IdentityServiceError(f"Server error: {e.response.status_code}")
                await asyncio.sleep(2 ** attempt)
                
            except Exception as e:
                logger.error(f"Identity service request error: {e}")
                if attempt == self.retry_count - 1:
                    raise IdentityServiceError(f"Request failed: {str(e)}")
                await asyncio.sleep(2 ** attempt)
    
    def validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token locally (fast path)"""
        try:
            if not self.jwt_secret:
                raise IdentityServiceError("JWT secret not configured")
            
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Check expiration
            if payload.get('exp') and datetime.utcfromtimestamp(payload['exp']) < datetime.utcnow():
                raise IdentityServiceError("Token expired")
            
            return payload
        except jwt.ExpiredSignatureError:
            raise IdentityServiceError("Token expired")
        except jwt.InvalidTokenError:
            raise IdentityServiceError("Invalid token")
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate token with Identity Service (authoritative)"""
        cache_key = f"token:{token[:20]}"  # Use token prefix as cache key
        
        # Try cache first
        cached_user = cache_manager.get(cache_key)
        if cached_user:
            return cached_user
        
        try:
            # Try local JWT validation first for speed
            local_payload = self.validate_jwt_token(token)
            user_data = {
                "user_id": local_payload.get("sub"),
                "email": local_payload.get("email"),
                "roles": local_payload.get("roles", []),
                "permissions": local_payload.get("permissions", []),
                "organization_id": local_payload.get("organization_id"),
                "validated_at": datetime.utcnow().isoformat()
            }
            
            # Cache for short time
            cache_manager.set(cache_key, user_data, ttl=self.cache_ttl)
            return user_data
            
        except IdentityServiceError:
            # Fall back to service validation
            user_data = await self._make_request(
                "POST",
                "/auth/validate",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Cache validated user data
            cache_manager.set(cache_key, user_data, ttl=self.cache_ttl)
            return user_data
    
    async def get_user_profile(self, user_id: str, auth_token: str) -> Dict[str, Any]:
        """Get user profile information"""
        cache_key = f"profile:{user_id}"
        
        # Try cache first
        cached_profile = cache_manager.get(cache_key)
        if cached_profile:
            return cached_profile
        
        profile_data = await self._make_request(
            "GET",
            f"/users/{user_id}/profile",
            auth_token=auth_token
        )
        
        # Cache profile data
        cache_manager.set(cache_key, profile_data, ttl=self.cache_ttl * 2)  # Cache longer
        return profile_data
    
    async def get_user_contact_info(self, user_id: str, auth_token: str) -> Dict[str, Any]:
        """Get user contact information (email, phone)"""
        cache_key = f"contact:{user_id}"
        
        cached_contact = cache_manager.get(cache_key)
        if cached_contact:
            return cached_contact
        
        contact_data = await self._make_request(
            "GET",
            f"/users/{user_id}/contact",
            auth_token=auth_token
        )
        
        cache_manager.set(cache_key, contact_data, ttl=self.cache_ttl)
        return contact_data
    
    async def get_organization_users(self, organization_id: str, auth_token: str) -> List[Dict[str, Any]]:
        """Get all users in an organization"""
        cache_key = f"org_users:{organization_id}"
        
        cached_users = cache_manager.get(cache_key)
        if cached_users:
            return cached_users
        
        users_data = await self._make_request(
            "GET",
            f"/organizations/{organization_id}/users",
            auth_token=auth_token
        )
        
        cache_manager.set(cache_key, users_data, ttl=self.cache_ttl)
        return users_data
    
    async def check_user_permissions(
        self, 
        user_id: str, 
        required_permissions: List[str], 
        auth_token: str
    ) -> bool:
        """Check if user has required permissions"""
        try:
            user_data = await self.validate_token(auth_token)
            user_permissions = user_data.get("permissions", [])
            
            # Check if user has all required permissions
            return all(perm in user_permissions for perm in required_permissions)
        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False
    
    async def get_user_roles(self, user_id: str, auth_token: str) -> List[str]:
        """Get user roles"""
        try:
            user_data = await self.validate_token(auth_token)
            return user_data.get("roles", [])
        except Exception as e:
            logger.error(f"Failed to get user roles: {e}")
            return []
    
    async def invalidate_user_cache(self, user_id: str):
        """Invalidate all cached data for a user"""
        cache_patterns = [
            f"profile:{user_id}",
            f"contact:{user_id}",
            f"token:*"  # This is broad but necessary for token cache invalidation
        ]
        
        for pattern in cache_patterns:
            if "*" in pattern:
                cache_manager.clear_pattern(pattern)
            else:
                cache_manager.delete(pattern)
    
    async def health_check(self) -> bool:
        """Check if Identity Service is healthy"""
        try:
            await self._make_request("GET", "/health")
            return True
        except Exception as e:
            logger.error(f"Identity service health check failed: {e}")
            return False

# Global identity service client
identity_client = IdentityServiceClient()

# FastAPI Security
security = HTTPBearer()

async def get_current_user(token: str = Depends(security)) -> Dict[str, Any]:
    """FastAPI dependency to get current authenticated user"""
    try:
        user_data = await identity_client.validate_token(token.credentials)
        return user_data
    except IdentityServiceError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=500, detail="Authentication service unavailable")

async def require_permissions(required_permissions: List[str]):
    """FastAPI dependency to require specific permissions"""
    def permission_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_permissions = current_user.get("permissions", [])
        
        missing_permissions = [perm for perm in required_permissions if perm not in user_permissions]
        if missing_permissions:
            raise HTTPException(
                status_code=403, 
                detail=f"Missing required permissions: {', '.join(missing_permissions)}"
            )
        
        return current_user
    
    return permission_checker

async def require_roles(required_roles: List[str]):
    """FastAPI dependency to require specific roles"""
    def role_checker(current_user: Dict[str, Any] = Depends(get_current_user)):
        user_roles = current_user.get("roles", [])
        
        # User needs at least one of the required roles
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=403,
                detail=f"Missing required roles: {', '.join(required_roles)}"
            )
        
        return current_user
    
    return role_checker

class UserContactResolver:
    """Resolve user contact information for notifications"""
    
    def __init__(self, identity_client: IdentityServiceClient):
        self.identity_client = identity_client
    
    async def get_email_address(self, user_id: str, auth_token: str) -> Optional[str]:
        """Get user's email address"""
        try:
            contact_info = await self.identity_client.get_user_contact_info(user_id, auth_token)
            return contact_info.get("email")
        except Exception as e:
            logger.error(f"Failed to get email for user {user_id}: {e}")
            return None
    
    async def get_phone_number(self, user_id: str, auth_token: str) -> Optional[str]:
        """Get user's phone number"""
        try:
            contact_info = await self.identity_client.get_user_contact_info(user_id, auth_token)
            return contact_info.get("phone")
        except Exception as e:
            logger.error(f"Failed to get phone for user {user_id}: {e}")
            return None
    
    async def get_push_tokens(self, user_id: str, auth_token: str) -> List[str]:
        """Get user's push notification tokens"""
        try:
            contact_info = await self.identity_client.get_user_contact_info(user_id, auth_token)
            return contact_info.get("push_tokens", [])
        except Exception as e:
            logger.error(f"Failed to get push tokens for user {user_id}: {e}")
            return []
    
    async def resolve_recipients(
        self, 
        user_ids: List[str], 
        channel: str, 
        auth_token: str
    ) -> Dict[str, str]:
        """Resolve contact information for multiple users"""
        recipients = {}
        
        for user_id in user_ids:
            try:
                if channel == "email":
                    contact = await self.get_email_address(user_id, auth_token)
                elif channel == "sms":
                    contact = await self.get_phone_number(user_id, auth_token)
                else:
                    contact = user_id  # For in-app notifications
                
                if contact:
                    recipients[user_id] = contact
            except Exception as e:
                logger.error(f"Failed to resolve contact for user {user_id}: {e}")
        
        return recipients

# Global user contact resolver
user_contact_resolver = UserContactResolver(identity_client)