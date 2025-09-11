"""
Middleware for Identity Service integration and authentication.
"""
import jwt
import requests
import json
from django.http import JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import cached_property
import logging
from typing import Optional, Dict, Any
import threading

logger = logging.getLogger(__name__)

# Thread-local storage for user context
_thread_locals = threading.local()


class UserContext:
    """Container for authenticated user information from JWT token."""
    
    def __init__(self, user_id: str, email: str, organization_id: str, roles: list, raw_token: dict):
        self.user_id = user_id
        self.email = email
        self.organization_id = organization_id
        self.roles = roles
        self.raw_token = raw_token
        
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
        
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.has_role('admin')
        
    def __str__(self):
        return f"UserContext(user_id={self.user_id}, email={self.email}, org={self.organization_id})"


def get_current_user() -> Optional[UserContext]:
    """Get the current authenticated user from thread-local storage."""
    return getattr(_thread_locals, 'user', None)


def set_current_user(user: Optional[UserContext]):
    """Set the current authenticated user in thread-local storage."""
    _thread_locals.user = user


class IdentityServiceMiddleware(MiddlewareMixin):
    """
    Middleware to validate JWT tokens from the Identity Service and set user context.
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.identity_service_url = getattr(settings, 'IDENTITY_SERVICE_URL', 'http://localhost:8001')
        self.jwt_cache_timeout = getattr(settings, 'JWT_CACHE_TIMEOUT', 300)  # 5 minutes
        self.skip_paths = getattr(settings, 'JWT_SKIP_PATHS', [
            '/admin/',
            '/health/',
            '/api/docs/',
            '/api/openapi.json',
            '/static/',
            '/media/',
        ])
    
    def process_request(self, request):
        """Process the request to validate JWT token and set user context."""
        # Clear any existing user context
        set_current_user(None)
        
        # Skip authentication for certain paths
        if self._should_skip_auth(request):
            return None
            
        # Extract JWT token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return self._unauthorized_response("Missing or invalid authorization header")
            
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        try:
            # Validate token and get user context
            user_context = self._validate_token(token)
            if not user_context:
                return self._unauthorized_response("Invalid or expired token")
                
            # Set user context for this request
            set_current_user(user_context)
            
            # Add user info to request object for convenience
            request.user_context = user_context
            
        except Exception as e:
            logger.error(f"Error validating JWT token: {e}")
            return self._unauthorized_response("Token validation failed")
            
        return None
    
    def process_response(self, request, response):
        """Clean up thread-local storage after request."""
        set_current_user(None)
        return response
    
    def _should_skip_auth(self, request) -> bool:
        """Check if authentication should be skipped for this request."""
        path = request.path
        return any(path.startswith(skip_path) for skip_path in self.skip_paths)
    
    def _validate_token(self, token: str) -> Optional[UserContext]:
        """Validate JWT token with Identity Service."""
        # Check cache first
        cache_key = f"jwt_validation:{token[:32]}"  # Use first 32 chars as cache key
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        try:
            # Call Identity Service to validate token
            response = requests.get(
                f"{self.identity_service_url}/auth/verify",
                headers={'Authorization': f'Bearer {token}'},
                timeout=5
            )
            
            if response.status_code == 200:
                token_data = response.json()
                user_context = UserContext(
                    user_id=token_data.get('sub'),
                    email=token_data.get('email'),
                    organization_id=token_data.get('organization_id'),
                    roles=token_data.get('roles', []),
                    raw_token=token_data
                )
                
                # Cache the validation result
                cache.set(cache_key, user_context, self.jwt_cache_timeout)
                
                return user_context
            else:
                logger.warning(f"Token validation failed with status {response.status_code}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Failed to validate token with Identity Service: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {e}")
            return None
    
    def _unauthorized_response(self, message: str) -> JsonResponse:
        """Return a 401 Unauthorized response."""
        return JsonResponse(
            {
                'error': 'Unauthorized',
                'message': message,
                'status_code': 401
            },
            status=401
        )


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware to automatically populate audit fields in models.
    This should be placed after IdentityServiceMiddleware in MIDDLEWARE setting.
    """
    
    def process_request(self, request):
        """Set up audit context for the request."""
        user_context = get_current_user()
        if user_context:
            # Store user info in request for use in model saves
            request._audit_user_id = user_context.user_id
            request._audit_organization_id = user_context.organization_id
        return None