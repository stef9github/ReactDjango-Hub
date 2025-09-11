# ADR-005: Service Port Assignment Strategy

## Status
Accepted

## Context
A critical port conflict was discovered in our microservices architecture where both Kong API Gateway and the Django Backend service were configured to use port 8000. This created a runtime conflict preventing both services from operating simultaneously.

The current port assignments across the platform were:
- Kong Gateway: 8000 (proxy), 8445 (admin) - CONFLICT
- Django Backend: 8000 - CONFLICT  
- Identity Service: 8001
- Communication Service: 8002/8003 (inconsistent)
- Content Service: 8003/8002 (inconsistent)
- Workflow Service: 8004
- Frontend: 3000/5173

This conflict required an immediate architectural decision to establish a consistent, memorable, and scalable port assignment strategy.

## Decision

### 1. Django Backend Port Assignment
**Django Backend will use port 8000** (remains unchanged)

Rationale:
- Port 8000 is the Django convention and default
- Django developers universally expect port 8000
- All existing Django documentation and tutorials use 8000
- Changing Django's port would break developer muscle memory

### 2. Kong API Gateway Port Assignment  
**Kong Gateway will use port 8080** (changed from 8000)

Rationale:
- Port 8080 is the standard alternative HTTP port
- Common for proxies and gateways (nginx, Apache, etc.)
- Maintains clear separation from application services
- Easy to remember: "80" for HTTP, "8080" for proxy

### 3. Complete Port Assignment Strategy

#### API Gateway Layer (8080-8089)
- **8080**: Kong Proxy (main gateway)
- **8081**: Kong Admin API
- **8443**: Kong Proxy SSL
- **8444**: Kong Admin SSL

#### Application Services Layer (8000-8099)
- **8000**: Django Backend (business logic)
- **8001**: Identity Service (authentication)
- **8002**: Communication Service
- **8003**: Content Service  
- **8004**: Workflow Intelligence Service
- **8005-8099**: Reserved for future microservices

#### Frontend Layer (3000-3999)
- **3000**: React production build
- **5173**: Vite development server

#### Database Layer (5432-5499)
- **5432**: Main PostgreSQL
- **5433**: Identity PostgreSQL
- **5434**: Communication PostgreSQL
- **5435**: Content PostgreSQL
- **5436**: Workflow PostgreSQL

#### Cache Layer (6379-6399)
- **6379**: Main Redis
- **6380**: Identity Redis
- **6381**: Communication Redis
- **6382**: Content Redis
- **6383**: Workflow Redis

#### Supporting Services (9000-9999)
- **9000**: MinIO API
- **9001**: MinIO Console
- **9200**: Elasticsearch (future)
- **9300**: Elasticsearch cluster (future)
- **9411**: Zipkin tracing (future)

## Consequences

### Positive
- **Clear separation of concerns**: Each layer has its own port range
- **No conflicts**: All services can run simultaneously
- **Industry standards**: Uses conventional ports (8080 for proxy, 8000 for Django)
- **Memorable pattern**: Sequential numbering within each layer
- **Scalable**: Room for growth in each port range
- **Developer friendly**: Respects framework conventions

### Negative
- **Configuration updates required**: Kong configuration must be updated across all environments
- **Documentation updates**: All references to Kong on port 8000 need updating
- **Frontend updates**: Any hardcoded gateway URLs need updating

### Risks
- **Migration complexity**: Existing deployments need coordinated updates
- **Client updates**: Any external clients using port 8000 for the gateway need notification

## Implementation Plan

### Immediate Actions (Priority 1)
1. Update `services/docker-compose.yml` to use Kong on port 8080
2. Update `docker-compose.local.yml` to use Kong on port 8080
3. Update Kong health check response to include correct port
4. Fix Communication Service port inconsistency (standardize on 8002)
5. Fix Content Service port inconsistency (standardize on 8003)

### Follow-up Actions (Priority 2)
1. Update all Kubernetes manifests with new port assignments
2. Update production docker-compose files
3. Update all environment variable templates
4. Update API documentation with new gateway port
5. Update developer onboarding documentation

### Validation Steps
1. Verify all services start without port conflicts
2. Test service-to-service communication through gateway
3. Validate frontend can reach all services
4. Ensure health checks pass for all services

## Alternatives Considered

### Alternative 1: Move Django to different port
- **Rejected**: Breaks Django conventions and developer expectations
- Would require retraining all Django developers
- Goes against 20+ years of Django tradition

### Alternative 2: Use reverse port numbers (Kong on 8001)
- **Rejected**: Conflicts with Identity Service
- Would require renumbering all microservices
- Less intuitive than using standard proxy port 8080

### Alternative 3: High port numbers (30000+)
- **Rejected**: Harder to remember
- Some firewalls block high ports
- Unnecessarily complex for local development

## References
- [IANA Port Number Registry](https://www.iana.org/assignments/service-names-port-numbers)
- [Common TCP/UDP Port Numbers](https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers)
- [Kong Default Ports Documentation](https://docs.konghq.com/gateway/latest/reference/configuration/#port-configuration)
- [Django Settings: ALLOWED_HOSTS](https://docs.djangoproject.com/en/5.1/ref/settings/#allowed-hosts)

## Decision Record
- **Date**: 2025-01-11
- **Decided by**: Technical Lead (ag-techlead)
- **Reviewed by**: Services Coordinator (ag-coordinator)
- **Approval**: Immediate implementation required due to blocking issue