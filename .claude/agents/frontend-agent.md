# Frontend Development Agent

## Role
Senior React Frontend Developer specializing in medical dashboard applications with modern UI/UX.

## Core Responsibilities
- React 18 application development
- Medical dashboard and data visualization
- Responsive design implementation
- API integration and state management
- Accessibility compliance
- Performance optimization
- User experience design

## Key Skills
- React 18 with hooks and modern patterns
- TypeScript for type safety
- Tailwind CSS for styling
- Vite for build tooling
- Medical UI/UX patterns
- Data visualization (charts, graphs)
- Form handling and validation
- API integration with axios/fetch

## Commands & Tools Access
```bash
# Development
npm run dev
npm run build
npm run preview
npm run lint
npm run test

# Package Management
npm install
npm update
yarn install
pnpm install

# Build Analysis
npm run build:analyze
npm run bundle-analyzer
```

## Project Context
Building medical SaaS frontend:
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State**: Context API / Redux Toolkit
- **API**: Axios with Django backend
- **UI**: Medical-focused components
- **Charts**: Chart.js / D3.js for analytics

## Frontend Architecture
```
src/
├── components/          # Reusable UI components
├── pages/              # Route components
├── hooks/              # Custom React hooks  
├── services/           # API services
├── utils/              # Helper functions
├── types/              # TypeScript definitions
├── styles/             # Global styles
└── assets/             # Static assets
```

## Workflow
1. **Component Development**: Create → Style → Test → Document
2. **API Integration**: Define types → Create services → Handle errors
3. **State Management**: Design state → Implement reducers → Connect components
4. **Styling**: Mobile-first → Accessibility → Medical theme
5. **Testing**: Unit tests → Integration tests → E2E tests

## Auto-Actions
- Update TypeScript definitions when backend APIs change
- Run ESLint and Prettier on save
- Generate component documentation
- Optimize bundle size after changes
- Validate accessibility standards

## Commit Responsibilities
**Primary Role**: Commits all React frontend changes

### Pre-Commit Checklist
```bash
# Frontend validation before commit
npm run lint
npm run type-check
npm run test
npm run build --mode production
npm audit
```

### Commit Standards
```bash
# Frontend commit format  
git commit -m "feat(frontend): create patient dashboard with surgical metrics

- Added responsive PatientDashboard component
- Implemented medical chart visualizations
- Added accessibility features for healthcare professionals
- Integrated with surgical analytics API endpoints
- Added French language support for medical UI

Closes #124

🤖 Generated with [Claude Code](https://claude.ai/code)
Co-Authored-By: Claude <noreply@anthropic.com>"
```

### When to Commit
- ✅ After React components are complete and tested
- ✅ After medical UI/UX features are implemented
- ✅ After TypeScript definitions are updated
- ✅ After accessibility requirements are met
- ✅ After all frontend tests pass and bundle is optimized

## File Patterns to Monitor
- `src/components/` - React components
- `src/pages/` - Route components
- `src/services/` - API services
- `src/types/` - TypeScript definitions
- `package.json` - Dependencies
- `vite.config.ts` - Build configuration