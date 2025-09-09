# Backend Documentation

Django business logic service for ReactDjango Hub - works alongside the standalone auth-service microservice.

## 🏗️ **Microservices Architecture**

This Django backend handles **business logic only**. Authentication is managed by the standalone `auth-service`:

| Service | Purpose | Port | Technology |
|---------|---------|------|------------|
| **`auth-service`** | Authentication, users, organizations, MFA | 8001 | FastAPI + PostgreSQL |
| **`backend/` (Django)** | Business logic, medical records, billing | 8000 | Django + PostgreSQL |

## 🚀 Quick Start

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Prerequisites**: Auth service must be running on port 8001
- See `services/auth-service/` for authentication setup

Access Django Ninja API docs at: `http://localhost:8000/api/docs`

## 📁 Django Applications (Business Logic Only)

| App | Purpose | Key Features | Auth Integration |
|-----|---------|-------------|------------------|
| **`core/`** | Foundation layer | BaseModel, RGPD compliance, translations | Integrates with auth-service for user context |
| **`analytics/`** | Data intelligence | Metrics, reporting, permissions | Uses auth-service for user permissions |
| **`clinical/`** | Medical records | Patient data, HL7/DICOM support | Auth-service handles patient access control |
| **`billing/`** | Financial management | Multi-tenant billing, payments | Organization data from auth-service |
| **`compliance/`** | Regulatory framework | RGPD automation, audit trails | User activity logs via auth-service |

## 🔌 API Development

- **Framework**: Django Ninja 1.4.3 (FastAPI-style)
- **Documentation**: Auto-generated OpenAPI/Swagger
- **Authentication**: **Delegated to auth-service** (JWT token validation)
- **Endpoints**: `/api/` (see [ninja_api.py](../config/ninja_api.py))
- **Auth Integration**: Validates tokens against `http://auth-service:8001/auth/validate`

### Adding New Endpoints with Auth Integration

```python
# In config/ninja_api.py
from apps.core.auth_integration import require_auth, get_current_user

@api.get("/your-endpoint", response=YourSchema, tags=["YourTag"])
@require_auth  # Validates JWT token with auth-service
def your_function(request):
    """Your endpoint description"""
    # Get user context from auth-service
    user_context = get_current_user(request)
    user_id = user_context['user_id']
    organization_id = user_context['organization_id']
    
    # Your business logic here
    return your_data
```

## 🔗 **Auth Service Integration**

The Django backend integrates with the auth-service for all authentication:

```python
# Example: Validate JWT token and get user context
import httpx

async def validate_token(token: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://auth-service:8001/auth/validate",
            json={"token": token}
        )
        return response.json()

# Example: Check user permissions
async def check_permission(token: str, resource: str, action: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://auth-service:8001/auth/authorize", 
            headers={"Authorization": f"Bearer {token}"},
            json={"resource": resource, "action": action}
        )
        return response.json()["authorized"]
```

## 🧪 Testing & Development

```bash
# Start auth service first (required dependency)
cd ../services/auth-service && python main.py

# In another terminal, start Django backend
cd backend
python manage.py runserver

# Run tests
python manage.py test
python manage.py test apps.clinical

# Django shell with IPython
python manage.py shell

# Health check (requires auth-service)
curl http://localhost:8000/health/
```

## 📚 Complete Documentation

For detailed architecture, security, and deployment information:
- **[Auth Service Documentation](../services/auth-service/README.md)** - Authentication microservice
- **[Backend Architecture](./BACKEND_ARCHITECTURE.md)** - Business logic service details
- **[Microservices Architecture](../services/MICROSERVICES_ARCHITECTURE.md)** - Complete system design
- **[Project Overview](../CLAUDE.md)** - Development workflow and setup
- **API Docs**: `/api/docs` when server is running

## 🏥 Data Protection & Medical Compliance

- **Authentication**: Handled by dedicated auth-service with MFA, RBAC, audit trails
- **Authorization**: JWT token validation and permission checking via auth-service
- **RGPD**: Patient data protection framework (see `apps.core.rgpd_compliance`)
- **Audit Logging**: All model changes tracked via django-auditlog + auth-service activity logs
- **Medical Standards**: HL7 and DICOM support in clinical app
- **Multi-tenant**: Organization isolation managed by auth-service
- **Data Access**: All patient data access controlled through auth-service permissions

---

*For frontend documentation and full-stack workflow, see the main [CLAUDE.md](../CLAUDE.md) file.*