"""
Pytest configuration and shared fixtures for Auth Service tests
"""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from test_app import app
from app.core.database import get_session
from app.models.enhanced_models import Base, User, Organization
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
    """Create test database session with proper cleanup"""
    async_session_maker = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            # Ensure session is properly closed and rolled back if needed
            if session.in_transaction():
                await session.rollback()
            await session.close()


@pytest_asyncio.fixture
async def test_client(test_session):
    """Create test HTTP client with database session override"""
    
    async def override_get_session():
        yield test_session
    
    app.dependency_overrides[get_session] = override_get_session
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def verify_db_cleanup(test_session):
    """Verify database cleanup between tests"""
    from sqlalchemy import text
    
    # Count records before test
    result = await test_session.execute(text("SELECT COUNT(*) FROM users"))
    users_before = result.scalar()
    
    result = await test_session.execute(text("SELECT COUNT(*) FROM organizations"))  
    orgs_before = result.scalar()
    
    yield
    
    # Verify counts are same or rolled back (should be 0 for fresh tests)
    result = await test_session.execute(text("SELECT COUNT(*) FROM users"))
    users_after = result.scalar()
    
    result = await test_session.execute(text("SELECT COUNT(*) FROM organizations"))
    orgs_after = result.scalar()
    
    # Log cleanup status for debugging
    if users_after > users_before or orgs_after > orgs_before:
        print(f"⚠️  Database cleanup warning: Users {users_before}→{users_after}, Orgs {orgs_before}→{orgs_after}")
    else:
        print(f"✅ Database cleanup verified: Clean state maintained")


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
    from app.core.security import SecurityUtils
    
    user = User(
        email="testuser@example.com",
        password_hash=SecurityUtils.hash_password("testpassword123"),
        is_active=True,
        is_verified=True,
        first_name="Test",
        last_name="User"
    )
    
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    
    return user


@pytest_asyncio.fixture
async def test_admin_user(test_session):
    """Create test admin user"""
    from app.models.enhanced_models import User
    from app.core.security import SecurityUtils
    
    # Create admin user
    admin_user = User(
        email="admin@example.com",
        password_hash=SecurityUtils.hash_password("adminpassword123"),
        is_active=True,
        is_verified=True,
        first_name="Admin",
        last_name="User"
    )
    
    test_session.add(admin_user)
    await test_session.commit()
    await test_session.refresh(admin_user)
    
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