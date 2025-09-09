# Claude Code Development Workflow Guide

Comprehensive guide for optimized development workflows using Claude Code with ReactDjango Hub.

## 🎯 **Overview**

This guide provides step-by-step workflows for developing with Claude Code, including agent-specific processes, handoff procedures, and best practices for full-stack development with internationalization and data protection.

## 🚀 **Quick Start Workflow**

### **1. Initial Setup (One-Time)**
```bash
# Clone and setup entire development environment
git clone <repository>
cd ReactDjango-Hub
make claude-dev-setup  # Automated setup script

# Start agent-specific development
make claude-agents      # Opens backend and frontend agent terminals
```

### **2. Daily Development Routine**
```bash
# Morning setup
make dev                # Start development environment
make docker-health      # Verify all services are running

# Start coding session
make claude-agents      # Launch agent terminals
```

## 🔧 **Agent-Specific Workflows**

### **Backend Agent Workflow**

#### **Environment Context**
```bash
# Backend agent operates in: ../ReactDjango-Hub-worktrees/backend-dev
# Focuses on: Django, APIs, database, RGPD compliance, internationalization
```

#### **Development Process**
1. **Start Session**
   ```bash
   # Automatic when using make claude-agents
   cd ../ReactDjango-Hub-worktrees/backend-dev
   git bcommit --help  # Review scoped commit options
   ```

2. **Feature Development**
   ```bash
   # Generate models with compliance
   make generate-model UserProfile
   
   # Create API endpoints
   make generate-api users
   
   # Run tests and compliance checks
   python manage.py test
   make rgpd-check
   ```

3. **Code Quality & Commit**
   ```bash
   # Format and lint
   make claude-format
   
   # Security scan
   make claude-security
   
   # Scoped commit (only backend files)
   git bcommit "feat: add user profile model with RGPD compliance"
   ```

4. **Documentation & Handoff**
   ```bash
   # Update API documentation
   python manage.py spectacular --file backend/docs/api/schema.yml
   
   # Generate TypeScript types for frontend
   python manage.py export_types > frontend/src/api/types.ts
   ```

### **Frontend Agent Workflow**

#### **Environment Context**
```bash
# Frontend agent operates in: ../ReactDjango-Hub-worktrees/frontend-dev
# Focuses on: React, UI/UX, i18n, accessibility, TypeScript
```

#### **Development Process**
1. **Start Session**
   ```bash
   # Check backend API documentation
   cat ../../ReactDjango-Hub/backend/docs/api/README.md
   cat frontend/docs/api/README.md
   ```

2. **Component Development**
   ```bash
   # Generate internationalized components
   make generate-component UserProfileCard
   
   # Start development server
   npm run dev
   
   # Test components
   npm test
   npm run storybook  # If configured
   ```

3. **Internationalization**
   ```bash
   # Update translations
   npm run extract-messages  # Extract new text for translation
   npm run translate          # Update FR/DE/EN translations
   
   # Validate translations
   npm run validate-i18n
   ```

4. **Code Quality & Commit**
   ```bash
   # Lint and type check
   npm run lint
   npm run type-check
   
   # Test accessibility
   npm run test:a11y  # If configured
   
   # Scoped commit (only frontend files)
   git fcommit "feat: add user profile card with French-first UI"
   ```

## 🔄 **Cross-Agent Communication**

### **Backend → Frontend Handoff**

#### **API Changes Workflow**
1. **Backend Agent** develops API endpoint
2. **Backend Agent** updates API documentation:
   ```bash
   # Update backend/docs/api/README.md with new endpoints
   # Generate updated TypeScript types
   # Update OpenAPI schema
   ```
3. **Frontend Agent** integrates new API:
   ```bash
   # Read updated API documentation
   # Import new TypeScript types
   # Update API client and components
   ```

#### **Communication Protocol**
```bash
# Backend Agent announces API changes
git bcommit "feat: add user profile API - ready for frontend integration"

# Include in commit message:
# - New endpoints available
# - TypeScript types updated
# - Breaking changes (if any)
# - Migration guide (if needed)
```

### **Frontend → Backend Feedback**

#### **UI Requirements Workflow**
1. **Frontend Agent** identifies backend needs:
   ```bash
   # Create issue or document requirements
   # Specify needed API endpoints, data structures
   ```
2. **Backend Agent** implements requirements:
   ```bash
   # Develop requested functionality
   # Ensure RGPD compliance
   # Update documentation
   ```

## 🛠️ **Development Patterns**

### **Feature Development Workflow**

#### **1. Feature Planning**
```bash
# Create feature branch (if needed)
git checkout -b feature/user-profiles

# Document feature requirements
# - Backend: API endpoints, models, permissions
# - Frontend: UI components, pages, routing
# - Shared: Data types, validation rules
```

#### **2. Backend-First Approach**
```bash
# Backend Agent starts with data modeling
make generate-model UserProfile

# Create API endpoints
make generate-api user-profiles

# Add business logic and validation
# Implement RGPD compliance
# Write unit tests
```

#### **3. Frontend Integration**
```bash
# Frontend Agent creates UI components
make generate-component UserProfilePage

# Integrate with backend API
# Implement forms and validation
# Add internationalization
# Write component tests
```

#### **4. End-to-End Integration**
```bash
# Test full user workflow
# Validate data flow backend ↔ frontend
# Check internationalization
# Verify RGPD compliance
```

### **Bug Fix Workflow**

#### **1. Bug Identification**
```bash
# Determine which domain (backend/frontend/both)
# Check logs and error messages
# Reproduce issue in development
```

#### **2. Scoped Fix**
```bash
# Backend bugs: Backend Agent fixes with git bcommit
# Frontend bugs: Frontend Agent fixes with git fcommit
# Full-stack bugs: Coordinate between agents
```

#### **3. Testing & Validation**
```bash
# Unit tests for specific fix
# Integration tests for user workflow
# Regression tests for related functionality
```

## 🔍 **Quality Assurance Workflow**

### **Pre-Commit Checks**

#### **Backend Agent Checklist**
```bash
# Code quality
make claude-format      # Format code
make claude-security    # Security scan
make claude-test       # Run tests

# Compliance
make rgpd-check        # RGPD compliance
python manage.py check --deploy  # Django deployment check

# Documentation
# Update API docs if endpoints changed
# Update model documentation if schema changed
```

#### **Frontend Agent Checklist**
```bash
# Code quality
npm run lint           # ESLint
npm run type-check     # TypeScript
npm test              # Unit tests

# Internationalization
npm run validate-i18n  # Translation consistency
npm run test:i18n      # i18n functionality

# Accessibility (if configured)
npm run test:a11y      # Accessibility tests
```

### **Integration Testing**
```bash
# Full stack testing
make test              # Run all tests
make docker-health     # Verify services
```

## 📊 **Monitoring & Optimization**

### **Development Health Monitoring**
```bash
# Check development environment status
make claude-health     # Custom health check script

# Monitor service performance
make docker-logs       # View service logs
make docker-stats      # Resource usage
```

### **Agent Performance Tracking**
```bash
# Track development velocity
# - Time per feature
# - Code quality metrics  
# - Bug fix turnaround
# - Cross-agent coordination efficiency
```

## 🚨 **Troubleshooting Common Issues**

### **Environment Issues**
```bash
# Services not starting
make stop
make clean
make dev

# Database connection issues  
make migrate
docker-compose restart db

# Port conflicts
lsof -i :5173 :8000 :5432 :6379
```

### **Agent Coordination Issues**
```bash
# API integration problems
# 1. Check backend/docs/api/README.md
# 2. Verify TypeScript types are updated
# 3. Test API endpoints manually
# 4. Check CORS configuration

# Translation inconsistencies
npm run validate-i18n
# Fix inconsistent translations
# Update terminology database
```

### **Git Workflow Issues**
```bash
# Wrong files committed
git reset --soft HEAD~1  # Undo last commit
git bcommit              # Use scoped commit

# Merge conflicts between agents
# Resolve in appropriate worktree
# Use scoped commits to avoid conflicts
```

## 📋 **Best Practices**

### **Code Organization**
- **Backend Agent**: Focus on `backend/`, `docker/` (backend-specific), `infrastructure/`
- **Frontend Agent**: Focus on `frontend/`, `docker/` (frontend-specific)
- **Shared Documentation**: Both agents can update `docs/`

### **Communication**
- Use descriptive commit messages
- Update documentation with significant changes
- Include migration guides for breaking changes
- Cross-reference related changes between agents

### **Quality Standards**
- All code must pass automated quality checks
- RGPD compliance is mandatory for data handling
- Internationalization support is required for user-facing features
- Accessibility standards must be met for UI components

### **Development Velocity**
- Use code generators to avoid repetitive tasks
- Maintain comprehensive test coverage
- Automate quality assurance checks
- Keep development environment healthy and fast

---

🎯 **This workflow guide ensures efficient, high-quality development with proper agent coordination and comprehensive quality assurance for full-stack applications with internationalization and data protection compliance.**