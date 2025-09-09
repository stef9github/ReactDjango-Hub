# JWT Authentication Integration Guide

**For**: All Microservices (Communication, Content, Workflow Intelligence)  
**Purpose**: Implement JWT token validation with Identity Service  
**Priority**: 🔴 **CRITICAL** - Security requirement for production deployment  
**Services Coordinator**: Implementation standard for all services  

---

## 🎯 **Overview**

This guide provides **copy-paste ready code** for implementing JWT authentication in all microservices. Each service must validate JWT tokens with the Identity Service before processing protected endpoints.

**Current Status**:
- ✅ **Identity Service**: JWT generation and validation implemented
- ❌ **Communication Service**: Missing JWT validation (25+ endpoints)
- ❌ **Content Service**: Has placeholder auth, needs JWT implementation
- ❌ **Workflow Service**: Missing JWT validation (12+ endpoints)

---

## 🔧 **Step-by-Step Implementation**

### **Step 1: Add Required Imports**

Add to the top of your `main.py`:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
import httpx
import logging

# Add logging for debugging
logger = logging.getLogger(__name__)
```

### **Step 2: Initialize Security Schema**

Add after your service configuration variables:

```python
# Service configuration (existing)
SERVICE_NAME = os.getenv("SERVICE_NAME", "your-service-name")
IDENTITY_SERVICE_URL = os.getenv("IDENTITY_SERVICE_URL", "http://localhost:8001")

# JWT Authentication setup
security = HTTPBearer()
```

### **Step 3: Implement Token Validation Function**

Add this authentication dependency function:

```python
async def validate_jwt_token(token: str = Depends(security)):
    """
    Validate JWT token with Identity Service.
    
    Args:
        token: Bearer token from Authorization header
        
    Returns:
        dict: User data from Identity Service
        
    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    try:
        # Call Identity Service to validate token
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{IDENTITY_SERVICE_URL}/auth/validate",
                headers={"Authorization": f"Bearer {token.credentials}"},
                timeout=5.0
            )
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"Token validated for user: {user_data.get('user_id', 'unknown')}")
                return user_data
            
            elif response.status_code == 401:
                logger.warning("Invalid or expired token provided")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            else:
                logger.error(f"Identity service returned unexpected status: {response.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token validation failed",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
    except httpx.TimeoutException:
        logger.error("Timeout calling Identity Service for token validation")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable"
        )
    except httpx.RequestError as e:
        logger.error(f"Network error calling Identity Service: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
            headers={"WWW-Authenticate": "Bearer"},
        )
```

### **Step 4: Protect Your Endpoints**

Update **ALL** protected endpoints (except `/health`) to include authentication:

```python
# BEFORE: Unprotected endpoint
@app.post("/api/v1/your-endpoint")
async def your_endpoint(request: RequestModel):
    # Your endpoint logic
    pass

# AFTER: Protected endpoint
@app.post("/api/v1/your-endpoint")
async def your_endpoint(
    request: RequestModel,
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS LINE
):
    # Now you have access to current_user data:
    user_id = current_user["user_id"]
    organization_id = current_user.get("organization_id")
    user_email = current_user.get("email")
    user_roles = current_user.get("roles", [])
    
    # Your existing endpoint logic with user context
    pass
```

### **Step 5: Leave Health Endpoint Unprotected**

**IMPORTANT**: Do NOT protect the `/health` endpoint:

```python
@app.get("/health")  # NO authentication dependency here
async def health_check():
    """Health check must remain accessible without authentication"""
    # Your existing health check logic
    pass
```

---

## 📋 **Service-Specific Implementation Instructions**

### **🔔 Communication Service**

Replace the placeholder authentication in `/communication-service/main.py`:

```python
# REMOVE any existing placeholder auth functions

# ADD the validate_jwt_token function from Step 3 above

# UPDATE all these endpoints:
@app.post("/api/v1/notifications")
async def send_notification(
    request: NotificationRequest,
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Use current_user["user_id"], current_user["organization_id"]
    # Your existing logic...

@app.get("/api/v1/notifications/unread")
async def get_unread_notifications(
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Your existing logic...

@app.post("/api/v1/messages")
async def send_message(
    request: MessageRequest,
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Your existing logic...

@app.get("/api/v1/conversations")
async def list_conversations(
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Your existing logic...

@app.get("/api/v1/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Your existing logic...

@app.post("/api/v1/templates")
async def create_template(
    request: TemplateRequest,
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Your existing logic...

@app.get("/api/v1/templates")
async def list_templates(
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Your existing logic...

@app.get("/api/v1/queue/status")
async def get_queue_status(
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Your existing logic...
```

### **📄 Content Service**

The Content Service already has a placeholder `get_current_user()` function. **Replace it**:

```python
# REPLACE this existing function:
# async def get_current_user():
#     """Placeholder for user authentication - returns mock user."""
#     return {...}

# WITH the real JWT validation:
async def get_current_user(current_user: dict = Depends(validate_jwt_token)):
    """Get current authenticated user from JWT token."""
    return {
        "id": current_user["user_id"],  # Convert to UUID if needed
        "organization_id": current_user["organization_id"],
        "email": current_user.get("email"),
        "roles": current_user.get("roles", [])
    }

# Your existing endpoints will automatically work because they already use:
# current_user: dict = Depends(get_current_user)
```

### **🔄 Workflow Intelligence Service**

Update all endpoints in `/workflow-intelligence-service/main.py`:

```python
# ADD the validate_jwt_token function from Step 3

# UPDATE all these endpoints:
@app.post("/api/v1/workflows")
async def create_workflow(
    request: WorkflowCreateRequest,
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Use current_user data in workflow creation
    # Your existing logic...

@app.get("/api/v1/workflows/{workflow_id}/status")
async def get_workflow_status(
    workflow_id: str,
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Your existing logic...

@app.patch("/api/v1/workflows/{workflow_id}/next")
async def advance_workflow(
    workflow_id: str,
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Your existing logic...

@app.get("/api/v1/workflows/user/{user_id}")
async def get_user_workflows(
    user_id: str,
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Verify user_id matches current_user or has admin permissions
    # Your existing logic...

@app.post("/api/v1/ai/summarize")
async def ai_summarize(
    request: SummarizeRequest,
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Your existing logic...

@app.post("/api/v1/ai/suggest")
async def ai_suggest(
    request: SuggestRequest,
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Your existing logic...

@app.post("/api/v1/ai/analyze")
async def ai_analyze(
    request: AnalyzeRequest,
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Your existing logic...

@app.get("/api/v1/definitions")
async def list_definitions(
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Your existing logic...

@app.post("/api/v1/definitions")
async def create_definition(
    request: DefinitionRequest,
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Your existing logic...

@app.get("/api/v1/workflows/stats")
async def get_workflow_stats(
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Your existing logic...

@app.get("/api/v1/workflows/sla-check")
async def check_sla_violations(
    current_user: dict = Depends(validate_jwt_token)  # ADD THIS
):
    # Your existing logic...
```

---

## 🧪 **Testing Your Implementation**

### **Step 1: Test Unauthenticated Request (Should Fail)**

```bash
curl -X POST http://localhost:8003/api/v1/notifications \
  -H "Content-Type: application/json" \
  -d '{"type":"email","to":"test@test.com","message":"test"}'

# Expected Response: 401 Unauthorized
{
  "detail": "Not authenticated"
}
```

### **Step 2: Test Invalid Token (Should Fail)**

```bash
curl -X POST http://localhost:8003/api/v1/notifications \
  -H "Authorization: Bearer invalid_token_here" \
  -H "Content-Type: application/json" \
  -d '{"type":"email","to":"test@test.com","message":"test"}'

# Expected Response: 401 Unauthorized
{
  "detail": "Invalid or expired token"
}
```

### **Step 3: Test Valid Token (Should Work)**

First, get a valid token from Identity Service:

```bash
# Login to get token
TOKEN=$(curl -s -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"admin123"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"

# Test protected endpoint with valid token
curl -X POST http://localhost:8003/api/v1/notifications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"email","to":"test@test.com","message":"test"}'

# Expected Response: 200 OK with your endpoint's response
```

### **Step 4: Verify Health Endpoint Still Works**

```bash
curl http://localhost:8003/health

# Expected Response: 200 OK (no authentication required)
{
  "service": "communication-service",
  "status": "healthy",
  ...
}
```

---

## 🔐 **Identity Service Token Validation Endpoint**

For reference, the Identity Service provides this token validation endpoint:

**Endpoint**: `POST /auth/validate`  
**Headers**: `Authorization: Bearer <jwt_token>`  
**Response** (200 OK):
```json
{
  "user_id": "uuid-here",
  "organization_id": "uuid-here",
  "email": "user@example.com",
  "roles": ["user", "admin"],
  "permissions": ["read", "write"],
  "is_verified": true,
  "expires_at": "2024-01-01T12:00:00Z"
}
```

**Response** (401 Unauthorized):
```json
{
  "detail": "Invalid or expired token"
}
```

---

## ⚠️ **Important Security Notes**

### **Token Handling**
- ✅ **DO**: Store tokens securely on frontend (httpOnly cookies or secure storage)
- ❌ **DON'T**: Log JWT tokens in your application logs
- ❌ **DON'T**: Store tokens in localStorage without proper security

### **Error Handling**
- ✅ **DO**: Return consistent 401 errors for all authentication failures
- ✅ **DO**: Log authentication failures for monitoring
- ❌ **DON'T**: Expose internal error details to clients

### **Performance**
- ✅ **DO**: Use connection pooling for Identity Service calls
- ✅ **DO**: Set reasonable timeouts (5-10 seconds)
- ✅ **DO**: Consider caching valid tokens (advanced implementation)

### **Service Availability**
- ✅ **DO**: Handle Identity Service downtime gracefully
- ✅ **DO**: Return 503 Service Unavailable when auth service is down
- ❌ **DON'T**: Allow requests through when auth service is unavailable

---

## 🚀 **Implementation Priority**

Implement JWT authentication in this order:

1. **🥇 Communication Service** (most endpoints, active development)
2. **🥈 Workflow Intelligence Service** (complex permissions needed)
3. **🥉 Content Service** (already has placeholder structure)

Each service should be fully tested before moving to the next.

---

## ✅ **Verification Checklist**

For each service, verify:

- [ ] All protected endpoints require JWT authentication
- [ ] Health endpoint remains unprotected
- [ ] Invalid tokens return 401 Unauthorized
- [ ] Valid tokens return user data correctly
- [ ] Network errors are handled gracefully
- [ ] Authentication failures are logged
- [ ] Service-specific user context is available in endpoints

---

## 🧪 **Unit Testing JWT Authentication**

Once JWT authentication is implemented, you'll need comprehensive tests to ensure security is working correctly. Here's how to structure your tests:

### **Test Structure**

Create these test files in your service:

```
tests/
├── test_auth_integration.py     # JWT authentication tests
├── test_endpoints_security.py   # Endpoint protection tests  
├── test_auth_failures.py       # Error handling tests
└── conftest.py                  # Test fixtures and mocks
```

### **Test Fixtures (conftest.py)**

```python
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
```

### **Authentication Integration Tests (test_auth_integration.py)**

```python
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from main import app

class TestJWTAuthentication:
    """Test JWT token validation integration"""

    @patch('httpx.AsyncClient')
    def test_valid_token_authentication(self, mock_client, client, valid_token, mock_user_data):
        """Test successful authentication with valid token"""
        # Mock Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Test protected endpoint
        response = client.post(
            "/api/v1/your-endpoint",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={"test": "data"}
        )
        
        assert response.status_code == 200
        
        # Verify Identity Service was called correctly
        mock_client.return_value.__aenter__.return_value.post.assert_called_once_with(
            "http://localhost:8001/auth/validate",
            headers={"Authorization": f"Bearer {valid_token}"},
            timeout=5.0
        )

    @patch('httpx.AsyncClient')
    def test_invalid_token_authentication(self, mock_client, client, invalid_token):
        """Test authentication failure with invalid token"""
        # Mock Identity Service rejection
        mock_response = AsyncMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"detail": "Invalid token"}
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Test protected endpoint
        response = client.post(
            "/api/v1/your-endpoint",
            headers={"Authorization": f"Bearer {invalid_token}"},
            json={"test": "data"}
        )
        
        assert response.status_code == 401
        assert "Invalid or expired token" in response.json()["detail"]

    def test_missing_token_authentication(self, client):
        """Test authentication failure with no token"""
        response = client.post(
            "/api/v1/your-endpoint",
            json={"test": "data"}
        )
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    def test_identity_service_timeout(self, mock_client, client, valid_token):
        """Test handling of Identity Service timeout"""
        # Mock timeout exception
        mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.TimeoutException("Timeout")
        
        response = client.post(
            "/api/v1/your-endpoint", 
            headers={"Authorization": f"Bearer {valid_token}"},
            json={"test": "data"}
        )
        
        assert response.status_code == 503
        assert "temporarily unavailable" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    def test_identity_service_network_error(self, mock_client, client, valid_token):
        """Test handling of Identity Service network errors"""
        # Mock network exception
        mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.RequestError("Network error")
        
        response = client.post(
            "/api/v1/your-endpoint",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={"test": "data"}
        )
        
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"]
```

### **Endpoint Security Tests (test_endpoints_security.py)**

```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app

class TestEndpointSecurity:
    """Test that all endpoints are properly protected"""

    def test_health_endpoint_unprotected(self, client):
        """Test that health endpoint doesn't require authentication"""
        response = client.get("/health")
        assert response.status_code == 200
        # Health endpoint should work without any authentication

    @pytest.mark.parametrize("endpoint,method,data", [
        ("/api/v1/notifications", "POST", {"type": "email", "to": "test@test.com", "message": "test"}),
        ("/api/v1/notifications/unread", "GET", None),
        ("/api/v1/messages", "POST", {"to": "user123", "content": "test"}),
        ("/api/v1/conversations", "GET", None),
        ("/api/v1/templates", "POST", {"name": "test", "content": "test"}),
        ("/api/v1/templates", "GET", None),
        # Add all your protected endpoints here
    ])
    def test_endpoints_require_authentication(self, client, endpoint, method, data):
        """Test that all protected endpoints require authentication"""
        if method == "GET":
            response = client.get(endpoint)
        elif method == "POST":
            response = client.post(endpoint, json=data)
        elif method == "PUT":
            response = client.put(endpoint, json=data)
        elif method == "DELETE":
            response = client.delete(endpoint)
        
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    @patch('httpx.AsyncClient')
    @pytest.mark.parametrize("endpoint,method,data", [
        ("/api/v1/notifications", "POST", {"type": "email", "to": "test@test.com", "message": "test"}),
        ("/api/v1/notifications/unread", "GET", None),
        # Add your endpoints here
    ])
    def test_endpoints_work_with_valid_authentication(self, mock_client, client, endpoint, method, data, valid_token, mock_user_data):
        """Test that protected endpoints work with valid authentication"""
        # Mock successful Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        headers = {"Authorization": f"Bearer {valid_token}"}
        
        if method == "GET":
            response = client.get(endpoint, headers=headers)
        elif method == "POST":
            response = client.post(endpoint, headers=headers, json=data)
        
        # Should not return 401 (authentication should succeed)
        assert response.status_code != 401
        # Actual status depends on your endpoint implementation
```

### **Error Handling Tests (test_auth_failures.py)**

```python
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app

class TestAuthenticationErrorHandling:
    """Test various authentication error scenarios"""

    @patch('httpx.AsyncClient')
    def test_malformed_token_handling(self, mock_client, client):
        """Test handling of malformed Bearer token"""
        response = client.post(
            "/api/v1/your-endpoint",
            headers={"Authorization": "Bearer malformed.token.here"},
            json={"test": "data"}
        )
        
        # Should handle gracefully and return 401
        assert response.status_code == 401

    @patch('httpx.AsyncClient')
    def test_identity_service_500_error(self, mock_client, client, valid_token):
        """Test handling when Identity Service returns 500"""
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        response = client.post(
            "/api/v1/your-endpoint",
            headers={"Authorization": f"Bearer {valid_token}"},
            json={"test": "data"}
        )
        
        assert response.status_code == 401  # Should treat as auth failure

    def test_authorization_header_variations(self, client):
        """Test various Authorization header formats"""
        test_cases = [
            "bearer token123",  # lowercase
            "Bearer",  # missing token
            "Basic token123",   # wrong auth type  
            "",  # empty
        ]
        
        for auth_header in test_cases:
            response = client.post(
                "/api/v1/your-endpoint",
                headers={"Authorization": auth_header},
                json={"test": "data"}
            )
            assert response.status_code == 401

    @patch('httpx.AsyncClient')
    def test_user_context_availability(self, mock_client, client, valid_token, mock_user_data):
        """Test that user context is properly passed to endpoints"""
        # Mock successful auth
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        # Test endpoint that uses user context
        response = client.get(
            "/api/v1/user-specific-data",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        
        # Verify user context was used (depends on your endpoint implementation)
        assert response.status_code != 401
        # Additional assertions based on how your endpoint uses user data
```

### **Running the Tests**

```bash
# Run all authentication tests
pytest tests/test_auth_integration.py -v

# Run specific test class
pytest tests/test_auth_integration.py::TestJWTAuthentication -v

# Run tests with coverage
pytest tests/test_auth_integration.py --cov=main --cov-report=html

# Test specific authentication scenario
pytest tests/test_auth_integration.py::TestJWTAuthentication::test_valid_token_authentication -v
```

### **Test Coverage Requirements**

Ensure your tests cover:

- ✅ **Valid token authentication** (200 responses)
- ✅ **Invalid token rejection** (401 responses)  
- ✅ **Missing token rejection** (401 responses)
- ✅ **Identity Service timeout handling** (503 responses)
- ✅ **Identity Service network errors** (503 responses)
- ✅ **Health endpoint accessibility** (no auth required)
- ✅ **All protected endpoints require auth** (comprehensive test)
- ✅ **User context availability** in endpoints
- ✅ **Error message consistency** (security)
- ✅ **Authorization header format variations**

### **Mocking Best Practices**

```python
# Mock httpx client at the module level
@patch('your_service.main.httpx.AsyncClient')

# Mock specific responses for different scenarios
def mock_identity_responses(status_code, json_data=None, exception=None):
    mock_response = AsyncMock()
    if exception:
        raise exception
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data or {}
    return mock_response

# Use fixtures for consistent test data
@pytest.fixture
def admin_user_data():
    return {
        "user_id": "admin-uuid",
        "roles": ["admin", "user"],
        "permissions": ["read", "write", "delete", "admin"]
    }

@pytest.fixture
def regular_user_data():
    return {
        "user_id": "user-uuid", 
        "roles": ["user"],
        "permissions": ["read", "write"]
    }
```

### **Performance Testing**

```python
import time
import pytest

class TestAuthenticationPerformance:
    """Test authentication performance"""

    @patch('httpx.AsyncClient')
    def test_auth_response_time(self, mock_client, client, valid_token, mock_user_data):
        """Test that authentication doesn't add excessive latency"""
        # Mock fast Identity Service response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_data
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        start_time = time.time()
        response = client.get(
            "/api/v1/quick-endpoint",
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        end_time = time.time()
        
        # Authentication should add minimal overhead (< 100ms in test environment)
        assert (end_time - start_time) < 0.1
        assert response.status_code != 401
```

### **Integration Test Example**

```python
import pytest
from fastapi.testclient import TestClient
import requests

class TestRealAuthenticationFlow:
    """Integration tests with real Identity Service (if available)"""
    
    @pytest.mark.integration
    def test_real_identity_service_integration(self, client):
        """Test with actual Identity Service (requires running Identity Service)"""
        # First, login to get real token
        login_response = requests.post(
            "http://localhost:8001/auth/login",
            json={"email": "test@example.com", "password": "testpass123"}
        )
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            
            # Test protected endpoint with real token
            response = client.get(
                "/api/v1/your-endpoint",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code != 401
        else:
            pytest.skip("Identity Service not available for integration test")
```

### **Test Configuration**

Add to `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --disable-warnings
    --cov=main
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=80

markers = 
    integration: marks tests as integration tests (require running services)
    slow: marks tests as slow
    auth: marks tests as authentication-related
```

### **Running Tests in CI/CD**

```yaml
# In your GitHub Actions or CI pipeline:
- name: Run Authentication Tests
  run: |
    # Start Identity Service for integration tests
    docker-compose up -d identity-service
    
    # Wait for service to be ready
    sleep 10
    
    # Run unit tests (mocked)
    pytest tests/test_auth_integration.py -m "not integration"
    
    # Run integration tests (real services)
    pytest tests/test_auth_integration.py -m integration
    
    # Cleanup
    docker-compose down
```

**🎯 These tests ensure your JWT authentication implementation is secure, robust, and handles all edge cases properly. Run these tests after implementing authentication to verify everything works correctly!**

---

## 🆘 **Troubleshooting**

### **Common Issues**

**Issue**: "Token validation failed" with valid token  
**Solution**: Check `IDENTITY_SERVICE_URL` environment variable

**Issue**: Timeout errors  
**Solution**: Verify Identity Service is running and accessible

**Issue**: "Not authenticated" even with Bearer token  
**Solution**: Ensure HTTPBearer() is configured and token format is correct

**Issue**: Health endpoint returns 401  
**Solution**: Remove authentication dependency from health endpoint

### **Debug Mode**

Add this to your service for debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In your validate_jwt_token function, add:
logger.debug(f"Validating token: {token.credentials[:20]}...")
logger.debug(f"Identity Service URL: {IDENTITY_SERVICE_URL}")
```

---

## 📞 **Support**

**Coordination Issues**: Add to `COORDINATION_ISSUES.md`  
**Identity Service Questions**: Check Identity Service documentation  
**Implementation Help**: Services Coordinator Agent

---

**🎯 After implementing JWT authentication, your microservices will achieve production-grade security with centralized user management through the Identity Service!**

---

**Document Maintainer**: Services Coordinator Agent  
**Last Updated**: 2025-09-09  
**Version**: 1.0  
**Next Review**: After all services implement JWT authentication