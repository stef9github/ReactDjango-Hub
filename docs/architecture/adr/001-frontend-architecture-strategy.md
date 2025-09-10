# ADR-001: Frontend Architecture Strategy for Microservices Platform

## Status
**Accepted** - December 2024

## Context

The ReactDjango Hub platform has evolved from a monolithic Django application to a microservices architecture with:
- **Identity Service** (FastAPI, Port 8001) - 100% production-ready with 40+ endpoints
- **Backend Service** (Django, Port 8000) - Business logic integration with identity service
- **Frontend** (React + Vite) - Must connect to multiple services
- **Future Services** - Communication, Content, and Workflow services planned

The existing architecture specification (`saas-hub-architecture-spec.md`) describes an ambitious monorepo structure with 4 microservices and Kong API Gateway. However, our current reality is:
1. We have 2 working services (identity + Django backend)
2. No Kong Gateway is currently deployed
3. Frontend needs immediate architectural decisions for multi-service integration

## Decision

We will adopt a **pragmatic, incremental frontend architecture** that:

### 1. **Service-Oriented API Layer**
Create a unified API client architecture that abstracts service communication:
```typescript
// Single point of configuration for all services
const apiConfig = {
  identity: import.meta.env.VITE_IDENTITY_SERVICE_URL || 'http://localhost:8001',
  backend: import.meta.env.VITE_BACKEND_SERVICE_URL || 'http://localhost:8000',
  // Future services can be added here
};
```

### 2. **Modular Component Architecture**
Organize components by business domain, not by service:
```
src/
├── features/           # Business domain features
│   ├── auth/          # Authentication (uses identity service)
│   ├── users/         # User management (uses identity + backend)
│   ├── dashboard/     # Dashboard (aggregates from multiple services)
│   └── settings/      # Settings (cross-service configuration)
├── shared/            # Shared components across features
│   ├── components/    # Reusable UI components
│   ├── hooks/         # Shared React hooks
│   └── utils/         # Utility functions
└── services/          # Service integration layer
    ├── api/           # API client implementations
    ├── auth/          # Authentication management
    └── state/         # Global state management
```

### 3. **State Management Strategy**
Use **TanStack Query** for server state and **Zustand** for client state:
- Server state managed by TanStack Query with proper caching strategies
- Client state (UI, preferences) managed by Zustand
- No Redux unless complexity demands it

### 4. **Authentication Architecture**
Implement a **unified authentication flow** that:
- Authenticates via identity service (port 8001)
- Shares JWT tokens across all service calls
- Implements automatic token refresh
- Provides centralized logout

### 5. **Progressive Enhancement Strategy**
Start simple and evolve:
- **Phase 1**: Direct service calls from frontend
- **Phase 2**: Add API Gateway when needed (Kong/custom)
- **Phase 3**: Implement service mesh if scale demands

### 6. **Multi-App Style Guide Architecture**
Establish a scalable design system for multiple microservice UIs:
- **Shared Design Tokens**: Centralized theme variables and design primitives
- **Component Library Strategy**: Monorepo or published npm packages for shared components
- **Per-Service Customization**: Service-specific theme extensions while maintaining brand consistency
- **Style Isolation**: CSS modules or CSS-in-JS to prevent style conflicts between micro-apps

### 7. **Internationalization (i18n) Architecture**
Implement comprehensive multi-language support:
- **Library Selection**: React-i18next for robust i18n with lazy loading and namespacing
- **Translation Management**: Structured key namespacing per service/feature
- **Dynamic Locale Switching**: Runtime language changes without page reload
- **Format Standardization**: ICU Message Format for complex translations

### 8. **Localization (l10n) Implementation**
Practical localization patterns for global readiness:
- **Locale-Aware Formatting**: Date, time, number, and currency formatting via Intl API
- **RTL/LTR Support**: Bidirectional text support with CSS logical properties
- **Content Delivery**: CDN-based translation file delivery with caching
- **Fallback Strategy**: Graceful degradation for missing translations

## Consequences

### Positive
- **Immediate Implementation**: Can start building with current services
- **Flexibility**: Easy to add new services as they're developed
- **Simplicity**: No over-engineering for current scale
- **Developer Experience**: Clear patterns and structure
- **Type Safety**: Full TypeScript coverage with generated types
- **Performance**: Optimized bundle sizes with code splitting
- **Global Readiness**: Built-in i18n/l10n support from the start
- **Design Consistency**: Unified design system across all microservice UIs
- **Scalable Styling**: Component library supports growing number of services

### Negative
- **No API Gateway Initially**: Must handle CORS and service discovery in frontend
- **Service Coupling**: Frontend knows about individual services
- **Refactoring Later**: Will need to update when gateway is added
- **Duplicate Logic**: Some cross-service logic in frontend initially
- **Translation Overhead**: Managing translations across multiple services
- **Component Library Maintenance**: Requires dedicated effort to maintain shared components
- **i18n Complexity**: Pluralization and context-aware translations add complexity

### Risks
- **Service Discovery**: If services move, frontend needs updates
- **CORS Complexity**: Multiple origins require proper CORS setup
- **Token Management**: Must be careful with JWT storage and refresh
- **Error Handling**: Need consistent error handling across services

## Alternatives Considered

### 1. **Full Monorepo with Nx/Turborepo**
- **Pros**: Shared code, consistent tooling, atomic commits
- **Cons**: Complex setup, steeper learning curve, overkill for current size
- **Decision**: Defer until team grows beyond 5 developers

### 2. **GraphQL Federation**
- **Pros**: Single endpoint, flexible queries, type safety
- **Cons**: Additional complexity, learning curve, service overhead
- **Decision**: Reconsider when we have 4+ services

### 3. **Backend-for-Frontend (BFF)**
- **Pros**: Single backend endpoint, aggregation logic
- **Cons**: Another service to maintain, potential bottleneck
- **Decision**: Implement if frontend-specific logic becomes complex

### 4. **Micro-Frontends**
- **Pros**: Independent deployment, team autonomy
- **Cons**: Complexity overhead, performance concerns
- **Decision**: Not needed until we have multiple frontend teams

## Implementation Plan

### Phase 1: Foundation (Current)
1. ✅ Set up React + Vite + TypeScript
2. ✅ Implement identity service integration
3. ⏳ Create unified API client architecture
4. ⏳ Implement authentication flow
5. ⏳ Set up TanStack Query + Zustand
6. ⏳ Establish design token system
7. ⏳ Configure i18n with react-i18next

### Phase 2: Service Integration (Next 2 weeks)
1. Generate TypeScript types from OpenAPI specs
2. Implement service-specific API clients
3. Create cross-service data aggregation hooks
4. Build error boundary architecture
5. Implement comprehensive error handling
6. Set up component library with Storybook
7. Implement multi-language support (5 initial languages)

### Phase 3: Production Readiness (Next month)
1. Add comprehensive testing (unit, integration, e2e)
2. Implement performance monitoring
3. Set up error tracking (Sentry)
4. Create build optimization pipeline
5. Document component library
6. Implement RTL support for Arabic
7. Set up translation management workflow
8. Configure CDN for localized assets

### Phase 4: Scale Preparation (Future)
1. Evaluate and implement API Gateway
2. Consider service mesh for observability
3. Implement advanced caching strategies
4. Add real-time capabilities (WebSocket/SSE)
5. Evaluate micro-frontend architecture

## Metrics for Success

- **Developer Velocity**: New features shipped per sprint
- **Bundle Size**: < 200KB initial, < 500KB total
- **Performance**: FCP < 1.5s, TTI < 3.5s
- **Type Coverage**: 100% TypeScript coverage
- **Test Coverage**: > 80% for critical paths
- **Error Rate**: < 0.1% in production

## References

- [Martin Fowler - Microservices](https://martinfowler.com/articles/microservices.html)
- [Frontend Architecture for Microservices](https://micro-frontends.org/)
- [TanStack Query Documentation](https://tanstack.com/query)
- [Zustand State Management](https://github.com/pmndrs/zustand)

---

**Decision made by**: Technical Lead Agent  
**Date**: December 10, 2024  
**Review date**: January 10, 2025