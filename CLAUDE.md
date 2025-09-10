# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 📋 **AGENT ARCHITECTURE & ROLES**

### **🏗️ Agent Hierarchy**

This project uses a **specialized agent architecture** where each agent has a specific domain and clear boundaries:

#### **🎯 Service Specialists** (Business Logic Owners)
- **`backend/CLAUDE.md`** - **Django Backend Agent**: Medical records, billing, business logic
- **`frontend/CLAUDE.md`** - **React Frontend Agent**: UI/UX, patient portal, dashboards
- **`services/identity-service/CLAUDE.md`** - **Identity Service Agent**: Authentication, users, MFA, RBAC
- **`services/communication-service/CLAUDE.md`** - **Communication Service Agent**: Notifications, messaging, real-time chat
- **`services/workflow-intelligence-service/CLAUDE.md`** - **Workflow Service Agent**: Process automation, AI workflows
- **`services/content-service/CLAUDE.md`** - **Content Service Agent**: Document management, file storage, search

#### **🤝 Coordination Specialists** (Integration Layer)
- **`services/CLAUDE.md`** - **Services Coordinator Agent**: API contracts, service discovery, Kong gateway
- **`infrastructure/CLAUDE.md`** - **Infrastructure Agent**: Docker, Kubernetes, CI/CD, cloud resources

#### **🔒 Cross-Cutting Specialists** (Quality & Security)
- **Security Agent**: HIPAA compliance, vulnerability scanning, security audits
- **Testing Agent**: Test coverage, quality assurance, CI testing

### **🚫 Agent Boundaries (Strict Separation)**

| **Agent Type** | **Can Modify** | **Cannot Modify** |
|----------------|----------------|-------------------|
| **Service Agents** | Own service code, APIs, models, tests | Other services, infrastructure, coordination |
| **Services Coordinator** | API contracts, service discovery, Kong config | Individual service logic, infrastructure deployment |
| **Infrastructure Agent** | Docker, K8s, CI/CD, cloud resources | Service business logic, API endpoints |
| **Cross-Cutting Agents** | Quality/security configs, global standards | Service implementation, infrastructure |

### **🔄 Agent Collaboration Pattern**

```mermaid
graph TB
    A[Infrastructure Agent] --> B[Services Coordinator]
    B --> C[Identity Service]
    B --> D[Communication Service]
    B --> E[Content Service]  
    B --> F[Workflow Service]
    B --> G[Backend Service]
    B --> H[Frontend Service]
    
    I[Security Agent] -.-> A
    I -.-> B
    I -.-> C
    I -.-> D
    I -.-> E
    I -.-> F
    I -.-> G
    I -.-> H
    
    J[Testing Agent] -.-> A
    J -.-> B
    J -.-> C
    J -.-> D
    J -.-> E
    J -.-> F
    J -.-> G
    J -.-> H
```

### **🎯 Agent Interaction Rules**

#### **Service-to-Service Communication**
- ✅ Services communicate **only through APIs** (managed by Services Coordinator)
- ✅ Use **Services Coordinator** for integration questions
- ❌ **Never directly modify another service's code**

#### **Infrastructure Requests**
- ✅ Service agents request deployment changes from **Infrastructure Agent**
- ✅ **Infrastructure Agent** implements without changing business logic
- ❌ **Service agents cannot modify Docker/K8s configs directly**

#### **Documentation Maintenance**
- ✅ Each agent maintains **its own CLAUDE.md file**
- ✅ Update priorities and completed tasks regularly
- ✅ Services Coordinator maintains **cross-service integration docs**

## 📄 **AGENT DOCUMENTATION FILES**

Each agent has a dedicated CLAUDE.md file with specific instructions:

## 🏥 **PROJECT OVERVIEW**

**ReactDjango Hub Medical** - A modern, secure, and scalable SaaS platform for medical practices with HIPAA/RGPD compliance, built on microservices architecture.

### **🏗️ Microservices Architecture**
| Service | Purpose | Port | Technology | Status |
|---------|---------|------|------------|---------|
| **`identity-service`** | Authentication, users, organizations, MFA | 8001 | FastAPI + PostgreSQL | ✅ **100% Production Ready + Enterprise Testing** |
| **`backend` (Django)** | Business logic, medical records, billing | 8000 | Django + PostgreSQL | 🚧 Integrates with auth-service |
| **`frontend`** | User interface | 3000/5173 | React + Vite + Tailwind | 🔄 Connects to both services |

### **Tech Stack**
- **Authentication Service**: Python 3.13.7 + FastAPI + SQLAlchemy + PostgreSQL 17
- **Business Logic Service**: Python 3.13.7 + Django 5.1.4 LTS + Django Ninja 1.4.3 + PostgreSQL 17  
- **Frontend**: React 18 + Vite + Tailwind CSS
- **Infrastructure**: Docker + Kubernetes
- **Security**: JWT tokens, MFA (email/SMS/TOTP), RBAC, audit trails

### **Key Features**
- **Microservices Architecture**: Separate authentication and business logic services
- **Comprehensive Authentication**: 40 endpoints with MFA, user management, organizations + enterprise testing
- **Multi-tenant Architecture**: Organization isolation managed by auth-service
- **Medical Records Management**: Patient data, HL7/DICOM support in Django service
- **HIPAA/RGPD Compliance**: Full audit logging across all services
- **Real-time Analytics**: Dashboard and reporting via Django service

## 🚀 **DEVELOPMENT WORKFLOW**

### **Local Development Commands**

#### **🔐 Identity Service (Start First)**
```bash
# Identity service - handles authentication, users, organizations  
cd services/identity-service
pip install -r requirements.txt
python main.py                    # Runs on http://localhost:8001
# OR: docker-compose up -d         # Full containerized stack
```

#### **🏥 Backend Service (Django)**
```bash
# Business logic service - requires auth service to be running
cd backend
python -m venv venv
source venv/bin/activate          # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver        # Runs on http://localhost:8000

# Django commands
python manage.py makemigrations
python manage.py migrate
python manage.py shell
python manage.py dbshell
```

#### **⚛️ Frontend (React + Vite)**
```bash
# UI - connects to both auth-service (8001) and backend (8000)
cd frontend
npm install
npm run dev                       # Runs on http://localhost:3000 or 5173
npm run build
npm run preview
npm run lint
npm run type-check
```

#### **🚀 Quick Full Stack Startup**
```bash
# Terminal 1: Identity Service  
cd services/identity-service && python main.py

# Terminal 2: Django Backend  
cd backend && python manage.py runserver

# Terminal 3: Frontend
cd frontend && npm run dev

# ✅ Full stack running:
# - Auth API: http://localhost:8001/docs
# - Backend API: http://localhost:8000/api/docs  
# - Frontend UI: http://localhost:3000
```
```

### **Testing Process**

```bash
# Django backend tests
cd backend
python manage.py test
python manage.py test app_name.tests
python manage.py test app_name.tests.test_file

# React frontend tests
cd frontend
npm test
npm test -- --coverage
npm test -- --watch
```

### **Build and Deployment**

```bash
# Development environment
make dev                    # Start all services with hot reloading
make stop                   # Stop all services  
make migrate               # Run database migrations

# Production environment
make prod-up               # Start production with Nginx + SSL
make prod-down             # Stop production
make migrate-prod          # Run production migrations

# Docker operations
make docker-build          # Build development images
make docker-build-prod     # Build optimized production images
make docker-logs           # View service logs
make docker-health         # Check service health
make clean                 # Clean unused Docker resources

# Direct Docker manager usage
bash docker/docker-manager.sh up development
bash docker/docker-manager.sh build production
bash docker/docker-manager.sh logs development backend
```

## 📁 **PROJECT STRUCTURE**

```
ReactDjango-Hub/
├── backend/                    # Django application
│   ├── apps/                  # Django apps
│   ├── config/                # Django settings
│   ├── docs/                  # Backend documentation
│   ├── tests/                 # Backend tests
│   ├── media/                 # User uploaded files
│   ├── static/                # Static assets
│   └── templates/             # Django templates
├── frontend/                  # React application
│   ├── public/                # Public assets
│   └── src/                   # React source code
│       ├── components/        # React components
│       ├── pages/             # Page components
│       ├── hooks/             # Custom React hooks
│       ├── api/               # API client functions
│       ├── utils/             # Utility functions
│       ├── styles/            # Styling files
│       ├── types/             # TypeScript type definitions
│       └── contexts/          # React contexts
├── infrastructure/            # Infrastructure as code
│   ├── docker/                # Docker configurations
│   ├── kubernetes/            # Kubernetes manifests
│   └── scripts/               # Deployment scripts
├── .github/                   # GitHub workflows
└── docs/                      # Project-wide documentation
```

## 🔧 **DEVELOPMENT GUIDELINES**

### **Django Backend Patterns**
- Use Django REST Framework for API endpoints
- Follow Django naming conventions for models, views, and serializers
- Use database migrations for all schema changes
- Implement proper authentication and authorization
- Ensure RGPD compliance for all patient data handling

### **React Frontend Patterns**
- Use functional components with hooks
- Implement TypeScript for type safety
- Follow component composition patterns
- Use Tailwind CSS for styling
- Implement proper error boundaries and loading states

### **Testing Requirements**
- Unit tests for all business logic
- Integration tests for API endpoints
- End-to-end tests for critical user flows
- Maintain >80% test coverage

### **Agent-Specific Git Workflow**
Each Claude agent has scoped commit permissions to maintain code integrity:

**Backend Agent** (in backend-dev worktree):
```bash
# Use scoped commit command (only commits backend files)
git bcommit "feat: add patient model with RGPD compliance"
```

**Frontend Agent** (in frontend-dev worktree):
```bash
# Use scoped commit command (only commits frontend files)  
git fcommit "feat: add patient dashboard with French UI"
```

**Setup agent git configuration:**
```bash
make claude-git-setup   # Configure git aliases for all agents
make claude-docs-setup  # Create agent-specific documentation structure
```

### **Agent-Specific Documentation**

Each agent maintains its own documentation in addition to global project docs:

```
docs/                     # Global project documentation
├── architecture/         # System architecture 
├── compliance/           # RGPD/HIPAA compliance
└── deployment/           # Infrastructure deployment

backend/docs/             # Backend Agent documentation
├── api/                  # REST API endpoints
├── models/               # Django models & relationships  
├── authentication/       # Auth system & permissions
└── testing/              # Backend testing strategy

frontend/docs/            # Frontend Agent documentation  
├── components/           # React component library
├── styling/              # Design system & themes
├── state-management/     # React state patterns
└── testing/              # Frontend testing strategy
```

## 🚀 **DEPLOYMENT PROCESS**

### **Environment Setup**
```bash
# Production environment variables
DATABASE_URL=postgresql://user:pass@localhost/dbname
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=medicalhub.stephanerichard.com

# Frontend environment
VITE_API_URL=https://medicalhub.stephanerichard.com/api
VITE_ENVIRONMENT=production
```

### **CI/CD Pipeline**
- Automated testing on pull requests
- Security scanning for vulnerabilities
- Automated deployment to staging environment
- Manual approval for production deployment
- Post-deployment health checks

*This is a Django + React full-stack application. Follow Django and React best practices for development.*

## ⚠️ **CRITICAL REMINDERS**

1. **HIPAA Compliance**: All patient data must be handled according to HIPAA requirements
2. **Security First**: Never commit sensitive information to version control
3. **Test Coverage**: Maintain >80% test coverage for both backend and frontend
4. **Documentation**: Update documentation with any architectural changes
5. **Audit Trails**: Ensure all data modifications are logged and traceable
6. **Multi-tenancy**: Maintain strict data isolation between medical practices

## 📚 **DEVELOPMENT RESOURCES**

### **Django Resources**
- Django 5.0 documentation
- Django REST Framework guides
- HIPAA compliance guidelines for Django
- GraphQL integration patterns

### **React Resources**
- React 18 documentation
- Vite configuration guides
- Tailwind CSS documentation
- TypeScript best practices

### **Security Resources**
- HIPAA compliance checklist
- RGPD compliance guidelines
- Security audit procedures
- Penetration testing protocols