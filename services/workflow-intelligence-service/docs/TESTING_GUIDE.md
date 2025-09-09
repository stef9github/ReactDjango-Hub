# Testing Guide - Workflow Intelligence Service

## Overview

This document provides comprehensive guidance for testing the Workflow Intelligence Service. The service implements a production-grade testing suite with **148 test methods** across multiple testing categories, ensuring robust quality assurance and reliability.

## Testing Philosophy

### Quality Standards
- **Overall Coverage**: Minimum 80% code coverage requirement
- **Unit Tests**: >90% coverage of business logic and models
- **Integration Tests**: >70% coverage of API endpoints and service integration
- **Authentication**: 100% coverage of all protected endpoints
- **End-to-End**: Complete workflow journey validation

### Testing Pyramid
```
        /\    E2E Tests (4)
       /  \   Complete workflow journeys
      /____\  
     /      \  Integration Tests (92)
    /        \ API endpoints, auth, services
   /__________\
  /            \ Unit Tests (52)  
 /              \ Models, business logic
/________________\
```

## Test Structure

### Directory Organization
```
tests/
├── unit/                           # Unit tests (52 tests)
│   ├── test_models.py             # Database models (21 tests)
│   └── test_workflow_engine.py    # Workflow engine (31 tests)
├── integration/                    # Integration tests (92 tests)
│   ├── test_api_endpoints.py      # API endpoints (39 tests)
│   ├── test_auth_integration.py   # Authentication (29 tests)
│   ├── test_workflow_state_machine.py # State machine (11 tests)
│   └── test_ai_integration.py     # AI services (13 tests)
├── e2e/                           # End-to-end tests (4 tests)
│   └── test_complete_workflows.py # Complete workflows
├── fixtures/                       # Test data and fixtures
└── conftest.py                    # Pytest configuration
```

### Test Categories and Markers

#### Available Test Markers
```bash
unit          # Unit tests (52 tests)
integration   # Integration tests (92 tests)
e2e           # End-to-end tests (4 tests)
auth          # Authentication tests (29 tests)
workflow      # Workflow-specific tests (24 tests)
ai            # AI service tests (13 tests)
slow          # Performance/load tests
requires_db   # Database-dependent tests
requires_redis # Cache-dependent tests
requires_external # External service tests
```

## Running Tests

### Basic Commands
```bash
# Run all tests
pytest

# Run all tests with coverage
pytest --cov=. --cov-report=html

# Run tests with coverage threshold enforcement
pytest --cov=. --cov-fail-under=80

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests
pytest -m auth          # Authentication tests
pytest -m workflow      # Workflow tests
pytest -m ai            # AI integration tests
```

### Advanced Execution
```bash
# Parallel test execution (faster)
pytest -n auto

# Run specific test file
pytest tests/unit/test_models.py

# Run specific test class
pytest tests/unit/test_models.py::TestWorkflowDefinition

# Run specific test method
pytest tests/unit/test_models.py::TestWorkflowDefinition::test_workflow_definition_creation

# Verbose output with detailed results
pytest -v --tb=short

# Run tests with performance profiling
pytest --benchmark-only
```

### Coverage Reporting
```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html:htmlcov

# Terminal coverage report with missing lines
pytest --cov=. --cov-report=term-missing

# XML coverage report (CI/CD friendly)
pytest --cov=. --cov-report=xml

# Combined coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing --cov-report=xml
```

## Test Implementation Details

### Unit Tests (52 tests)

#### Database Models Tests (21 tests)
- **WorkflowDefinition** (6 tests): Creation, validation, state management
- **WorkflowInstance** (7 tests): Lifecycle, properties, context management
- **WorkflowHistory** (3 tests): Audit trail, transition tracking
- **AIInsight** (2 tests): AI-generated insights storage
- **Model Relationships** (3 tests): Foreign keys, associations

#### Workflow Engine Tests (31 tests)
- **Core Engine** (14 tests): CRUD operations, state transitions
- **State Machine** (3 tests): Transition validation, state management
- **Error Handling** (4 tests): Exception scenarios, recovery
- **Helper Methods** (6 tests): Utility functions, calculations
- **Integration Points** (4 tests): External service interactions

### Integration Tests (92 tests)

#### API Endpoints (39 tests)
- **Workflow Management** (14 tests): CRUD operations, lifecycle
- **Workflow Definitions** (5 tests): Admin operations, templates
- **Health & Monitoring** (7 tests): Status checks, metrics
- **AI Services** (4 tests): Content analysis, suggestions
- **Error Handling** (4 tests): Validation, exception handling
- **Performance** (2 tests): Response times, load testing
- **API Documentation** (3 tests): OpenAPI schema validation

#### Authentication Integration (29 tests)
- **Authentication Flow** (9 tests): JWT validation, token handling
- **Role-Based Access Control** (6 tests): Permissions, authorization
- **Security Headers** (3 tests): CORS, security policies
- **Error Scenarios** (6 tests): Invalid tokens, timeouts
- **Endpoint Coverage** (2 tests): Protected endpoint validation
- **Performance** (3 tests): Authentication latency, concurrent requests

#### Workflow State Machine (11 tests)
- **Basic Transitions** (7 tests): State changes, validation rules
- **Complex Scenarios** (4 tests): Multi-step workflows, conditions

#### AI Integration (13 tests)
- **AI Services** (9 tests): OpenAI, Anthropic, content analysis
- **Intelligent Features** (4 tests): Smart routing, predictions

### End-to-End Tests (4 tests)

#### Complete Workflow Journeys
- **Full Approval Workflow**: Complete process from creation to approval
- **Rejection & Revision**: Workflow rejection and revision cycles
- **AI-Enhanced Processing**: Intelligent workflow with AI integration
- **Multi-User Collaboration**: Complex multi-stakeholder workflows

## Test Configuration

### Environment Setup
```bash
# Install test dependencies
pip install -r test_requirements.txt

# Set testing environment
export TESTING=true
export LOG_LEVEL=ERROR
export DATABASE_URL="sqlite:///./test_workflow_intelligence.db"
export REDIS_URL="redis://localhost:6379/15"
```

### pytest.ini Configuration
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --cov=.
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=80
asyncio_mode = auto
```

## Test Fixtures and Mocking

### Database Testing
- **In-Memory SQLite**: Fast, isolated database for tests
- **Automatic Setup/Teardown**: Clean database state per test
- **Transaction Rollback**: Ensure test isolation
- **Sample Data**: Comprehensive test fixtures

### Authentication Mocking
```python
# JWT token validation mocking
@pytest.fixture
def mock_identity_service_success(mock_user_data):
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_post.return_value = mock_response
        yield mock_post
```

### AI Service Mocking
```python
# OpenAI API response mocking
@patch('openai.ChatCompletion.create')
def test_openai_integration(mock_openai):
    mock_openai.return_value = {
        "choices": [{"message": {"content": "Test AI response"}}]
    }
    # Test implementation
```

## Continuous Integration

### CI/CD Pipeline Integration
```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r test_requirements.txt
      - name: Run tests
        run: pytest --cov=. --cov-report=xml --cov-fail-under=80
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

### Quality Gates
- **Coverage Threshold**: Tests fail if coverage < 80%
- **Authentication Coverage**: 100% coverage required for auth endpoints
- **Performance Benchmarks**: Response time validation
- **Security Testing**: Authentication and authorization validation

## Best Practices

### Writing Tests
1. **Test Naming**: Use descriptive test method names
2. **Test Structure**: Follow Arrange-Act-Assert pattern
3. **Test Isolation**: Each test should be independent
4. **Mock External Services**: Use mocks for external dependencies
5. **Edge Cases**: Test error conditions and boundary cases

### Test Data Management
1. **Fixtures**: Use pytest fixtures for reusable test data
2. **Factories**: Use factory-boy for dynamic test data generation
3. **Cleanup**: Ensure proper cleanup after tests
4. **Deterministic**: Tests should produce consistent results

### Performance Considerations
1. **Parallel Execution**: Use `pytest-xdist` for faster test runs
2. **Database Optimization**: Use in-memory databases for speed
3. **Mock Heavy Operations**: Mock time-consuming external calls
4. **Resource Management**: Properly manage test resources

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure PYTHONPATH includes service directory
2. **Database Conflicts**: Use separate test database configuration
3. **External Service Failures**: Verify mock configurations
4. **Coverage Gaps**: Check untested code paths

### Debug Commands
```bash
# Run tests with debugging
pytest --pdb --pdbcls=IPython.terminal.debugger:Pdb

# Run tests with detailed logging
pytest -s --log-cli-level=DEBUG

# Profile test performance
pytest --profile

# Test validation
python validate_tests.py
```

## Maintenance

### Regular Tasks
1. **Review Coverage Reports**: Identify untested code areas
2. **Update Test Data**: Keep fixtures current with schema changes
3. **Performance Monitoring**: Track test execution times
4. **Dependency Updates**: Keep test dependencies current

### Quality Metrics Monitoring
- Monitor test execution time trends
- Track code coverage changes over time
- Validate authentication coverage remains at 100%
- Review failed test patterns and root causes

---

For detailed implementation reports and metrics, see:
- [TESTING_IMPLEMENTATION_REPORT.md](../TESTING_IMPLEMENTATION_REPORT.md)
- [Test Coverage Reports](../htmlcov/index.html) (generated after running tests)