"""
Pytest configuration and shared fixtures for Workflow Intelligence Service tests
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials

# Set test environment variables
os.environ["DATABASE_URL"] = "sqlite:///./test_workflow_intelligence.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # Use test database
os.environ["SERVICE_NAME"] = "workflow-intelligence-service-test"

# Import after setting environment variables
from database import engine, SessionLocal
from models import Base
from main import app

@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine"""
    # Use in-memory SQLite for tests
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    return test_engine

@pytest.fixture(scope="session")
def test_tables(test_engine):
    """Create database tables for testing"""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def test_session(test_engine, test_tables):
    """Create a test database session"""
    TestSessionLocal = sessionmaker(bind=test_engine)
    session = TestSessionLocal()
    
    yield session
    
    session.rollback()
    session.close()
    
    # Clean up tables after each test
    with test_engine.connect() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
        connection.commit()

@pytest.fixture(scope="function")
def client(test_session):
    """Create a test client with database session override"""
    def get_test_session():
        try:
            yield test_session
        finally:
            pass
    
    # Override the database dependency
    from database import get_database_session
    app.dependency_overrides[get_database_session] = get_test_session
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up dependency override
    app.dependency_overrides.clear()

@pytest.fixture
def sample_workflow_definition(test_session):
    """Create a sample workflow definition for testing"""
    from models import WorkflowDefinition
    
    definition = WorkflowDefinition(
        name="Test Approval Workflow",
        description="A simple approval workflow for testing",
        category="approval",
        version="1.0.0",
        organization_id="test-org-123",
        initial_state="draft",
        states=[
            {"name": "draft", "is_initial": True, "is_final": False},
            {"name": "pending_review", "is_initial": False, "is_final": False},
            {"name": "approved", "is_initial": False, "is_final": True},
            {"name": "rejected", "is_initial": False, "is_final": True}
        ],
        transitions=[
            {"from": "draft", "to": "pending_review", "action": "submit_for_review"},
            {"from": "pending_review", "to": "approved", "action": "approve"},
            {"from": "pending_review", "to": "rejected", "action": "reject"},
            {"from": "rejected", "to": "draft", "action": "revise"}
        ],
        business_rules={
            "required_fields": ["title", "description"],
            "auto_assignments": {
                "pending_review": "reviewer_role"
            }
        },
        is_active=True,
        created_by="test-user"
    )
    
    test_session.add(definition)
    test_session.commit()
    test_session.refresh(definition)
    
    return definition

@pytest.fixture
def sample_workflow_instance(test_session, sample_workflow_definition):
    """Create a sample workflow instance for testing"""
    from models import WorkflowInstance
    import uuid
    from datetime import datetime
    
    instance = WorkflowInstance(
        id=uuid.uuid4(),
        definition_id=sample_workflow_definition.id,
        entity_id="test-request-123",
        entity_type="purchase_request",
        title="Test Purchase Request",
        description="Test purchase request for office supplies",
        current_state="draft",
        organization_id="test-org-123",
        context_data={
            "amount": 500,
            "department": "IT",
            "priority": "medium"
        },
        status="active",
        created_by="test-user",
        started_at=datetime.utcnow()
    )
    
    test_session.add(instance)
    test_session.commit()
    test_session.refresh(instance)
    
    return instance

@pytest.fixture
def mock_ai_service():
    """Mock AI service responses"""
    class MockAIService:
        @staticmethod
        def summarize_text(text: str, **kwargs):
            return {
                "summary": f"Summary of: {text[:50]}...",
                "confidence": 0.95,
                "original_length": len(text),
                "summary_length": 50
            }
        
        @staticmethod
        def suggest_content(context: dict, **kwargs):
            return {
                "suggestions": [
                    {"field": "priority", "value": "high", "confidence": 0.8},
                    {"field": "category", "value": "office_supplies", "confidence": 0.9}
                ]
            }
        
        @staticmethod
        def analyze_content(text: str, **kwargs):
            return {
                "sentiment": "neutral",
                "topics": ["business", "workflow"],
                "confidence": 0.85,
                "risk_factors": []
            }
    
    return MockAIService()

@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing"""
    class MockRedisClient:
        def __init__(self):
            self.data = {}
        
        async def get(self, key):
            return self.data.get(key)
        
        async def set(self, key, value):
            self.data[key] = value
        
        async def setex(self, key, seconds, value):
            self.data[key] = value  # Ignore expiration for tests
        
        async def delete(self, key):
            self.data.pop(key, None)
        
        async def ping(self):
            return True
        
        async def close(self):
            pass
    
    return MockRedisClient()

# Test data helpers
def create_test_user_context():
    """Create test user context"""
    return {
        "user_id": "test-user-123",
        "email": "test@example.com",
        "organization_id": "test-org-123",
        "roles": ["user", "reviewer"],
        "permissions": ["workflow:read", "workflow:write"]
    }

def create_test_workflow_context():
    """Create test workflow context data"""
    return {
        "request_type": "purchase",
        "amount": 1000,
        "department": "IT", 
        "priority": "medium",
        "requester": "john.doe@company.com",
        "approval_level": "manager"
    }

# Authentication test fixtures
@pytest.fixture
def mock_valid_token():
    """Create a mock valid JWT token"""
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoidXNlci0xMjMiLCJvcmdhbml6YXRpb25faWQiOiJvcmctMTIzIiwicm9sZXMiOlsidXNlciJdLCJleHAiOjk5OTk5OTk5OTl9.VALID_SIGNATURE"
    )

@pytest.fixture
def mock_invalid_token():
    """Create a mock invalid JWT token"""
    return HTTPAuthorizationCredentials(
        scheme="Bearer", 
        credentials="invalid.token.here"
    )

@pytest.fixture
def mock_admin_token():
    """Create a mock admin JWT token"""
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiYWRtaW4tMTIzIiwib3JnYW5pemF0aW9uX2lkIjoib3JnLTEyMyIsInJvbGVzIjpbImFkbWluIiwidXNlciJdLCJleHAiOjk5OTk5OTk5OTl9.ADMIN_SIGNATURE"
    )

@pytest.fixture  
def mock_auth_headers():
    """Create mock authentication headers for requests"""
    return {
        "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoidXNlci0xMjMifQ.SIGNATURE"
    }

@pytest.fixture
def mock_admin_headers():
    """Create mock admin authentication headers"""
    return {
        "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiYWRtaW4tMTIzIiwicm9sZXMiOlsiYWRtaW4iXX0.ADMIN_SIGNATURE"
    }

@pytest.fixture
def mock_identity_service_response():
    """Mock successful Identity Service response"""
    return {
        "user_id": "user-123",
        "email": "test@example.com", 
        "organization_id": "org-123",
        "roles": ["user", "workflow_user"],
        "permissions": ["workflow:read", "workflow:write"],
        "first_name": "Test",
        "last_name": "User"
    }