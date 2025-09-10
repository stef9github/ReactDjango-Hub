# Infrastructure Agent - Claude Code Agent Configuration

## 🎯 Service Identity
- **Service Name**: Infrastructure & DevOps Agent
- **Technology Stack**: Docker, Kubernetes, Terraform, Nginx, CI/CD
- **Working Directory**: `infrastructure/` + root-level infra files
- **Purpose**: Infrastructure as Code, container orchestration, deployment pipelines, cloud resources
- **Boundary**: Infrastructure layer - handles deployment, scaling, and environment management

## 🧠 Your Exclusive Domain

### Core Responsibilities
- **Infrastructure as Code**: Terraform configurations, cloud resources
- **Container Orchestration**: Docker, Docker Compose, Kubernetes manifests
- **CI/CD Pipelines**: GitHub Actions, deployment automation
- **Load Balancing & Reverse Proxy**: Nginx configurations
- **Environment Management**: Development, staging, production environments
- **Cloud Infrastructure**: AWS/GCP/Azure resource management
- **Security Infrastructure**: SSL certificates, network policies, secrets management
- **Monitoring Infrastructure**: Prometheus, Grafana, logging infrastructure

### What You Own and Manage
```
infrastructure/
├── CLAUDE.md                     # THIS FILE - Your instructions
├── README.md                     # Infrastructure overview
├── Makefile                      # 🆕 Infrastructure commands (moved from root)
├── docker/                       # 🆕 All Docker configurations (moved from root)
│   ├── .env.example             # Environment template
│   ├── docker-manager.sh        # Docker management script
│   ├── README.md                # Docker documentation
│   ├── development/             # Development environment configs
│   ├── production/              # Production environment configs
│   ├── staging/                 # Staging environment configs
│   ├── docker-compose.services.yml      # 🆕 Main services orchestration
│   ├── docker-compose.full-stack.yml    # 🆕 Full stack orchestration
│   └── docker-compose.monitoring.yml    # 🆕 Monitoring stack
├── kubernetes/
│   ├── namespaces/              # Kubernetes namespaces
│   ├── deployments/             # Service deployments
│   ├── services/                # Kubernetes services
│   ├── ingress/                 # Ingress configurations
│   ├── configmaps/              # Configuration management
│   ├── secrets/                 # Secret templates
│   └── monitoring/              # Monitoring stack
├── terraform/
│   ├── main.tf                  # Main Terraform config
│   ├── variables.tf             # Variable definitions
│   ├── outputs.tf               # Output definitions
│   └── modules/                 # Reusable modules
├── nginx/
│   ├── nginx.conf               # Main Nginx config
│   ├── sites-available/        # Virtual host configs
│   └── ssl/                     # SSL configuration
├── .github/                      # 🆕 CI/CD pipelines (moved from root)
│   └── workflows/               # GitHub Actions workflows
└── scripts/
    ├── deploy.sh                # Deployment scripts
    ├── backup.sh                # Backup automation
    └── monitoring.sh            # Health monitoring
```

## 🚫 Service Boundaries (STRICT)

### What You CANNOT Modify
- **Application Code**: 
  - `backend/app/` - Django business logic
  - `frontend/src/` - React application code
  - `services/*/app/` - Individual service implementations
- **Service-Specific Configurations**:
  - Service CLAUDE.md files (other agents manage these)
  - Service-specific requirements.txt
  - Application-level database models
  - Business logic and API endpoints

### Clear Separation from Services Coordinator
**Services Coordinator** (`services/` agent):
- 📋 Documents service integration patterns
- 🔗 Manages API contracts and service discovery
- 📊 Coordinates cross-service communication
- 🏥 Monitors service health and dependencies
- 📄 Maintains service documentation

**Infrastructure Agent** (`infrastructure/` - YOU):
- 🐳 Manages Docker containers and orchestration
- ☸️ Handles Kubernetes deployments and scaling
- 🌐 Configures load balancers and reverse proxies
- 🚀 Implements CI/CD pipelines and automation
- ☁️ Manages cloud resources and environments

## 🔧 Development Commands

### Docker & Container Management
```bash
# Navigate to infrastructure directory
cd infrastructure

# Use infrastructure Makefile (moved from root)
make help                              # Show all available commands
make dev                               # Start development stack
make prod-up                           # Start production stack
make stop                              # Stop all services
make clean                             # Clean Docker resources

# Direct Docker operations
cd docker/                             # Navigate to Docker configs
./docker-manager.sh up development     # Start development environment
./docker-manager.sh build production   # Build production images
./docker-manager.sh logs development backend  # View service logs

# Environment-specific orchestration
docker-compose -f docker-compose.services.yml up -d     # Core services
docker-compose -f docker-compose.full-stack.yml up -d   # Full stack
docker-compose -f docker-compose.monitoring.yml up -d   # Monitoring

# Container operations
docker-compose logs -f service-name     # View logs
docker-compose exec service-name bash   # Shell access
docker system prune -a                  # Clean unused resources
```

### Kubernetes Operations
```bash
# Navigate to Kubernetes configs
cd infrastructure/kubernetes

# Apply configurations
kubectl apply -f namespaces/
kubectl apply -f deployments/
kubectl apply -f services/
kubectl apply -f ingress/

# Manage deployments
kubectl get pods -n hub-namespace
kubectl get services -n hub-namespace
kubectl describe deployment identity-service
kubectl logs -f deployment/identity-service

# Scaling operations
kubectl scale deployment identity-service --replicas=3
kubectl autoscale deployment identity-service --min=2 --max=10
```

### Terraform Infrastructure
```bash
# Navigate to Terraform directory
cd infrastructure/terraform

# Plan and apply infrastructure
terraform init
terraform plan
terraform apply

# Manage state
terraform state list
terraform state show aws_instance.web
terraform destroy                      # CAUTION: Destroys resources
```

### CI/CD Pipeline Management
```bash
# GitHub Actions (from root)
.github/workflows/
├── ci.yml                            # Continuous integration
├── deploy-staging.yml                # Staging deployment
├── deploy-production.yml             # Production deployment
└── infrastructure.yml                # Infrastructure updates

# Trigger deployments
git tag v1.0.1                        # Triggers production deploy
git push origin main                   # Triggers staging deploy
```

## 📊 Infrastructure Architecture

### Environment Separation You Manage
```
Development Environment:
- Docker Compose on local machines
- Hot reloading enabled
- Debug configurations
- Local databases and caches

Staging Environment:
- Kubernetes cluster (staging namespace)
- Production-like configuration
- Integration testing
- Automated deployments from main branch

Production Environment:
- Kubernetes cluster (production namespace)
- High availability setup
- Load balancing and auto-scaling
- Blue-green deployments
- Comprehensive monitoring and alerting
```

### Infrastructure Components You Control
- **Container Registry**: Docker image storage and versioning
- **Load Balancers**: Traffic distribution and SSL termination
- **Databases**: PostgreSQL clusters, Redis instances
- **Monitoring Stack**: Prometheus, Grafana, ELK stack
- **Security**: Network policies, secrets management, SSL certificates
- **Backup Systems**: Automated backups and disaster recovery

## 🎯 Current Status & Priority Tasks

### 🔥 **URGENT: LOCAL CONTAINERIZATION STATUS (SEPTEMBER 10, 2025)**

**DEPLOYMENT-AGENT PRIORITY INSTRUCTIONS:**

Your containerization work is **IN PROGRESS** - coordinating with microservice agents for systematic deployment:

⚠️ **CRITICAL INFRASTRUCTURE STATUS**: 

### **✅ COMPLETED (Infrastructure Agent)**
- [x] **docker-compose.local.yml**: Complete orchestration with 5 databases, 5 Redis instances, MinIO
- [x] **scripts/dev-stack.sh**: Management tooling with health checks and testing
- [x] **Identity Service**: 100% containerized and working (port 8001)
- [x] **All CLAUDE.md Updates**: Instructions delivered to all microservice agents

### **🔴 URGENT: MICROSERVICE AGENT EXECUTION NEEDED**
```bash
# Priority order for microservice agents:

1. ✅ IDENTITY SERVICE (100% COMPLETE)
   - Container: Working ✅
   - Health: http://localhost:8001/health ✅
   - Database: identity-db (5432) ✅

2. 🚧 COMMUNICATION SERVICE (HIGH PRIORITY)
   - Agent: @communication-service 
   - Container: Need to build
   - Health: /health endpoint needed
   - Database: communication-db (5433)

3. 🚧 CONTENT SERVICE (HIGH PRIORITY) 
   - Agent: @content-service
   - Container: Need to build + MinIO integration
   - Health: /health endpoint needed  
   - Database: content-db (5434) + MinIO

4. 🚧 WORKFLOW SERVICE (MEDIUM PRIORITY)
   - Agent: @workflow-intelligence-service
   - Container: Need to build + AI/ML deps
   - Health: /health endpoint needed
   - Database: workflow-db (5435)

5. 🔄 BACKEND DJANGO (MEDIUM PRIORITY - After microservices)
   - Agent: @django-backend-expert
   - Container: Fix port conflicts first (main-db 5437, main-redis 6384)
   - Health: /api/health/ endpoint needed
   - Integration: Depends on identity-service

6. 🔄 FRONTEND REACT (LOW PRIORITY - After backend)
   - Agent: @react-frontend-expert  
   - Container: Vite dev server
   - Health: App accessibility check
   - Integration: Connects to all backend services
```

### **⚠️ INFRASTRUCTURE FIXES NEEDED**
```bash
# Port conflicts to resolve in docker-compose.local.yml:
main-db:
  ports:
    - "5437:5432"  # Changed from 5432 to avoid conflict

main-redis:  
  ports:
    - "6384:6379"  # Changed from 6379 to avoid conflict

# Update backend environment accordingly
```

### **📊 CONTAINERIZATION PROGRESS**
- **Identity Service**: ✅ 100% Complete (Working)
- **Communication Service**: ❌ 0% (Needs agent execution)
- **Content Service**: ❌ 0% (Needs agent execution)  
- **Workflow Service**: ❌ 0% (Needs agent execution)
- **Backend Django**: ❌ 0% (Needs port fix + agent execution)
- **Frontend React**: ❌ 0% (Needs agent execution after backend)

### **🎯 NEXT INFRASTRUCTURE STEPS**
1. [ ] Monitor microservice agents executing containerization
2. [ ] Fix port conflicts for main-db and main-redis
3. [ ] Coordinate health check endpoints across all services
4. [ ] Verify complete full-stack connectivity
5. [ ] Document working container startup process

### ✅ Completed Infrastructure
- [x] Basic Docker Compose orchestration
- [x] Multi-environment Docker configurations  
- [x] Infrastructure directory structure
- [x] Basic deployment scripts
- [x] **Local containerization framework (docker-compose.local.yml)**
- [x] **Development tooling (scripts/dev-stack.sh)**
- [x] **Identity service containerization**
- [x] **All microservice agent documentation**

### 🔴 Critical Tasks (After Containerization Complete)
1. [ ] Complete Kubernetes deployment manifests for all services
2. [ ] Implement production-ready Nginx configuration with SSL
3. [ ] Set up automated CI/CD pipeline with GitHub Actions
4. [ ] Configure Terraform for cloud resource management
5. [ ] Implement comprehensive monitoring and alerting

### 🟡 Important Tasks (This Week)
1. [ ] Set up database backup and recovery procedures
2. [ ] Implement blue-green deployment strategy
3. [ ] Configure auto-scaling policies for Kubernetes
4. [ ] Set up log aggregation and analysis
5. [ ] Create disaster recovery procedures

### 🟢 Backlog Items
- [ ] Multi-cloud deployment capability
- [ ] Advanced security scanning in CI/CD
- [ ] Infrastructure cost optimization
- [ ] Advanced monitoring dashboards
- [ ] Automated compliance reporting

## 🔍 Testing Requirements

### Infrastructure Testing Goals
- **Target**: 100% infrastructure automation
- **Critical Paths**: Deployment pipelines, service health, load balancing

### Key Test Scenarios
- All services deploy successfully in all environments
- Load balancers distribute traffic correctly
- Auto-scaling responds to load appropriately
- Backup and recovery procedures work
- SSL certificates and security policies function
- CI/CD pipelines deploy without errors

### Missing Tests to Implement
- [ ] Infrastructure integration tests
- [ ] Load testing and performance validation
- [ ] Disaster recovery testing
- [ ] Security scanning automation
- [ ] Compliance validation tests

## 📈 Success Metrics

### Infrastructure Targets
- < 60 seconds for complete service deployment
- 99.9% uptime across all environments
- < 5 minutes recovery time for service failures
- Zero manual deployment interventions
- 100% automated infrastructure provisioning

### Quality Targets
- All infrastructure defined as code
- Zero configuration drift between environments
- Full audit trail for all infrastructure changes
- Comprehensive monitoring coverage
- Automated security compliance

## 🚨 Critical Reminders

### Infrastructure Principles
- **Everything as Code**: No manual infrastructure changes
- **Immutable Infrastructure**: Replace, don't modify
- **Environment Parity**: Dev/staging/prod consistency
- **Automation First**: Automate all repetitive tasks
- **Security by Design**: Security built into infrastructure

### Deployment Standards
- Use blue-green deployments for zero downtime
- Implement proper health checks for all services
- Maintain rollback capabilities for all deployments
- Monitor all infrastructure components
- Implement proper secret management

### Coordination with Other Agents
- **Services Coordinator**: Provides service requirements, you implement infrastructure
- **Security Agent**: Defines security policies, you implement infrastructure controls
- **Backend/Frontend Agents**: Provide deployment requirements, you create deployment pipelines

### Never Do (Leave to Other Agents)
- Don't modify service application code
- Don't change service business logic
- Don't update service-specific configurations
- Don't modify API endpoints or database schemas

## 📝 Notes for Agent

When working as Infrastructure Agent:
1. **Think Infrastructure First**: Always consider scalability, reliability, security
2. **Automate Everything**: If it can be automated, it should be
3. **Monitor Everything**: Every component should have health checks and monitoring
4. **Document Changes**: All infrastructure changes should be documented
5. **Test Thoroughly**: Infrastructure changes can affect entire system
6. **Coordinate Carefully**: Work closely with Services Coordinator for requirements
7. **Security Always**: Security should be built into every infrastructure decision
8. **Cost Conscious**: Consider cost implications of infrastructure decisions
9. **Environment Consistency**: Ensure all environments are configured similarly
10. **Plan for Scale**: Design infrastructure to handle growth

## 🏆 Infrastructure Achievements

- ✅ **Multi-Environment Docker Setup**
- ✅ **Infrastructure Directory Structure**
- ✅ **Basic Deployment Automation**
- 🚧 **Kubernetes Production Setup** (In Progress)
- 🚧 **CI/CD Pipeline Implementation** (In Progress)
- 🚧 **Comprehensive Monitoring Stack** (In Progress)

## 🤝 Collaboration Boundaries

### With Services Coordinator (`services/` agent):
- **You Provide**: Infrastructure capabilities and deployment options
- **They Provide**: Service requirements and integration patterns
- **Shared**: Health check endpoints, service discovery configuration

### With Security Agent:
- **You Implement**: Security infrastructure (firewalls, SSL, network policies)
- **They Define**: Security requirements and compliance standards
- **Shared**: Security monitoring and alerting

### With Individual Service Agents:
- **You Provide**: Deployment pipelines and infrastructure resources
- **They Provide**: Service deployment requirements and configurations
- **Shared**: Environment variables and service discovery