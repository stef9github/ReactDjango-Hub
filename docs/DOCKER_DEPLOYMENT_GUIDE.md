# Docker Deployment Guide

## Current Python Version Standards

### Microservices (FastAPI-based)
**Standard: Python 3.11**

All microservices use Python 3.11 due to technical constraints:

| Service | Technology | Port | Python Version | Reason |
|---------|------------|------|----------------|---------|
| `identity-service` | FastAPI | 8001 | **3.11** | gRPC compatibility issues with 3.13 |
| `communication-service` | FastAPI | 8002 | **3.11** | Dependency consistency |
| `content-service` | FastAPI | 8003 | **3.11** | python-consul compatibility |
| `workflow-intelligence-service` | FastAPI | 8004 | **3.11** | Dependency consistency |

### Backend Services
**Standard: Python 3.13**

| Service | Technology | Port | Python Version | Status |
|---------|------------|------|----------------|--------|
| `backend` (Django) | Django 5.1.4 | 8000 | **3.13** | ✅ Production ready |
| `frontend` | React + Vite | 3000/5173 | N/A | Node.js based |

## Critical Security Issue: Identity Service Root User

### Current Problem
The identity service Dockerfile runs as root user:
```dockerfile
# services/identity-service/Dockerfile
# For now, run as root to avoid permission issues  
# TODO: Fix user permissions properly
```

### Security Fix Required
Add non-root user before production deployment:

```dockerfile
# Add after line 28 (after installing runtime dependencies):
RUN groupadd -r identityuser \
    && useradd -r -g identityuser -d /app -s /bin/bash identityuser \
    && chown -R identityuser:identityuser /app

# Before COPY . . (around line 37):
COPY --chown=identityuser:identityuser . .

# After copying code, switch user:
USER identityuser

# Update PATH to use user local packages:
ENV PATH=/home/identityuser/.local/bin:$PATH
```

## Deployment Readiness Status

### ✅ Production Ready
- Backend Django service
- Frontend React application
- Docker orchestration infrastructure
- Health checks and monitoring
- Multi-environment support

### ⚠️ Requires Security Fix
- Identity service (root user issue)

### 📋 Deployment Checklist

**Before Production:**
- [ ] Fix identity service root user security issue
- [ ] Test all service health checks
- [ ] Verify environment variable configuration
- [ ] Run integration tests across all services
- [ ] Security scan all Docker images

**Production Deployment:**
```bash
# Start full production stack
make prod-up

# Verify all services are healthy
make docker-health

# Monitor service logs
make docker-logs
```

## Docker Architecture

The project uses a mature microservices architecture with:

- **4 microservices** with individual Dockerfiles and health checks
- **Comprehensive orchestration** via docker-compose and Makefile
- **Multi-environment support** (development, staging, production)
- **Centralized Docker management** through docker-manager.sh script
- **Production-ready infrastructure** with API gateway and service discovery

## Technical Constraints Documentation

### Python Version Rationale

**Why Python 3.11 for Microservices:**
- `grpcio` dependencies have compilation issues with Python 3.13
- `python-consul==1.1.0` compatibility concerns with newer Python versions
- Temporarily disabled gRPC dependencies in identity service due to Python 3.13 issues

**Future Migration Path:**
Monitor dependency updates for Python 3.13 compatibility:
- Check `grpcio` wheel availability for Python 3.13
- Test `python-consul` with Python 3.13
- Gradual migration when dependencies are stable

---

*Last Updated: September 10, 2025*
*Status: 1 Critical Security Issue Remaining Before Production*