# Identity Service - Claude Code Agent Configuration

## 🎯 Service Identity
- **Service Name**: Identity & Authentication Service
- **Technology Stack**: FastAPI, SQLAlchemy, PostgreSQL 17, Alembic
- **Port**: 8001
- **Database**: PostgreSQL (identity_service_db)
- **Purpose**: Authentication, authorization, user management, organizations, MFA
- **Status**: ✅ **100% Production Ready with Enterprise Testing**

## 🧠 Your Exclusive Domain

### Core Responsibilities
- User authentication and authorization
- Multi-factor authentication (MFA) - Email, SMS, TOTP
- User account management
- Organization and team management
- Role-based access control (RBAC)
- Session and token management
- Password policies and security
- Audit logging for compliance
- API key management

### What You Own and Manage
```
services/identity-service/
├── app/
│   ├── api/                # FastAPI routes
│   │   ├── auth/           # Authentication endpoints
│   │   ├── users/          # User management
│   │   ├── organizations/  # Organization management
│   │   ├── mfa/            # Multi-factor auth
│   │   └── audit/          # Audit endpoints
│   ├── core/               # Core configuration
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   ├── utils/              # Utility functions
│   └── middleware/         # Custom middleware
├── tests/                  # Comprehensive test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── e2e/              # End-to-end tests
│   └── performance/       # Performance tests
├── alembic/               # Database migrations
├── requirements.txt       # Python dependencies
└── main.py               # Application entry point
```

## 🚫 Service Boundaries (STRICT)

### What You CANNOT Modify
- **Backend** (`backend/`): Business logic service - integration only
- **Frontend** (`frontend/`): UI layer - API contracts only
- **Other Services** (`services/communication-service/`, `services/workflow-intelligence-service/`): Peer services
- **Infrastructure** (`docker/`, `kubernetes/`): Deployment configs
- **GitHub Workflows** (`.github/`): CI/CD pipelines

### Integration Points (Provide APIs)
- Backend Service: Validates JWT tokens, provides user context
- Frontend: Authentication flows, user management UI
- Other Services: Token validation, user information
- External Systems: OAuth providers, MFA services

## 🔧 Development Commands

### Service Management
```bash
# Setup & Installation
cd services/identity-service
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
pip install -r requirements.txt

# Run Development Server
python main.py                  # Starts on http://localhost:8001
# OR
uvicorn app.main:app --reload --port 8001

# Database Operations
alembic init alembic            # Initialize migrations (already done)
alembic revision --autogenerate -m "Description"
alembic upgrade head            # Apply migrations
alembic downgrade -1           # Rollback one migration

# Testing (Comprehensive Suite)
pytest                          # Run all tests
pytest tests/unit              # Unit tests only
pytest tests/integration       # Integration tests
pytest tests/e2e              # End-to-end tests
pytest --cov=app              # Coverage report
pytest -v -s                  # Verbose with print statements

# Code Quality
black .                        # Format code
isort .                       # Sort imports
flake8 .                      # Linting
mypy app                      # Type checking
```

## 📊 Service Architecture

### Key Files You Own
- `app/main.py` - FastAPI application setup
- `app/api/` - All API route definitions
- `app/models/` - Database models (User, Organization, Role, etc.)
- `app/schemas/` - Request/response schemas
- `app/services/` - Business logic layer
- `app/core/security.py` - JWT and security functions
- `app/core/config.py` - Configuration management
- `alembic/` - Database migration scripts

### Database Models You Manage
- **User**: Core user accounts with profiles
- **Organization**: Multi-tenant organizations
- **Role**: RBAC roles and permissions
- **Session**: Active user sessions
- **MFAConfig**: Multi-factor auth settings
- **AuditLog**: Compliance audit trails
- **APIKey**: Service API keys
- **PasswordHistory**: Password rotation tracking

### API Endpoints You Control (40 endpoints)
- `/api/v1/auth/` - Login, logout, refresh tokens
- `/api/v1/users/` - User CRUD operations
- `/api/v1/organizations/` - Organization management
- `/api/v1/mfa/` - MFA setup and verification
- `/api/v1/roles/` - Role and permission management
- `/api/v1/audit/` - Audit log access
- `/api/v1/sessions/` - Session management
- `/api/v1/api-keys/` - API key management

## 🎯 Current Status & Priority Tasks

### ✅ Completed (100% Production Ready)
- [x] Complete authentication system with JWT
- [x] Multi-factor authentication (Email, SMS, TOTP)
- [x] User and organization management
- [x] Role-based access control (RBAC)
- [x] Comprehensive test suite (unit, integration, e2e)
- [x] Performance testing infrastructure
- [x] Database migrations with Alembic
- [x] API documentation (OpenAPI/Swagger)
- [x] Audit logging for compliance
- [x] Password policies and rotation
- [x] Session management
- [x] Rate limiting and security headers

### 🔴 Critical Tasks (Immediate)
1. [ ] Add OAuth 2.0 provider support (Google, Microsoft)
2. [ ] Implement SAML 2.0 for enterprise SSO
3. [ ] Add biometric authentication support
4. [ ] Create admin dashboard for user management
5. [ ] Implement account recovery workflows

### 🟡 Important Tasks (This Week)
1. [ ] Add LDAP/Active Directory integration
2. [ ] Implement IP whitelisting for organizations
3. [ ] Create bulk user import/export
4. [ ] Add advanced audit reporting
5. [ ] Implement delegated administration

### 🟢 Backlog Items
- [ ] WebAuthn/FIDO2 support
- [ ] Risk-based authentication
- [ ] Behavioral analytics
- [ ] Compliance reporting (SOC2, ISO27001)
- [ ] Multi-region deployment support

## 🔍 Testing Requirements

### Coverage Goals
- **Current**: 95% test coverage
- **Target**: Maintain > 90% coverage
- **Critical Paths**: 100% coverage for auth flows

### Existing Test Suite
- ✅ 150+ unit tests
- ✅ 75+ integration tests
- ✅ 25+ end-to-end tests
- ✅ Performance benchmarks
- ✅ Security test cases
- ✅ Load testing scenarios

### Test Scenarios Covered
- Authentication flows (login, logout, refresh)
- MFA setup and verification
- User lifecycle management
- Organization operations
- RBAC and permissions
- Session management
- API key operations
- Password policies
- Audit logging

## 📈 Success Metrics

### Performance Targets
- Authentication < 100ms response time
- Support 10,000+ concurrent users
- 99.99% uptime SLA
- < 0.01% failed authentication rate
- Token refresh < 50ms

### Security Targets
- Zero security vulnerabilities
- 100% OWASP Top 10 compliance
- Full audit trail coverage
- MFA adoption > 80%
- Password rotation compliance

## 🚨 Critical Reminders

### Security Considerations
- **NEVER** log passwords or tokens
- **ALWAYS** hash passwords with bcrypt
- **VALIDATE** all input data
- **ROTATE** JWT secrets regularly
- **IMPLEMENT** rate limiting on all endpoints
- **AUDIT** all authentication events

### Data Privacy Compliance
- Log all access attempts (success and failure)
- Implement data minimization principles
- Provide user data export capabilities
- Support right to be forgotten
- Maintain encryption at rest and transit
- Regular security assessments

### FastAPI Best Practices
- Use dependency injection for services
- Implement proper error handling
- Use Pydantic for validation
- Maintain OpenAPI documentation
- Use async/await for I/O operations
- Implement middleware for cross-cutting concerns

### Integration Requirements
- Provide JWT tokens for all services
- Maintain backwards compatibility
- Version all API endpoints
- Document breaking changes
- Support multiple authentication methods
- Provide health check endpoints

## 📝 Notes for Agent

When working in this service:
1. This is the ONLY service handling authentication
2. All other services depend on this for auth
3. Maintain 100% uptime - this is critical infrastructure
4. Test all auth flows thoroughly
5. Security is paramount - no compromises
6. Keep audit logs comprehensive
7. Coordinate API changes with all consumers
8. Performance is critical for user experience
9. Always consider multi-tenancy in design
10. Maintain production-ready status at all times

## 🏆 Service Achievements

- ✅ **100% Production Ready**
- ✅ **Enterprise-Grade Testing**
- ✅ **95% Test Coverage**
- ✅ **40 API Endpoints**
- ✅ **MFA Implementation**
- ✅ **RBAC System**
- ✅ **Audit Compliance**
- ✅ **Performance Optimized**