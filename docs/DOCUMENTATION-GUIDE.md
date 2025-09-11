# Documentation Guide for ReactDjango Hub

**Last Updated**: September 11, 2025  
**Purpose**: Complete documentation map and guidelines for all agents and developers

## Documentation Architecture Overview

```
ReactDjango-Hub/
├── docs/                           # Primary documentation hub
│   ├── DOCUMENTATION-GUIDE.md      # This file - master guide
│   ├── INDEX.md                    # Complete documentation index
│   ├── README.md                   # Documentation entry point
│   │
│   ├── architecture/               # System architecture & design
│   │   ├── adr/                   # Architecture Decision Records
│   │   ├── agents/                 # Agent-specific implementation guides
│   │   │   ├── backend/           # Backend agent architecture docs
│   │   │   └── frontend/          # Frontend agent architecture docs
│   │   ├── analysis/              # Technical analysis documents
│   │   ├── patterns/              # Design patterns & standards
│   │   └── decisions/             # Technical decisions tracking
│   │
│   ├── products/                   # Vertical-specific documentation
│   │   ├── project-medical-hub/   # Medical Hub (ChirurgieProX)
│   │   └── project-public-hub/    # Public Procurement Hub
│   │
│   ├── development/               # Development guides & workflows
│   ├── testing/                   # Testing strategies & frameworks
│   ├── deployment/                # Infrastructure & deployment
│   ├── compliance/                # Regulatory & compliance docs
│   ├── api/                       # API documentation
│   └── technical-leadership/      # Strategic technical docs
│
├── .claude/                       # Claude agent configuration
│   ├── agents/                    # Agent definitions
│   └── commands/                  # Agent command scripts
│
├── services/                      # Microservices documentation
│   ├── docs/                      # Cross-service documentation
│   ├── identity-service/docs/     # Identity service specific
│   ├── communication-service/     # Communication service docs
│   ├── content-service/          # Content service docs
│   └── workflow-intelligence/    # Workflow service docs
│
├── backend/                       # Django backend documentation
│   └── docs/                      # Backend-specific docs
│
├── frontend/                      # React frontend documentation
│   └── docs/                      # Frontend-specific docs
│
└── infrastructure/                # Infrastructure documentation
    ├── docker/                    # Docker configurations
    └── kubernetes/                # Kubernetes manifests

```

## Documentation Responsibilities by Agent

### Technical Lead Agent (`ag-techlead`)
**Primary Location**: `/docs/architecture/`, `/docs/technical-leadership/`

**Responsibilities**:
- Architecture Decision Records (ADRs) in `/docs/architecture/adr/`
- Technical analysis in `/docs/architecture/analysis/`
- Cross-service patterns in `/docs/architecture/patterns/`
- Strategic roadmaps in `/docs/technical-leadership/`
- Platform architecture documents
- Technology evaluation and selection

**Key Files to Maintain**:
- `/docs/architecture/platform-architecture-v2.md`
- `/docs/architecture/saas-hub-architecture-spec.md`
- `/docs/architecture/implementation-priority-matrix.md`
- All ADRs in `/docs/architecture/adr/`

### Backend Agent (`ag-backend`)
**Primary Location**: `/backend/docs/`, `/docs/architecture/agents/backend/`

**Responsibilities**:
- Django models and API documentation
- Backend implementation guides
- Database schema documentation
- Business logic documentation

**Key Files to Maintain**:
- `/backend/docs/BACKEND_ARCHITECTURE.md`
- `/backend/docs/api/README.md`
- `/docs/architecture/agents/backend/*.md`
- `/docs/architecture/django-multi-vertical-structure.md`

### Frontend Agent (`ag-frontend`)
**Primary Location**: `/frontend/docs/`, `/docs/architecture/agents/frontend/`

**Responsibilities**:
- React component documentation
- Frontend architecture guides
- UI/UX implementation docs
- Internationalization guides

**Key Files to Maintain**:
- `/frontend/docs/FRONTEND-ARCHITECTURE.md`
- `/frontend/COMPONENT_LIBRARY.md`
- `/docs/architecture/agents/frontend/*.md`
- `/docs/architecture/frontend-component-library.md`
- `/docs/architecture/internationalization-architecture.md`

### Service Agents (Identity, Communication, Content, Workflow)
**Primary Location**: `/services/{service-name}/`, `/services/docs/`

**Responsibilities**:
- Service-specific API documentation
- Service implementation details
- Integration patterns with other services
- Service testing documentation

**Key Files to Maintain**:
- `/services/{service-name}/README.md`
- `/services/{service-name}/docs/`
- `/services/docs/SERVICE_INTEGRATION_PATTERNS.md`
- Service-specific CLAUDE.md files

### Services Coordinator Agent (`ag-coordinator`)
**Primary Location**: `/services/docs/`, `/services/api-gateway/`

**Responsibilities**:
- Cross-service integration documentation
- API gateway configuration
- Service discovery and routing
- Inter-service communication patterns

**Key Files to Maintain**:
- `/services/docs/ARCHITECTURE.md`
- `/services/docs/API_INTEGRATION_GUIDE.md`
- `/services/docs/MICROSERVICES_COORDINATION_ACHIEVEMENTS.md`
- `/services/SERVICES_COORDINATION_SUMMARY.md`

### Infrastructure Agent (`ag-infrastructure`)
**Primary Location**: `/infrastructure/`, `/docs/deployment/`

**Responsibilities**:
- Docker and Kubernetes configurations
- Deployment guides and scripts
- Infrastructure as Code documentation
- CI/CD pipeline documentation

**Key Files to Maintain**:
- `/infrastructure/README.md`
- `/infrastructure/docker/README.md`
- `/infrastructure/kubernetes/README.md`
- `/docs/deployment/*.md`
- `/docs/DOCKER_DEPLOYMENT_GUIDE.md`

### Security Agent (`ag-security`)
**Primary Location**: `/docs/compliance/`, `/reviews/`

**Responsibilities**:
- Security policies and procedures
- Compliance documentation
- Security audit reports
- Vulnerability assessments

**Key Files to Maintain**:
- `/docs/compliance/rgpd-compliance.md`
- `/reviews/templates/security-checklist.md`
- Security sections in all service documentation

### Review Agent (`ag-reviewer`)
**Primary Location**: `/reviews/`, `/docs/testing/`

**Responsibilities**:
- Code review standards
- Quality assurance documentation
- Testing strategies
- Performance benchmarks

**Key Files to Maintain**:
- `/reviews/templates/`
- `/docs/testing/agent-testing.md`
- Quality sections in all documentation

## Documentation Standards

### File Naming Conventions

1. **Architecture Decision Records**: `XXX-decision-title.md` (e.g., `001-frontend-architecture-strategy.md`)
2. **Implementation Guides**: `{feature}-implementation-guide.md`
3. **API Documentation**: `API_DOCUMENTATION.md` or `api/README.md`
4. **Service Documentation**: `README.md` at service root, detailed docs in `docs/` subdirectory
5. **Analysis Documents**: `{topic}-analysis.md`

### Document Structure Template

```markdown
# Document Title

**Status**: Draft | In Review | Approved | Deprecated  
**Author**: Agent Name  
**Last Updated**: YYYY-MM-DD  
**Related ADRs**: [ADR-XXX](link), [ADR-YYY](link)

## Executive Summary
Brief overview of the document's purpose and key points

## Context
Background information and problem statement

## [Main Content Sections]
Detailed content organized by logical sections

## Implementation Guidelines
Specific steps or code examples for implementation

## References
- Related documentation
- External resources
- Dependencies

## Revision History
| Date | Version | Changes | Author |
|------|---------|---------|--------|
| YYYY-MM-DD | 1.0 | Initial version | ag-name |
```

### Markdown Standards

1. **Headers**: Use proper hierarchy (# for title, ## for main sections, ### for subsections)
2. **Code Blocks**: Always specify language for syntax highlighting
3. **Links**: Use relative paths for internal docs, absolute URLs for external
4. **Tables**: Use for structured data, keep aligned for readability
5. **Lists**: Use numbered lists for sequential steps, bullets for unordered items
6. **Diagrams**: Use Mermaid for architecture diagrams when possible

## Documentation Update Process

### When Making Code Changes

1. **Before Implementation**:
   - Check existing documentation for the feature/component
   - Review relevant ADRs and architecture docs
   - Update implementation guides if approach changes

2. **During Implementation**:
   - Add inline code comments for complex logic
   - Update API documentation for new/changed endpoints
   - Document configuration changes

3. **After Implementation**:
   - Update relevant README files
   - Add/update integration guides
   - Update testing documentation
   - Create ADR if architectural decision was made

### Documentation Review Checklist

- [ ] Is the documentation in the correct location?
- [ ] Are all code examples tested and working?
- [ ] Are cross-references to other docs accurate?
- [ ] Is the language clear and concise?
- [ ] Are diagrams up-to-date?
- [ ] Is versioning information current?
- [ ] Are related docs updated?

## Cross-Reference Matrix

### Architecture Documentation
| Topic | Primary Location | Related Agents | Key Files |
|-------|-----------------|----------------|-----------|
| Platform Architecture | `/docs/architecture/` | ag-techlead | platform-architecture-v2.md |
| Microservices Design | `/services/docs/` | ag-coordinator | ARCHITECTURE.md |
| Frontend Architecture | `/frontend/docs/` | ag-frontend | FRONTEND-ARCHITECTURE.md |
| Backend Architecture | `/backend/docs/` | ag-backend | BACKEND_ARCHITECTURE.md |
| Deployment Architecture | `/infrastructure/` | ag-infrastructure | docker/, kubernetes/ |

### Vertical-Specific Documentation
| Vertical | Location | Product Manager | Key Files |
|----------|----------|-----------------|-----------|
| Medical Hub | `/docs/products/project-medical-hub/` | ag-surgical-product-manager | ChirurgieProX specs |
| Public Hub | `/docs/products/project-public-hub/` | ag-public-procurement-product-manager | PublicHub specs |

### Service Documentation
| Service | Primary Docs | API Docs | Integration Docs |
|---------|--------------|----------|------------------|
| Identity | `/services/identity-service/` | docs/api/ | /services/docs/JWT_*.md |
| Communication | `/services/communication-service/` | README.md | /services/docs/API_*.md |
| Content | `/services/content-service/` | README.md | TECHNICAL_SPECIFICATIONS.md |
| Workflow | `/services/workflow-intelligence-service/` | docs/API_TESTING.md | AI_ARCHITECTURE.md |

## Documentation Maintenance Schedule

### Daily Updates
- Code changes must include documentation updates
- API changes require immediate documentation

### Weekly Reviews
- Review and update implementation status
- Update roadmap documents
- Clean up outdated TODOs

### Monthly Audits
- Full documentation consistency check
- Update architecture diagrams
- Review and archive deprecated docs

### Quarterly Reviews
- Major architecture documentation updates
- ADR reviews and updates
- Documentation structure reorganization if needed

## Quick Links to Key Documents

### Getting Started
- [Project Overview](/docs/README.md)
- [Development Setup](/docs/development/setup.md)
- [Agent Configuration](/.claude/agents/README.md)

### Architecture
- [Platform Architecture](/docs/architecture/platform-architecture-v2.md)
- [ADR Index](/docs/architecture/adr/)
- [Service Integration](/services/docs/SERVICE_INTEGRATION_PATTERNS.md)

### Implementation
- [Backend Guide](/backend/docs/BACKEND_ARCHITECTURE.md)
- [Frontend Guide](/frontend/docs/FRONTEND-ARCHITECTURE.md)
- [Service Coordination](/services/docs/MICROSERVICES_COORDINATION_ACHIEVEMENTS.md)

### Deployment
- [Docker Guide](/docs/DOCKER_DEPLOYMENT_GUIDE.md)
- [Infrastructure Setup](/infrastructure/README.md)
- [CI/CD Pipeline](/docs/deployment/)

## Documentation Tools and Scripts

### Available Scripts
```bash
# Generate documentation index
./scripts/generate-doc-index.sh

# Check documentation links
./scripts/check-doc-links.sh

# Update documentation timestamps
./scripts/update-doc-timestamps.sh
```

### Documentation Generation
- API docs auto-generated from OpenAPI specs
- Component docs from JSDoc/TSDoc comments
- Database schema from Django models

## Contact and Support

For documentation questions or improvements:
- Create an issue with `documentation` label
- Contact the relevant agent through Claude Code
- Review the [Agent Documentation](/.claude/AGENTS_DOCUMENTATION.md)

---

**Note**: This guide is the authoritative source for documentation organization. All agents should refer to this guide when creating or updating documentation.