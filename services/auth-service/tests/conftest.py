"""
Pytest configuration and shared fixtures for Auth Service tests
"""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_session
from app.core.config import settings


# Test database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    """Create test database session"""
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture
async def test_client(test_session):
    """Create test HTTP client with database session override"""
    
    async def override_get_session():
        yield test_session
    
    app.dependency_overrides[get_session] = override_get_session
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Generate authentication headers for tests"""
    def _auth_headers(token: str):
        return {"Authorization": f"Bearer {token}"}
    return _auth_headers


@pytest_asyncio.fixture
async def test_user(test_session):
    """Create test user"""
    from app.models.enhanced_models import User
    from app.core.security import hash_password
    
    user = User(
        email="testuser@example.com",
        password_hash=hash_password("testpassword123"),
        is_active=True,
        is_verified=True
    )
    
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def test_admin_user(test_session):
    """Create test admin user"""
    from app.models.enhanced_models import User, Role, UserRole
    from app.core.security import hash_password
    
    # Create admin role
    admin_role = Role(name="admin", description="Administrator role")
    test_session.add(admin_role)
    await test_session.commit()
    await test_session.refresh(admin_role)
    
    # Create admin user
    admin_user = User(
        email="admin@example.com",
        password_hash=hash_password("adminpassword123"),
        is_active=True,
        is_verified=True
    )
    
    test_session.add(admin_user)
    await test_session.commit()
    await test_session.refresh(admin_user)
    
    # Assign admin role
    user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
    test_session.add(user_role)
    await test_session.commit()
    
    return admin_user


@pytest_asyncio.fixture
async def test_organization(test_session, test_user):
    """Create test organization"""
    from app.models.enhanced_models import Organization
    
    org = Organization(
        name="Test Organization",
        description="Test organization for unit tests",
        organization_type="company",
        created_by=test_user.id
    )
    
    test_session.add(org)
    await test_session.commit()
    await test_session.refresh(org)
    
    return org


@pytest.fixture
def mock_email_service():
    """Mock email service for tests"""
    from unittest.mock import AsyncMock
    return AsyncMock()


@pytest.fixture
def mock_redis():
    """Mock Redis for tests"""
    from unittest.mock import AsyncMock
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = True
    mock.exists.return_value = False
    return mock


# Pytest configuration
pytest_plugins = ["pytest_asyncio"]

# Configure asyncio event loop for tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test markers
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests") 
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "auth: Authentication related tests")
    config.addinivalue_line("markers", "mfa: Multi-factor authentication tests")
    config.addinivalue_line("markers", "organization: Organization management tests")