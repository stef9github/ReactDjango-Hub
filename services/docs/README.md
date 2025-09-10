# Services Documentation

This directory contains documentation specific to the microservices architecture and coordination within the `/services` directory.

## 📁 Documentation Structure

### Service-Specific Documentation
Documentation that relates to the coordination, integration, and testing of microservices:

- **MICROSERVICES_COORDINATION_ACHIEVEMENTS.md** - Achievements and patterns for service coordination
- **MICROSERVICES_QUALITY_AUDIT.md** - Quality audits and standards for microservices
- **MICROSERVICES_TESTING_GUIDE.md** - Testing strategies for microservices
- **API_INTEGRATION_GUIDE.md** - API integration patterns between services
- **SERVICE_INTEGRATION_PATTERNS.md** - Common integration patterns
- **JWT_AUTHENTICATION_INTEGRATION_GUIDE.md** - JWT authentication across services
- **DOCKER_CONFIGURATION_GUIDE.md** - Docker setup for services
- **CONFIGURATION_SHARING.md** - Sharing configuration between services

### Global Documentation (Located in /docs/development/)
Documentation that applies to the entire project and Claude Code agents:

- **inter-agent-communication.md** - Communication protocols between Claude Code agents
- **agent-optimization-guide.md** - Optimization strategies for all agents
- **agent-context-management.md** - Managing agent context across the project
- **claude-workflow-guide.md** - Claude Code workflow best practices

## 🎯 Key Distinction

- **This directory (`/services/docs/`)**: Microservices architecture, coordination, and integration
- **Project docs (`/docs/`)**: Global project documentation, agent guides, compliance, etc.

## 📝 When to Add Documentation Here

Add documentation to this directory when it:
- Relates specifically to microservice coordination
- Describes service-to-service communication patterns
- Documents API contracts between services
- Covers service-specific testing or deployment strategies
- Details configuration sharing between services

For Claude Code agent documentation, development workflows, or project-wide standards, use `/docs/development/` instead.