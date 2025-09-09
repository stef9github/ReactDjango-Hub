"""
Unit tests for AuthService
Tests core authentication business logic
"""

import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

from app.services.auth_service import AuthService, TokenService
from app.core.security import hash_password


@pytest.mark.unit
@pytest.mark.auth
class TestAuthService:
    """Test AuthService business logic"""
    
    @pytest_asyncio.fixture
    async def auth_service(self, test_session):
        """Create AuthService instance for testing"""
        return AuthService(test_session)
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, test_user):
        """Test successful user authentication"""
        result = await auth_service.authenticate_user(
            email="testuser@example.com",
            password="testpassword123",
            ip_address="127.0.0.1",
            user_agent="test-agent"
        )
        
        assert result is not None
        assert result["user_id"] == str(test_user.id)
        assert result["email"] == test_user.email
        assert "access_token" in result
        assert "refresh_token" in result
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(self, auth_service, test_user):
        """Test authentication with invalid password"""
        with pytest.raises(Exception) as exc_info:
            await auth_service.authenticate_user(
                email="testuser@example.com",
                password="wrongpassword",
                ip_address="127.0.0.1",
                user_agent="test-agent"
            )
        
        assert "Invalid credentials" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent_email(self, auth_service):
        """Test authentication with non-existent email"""
        with pytest.raises(Exception) as exc_info:
            await auth_service.authenticate_user(
                email="nonexistent@example.com",
                password="password123",
                ip_address="127.0.0.1",
                user_agent="test-agent"
            )
        
        assert "Invalid credentials" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service):
        """Test successful user registration"""
        result = await auth_service.register_user(
            email="newuser@example.com",
            password="newpassword123",
            first_name="New",
            last_name="User",
            ip_address="127.0.0.1"
        )
        
        assert result is not None
        assert result["email"] == "newuser@example.com"
        assert "access_token" in result
        assert "user_id" in result
    
    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, auth_service, test_user):
        """Test registration with duplicate email"""
        with pytest.raises(Exception) as exc_info:
            await auth_service.register_user(
                email="testuser@example.com",  # Already exists
                password="password123",
                first_name="Test",
                last_name="User",
                ip_address="127.0.0.1"
            )
        
        assert "already exists" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_get_user_permissions(self, auth_service, test_admin_user):
        """Test getting user permissions"""
        permissions = await auth_service.get_user_permissions(str(test_admin_user.id))
        
        assert isinstance(permissions, list)
        # Admin user should have permissions
        # This depends on your permission system setup


@pytest.mark.unit
class TestTokenService:
    """Test TokenService functionality"""
    
    def test_create_access_token(self):
        """Test access token creation"""
        token_service = TokenService()
        
        payload = {
            "user_id": "test-user-id",
            "email": "test@example.com",
            "roles": ["user"]
        }
        
        token = token_service.create_access_token(payload)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_refresh_token(self):
        """Test refresh token creation"""
        token_service = TokenService()
        
        user_id = "test-user-id"
        token = token_service.create_refresh_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    @pytest.mark.asyncio
    async def test_verify_token_valid(self):
        """Test verifying valid token"""
        token_service = TokenService()
        
        payload = {
            "user_id": "test-user-id",
            "email": "test@example.com",
            "roles": ["user"]
        }
        
        token = token_service.create_access_token(payload)
        verified_payload = await token_service.verify_token(token)
        
        assert verified_payload is not None
        assert verified_payload["user_id"] == "test-user-id"
        assert verified_payload["email"] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_verify_token_invalid(self):
        """Test verifying invalid token"""
        token_service = TokenService()
        
        invalid_token = "invalid.token.here"
        verified_payload = await token_service.verify_token(invalid_token)
        
        assert verified_payload is None
    
    @pytest.mark.asyncio
    async def test_refresh_token_valid(self):
        """Test refreshing valid token"""
        token_service = TokenService()
        
        user_id = "test-user-id"
        refresh_token = token_service.create_refresh_token(user_id)
        
        with patch.object(token_service, '_validate_refresh_token', return_value=True):
            result = await token_service.refresh_token(refresh_token)
            
            assert result is not None
            assert "access_token" in result
            assert "expires_in" in result


@pytest.mark.unit
class TestPasswordSecurity:
    """Test password hashing and verification"""
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        from app.core.security import verify_password
        
        password = "testpassword123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        from app.core.security import verify_password
        
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False