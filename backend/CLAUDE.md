# Backend Service - Claude Code Agent Configuration

## 🎯 Service Identity
- **Service Name**: ReactDjango Hub Medical Backend
- **Technology Stack**: Django 5.1.4 LTS, Django Ninja 1.4.3, PostgreSQL 17
- **Port**: 8000
- **Database**: PostgreSQL (medical_hub_backend)
- **Purpose**: Business logic, medical records, billing, analytics

## 🧠 Your Exclusive Domain

### Core Responsibilities
- Django application architecture and models
- Business logic implementation
- Medical records management (DICOM, HL7)
- Billing and insurance processing
- Analytics and reporting
- API endpoints via Django Ninja
- Database migrations and schema
- Backend testing and quality assurance

### What You Own and Manage
```
backend/
├── apps/                    # ALL Django applications
│   ├── medical_records/    # Patient data, medical history
│   ├── billing/            # Insurance, payments, claims
│   ├── analytics/          # Reporting and dashboards
│   ├── appointments/       # Scheduling system
│   └── notifications/      # Alert system
├── config/                 # Django settings and configuration
├── api/                    # Django Ninja API routes
├── tests/                  # ALL backend tests
├── migrations/             # Database migrations
└── requirements.txt        # Python dependencies
```

## 🚫 Service Boundaries (STRICT)

### What You CANNOT Modify
- **Identity Service** (`services/identity-service/`): Authentication is handled externally
- **Frontend** (`frontend/`): Only consume, never modify React code
- **Other Services** (`services/communication-service/`, `services/workflow-intelligence-service/`): Integration only
- **Infrastructure** (`infrastructure/`, `docker/`, `kubernetes/`): Read-only access
- **GitHub Workflows** (`.github/`): No modifications

### Integration Points (Read-Only)
- Identity Service API (port 8001): User authentication, organizations, MFA
- Frontend API contracts: Maintain compatibility
- Communication Service: Send requests only
- Workflow Service: Trigger workflows only

## 🔧 Development Commands

### Service Management
```bash
# Activation & Setup
cd backend
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
pip install -r requirements.txt

# Run Development Server
python manage.py runserver      # Starts on http://localhost:8000

# Database Operations
python manage.py makemigrations
python manage.py migrate
python manage.py dbshell
python manage.py shell

# Testing
python manage.py test
python manage.py test apps.medical_records
python manage.py test --coverage
python manage.py test --parallel

# Code Quality
python manage.py check
ruff check .
ruff format .
mypy .
```

## 📊 Service Architecture

### Key Files You Own
- `config/settings/` - Django configuration
- `config/urls.py` - URL routing
- `api/` - Django Ninja API endpoints
- `apps/*/models.py` - Database models
- `apps/*/views.py` - Business logic
- `apps/*/serializers.py` - Data serialization
- `apps/*/tests/` - Test suites

### Database Models You Manage
- Patient records and medical history
- Billing and insurance claims
- Appointments and scheduling
- Analytics and reporting data
- Audit logs for HIPAA compliance

### API Endpoints You Control
- `/api/medical-records/` - Patient data CRUD
- `/api/billing/` - Insurance and payments
- `/api/appointments/` - Scheduling system
- `/api/analytics/` - Reports and dashboards
- `/api/notifications/` - Alert management

## 🎯 Current Status & Priority Tasks

### ✅ Completed
- [x] Initial Django project setup
- [x] PostgreSQL database configuration
- [x] Django Ninja integration
- [x] Basic project structure

### 🔴 Critical Tasks (Immediate)
1. [ ] Implement patient model with HIPAA compliance fields
2. [ ] Create Django Ninja API endpoints for medical records
3. [ ] Add audit logging for all data modifications
4. [ ] Implement integration with Identity Service for auth
5. [ ] Set up comprehensive test suite structure

### 🟡 Important Tasks (This Week)
1. [ ] Design billing models for insurance claims
2. [ ] Create appointment scheduling system
3. [ ] Implement HL7/DICOM data format support
4. [ ] Add data validation and sanitization
5. [ ] Set up API documentation with Django Ninja

### 🟢 Backlog Items
- [ ] Analytics dashboard implementation
- [ ] Bulk data import/export functionality
- [ ] Advanced reporting features
- [ ] Performance optimization
- [ ] Caching strategy implementation

## 🔍 Testing Requirements

### Coverage Goals
- **Target**: 85% test coverage minimum
- **Critical Paths**: 100% coverage for patient data, billing

### Key Test Scenarios
- Patient data CRUD operations
- HIPAA compliance validation
- Billing calculations accuracy
- Appointment conflict detection
- API authentication integration
- Data migration integrity

### Missing Tests to Implement
- [ ] Patient model unit tests
- [ ] API endpoint integration tests
- [ ] Billing calculation tests
- [ ] Security and permission tests
- [ ] Performance tests for large datasets

## 📈 Success Metrics

### Performance Targets
- API response time < 200ms for queries
- Database query optimization (N+1 prevention)
- Support 1000+ concurrent users
- 99.9% uptime availability

### Quality Targets
- 85% test coverage minimum
- Zero critical security vulnerabilities
- 100% HIPAA compliance
- Full audit trail coverage
- Type hints on all functions

## 🚨 Critical Reminders

### Security Considerations
- **NEVER** store unencrypted patient data
- **ALWAYS** use Django's ORM to prevent SQL injection
- **VALIDATE** all input data before processing
- **AUDIT** all data access and modifications
- **ENCRYPT** sensitive fields in the database

### HIPAA/RGPD Compliance
- Implement audit logging for all patient data access
- Ensure data encryption at rest and in transit
- Implement data retention policies
- Provide data export for patient requests
- Maintain access control lists

### Django Best Practices
- Use Django migrations for ALL schema changes
- Follow Django's MVT (Model-View-Template) pattern
- Use Django Ninja for RESTful API design
- Implement proper error handling
- Use Django's built-in security features
- Maintain database query efficiency

### Integration Requirements
- Identity Service handles ALL authentication
- Frontend consumes your API endpoints
- Maintain backwards compatibility
- Document all API changes
- Version your API endpoints

## 📝 Notes for Agent

When working in this service:
1. Check Identity Service API docs before implementing auth features
2. Ensure all patient data operations are audited
3. Run tests after every significant change
4. Update API documentation when adding endpoints
5. Coordinate with Frontend agent for API contracts
6. Never modify authentication logic (use Identity Service)
7. Always consider HIPAA compliance in design decisions
8. Maintain high test coverage for critical paths