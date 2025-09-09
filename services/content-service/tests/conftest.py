"""
Test fixtures and configuration for content service tests.
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def valid_token():
    """Mock valid JWT token"""
    return "valid.jwt.token"


@pytest.fixture
def invalid_token():
    """Mock invalid JWT token"""
    return "invalid.jwt.token"


@pytest.fixture
def expired_token():
    """Mock expired JWT token"""
    return "expired.jwt.token"


@pytest.fixture
def mock_user_data():
    """Mock user data returned by Identity Service"""
    return {
        "user_id": "12345678-1234-5678-9012-123456789012",
        "organization_id": "87654321-4321-8765-2109-876543210987",
        "email": "test@example.com",
        "roles": ["user"],
        "permissions": ["read", "write"],
        "is_verified": True,
        "expires_at": "2025-12-31T23:59:59Z"
    }


@pytest.fixture
def admin_user_data():
    """Mock admin user data"""
    return {
        "user_id": "admin-uuid-1234-5678-9012-123456789012",
        "organization_id": "87654321-4321-8765-2109-876543210987",
        "email": "admin@example.com",
        "roles": ["admin", "user"],
        "permissions": ["read", "write", "delete", "admin"],
        "is_verified": True,
        "expires_at": "2025-12-31T23:59:59Z"
    }


@pytest.fixture
def regular_user_data():
    """Mock regular user data"""
    return {
        "user_id": "user-uuid-1234-5678-9012-123456789012",
        "organization_id": "87654321-4321-8765-2109-876543210987",
        "email": "user@example.com", 
        "roles": ["user"],
        "permissions": ["read", "write"],
        "is_verified": True,
        "expires_at": "2025-12-31T23:59:59Z"
    }


@pytest.fixture
def mock_identity_service_success():
    """Mock successful Identity Service response"""
    def _mock_response(mock_user_data):
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        return mock_response
    return _mock_response


@pytest.fixture
def mock_identity_service_failure():
    """Mock failed Identity Service response"""
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"detail": "Invalid token"}
    return mock_response


@pytest.fixture
def mock_identity_service_timeout():
    """Mock Identity Service timeout"""
    def _mock_timeout():
        import httpx
        raise httpx.TimeoutException("Timeout")
    return _mock_timeout


@pytest.fixture
def mock_identity_service_network_error():
    """Mock Identity Service network error"""
    def _mock_network_error():
        import httpx
        raise httpx.RequestError("Network error")
    return _mock_network_error


@pytest.fixture
def mock_database_session():
    """Mock database session"""
    session_mock = AsyncMock()
    return session_mock


def mock_identity_responses(status_code, json_data=None, exception=None):
    """Helper function to create mock Identity Service responses"""
    if exception:
        raise exception
    
    mock_response = AsyncMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data or {}
    return mock_response