# Frontend Agent Task Clarification

## Purpose

This document provides crystal-clear guidance to the Frontend Agent (ag-frontend) about task ownership, boundaries, and collaboration requirements based on the microservices architecture.

**Created for**: ag-frontend  
**Created by**: ag-techlead  
**Date**: September 11, 2025  
**Status**: AUTHORITATIVE GUIDANCE

## Your Domain

### What You OWN ✅

```
frontend/
├── src/
│   ├── components/      # All React components
│   ├── pages/          # Page components
│   ├── hooks/          # React hooks
│   ├── services/       # API clients and service orchestration
│   ├── stores/         # Zustand state management
│   ├── utils/          # Frontend utilities
│   ├── i18n/           # Internationalization
│   └── styles/         # CSS and styling
├── public/             # Static assets
├── tests/              # Frontend tests
└── package.json        # Frontend dependencies
```

### What You DO NOT OWN ❌

```
services/               # ❌ Backend microservices (identity, communication, etc.)
backend/                # ❌ Django backend service
infrastructure/kong/    # ❌ Kong API Gateway configuration
infrastructure/docker/  # ❌ Docker and deployment configs
```

## Task Ownership Breakdown

### Tasks You FULLY Own 👑

#### 1. API Client Updates
**Your Responsibility**:
- Update `src/services/api/client.ts` to use Kong endpoints
- Change all API calls to go through `http://localhost:8000`
- Update environment variables (`.env` files)
- Remove hardcoded service ports (8001, 8002, etc.)

**Example Implementation**:
```typescript
// ✅ CORRECT - Your code
// frontend/src/services/api/client.ts
const KONG_URL = import.meta.env.VITE_KONG_URL || 'http://localhost:8000';

const endpoints = {
  auth: `${KONG_URL}/api/v1/auth`,
  users: `${KONG_URL}/api/v1/users`,
  documents: `${KONG_URL}/api/v1/documents`,
  // ... etc
};
```

**What You're Waiting For**:
- Kong routes must be configured by ag-coordinator FIRST
- You'll receive documentation of available routes

#### 2. Service Orchestrator Implementation
**Your Responsibility**:
- Create `src/services/integration/ServiceOrchestrator.ts`
- Implement client-side coordination of multiple API calls
- Handle complex UI workflows that need multiple services

**This is 100% Frontend Code**:
```typescript
// ✅ This is YOUR domain - client-side orchestration
export class ServiceOrchestrator {
  async createUserWithProfile(data) {
    // 1. Create user via identity service
    const user = await identityAPI.createUser(data.user);
    
    // 2. Upload profile photo via content service
    const photo = await contentAPI.uploadFile(data.photo);
    
    // 3. Send welcome email via communication service
    await communicationAPI.sendWelcome(user.id);
    
    return { user, photo };
  }
}
```

#### 3. Internationalization (i18n)
**Your Responsibility**:
- Install i18next and react-i18next
- Create translation files in `frontend/src/i18n/locales/`
- Build language switcher component
- Manage all UI text translations

**Your Implementation**:
```typescript
// ✅ All frontend/src/i18n/ is yours
frontend/src/i18n/
├── config.ts           # i18next configuration
├── locales/
│   ├── fr/             # French translations (primary)
│   ├── en/             # English translations
│   ├── de/             # German translations
│   └── ...
└── LanguageSwitcher.tsx # UI component
```

#### 4. State Management
**Your Responsibility**:
- All Zustand stores in `frontend/src/stores/`
- TanStack Query configuration
- Client-side state synchronization
- Cache management

### Tasks You SHARE 🤝

#### 1. Authentication Flow

**Your Part** ✅:
```typescript
// frontend/src/features/auth/
├── LoginForm.tsx       # ✅ Login UI component
├── MFAScreen.tsx       # ✅ Multi-factor auth UI
├── useAuth.ts          # ✅ Auth hook
└── authStore.ts        # ✅ Zustand auth state
```

**NOT Your Part** ❌:
- JWT token generation (ag-identity)
- Token validation logic (ag-identity)
- Kong JWT plugin setup (ag-coordinator)

**How You Collaborate**:
1. ag-identity creates auth endpoints
2. ag-coordinator configures Kong routes
3. YOU create the UI and integrate with the endpoints

#### 2. WebSocket Implementation

**Your Part** ✅:
```typescript
// frontend/src/services/realtime/
├── WebSocketManager.ts  # ✅ Client-side WebSocket manager
├── useWebSocket.ts      # ✅ React hook for WS
└── RealtimeUpdates.tsx  # ✅ UI components for real-time
```

**NOT Your Part** ❌:
- WebSocket server (ag-communication)
- Kong WebSocket proxy (ag-coordinator)
- Message queue setup (ag-communication)

## Clear Examples of What You DO and DON'T Do

### ✅ DO: Update Frontend Code
```typescript
// frontend/src/services/api/users.ts
export const usersAPI = {
  // ✅ YES - Update these to use Kong
  getUsers: () => apiClient.get('/api/v1/users'),
  getProfile: (id) => apiClient.get(`/api/v1/users/${id}`),
};
```

### ❌ DON'T: Configure Kong
```yaml
# infrastructure/kong/kong.yml
# ❌ NO - This is ag-coordinator's job
services:
  - name: identity-service
    url: http://identity-service:8001
routes:
  - name: auth-routes
    paths: ['/api/v1/auth']
```

### ❌ DON'T: Modify Backend Services
```python
# services/identity-service/api/auth.py
# ❌ NO - This is ag-identity's job
@router.post("/login")
async def login(credentials: LoginCredentials):
    # Backend logic - NOT YOUR DOMAIN
    pass
```

## Waiting Dependencies

Before you can complete certain tasks, you need:

### From ag-coordinator:
1. **Kong Routes Configuration**
   - List of available API endpoints
   - Authentication requirements
   - WebSocket proxy endpoints
   - CORS configuration

### From ag-identity:
1. **Authentication API Specification**
   - Login/logout endpoints
   - Token refresh mechanism
   - MFA flow documentation
   - User data structure

### From ag-communication:
1. **WebSocket Event Schema**
   - Event types and payloads
   - Channel names
   - Connection requirements
   - Reconnection strategy

## How to Proceed

### Tasks You Can Start NOW 🚀

1. **Set up project structure**:
   ```bash
   cd frontend
   npm install i18next react-i18next
   npm install zustand @tanstack/react-query
   npm install socket.io-client
   ```

2. **Create ServiceOrchestrator class**:
   - Design the class structure
   - Plan orchestration patterns
   - Create mock implementations

3. **Set up i18n**:
   - Configure i18next
   - Create French translation files
   - Build language switcher

4. **Prepare API client structure**:
   - Create the client architecture
   - Set up interceptors
   - Prepare for Kong integration

### Tasks That Must Wait ⏸

1. **Kong API Integration**: Wait for ag-coordinator to provide routes
2. **Auth UI Testing**: Wait for ag-identity endpoints
3. **WebSocket Connection**: Wait for ag-communication server + ag-coordinator proxy

## Communication Protocol

### When You Need Something

1. **Check the task ownership matrix** first
2. **Create a handoff request** with:
   - What you need
   - Why you need it
   - When you need it
   - Acceptance criteria

### When Providing to Others

1. **Frontend components for other agents**: Not typical, but if needed:
   - Document component props
   - Provide usage examples
   - Include TypeScript types

## Success Checklist

### Sprint 1 Goals for Frontend Agent

- [ ] API client updated to use Kong endpoints
- [ ] ServiceOrchestrator class implemented
- [ ] i18n configured with French translations
- [ ] Zustand stores created for each service domain
- [ ] TanStack Query configured with proper caching
- [ ] Auth UI components created
- [ ] WebSocket client manager implemented
- [ ] Error handling standardized
- [ ] Loading states implemented
- [ ] Basic testing coverage

## Quick Reference

### Your API Endpoints (via Kong)
```typescript
const API_BASE = 'http://localhost:8000';

// Identity Service
GET    ${API_BASE}/api/v1/auth/me
POST   ${API_BASE}/api/v1/auth/login
POST   ${API_BASE}/api/v1/auth/logout
POST   ${API_BASE}/api/v1/auth/refresh

// User Management
GET    ${API_BASE}/api/v1/users
GET    ${API_BASE}/api/v1/users/{id}
POST   ${API_BASE}/api/v1/users
PATCH  ${API_BASE}/api/v1/users/{id}

// Document Management
GET    ${API_BASE}/api/v1/documents
POST   ${API_BASE}/api/v1/documents/upload
GET    ${API_BASE}/api/v1/documents/{id}/download

// Communication
POST   ${API_BASE}/api/v1/messages/send
GET    ${API_BASE}/api/v1/notifications
WS     ${API_BASE}/ws/notifications

// Workflows
GET    ${API_BASE}/api/v1/workflows
POST   ${API_BASE}/api/v1/workflows/execute
```

### Your Key Files
```
frontend/
├── src/services/api/client.ts        # Main API client
├── src/services/integration/         # Service orchestration
├── src/stores/                       # Zustand stores
├── src/i18n/                         # Translations
├── src/features/auth/                # Auth UI
└── .env                              # Environment variables
```

---

**Remember**: You own the entire frontend user experience. Focus on building excellent UI/UX while respecting service boundaries. When in doubt, check the task ownership matrix or ask ag-techlead for clarification.

**Document Status**: ACTIVE  
**For Agent**: ag-frontend  
**Maintained By**: ag-techlead  
**Last Updated**: September 11, 2025