# Claude Code Agents Documentation

This document provides a comprehensive overview of all available Claude Code agents in the ReactDjango-Hub Enterprise SaaS project.

## 📋 **Agent Overview**

**Total Agents**: 11 specialized agents following the simplified `ag-` prefix naming convention.

## 🏗️ **Infrastructure & Coordination Agents**

### **ag-coordinator**
- **Description**: Services Coordinator - API gateway, service mesh, integration
- **Scope**: `services/` directory, API Gateway, cross-service integration
- **Use Cases**: Microservices orchestration, service integration, API Gateway management

### **ag-infrastructure**
- **Description**: Infrastructure - Docker, Kubernetes, CI/CD, deployment
- **Scope**: `infrastructure/` directory, CI/CD, cloud infrastructure
- **Use Cases**: Production deployments, infrastructure management, DevOps automation

## 🛡️ **Quality & Leadership Agents**

### **ag-techlead**
- **Description**: Technical Leadership - Architecture decisions, research analysis, strategic planning
- **Scope**: System architecture, technical strategy, research and analysis
- **Use Cases**: Architecture decisions, technical planning, strategic guidance

### **ag-security**
- **Description**: Security & Compliance - Security audits, vulnerability scanning
- **Scope**: Security audits, compliance validation, vulnerability assessments
- **Use Cases**: Compliance checks, security reviews, audit trails

### **ag-reviewer**
- **Description**: Code Review - Code quality, PR reviews, best practices
- **Scope**: Code quality, security, performance, compliance validation
- **Use Cases**: Pull request reviews, code quality audits, security validation

## 🚀 **Core Service Agents**

### **ag-backend**
- **Description**: Django Backend - Core business logic, data models, REST APIs
- **Scope**: `backend/` directory, Django application, business logic
- **Use Cases**: Django development, REST APIs, data models, business logic

### **ag-frontend**
- **Description**: React Frontend - User interface, components, state management
- **Scope**: `frontend/` directory, React application, UI/UX
- **Use Cases**: React development, UI components, state management, user interfaces

### **ag-identity**
- **Description**: Identity Service - Authentication, users, MFA, RBAC
- **Scope**: `services/identity-service/` directory, authentication systems
- **Use Cases**: Authentication features, MFA implementation, user management, RBAC

### **ag-communication**
- **Description**: Communication Service - Notifications, messaging, real-time
- **Scope**: `services/communication-service/` directory  
- **Use Cases**: Notification systems, messaging, email/SMS, real-time communication

### **ag-content**
- **Description**: Content Service - Document management, file storage
- **Scope**: `services/content-service/` directory
- **Use Cases**: Document management, search functionality, file storage, content processing

### **ag-workflow**
- **Description**: Workflow Intelligence - Process automation, AI workflows
- **Scope**: `services/workflow-intelligence-service/` directory
- **Use Cases**: Process automation, AI integration, workflow orchestration

## 🗂️ **Agent Directory Structure**

```
.claude/agents/
├── ag-backend.md                         # Django Backend Agent
├── ag-frontend.md                        # React Frontend Agent
├── ag-identity.md                        # Identity Service Agent
├── ag-communication.md                   # Communication Service Agent
├── ag-content.md                         # Content Service Agent
├── ag-workflow.md                        # Workflow Intelligence Agent
├── ag-infrastructure.md                  # Infrastructure Agent
├── ag-coordinator.md                     # Services Coordinator Agent
├── ag-security.md                        # Security & Compliance Agent
├── ag-reviewer.md                        # Code Review Agent
└── ag-techlead.md                        # Technical Leadership Agent
```

## 🎯 **Agent Selection Guidelines**

### **For Architecture & Planning**
- Use **ag-techlead** for strategic decisions and project planning
- Use **ag-coordinator** for microservices integration and API Gateway

### **For Backend Development**
- Use **ag-backend** for Django business logic and REST APIs
- Use **ag-identity** for authentication and security features
- Use microservice agents for service-specific development

### **For Frontend Development** 
- Use **ag-frontend** for React UI/UX and user interfaces
- **IMPORTANT**: Frontend requires services to be running first (see Agent Dependencies below)

### **For Security & Compliance**
- Use **ag-security** for security audits and compliance reviews

### **For DevOps & Deployment**
- Use **ag-infrastructure** for infrastructure and deployment automation

### **For Code Quality**
- Use **ag-reviewer** for pull request reviews and code audits

## 🔗 **Agent Dependencies & Coordination**

### **Frontend Development Dependencies**
The **ag-frontend** agent requires the following services to be running before starting development:

1. **Microservices Infrastructure** (managed by ag-coordinator):
   - Kong API Gateway on port 8080 (primary API endpoint)
   - Identity Service on port 8001
   - Content Service on port 8002
   - Communication Service on port 8003
   - Workflow Service on port 8004

2. **Django Backend** (managed by ag-backend):
   - Django REST API on port 8000

**Startup Sequence for Frontend Development**:
```bash
# Step 1: Invoke ag-coordinator to start microservices
# Step 2: Invoke ag-backend to start Django
# Step 3: Frontend can now start development
```

### **Service Integration Patterns**
- **ag-coordinator** manages cross-service integration and Kong API Gateway
- **ag-backend** integrates with microservices through API clients
- **ag-frontend** connects to services through Kong (port 8080) and Django (port 8000)
- Individual service agents (ag-identity, ag-content, etc.) handle their own service logic

### **Agent Interaction Rules**
- Service agents communicate only through APIs (no direct code modification)
- Infrastructure changes go through **ag-infrastructure**
- Cross-service integration questions go to **ag-coordinator**
- Each agent maintains its own documentation and configuration

## 🔄 **Microservices Architecture Coverage**

| Service | Port | Agent | Scope |
|---------|------|-------|--------|
| **Identity Service** | 8001 | `ag-identity` | Authentication, users, MFA |
| **Content Service** | 8002 | `ag-content` | Documents, search, audit |
| **Communication Service** | 8003 | `ag-communication` | Notifications, messaging |
| **Workflow Service** | 8004 | `ag-workflow` | Automation, AI |
| **Django Backend** | 8000 | `ag-backend` | Business logic, medical records |
| **React Frontend** | 3000 | `ag-frontend` | UI/UX, patient interfaces |
| **API Gateway/Kong** | 8080 | `ag-coordinator` | Service routing, load balancing |

## 🚀 **Usage Best Practices**

1. **Agent Specialization**: Use the most specific agent for your task
2. **Cross-Service Work**: Use `ag-coordinator` for integration tasks
3. **Security Reviews**: Always involve `ag-security` for sensitive data
4. **Code Quality**: Use `ag-reviewer` before merging significant changes
5. **Architecture Decisions**: Consult `ag-techlead` for major technical decisions

## 🔧 **Agent Configuration**

All agents are configured with proper YAML frontmatter:
```yaml
---
name: agent-name
description: Agent description
---
```

Agents are available through Claude Code's agent selection interface and can be invoked for specialized tasks within their defined scope.

---

**Last Updated**: September 2025  
**Total Agents**: 11  
**Project**: ReactDjango-Hub Enterprise SaaS Platform