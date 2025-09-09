# API Integration Guide

Guide for integrating microservices APIs in the React frontend.

## 🏗️ **Microservices Architecture**

The frontend connects to **two separate services**:

| Service | Purpose | Base URL | Documentation |
|---------|---------|----------|---------------|
| **Auth Service** | Authentication, users, organizations | `http://localhost:8001` | `../../services/auth-service/README.md` |
| **Backend Service** | Business logic, medical records | `http://localhost:8000/api` | `../../backend/docs/README.md` |

## 📡 **API Endpoints**

### 🔐 **Auth Service Endpoints** (Port 8001)

#### Base URL
```typescript
const AUTH_API_URL = import.meta.env.VITE_AUTH_API_URL || 'http://localhost:8001'
```

#### Authentication & Users
```typescript
// Core Authentication (7 endpoints)
POST   /auth/login              // JWT login with MFA support
POST   /auth/register           // User registration  
POST   /auth/refresh            // Token refresh
POST   /auth/logout             // Logout with session cleanup
POST   /auth/validate           // Token validation
POST   /auth/authorize          // Permission checking
GET    /auth/permissions/{id}   // User permissions

// User Management (4 endpoints)  
POST   /users/profile           // Create user with profile
GET    /users/{id}/dashboard    // User dashboard data
PATCH  /users/{id}/preferences  // Update preferences
GET    /users/{id}/activity     // User activity logs

// Organizations (4 endpoints)
POST   /organizations           // Create organization
GET    /organizations/{id}/dashboard  // Org dashboard
POST   /organizations/{id}/users     // Add user to org
GET    /organizations/{id}/users     // List org members

// Multi-Factor Authentication (6 endpoints)
POST   /mfa/setup               // Setup MFA (email/SMS/TOTP)
GET    /mfa/methods             // List MFA methods
POST   /mfa/challenge           // Initiate MFA challenge
POST   /mfa/verify              // Verify MFA code
DELETE /mfa/methods/{id}        // Remove MFA method
POST   /mfa/backup-codes/regenerate  // New backup codes
```

### 🏥 **Backend Service Endpoints** (Port 8000)

#### Base URL
```typescript  
const BACKEND_API_URL = import.meta.env.VITE_BACKEND_API_URL || 'http://localhost:8000/api'
```

#### Business Logic (Requires Auth Service JWT)
```typescript
// Medical Records
GET    /api/patients/           // List patients (with auth)
POST   /api/patients/           // Create patient
GET    /api/patients/{id}/      // Patient details
PUT    /api/patients/{id}/      // Update patient

// Analytics  
GET    /api/analytics/dashboard // Analytics dashboard
GET    /api/analytics/reports   // Generate reports

// Billing
GET    /api/billing/invoices    // List invoices
POST   /api/billing/invoices    // Create invoice
```

> 📚 **Complete API Documentation:**
> - **Auth Service**: See `services/auth-service/README.md` - 30 production endpoints
> - **Backend Service**: See `backend/docs/README.md` - Business logic integration

## 🛠 **TypeScript API Client**

### Recommended Structure

```typescript
// src/api/client.ts
export class ApiClient {
  private baseURL: string
  private token: string | null = null

  constructor(baseURL: string) {
    this.baseURL = baseURL
  }

  // Methods for each endpoint...
}

// src/api/types.ts - TypeScript types generated from backend
export interface User {
  id: number
  first_name: string
  last_name: string
  email: string
  // ... other fields according to backend/docs/api/users.md
}
```

## 🔄 **Backend Synchronization**

### Shared API Contract

The frontend and backend share an API contract defined in:
- `docs/api/schema.json` - OpenAPI/Swagger schema
- `docs/api/types.ts` - Shared TypeScript types

### Synchronization Workflow

1. **Backend Agent** generates API documentation
2. **Frontend Agent** consults this documentation  
3. **Shared types** are updated automatically

```bash
# Generate types from backend schema
npm run api:generate-types
```

## 🧪 **Testing API Integration**

### Mock API for Tests

```typescript
// src/api/__mocks__/client.ts
export const mockApiClient = {
  getUsers: jest.fn().mockResolvedValue([
    { id: 1, first_name: 'John', last_name: 'Doe', email: 'john@example.com' }
  ]),
  // ... other mocks
}
```

### Integration Tests

```typescript
// src/api/__tests__/integration.test.ts
describe('API Integration', () => {
  it('should fetch users list', async () => {
    const users = await apiClient.getUsers()
    expect(users).toHaveLength(2)
  })
})
```

## 🚨 **Error Handling**

### Standard Error Codes

- `400` - Validation error (invalid data)
- `401` - Authentication required
- `403` - Permission denied  
- `404` - Resource not found
- `500` - Server error

### Error Handling Pattern

```typescript
try {
  const user = await apiClient.getUser(id)
} catch (error) {
  if (error.status === 404) {
    showNotification('User not found', 'error')
  } else if (error.status === 403) {
    redirectToLogin()
  }
}
```

## 📋 **Frontend-Backend Sync Checklist**

- [ ] TypeScript types updated with Django models
- [ ] Endpoints documented in `backend/docs/api/`
- [ ] Frontend API tests implemented
- [ ] Error handling implemented
- [ ] Frontend data validation
- [ ] Performance optimized (cache, pagination)

---

💡 **Tip**: Use `git commit` in backend-dev to update API docs, then `git commit` in frontend-dev to sync integration.