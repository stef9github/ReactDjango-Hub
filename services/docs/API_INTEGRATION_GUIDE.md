# API Integration Guide - Cross-Service Communication

**Managed by**: Services Coordinator Agent

## 🏗️ **Service Architecture**

```mermaid
graph TD
    Frontend[Frontend React App]
    Identity[🔐 Identity Service :8001]
    Content[📄 Content Service :8002]
    Comm[📢 Communication Service :8003]
    Workflow[🔄 Workflow Service :8004]
    
    Frontend --> Identity
    Frontend --> Content
    Frontend --> Comm  
    Frontend --> Workflow
    
    Content --> Identity
    Comm --> Identity
    Workflow --> Identity
    Workflow --> Content
    Workflow --> Comm
```

## 🔐 **Authentication Flow**

### 1. **Login Process**
```typescript
// 1. Frontend authenticates with Identity Service
const response = await fetch('http://localhost:8001/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});

const { access_token, refresh_token } = await response.json();
```

### 2. **Service-to-Service Authentication**
```python
# All other services validate tokens with Identity Service
async def validate_token(token: str) -> UserContext:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://identity-service:8001/auth/validate",
            json={"token": token}
        )
        if response.status_code == 200:
            return UserContext(**response.json())
        raise AuthenticationError("Invalid token")
```

## 📡 **Standard API Patterns**

### **Health Check** (All Services)
```bash
GET /health
```
Response:
```json
{
  "service": "service-name",
  "status": "healthy|degraded|unhealthy",
  "version": "1.0.0",
  "port": 8001,
  "dependencies": {
    "database": "healthy",
    "redis": "healthy",
    "identity-service": "healthy"
  }
}
```

### **API Documentation** (All Services)
```bash
GET /docs          # Swagger UI
GET /redoc         # ReDoc
GET /openapi.json  # OpenAPI specification
```

### **Standard Headers**
```http
Authorization: Bearer {jwt_token}
Content-Type: application/json
X-Trace-ID: {uuid}
X-Request-ID: {uuid}
```

### **Standard Error Format**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "service": "content-service",
    "timestamp": "2024-01-01T12:00:00Z",
    "trace_id": "uuid",
    "details": {}
  }
}
```

## 🔄 **Service Integration Patterns**

### **Identity Service Integration** (Required by all services)
```python
# Standard identity integration pattern
class IdentityServiceClient:
    def __init__(self):
        self.base_url = os.getenv("IDENTITY_SERVICE_URL", "http://identity-service:8001")
    
    async def validate_token(self, token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/auth/validate",
                json={"token": token}
            )
            return response.json()
    
    async def get_user_permissions(self, user_id: str) -> list:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/auth/permissions/{user_id}"
            )
            return response.json()
```

### **Content Service Integration**
```python
# How other services interact with Content Service
class ContentServiceClient:
    async def store_document(self, file_data: bytes, metadata: dict) -> str:
        async with httpx.AsyncClient() as client:
            files = {"file": file_data}
            data = {"metadata": json.dumps(metadata)}
            response = await client.post(
                "http://content-service:8002/api/v1/documents",
                files=files,
                data=data
            )
            return response.json()["document_id"]
```

### **Communication Service Integration**
```python
# How other services send notifications
class CommunicationServiceClient:
    async def send_notification(self, user_id: str, message: str, type: str = "in_app"):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://communication-service:8003/api/v1/notifications",
                json={
                    "to": user_id,
                    "message": message,
                    "type": type
                }
            )
            return response.json()
```

### **Workflow Service Integration**
```python
# How other services trigger workflows
class WorkflowServiceClient:
    async def create_workflow(self, definition_id: str, entity_id: str, context: dict):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://workflow-service:8004/api/v1/workflows",
                json={
                    "definition_id": definition_id,
                    "entity_id": entity_id,
                    "context": context
                }
            )
            return response.json()
```

## 🌐 **Environment Configuration**

### **Service Discovery**
```bash
# Each service should define these for service-to-service communication
IDENTITY_SERVICE_URL=http://identity-service:8001
CONTENT_SERVICE_URL=http://content-service:8002
COMMUNICATION_SERVICE_URL=http://communication-service:8003
WORKFLOW_SERVICE_URL=http://workflow-service:8004
```

### **Database Configuration Pattern**
```bash
# Each service follows this pattern
DATABASE_URL=postgresql+asyncpg://service_user:service_pass@service-db:5432/service_database
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

### **Redis Configuration Pattern**  
```bash
# Each service follows this pattern
REDIS_URL=redis://service-redis:6379/0
REDIS_MAX_CONNECTIONS=10
```

## 🧪 **Integration Testing**

### **Service Health Verification**
```bash
# Check all services are running
./scripts/health-check-all.sh
```

### **Cross-Service Authentication Test**
```python
async def test_cross_service_auth():
    # 1. Get token from identity service
    login_response = await client.post("/auth/login", json={"email": "test@example.com", "password": "password"})
    token = login_response.json()["access_token"]
    
    # 2. Use token with other services
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test content service
    content_response = await client.get("http://content-service:8002/api/v1/documents", headers=headers)
    assert content_response.status_code == 200
    
    # Test communication service  
    comm_response = await client.get("http://communication-service:8003/api/v1/notifications/unread", headers=headers)
    assert comm_response.status_code == 200
```

## 📋 **API Contract Versioning**

### **Version Strategy**
- **URL Versioning**: `/api/v1/`, `/api/v2/`
- **Header Versioning**: `Accept: application/vnd.api+json;version=1`
- **Backward Compatibility**: Maintain previous version for 6 months

### **Breaking Changes**
1. Announce 30 days before implementation
2. Update all dependent services
3. Maintain backward compatibility during transition
4. Document migration guide

---

**⚠️ This guide is maintained by the Services Coordinator Agent. Updates to cross-service communication patterns should be coordinated here.**