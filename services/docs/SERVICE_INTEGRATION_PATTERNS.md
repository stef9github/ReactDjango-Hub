# Service Integration Patterns

## 🎯 Overview
This document defines the standard integration patterns that all services in the ReactDjango Hub microservices architecture must follow.

---

## 🔐 Authentication Integration (MANDATORY)

All services MUST integrate with the **Identity Service** for authentication and authorization.

### Standard Authentication Flow
```python
# Every service includes this authentication dependency pattern:

import httpx
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

# Authentication client configuration
IDENTITY_SERVICE_URL = os.getenv("IDENTITY_SERVICE_URL", "http://identity-service:8001")
security = HTTPBearer()

async def validate_token(token: str = Depends(security)):
    """Validate JWT token with Identity Service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{IDENTITY_SERVICE_URL}/auth/validate",
                headers={"Authorization": f"Bearer {token.credentials}"}
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid token")
            
            return response.json()  # User info and permissions
        except httpx.RequestError:
            raise HTTPException(status_code=503, detail="Identity service unavailable")

# Usage in endpoints:
@app.get("/protected-resource")
async def get_resource(user_info = Depends(validate_token)):
    # user_info contains: user_id, email, roles, permissions
    return {"data": "protected", "user": user_info["user_id"]}
```

### Environment Variables Required
```bash
# All services must include:
IDENTITY_SERVICE_URL=http://identity-service:8001
JWT_SECRET_KEY=${SHARED_JWT_SECRET}  # From .env.shared
JWT_ALGORITHM=HS256
```

---

## 🏗️ Service-to-Service Communication

### HTTP Client Pattern
```python
# Standard HTTP client for service communication
import httpx
import asyncio
from typing import Optional

class ServiceClient:
    def __init__(self, base_url: str, service_name: str):
        self.base_url = base_url
        self.service_name = service_name
        self.timeout = httpx.Timeout(30.0, connect=5.0)
    
    async def make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[dict] = None,
        headers: Optional[dict] = None
    ):
        """Standard request with error handling and retries"""
        default_headers = {
            "Content-Type": "application/json",
            "X-Service-Name": self.service_name,
            "X-Trace-ID": str(uuid.uuid4())  # For distributed tracing
        }
        
        if headers:
            default_headers.update(headers)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=f"{self.base_url}{endpoint}",
                    json=data,
                    headers=default_headers
                )
                response.raise_for_status()
                return response.json()
            
            except httpx.TimeoutException:
                raise ServiceError(f"{self.service_name} timeout", 503)
            except httpx.HTTPStatusError as e:
                raise ServiceError(f"{self.service_name} error: {e.response.status_code}", e.response.status_code)
            except Exception as e:
                raise ServiceError(f"{self.service_name} unavailable: {str(e)}", 503)

# Usage example:
identity_client = ServiceClient(
    base_url=os.getenv("IDENTITY_SERVICE_URL"),
    service_name="content-service"
)

# Get user profile from identity service
user_profile = await identity_client.make_request(
    "GET", 
    f"/users/{user_id}/profile",
    headers={"Authorization": f"Bearer {token}"}
)
```

---

## 🗄️ Database Patterns

### Database Driver Selection (SERVICE-SPECIFIC)

**IMPORTANT**: Database drivers are **NOT** in shared requirements due to compilation conflicts. Each service must specify its own database driver in `requirements.txt`.

#### For Identity Service (Async Pattern)
```python
# requirements.txt
-r ../requirements.shared.txt
asyncpg==0.29.0  # Async PostgreSQL driver

# database.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")  # postgresql+asyncpg://...
engine = create_async_engine(
    DATABASE_URL,
    pool_size=int(os.getenv("DATABASE_POOL_SIZE", 10)),
    max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", 20)),
    pool_pre_ping=True
)

async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db_session() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

#### For Other Services (Sync Pattern)
```python
# requirements.txt
-r ../requirements.shared.txt
psycopg2-binary==2.9.9  # Sync PostgreSQL driver

# database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = os.getenv("DATABASE_URL")  # postgresql://...
engine = create_engine(
    DATABASE_URL,
    pool_size=int(os.getenv("DATABASE_POOL_SIZE", 10)),
    max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", 20)),
    pool_pre_ping=True
)

session_maker = sessionmaker(bind=engine)

def get_db_session() -> Session:
    session = session_maker()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

### Database Naming Conventions
```sql
-- Database names: {service_name}_service
-- Examples:
-- identity_service
-- content_service  
-- communication_service
-- workflow_intelligence_service

-- Table naming: snake_case, service prefix optional for clarity
-- Examples:
CREATE TABLE users (id SERIAL PRIMARY KEY, ...);
CREATE TABLE content_documents (id SERIAL PRIMARY KEY, ...);
CREATE TABLE communication_templates (id SERIAL PRIMARY KEY, ...);
```

---

## 🔄 Redis Integration Patterns

### Standard Redis Configuration
```python
# redis_client.py - Standard across all services
import os
import redis.asyncio as redis
from typing import Optional

class RedisClient:
    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL")
        if not self.redis_url:
            raise ValueError("REDIS_URL environment variable is required")
        
        self.client = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", 10))
        )
    
    async def set_with_expiry(self, key: str, value: str, expiry_seconds: int = 3600):
        await self.client.setex(key, expiry_seconds, value)
    
    async def get(self, key: str) -> Optional[str]:
        return await self.client.get(key)
    
    async def delete(self, key: str):
        await self.client.delete(key)

# Service-specific Redis key patterns:
# {service_name}:{resource_type}:{identifier}
# Examples:
# identity:session:user_123
# content:cache:document_456
# communication:queue:notification_789
```

---

## 📊 Health Check Standards

### Mandatory Health Endpoint
```python
# health.py - Required in all services
from fastapi import APIRouter
from sqlalchemy import text
import redis.asyncio as redis

router = APIRouter()

@router.get("/health")
async def health_check():
    """Standard health check format"""
    health_status = {
        "service": os.getenv("SERVICE_NAME", "unknown"),
        "status": "healthy",
        "version": "1.0.0",  # Should be from version file
        "port": int(os.getenv("SERVICE_PORT", 8000)),
        "dependencies": {},
        "metrics": {
            "uptime_seconds": get_uptime(),
            "active_connections": get_active_connections(),
            "memory_usage_mb": get_memory_usage()
        }
    }
    
    # Check database
    try:
        async with get_db_session() as db:
            await db.execute(text("SELECT 1"))
        health_status["dependencies"]["database"] = "healthy"
    except:
        health_status["dependencies"]["database"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        redis_client = redis.from_url(os.getenv("REDIS_URL"))
        await redis_client.ping()
        await redis_client.close()
        health_status["dependencies"]["redis"] = "healthy"
    except:
        health_status["dependencies"]["redis"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Identity Service (for non-identity services)
    if os.getenv("SERVICE_NAME") != "identity-service":
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{IDENTITY_SERVICE_URL}/health", timeout=5.0)
                if response.status_code == 200:
                    health_status["dependencies"]["identity-service"] = "healthy"
                else:
                    raise Exception("Identity service unhealthy")
        except:
            health_status["dependencies"]["identity-service"] = "unhealthy"
            health_status["status"] = "degraded"
    
    return health_status
```

---

## 🚀 FastAPI Application Structure

### Standard main.py Template
```python
# main.py - Standard structure for all services
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Service-specific imports
from .api import router as api_router
from .health import router as health_router

# Application configuration
SERVICE_NAME = os.getenv("SERVICE_NAME", "unknown-service")
SERVICE_VERSION = "1.0.0"
SERVICE_PORT = int(os.getenv("SERVICE_PORT", 8000))

# FastAPI app configuration
app = FastAPI(
    title=f"{SERVICE_NAME.title()} API",
    description=f"Microservice for {SERVICE_NAME} functionality",
    version=SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware - configure for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standard routers
app.include_router(health_router, tags=["Health"])
app.include_router(api_router, prefix="/api/v1", tags=["API"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=os.getenv("DEBUG") == "true",
        log_level="info"
    )
```

---

## 🐳 Docker Standards

### Standard Dockerfile Template
```dockerfile
# Dockerfile - Standard across all services
FROM python:3.13.7-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${SERVICE_PORT}/health || exit 1

# Default command
CMD ["python", "main.py"]
```

---

## 🧪 Testing Standards

### Integration Test Template
```python
# tests/test_integration.py - Standard integration tests
import pytest
import httpx
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    """Test health endpoint returns expected format"""
    response = client.get("/health")
    assert response.status_code == 200
    
    health_data = response.json()
    required_fields = ["service", "status", "version", "port", "dependencies", "metrics"]
    
    for field in required_fields:
        assert field in health_data

def test_authentication_integration():
    """Test authentication with Identity Service"""
    # This test requires Identity Service to be running
    # Implementation depends on service-specific endpoints
    pass

@pytest.mark.asyncio
async def test_service_communication():
    """Test communication with other services"""
    # Test HTTP client patterns
    # Verify error handling and retries
    pass
```

---

## 📝 Environment Variables Standards

### Required Variables (All Services)
```bash
# Service Identity
SERVICE_NAME=service-name
SERVICE_VERSION=1.0.0
SERVICE_PORT=800X

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/database
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://host:port/0
REDIS_MAX_CONNECTIONS=10

# Identity Service Integration
IDENTITY_SERVICE_URL=http://identity-service:8001
JWT_SECRET_KEY=${SHARED_JWT_SECRET}
JWT_ALGORITHM=HS256

# Logging and Debug
DEBUG=false
LOG_LEVEL=INFO
```

### Service-Specific Environment Variables
```bash
# Content Service
CONTENT_SERVICE_URL=http://content-service:8002

# Communication Service  
COMMUNICATION_SERVICE_URL=http://communication-service:8003
CELERY_BROKER_URL=redis://communication-redis:6379/1

# Workflow Service
WORKFLOW_SERVICE_URL=http://workflow-service:8004
OPENAI_API_KEY=${OPENAI_API_KEY}
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

---

## 🎯 Implementation Checklist

When implementing a new service, ensure:

### ✅ Core Requirements
- [ ] Uses `requirements.shared.txt` as base dependencies
- [ ] Implements standard health check endpoint `/health`
- [ ] Integrates with Identity Service for authentication
- [ ] Follows database naming conventions
- [ ] Uses standard Redis key patterns
- [ ] Implements proper error handling and logging

### ✅ Integration Requirements  
- [ ] HTTP client for service-to-service communication
- [ ] Standard environment variable configuration
- [ ] Docker configuration following template
- [ ] CORS middleware configured for frontend
- [ ] Integration tests covering auth and service communication

### ✅ Documentation Requirements
- [ ] Service-specific README.md
- [ ] API documentation accessible via `/docs`
- [ ] Environment variables documented in `.env.example`
- [ ] Integration patterns documented

---

## 🔄 Service Communication Matrix

| From Service | To Service | Purpose | Authentication Required |
|--------------|------------|---------|------------------------|
| **All Services** | Identity Service | Token validation, user info | Yes (JWT) |
| Content Service | Identity Service | User permissions, profiles | Yes |
| Communication Service | Identity Service | User contact info | Yes |
| Workflow Service | Identity Service | User roles, permissions | Yes |
| Workflow Service | Content Service | Document processing | Yes |
| Workflow Service | Communication Service | Send notifications | Yes |

---

**Maintained by**: Services Coordinator Agent  
**Last Updated**: 2025-09-09  
**Version**: 1.0