# Backend Documentation

Quick reference for Django Ninja backend development.

## 🚀 Quick Start

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Access Django Ninja API docs at: `http://localhost:8000/api/docs`

## 📁 Django Applications

| App | Purpose | Key Features |
|-----|---------|-------------|
| **`core/`** | Foundation layer | BaseModel, RGPD compliance, translations |
| **`analytics/`** | Data intelligence | Metrics, reporting, object permissions |
| **`clinical/`** | Medical records | Patient data, HL7/DICOM support |
| **`billing/`** | Financial management | Multi-tenant billing, payment processing |
| **`compliance/`** | Regulatory framework | RGPD automation, audit trails |

## 🔌 API Development

- **Framework**: Django Ninja 1.4.3 (FastAPI-style)
- **Documentation**: Auto-generated OpenAPI/Swagger
- **Authentication**: Django sessions + object permissions
- **Endpoints**: `/api/` (see [ninja_api.py](../config/ninja_api.py))

### Adding New Endpoints

```python
# In config/ninja_api.py
@api.get("/your-endpoint", response=YourSchema, tags=["YourTag"])
def your_function(request):
    """Your endpoint description"""
    return your_data
```

## 🧪 Testing & Development

```bash
# Run tests
python manage.py test
python manage.py test apps.analytics

# Django shell with IPython
python manage.py shell

# Health check
curl http://localhost:8000/health/
```

## 📚 Complete Documentation

For detailed architecture, security, and deployment information:
- **[Backend Architecture](./BACKEND_ARCHITECTURE.md)** - Complete technical documentation
- **[Project Overview](../CLAUDE.md)** - Development workflow and setup
- **API Docs**: `/api/docs` when server is running

## 🏥 Data Protection & Medical Compliance

- **RGPD**: Patient data protection framework (see `apps.core.rgpd_compliance`)
- **Audit Logging**: All model changes tracked via django-auditlog
- **Medical Standards**: HL7 and DICOM support in clinical app
- **Multi-tenant**: Strict data isolation between medical practices
- **Object Permissions**: Fine-grained access control via django-guardian

---

*For frontend documentation and full-stack workflow, see the main [CLAUDE.md](../CLAUDE.md) file.*