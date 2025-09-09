"""
Pytest configuration and fixtures for Communication Service tests
Comprehensive testing setup following standardized microservices approach
"""
import os
import pytest
import uuid
import asyncio
import tempfile
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, AsyncGenerator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from fastapi.testclient import TestClient

# Set test environment variables before importing modules
os.environ.update({
    "DATABASE_URL": "sqlite:///test_communication.db",
    "REDIS_URL": "redis://localhost:6379/15",  # Use different DB for tests
    "IDENTITY_SERVICE_URL": "http://test-identity:8001",
    "JWT_SECRET_KEY": "test-secret-key-for-testing-only",
    "DEBUG": "true",
    "TESTING": "true",
    "LOG_LEVEL": "ERROR",
    "EMAIL_BACKEND": "console",  # Use console backend for testing
    "CELERY_ALWAYS_EAGER": "true",  # Execute tasks synchronously in tests
    "CELERY_TASK_ALWAYS_EAGER": "true"
})

from models import Base, NotificationCategory, NotificationTemplate, Notification
from database import DatabaseConfig, get_db_session
from redis_client import RedisConfig, CacheManager
from identity_client import IdentityServiceClient
from main import app

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

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
async def async_test_engine():
    """Create async test database engine"""
    test_database_url = "sqlite+aiosqlite:///test_communication_async.db"
    engine = create_async_engine(test_database_url, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
    try:
        os.remove("test_communication_async.db")
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
async def async_db_session(async_test_engine):
    """Create async test database session"""
    async_session = sessionmaker(
        async_test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
def override_get_db(db_session):
    """Override database dependency for testing"""
    async def _get_test_db():
        yield db_session
    
    app.dependency_overrides[get_db_session] = _get_test_db
    yield
    app.dependency_overrides.clear()

@pytest.fixture
def mock_redis():
    """Mock Redis client with comprehensive methods"""
    mock = AsyncMock()
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
    mock.hget.return_value = None
    mock.hset.return_value = True
    mock.hdel.return_value = 1
    mock.expire.return_value = True
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

# Enhanced Authentication Fixtures
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
def mock_user_data():
    """Mock authenticated user data"""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "organization_id": "org-123",
        "roles": ["user"],
        "permissions": ["notification:read", "notification:write"],
        "is_active": True,
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
    }

@pytest.fixture
def admin_user_data():
    """Mock admin user data"""
    return {
        "user_id": "admin-user-123", 
        "email": "admin@example.com",
        "organization_id": "org-123",
        "roles": ["admin", "user"],
        "permissions": ["notification:read", "notification:write", "notification:delete", "admin"],
        "is_active": True,
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
    }

@pytest.fixture
def auth_headers(valid_jwt_token):
    """Create valid authentication headers for API tests"""
    return {
        "Authorization": f"Bearer {valid_jwt_token}",
        "Content-Type": "application/json"
    }

@pytest.fixture
def admin_auth_headers(valid_jwt_token):
    """Create admin authentication headers for API tests"""
    return {
        "Authorization": f"Bearer {valid_jwt_token}",
        "Content-Type": "application/json",
        "X-Admin-Access": "true"
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

# Additional Enhanced Fixtures for Comprehensive Testing

# Notification Provider Mock Fixtures
@pytest.fixture
def mock_email_provider():
    """Mock email notification provider"""
    with patch('providers.email.EmailProvider') as mock_provider:
        mock_instance = AsyncMock()
        mock_instance.send.return_value = {"status": "sent", "message_id": "email-123"}
        mock_provider.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_sms_provider():
    """Mock SMS notification provider"""
    with patch('providers.sms.SMSProvider') as mock_provider:
        mock_instance = AsyncMock()
        mock_instance.send.return_value = {"status": "sent", "message_id": "sms-123"}
        mock_provider.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_push_provider():
    """Mock push notification provider"""
    with patch('providers.push.PushProvider') as mock_provider:
        mock_instance = AsyncMock()
        mock_instance.send.return_value = {"status": "sent", "message_id": "push-123"}
        mock_provider.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_in_app_provider():
    """Mock in-app notification provider"""
    with patch('providers.in_app.InAppProvider') as mock_provider:
        mock_instance = AsyncMock()
        mock_instance.send.return_value = {"status": "sent", "message_id": "inapp-123"}
        mock_instance.get_unread_notifications.return_value = []
        mock_instance.get_unread_count.return_value = 0
        mock_provider.return_value = mock_instance
        yield mock_instance

# Celery Mock Fixtures
@pytest.fixture
def mock_celery_task():
    """Mock Celery task execution"""
    with patch('tasks.notification_tasks.send_notification') as mock_task:
        mock_result = MagicMock()
        mock_result.id = "task-123"
        mock_result.status = "SUCCESS"
        mock_result.result = {"status": "sent", "message_id": "msg-123"}
        mock_task.apply_async.return_value = mock_result
        yield mock_task

# Template Engine Mock Fixtures
@pytest.fixture
def mock_template_engine():
    """Mock template rendering engine"""
    with patch('services.template_engine.TemplateEngine') as mock_engine:
        mock_instance = MagicMock()
        mock_instance.render.return_value = "Rendered template content"
        mock_instance.validate_template.return_value = True
        mock_engine.return_value = mock_instance
        yield mock_instance

# Test Data Factories
class NotificationDataFactory:
    """Factory for generating test notification data"""
    
    @staticmethod
    def create_email_notification(user_id: str = None, **kwargs):
        """Create email notification test data"""
        default_data = {
            "user_id": user_id or str(uuid.uuid4()),
            "channel": "email",
            "subject": "Test Email Notification",
            "content": "This is a test email notification content.",
            "recipient": "test@example.com",
            "category": "system",
            "priority": "normal",
            "data": {"name": "Test User", "action": "test_action"}
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_sms_notification(user_id: str = None, **kwargs):
        """Create SMS notification test data"""
        default_data = {
            "user_id": user_id or str(uuid.uuid4()),
            "channel": "sms",
            "content": "Test SMS notification message.",
            "recipient": "+1234567890",
            "category": "alert",
            "priority": "high",
            "data": {"code": "123456"}
        }
        default_data.update(kwargs)
        return default_data
    
    @staticmethod
    def create_push_notification(user_id: str = None, **kwargs):
        """Create push notification test data"""
        default_data = {
            "user_id": user_id or str(uuid.uuid4()),
            "channel": "push",
            "title": "Test Push Notification",
            "content": "This is a test push notification.",
            "recipient": "push-token-123",
            "category": "update",
            "priority": "normal",
            "data": {"deep_link": "/notifications"}
        }
        default_data.update(kwargs)
        return default_data

# Test fixtures for specific notification types
@pytest.fixture
def email_notification_data(mock_user_data):
    """Email notification test data"""
    return NotificationDataFactory.create_email_notification(user_id=mock_user_data["user_id"])

@pytest.fixture
def sms_notification_data(mock_user_data):
    """SMS notification test data"""
    return NotificationDataFactory.create_sms_notification(user_id=mock_user_data["user_id"])

@pytest.fixture
def push_notification_data(mock_user_data):
    """Push notification test data"""
    return NotificationDataFactory.create_push_notification(user_id=mock_user_data["user_id"])