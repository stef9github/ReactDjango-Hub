# ADR-005: Generic Building Blocks Architecture

## Status
Proposed

## Context
After analyzing the ChirurgieProX technical specifications, we've identified numerous technical components that are industry-agnostic and should form the foundation of our platform. These components represent common patterns found in most enterprise SaaS applications, regardless of the specific vertical market.

Our current microservices architecture includes:
- 4 FastAPI microservices (identity, communication, content, workflow)
- 1 Django backend service
- 1 React frontend
- Kong API Gateway

We need to decide how to evolve this architecture to support the generic building blocks identified while maintaining clean separation of concerns and enabling easy specialization for different industries.

## Decision

We will implement a **layered microservices architecture** with generic, reusable building blocks that can be specialized through configuration and extension rather than modification.

### Architecture Layers

1. **Infrastructure Layer**
   - API Gateway (Kong)
   - Message Queue (RabbitMQ initially, with abstraction for Kafka migration)
   - Cache Layer (Redis)
   - Search Engine (ElasticSearch)
   - File Storage (S3-compatible)

2. **Core Services Layer** (Microservices)
   - **Identity Service** (existing, enhanced)
   - **Entity Service** (new) - Generic entity management
   - **Scheduling Service** (new) - Universal scheduling
   - **Document Service** (enhanced from content)
   - **Financial Service** (new) - Billing and payments
   - **Notification Service** (enhanced from communication)
   - **Workflow Service** (existing, enhanced)
   - **Search Service** (new) - Advanced search
   - **Analytics Service** (new) - BI and reporting

3. **Business Logic Layer** (Django)
   - Domain-specific logic
   - Business rules engine
   - Data aggregation
   - Complex transactions
   - API orchestration

4. **Presentation Layer**
   - React web application
   - Mobile applications
   - Admin panels
   - Public portals

### Implementation Strategy

#### Phase 1: Service Evolution (Weeks 1-2)
- Enhance existing services to be more generic
- Extract healthcare-specific logic into configuration
- Implement service discovery and health checks

#### Phase 2: New Core Services (Weeks 3-4)
- Build Entity Service as generic CRUD microservice
- Build Scheduling Service with resource management
- Build Financial Service with payment integration

#### Phase 3: Django as Orchestrator (Weeks 5-6)
- Refactor Django to orchestrate microservices
- Implement business rules engine
- Create domain-specific APIs

#### Phase 4: Advanced Services (Weeks 7-8)
- Implement Search Service with ElasticSearch
- Build Analytics Service with dashboard framework
- Add AI/ML integration points

## Consequences

### Positive
- **Reusability**: Building blocks can be used across different industries
- **Scalability**: Each service can scale independently
- **Maintainability**: Clear separation of generic vs. domain-specific code
- **Flexibility**: Easy to add industry-specific features through configuration
- **Speed to Market**: New verticals can be launched quickly using existing blocks
- **Testing**: Generic components can be thoroughly tested once
- **Team Productivity**: Teams can specialize on specific services

### Negative
- **Complexity**: More services to manage and deploy
- **Network Overhead**: Inter-service communication latency
- **Data Consistency**: Distributed transactions are complex
- **Debugging**: Tracing issues across services is harder
- **Initial Development Time**: Building generic solutions takes longer
- **Resource Requirements**: More infrastructure needed

### Risks
- **Over-engineering**: Building too generic might slow initial development
- **Performance**: Multiple service calls might impact response times
- **Migration Complexity**: Moving from current architecture requires careful planning
- **Team Learning Curve**: Developers need to understand microservices patterns

## Alternatives Considered

### Alternative 1: Monolithic Multi-tenant Django
- **Pros**: Simpler deployment, easier transactions, single codebase
- **Cons**: Harder to scale, slower development, harder to customize per vertical
- **Rejected because**: Doesn't align with our microservices strategy

### Alternative 2: Industry-Specific Services
- **Pros**: Optimized for each use case, simpler individual services
- **Cons**: Code duplication, harder maintenance, slower new market entry
- **Rejected because**: Defeats the purpose of building a platform

### Alternative 3: Plugin Architecture
- **Pros**: Single deployment, dynamic extensions, easier management
- **Cons**: Plugin conflicts, harder isolation, security concerns
- **Rejected because**: Less flexible than microservices

## Implementation Plan

### Technical Implementation

1. **Service Template Creation**
```python
# Base service template for all microservices
class BaseService:
    def __init__(self):
        self.setup_database()
        self.setup_cache()
        self.setup_messaging()
        self.setup_monitoring()
        self.register_with_discovery()
```

2. **API Gateway Configuration**
```yaml
# Kong configuration for service routing
services:
  - name: entity-service
    url: http://entity-service:8002
    routes:
      - paths: ['/api/v1/entities']
    plugins:
      - jwt
      - rate-limiting
      - cors
```

3. **Message Bus Implementation**
```python
# Event-driven communication
class EventBus:
    def publish(self, event_type, payload):
        # Publish to RabbitMQ/Kafka
        pass
    
    def subscribe(self, event_type, handler):
        # Subscribe to events
        pass
```

### Migration Strategy

1. **Week 1-2**: Setup infrastructure (Message Queue, ElasticSearch)
2. **Week 3-4**: Create new generic services alongside existing ones
3. **Week 5-6**: Migrate existing services to generic patterns
4. **Week 7-8**: Implement advanced services (Search, Analytics)
5. **Week 9-10**: Testing and optimization
6. **Week 11-12**: Documentation and training

### Success Metrics

- Service response time < 200ms (P95)
- Inter-service communication latency < 50ms
- 80% code reuse across different verticals
- New vertical deployment time < 1 week
- Test coverage > 85% for generic components
- Zero downtime deployments

## Related ADRs

- ADR-001: Microservices Architecture
- ADR-002: API Gateway Selection
- ADR-003: Database per Service
- ADR-004: Authentication Strategy

## References

- [Microservices Patterns](https://microservices.io/patterns/)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [12 Factor App](https://12factor.net/)
- [Building Microservices](https://www.oreilly.com/library/view/building-microservices-2nd/9781492034018/)

---

*Decision Date: September 9, 2025*
*Review Date: October 9, 2025*