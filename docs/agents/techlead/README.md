# Technical Lead Agent Documentation

**Agent**: ag-techlead  
**Domain**: Architecture, Strategic Planning, Technical Leadership  
**Last Updated**: September 11, 2025

## Overview

This directory contains documentation maintained by the Technical Lead agent, focusing on strategic technical decisions, architectural patterns, and cross-cutting concerns.

## Documentation Structure

```
techlead/
├── README.md                    # This file
├── decisions/                   # Strategic technical decisions
├── evaluations/                # Technology evaluations
├── patterns/                   # Cross-cutting patterns
├── debt-analysis/              # Technical debt tracking
└── roadmaps/                   # Technical roadmaps
```

## Key Documents

### Architecture & Design
- [Platform Architecture](/docs/architecture/platform-architecture-v2.md)
- [Architecture Decision Records](/docs/architecture/adr/)
- [Common Platform Patterns](/docs/architecture/common-platform-patterns.md)

### Strategic Planning
- [Implementation Priority Matrix](/docs/architecture/implementation-priority-matrix.md)
- [Implementation Roadmap](/docs/architecture/implementation-roadmap.md)
- [Service Enhancement Roadmaps](/docs/architecture/service-enhancement-roadmap.md)

### Technical Analysis
- [Frontend Architecture Analysis](/docs/technical-leadership/frontend-architecture-analysis.md)
- [Generic Building Blocks](/docs/architecture/analysis/generic-technical-building-blocks.md)

## Current Focus Areas

### Q4 2025 Priorities

1. **Microservices Architecture Evolution**
   - Service mesh evaluation
   - API versioning strategy
   - Event-driven architecture design

2. **Performance & Scalability**
   - Caching strategy optimization
   - Database sharding planning
   - Load testing framework

3. **Technical Debt Management**
   - Legacy code migration plan
   - Dependency updates strategy
   - Code quality improvements

4. **Security Architecture**
   - Zero-trust architecture evaluation
   - Secrets management improvement
   - Security automation

## Decision Log

Recent strategic decisions:

| Date | Decision | ADR | Status |
|------|----------|-----|--------|
| 2025-09-11 | Internationalization Architecture | [ADR-002](/docs/architecture/adr/002-internationalization-strategy.md) | Approved |
| 2025-09-11 | Generic Building Blocks | [ADR-005](/docs/architecture/adr/005-generic-building-blocks-architecture.md) | Approved |
| 2025-09-11 | Event System Architecture | [ADR-006](/docs/architecture/adr/006-time-based-event-system-architecture-REVISED.md) | Approved |

## Technology Evaluations

### Under Evaluation
- **Message Queue**: Kafka vs RabbitMQ vs Redis Streams
- **Service Mesh**: Istio vs Linkerd vs Kong Mesh
- **Observability**: Datadog vs New Relic vs Open Source Stack

### Approved Technologies
- **API Gateway**: Kong
- **Container Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions
- **Cloud Provider**: AWS

## Cross-Agent Coordination

### Documentation Dependencies
- Provides architectural guidance to all agents
- Reviews technical proposals from service agents
- Coordinates with ag-infrastructure on deployment architecture
- Collaborates with ag-security on security architecture

### Key Interfaces
- `/docs/architecture/agents/` - Agent-specific implementation guides
- `/services/docs/` - Service integration patterns
- `/.claude/agents/` - Agent configuration and boundaries

## Best Practices

### For Architecture Documentation
1. Always create ADRs for significant decisions
2. Include context, alternatives, and consequences
3. Link related documentation
4. Update implementation guides when decisions change

### For Technology Evaluation
1. Document evaluation criteria
2. Include proof-of-concept results
3. Consider total cost of ownership
4. Assess team expertise requirements

### For Technical Debt
1. Quantify impact and effort
2. Prioritize based on risk
3. Create actionable remediation plans
4. Track progress regularly

## Resources

### Internal Documentation
- [Documentation Guide](/docs/DOCUMENTATION-GUIDE.md)
- [Agent System Overview](/.claude/AGENTS_DOCUMENTATION.md)
- [Platform Architecture](/docs/architecture/platform-architecture-v2.md)

### External Resources
- [Microservices Patterns](https://microservices.io/patterns/)
- [12 Factor App](https://12factor.net/)
- [Domain-Driven Design](https://dddcommunity.org/)

## Contact

For technical leadership questions:
- Review existing ADRs and documentation
- Consult the ag-techlead agent via Claude Code
- Check the [Technical Leadership](/docs/technical-leadership/) directory

---

**Maintained by**: ag-techlead  
**Review Schedule**: Weekly architecture reviews, Monthly strategic planning