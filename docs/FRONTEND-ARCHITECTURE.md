# Frontend Architecture Documentation

## Overview
ReactDjango Hub Medical is a modern medical SaaS platform built with React 18, TypeScript, and Vite. The frontend is designed for French medical practices with HIPAA/RGPD compliance requirements.

## Tech Stack

### Core Technologies
- **React 18.2.0** - Component library with hooks
- **TypeScript 5.3.3** - Type safety and developer experience
- **Vite 5.0.11** - Build tool and dev server
- **Tailwind CSS 4.0.0** - Utility-first CSS framework

### State Management & Data Fetching
- **Zustand 4.4.7** - Lightweight state management
- **React Query (TanStack) 5.17.9** - Server state management and caching
- **Apollo Client 3.8.8** - GraphQL client for advanced queries
- **Axios 1.6.5** - HTTP client for REST API calls

### Routing & Forms
- **React Router DOM 6.21.1** - Client-side routing
- **React Hook Form 7.48.2** - Form management
- **Zod 3.22.4** - Schema validation

### Development & Testing
- **Vitest 3.2.4** - Unit testing framework
- **ESLint** - Code linting and quality
- **PostCSS** - CSS processing

## Project Structure

```
frontend/
├── public/                 # Static assets
├── src/                   # Source code
│   ├── components/        # Reusable UI components
│   ├── pages/            # Page-level components
│   ├── hooks/            # Custom React hooks
│   ├── api/              # API client functions
│   ├── utils/            # Utility functions
│   ├── styles/           # Global styles and themes
│   ├── types/            # TypeScript type definitions
│   ├── contexts/         # React contexts for global state
│   ├── stores/           # Zustand store definitions
│   └── translations/     # i18n translation files
├── index.html            # HTML entry point
├── vite.config.ts        # Vite configuration
├── tsconfig.json         # TypeScript configuration
├── tailwind.config.js    # Tailwind CSS configuration
└── package.json          # Dependencies and scripts
```

## Architecture Patterns

### Component Architecture
- **Atomic Design Pattern**: Components organized by complexity (atoms → molecules → organisms → templates → pages)
- **Functional Components**: All components use hooks-based approach
- **TypeScript First**: Strict typing for all components and props
- **Compound Components**: Complex UI elements broken into composable parts

### State Management Strategy
```typescript
// Global state: Zustand stores
// Server state: React Query
// Local state: useState/useReducer
// Form state: React Hook Form
```

### Data Fetching Architecture
```typescript
// GraphQL queries: Apollo Client
// REST API calls: React Query + Axios
// Real-time updates: WebSocket integration
// Optimistic updates: React Query mutations
```

## Key Features Implementation

### Multi-tenant Architecture
- Tenant context provider for practice isolation
- Route-level tenant validation
- Data fetching with tenant scoping

### HIPAA/RGPD Compliance
- Encrypted data transmission (HTTPS)
- Client-side data sanitization
- Audit logging for user actions
- Session management with secure tokens

### Internationalization (i18n)
- Primary language: French
- Secondary languages: German, English
- React-i18next integration
- Lazy-loaded translation bundles

### Authentication & Authorization
- JWT token management
- Role-based access control (RBAC)
- Multi-factor authentication (2FA)
- Secure session handling

## Configuration

### Environment Variables
```bash
VITE_API_URL=http://localhost:8000/api
VITE_GRAPHQL_URL=http://localhost:8000/graphql
VITE_ENVIRONMENT=development
VITE_TENANT_MODE=multi
```

### Build Configuration
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    watch: { usePolling: true }
  }
})
```

### TypeScript Configuration
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "jsx": "react-jsx",
    "strict": true,
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }
  }
}
```

## Development Workflow

### Scripts
```bash
npm run dev       # Development server
npm run build     # Production build
npm run preview   # Preview production build
npm run test      # Run unit tests
npm run lint      # Code linting
```

### Code Quality
- **ESLint**: Enforces coding standards
- **TypeScript**: Compile-time type checking
- **Vitest**: Unit and integration testing
- **Pre-commit hooks**: Quality gates before commits

## Performance Optimizations

### Bundle Optimization
- Code splitting with React.lazy()
- Tree shaking for unused code
- Dynamic imports for large dependencies
- Asset optimization with Vite

### Runtime Performance
- React.memo for expensive components
- useMemo/useCallback for expensive calculations
- Virtual scrolling for large lists
- Image lazy loading and optimization

## Security Implementation

### Client-side Security
- Input sanitization and validation
- XSS protection through React's built-in escaping
- CSRF protection with token validation
- Secure cookie handling

### Data Protection
- No sensitive data in localStorage
- Encrypted data transmission
- Session timeout management
- Audit trail for all user actions

## Testing Strategy

### Test Types
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **E2E Tests**: Full user workflow testing
- **Accessibility Tests**: WCAG compliance testing

### Testing Tools
```typescript
// Vitest for unit testing
// React Testing Library for component testing
// MSW for API mocking
// Playwright for E2E testing
```

## Deployment Architecture

### Build Process
1. TypeScript compilation
2. Asset optimization
3. Bundle generation
4. Static file preparation

### Production Deployment
- CDN integration for static assets
- Docker containerization
- Kubernetes orchestration
- Health checks and monitoring

## Medical Domain Considerations

### Patient Data Handling
- Encrypted patient identifiers
- Secure form submissions
- Data retention compliance
- Access logging for all patient data

### Clinical Workflow Support
- Real-time appointment updates
- Prescription management UI
- Medical record navigation
- Multi-provider collaboration tools

### Regulatory Compliance
- HIPAA audit trails
- RGPD data handling
- Medical device integration
- Clinical decision support

## Future Architecture Plans

### Planned Enhancements
- Progressive Web App (PWA) capabilities
- Offline-first architecture
- Real-time collaboration features
- AI-powered clinical insights

### Technology Roadmap
- React Server Components adoption
- Micro-frontend architecture
- Advanced GraphQL subscriptions
- Enhanced accessibility features

---

*This documentation reflects the current frontend architecture for ReactDjango Hub Medical SaaS platform.*