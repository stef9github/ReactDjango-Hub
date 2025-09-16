# ADR-010: Local-First Development Strategy

## Status
**Accepted** - September 13, 2025

## Context

### Background
The ReactDjango Hub platform is in active development with multiple microservices (Identity, Communication, Content, Workflow, Django Backend, React Frontend). ADR-009 proposed a hybrid containerization strategy to balance developer experience with production consistency.

### Current Development Challenges
After evaluating our development workflow with Claude Code and other AI-assisted development tools, we've identified significant friction points:

1. **AI Agent Efficiency**: Claude Code and similar AI agents work most effectively with direct file system access. Container abstractions add unnecessary complexity for AI-driven development.

2. **Development Velocity**: Container rebuilds, volume mounting issues, and networking complexity slow down the rapid iteration cycles essential for early-stage development.

3. **Debugging Complexity**: Debugging containerized applications requires additional tooling and commands (docker exec, container logs, remote debugging setup) that impede quick problem resolution.

4. **Onboarding Overhead**: New developers and AI agents need to understand Docker concepts, networking, and container orchestration before being productive.

5. **Premature Optimization**: The platform is not yet at a stage where the benefits of containerization (production parity, resource isolation) outweigh the development costs.

### Critical Insight
**Development velocity and simplicity are paramount during the active development phase.** The ability to quickly iterate, test, and debug is more valuable than production parity at this stage of the project.

## Decision

### Primary Decision: **Local-First Development Strategy**

We will adopt a **local-first development approach** for all services during the active development phase:

#### Development Environment (Primary Focus)
- **All Services**: Run directly on the host machine without containers
- **Databases**: Use locally installed PostgreSQL instances
- **Redis**: Use locally installed Redis or skip for development
- **API Gateway**: Optional - direct service-to-service communication for development
- **Frontend**: Direct npm/yarn execution with hot module replacement

#### Production Environment (Future Consideration)
- **Containerization**: Will be reconsidered when platform reaches production maturity
- **Deployment Strategy**: To be determined based on actual production requirements
- **Infrastructure**: Cloud-native deployment patterns can be adopted later

### Implementation Guidelines

#### 1. Service Startup Simplification

**Current Simplified Workflow**
```bash
# Terminal 1: PostgreSQL (if not already running as system service)
postgres -D /usr/local/var/postgres

# Terminal 2: Identity Service
cd services/identity-service
source venv/bin/activate
pip install -r requirements.txt
python main.py

# Terminal 3: Django Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Terminal 4: Frontend
cd frontend
npm install
npm run dev
```

#### 2. Database Configuration

**Local PostgreSQL Setup**
```bash
# Install PostgreSQL locally (once)
brew install postgresql@17  # macOS
sudo apt install postgresql-17  # Ubuntu
sudo yum install postgresql17-server  # RHEL/CentOS

# Create databases for each service
createdb identity_service_db
createdb django_backend_db
createdb communication_service_db
createdb content_service_db
createdb workflow_service_db

# Services connect via localhost
DATABASE_URL=postgresql://localhost/identity_service_db
```

#### 3. Service Communication

**Direct Service Communication**
```python
# Services communicate directly via localhost ports
IDENTITY_SERVICE_URL = "http://localhost:8001"
BACKEND_SERVICE_URL = "http://localhost:8000"
COMMUNICATION_SERVICE_URL = "http://localhost:8003"
CONTENT_SERVICE_URL = "http://localhost:8002"
WORKFLOW_SERVICE_URL = "http://localhost:8004"
```

#### 4. Environment Management

**Simple .env Files**
```bash
# Each service has a simple .env file
# services/identity-service/.env
DATABASE_URL=postgresql://localhost/identity_service_db
PORT=8001
DEBUG=True

# backend/.env
DATABASE_URL=postgresql://localhost/django_backend_db
IDENTITY_SERVICE_URL=http://localhost:8001
DEBUG=True
```

## Consequences

### Positive Consequences

1. **Maximized Development Velocity**
   - Instant code changes without rebuild cycles
   - Direct debugging with native tools
   - Immediate test execution
   - No container overhead

2. **Simplified AI Agent Integration**
   - Claude Code can directly manipulate files
   - No Docker commands needed in agent workflows
   - Simpler mental model for AI agents
   - Faster feedback loops for AI-assisted development

3. **Reduced Complexity**
   - No Docker networking issues
   - No volume mounting problems
   - No container orchestration complexity
   - Simple, standard development tools

4. **Improved Developer Experience**
   - Familiar development environment
   - Native IDE integration
   - Direct database access for debugging
   - Standard debugging tools work immediately

5. **Lower Barrier to Entry**
   - New developers productive immediately
   - No Docker/Kubernetes knowledge required
   - Focus on business logic, not infrastructure
   - Simpler onboarding documentation

### Negative Consequences

1. **Environment Differences**
   - Development differs from eventual production
   - Potential for "works on my machine" issues
   - Need to test production builds separately

2. **Dependency Management**
   - Developers must manage local service versions
   - Potential for version conflicts
   - Need clear documentation of requirements

3. **Future Migration Effort**
   - Will need to containerize for production eventually
   - Technical debt accumulation
   - Potential rework of deployment scripts

### Risk Mitigation

1. **Version Management**
   - Use pyenv/nvm for consistent language versions
   - Document exact version requirements
   - Use virtual environments for Python isolation
   - Regular dependency updates

2. **Environment Consistency**
   - Detailed setup documentation
   - Automated setup scripts where possible
   - Regular team sync on environment changes
   - CI/CD tests on clean environments

3. **Production Readiness**
   - Maintain containerization as future option
   - Keep infrastructure code modular
   - Plan for gradual containerization when needed
   - Document production requirements early

## Alternatives Considered

### Alternative 1: Full Containerization (ADR-009 Approach)
**Rejected because:** Significantly impedes development velocity and AI agent effectiveness during active development phase.

### Alternative 2: Hybrid Approach (Some Services Containerized)
**Rejected because:** Adds complexity without clear benefits; inconsistent developer experience.

### Alternative 3: Development Containers (Dev Containers/Codespaces)
**Rejected because:** Still adds container overhead; limits local tool usage; complicates AI agent integration.

## Implementation Plan

### Phase 1: Documentation Update (Immediate)
1. Update CLAUDE.md to reflect local-first approach
2. Remove Docker commands from primary development workflow
3. Update agent instructions to use local commands
4. Create simple setup guides for each service

### Phase 2: Simplification (Week 1)
1. Create setup scripts for local PostgreSQL databases
2. Simplify environment configuration
3. Remove Docker-specific configuration from development
4. Update CI/CD to test local development patterns

### Phase 3: Developer Experience (Week 2)
1. Create automated setup scripts
2. Improve error messages for missing dependencies
3. Add health check endpoints for service discovery
4. Document troubleshooting guide

### Phase 4: Future Planning (Ongoing)
1. Monitor when containerization becomes necessary
2. Keep deployment patterns modular
3. Plan gradual migration path to containers
4. Maintain production deployment options

## Success Metrics

1. **Development Velocity**
   - Time from code change to test: < 2 seconds
   - New developer setup time: < 15 minutes
   - AI agent task completion: 50% faster

2. **Developer Satisfaction**
   - Reduced complexity complaints
   - Faster feature delivery
   - Improved debugging efficiency

3. **Code Quality**
   - Maintain test coverage > 80%
   - No increase in environment-related bugs
   - Consistent code review velocity

## Review Schedule

- **1 month**: Evaluate development velocity improvements
- **3 months**: Assess if containerization needs have emerged
- **6 months**: Review production deployment requirements
- **As needed**: When platform approaches production readiness

## Decision Makers

- **Technical Lead**: Architecture approval and strategy alignment
- **Development Team**: Validation of improved developer experience
- **Product Owner**: Confirmation of improved delivery velocity

## Migration Path to Containerization

When the platform reaches maturity and containerization becomes necessary:

1. **Gradual Adoption**: Start with stateless services
2. **Production First**: Containerize for production while maintaining local development
3. **Optional Containers**: Provide Docker as optional development environment
4. **Full Migration**: Only when benefits clearly outweigh costs

## References

- [The Cost of Containerization in Development](https://www.thoughtworks.com/insights/blog/containerization-development)
- [Local Development Best Practices](https://12factor.net/dev-prod-parity)
- [AI-Assisted Development Patterns](https://github.com/features/copilot)
- [Pragmatic Architecture Decisions](https://www.infoq.com/articles/architecture-pragmatic/)

---

**Created**: September 2025
**Next Review**: January 2025
**Status**: Active - Supersedes ADR-009

## Summary

This ADR establishes a local-first development strategy that prioritizes development velocity and simplicity during the active development phase of the ReactDjango Hub platform. By removing containerization complexity from the development workflow, we enable faster iteration, better AI agent integration, and improved developer experience. Containerization remains a future option for production deployment when the platform reaches appropriate maturity.