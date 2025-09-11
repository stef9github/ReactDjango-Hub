"""
Authentication decorators and utilities for Django Ninja API endpoints.
"""
from functools import wraps
from django.http import JsonResponse
from ninja import NinjaAPI
from ninja.security import HttpBearer
from ninja.errors import HttpError
from typing import Optional, List
from .middleware import get_current_user, UserContext


class JWTAuth(HttpBearer):
    """
    Django Ninja authentication class for JWT tokens.
    Validates tokens via the Identity Service middleware.
    """
    
    def authenticate(self, request, token: str) -> Optional[UserContext]:
        """
        Authenticate the request using JWT token.
        This relies on the IdentityServiceMiddleware to validate the token.
        """
        user_context = get_current_user()
        if user_context:
            return user_context
        
        # If no user context, the middleware should have returned 401
        # But in case it didn't, we raise an error here
        raise HttpError(401, "Authentication required")


# Global JWT auth instance
jwt_auth = JWTAuth()


def require_auth(func=None, *, roles: Optional[List[str]] = None):
    """
    Decorator to require authentication for Django Ninja endpoints.
    
    Args:
        roles: Optional list of required roles. If provided, user must have at least one of these roles.
    
    Usage:
        @require_auth
        def my_endpoint(request):
            pass
            
        @require_auth(roles=['admin', 'manager'])
        def admin_endpoint(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            user_context = get_current_user()
            
            if not user_context:
                raise HttpError(401, "Authentication required")
            
            # Check roles if specified
            if roles:
                if not any(user_context.has_role(role) for role in roles):
                    raise HttpError(403, f"Required roles: {roles}")
            
            # Add user_context to request for convenience
            request.user_context = user_context
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    
    if func is None:
        return decorator
    else:
        return decorator(func)


def require_admin(func):
    """Decorator to require admin role for Django Ninja endpoints."""
    return require_auth(roles=['admin'])(func)


def require_organization_access(func):
    """
    Decorator to ensure user can only access data from their organization.
    This adds organization filtering to querysets automatically.
    """
    @wraps(func)
    def wrapped_view(request, *args, **kwargs):
        user_context = get_current_user()
        
        if not user_context:
            raise HttpError(401, "Authentication required")
        
        if not user_context.organization_id:
            raise HttpError(403, "Organization membership required")
        
        # Add organization context to request
        request.organization_id = user_context.organization_id
        
        return func(request, *args, **kwargs)
    return wrapped_view


class AuthenticatedAPIRouter:
    """
    Helper class to create authenticated API routes with automatic organization isolation.
    """
    
    def __init__(self, api: NinjaAPI, prefix: str = "", auth=None):
        self.api = api
        self.prefix = prefix
        self.auth = auth or jwt_auth
    
    def get(self, path: str, **kwargs):
        """Create authenticated GET endpoint."""
        return self.api.get(f"{self.prefix}{path}", auth=self.auth, **kwargs)
    
    def post(self, path: str, **kwargs):
        """Create authenticated POST endpoint."""
        return self.api.post(f"{self.prefix}{path}", auth=self.auth, **kwargs)
    
    def put(self, path: str, **kwargs):
        """Create authenticated PUT endpoint."""
        return self.api.put(f"{self.prefix}{path}", auth=self.auth, **kwargs)
    
    def patch(self, path: str, **kwargs):
        """Create authenticated PATCH endpoint."""
        return self.api.patch(f"{self.prefix}{path}", auth=self.auth, **kwargs)
    
    def delete(self, path: str, **kwargs):
        """Create authenticated DELETE endpoint."""
        return self.api.delete(f"{self.prefix}{path}", auth=self.auth, **kwargs)


def get_user_queryset(model_class, user_context: Optional[UserContext] = None):
    """
    Get a queryset filtered by user's organization for multi-tenant isolation.
    
    Args:
        model_class: The Django model class
        user_context: Optional user context. If not provided, gets from thread-local.
    
    Returns:
        Filtered queryset for the user's organization
    """
    if not user_context:
        user_context = get_current_user()
    
    if not user_context or not user_context.organization_id:
        return model_class.objects.none()
    
    return model_class.objects.filter(organization_id=user_context.organization_id)


def check_object_access(obj, user_context: Optional[UserContext] = None) -> bool:
    """
    Check if user has access to a specific object based on organization.
    
    Args:
        obj: The model instance to check
        user_context: Optional user context. If not provided, gets from thread-local.
    
    Returns:
        True if user has access, False otherwise
    """
    if not user_context:
        user_context = get_current_user()
    
    if not user_context:
        return False
    
    # Check if object has organization_id field and if it matches user's organization
    if hasattr(obj, 'organization_id'):
        return str(obj.organization_id) == str(user_context.organization_id)
    
    # If no organization_id field, allow access (for shared resources)
    return True


# Utility functions for common authentication patterns

def get_current_user_or_403() -> UserContext:
    """Get current user or raise 403 error."""
    user = get_current_user()
    if not user:
        raise HttpError(403, "Authentication required")
    return user


def get_current_organization_or_403() -> str:
    """Get current user's organization ID or raise 403 error."""
    user = get_current_user_or_403()
    if not user.organization_id:
        raise HttpError(403, "Organization membership required")
    return user.organization_id