# Auth Service Test Suite

## 🧪 **Comprehensive Test Coverage**

This test suite provides complete coverage for the Auth Service with organized test types and comprehensive fixtures.

## 📁 **Test Organization**

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (isolated components)
│   ├── test_auth_service.py # AuthService business logic
│   ├── test_user_service.py # User management logic
│   ├── test_mfa_service.py  # MFA business logic
│   └── test_security.py     # Security utilities
├── integration/             # Integration tests (API + database)
│   ├── test_auth_api.py     # Authentication API endpoints
│   ├── test_user_api.py     # User management API endpoints
│   ├── test_org_api.py      # Organization API endpoints
│   └── test_mfa_api.py      # MFA API endpoints
├── e2e/                     # End-to-end tests (complete workflows)
│   ├── test_user_journey.py # Complete user lifecycle
│   ├── test_org_workflow.py # Organization management workflow
│   └── test_mfa_setup.py    # MFA setup and usage workflow
└── fixtures/                # Test data and fixtures
    ├── sample_users.json    # Sample user data
    └── sample_orgs.json     # Sample organization data
```

## 🚀 **Running Tests**

### **All Tests**
```bash
# Run complete test suite
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run with coverage and detailed output
pytest tests/ --cov=app --cov-report=term-missing -v
```

### **By Test Type**
```bash
# Unit tests only (fast)
pytest tests/unit/ -v -m unit

# Integration tests (with database)
pytest tests/integration/ -v -m integration

# End-to-end tests (complete workflows)
pytest tests/e2e/ -v -m e2e

# Authentication-related tests only
pytest tests/ -v -m auth
```

### **By Performance**
```bash
# Fast tests only
pytest tests/ -v -m "not slow"

# Include slow tests
pytest tests/ -v

# Parallel execution (if pytest-xdist installed)
pytest tests/ -n auto
```

## 🔧 **Test Configuration**

### **pytest.ini Configuration**
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
    auth: Authentication tests
    mfa: Multi-factor authentication tests
    organization: Organization management tests
asyncio_mode = auto
```

### **Test Markers**
- `@pytest.mark.unit` - Isolated unit tests
- `@pytest.mark.integration` - API integration tests  
- `@pytest.mark.e2e` - End-to-end workflow tests
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.auth` - Authentication-specific tests
- `@pytest.mark.mfa` - Multi-factor authentication tests
- `@pytest.mark.organization` - Organization management tests

## 🧩 **Available Fixtures**

### **Database Fixtures**
```python
# Test database engine (SQLite in-memory)
@pytest_asyncio.fixture
async def test_engine():
    # Creates isolated test database

# Test database session
@pytest_asyncio.fixture  
async def test_session(test_engine):
    # Database session for tests

# Test HTTP client with database override
@pytest_asyncio.fixture
async def test_client(test_session):
    # FastAPI test client with test database
```

### **User Fixtures**
```python
# Regular test user
@pytest_asyncio.fixture
async def test_user(test_session):
    # Creates test user: testuser@example.com

# Admin test user with permissions
@pytest_asyncio.fixture
async def test_admin_user(test_session):
    # Creates admin user: admin@example.com
```

### **Organization Fixtures**
```python
# Test organization
@pytest_asyncio.fixture
async def test_organization(test_session, test_user):
    # Creates "Test Organization"
```

### **Utility Fixtures**
```python
# Authentication headers generator
@pytest.fixture
def auth_headers():
    # Returns function to generate Bearer token headers

# Mock email service
@pytest.fixture
def mock_email_service():
    # AsyncMock for email service

# Mock Redis
@pytest.fixture
def mock_redis():
    # Mock Redis client
```

## 📊 **Test Coverage Goals**

### **Coverage Targets**
- **Overall Coverage**: >90%
- **Business Logic (services/)**: >95%
- **API Endpoints (api/)**: >90%
- **Critical Paths**: 100% (auth, security)

### **Coverage by Component**
```bash
# Generate coverage report
pytest --cov=app --cov-report=html

# View HTML report
open htmlcov/index.html

# Terminal coverage report
pytest --cov=app --cov-report=term-missing
```

## 🔍 **Test Categories**

### **1. Unit Tests (`tests/unit/`)**
**Purpose**: Test individual components in isolation

**Characteristics**:
- ✅ Fast execution (<1s per test)
- ✅ No database dependencies
- ✅ Mock external services
- ✅ Test business logic only

**Examples**:
```python
# Test service methods with mocked dependencies
def test_hash_password():
    password = "test123"
    hashed = hash_password(password)
    assert hashed != password

# Test token creation and validation
def test_create_access_token():
    token_service = TokenService()
    token = token_service.create_access_token({"user_id": "123"})
    assert token is not None
```

### **2. Integration Tests (`tests/integration/`)**
**Purpose**: Test API endpoints with real database interactions

**Characteristics**:
- ✅ Test complete API flows
- ✅ Use test database (SQLite)
- ✅ Validate request/response cycles
- ✅ Test error handling

**Examples**:
```python
# Test complete login flow
async def test_login_flow(test_client):
    response = await test_client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### **3. End-to-End Tests (`tests/e2e/`)**
**Purpose**: Test complete user workflows across multiple endpoints

**Characteristics**:
- ✅ Test real user scenarios
- ✅ Multiple API calls in sequence
- ✅ Validate business workflows
- ✅ Test edge cases and error scenarios

**Examples**:
```python
# Test complete user registration -> profile setup -> organization creation
async def test_new_user_journey(test_client):
    # 1. Register user
    # 2. Verify email
    # 3. Setup profile
    # 4. Create organization
    # 5. Invite team members
    # Validate each step works correctly
```

## 🛠️ **Test Development Patterns**

### **Writing Unit Tests**
```python
@pytest.mark.unit
class TestAuthService:
    @pytest_asyncio.fixture
    async def auth_service(self, test_session):
        return AuthService(test_session)
    
    @pytest.mark.asyncio
    async def test_authenticate_user(self, auth_service, test_user):
        result = await auth_service.authenticate_user(
            email="testuser@example.com",
            password="testpassword123"
        )
        assert result["user_id"] == str(test_user.id)
```

### **Writing Integration Tests**
```python
@pytest.mark.integration
@pytest.mark.auth
class TestAuthAPI:
    @pytest.mark.asyncio
    async def test_login_endpoint(self, test_client, test_user):
        response = await test_client.post("/api/v1/auth/login", json={
            "email": "testuser@example.com",
            "password": "testpassword123"
        })
        assert response.status_code == 200
```

### **Writing E2E Tests**
```python
@pytest.mark.e2e
@pytest.mark.slow
class TestUserJourney:
    @pytest.mark.asyncio
    async def test_complete_user_lifecycle(self, test_client):
        # Test complete workflow from registration to organization management
        # Multiple API calls testing real user scenarios
```

## 📈 **Testing Best Practices**

### **Test Organization**
1. **One test per behavior** - Each test validates one specific behavior
2. **Descriptive names** - Test names explain what is being tested
3. **Arrange-Act-Assert** - Clear test structure
4. **Independent tests** - Tests don't depend on each other

### **Test Data Management**
1. **Use fixtures** - Centralized test data creation
2. **Clean slate** - Each test starts with fresh data
3. **Minimal data** - Only create data needed for the test
4. **Realistic data** - Test data reflects real-world scenarios

### **Mocking Strategy**
1. **Mock external services** - Email, SMS, external APIs
2. **Don't mock what you own** - Test your own services
3. **Mock at boundaries** - Mock at service boundaries
4. **Verify interactions** - Assert that mocked services are called correctly

## 🔧 **Continuous Integration**

### **Pre-commit Hooks**
Tests run automatically before commits:
```bash
# Setup pre-commit hooks (includes test run)
python3 scripts/setup_pre_commit.py
```

### **GitHub Actions**
Tests run on pull requests:
- All test types (unit, integration, e2e)
- Coverage reporting
- Performance regression detection

### **Local Development**
```bash
# Quick test run during development
pytest tests/unit/ -x  # Stop on first failure

# Test specific functionality
pytest tests/ -k "test_auth" -v

# Watch mode (if pytest-watch installed)
ptw tests/ -- --cov=app
```

## 🎯 **Next Steps**

1. **Run existing tests**: `pytest tests/ -v`
2. **Check coverage**: `pytest tests/ --cov=app --cov-report=html`
3. **Add missing tests**: Focus on uncovered code paths
4. **Setup CI integration**: Ensure tests run on pull requests
5. **Add performance tests**: Monitor API response times

---

**🧪 Comprehensive test coverage ensures Auth Service reliability and quality!**