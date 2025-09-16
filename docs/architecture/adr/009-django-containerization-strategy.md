# ADR-009: Django Containerization Strategy

## Status
**Superseded by ADR-010** - September 2025

## Context

### Current State
The ReactDjango Hub platform consists of multiple microservices with inconsistent deployment patterns:

**Containerized Services:**
- 4 FastAPI microservices (Identity, Content, Communication, Workflow) - All running in Docker containers
- Kong API Gateway - Running in container on port 8080
- PostgreSQL databases - Multiple containerized instances per service
- Redis instances - Multiple containerized instances per service

**Non-Containerized Services:**
- Django backend service - Running directly on host machine (port 8000)
- Frontend (React/Vite) - Running directly on host via Yarn (port 5173)

### Problem Statement
This hybrid approach creates several challenges:

1. **Development Environment Inconsistency**: Developers need different workflows for containerized vs non-containerized services
2. **Network Complexity**: Mixed container/host networking complicates service discovery and API routing
3. **Database Connection Management**: Django needs special configuration to connect to containerized databases
4. **Environment Parity**: Difficulty maintaining consistency between development, staging, and production
5. **Team Onboarding**: New developers must understand two different deployment paradigms
6. **CI/CD Complexity**: Build and deployment pipelines must handle both patterns

### Kong API Gateway Integration Challenge
Kong expects to route to services within the Docker network. The current Kong configuration shows all services are expected to be containerized (e.g., `http://identity-service:8001`). Django running on the host requires special handling.

## Decision

### Primary Decision: **Hybrid Containerization Strategy**

We will adopt a **hybrid approach** that optimizes for both developer experience and architectural consistency:

#### Development Environment
- **Django**: Run **outside** containers by default for optimal DX
- **Microservices**: Continue running in containers
- **Infrastructure**: All databases, Redis, Kong in containers
- **Frontend**: Run on host for hot module replacement

#### Production Environment
- **All services**: Run in containers including Django and Frontend
- **Orchestration**: Kubernetes for production deployment
- **Service Mesh**: Kong handles all inter-service communication

### Implementation Strategy

#### 1. Development Environment Configuration

**Django Host Mode (Default)**
```yaml
# docker-compose.dev.yml
services:
  # Django DB runs in container
  django-db:
    image: postgres:17-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: reactdjango_hub
      POSTGRES_USER: django_user
      POSTGRES_PASSWORD: django_pass

  # Kong configured to route to host
  kong:
    environment:
      KONG_DECLARATIVE_CONFIG: /kong/kong-dev.yml
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

**Django Container Mode (Optional)**
```yaml
# docker-compose.dev-containerized.yml
services:
  django:
    build:
      context: ./backend
      dockerfile: ../infrastructure/docker/development/Dockerfile.backend
    volumes:
      - ./backend:/app  # Mount for hot reload
      - pip-cache:/root/.cache/pip
    environment:
      DATABASE_URL: postgresql://django_user:django_pass@django-db:5432/reactdjango_hub
    command: python manage.py runserver 0.0.0.0:8000
```

#### 2. Production Environment Configuration

**Full Containerization**
```yaml
# docker-compose.prod.yml
services:
  django:
    image: reactdjango-hub/backend:${VERSION}
    environment:
      DATABASE_URL: ${DATABASE_URL}
      DJANGO_SETTINGS_MODULE: config.settings.production
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 512M
```

#### 3. Network Architecture

**Development Network Setup**
```
Host Machine:
  - Django (8000) -> Connects to containers via localhost ports
  - Frontend (5173) -> Connects to Django and Kong

Docker Network (reactdjango-hub-network):
  - Kong Gateway (8080) -> Routes to all services
  - Identity Service (8001)
  - Content Service (8002)
  - Communication Service (8003)
  - Workflow Service (8004)
  - PostgreSQL instances (5432-5436)
  - Redis instances (6379-6383)
```

**Production Network Setup**
```
Kubernetes Cluster:
  - All services in containers
  - Service mesh for inter-service communication
  - Ingress controller for external access
  - Network policies for security
```

## Consequences

### Positive Consequences

1. **Optimized Developer Experience**
   - Django hot reload works instantly without container rebuild
   - Direct database access for debugging via psql
   - Simplified debugging with native Python tools
   - Faster iteration cycles for business logic development

2. **Production Consistency**
   - All services containerized in production
   - Consistent deployment patterns
   - Simplified CI/CD pipelines for production
   - Better resource isolation and management

3. **Flexible Migration Path**
   - Teams can gradually adopt containerization
   - Optional container mode for Django in development
   - Easy switch between modes via environment variables

4. **Simplified Database Management**
   - Django migrations run directly without container exec
   - Easy database inspection and manipulation
   - Consistent database containerization across all environments

### Negative Consequences

1. **Development Complexity**
   - Developers must understand hybrid networking
   - Special Kong configuration for host services
   - Different commands for different services

2. **Environment Disparity**
   - Development differs from production
   - Potential for "works on my machine" issues
   - Additional testing needed for production builds

3. **Documentation Overhead**
   - Must maintain docs for both patterns
   - Onboarding complexity for new developers
   - Multiple configuration files to maintain

### Risk Mitigation

1. **Network Issues**
   - Use `host.docker.internal` for container-to-host communication
   - Implement service discovery abstraction layer
   - Comprehensive network documentation

2. **Environment Parity**
   - Regular production-like testing in CI/CD
   - Docker compose profiles for different scenarios
   - Automated environment validation scripts

3. **Developer Confusion**
   - Clear documentation and runbooks
   - Makefile targets for common operations
   - Automated setup scripts for new developers

## Alternatives Considered

### Alternative 1: Full Containerization (All Services)
**Pros:**
- Complete consistency across all services
- Simplified networking (all in Docker)
- Single deployment pattern

**Cons:**
- Degraded Django development experience
- Complex volume mounting for hot reload
- Slower iteration cycles
- Debugging challenges

**Rejected because:** Developer productivity impact too significant for Django development.

### Alternative 2: No Containerization (All Host)
**Pros:**
- Simplified development setup
- Direct access to all services
- No Docker overhead

**Cons:**
- Loss of production parity
- Complex dependency management
- Difficult team onboarding
- No isolation between services

**Rejected because:** Loses benefits of containerization and microservices architecture.

### Alternative 3: Docker Compose Profiles
**Pros:**
- Single configuration file
- Easy mode switching
- Consistent tooling

**Cons:**
- Complex compose file
- Profile management overhead
- Potential for configuration drift

**Partially adopted:** Will use profiles for optional Django containerization.

## Implementation Plan

### Phase 1: Development Environment (Week 1)
1. Update docker-compose files for hybrid mode
2. Configure Kong for host service routing
3. Create Makefile targets for common operations
4. Update developer documentation

### Phase 2: CI/CD Pipeline (Week 2)
1. Create Django production Dockerfile
2. Update CI/CD for dual-mode testing
3. Implement production build pipeline
4. Add environment validation tests

### Phase 3: Production Deployment (Week 3)
1. Create Kubernetes manifests for Django
2. Configure production networking
3. Implement health checks and monitoring
4. Deploy to staging environment

### Phase 4: Documentation & Training (Week 4)
1. Complete architecture documentation
2. Create developer runbooks
3. Team training sessions
4. Update onboarding materials

## Success Metrics

1. **Developer Productivity**
   - Django change-to-test time < 5 seconds
   - Setup time for new developers < 30 minutes
   - No increase in debugging time

2. **System Reliability**
   - Production deployment success rate > 99%
   - Service discovery success rate = 100%
   - Container health check pass rate > 99.9%

3. **Team Adoption**
   - Developer satisfaction score > 4/5
   - Reduced support tickets for environment issues
   - Successful onboarding of new team members

## Review Schedule

- **3 months**: Evaluate developer experience and productivity metrics
- **6 months**: Review production stability and performance
- **12 months**: Full architecture review and optimization

## Decision Makers

- Technical Lead: Architecture approval
- Backend Team Lead: Django implementation
- DevOps Lead: Infrastructure implementation
- Product Manager: Timeline and resource approval

## References

- [Docker Best Practices for Python](https://docs.docker.com/language/python/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/)
- [Kong Gateway Documentation](https://docs.konghq.com/)
- [Kubernetes Django Deployment Guide](https://kubernetes.io/docs/tutorials/stateless-application/)

---

**Last Updated**: September 2025
**Superseded**: September 2025
**Status**: Superseded by ADR-010 - Local-First Development Strategy

## Supersession Note

This ADR has been superseded by ADR-010: Local-First Development Strategy. After careful consideration, we have decided to prioritize development velocity and simplicity by adopting a local-first approach for all services during the active development phase. Containerization will be reconsidered for production deployment when the platform reaches maturity.