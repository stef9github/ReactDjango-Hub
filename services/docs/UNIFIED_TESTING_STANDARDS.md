# Unified Testing Standards for Microservices

**Version:** 1.0  
**Last Updated:** September 10, 2025  
**Purpose:** Establish consistent testing practices across all microservices

## 📋 Overview

All microservices MUST follow these testing standards to ensure quality, maintainability, and production readiness. These standards apply to Identity, Communication, Content, and Workflow Intelligence services.

## 🎯 Testing Requirements

### Coverage Targets
- **Overall Coverage:** Minimum 80%
- **Critical Paths:** 100% coverage required
- **Models:** 95% coverage minimum  
- **API Endpoints:** 100% integration test coverage
- **Business Logic:** 90% unit test coverage

### Test Categories
```
tests/
├── unit/           # Business logic, isolated components
├── integration/    # API endpoints, service interactions
├── e2e/           # Complete user workflows
├── performance/   # Load testing, benchmarks
└── security/      # Security-specific tests
```

## 📦 Standardized Dependencies

### Base Test Requirements
All services MUST use these versions for consistency:

```txt
# test_requirements.txt - Base for all services
# Core testing framework
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-cov==5.0.0
pytest-mock==3.14.0
pytest-timeout==2.3.1
pytest-xdist==3.6.1  # Parallel execution

# FastAPI testing
httpx==0.27.2
asgi-lifespan==2.1.0

# Database testing
pytest-postgresql==6.0.0
sqlalchemy-utils==0.41.2
aiosqlite==0.20.0

# Mocking and factories
factory-boy==3.3.1
faker==26.0.0
responses==0.25.3
freezegun==1.5.1

# Performance testing
pytest-benchmark==4.0.0
locust==2.20.0
memory-profiler==0.61.0

# Utilities
python-multipart==0.0.9
aiofiles==24.1.0
python-magic==0.4.27
```

### Service-Specific Additions
Services may ADD to base requirements but MUST NOT change versions:

```txt
# Identity Service additions
pyotp==2.9.0  # TOTP testing
qrcode==7.4.2  # QR code testing
hypothesis==6.112.0  # Property-based testing

# Communication Service additions
aiosmtpd==1.4.4.1  # SMTP testing
fakeredis==2.20.1  # Redis mocking
celery[pytest]==5.3.4  # Celery testing

# Content Service additions
Pillow==10.1.0  # Image processing
PyPDF2==3.0.1  # PDF testing
minio==7.2.0  # Object storage

# Workflow Service additions
transitions==0.9.0  # State machine
openai==1.3.5  # AI mocking
```

## 🧪 Test Structure Standards

### 1. Test File Naming
```python
# Unit tests
test_<module>_<functionality>.py
# Example: test_document_service_crud.py

# Integration tests  
test_<endpoint>_integration.py
# Example: test_notifications_api_integration.py

# E2E tests
test_<workflow>_e2e.py
# Example: test_document_upload_workflow_e2e.py
```

### 2. Test Class Organization
```python
"""
Test module docstring explaining what is being tested
"""
import pytest
from typing import Any
from unittest.mock import AsyncMock, patch

@pytest.mark.unit  # Always mark test type
class TestDocumentService:
    """Test document service operations"""
    
    @pytest.fixture(autouse=True)
    async def setup(self, db_session, mock_storage):
        """Setup run before each test"""
        self.service = DocumentService(db_session, mock_storage)
        yield
        # Cleanup if needed
    
    async def test_create_document_success(self):
        """Test successful document creation with all validations"""
        # Arrange
        test_data = self._create_test_document_data()
        
        # Act
        result = await self.service.create_document(test_data)
        
        # Assert
        assert result.id is not None
        assert result.status == "active"
        self._verify_audit_log_created(result.id)
    
    async def test_create_document_validation_error(self):
        """Test document creation with invalid data"""
        # Arrange
        invalid_data = {"filename": ""}  # Missing required fields
        
        # Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            await self.service.create_document(invalid_data)
        
        assert "filename" in str(exc_info.value)
```

### 3. Fixture Standards
```python
# conftest.py - Shared fixtures
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine - session scoped"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(test_engine):
    """Create database session - function scoped"""
    async with AsyncSession(test_engine) as session:
        yield session
        await session.rollback()

@pytest.fixture
def mock_user_context():
    """Standard user context for testing"""
    return {
        "user_id": "test-user-123",
        "organization_id": "test-org-456",
        "roles": ["user"],
        "permissions": ["read", "write"]
    }
```

## 🔍 Test Patterns

### 1. API Endpoint Testing
```python
@pytest.mark.integration
class TestNotificationAPI:
    """Test notification API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    async def test_send_notification_authenticated(
        self, 
        client,
        mock_auth,
        mock_user_context
    ):
        """Test sending notification with valid authentication"""
        # Mock authentication
        mock_auth.return_value = mock_user_context
        
        # Make request
        response = client.post(
            "/api/v1/notifications",
            json={"template_id": "welcome", "user_id": "123"},
            headers={"Authorization": "Bearer valid-token"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["notification_id"] is not None
    
    async def test_send_notification_unauthorized(self, client):
        """Test sending notification without authentication"""
        response = client.post(
            "/api/v1/notifications",
            json={"template_id": "welcome", "user_id": "123"}
        )
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
```

### 2. Service Layer Testing
```python
@pytest.mark.unit
class TestDocumentService:
    """Test document service business logic"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock document repository"""
        repo = AsyncMock()
        repo.create.return_value = Document(id="doc-123")
        repo.get.return_value = Document(id="doc-123")
        return repo
    
    async def test_create_document_with_metadata(
        self,
        mock_repository,
        mock_storage
    ):
        """Test document creation with metadata extraction"""
        # Arrange
        service = DocumentService(mock_repository, mock_storage)
        file_data = create_test_file()
        
        # Act
        document = await service.create_document(file_data)
        
        # Assert
        mock_repository.create.assert_called_once()
        mock_storage.store.assert_called_once()
        assert document.metadata is not None
        assert document.metadata["content_type"] == "application/pdf"
```

### 3. Error Injection Testing
```python
@pytest.mark.unit
class TestErrorHandling:
    """Test error handling and resilience"""
    
    async def test_database_connection_failure(self, service):
        """Test handling of database connection errors"""
        with patch.object(service.db, 'execute') as mock_execute:
            mock_execute.side_effect = DatabaseError("Connection lost")
            
            with pytest.raises(ServiceUnavailableError):
                await service.get_document("doc-123")
    
    async def test_retry_on_transient_failure(self, service):
        """Test retry logic for transient failures"""
        with patch.object(service, '_execute_with_retry') as mock_retry:
            mock_retry.side_effect = [
                TimeoutError("Timeout"),
                TimeoutError("Timeout"),
                {"id": "doc-123"}  # Success on third try
            ]
            
            result = await service.get_document_with_retry("doc-123")
            assert result["id"] == "doc-123"
            assert mock_retry.call_count == 3
```

### 4. Performance Testing
```python
@pytest.mark.performance
class TestPerformance:
    """Performance and load testing"""
    
    @pytest.mark.benchmark(group="api")
    def test_api_response_time(self, benchmark, client):
        """Benchmark API response time"""
        def make_request():
            return client.get("/api/v1/health")
        
        result = benchmark(make_request)
        assert result.status_code == 200
        
        # Verify performance requirements
        stats = benchmark.stats
        assert stats["mean"] < 0.1  # Mean response < 100ms
        assert stats["max"] < 0.5   # Max response < 500ms
    
    @pytest.mark.slow
    async def test_concurrent_load(self, service):
        """Test service under concurrent load"""
        import asyncio
        
        async def make_request(i):
            return await service.get_document(f"doc-{i}")
        
        # Create 100 concurrent requests
        tasks = [make_request(i) for i in range(100)]
        start_time = time.time()
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.time() - start_time
        
        # Verify results
        successful = sum(1 for r in results if not isinstance(r, Exception))
        assert successful > 95  # >95% success rate
        assert elapsed < 10     # Complete within 10 seconds
```

## 📝 Test Documentation

### Test Docstrings
Every test MUST have a docstring explaining:
- What is being tested
- Expected behavior
- Any special conditions

```python
async def test_document_upload_with_virus_scanning(self):
    """
    Test document upload with virus scanning enabled.
    
    Verifies that:
    - File is scanned before storage
    - Infected files are rejected
    - Clean files proceed to storage
    - Appropriate audit logs are created
    """
```

### Test Markers
Use pytest markers to categorize tests:

```python
# pytest.ini
[tool:pytest]
markers =
    unit: Unit tests for isolated components
    integration: Integration tests with dependencies
    e2e: End-to-end workflow tests
    performance: Performance and load tests
    security: Security-specific tests
    slow: Tests that take >5 seconds
    requires_db: Tests requiring database
    requires_redis: Tests requiring Redis
    requires_minio: Tests requiring object storage
```

## 🚀 CI/CD Integration

### GitHub Actions Workflow
```yaml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r test_requirements.txt
      
      - name: Run tests with coverage
        run: |
          pytest tests/ \
            --cov=app \
            --cov-report=xml \
            --cov-report=html \
            --cov-fail-under=80 \
            -v
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## 🎯 Testing Checklist

Before marking a feature as complete, ensure:

- [ ] Unit tests written for all business logic
- [ ] Integration tests for all API endpoints
- [ ] Error cases tested (invalid input, failures)
- [ ] Performance benchmarks meet requirements
- [ ] Security tests pass (auth, permissions)
- [ ] Test coverage >80%
- [ ] All tests pass in CI/CD
- [ ] Documentation updated

## 📊 Test Reporting

### Coverage Reports
Generate comprehensive coverage reports:

```bash
# HTML report
pytest --cov=app --cov-report=html

# Terminal report with missing lines
pytest --cov=app --cov-report=term-missing

# XML for CI/CD
pytest --cov=app --cov-report=xml
```

### Performance Reports
Track performance over time:

```bash
# Run benchmarks and save results
pytest tests/performance/ --benchmark-only --benchmark-save=baseline

# Compare with baseline
pytest tests/performance/ --benchmark-only --benchmark-compare=baseline
```

## 🔄 Continuous Improvement

### Monthly Review
- Review test coverage trends
- Identify flaky tests
- Update test data factories
- Review and update markers
- Performance regression analysis

### Quarterly Updates
- Update testing dependencies
- Review and update standards
- Share best practices across teams
- Conduct testing workshops

---

**All services MUST comply with these standards. Non-compliance will block PR merges.**

**For questions or clarifications, consult the Testing Standards Committee or create an issue in the standards repository.**