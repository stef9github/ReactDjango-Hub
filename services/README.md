# ReactDjango Hub - Microservices Architecture

## 🏗️ **Services Overview**

| Service | Purpose | Port | Technology | Status |
|---------|---------|------|------------|---------|
| **🔐 Identity Service** | Auth + Users + Roles + MFA | 8001 | FastAPI + PostgreSQL + Redis | ✅ **Production Ready** |
| **📄 Content Service** | Documents + Search + Audit | 8002 | FastAPI + PostgreSQL + Redis | ✅ **Framework Complete** |
| **📢 Communication Service** | Notifications + Messaging | 8003 | FastAPI + Celery + Redis | ✅ **Framework Complete** |
| **🔄 Workflow & Intelligence Service** | Process Automation + AI | 8004 | FastAPI + AI/ML + Redis | ✅ **Framework Complete** |

## 🚀 **Quick Start**

### ⭐ **Centralized Service Orchestration** (RECOMMENDED)
```bash
cd services

# Start all services with automatic conflict resolution
./scripts/start-all-services.sh     # Handles cleanup & startup automatically

# Check service health
./scripts/health-check-all.sh

# Stop all services gracefully  
./scripts/stop-all-services.sh

# Complete cleanup (removes all containers and volumes)
./scripts/cleanup-services.sh       # Use when you need a fresh start
```

### Manual Docker Compose
```bash
cd services
docker-compose up -d
```

### Individual Service Development
```bash
# Identity Service (Auth + Users + Roles) - PRODUCTION READY
cd services/identity-service
python main.py  # or uvicorn main:app --reload --port 8001

# Content Service (Documents + Search) - FRAMEWORK COMPLETE
cd services/content-service  
python main.py  # or uvicorn main:app --reload --port 8002

# Communication Service (Notifications + Messaging) - FRAMEWORK COMPLETE
cd services/communication-service
python main.py  # or uvicorn main:app --reload --port 8003

# Workflow Service (Process Automation + AI) - FRAMEWORK COMPLETE
cd services/workflow-intelligence-service
python main.py  # or uvicorn main:app --reload --port 8004
```

## 📡 **API Documentation & Endpoints**

### 🚪 **API Gateway (Kong) - Primary Access Point**
- **Kong Proxy**: http://localhost:8000 (routes to all services)
- **Kong Admin API**: http://localhost:8445

### 📖 **Service Documentation**
When services are running, access interactive API docs:

- **Identity Service**: http://localhost:8001/docs ✅ **Production Ready**
- **Content Service**: http://localhost:8002/docs ✅ **Framework Complete**  
- **Communication Service**: http://localhost:8003/docs ✅ **Framework Complete**
- **Workflow Service**: http://localhost:8004/docs ✅ **Framework Complete**

## 🗃️ **Database Configuration**

Each service has its own isolated database:

| Service | Database | Port | User | Password |
|---------|----------|------|------|----------|
| Identity | `identity_service` | 5433 | `identity_user` | `identity_pass` |
| Content | `content_service` | 5434 | `content_user` | `content_pass` |
| Communication | `communication_service` | 5435 | `communication_user` | `communication_pass` |
| Workflow | `workflow_intelligence_service` | 5436 | `workflow_user` | `workflow_pass` |

## 🔄 **Redis Configuration**

Each service has dedicated Redis instances:

| Service | Redis Port | Usage |
|---------|------------|-------|
| Identity | 6380 | Caching + Rate Limiting |
| Content | 6381 | Search Cache + Processing |
| Communication | 6382 | Celery Broker + Message Queue |
| Workflow | 6383 | Pub/Sub + AI Job Queue |

## 👥 **Service Integration**

### Authentication Flow
1. **Frontend** → **Identity Service** (login, get JWT)
2. **Other Services** → **Identity Service** (validate JWT)

### Service Communication Architecture
```mermaid
graph TD
    Frontend[Frontend React App]
    Gateway[API Gateway - Kong]
    Identity[🔐 Identity Service :8001<br/>✅ PRODUCTION READY]
    Content[📄 Content Service :8002<br/>✅ FRAMEWORK COMPLETE]
    Comm[📢 Communication Service :8003<br/>✅ FRAMEWORK COMPLETE]
    Workflow[🔄 Workflow Intelligence :8004<br/>✅ FRAMEWORK COMPLETE]
    
    Frontend --> Gateway
    Gateway --> Identity
    Gateway --> Content
    Gateway --> Comm  
    Gateway --> Workflow
    
    Content -.-> Identity
    Comm -.-> Identity
    Workflow -.-> Identity
    Workflow -.-> Content
    Workflow -.-> Comm
    
    Identity --> IdentityDB[(PostgreSQL<br/>Port 5433)]
    Content --> ContentDB[(PostgreSQL<br/>Port 5434)]
    Comm --> CommDB[(PostgreSQL<br/>Port 5435)]
    Workflow --> WorkflowDB[(PostgreSQL<br/>Port 5436)]
    
    Identity --> IdentityRedis[(Redis<br/>Port 6380)]
    Content --> ContentRedis[(Redis<br/>Port 6381)]
    Comm --> CommRedis[(Redis<br/>Port 6382)]
    Workflow --> WorkflowRedis[(Redis<br/>Port 6383)]
```

## 📦 **Requirements Management**

### Shared Dependencies Strategy
All services use a shared requirements baseline to ensure consistency:

```bash
# Shared requirements file (maintained by Services Coordinator)
services/requirements.shared.txt

# Each service extends the shared requirements:
# In your service requirements.txt:
-r ../requirements.shared.txt

# Add SERVICE-SPECIFIC dependencies below:
# Database driver (choose one):
asyncpg==0.29.0          # For async services (identity-service)
# psycopg2-binary==2.9.9 # For sync services (other services)

# Other service-specific dependencies...
```

### ⚠️ **Important**: Database Drivers are Service-Specific
Database drivers are **NOT** in shared requirements due to compilation conflicts:
- **Identity Service**: Uses `asyncpg==0.29.0` (async PostgreSQL)
- **Other Services**: Use `psycopg2-binary==2.9.9` (sync PostgreSQL)

### Current Dependency Versions (Latest Stable - Sep 2025)
- **FastAPI**: 0.116.1
- **Pydantic**: 2.11.7  
- **SQLAlchemy**: 2.0.43
- **Redis**: 6.4.0
- **pytest**: 8.3.4

See [`requirements.shared.txt`](./requirements.shared.txt) for the complete list.

## 🎯 **Development Workflow**

### 🔧 **Centralized Service Management**
```bash
# From services/ directory - manage all services together:
cd services

# Start everything with automatic conflict resolution & health checks
./scripts/start-all-services.sh    # Automatically stops conflicting standalone services

# Monitor all services
./scripts/health-check-all.sh

# View logs for specific service
docker-compose logs -f identity-service

# Scale a specific service  
docker-compose up -d --scale communication-service=3

# Stop everything gracefully
./scripts/stop-all-services.sh

# Complete cleanup when needed
./scripts/cleanup-services.sh      # Removes all containers, volumes, and networks
```

### 🛠️ **Service Management Patterns & Conflict Resolution**

#### **Two Service Deployment Patterns**
1. **🐳 Coordinated Docker Stack** (Recommended for integration testing)
   - All services run in Docker containers with shared networking
   - Managed via `docker-compose` with centralized configuration
   - Best for testing service-to-service communication

2. **⚡ Standalone Development** (Recommended for individual service development)
   - Services run directly via `python main.py` with local virtual environments
   - Each service has `setup-dev-env.sh` and `requirements-standalone.txt`
   - Faster development cycle with instant reloading

#### **⚠️ Conflict Prevention & Resolution**

**Common Conflict Scenario:**
```bash
# If a standalone Communication Service is running:
python main.py  # (running on port 8003)

# And you try to start the coordinated stack:
docker-compose up -d  # ❌ Will fail - port 8003 already in use
```

**Automatic Cleanup Features:**
- **✅ Standalone Service Detection**: Stops Python processes on ports 8001-8004 that conflict with Docker stack
- **✅ Port Conflict Resolution**: Automatically frees up service ports from standalone containers  
- **✅ Container Name Conflicts**: Removes containers with conflicting names
- **✅ Volume Cleanup**: Cleans up orphaned volumes to prevent data conflicts
- **✅ Network Management**: Recreates service networks with proper configuration

**Service Management Commands:**
```bash
# Enhanced cleanup that handles both Docker AND standalone services:
./scripts/cleanup-services.sh      # Stops Python processes + removes containers

# Enhanced stop that handles both deployment patterns:
./scripts/stop-all-services.sh     # Gracefully stops Docker + standalone services

# Start with automatic conflict resolution:
./scripts/start-all-services.sh    # Auto-detects and stops conflicting services
```

**Manual Troubleshooting:**
```bash
# Check what's running on service ports:
lsof -i :8001  # Identity Service
lsof -i :8002  # Content Service  
lsof -i :8003  # Communication Service
lsof -i :8004  # Workflow Service

# Stop specific standalone service:
kill $(lsof -t -i:8003)  # Stop Communication Service on port 8003

# Debug Docker conflicts:
docker ps -a                       # See all containers
docker-compose down --remove-orphans  # Clean up orphaned containers
```

**Recommended Development Workflow:**
```bash
# Option A: Individual Service Development (fastest iteration)
cd services/communication-service
./setup-dev-env.sh      # Set up virtual environment
source venv/bin/activate
python main.py          # Run standalone on port 8003

# Option B: Full Integration Testing (most realistic)
cd services
./scripts/start-all-services.sh    # Auto-stops standalone, starts Docker stack
./scripts/health-check-all.sh      # Verify all services are healthy
```

### 🌐 **API Gateway Coordination**
All frontend requests should route through Kong API Gateway at `http://localhost:8000`:

```javascript
// Frontend API calls should use gateway endpoints:
const API_BASE = 'http://localhost:8000/api/v1';

// Authentication
fetch(`${API_BASE}/auth/login`, { ... });

// Documents  
fetch(`${API_BASE}/documents`, { ... });

// Notifications
fetch(`${API_BASE}/notifications`, { ... });

// Workflows
fetch(`${API_BASE}/workflows`, { ... });
```

### 🤖 **Using Specialized Agents**
Each service has a dedicated Claude Code agent in `.claude/agents/`:

- `identity-service-agent.md` - Auth + Users + Roles specialist
- `content-service-agent.md` - Documents + Search specialist  
- `communication-service-agent.md` - Notifications + Messaging specialist
- `workflow-intelligence-service-agent.md` - Process Automation + AI specialist

### Service-Specific Development
```bash
# Work on individual services (for service-specific agents)
cd services/identity-service
claude  # Uses identity-service-agent

# Work on content service  
cd services/content-service
claude  # Uses content-service-agent
```

## 📋 **Multi-Domain Applications**

### **PublicHub Context**
- **Identity**: Supplier accounts, procurement roles
- **Content**: RC, CCAP, CCTP documents, offers
- **Communication**: Bid notifications, supplier alerts
- **Workflow**: Consultation lifecycle automation

### **Medical Context**
- **Identity**: Doctor/patient accounts, medical roles
- **Content**: Medical documents, patient records  
- **Communication**: Patient reminders, clinical messaging
- **Workflow**: Patient care pathway automation

## 🔄 **Service Coordination Features**

### ✅ **Health Monitoring**
- Comprehensive health checks for all services, databases, and Redis
- Dependency-aware startup sequence
- Graceful shutdown with proper cleanup
- Real-time service status monitoring

### 🔗 **Service Discovery**
- Kong API Gateway manages all service routing
- Proper service-to-service communication patterns
- Load balancing and failover support
- API versioning and backward compatibility

### 🏗️ **Infrastructure Coordination**
- Unified Docker Compose orchestration
- Shared environment configuration
- Centralized logging and monitoring
- Database and Redis instance management

---

## 📚 **Documentation**

### **Architecture & Technical Details**
- **[Architecture Overview](docs/ARCHITECTURE.md)** - Detailed technical architecture, deployment patterns, and service communication
- **[Service Integration Patterns](docs/SERVICE_INTEGRATION_PATTERNS.md)** - Standard patterns for implementing services
- **[API Integration Guide](docs/API_INTEGRATION_GUIDE.md)** - Cross-service API usage and authentication
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### **Coordination & Management**
- **[Coordination Issues](COORDINATION_ISSUES.md)** - Cross-service issue tracking and resolution
- **[Shared Requirements](requirements.shared.txt)** - Centralized dependency management

### **Service-Specific Documentation**
Each service maintains its own detailed documentation in its respective directory.

---

**🤖 Each service is designed to be domain-agnostic with specialized configurations for different applications.**