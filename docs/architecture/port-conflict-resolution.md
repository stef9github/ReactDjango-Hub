# PORT CONFLICT RESOLUTION - IMMEDIATE ACTION REQUIRED

## Critical Issue
Kong Gateway and Django Backend both configured for port 8000 - BLOCKING deployment

## Architectural Decision: Port 8080 for Kong Gateway

### Why This Decision?
1. **Django stays on 8000**: Industry standard, developer expectation, 20+ years of convention
2. **Kong moves to 8080**: Standard proxy/gateway port, widely recognized alternative HTTP port
3. **Clear separation**: Gateway layer (8080-8089) vs Application layer (8000-8099)

## Immediate Fix Required

### 1. Update services/docker-compose.yml
```yaml
kong:
  image: kong:3.4
  ports:
    - "8080:8000"   # Changed from 8000:8000 - Kong proxy port
    - "8443:8443"   # Kong SSL proxy port (unchanged)
    - "8445:8444"   # Kong admin API port (unchanged)
```

### 2. Update docker-compose.local.yml
Add Kong service configuration (currently missing):
```yaml
# API Gateway - Kong (Port 8080)
kong:
  image: kong:3.4
  container_name: kong
  environment:
    KONG_DATABASE: "off"
    KONG_DECLARATIVE_CONFIG: /kong/kong.yml
    KONG_PROXY_ACCESS_LOG: /dev/stdout
    KONG_ADMIN_ACCESS_LOG: /dev/stdout
    KONG_PROXY_ERROR_LOG: /dev/stderr
    KONG_ADMIN_ERROR_LOG: /dev/stderr
    KONG_ADMIN_LISTEN: "0.0.0.0:8444"
  ports:
    - "8080:8000"   # Kong proxy port (main API gateway)
    - "8443:8443"   # Kong SSL proxy port
    - "8445:8444"   # Kong admin API port
  volumes:
    - ./services/api-gateway/kong.yml:/kong/kong.yml:ro
  depends_on:
    identity-service:
      condition: service_healthy
    backend:
      condition: service_healthy
    communication-service:
      condition: service_healthy
    content-service:
      condition: service_healthy
    workflow-intelligence-service:
      condition: service_healthy
  networks:
    - microservices_network
  healthcheck:
    test: ["CMD", "kong", "health"]
    interval: 30s
    timeout: 10s
    retries: 5
  restart: unless-stopped
```

### 3. Fix Port Inconsistencies
Current docker-compose.local.yml has port mismatches:
- Communication Service: Shows 8002 (should be 8003 per Kong config)
- Content Service: Shows 8003 (should be 8002 per Kong config)

**IMPORTANT**: The Kong configuration is authoritative. Fix docker-compose to match:
- Communication Service: Use port **8003**
- Content Service: Use port **8002**

### 4. Update Kong Health Check
In services/api-gateway/kong.yml, update the health check response:
```yaml
routes:
  - name: kong-health-check
    paths:
      - /health
    plugins:
      - name: request-termination
        config:
          status_code: 200
          body: '{"service":"kong-gateway","status":"healthy","version":"3.4","port":8080}'
```

### 5. Update Frontend Environment
When Kong is deployed, update frontend to use the gateway:
```env
VITE_API_GATEWAY_URL=http://localhost:8080
```

## Final Port Assignments (OFFICIAL)

| Service | Port | Purpose |
|---------|------|---------|
| **Kong Gateway** | 8080 | API Gateway Proxy |
| **Kong Admin** | 8445 | Gateway Admin API |
| **Django Backend** | 8000 | Business Logic Service |
| **Identity Service** | 8001 | Authentication/Users |
| **Content Service** | 8002 | Document Management |
| **Communication Service** | 8003 | Notifications/Messages |
| **Workflow Service** | 8004 | Process Automation |
| **Frontend** | 3000/5173 | React UI |

## Testing After Changes

```bash
# 1. Stop all services
docker-compose -f docker-compose.local.yml down

# 2. Start services with new configuration
docker-compose -f docker-compose.local.yml up -d

# 3. Verify no port conflicts
docker ps  # All containers should be running

# 4. Test each service directly
curl http://localhost:8000/api/health/  # Django
curl http://localhost:8001/health       # Identity
curl http://localhost:8002/health       # Content
curl http://localhost:8003/health       # Communication
curl http://localhost:8004/health       # Workflow
curl http://localhost:8080/health       # Kong Gateway

# 5. Test through gateway
curl http://localhost:8080/api/v1/auth/health
curl http://localhost:8080/api/v1/documents/health
```

## Notes for Coordinator
1. This is the DEFINITIVE architectural decision - implement exactly as specified
2. Kong on 8080 is permanent - update all documentation
3. Django stays on 8000 forever - this is non-negotiable
4. Fix the Communication/Content port swap issue while you're at it
5. See ADR-005 for full architectural rationale

**Status**: APPROVED for immediate implementation