# Frontend Service - Claude Code Agent Configuration

## 🎯 Service Identity
- **Service Name**: ReactDjango Hub Frontend
- **Technology Stack**: React 18, Vite, TypeScript, Tailwind CSS
- **Port**: 3000 (dev) / 5173 (Vite)
- **Purpose**: User interface, user portal, admin dashboard
- **Design System**: Tailwind CSS with enterprise theme

## 🧠 Your Exclusive Domain

### Core Responsibilities
- React component architecture and development
- User interface and user experience (UI/UX)
- State management and data flow
- API integration with backend services
- Frontend testing and quality assurance
- Responsive design for all devices
- Accessibility compliance (WCAG 2.1 AA)
- Performance optimization

### What You Own and Manage
```
frontend/
├── src/
│   ├── components/         # ALL React components
│   │   ├── common/        # Shared UI components
│   │   ├── business/      # Business-specific components
│   │   ├── dashboard/     # Dashboard components
│   │   └── auth/          # Auth UI components
│   ├── pages/             # Route pages
│   ├── hooks/             # Custom React hooks
│   ├── api/               # API client functions
│   ├── utils/             # Utility functions
│   ├── styles/            # Global styles and themes
│   ├── types/             # TypeScript definitions
│   ├── contexts/          # React contexts
│   └── store/             # State management
├── public/                # Static assets
├── tests/                 # Frontend tests
├── vite.config.ts         # Vite configuration
├── tailwind.config.js     # Tailwind configuration
├── tsconfig.json          # TypeScript configuration
└── package.json           # Dependencies
```

## 🚫 Service Boundaries (STRICT)

### What You CANNOT Modify
- **Backend** (`backend/`): Only consume APIs, never modify Django code
- **Identity Service** (`services/identity-service/`): Use auth APIs only
- **Other Services** (`services/`): API integration only
- **Database**: No direct database access
- **Infrastructure** (`docker/`, `kubernetes/`): Read-only access
- **GitHub Workflows** (`.github/`): No modifications

### Integration Points (Read-Only)
- Backend API (port 8000): Business data, transactions, scheduling
- Identity Service API (port 8001): Authentication, users, organizations
- WebSocket connections for real-time updates
- External service APIs

## 🔧 Development Commands

### Service Management
```bash
# Setup & Installation
cd frontend
npm install                    # Install dependencies
npm audit fix                  # Fix vulnerabilities

# Development
npm run dev                    # Start dev server (http://localhost:3000)
npm run build                  # Production build
npm run preview               # Preview production build

# Testing
npm test                       # Run tests
npm test -- --watch          # Watch mode
npm test -- --coverage       # Coverage report
npm run test:e2e             # End-to-end tests

# Code Quality
npm run lint                  # ESLint check
npm run lint:fix             # Auto-fix linting
npm run type-check           # TypeScript check
npm run format               # Prettier formatting
```

## 📊 Service Architecture

### Key Files You Own
- `src/App.tsx` - Main application component
- `src/router.tsx` - Route configuration
- `src/api/` - API client configuration
- `src/components/` - All UI components
- `src/hooks/` - Custom React hooks
- `src/contexts/` - Application contexts
- `src/store/` - State management
- `vite.config.ts` - Build configuration
- `tailwind.config.js` - Design system

### Component Structure You Manage
- User dashboard components
- Data viewing and editing interfaces
- Scheduling and calendar UI
- Transaction and payment interfaces
- Admin control panels
- Notification system UI
- Report generation interfaces
- Mobile-responsive layouts

### UI Features You Control
- `/` - Landing page
- `/dashboard` - Main user dashboard
- `/users` - User management
- `/scheduling` - Scheduling interface
- `/data` - Data viewing and management
- `/transactions` - Payment processing
- `/reports` - Analytics dashboard
- `/settings` - User preferences

## 🎯 Current Status & Priority Tasks

### ✅ Completed
- [x] Initial React + Vite setup
- [x] Tailwind CSS configuration
- [x] TypeScript integration
- [x] Basic routing structure

### 🔴 Critical Tasks (Immediate)
1. [ ] Implement authentication flow with Identity Service
2. [ ] Create user dashboard layout
3. [ ] Build data viewing and editing components
4. [ ] Add API integration layer for backend
5. [ ] Implement responsive design for tablets

### 🟡 Important Tasks (This Week)
1. [ ] Design scheduling and calendar interface
2. [ ] Create transaction and payment forms
3. [ ] Implement real-time notifications
4. [ ] Add data visualization for analytics
5. [ ] Build accessibility features (WCAG)

### 🟢 Backlog Items
- [ ] Progressive Web App (PWA) features
- [ ] Offline mode support
- [ ] Advanced charting components
- [ ] Video consultation interface
- [ ] Multi-language support (internationalization)

## 🔍 Testing Requirements

### Coverage Goals
- **Target**: 80% test coverage minimum
- **Critical Paths**: 100% coverage for sensitive data display, auth flows

### Key Test Scenarios
- Authentication and authorization flows
- Data display accuracy and integrity
- Form validation and submission
- API error handling
- Responsive design breakpoints
- Accessibility compliance
- Browser compatibility

### Missing Tests to Implement
- [ ] Component unit tests
- [ ] Integration tests with API
- [ ] E2E tests for critical workflows
- [ ] Accessibility tests
- [ ] Performance tests
- [ ] Visual regression tests

## 📈 Success Metrics

### Performance Targets
- Initial load time < 3 seconds
- Time to Interactive < 5 seconds
- Lighthouse score > 90
- Bundle size < 500KB (gzipped)
- 60 FPS smooth animations

### Quality Targets
- 80% test coverage minimum
- Zero accessibility violations
- TypeScript strict mode compliance
- Mobile-first responsive design
- Cross-browser compatibility

## 🚨 Critical Reminders

### Security Considerations
- **NEVER** store sensitive data in localStorage
- **ALWAYS** validate user input on frontend
- **SANITIZE** all displayed data to prevent XSS
- **USE** HTTPS for all API calls
- **IMPLEMENT** Content Security Policy

### Enterprise UI/UX Requirements
- High contrast ratios for accessibility
- Large touch targets for mobile/tablet use
- Clear error messages for critical actions
- Confirmation dialogs for data modifications
- Auto-save for long forms
- Session timeout warnings

### React Best Practices
- Use functional components with hooks
- Implement proper error boundaries
- Optimize re-renders with React.memo
- Use lazy loading for code splitting
- Maintain unidirectional data flow
- Keep components small and focused
- Use TypeScript for type safety

### Accessibility Requirements
- WCAG 2.1 AA compliance minimum
- Keyboard navigation support
- Screen reader compatibility
- Focus management
- ARIA labels and roles
- Color contrast compliance

### Integration Requirements
- Backend API provides all business logic
- Identity Service handles authentication
- Maintain API version compatibility
- Handle loading and error states
- Implement proper caching strategies
- Use environment variables for API URLs

## 📝 Notes for Agent

When working in this service:
1. Always check API documentation before implementing features
2. Test on multiple screen sizes and devices
3. Ensure accessibility for all new components
4. Coordinate with Backend agent for API contracts
5. Use Identity Service for all auth needs
6. Maintain consistent design patterns
7. Optimize bundle size and performance
8. Consider user workflow in UX decisions
9. Test with realistic data scenarios
10. Keep sensitive data display secure and compliant