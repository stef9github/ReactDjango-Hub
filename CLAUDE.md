# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🏥 **PROJECT OVERVIEW**

**ReactDjango Hub Medical** - A modern, secure, and scalable SaaS platform for medical practices with HIPAA/RGPD compliance.

### **Tech Stack**
- **Backend**: Python 3.13.7 + Django 5.1.4 LTS + Django Ninja 1.4.3 + PostgreSQL 17
- **Frontend**: React 18 + Vite + Tailwind CSS
- **Infrastructure**: Docker + Kubernetes
- **Security**: End-to-end encryption, RBAC, 2FA

### **Key Features**
- Multi-tenant architecture with secure isolation between medical practices
- Patient management with encrypted PII and audit trails
- Clinical workflows (appointments, consultations, prescriptions)
- HIPAA/RGPD compliance with full audit logging
- Real-time analytics dashboards and reporting

## 🚀 **DEVELOPMENT WORKFLOW**

### **Local Development Commands**

```bash
# Backend (Django)
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Django commands
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
python manage.py shell
python manage.py dbshell

# Frontend (React + Vite)
cd frontend
npm install
npm run dev
npm run build
npm run preview
npm run lint
npm run type-check
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