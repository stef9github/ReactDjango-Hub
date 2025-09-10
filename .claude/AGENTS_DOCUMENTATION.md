# Claude Code Agents Documentation

This document provides a comprehensive overview of all available Claude Code agents in the ReactDjango-Hub Enterprise SaaS project.

## 📋 **Agent Overview**

**Total Agents**: 10 specialized agents following the simplified `ag-` prefix naming convention.

## 🏗️ **Infrastructure & Coordination Agents**

### **ag-coordinator**
- **Description**: Services Coordinator - API gateway, service mesh, integration
- **Scope**: `services/` directory, API Gateway, cross-service integration
- **Use Cases**: Microservices orchestration, service integration, API Gateway management

### **ag-infrastructure**
- **Description**: Infrastructure - Docker, Kubernetes, CI/CD, deployment
- **Scope**: `infrastructure/` directory, CI/CD, cloud infrastructure
- **Use Cases**: Production deployments, infrastructure management, DevOps automation

## 🛡️ **Quality & Compliance Agents**

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
├── tech-lead.md                          # Technical leadership
└── workflow-intelligence-service-agent.md # Workflow microservice
```

## 🎯 **Agent Selection Guidelines**

### **For Architecture & Planning**
- Use **tech-lead** for strategic decisions and project planning
- Use **services-coordinator** for microservices integration and API Gateway

### **For Backend Development**
- Use **django-backend-expert** for Django business logic and medical records
- Use **identity-service-expert** for authentication and security features
- Use microservice agents for service-specific development

### **For Frontend Development** 
- Use **react-frontend-expert** for React UI/UX and patient interfaces

### **For Security & Compliance**
- Use **security-compliance-expert** for HIPAA/RGPD audits and security reviews

### **For DevOps & Deployment**
- Use **deployment-agent** for infrastructure and deployment automation

### **For Code Quality**
- Use **code-reviewer** for pull request reviews and code audits

### **For Tool Optimization**
- Use **claude-code-optimization-expert** for Claude Code setup and workflow optimization

## 🔄 **Microservices Architecture Coverage**

| Service | Port | Agent | Scope |
|---------|------|-------|--------|
| **Identity Service** | 8001 | `identity-service-expert` / `identity-service` | Authentication, users, MFA |
| **Content Service** | 8002 | `content-service` | Documents, search, audit |
| **Communication Service** | 8003 | `communication-service` | Notifications, messaging |
| **Workflow Service** | 8004 | `workflow-intelligence-service` | Automation, AI |
| **Django Backend** | 8000 | `django-backend-expert` | Business logic, medical records |
| **React Frontend** | 3000 | `react-frontend-expert` | UI/UX, patient interfaces |
| **API Gateway** | - | `services-coordinator` | Service routing, load balancing |

## 🚀 **Usage Best Practices**

1. **Agent Specialization**: Use the most specific agent for your task
2. **Cross-Service Work**: Use `services-coordinator` for integration tasks
3. **Security Reviews**: Always involve `security-compliance-expert` for medical data
4. **Code Quality**: Use `code-reviewer` before merging significant changes
5. **Architecture Decisions**: Consult `tech-lead` for major technical decisions

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
**Total Agents**: 14  
**Project**: ReactDjango-Hub Medical SaaS Platform