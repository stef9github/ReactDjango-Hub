# ReactDjango Hub - Enterprise SaaS Platform

**Version**: 2.0.0  
**Status**: Active Development  
**Architecture**: Microservices with Domain-Driven Design

## Project Overview

ReactDjango Hub is a modern, secure, and scalable enterprise SaaS platform built on microservices architecture. The platform supports multiple vertical markets through a flexible, multi-tenant architecture with comprehensive compliance capabilities.

### Key Features

- **Microservices Architecture**: Distributed services for scalability and maintainability
- **Multi-Vertical Support**: Medical Hub (ChirurgieProX) and Public Procurement Hub
- **Multi-Tenant**: Organization-level isolation with complete data privacy
- **Internationalization**: Built-in support for multiple languages (FR, DE, EN)
- **Enterprise Security**: JWT authentication, MFA, RBAC, audit trails
- **Compliance Ready**: GDPR/RGPD compliant with healthcare data standards

## Quick Start

### Prerequisites

- Python 3.13.7+
- Node.js 18+
- PostgreSQL 17
- Docker & Docker Compose
- Git

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/ReactDjango-Hub.git
cd ReactDjango-Hub

# Start all services with Docker
make dev

# Or start services individually:

# 1. Identity Service (required first)
cd services/identity-service
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py  # Runs on http://localhost:8001

# 2. Django Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver  # Runs on http://localhost:8000

# 3. React Frontend
cd frontend
npm install
npm run dev  # Runs on http://localhost:3000
```

### Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/docs
- **Identity Service**: http://localhost:8001/docs
- **Communication Service**: http://localhost:8002/docs
- **Content Service**: http://localhost:8003/docs
- **Workflow Service**: http://localhost:8004/docs

## Documentation Structure

### Documentation Hub

Our comprehensive documentation is organized for easy navigation:

```
docs/
├── DOCUMENTATION-GUIDE.md     # Master documentation guide
├── INDEX.md                   # Complete documentation index
├── architecture/              # System architecture & design
│   ├── adr/                  # Architecture Decision Records
│   ├── agents/               # Agent-specific guides
│   └── analysis/             # Technical analysis
├── products/                  # Vertical-specific documentation
│   ├── project-medical-hub/  # Medical Hub (ChirurgieProX)
│   └── project-public-hub/   # Public Procurement Hub
├── development/              # Development guides
├── testing/                  # Testing documentation
├── deployment/               # Infrastructure & deployment
└── compliance/               # Regulatory compliance
```

### Quick Documentation Links

#### Getting Started
- [Documentation Guide](/docs/DOCUMENTATION-GUIDE.md) - How to navigate and maintain docs
- [Documentation Index](/docs/INDEX.md) - Complete list of all documentation
- [Development Setup](/docs/development/setup.md) - Local environment setup
- [Agent System Overview](/.claude/AGENTS_DOCUMENTATION.md) - Claude Code agent system

#### Architecture & Design
- [Platform Architecture](/docs/architecture/platform-architecture-v2.md) - Complete system architecture
- [Architecture Decision Records](/docs/architecture/adr/) - Key architectural decisions
- [Service Integration Patterns](/services/docs/SERVICE_INTEGRATION_PATTERNS.md) - Microservices communication
- [Frontend Component Library](/docs/architecture/frontend-component-library.md) - React components

#### Vertical Markets
- [Medical Hub Architecture](/docs/architecture/vertical-medical-hub-architecture.md) - ChirurgieProX platform
- [Public Hub Architecture](/docs/architecture/vertical-public-hub-architecture.md) - Public procurement platform
- [Medical Hub Business Plan](/docs/products/project-medical-hub/02-business-plan/ChirurgieProX_Business_Plan_Complete.md)
- [Public Hub Technical Specs](/docs/products/project-public-hub/specifications-techniques-publichub.md)

#### Development Resources
- [Backend Architecture](/backend/docs/BACKEND_ARCHITECTURE.md) - Django backend design
- [Frontend Architecture](/frontend/docs/FRONTEND-ARCHITECTURE.md) - React frontend patterns
- [API Integration Guide](/services/docs/API_INTEGRATION_GUIDE.md) - Service API patterns
- [Testing Guide](/services/docs/UNIFIED_TESTING_STANDARDS.md) - Testing standards

## Technology Stack

### Backend Services
- **Python 3.13.7**: Core language for all backend services
- **Django 5.1.4 LTS**: Business logic and admin interface
- **FastAPI**: High-performance microservices
- **PostgreSQL 17**: Primary database for all services
- **Redis**: Caching and session management
- **SQLAlchemy**: ORM for microservices

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type-safe development
- **Vite**: Build tool and dev server
- **Tailwind CSS**: Utility-first styling
- **React Query**: Data fetching and caching
- **React Hook Form**: Form management
- **i18next**: Internationalization

### Infrastructure
- **Docker**: Containerization
- **Kubernetes**: Container orchestration (production)
- **Kong**: API Gateway
- **GitHub Actions**: CI/CD pipeline
- **AWS**: Cloud infrastructure

## Project Structure

```
ReactDjango-Hub/
├── backend/                   # Django backend application
│   ├── apps/                 # Django apps (core, medical, public)
│   ├── config/               # Django settings
│   └── docs/                 # Backend documentation
├── frontend/                  # React frontend application
│   ├── src/                  # React source code
│   └── docs/                 # Frontend documentation
├── services/                  # Microservices
│   ├── identity-service/     # Authentication & authorization
│   ├── communication-service/# Notifications & messaging
│   ├── content-service/      # Document management
│   ├── workflow-intelligence/# AI-powered workflows
│   └── api-gateway/          # Kong API gateway config
├── infrastructure/            # Infrastructure as code
│   ├── docker/               # Docker configurations
│   └── kubernetes/           # K8s manifests
├── docs/                     # Project documentation
└── .claude/                  # Claude Code agent configs
```

## Development with Claude Code

This project is optimized for development with Claude Code agents:

### Available Agents

```bash
# Launch any agent
./.claude/launch-agent.sh <agent-name>

# Core development agents
./.claude/launch-agent.sh backend      # Django backend
./.claude/launch-agent.sh frontend     # React frontend
./.claude/launch-agent.sh identity     # Identity service
./.claude/launch-agent.sh coordinator  # Service coordination
./.claude/launch-agent.sh techlead    # Architecture decisions

# See all available agents
ls .claude/agents/
```

### Agent Responsibilities

| Agent | Responsibility | Documentation |
|-------|---------------|---------------|
| ag-techlead | Architecture & strategic decisions | [Guide](/.claude/agents/ag-techlead.md) |
| ag-backend | Django backend development | [Guide](/.claude/agents/ag-backend.md) |
| ag-frontend | React frontend development | [Guide](/.claude/agents/ag-frontend.md) |
| ag-coordinator | Service integration | [Guide](/.claude/agents/ag-coordinator.md) |
| ag-infrastructure | Deployment & DevOps | [Guide](/.claude/agents/ag-infrastructure.md) |

## Testing

### Running Tests

```bash
# Backend tests
cd backend
python manage.py test

# Frontend tests
cd frontend
npm test

# Service tests
cd services/identity-service
pytest

# All services
make test-all
```

### Testing Documentation
- [Unified Testing Standards](/services/docs/UNIFIED_TESTING_STANDARDS.md)
- [Agent Testing Guide](/docs/testing/agent-testing.md)
- [Microservices Testing](/services/docs/MICROSERVICES_TESTING_GUIDE.md)

## Deployment

### Production Deployment

```bash
# Build production images
make docker-build-prod

# Deploy to Kubernetes
kubectl apply -f infrastructure/kubernetes/

# Or use Docker Compose for staging
docker-compose -f docker-compose.prod.yml up
```

### Deployment Documentation
- [Docker Deployment Guide](/docs/DOCKER_DEPLOYMENT_GUIDE.md)
- [AWS Setup Guide](/docs/deployment/aws-setup.md)
- [Infrastructure Documentation](/infrastructure/README.md)

## Contributing

### Development Workflow

1. **Choose the appropriate agent** for your task
2. **Review relevant documentation** in `/docs/`
3. **Follow the coding standards** for your domain
4. **Update documentation** when making changes
5. **Write tests** for new functionality
6. **Submit PR** with clear description

### Documentation Updates

When contributing, please maintain documentation:
- Update relevant README files
- Add/update API documentation
- Update architectural diagrams if needed
- Follow the [Documentation Guide](/docs/DOCUMENTATION-GUIDE.md)

## Security & Compliance

### Security Features
- JWT-based authentication with refresh tokens
- Multi-factor authentication (MFA)
- Role-based access control (RBAC)
- Complete audit trails
- Data encryption at rest and in transit

### Compliance
- **GDPR/RGPD**: Full compliance for EU data protection
- **Healthcare**: Support for medical data standards
- **Audit Trails**: Complete activity logging
- **Data Privacy**: Multi-tenant isolation

See [Compliance Documentation](/docs/compliance/) for details.

## Support

### Documentation Resources
- [Complete Documentation Index](/docs/INDEX.md)
- [Documentation Guide](/docs/DOCUMENTATION-GUIDE.md)
- [Architecture Overview](/docs/architecture/platform-architecture-v2.md)
- [API Documentation](/services/docs/API_INTEGRATION_GUIDE.md)

### Getting Help
- Review the [Troubleshooting Guide](/services/docs/TROUBLESHOOTING.md)
- Check agent-specific documentation in `.claude/agents/`
- Consult the [FAQ](/docs/FAQ.md)
- Create an issue with appropriate labels

## License

This project is proprietary software. All rights reserved.

## Acknowledgments

- Built with Claude Code agent system
- Powered by Anthropic's Claude AI
- Optimized for AI-assisted development

---

**Last Updated**: September 11, 2025  
**Maintained by**: ReactDjango Hub Development Team with Claude Code Agents