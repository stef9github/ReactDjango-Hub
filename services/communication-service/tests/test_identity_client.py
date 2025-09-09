"""
Tests for Identity Service client integration
"""
import pytest
import jwt
import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException

from identity_client import (
    IdentityServiceClient, IdentityServiceError, get_current_user,
    require_permissions, require_roles, UserContactResolver
)

class TestIdentityServiceClient:
    """Test IdentityServiceClient functionality"""
    
    def test_jwt_validation_success(self):
        """Test successful JWT validation"""
        client = IdentityServiceClient()
        
        # Create a valid token
        payload = {
            "sub": "user_123",
            "email": "test@example.com",
            "roles": ["user"],
            "permissions": ["read", "write"],
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        with patch.object(client, 'jwt_secret', 'test-secret'):
            token = jwt.encode(payload, 'test-secret', algorithm='HS256')
            result = client.validate_jwt_token(token)
            
            assert result["sub"] == "user_123"
            assert result["email"] == "test@example.com"
            assert result["roles"] == ["user"]
    
    def test_jwt_validation_expired(self):
        """Test JWT validation with expired token"""
        client = IdentityServiceClient()
        
        # Create an expired token
        payload = {
            "sub": "user_123",
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        
        with patch.object(client, 'jwt_secret', 'test-secret'):
            token = jwt.encode(payload, 'test-secret', algorithm='HS256')
            
            with pytest.raises(IdentityServiceError, match="Token expired"):
                client.validate_jwt_token(token)
    
    def test_jwt_validation_invalid(self):
        """Test JWT validation with invalid token"""
        client = IdentityServiceClient()
        
        with patch.object(client, 'jwt_secret', 'test-secret'):
            with pytest.raises(IdentityServiceError, match="Invalid token"):
                client.validate_jwt_token("invalid.token.here")
    
    def test_jwt_validation_no_secret(self):
        """Test JWT validation without secret configured"""
        client = IdentityServiceClient()
        client.jwt_secret = None
        
        with pytest.raises(IdentityServiceError, match="JWT secret not configured"):
            client.validate_jwt_token("some.jwt.token")
    
    @pytest.mark.asyncio
    async def test_make_request_success(self):
        """Test successful HTTP request to Identity Service"""
        client = IdentityServiceClient()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user_id": "123", "email": "test@example.com"}
        
        with patch('identity_client.httpx.AsyncClient') as mock_httpx:
            mock_client = AsyncMock()
            mock_httpx.return_value.__aenter__.return_value = mock_client
            mock_client.request.return_value = mock_response
            
            result = await client._make_request("GET", "/test")
            
            assert result == {"user_id": "123", "email": "test@example.com"}
    
    @pytest.mark.asyncio
    async def test_make_request_retry_on_timeout(self):
        """Test request retry on timeout"""
        client = IdentityServiceClient()
        client.retry_count = 2
        
        with patch('identity_client.httpx.AsyncClient') as mock_httpx, \
             patch('identity_client.asyncio.sleep') as mock_sleep:
            
            mock_client = AsyncMock()
            mock_httpx.return_value.__aenter__.return_value = mock_client
            
            # First call times out, second succeeds
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"success": True}
            
            mock_client.request.side_effect = [
                Exception("Timeout"),
                mock_response
            ]
            
            result = await client._make_request("GET", "/test")
            
            assert result == {"success": True}
            assert mock_client.request.call_count == 2
            mock_sleep.assert_called_once_with(1)  # 2^0 = 1 second
    
    @pytest.mark.asyncio
    async def test_make_request_max_retries_exceeded(self):
        """Test request fails after max retries"""
        client = IdentityServiceClient()
        client.retry_count = 2
        
        with patch('identity_client.httpx.AsyncClient') as mock_httpx, \
             patch('identity_client.asyncio.sleep'):
            
            mock_client = AsyncMock()
            mock_httpx.return_value.__aenter__.return_value = mock_client
            mock_client.request.side_effect = Exception("Persistent error")
            
            with pytest.raises(IdentityServiceError, match="Request failed"):
                await client._make_request("GET", "/test")
    
    @pytest.mark.asyncio
    async def test_validate_token_with_cache(self):
        """Test token validation with caching"""
        client = IdentityServiceClient()
        
        # Mock cache manager
        with patch('identity_client.cache_manager') as mock_cache:
            cached_user = {
                "user_id": "user_123",
                "email": "test@example.com",
                "validated_at": datetime.utcnow().isoformat()
            }
            mock_cache.get.return_value = cached_user
            
            result = await client.validate_token("test.jwt.token")
            
            assert result == cached_user
            mock_cache.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_token_fallback_to_service(self):
        """Test token validation fallback to service call"""
        client = IdentityServiceClient()
        
        with patch('identity_client.cache_manager') as mock_cache, \
             patch.object(client, 'validate_jwt_token') as mock_jwt_validate, \
             patch.object(client, '_make_request') as mock_request:
            
            # No cached data
            mock_cache.get.return_value = None
            
            # JWT validation fails
            mock_jwt_validate.side_effect = IdentityServiceError("Invalid token")
            
            # Service validation succeeds
            service_response = {
                "user_id": "user_123",
                "email": "test@example.com",
                "roles": ["user"]
            }
            mock_request.return_value = service_response
            
            result = await client.validate_token("test.jwt.token")
            
            assert result == service_response
            mock_request.assert_called_once_with(
                "POST",
                "/auth/validate",
                headers={"Authorization": "Bearer test.jwt.token"}
            )
            mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_profile_with_cache(self):
        """Test getting user profile with caching"""
        client = IdentityServiceClient()
        
        with patch('identity_client.cache_manager') as mock_cache:
            cached_profile = {
                "user_id": "user_123",
                "name": "Test User",
                "email": "test@example.com"
            }
            mock_cache.get.return_value = cached_profile
            
            result = await client.get_user_profile("user_123", "auth_token")
            
            assert result == cached_profile
            mock_cache.get.assert_called_with("profile:user_123")
    
    @pytest.mark.asyncio
    async def test_get_user_contact_info(self):
        """Test getting user contact information"""
        client = IdentityServiceClient()
        
        contact_data = {
            "email": "test@example.com",
            "phone": "+1234567890",
            "push_tokens": ["token1", "token2"]
        }
        
        with patch('identity_client.cache_manager') as mock_cache, \
             patch.object(client, '_make_request') as mock_request:
            
            mock_cache.get.return_value = None  # No cache
            mock_request.return_value = contact_data
            
            result = await client.get_user_contact_info("user_123", "auth_token")
            
            assert result == contact_data
            mock_request.assert_called_with(
                "GET",
                "/users/user_123/contact",
                auth_token="auth_token"
            )
            mock_cache.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_user_permissions_success(self):
        """Test successful user permission check"""
        client = IdentityServiceClient()
        
        user_data = {
            "permissions": ["read", "write", "admin"]
        }
        
        with patch.object(client, 'validate_token') as mock_validate:
            mock_validate.return_value = user_data
            
            result = await client.check_user_permissions(
                "user_123", 
                ["read", "write"], 
                "auth_token"
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_check_user_permissions_failure(self):
        """Test failed user permission check"""
        client = IdentityServiceClient()
        
        user_data = {
            "permissions": ["read"]
        }
        
        with patch.object(client, 'validate_token') as mock_validate:
            mock_validate.return_value = user_data
            
            result = await client.check_user_permissions(
                "user_123", 
                ["read", "admin"], 
                "auth_token"
            )
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_invalidate_user_cache(self):
        """Test invalidating user cache"""
        client = IdentityServiceClient()
        
        with patch('identity_client.cache_manager') as mock_cache:
            await client.invalidate_user_cache("user_123")
            
            # Should delete specific keys and clear token pattern
            expected_calls = [
                ("profile:user_123",),
                ("contact:user_123",)
            ]
            
            for call in expected_calls:
                mock_cache.delete.assert_any_call(*call)
            
            mock_cache.clear_pattern.assert_called_with("token:*")
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test successful health check"""
        client = IdentityServiceClient()
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.return_value = {"status": "healthy"}
            
            result = await client.health_check()
            
            assert result is True
            mock_request.assert_called_with("GET", "/health")
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test failed health check"""
        client = IdentityServiceClient()
        
        with patch.object(client, '_make_request') as mock_request:
            mock_request.side_effect = IdentityServiceError("Service unavailable")
            
            result = await client.health_check()
            
            assert result is False

class TestFastAPIDependencies:
    """Test FastAPI dependencies"""
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self):
        """Test successful current user retrieval"""
        mock_token = MagicMock()
        mock_token.credentials = "valid.jwt.token"
        
        user_data = {
            "user_id": "user_123",
            "email": "test@example.com",
            "roles": ["user"]
        }
        
        with patch('identity_client.identity_client') as mock_client:
            mock_client.validate_token.return_value = user_data
            
            result = await get_current_user(mock_token)
            
            assert result == user_data
            mock_client.validate_token.assert_called_with("valid.jwt.token")
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self):
        """Test current user retrieval with invalid token"""
        mock_token = MagicMock()
        mock_token.credentials = "invalid.jwt.token"
        
        with patch('identity_client.identity_client') as mock_client:
            mock_client.validate_token.side_effect = IdentityServiceError("Invalid token")
            
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_token)
            
            assert exc_info.value.status_code == 401
            assert "Invalid token" in str(exc_info.value.detail)
    
    def test_require_permissions_success(self):
        """Test successful permission requirement"""
        current_user = {
            "user_id": "user_123",
            "permissions": ["read", "write", "admin"]
        }
        
        permission_checker = require_permissions(["read", "write"])
        result = permission_checker(current_user)
        
        assert result == current_user
    
    def test_require_permissions_failure(self):
        """Test failed permission requirement"""
        current_user = {
            "user_id": "user_123",
            "permissions": ["read"]
        }
        
        permission_checker = require_permissions(["read", "admin"])
        
        with pytest.raises(HTTPException) as exc_info:
            permission_checker(current_user)
        
        assert exc_info.value.status_code == 403
        assert "Missing required permissions" in str(exc_info.value.detail)
    
    def test_require_roles_success(self):
        """Test successful role requirement"""
        current_user = {
            "user_id": "user_123",
            "roles": ["user", "admin"]
        }
        
        role_checker = require_roles(["admin", "moderator"])  # User has admin
        result = role_checker(current_user)
        
        assert result == current_user
    
    def test_require_roles_failure(self):
        """Test failed role requirement"""
        current_user = {
            "user_id": "user_123",
            "roles": ["user"]
        }
        
        role_checker = require_roles(["admin", "moderator"])
        
        with pytest.raises(HTTPException) as exc_info:
            role_checker(current_user)
        
        assert exc_info.value.status_code == 403
        assert "Missing required roles" in str(exc_info.value.detail)

class TestUserContactResolver:
    """Test UserContactResolver functionality"""
    
    def test_init(self):
        """Test UserContactResolver initialization"""
        mock_client = MagicMock()
        resolver = UserContactResolver(mock_client)
        
        assert resolver.identity_client == mock_client
    
    @pytest.mark.asyncio
    async def test_get_email_address_success(self):
        """Test successful email address retrieval"""
        mock_client = AsyncMock()
        mock_client.get_user_contact_info.return_value = {
            "email": "test@example.com",
            "phone": "+1234567890"
        }
        
        resolver = UserContactResolver(mock_client)
        result = await resolver.get_email_address("user_123", "auth_token")
        
        assert result == "test@example.com"
        mock_client.get_user_contact_info.assert_called_with("user_123", "auth_token")
    
    @pytest.mark.asyncio
    async def test_get_email_address_failure(self):
        """Test email address retrieval failure"""
        mock_client = AsyncMock()
        mock_client.get_user_contact_info.side_effect = Exception("Service error")
        
        resolver = UserContactResolver(mock_client)
        result = await resolver.get_email_address("user_123", "auth_token")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_phone_number(self):
        """Test phone number retrieval"""
        mock_client = AsyncMock()
        mock_client.get_user_contact_info.return_value = {
            "phone": "+1234567890"
        }
        
        resolver = UserContactResolver(mock_client)
        result = await resolver.get_phone_number("user_123", "auth_token")
        
        assert result == "+1234567890"
    
    @pytest.mark.asyncio
    async def test_get_push_tokens(self):
        """Test push tokens retrieval"""
        mock_client = AsyncMock()
        mock_client.get_user_contact_info.return_value = {
            "push_tokens": ["token1", "token2", "token3"]
        }
        
        resolver = UserContactResolver(mock_client)
        result = await resolver.get_push_tokens("user_123", "auth_token")
        
        assert result == ["token1", "token2", "token3"]
    
    @pytest.mark.asyncio
    async def test_resolve_recipients_email(self):
        """Test resolving email recipients"""
        mock_client = AsyncMock()
        resolver = UserContactResolver(mock_client)
        
        # Mock email addresses for multiple users
        def mock_get_contact_info(user_id, auth_token):
            contacts = {
                "user_1": {"email": "user1@example.com"},
                "user_2": {"email": "user2@example.com"},
                "user_3": {"email": None}  # No email
            }
            return contacts.get(user_id, {})
        
        mock_client.get_user_contact_info.side_effect = mock_get_contact_info
        
        result = await resolver.resolve_recipients(
            ["user_1", "user_2", "user_3"], 
            "email", 
            "auth_token"
        )
        
        expected = {
            "user_1": "user1@example.com",
            "user_2": "user2@example.com"
            # user_3 should be excluded due to no email
        }
        
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_resolve_recipients_sms(self):
        """Test resolving SMS recipients"""
        mock_client = AsyncMock()
        resolver = UserContactResolver(mock_client)
        
        def mock_get_contact_info(user_id, auth_token):
            contacts = {
                "user_1": {"phone": "+1234567890"},
                "user_2": {"phone": "+0987654321"}
            }
            return contacts.get(user_id, {})
        
        mock_client.get_user_contact_info.side_effect = mock_get_contact_info
        
        result = await resolver.resolve_recipients(
            ["user_1", "user_2"], 
            "sms", 
            "auth_token"
        )
        
        expected = {
            "user_1": "+1234567890",
            "user_2": "+0987654321"
        }
        
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_resolve_recipients_in_app(self):
        """Test resolving in-app recipients"""
        mock_client = AsyncMock()
        resolver = UserContactResolver(mock_client)
        
        # For in-app notifications, should return user IDs as contacts
        result = await resolver.resolve_recipients(
            ["user_1", "user_2"], 
            "in_app", 
            "auth_token"
        )
        
        expected = {
            "user_1": "user_1",
            "user_2": "user_2"
        }
        
        assert result == expected
        # Should not call get_user_contact_info for in-app
        mock_client.get_user_contact_info.assert_not_called()