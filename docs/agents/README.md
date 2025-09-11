# Agent-Specific Documentation

This directory contains documentation spaces for each Claude Code agent. Each agent maintains their own documentation related to their specific domain and responsibilities.

## Agent Documentation Structure

```
agents/
├── README.md              # This file
├── overview.md           # Agent system overview
├── techlead/            # Technical Lead documentation
├── backend/             # Backend agent documentation
├── frontend/            # Frontend agent documentation
├── identity/            # Identity service documentation
├── communication/       # Communication service documentation
├── content/            # Content service documentation
├── workflow/           # Workflow service documentation
├── coordinator/        # Service coordination documentation
├── infrastructure/     # Infrastructure agent documentation
├── security/           # Security agent documentation
└── reviewer/           # Code review agent documentation
```

## Documentation Guidelines for Agents

### What Goes Here

Each agent should maintain in their directory:

1. **Design Decisions**: Domain-specific architectural decisions
2. **Implementation Guides**: How-to guides for their domain
3. **Best Practices**: Standards and patterns for their area
4. **Integration Notes**: How their domain integrates with others
5. **Troubleshooting**: Common issues and solutions in their domain

### What Doesn't Go Here

- General architecture decisions → `/docs/architecture/adr/`
- Service implementation code documentation → `/services/{service-name}/docs/`
- Frontend/Backend specific code docs → `/frontend/docs/` or `/backend/docs/`
- Product/vertical specific docs → `/docs/products/`

## Agent Directory Purposes

### Technical Lead (`/techlead/`)
- Strategic technical decisions
- Cross-cutting architectural patterns
- Technology evaluation reports
- Technical debt analysis

### Backend (`/backend/`)
- Django-specific patterns
- Backend integration guides
- Data model documentation
- Business logic patterns

### Frontend (`/frontend/`)
- React component patterns
- UI/UX implementation guides
- State management strategies
- Frontend performance guides

### Service Agents (`/identity/`, `/communication/`, `/content/`, `/workflow/`)
- Service-specific architecture
- API design documentation
- Service integration patterns
- Service-level best practices

### Coordinator (`/coordinator/`)
- Service orchestration patterns
- API gateway configuration
- Inter-service communication
- Service mesh documentation

### Infrastructure (`/infrastructure/`)
- Deployment strategies
- Infrastructure patterns
- CI/CD documentation
- Monitoring and logging

### Security (`/security/`)
- Security policies
- Vulnerability assessments
- Compliance documentation
- Security best practices

### Reviewer (`/reviewer/`)
- Code review standards
- Quality metrics
- Review checklists
- Performance benchmarks

## Cross-References

For complete documentation navigation, see:
- [Documentation Guide](/docs/DOCUMENTATION-GUIDE.md)
- [Documentation Index](/docs/INDEX.md)
- [Agent System Documentation](/.claude/AGENTS_DOCUMENTATION.md)

---

**Note**: Each agent is responsible for maintaining their own documentation directory. Keep documentation up-to-date with code changes.