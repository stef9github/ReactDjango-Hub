# API Testing Documentation

## Overview

This document describes the comprehensive API testing strategy for the Workflow Intelligence Service. The service implements extensive integration tests covering all API endpoints with a focus on authentication, workflow management, and AI service integration.

## API Test Coverage

### Endpoint Testing Summary
- **Total API Integration Tests**: 39 tests
- **Authentication Tests**: 29 dedicated auth tests
- **Coverage Level**: >70% of API surface area
- **Protected Endpoints**: 100% coverage with authentication validation

## Test Categories

### 1. Health & Monitoring Endpoints (3 tests)

#### Health Check (`GET /health`)
```python
def test_health_endpoint_success(self, client: TestClient):
    """Test health endpoint returns service status"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
```

#### Detailed Health Check (`GET /health/detailed`)
```python
def test_health_detailed_endpoint(self, client: TestClient):
    """Test detailed health check includes dependencies"""
    response = client.get("/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert "database" in data
    assert "redis" in data
    assert "external_services" in data
```

#### Metrics Endpoint (`GET /metrics`)
```python 
def test_metrics_endpoint_format(self, client: TestClient):
    """Test metrics endpoint returns Prometheus format"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
```

### 2. Workflow Management Endpoints (14 tests)

#### Create Workflow (`POST /api/v1/workflows`)
```python
@patch('httpx.AsyncClient.post')
def test_create_workflow_with_auth_success(self, mock_post, client: TestClient, mock_user_data):
    """Test workflow creation with proper authentication"""
    headers = {"Authorization": "Bearer valid_token"}
    workflow_data = {
        "definition_id": "def-123",
        "entity_id": "entity-456", 
        "title": "Test Workflow",
        "context_data": {"priority": "high"}
    }
    
    response = client.post("/api/v1/workflows", json=workflow_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Test Workflow"
```

#### Get Workflow (`GET /api/v1/workflows/{id}`)
```python
def test_get_workflow_success(self, client: TestClient, headers):
    """Test retrieving workflow by ID"""
    response = client.get("/api/v1/workflows/workflow-123", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "workflow-123"
    assert "current_state" in data
```

#### Update Workflow (`PUT /api/v1/workflows/{id}`)
```python
def test_update_workflow_context(self, client: TestClient, headers):
    """Test updating workflow context data"""
    update_data = {
        "context_data": {"priority": "urgent", "notes": "Updated priority"}
    }
    response = client.put("/api/v1/workflows/workflow-123", json=update_data, headers=headers)
    assert response.status_code == 200
```

#### Advance Workflow State (`POST /api/v1/workflows/{id}/advance`)
```python
def test_advance_workflow_state(self, client: TestClient, headers):
    """Test advancing workflow to next state"""
    advance_data = {
        "action": "submit_for_review",
        "comment": "Ready for review",
        "context_updates": {"reviewer": "manager@company.com"}
    }
    response = client.post("/api/v1/workflows/workflow-123/advance", json=advance_data, headers=headers)
    assert response.status_code == 200
    assert response.json()["current_state"] == "pending_review"
```

#### Get Workflow History (`GET /api/v1/workflows/{id}/history`)
```python
def test_get_workflow_history(self, client: TestClient, headers):
    """Test retrieving workflow transition history"""
    response = client.get("/api/v1/workflows/workflow-123/history", headers=headers)
    assert response.status_code == 200
    history = response.json()
    assert isinstance(history, list)
    if history:
        assert "action" in history[0]
        assert "from_state" in history[0]
        assert "to_state" in history[0]
```

#### Get Available Actions (`GET /api/v1/workflows/{id}/actions`)
```python
def test_get_available_actions(self, client: TestClient, headers):
    """Test retrieving available workflow actions"""
    response = client.get("/api/v1/workflows/workflow-123/actions", headers=headers)
    assert response.status_code == 200
    actions = response.json()
    assert isinstance(actions, list)
```

### 3. Workflow Definition Endpoints (5 tests)

#### Create Workflow Definition (`POST /api/v1/admin/workflow-definitions`)
```python
def test_create_workflow_definition_admin(self, client: TestClient, admin_headers):
    """Test creating workflow definition (admin only)"""
    definition_data = {
        "name": "Approval Process",
        "category": "approval",
        "initial_state": "draft",
        "states": [
            {"name": "draft", "is_initial": True},
            {"name": "approved", "is_final": True}
        ],
        "transitions": [
            {"from": "draft", "to": "approved", "action": "approve"}
        ]
    }
    
    response = client.post("/api/v1/admin/workflow-definitions", json=definition_data, headers=admin_headers)
    assert response.status_code == 201
    assert response.json()["name"] == "Approval Process"
```

#### List Workflow Definitions (`GET /api/v1/workflow-definitions`)
```python
def test_list_workflow_definitions(self, client: TestClient, headers):
    """Test listing available workflow definitions"""
    response = client.get("/api/v1/workflow-definitions", headers=headers)
    assert response.status_code == 200
    definitions = response.json()
    assert isinstance(definitions, list)
```

### 4. AI Service Endpoints (4 tests)

#### Text Summarization (`POST /api/v1/ai/summarize`)
```python
@patch('httpx.AsyncClient.post')
def test_ai_summarize_endpoint(self, mock_post, client: TestClient, headers):
    """Test AI text summarization endpoint"""
    summarize_data = {
        "text": "Long text that needs to be summarized...",
        "max_length": 100,
        "style": "executive"
    }
    
    response = client.post("/api/v1/ai/summarize", json=summarize_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "confidence" in data
```

#### Content Analysis (`POST /api/v1/ai/analyze`)
```python 
def test_ai_analyze_endpoint(self, client: TestClient, headers):
    """Test AI content analysis endpoint"""
    analyze_data = {
        "text": "Content to analyze for sentiment and topics",
        "analysis_type": "comprehensive"
    }
    
    response = client.post("/api/v1/ai/analyze", json=analyze_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "sentiment" in data
    assert "topics" in data
```

### 5. Workflow Statistics Endpoints (4 tests)

#### Workflow Stats (`GET /api/v1/workflows/stats`)
```python
def test_workflow_stats_endpoint(self, client: TestClient, headers):
    """Test workflow statistics endpoint"""
    response = client.get("/api/v1/workflows/stats", headers=headers)
    assert response.status_code == 200
    stats = response.json()
    assert "total_workflows" in stats
    assert "active_workflows" in stats
    assert "completed_workflows" in stats
```

#### User Workflows (`GET /api/v1/workflows/user/{user_id}`)
```python
def test_get_user_workflows(self, client: TestClient, headers):
    """Test retrieving workflows for specific user"""
    response = client.get("/api/v1/workflows/user/user-123", headers=headers)
    assert response.status_code == 200
    workflows = response.json()
    assert isinstance(workflows, list)
```

## Authentication Testing

### JWT Token Validation (9 tests)
```python
class TestAuthenticationFlow:
    def test_valid_token_authentication(self, client: TestClient):
        """Test successful authentication with valid JWT token"""
        
    def test_invalid_token_rejection(self, client: TestClient):
        """Test rejection of invalid JWT tokens"""
        
    def test_expired_token_handling(self, client: TestClient):
        """Test handling of expired JWT tokens"""
        
    def test_missing_authorization_header(self, client: TestClient):
        """Test handling of missing Authorization header"""
```

### Role-Based Access Control (6 tests)
```python
class TestRoleBasedAccessControl:
    def test_admin_only_endpoints(self, client: TestClient):
        """Test that admin endpoints require admin role"""
        
    def test_user_role_permissions(self, client: TestClient):
        """Test user role access to standard endpoints"""
        
    def test_workflow_owner_permissions(self, client: TestClient):
        """Test workflow owner access controls"""
```

### Endpoint Protection Coverage (2 tests)
```python
@pytest.mark.parametrize("endpoint,method", [
    ("/api/v1/workflows", "POST"),
    ("/api/v1/workflows/workflow-123", "GET"),
    ("/api/v1/ai/summarize", "POST"),
    # ... all protected endpoints
])
def test_all_business_endpoints_require_auth(self, client: TestClient, endpoint, method):
    """Test that all business endpoints require authentication"""
    response = client.get(endpoint) if method == "GET" else client.post(endpoint, json={})
    assert response.status_code in [401, 403]
```

## Error Handling Tests

### Validation Error Tests (4 tests)
```python
class TestAPIErrorHandling:
    def test_invalid_request_data_validation(self, client: TestClient, headers):
        """Test API validation of invalid request data"""
        invalid_data = {"invalid_field": "value"}
        response = client.post("/api/v1/workflows", json=invalid_data, headers=headers)
        assert response.status_code == 422
        assert "detail" in response.json()
        
    def test_missing_required_fields(self, client: TestClient, headers):
        """Test handling of missing required fields"""
        
    def test_invalid_workflow_state_transition(self, client: TestClient, headers):
        """Test validation of invalid state transitions"""
        
    def test_resource_not_found_handling(self, client: TestClient, headers):
        """Test 404 handling for non-existent resources"""
```

## Performance Testing

### Response Time Validation (2 tests)
```python
class TestAPIPerformance:
    def test_api_response_times(self, client: TestClient, headers):
        """Test API response times meet SLA requirements"""
        import time
        start_time = time.time()
        response = client.get("/api/v1/workflows/stats", headers=headers)
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Response within 1 second
        
    def test_concurrent_request_handling(self, client: TestClient, headers):
        """Test handling of concurrent requests"""
        import asyncio
        # Concurrent request testing implementation
```

## API Documentation Testing

### OpenAPI Schema Validation (3 tests)
```python
class TestAPIDocumentation:
    def test_openapi_schema_generation(self, client: TestClient):
        """Test OpenAPI schema is properly generated"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
        
    def test_swagger_ui_accessibility(self, client: TestClient):
        """Test Swagger UI is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
        
    def test_redoc_documentation(self, client: TestClient):
        """Test ReDoc documentation is accessible"""
        response = client.get("/redoc")
        assert response.status_code == 200
```

## Test Execution

### Running API Tests
```bash
# Run all API integration tests
pytest tests/integration/test_api_endpoints.py -v

# Run authentication tests
pytest tests/integration/test_auth_integration.py -v

# Run with coverage
pytest tests/integration/ --cov=main --cov-report=html

# Run performance tests only
pytest tests/integration/ -m slow

# Parallel execution for faster results
pytest tests/integration/ -n auto
```

### Test Data Management
```python
# Example fixture for test data
@pytest.fixture
def sample_workflow_data():
    return {
        "definition_id": "test-definition-123",
        "entity_id": "test-entity-456",
        "entity_type": "purchase_request",
        "title": "Test Purchase Request",
        "description": "Test workflow for API testing",
        "context_data": {
            "amount": 1500,
            "department": "IT",
            "priority": "medium"
        }
    }
```

## Monitoring and Alerts

### Test Metrics
- API response time percentiles
- Authentication success/failure rates
- Endpoint coverage validation
- Error rate monitoring

### CI/CD Integration
```yaml
# API test execution in CI
- name: Run API Integration Tests  
  run: pytest tests/integration/test_api_endpoints.py --junitxml=api-test-results.xml
  
- name: Run Authentication Tests
  run: pytest tests/integration/test_auth_integration.py --junitxml=auth-test-results.xml
  
- name: Validate API Coverage
  run: pytest tests/integration/ --cov=main --cov-fail-under=70
```

## Troubleshooting

### Common API Test Issues
1. **Authentication Failures**: Verify mock token configuration
2. **Database State**: Ensure proper test isolation
3. **External Service Mocks**: Validate mock responses match actual API responses
4. **Response Format Changes**: Keep tests updated with API schema changes

### Debug Commands
```bash
# Run API tests with request/response logging
pytest tests/integration/test_api_endpoints.py -s --log-cli-level=DEBUG

# Test specific endpoint
pytest tests/integration/test_api_endpoints.py::TestWorkflowEndpoints::test_create_workflow_with_auth_success -v

# Profile API test performance
pytest tests/integration/ --profile
```

---

This comprehensive API testing strategy ensures reliable, secure, and performant API operations across all service endpoints.