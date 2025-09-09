# Medical SaaS Microservices Architecture

## 🎯 **Architecture Principles**

This document provides the **technical architecture overview** for ReactDjango Hub's medical practice management platform.

### **Design Principles**
- **Domain-Driven Design**: Services organized around medical practice domains
- **Database-per-Service**: Complete data isolation with PostgreSQL + Redis per service  
- **API-First**: All services expose REST APIs with OpenAPI documentation
- **Consistent Technology Stack**: FastAPI + Python for maintainability and team efficiency
- **JWT-based Security**: Centralized authentication with distributed authorization
- **Shared Infrastructure**: Coordinated dependency management and deployment patterns

## 🏗️ **Current Architecture Diagram**

```
┌──────────────────────────────────────────────────────────────┐
│                    Medical Practice Frontend                 │
│              (React + Vite + Tailwind CSS)                 │
└────────────────────────┬─────────────────────────────────────┘
                         │ HTTPS/WebSocket
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                      API Gateway                             │
│                        (Kong)                               │
│        • JWT Validation • Rate Limiting • CORS              │
└────┬─────────────┬─────────────┬─────────────┬──────────────┘
     │             │             │             │
     ▼             ▼             ▼             ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│Identity  │ │ Content  │ │  Comm.   │ │Workflow  │
│ Service  │ │ Service  │ │ Service  │ │Intel.Svc │
│Port: 8001│ │Port: 8002│ │Port: 8003│ │Port: 8004│
│✅ READY  │ │🔄 PLANNED│ │🔄 PLANNED│ │🔄 PLANNED│
└─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘
      │            │            │            │
      ▼            ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│Identity  │ │ Content  │ │  Comm.   │ │Workflow  │
│Database  │ │Database  │ │Database  │ │Database  │
│PostgreSQL│ │PostgreSQL│ │PostgreSQL│ │PostgreSQL│
│Port: 5433│ │Port: 5434│ │Port: 5435│ │Port: 5436│
└──────────┘ └──────────┘ └──────────┘ └──────────┘
      │            │            │            │
      ▼            ▼            ▼            ▼
┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│Identity  │ │ Content  │ │  Comm.   │ │Workflow  │
│  Redis   │ │  Redis   │ │  Redis   │ │  Redis   │
│Port: 6380│ │Port: 6381│ │Port: 6382│ │Port: 6383│
└──────────┘ └──────────┘ └──────────┘ └──────────┘

════════════════════════════════════════════════════════════
         Service Coordination & Shared Infrastructure
════════════════════════════════════════════════════════════
                              │
        ┌─────────────────────┴─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Docker     │    │Requirements  │    │  Claude      │
│  Compose     │    │Coordination  │    │   Agents     │
│Orchestration │    │   System     │    │ Specialized  │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 📦 **Service Breakdown**

### **1. 🔐 Identity Service (Port 8001)** ✅ **IMPLEMENTED**
```python
# Complete authentication & authorization service
- Technology: Python 3.13.7 + FastAPI 0.116.1
- Database: PostgreSQL 17 (port 5433) + Redis (port 6380)
- Database Driver: asyncpg (async PostgreSQL)
- Status: ✅ Production Ready with 30+ endpoints
- Responsibilities:
  • User authentication (JWT + MFA)
  • Organization management (multi-tenant)
  • Role-based access control (RBAC)
  • User profiles and preferences
  • Email verification workflows
  • Security audit trails
  • Token refresh and session management
```

### **2. 📄 Content Service (Port 8002)** 🔄 **PLANNED**
```python
# Document management and search service
- Technology: Python + FastAPI
- Database: PostgreSQL (port 5434) + Redis (port 6381)
- Database Driver: psycopg2-binary (sync PostgreSQL)
- Status: 🔄 Not Implemented
- Planned Responsibilities:
  • Medical document storage (HL7/DICOM)
  • Full-text search capabilities
  • Document version control
  • Compliance audit trails
  • File processing (PDF, images, etc.)
  • Document sharing and permissions
```

### **3. 📢 Communication Service (Port 8003)** 🔄 **PLANNED**
```python
# Notifications and messaging service
- Technology: Python + FastAPI + Celery
- Database: PostgreSQL (port 5435) + Redis (port 6382)
- Database Driver: psycopg2-binary (sync PostgreSQL)
- Status: 🔄 Not Implemented
- Planned Responsibilities:
  • Email notifications (SendGrid, Mailgun)
  • SMS messaging (Twilio, OVH)
  • Push notifications (Firebase)
  • In-app messaging system
  • Notification templates and scheduling
  • Communication preferences management
```

### **4. 🔄 Workflow Intelligence Service (Port 8004)** 🔄 **PLANNED**
```python
# Process automation and AI service
- Technology: Python + FastAPI + AI/ML libraries
- Database: PostgreSQL (port 5436) + Redis (port 6383)
- Database Driver: psycopg2-binary (sync PostgreSQL)
- Status: 🔄 Not Implemented
- Planned Responsibilities:
  • Medical workflow automation
  • AI-powered patient care pathways
  • Decision support systems
  • Process optimization analytics
  • Integration with OpenAI/Anthropic APIs
  • Medical protocol compliance checking
```

## 🔄 **Inter-Service Communication Patterns**

### **Synchronous Communication (HTTP/REST)**
All services communicate via HTTP REST APIs with JWT token validation:

```python
# Standard service-to-service communication pattern
import httpx
import os

IDENTITY_SERVICE_URL = os.getenv("IDENTITY_SERVICE_URL", "http://identity-service:8001")

async def validate_user_permissions(user_id: str, token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{IDENTITY_SERVICE_URL}/auth/validate",
            headers={"Authorization": f"Bearer {token}"},
            json={"user_id": user_id}
        )
        response.raise_for_status()
        return response.json()

# Usage in service endpoints
@app.get("/api/content/documents")
async def get_user_documents(user_id: str = Depends(get_current_user)):
    # Validate permissions with identity service
    user_info = await validate_user_permissions(user_id, request.token)
    
    if "documents:read" not in user_info["permissions"]:
        raise HTTPException(403, "Insufficient permissions")
    
    return await document_service.get_user_documents(user_id)
```

### **Service Discovery Pattern**
Services use environment-based discovery with health checks:

```python
# Service registration and discovery
SERVICE_REGISTRY = {
    "identity-service": {"url": os.getenv("IDENTITY_SERVICE_URL"), "port": 8001},
    "content-service": {"url": os.getenv("CONTENT_SERVICE_URL"), "port": 8002},
    "communication-service": {"url": os.getenv("COMMUNICATION_SERVICE_URL"), "port": 8003},
    "workflow-service": {"url": os.getenv("WORKFLOW_SERVICE_URL"), "port": 8004}
}

async def health_check_service(service_name: str) -> bool:
    service_config = SERVICE_REGISTRY.get(service_name)
    if not service_config:
        return False
        
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{service_config['url']}/health", timeout=5.0)
            return response.status_code == 200
        except:
            return False
```

## 🚀 **Deployment Architecture**

### **Current Infrastructure Setup**

#### **Development Environment**
```yaml
# docker-compose.yml - Current setup
services:
  # Identity Service - IMPLEMENTED
  identity-service:
    build: ./identity-service
    ports: ["8001:8001"]
    depends_on: [identity-db, identity-redis]
    environment:
      DATABASE_URL: postgresql+asyncpg://identity_user:identity_pass@identity-db:5432/identity_service
      REDIS_URL: redis://identity-redis:6379/0
    
  identity-db:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: identity_service
      POSTGRES_USER: identity_user
      POSTGRES_PASSWORD: identity_pass
    ports: ["5433:5432"]
    
  identity-redis:
    image: redis:7-alpine
    ports: ["6380:6379"]

  # Future services follow same pattern (commented out until implemented)
  # content-service, communication-service, workflow-intelligence-service
```

#### **Production Environment (Kubernetes)**
```yaml
# Kubernetes deployment pattern (when implemented)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: identity-service
spec:
  replicas: 2  # Scale based on load
  selector:
    matchLabels:
      app: identity-service
  template:
    metadata:
      labels:
        app: identity-service
    spec:
      containers:
      - name: identity-service
        image: identity-service:latest
        ports:
        - containerPort: 8001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: identity-db-secret
              key: url
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
```

## 🔐 **Security Between Services**

### **Service-to-Service Authentication**
```python
# mTLS for service communication
@app.before_request
async def verify_service_identity():
    cert = request.headers.get("X-Client-Cert")
    if not verify_service_certificate(cert):
        raise Unauthorized("Invalid service certificate")
```

### **API Gateway Token Validation**
```python
# Gateway validates token once, passes user context
@app.post("/api/billing/invoice")
async def create_invoice(request):
    # User already authenticated by gateway
    user_id = request.headers.get("X-User-ID")
    tenant_id = request.headers.get("X-Tenant-ID")
    permissions = request.headers.get("X-Permissions").split(",")
```

## 📊 **Data Consistency**

### **Saga Pattern for Distributed Transactions**
```python
class CreateOrderSaga:
    async def execute(self, order_data):
        # Step 1: Reserve inventory
        inventory_reserved = await core_service.reserve_inventory(
            order_data["items"]
        )
        
        # Step 2: Process payment
        try:
            payment_processed = await billing_service.process_payment(
                order_data["payment"]
            )
        except PaymentFailed:
            # Compensate: Release inventory
            await core_service.release_inventory(inventory_reserved)
            raise
        
        # Step 3: Create order
        order = await core_service.create_order(order_data)
        
        return order
```

## 🔄 **Service Discovery**

### **Consul Registration**
```python
# Each service registers itself
async def register_with_consul():
    await consul_client.agent.service.register(
        name="auth-service",
        service_id=f"auth-{instance_id}",
        address=SERVICE_HOST,
        port=SERVICE_PORT,
        check=Check.http(f"http://{SERVICE_HOST}:{SERVICE_PORT}/health")
    )
```

### **Client-Side Discovery**
```python
# Services discover each other
async def get_service_url(service_name: str):
    services = await consul_client.health.service(service_name, passing=True)
    if services:
        service = random.choice(services)
        return f"http://{service['Service']['Address']}:{service['Service']['Port']}"
    raise ServiceNotFound(service_name)
```

## 🎯 **Benefits of This Architecture**

1. **Independent Scaling**
   - Scale auth service during login spikes
   - Scale analytics during report generation
   - Scale billing during payment processing

2. **Technology Freedom**
   - Use Go for high-performance analytics
   - Use Java for enterprise billing
   - Use Python for rapid development

3. **Fault Isolation**
   - Billing service failure doesn't affect auth
   - Analytics outage doesn't block core operations

4. **Independent Deployment**
   - Deploy auth service updates without touching billing
   - A/B test new analytics features independently

5. **Team Autonomy**
   - Auth team owns their service completely
   - Billing team can choose their tech stack
   - Analytics team deploys on their schedule

## 🤖 **Development Coordination with Claude Code Agents**

### **Specialized Agent Architecture**
Each service domain has a dedicated Claude Code agent for focused development:

```bash
# Service-specific agents (in .claude/agents/)
identity-service-agent.md          # Authentication & user management
content-service-agent.md           # Document management & search  
communication-service-agent.md     # Notifications & messaging
workflow-intelligence-service-agent.md  # Process automation & AI
services-coordinator-agent.md      # Cross-service coordination (this agent)
```

### **Coordination Patterns**
- **Services Coordinator Agent**: Manages shared requirements, documentation, Docker orchestration
- **Service Agents**: Focus on domain-specific implementation within integration patterns
- **Issue Escalation**: Service agents report cross-service issues via `COORDINATION_ISSUES.md`
- **Standards Enforcement**: Automated validation via `scripts/validate-coordination.sh`

### **Development Workflow**
```bash
# Start with coordinator for infrastructure
cd services/
claude  # Uses services-coordinator-agent.md

# Then work on specific services
cd identity-service/
claude  # Uses identity-service-agent.md
```

## 🎯 **Architecture Benefits**

This microservices architecture provides:

### **🔄 Independent Scaling**
- Scale identity service during authentication spikes
- Scale content service during document processing peaks  
- Scale communication service during notification bursts
- Scale workflow service during AI processing loads

### **🛡️ Fault Isolation**
- Content service failures don't affect authentication
- Communication service outages don't block document access
- Identity service remains available for critical auth operations

### **👥 Team Autonomy**
- Identity team owns authentication completely
- Content team controls document management
- Communication team manages all messaging
- Workflow team develops AI and automation features

### **🚀 Independent Deployment**
- Deploy identity service updates without affecting other services
- A/B test communication features independently
- Roll out AI improvements in workflow service separately

---

This architecture balances **microservices independence** with **coordination efficiency**, using consistent patterns and centralized coordination to prevent common pitfalls while maintaining service autonomy.