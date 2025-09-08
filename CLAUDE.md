# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🏥 **PROJECT OVERVIEW**

**ReactDjango Hub Medical** - A modern, secure, and scalable SaaS platform for medical practices with HIPAA/RGPD compliance.

### **Tech Stack**
- **Backend**: Django 5.0 + GraphQL + PostgreSQL
- **Frontend**: React 18 + Vite + Tailwind CSS
- **Infrastructure**: Docker + Kubernetes
- **Security**: End-to-end encryption, RBAC, 2FA

### **Key Features**
- Multi-tenant architecture with secure isolation between medical practices
- Patient management with encrypted PII and audit trails
- Clinical workflows (appointments, consultations, prescriptions)
- Billing system with insurance claims and payment processing
- HIPAA/RGPD compliance with full audit logging
- Real-time analytics dashboards and reporting

## 🚀 **DEVELOPMENT WORKFLOW**

### **Local Development Commands**

```bash
# Backend (Django) - Detailed Commands
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Specific Django commands
python manage.py makemigrations                    # Create new migrations
python manage.py migrate                           # Apply migrations
python manage.py migrate --database=secondary     # Multi-database migrations
python manage.py createsuperuser                  # Create admin user
python manage.py collectstatic                    # Collect static files
python manage.py shell                            # Django shell
python manage.py dbshell                          # Database shell

# Frontend (React + Vite)
cd frontend
npm install
npm run dev
npm run build                                      # Production build
npm run preview                                    # Preview production build
npm run lint                                       # Lint code
npm run type-check                                 # TypeScript type checking

# Full stack development
npm run dev:start        # Start both backend and frontend
npm run dev:status       # Check health of all services  
npm run dev:test         # Run comprehensive tests
npm run dev:logs         # View real-time logs
npm run dev:stop         # Clean shutdown
npm run dev:reset        # Reset database with test data

# Requirements Management
python scripts/sync_requirements.py               # Sync production requirements
python scripts/sync_requirements.py --check-only  # Check if requirements are in sync
python scripts/install_git_hooks.py              # Install git hooks to prevent sync issues
```

### **Testing Process**

```bash
# Django backend tests - Detailed
cd backend
python manage.py test                                    # Run all tests
python manage.py test apps.core.tests                   # Run specific app tests
python manage.py test apps.core.tests.test_models       # Run specific test file
python manage.py test apps.core.tests.TestPatientModel.test_patient_creation  # Run specific test

# React frontend tests
cd frontend
npm test                                                 # Run all tests
npm test -- --coverage                                  # Run with coverage report
npm test -- --watch                                     # Run in watch mode
npm test -- ComponentName                               # Run specific component tests

# Integration tests
npm run test:integration                                 # API integration tests
npm run test:e2e                                        # End-to-end tests

# Comprehensive testing
npm run dev:test-comprehensive                           # All tests with real data
npm run test:security                                   # Security compliance tests
npm run test:performance                                # Performance benchmarks
npm run test:accessibility                             # A11y compliance tests

# API Testing
python test_api_endpoints.py                           # Test API functionality
python test_patient_api.py                             # Test patient API
python test_clinical_api.py                            # Test clinical workflows API
```

### **Build and Deployment**

```bash
# Build frontend for production
cd frontend
npm run build

# Django production setup
cd backend
python manage.py collectstatic
python manage.py migrate

# Docker deployment
docker-compose up -d --build

# Kubernetes deployment
kubectl apply -f infrastructure/kubernetes/
```

## 📁 **PROJECT STRUCTURE**

```
ReactDjango-Hub/
├── backend/                    # Django application
│   ├── apps/                  # Django apps
│   │   ├── core/              # Core models and utilities
│   │   ├── clinical/          # Clinical workflows
│   │   ├── billing/           # Billing and payments
│   │   ├── compliance/        # HIPAA/RGPD compliance
│   │   └── analytics/         # Analytics and reporting
│   ├── config/                # Django settings
│   │   └── settings/          # Environment-specific settings
│   ├── tests/                 # Backend tests
│   │   ├── unit/
│   │   ├── integration/
│   │   └── e2e/
│   ├── media/                 # User uploaded files
│   ├── static/                # Static assets
│   └── templates/             # Django templates
├── frontend/                  # React application
│   ├── public/                # Public assets
│   └── src/                   # React source code
│       ├── components/        # React components
│       │   ├── common/        # Reusable components
│       │   ├── layout/        # Layout components
│       │   └── medical/       # Medical-specific components
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
│   ├── terraform/             # Terraform configurations
│   ├── nginx/                 # Nginx configurations
│   └── scripts/               # Deployment scripts
├── .github/                   # GitHub workflows
│   └── workflows/             # CI/CD pipelines
├── docs/                      # Documentation
└── .claude/                   # Claude-specific configurations
    └── prompts/               # Custom prompts
```

## 📦 **REQUIREMENTS MANAGEMENT**

The project uses separate requirements files for different environments:

### **Requirements Structure**
```bash
backend/
├── requirements.txt                    # Main requirements (development)
├── requirements-production.txt         # Production-specific requirements
├── requirements-dev.txt               # Development-only requirements
└── requirements-test.txt              # Testing-specific requirements
```

### **Adding New Packages**
When adding new packages:
1. Add to appropriate requirements file (`requirements.txt` for main dependencies)
2. Run `python scripts/sync_requirements.py` to update production requirements
3. Test in both development and production environments
4. Use git hooks to prevent deployment issues

### **Requirements Sync Commands**
```bash
# Check if requirements are synchronized
python scripts/sync_requirements.py --check-only

# Automatically sync requirements
python scripts/sync_requirements.py

# Install git hooks (one-time setup)
python scripts/install_git_hooks.py
```

### **Database Setup**

The project uses multiple databases for separation of concerns:
- `db.sqlite3` (development) / PostgreSQL (production) - Main application database  
- `sessions.sqlite3` / Redis (production) - Session storage
- `analytics.sqlite3` / PostgreSQL (production) - Analytics data

#### **Database Commands**
```bash
# Set up all databases
python manage.py setup_databases

# Set up sessions database specifically  
python manage.py setup_sessions_db --check-only    # Check setup
python manage.py setup_sessions_db                 # Create if needed

# Multi-database migrations
python manage.py migrate                           # Default database
python manage.py migrate --database=sessions      # Sessions database
python manage.py migrate --database=analytics     # Analytics database
```

## 🔧 **DEVELOPMENT GUIDELINES**

### **Django Backend Patterns**
- Use Django REST Framework for API endpoints
- Implement proper authentication and authorization
- Follow Django naming conventions for models, views, and serializers
- Ensure HIPAA compliance for all patient data handling
- Use database migrations for all schema changes

### **React Frontend Patterns**
- Use functional components with hooks
- Implement TypeScript for type safety
- Follow component composition patterns
- Use Tailwind CSS for styling
- Implement proper error boundaries and loading states

### **Security Requirements** ⭐ **CRITICAL**
- All patient data must be encrypted at rest and in transit
- Implement audit logging for all data access
- Use proper authentication mechanisms (JWT tokens, 2FA)
- Follow HIPAA/RGPD compliance guidelines
- Regular security audits and penetration testing

### **Testing Requirements**
- Unit tests for all business logic
- Integration tests for API endpoints
- End-to-end tests for critical user flows
- Performance tests for scalability
- Security tests for compliance verification

## 🚀 **DEPLOYMENT PROCESS**

### **Environment Setup**
```bash
# Production environment variables
DATABASE_URL=postgresql://user:pass@localhost/dbname
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com

# Frontend environment
VITE_API_URL=https://your-domain.com/api
VITE_ENVIRONMENT=production
```

### **CI/CD Pipeline**
- Automated testing on pull requests
- Security scanning for vulnerabilities
- Automated deployment to staging environment
- Manual approval for production deployment
- Post-deployment health checks

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

---

*This is a medical software project requiring strict compliance with healthcare regulations. Always prioritize security, privacy, and regulatory compliance in all development decisions.*