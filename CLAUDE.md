# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🎯 **LOCAL-FIRST DEVELOPMENT STRATEGY**

**Important**: This project follows a **local-first development strategy** (see ADR-010) to maximize development velocity with Claude Code and other AI-assisted development tools. All services run directly on the host machine without containerization during development. Containerization is reserved for future production deployment when the platform reaches maturity.

## 📋 **SIMPLIFIED AGENT ARCHITECTURE**

### **🚀 Streamlined Agent System**

This project uses a **simplified agent architecture** with one agent per service/domain, accessible through a unified launcher:

```bash
# Launch any agent with:
./.claude/launch-agent.sh <agent-name>

# Examples:
./.claude/launch-agent.sh backend      # Django backend development
./.claude/launch-agent.sh frontend     # React frontend development
./.claude/launch-agent.sh identity     # Identity service
./.claude/launch-agent.sh techlead     # Technical leadership and architecture
```

### **📦 Available Agents**

#### **Core Service Agents** (One per microservice)
- **`backend`** - Django Backend: Core business logic, data models, REST APIs
- **`frontend`** - React Frontend: User interface, components, state management
- **`identity`** - Identity Service: Authentication, users, MFA, RBAC
- **`communication`** - Communication Service: Notifications, messaging, real-time
- **`content`** - Content Service: Document management, file storage
- **`workflow`** - Workflow Intelligence: Process automation, AI workflows

#### **Infrastructure & Coordination**
- **`infrastructure`** - Infrastructure: Future production deployment (currently deferred per ADR-010)
- **`coordinator`** - Services Coordinator: Service integration, API contracts

#### **Leadership & Quality**
- **`techlead`** - Technical Lead: Architecture decisions, research analysis, strategic planning
- **`security`** - Security & Compliance: Audits, vulnerability scanning
- **`review`** - Code Review: Quality assessment, best practices

### **🚫 Agent Boundaries (Strict Separation)**

| **Agent Type** | **Can Modify** | **Cannot Modify** |
|----------------|----------------|-------------------|
| **Service Agents** | Own service code, APIs, models, tests | Other services, infrastructure, coordination |
| **Services Coordinator** | API contracts, service integration patterns | Individual service logic, infrastructure |
| **Infrastructure Agent** | Setup scripts, future deployment planning | Service business logic, API endpoints |
| **Cross-Cutting Agents** | Quality/security configs, global standards | Service implementation, infrastructure |

### **🔄 Simplified Agent Workflow**

```mermaid
graph LR
    A[Infrastructure] --> B[Coordinator]
    B --> C[Services]
    C --> D[Backend]
    C --> E[Frontend]
    C --> F[Identity]
    C --> G[Communication]
    C --> H[Content]
    C --> I[Workflow]
    
    J[Security/Review] -.-> A
    J -.-> B
    J -.-> C
```

### **🎯 Agent Interaction Rules**

#### **Service-to-Service Communication**
- ✅ Services communicate **only through APIs** (managed by Services Coordinator)
- ✅ Use **Services Coordinator** for integration questions
- ❌ **Never directly modify another service's code**

#### **Infrastructure Requests**
- ✅ Service agents request deployment changes from **Deployment Agent**
- ✅ **Deployment Agent** implements without changing business logic
- ❌ **Service agents cannot modify Docker/K8s configs directly**

#### **Documentation Maintenance**
- ✅ Each agent maintains **its own CLAUDE.md file**
- ✅ Update priorities and completed tasks regularly
- ✅ Services Coordinator maintains **cross-service integration docs**

## 📄 **AGENT CONFIGURATION**

All agents are configured in `.claude/agents.yaml` with standardized definitions:

## 🚀 **PROJECT OVERVIEW**

**ReactDjango Hub** - A modern, secure, and scalable enterprise SaaS platform with compliance capabilities, built on microservices architecture.

### **🏗️ Microservices Architecture**
| Service | Purpose | Port | Technology | Status |
|---------|---------|------|------------|---------|
| **`identity-service`** | Authentication, users, organizations, MFA | 8001 | FastAPI + PostgreSQL | ✅ **100% Production Ready + Enterprise Testing** |
| **`backend` (Django)** | Core business logic, data models, APIs | 8000 | Django + PostgreSQL | 🚧 Integrates with auth-service |
| **`frontend`** | User interface | 3000/5173 | React + Vite + Tailwind | 🔄 Connects to both services |

### **Tech Stack**
- **Authentication Service**: Python 3.13.7 + FastAPI + SQLAlchemy + PostgreSQL 17
- **Business Logic Service**: Python 3.13.7 + Django 5.1.4 LTS + Django Ninja 1.4.3 + PostgreSQL 17  
- **Frontend**: React 18 + Vite + Tailwind CSS
- **Development**: Local-first approach for maximum velocity
- **Security**: JWT tokens, MFA (email/SMS/TOTP), RBAC, audit trails

### **Key Features**
- **Microservices Architecture**: Separate authentication and business logic services
- **Comprehensive Authentication**: 40 endpoints with MFA, user management, organizations + enterprise testing
- **Multi-tenant Architecture**: Organization isolation managed by auth-service
- **Data Management**: Structured data models with versioning and audit trails
- **Compliance Ready**: Full audit logging and data governance across all services
- **Real-time Analytics**: Dashboard and reporting via Django service

## 🚀 **DEVELOPMENT WORKFLOW**

### **Local Development Commands**

#### **🔐 Identity Service (Start First)**
```bash
# Identity service - handles authentication, users, organizations  
cd services/identity-service
python -m venv venv               # Create virtual environment (first time only)
source venv/bin/activate          # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py                    # Runs on http://localhost:8001
```

#### **⚙️ Backend Service (Django)**
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

### **Local Development Setup**

```bash
# One-time setup: Install PostgreSQL locally
# macOS: brew install postgresql@17
# Ubuntu: sudo apt install postgresql-17
# Windows: Download from postgresql.org

# Create databases for each service
createdb identity_service_db
createdb django_backend_db
createdb communication_service_db
createdb content_service_db
createdb workflow_service_db

# Development commands
make dev                    # Start all services locally
make stop                   # Stop all services  
make migrate               # Run database migrations
make test                  # Run all tests
make lint                  # Run linting checks
```

### **Future Production Deployment**

```bash
# Note: Containerization will be considered for production
# deployment when the platform reaches maturity.
# For now, focus on local development for maximum velocity.
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
├── infrastructure/            # Infrastructure (future use)
│   ├── docker/                # Docker configs (production only)
│   ├── kubernetes/            # K8s manifests (future)
│   └── scripts/               # Setup and utility scripts
├── .github/                   # GitHub workflows
└── docs/                      # Project-wide documentation
```

## 🔧 **DEVELOPMENT GUIDELINES**

### **Django Backend Patterns**
- Use Django REST Framework for API endpoints
- Follow Django naming conventions for models, views, and serializers
- Use database migrations for all schema changes
- Implement proper authentication and authorization
- Ensure data privacy compliance for all sensitive data handling

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
git bcommit "feat: add user model with data compliance"
```

**Frontend Agent** (in frontend-dev worktree):
```bash
# Use scoped commit command (only commits frontend files)  
git fcommit "feat: add user dashboard with internationalization"
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
├── compliance/           # Data privacy and regulatory compliance
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
ALLOWED_HOSTS=hub.stephanerichard.com

# Frontend environment
VITE_API_URL=https://hub.stephanerichard.com/api
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

1. **Data Compliance**: All sensitive data must be handled according to regulatory requirements
2. **Security First**: Never commit sensitive information to version control
3. **Test Coverage**: Maintain >80% test coverage for both backend and frontend
4. **Documentation**: Update documentation with any architectural changes
5. **Audit Trails**: Ensure all data modifications are logged and traceable
6. **Multi-tenancy**: Maintain strict data isolation between organizations

## 📚 **DEVELOPMENT RESOURCES**

### **Django Resources**
- Django 5.0 documentation
- Django REST Framework guides
- Data compliance best practices
- GraphQL integration patterns

### **React Resources**
- React 18 documentation
- Vite configuration guides
- Tailwind CSS documentation
- TypeScript best practices

### **Security Resources**
- General compliance frameworks
- Data privacy guidelines
- Security audit procedures
- Penetration testing protocols

## 🤖 **AGENT CONFIGURATION NOTES**

### **Agent File Format Requirements**
All agents in `.claude/agents/` must use the correct YAML frontmatter format to be recognized by Claude Code:

```markdown
---
name: agent-name
description: Clear description of when this agent should be invoked
tools: optional,comma,separated,list  # Optional - defaults to all tools
---

# Agent instructions content follows...
```

### **Recent Configuration Fixes**
- ✅ **ag-techlead** - Fixed YAML frontmatter format (September 10, 2025)
  - Added required `---` YAML frontmatter block
  - Now properly recognized by Claude Code interface
  - Configured for architectural decisions, research analysis, and strategic planning

### **Agent Documentation Structure**
```
.claude/
├── agents.yaml          # Main agent definitions
├── agents/
│   ├── config.yaml      # Agent configuration registry
│   ├── ag-techlead.md   # Technical Lead agent (✅ YAML frontmatter)
│   ├── ag-backend.md    # Backend agent
│   ├── ag-frontend.md   # Frontend agent
│   └── [other-agents].md
└── launch-agent.sh      # Unified agent launcher
```