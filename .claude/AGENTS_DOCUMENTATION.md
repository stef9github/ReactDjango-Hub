# Claude Code Agents Documentation

This document provides a comprehensive overview of all available Claude Code agents in the ReactDjango-Hub Medical SaaS project.

## 📋 **Agent Overview**

**Total Agents**: 14 specialized agents for different aspects of the medical SaaS platform.

## 🏗️ **Architecture & Leadership Agents**

### **tech-lead** 
- **Description**: Technical lead for architecture decisions, project planning, and team coordination
- **Scope**: Project-wide architecture, technical decisions, team coordination
- **Use Cases**: Strategic technical planning, architecture reviews, cross-team coordination

### **services-coordinator**
- **Description**: Cross-service coordination, API Gateway management, and microservices documentation  
- **Scope**: `services/` directory, API Gateway, cross-service integration
- **Use Cases**: Microservices orchestration, service integration, API Gateway management

## 🛡️ **Security & Compliance Agents**

### **security-compliance-expert**
- **Description**: Cybersecurity and compliance specialist for HIPAA/RGPD compliance and security audits
- **Scope**: Security audits, compliance validation, vulnerability assessments
- **Use Cases**: HIPAA compliance checks, security reviews, audit trails

## 🔧 **Development & Optimization Agents**

### **claude-code-optimization-expert**
- **Description**: Claude Code specialist for optimizing development workflows, agent configurations, and automation
- **Scope**: Claude Code setup, agent configurations, workflow optimization
- **Use Cases**: Agent management, Claude Code setup, development workflow optimization

### **code-reviewer**
- **Description**: Senior code reviewer specializing in Django, React, and medical software compliance
- **Scope**: Code quality, security, performance, compliance validation
- **Use Cases**: Pull request reviews, code quality audits, security validation

### **deployment-agent**
- **Description**: DevOps engineer for medical SaaS deployments with HIPAA-compliant infrastructure
- **Scope**: CI/CD, cloud infrastructure, deployment automation
- **Use Cases**: Production deployments, infrastructure management, DevOps automation

## 🎯 **Backend Development Agents**

### **django-backend-expert**
- **Description**: Senior Django backend developer for medical SaaS platforms with HIPAA/RGPD compliance expertise
- **Scope**: `backend/` directory, Django application, business logic
- **Use Cases**: Django development, medical records, billing systems, HIPAA compliance

### **identity-service-expert**
- **Description**: FastAPI authentication specialist for identity microservice with MFA and user management
- **Scope**: `services/identity-service/` directory, authentication systems
- **Use Cases**: Authentication features, MFA implementation, user management

### **identity-service** (Microservice Agent)
- **Description**: Identity microservice specialist for authentication and user management
- **Scope**: `services/identity-service/` directory, microservice-specific development
- **Use Cases**: Identity microservice development, service-specific features

## 🎨 **Frontend Development Agents**

### **react-frontend-expert**
- **Description**: Senior React frontend developer specializing in TypeScript and medical UI/UX requirements
- **Scope**: `frontend/` directory, React application, medical UI/UX
- **Use Cases**: React development, medical dashboards, patient interfaces, French localization

## 📊 **Microservice-Specific Agents**

### **content-service**
- **Description**: Content management microservice specialist for documents and search
- **Scope**: `services/content-service/` directory
- **Use Cases**: Document management, search functionality, content processing

### **communication-service**
- **Description**: Communication microservice specialist for notifications and messaging
- **Scope**: `services/communication-service/` directory  
- **Use Cases**: Notification systems, messaging, communication features

### **workflow-intelligence-service**
- **Description**: Workflow and intelligence microservice specialist for automation and AI
- **Scope**: `services/workflow-intelligence-service/` directory
- **Use Cases**: Process automation, AI integration, workflow management

## 🗂️ **Agent Directory Structure**

```
.claude/agents/
├── claude-code-optimization-expert.md    # Claude Code optimization
├── code-reviewer.md                      # Code review and quality
├── communication-service-agent.md        # Communication microservice
├── content-service-agent.md              # Content microservice  
├── deployment-agent.md                   # DevOps and deployment
├── django-backend-expert.md              # Django backend development
├── identity-service-agent.md             # Identity microservice
├── identity-service-expert.md            # Identity service specialist
├── react-frontend-expert.md              # React frontend development
├── security-compliance-expert.md         # Security and compliance
├── services-coordinator-agent.md         # Microservices coordination
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