# API Integration Guide

Guide for integrating backend APIs in the React frontend.

## 🔗 **Backend API References**

The frontend agent should consult the backend API documentation located at:

```
../../backend/docs/api/     # Complete endpoint documentation
../../docs/api/             # Global API schemas and contracts
```

## 📡 **Main Endpoints**

### Base URL
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'
```

### Endpoints by Domain

**Authentication** - `/api/auth/`
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - Logout
- `POST /api/auth/refresh/` - JWT token refresh
- `GET /api/auth/user/` - Current user profile

**Users** - `/api/users/`
- `GET /api/users/` - List users
- `POST /api/users/` - Create user
- `GET /api/users/{id}/` - User details
- `PUT /api/users/{id}/` - Update user

**Resources** - `/api/resources/`
- `GET /api/resources/` - List resources
- `POST /api/resources/` - Create resource
- `PUT /api/resources/{id}/` - Update resource

> 📚 **Detailed documentation:** See `backend/docs/api/` for complete schemas, validations and response examples.

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