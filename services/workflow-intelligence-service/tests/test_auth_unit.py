"""
Unit tests for JWT authentication integration
"""
import pytest
from unittest.mock import AsyncMock, patch, Mock
from fastapi import HTTPException, status
import httpx

from main import validate_jwt_token
from tests.conftest import mock_valid_token, mock_invalid_token

class TestJWTValidation:
    """Test JWT token validation function"""
    
    @pytest.mark.asyncio
    async def test_valid_token_success(self, mock_valid_token):
        """Test successful token validation"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "user_id": "user-123",
            "email": "test@example.com",
            "organization_id": "org-123",
            "roles": ["user", "workflow_user"]
        }
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            result = await validate_jwt_token(mock_valid_token)
            
            assert result["user_id"] == "user-123"
            assert result["email"] == "test@example.com"
            assert result["organization_id"] == "org-123"
            assert "user" in result["roles"]
    
    @pytest.mark.asyncio
    async def test_invalid_token_401(self, mock_invalid_token):
        """Test invalid token returns 401"""
        mock_response = Mock()
        mock_response.status_code = 401
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(HTTPException) as exc_info:
                await validate_jwt_token(mock_invalid_token)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Invalid or expired token" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_identity_service_timeout(self, mock_valid_token):
        """Test Identity Service timeout handling"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Request timeout")
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await validate_jwt_token(mock_valid_token)
            
            assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert "temporarily unavailable" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_identity_service_network_error(self, mock_valid_token):
        """Test Identity Service network error handling"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.RequestError("Network error")
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await validate_jwt_token(mock_valid_token)
            
            assert exc_info.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            assert "Authentication service unavailable" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_identity_service_unexpected_status(self, mock_valid_token):
        """Test Identity Service unexpected status code"""
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(HTTPException) as exc_info:
                await validate_jwt_token(mock_valid_token)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Token validation failed" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_unexpected_exception_handling(self, mock_valid_token):
        """Test handling of unexpected exceptions"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=Exception("Unexpected error")
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await validate_jwt_token(mock_valid_token)
            
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert "Token validation failed" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_identity_service_request_format(self, mock_valid_token):
        """Test that requests to Identity Service are properly formatted"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user_id": "user-123"}
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.post = mock_post
            
            await validate_jwt_token(mock_valid_token)
            
            # Verify the request was made with correct parameters
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            
            assert "http://localhost:8001/auth/validate" in args[0]
            assert kwargs["headers"]["Authorization"] == f"Bearer {mock_valid_token.credentials}"
            assert kwargs["timeout"] == 5.0

class TestAuthenticationLogging:
    """Test authentication logging functionality"""
    
    @pytest.mark.asyncio
    async def test_successful_validation_logging(self, mock_valid_token):
        """Test that successful validations are logged"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"user_id": "user-123"}
        
        with patch("httpx.AsyncClient") as mock_client, \
             patch("main.logger") as mock_logger:
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            await validate_jwt_token(mock_valid_token)
            
            mock_logger.info.assert_called_with("Token validated for user: user-123")
    
    @pytest.mark.asyncio
    async def test_invalid_token_logging(self, mock_invalid_token):
        """Test that invalid tokens are logged as warnings"""
        mock_response = Mock()
        mock_response.status_code = 401
        
        with patch("httpx.AsyncClient") as mock_client, \
             patch("main.logger") as mock_logger:
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            
            with pytest.raises(HTTPException):
                await validate_jwt_token(mock_invalid_token)
            
            mock_logger.warning.assert_called_with("Invalid or expired token provided")
    
    @pytest.mark.asyncio
    async def test_error_logging(self, mock_valid_token):
        """Test that errors are logged appropriately"""
        with patch("httpx.AsyncClient") as mock_client, \
             patch("main.logger") as mock_logger:
            
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )
            
            with pytest.raises(HTTPException):
                await validate_jwt_token(mock_valid_token)
            
            mock_logger.error.assert_called_with("Timeout calling Identity Service for token validation")