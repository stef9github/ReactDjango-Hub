# ⚠️ DEPRECATED: Django Authentication Files

**Status**: DEPRECATED as of microservices migration  
**Date**: 2024-12-08  
**Reason**: Authentication moved to standalone auth-service

## 🚨 Important Notice

These authentication files are **NO LONGER USED** in the current architecture. 

Authentication is now handled by the **standalone auth-service** (FastAPI + PostgreSQL on port 8001).

### Current Architecture

| Service | Purpose | Port | Technology |
|---------|---------|------|------------|
| **auth-service** | Authentication, users, organizations, MFA | 8001 | FastAPI + PostgreSQL |
| **Django backend** | Business logic only | 8000 | Django + PostgreSQL |

### Files Status

- `api.py` - ⚠️ **OBSOLETE** - Authentication endpoints moved to auth-service
- `models.py` - ⚠️ **OBSOLETE** - User models moved to auth-service
- `services.py` - ⚠️ **OBSOLETE** - Auth services moved to auth-service
- `architecture.md` - ⚠️ **OBSOLETE** - See auth-service documentation instead

### Migration Guide

**For authentication features**, see:
- `services/auth-service/README.md` - Complete auth-service documentation
- `frontend/docs/api/README.md` - Frontend integration guide
- `backend/docs/README.md` - Django integration with auth-service

### Django Integration

Django now validates JWT tokens against the auth-service:

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
```

## 🧹 Cleanup

These files can be safely removed once the migration is fully complete and tested.