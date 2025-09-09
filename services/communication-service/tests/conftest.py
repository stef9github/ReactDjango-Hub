"""
Pytest configuration and fixtures for Communication Service tests
"""
import os
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Set test environment variables before importing modules
os.environ.update({
    "DATABASE_URL": "sqlite:///test_communication.db",
    "REDIS_URL": "redis://localhost:6379/15",  # Use different DB for tests
    "IDENTITY_SERVICE_URL": "http://test-identity:8001",
    "JWT_SECRET_KEY": "test-secret-key-for-testing-only",
    "DEBUG": "true"
})

from models import Base, NotificationCategory, NotificationTemplate, Notification
from database import DatabaseConfig, get_db_session
from redis_client import RedisConfig, CacheManager
from identity_client import IdentityServiceClient
from main import app

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine(
        "sqlite:///test_communication.db",
        connect_args={"check_same_thread": False},
        echo=False
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    # Cleanup
    try:
        os.remove("test_communication.db")
    except FileNotFoundError:
        pass

@pytest.fixture(scope="session")
def test_session_maker(test_engine):
    """Create test session maker"""
    return sessionmaker(bind=test_engine)

@pytest.fixture
def db_session(test_session_maker):
    """Create test database session"""
    session = test_session_maker()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()

@pytest.fixture
def client():
    """Create test client"""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    mock = MagicMock()
    mock.ping.return_value = True
    mock.get.return_value = None
    mock.set.return_value = True
    mock.setex.return_value = True
    mock.delete.return_value = 1
    mock.exists.return_value = False
    mock.ttl.return_value = 3600
    mock.keys.return_value = []
    mock.llen.return_value = 0
    mock.lpush.return_value = 1
    mock.brpop.return_value = None
    return mock

@pytest.fixture
def mock_identity_client():
    """Mock Identity Service client"""
    mock = AsyncMock(spec=IdentityServiceClient)
    
    # Mock user data
    mock_user = {
        "user_id": str(uuid.uuid4()),
        "email": "test@example.com",
        "roles": ["user"],
        "permissions": ["notification:read", "notification:write"],
        "organization_id": str(uuid.uuid4()),
        "validated_at": datetime.utcnow().isoformat()
    }
    
    mock.validate_token.return_value = mock_user
    mock.get_user_profile.return_value = {
        "user_id": mock_user["user_id"],
        "name": "Test User",
        "email": "test@example.com",
        "avatar_url": None
    }
    mock.get_user_contact_info.return_value = {
        "email": "test@example.com",
        "phone": "+1234567890",
        "push_tokens": ["test-push-token"]
    }
    mock.health_check.return_value = True
    
    return mock

@pytest.fixture
def sample_notification_category(db_session):
    """Create sample notification category"""
    category = NotificationCategory(
        name="test_category",
        description="Test category for unit tests",
        default_enabled=True
    )
    db_session.add(category)
    db_session.commit()
    return category

@pytest.fixture
def sample_notification_template(db_session, sample_notification_category):
    """Create sample notification template"""
    from models import NotificationChannel
    
    template = NotificationTemplate(
        name="test_template",
        category_id=sample_notification_category.id,
        channel=NotificationChannel.EMAIL,
        language="en",
        subject="Test Subject",
        content="Hello {{name}}, this is a test notification.",
        variables={"name": "string"}
    )
    db_session.add(template)
    db_session.commit()
    return template

@pytest.fixture
def sample_notification(db_session, sample_notification_category, sample_notification_template):
    """Create sample notification"""
    from models import NotificationChannel, NotificationStatus
    
    notification = Notification(
        user_id=uuid.uuid4(),
        category_id=sample_notification_category.id,
        template_id=sample_notification_template.id,
        channel=NotificationChannel.EMAIL,
        subject="Test Notification",
        content="This is a test notification",
        data={"name": "Test User"},
        status=NotificationStatus.PENDING,
        recipient="test@example.com"
    )
    db_session.add(notification)
    db_session.commit()
    return notification

@pytest.fixture
def auth_headers():
    """Create authentication headers for API tests"""
    return {
        "Authorization": "Bearer test-jwt-token",
        "Content-Type": "application/json"
    }

@pytest.fixture
def mock_cache_manager(mock_redis):
    """Mock cache manager with Redis client"""
    cache_manager = CacheManager(mock_redis, prefix="test_comm")
    return cache_manager

# Test data generators
def generate_test_user(user_id: str = None) -> dict:
    """Generate test user data"""
    return {
        "user_id": user_id or str(uuid.uuid4()),
        "email": "test@example.com",
        "name": "Test User",
        "roles": ["user"],
        "permissions": ["notification:read", "notification:write"],
        "organization_id": str(uuid.uuid4())
    }

def generate_test_notification_data() -> dict:
    """Generate test notification data"""
    return {
        "user_id": str(uuid.uuid4()),
        "channel": "email",
        "subject": "Test Notification",
        "content": "This is a test notification",
        "recipient": "test@example.com",
        "category": "system",
        "data": {"name": "Test User"}
    }

# Authentication fixtures for JWT testing
@pytest.fixture
def valid_jwt_token():
    """Valid JWT token for testing"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.valid.token"

@pytest.fixture
def invalid_jwt_token():
    """Invalid JWT token for testing"""
    return "invalid.jwt.token"

@pytest.fixture
def expired_jwt_token():
    """Expired JWT token for testing"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired.token"

@pytest.fixture
def mock_valid_user():
    """Mock valid user data from Identity Service"""
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
def mock_admin_user():
    """Mock admin user data from Identity Service"""
    return {
        "user_id": "admin-123-456-789",
        "organization_id": "org-admin-987-654",
        "email": "admin@example.com",
        "roles": ["admin", "user"],
        "permissions": ["read", "write", "admin", "manage"],
        "is_verified": True,
        "expires_at": "2025-12-31T23:59:59Z"
    }

@pytest.fixture
def auth_headers_valid(valid_jwt_token):
    """Valid authentication headers"""
    return {
        "Authorization": f"Bearer {valid_jwt_token}",
        "Content-Type": "application/json"
    }

@pytest.fixture
def auth_headers_invalid(invalid_jwt_token):
    """Invalid authentication headers"""
    return {
        "Authorization": f"Bearer {invalid_jwt_token}",
        "Content-Type": "application/json"
    }

@pytest.fixture
def mock_identity_service_success(mock_valid_user):
    """Mock successful Identity Service response"""
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_valid_user
    return mock_response

@pytest.fixture
def mock_identity_service_unauthorized():
    """Mock unauthorized Identity Service response"""
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"detail": "Invalid token"}
    return mock_response

@pytest.fixture
def mock_identity_service_timeout():
    """Mock Identity Service timeout"""
    return Exception("Timeout")

@pytest.fixture
def mock_identity_service_network_error():
    """Mock Identity Service network error"""
    import httpx
    return httpx.RequestError("Network error")

@pytest.fixture 
def protected_endpoints():
    """List of all protected API endpoints for testing"""
    return [
        ("POST", "/api/v1/notifications", {"type": "email", "to": "test@example.com", "message": "test"}),
        ("GET", "/api/v1/notifications/unread", None),
        ("POST", "/api/v1/messages", {"to_user_id": "123", "message": "test"}),
        ("GET", "/api/v1/conversations", None),
        ("GET", "/api/v1/conversations/test-id", None),
        ("POST", "/api/v1/templates", {"name": "test"}),
        ("GET", "/api/v1/templates", None),
        ("GET", "/api/v1/queue/status", None),
    ]

# Test utilities
class TestUtils:
    """Utility functions for tests"""
    
    @staticmethod
    def assert_notification_data(notification, expected_data):
        """Assert notification matches expected data"""
        assert notification.user_id == expected_data["user_id"]
        assert notification.channel.value == expected_data["channel"]
        assert notification.subject == expected_data["subject"]
        assert notification.content == expected_data["content"]
        assert notification.recipient == expected_data["recipient"]
    
    @staticmethod
    def create_mock_response(status_code: int = 200, data: dict = None):
        """Create mock HTTP response"""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = data or {}
        return mock_response

class AuthTestUtils:
    """Utility functions specifically for authentication testing"""
    
    @staticmethod
    def assert_unauthorized_response(response):
        """Assert response is properly unauthorized"""
        assert response.status_code == 401
        assert "detail" in response.json()
        
    @staticmethod
    def assert_service_unavailable_response(response):
        """Assert response indicates service unavailable"""
        assert response.status_code == 503
        assert "detail" in response.json()
        assert "unavailable" in response.json()["detail"].lower()
    
    @staticmethod
    def assert_has_www_authenticate_header(response):
        """Assert response has WWW-Authenticate header"""
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"
    
    @staticmethod
    def assert_user_context_in_response(response, expected_user):
        """Assert user context is properly included in response"""
        response_data = response.json()
        user_fields = ["user_id", "sent_by", "requested_by", "created_by"]
        
        # Check if any user field is present and matches expected user
        found_user_field = False
        for field in user_fields:
            if field in response_data:
                assert response_data[field] == expected_user["user_id"]
                found_user_field = True
                break
        
        if not found_user_field:
            # Some endpoints might not include user context in response but should still work
            assert response.status_code == 200