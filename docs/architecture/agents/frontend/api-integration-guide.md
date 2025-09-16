# Frontend API Integration Guide

## Overview

This guide provides the frontend agent with comprehensive patterns and best practices for integrating with the ReactDjango Hub microservices architecture.

## Current Service Architecture

### Available Services

| Service | Port | Status | Authentication | Base URL |
|---------|------|--------|----------------|----------|
| Identity Service | 8001 | ✅ Production Ready | JWT | `http://localhost:8001` |
| Django Backend | 8000 | 🚧 In Development | JWT (via Identity) | `http://localhost:8000` |

### Service Responsibilities

**Identity Service (FastAPI - Port 8001)**
- User authentication and authorization
- User management (CRUD)
- Organization management
- Multi-factor authentication (MFA)
- Role-based access control (RBAC)
- JWT token issuance and validation

**Django Backend (Port 8000)**
- Business logic and data models
- Domain-specific operations
- Integrates with Identity Service for auth
- Provides REST APIs via Django REST Framework
- Handles complex business workflows

## API Client Architecture

### 1. Environment Configuration

```typescript
// src/config/env.ts
export const config = {
  services: {
    identity: {
      url: import.meta.env.VITE_IDENTITY_SERVICE_URL || 'http://localhost:8001',
      version: 'v1',
    },
    backend: {
      url: import.meta.env.VITE_BACKEND_SERVICE_URL || 'http://localhost:8000',
      version: 'v1',
    },
  },
  app: {
    name: import.meta.env.VITE_APP_NAME || 'ReactDjango Hub',
    version: import.meta.env.VITE_APP_VERSION || '1.0.0',
    environment: import.meta.env.VITE_APP_ENV || 'development',
  },
  features: {
    enableMFA: import.meta.env.VITE_ENABLE_MFA === 'true',
    enableAnalytics: import.meta.env.VITE_ENABLE_ANALYTICS === 'true',
  },
};
```

### 2. Base API Client

```typescript
// src/services/api/base-client.ts
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { TokenManager } from '../auth/token-manager';

export interface ApiError {
  message: string;
  code: string;
  status: number;
  details?: Record<string, any>;
}

export class BaseApiClient {
  protected instance: AxiosInstance;
  private tokenManager: TokenManager;
  
  constructor(baseURL: string, serviceName: string) {
    this.tokenManager = TokenManager.getInstance();
    
    this.instance = axios.create({
      baseURL,
      timeout: 15000,
      headers: {
        'Content-Type': 'application/json',
        'X-Service-Name': serviceName,
      },
    });
    
    this.setupInterceptors();
  }
  
  private setupInterceptors(): void {
    // Request interceptor
    this.instance.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = this.tokenManager.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        // Add request ID for tracing
        config.headers['X-Request-ID'] = this.generateRequestId();
        
        return config;
      },
      (error: AxiosError) => {
        return Promise.reject(this.handleError(error));
      }
    );
    
    // Response interceptor
    this.instance.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
        
        // Handle 401 - Token expired
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            await this.tokenManager.refreshToken();
            const newToken = this.tokenManager.getAccessToken();
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            return this.instance(originalRequest);
          } catch (refreshError) {
            // Refresh failed - redirect to login
            this.tokenManager.clearTokens();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }
        
        return Promise.reject(this.handleError(error));
      }
    );
  }
  
  private handleError(error: AxiosError): ApiError {
    if (error.response) {
      // Server responded with error
      const data = error.response.data as any;
      return {
        message: data.message || data.detail || 'An error occurred',
        code: data.code || 'SERVER_ERROR',
        status: error.response.status,
        details: data.errors || data.details,
      };
    } else if (error.request) {
      // Request made but no response
      return {
        message: 'No response from server',
        code: 'NETWORK_ERROR',
        status: 0,
        details: { originalError: error.message },
      };
    } else {
      // Request setup error
      return {
        message: error.message || 'Request failed',
        code: 'REQUEST_ERROR',
        status: 0,
        details: { originalError: error.message },
      };
    }
  }
  
  private generateRequestId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
}
```

### 3. Service-Specific Clients

#### Identity Service Client

```typescript
// src/services/api/identity-client.ts
import { BaseApiClient } from './base-client';
import { config } from '@/config/env';

export interface LoginRequest {
  email: string;
  password: string;
  mfa_code?: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface User {
  id: string;
  email: string;
  name: string;
  roles: Role[];
  permissions: string[];
  organization?: Organization;
  is_active: boolean;
  mfa_enabled: boolean;
}

export interface Role {
  id: string;
  name: string;
  permissions: string[];
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
}

export class IdentityServiceClient extends BaseApiClient {
  constructor() {
    super(config.services.identity.url, 'identity');
  }
  
  // Authentication endpoints
  async login(data: LoginRequest): Promise<LoginResponse> {
    const response = await this.instance.post<LoginResponse>('/auth/login', data);
    return response.data;
  }
  
  async logout(): Promise<void> {
    await this.instance.post('/auth/logout');
  }
  
  async refreshToken(refreshToken: string): Promise<LoginResponse> {
    const response = await this.instance.post<LoginResponse>('/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  }
  
  async getCurrentUser(): Promise<User> {
    const response = await this.instance.get<User>('/auth/me');
    return response.data;
  }
  
  // User management endpoints
  async getUsers(params?: {
    page?: number;
    limit?: number;
    search?: string;
    role?: string;
  }): Promise<{ users: User[]; total: number }> {
    const response = await this.instance.get('/users', { params });
    return response.data;
  }
  
  async getUser(userId: string): Promise<User> {
    const response = await this.instance.get<User>(`/users/${userId}`);
    return response.data;
  }
  
  async createUser(data: Partial<User>): Promise<User> {
    const response = await this.instance.post<User>('/users', data);
    return response.data;
  }
  
  async updateUser(userId: string, data: Partial<User>): Promise<User> {
    const response = await this.instance.patch<User>(`/users/${userId}`, data);
    return response.data;
  }
  
  async deleteUser(userId: string): Promise<void> {
    await this.instance.delete(`/users/${userId}`);
  }
  
  // MFA endpoints
  async enableMFA(): Promise<{ secret: string; qr_code: string }> {
    const response = await this.instance.post('/auth/mfa/enable');
    return response.data;
  }
  
  async verifyMFA(code: string): Promise<{ verified: boolean }> {
    const response = await this.instance.post('/auth/mfa/verify', { code });
    return response.data;
  }
  
  async disableMFA(code: string): Promise<void> {
    await this.instance.post('/auth/mfa/disable', { code });
  }
}

// Export singleton instance
export const identityClient = new IdentityServiceClient();
```

#### Backend Service Client

```typescript
// src/services/api/backend-client.ts
import { BaseApiClient } from './base-client';
import { config } from '@/config/env';

export interface DashboardData {
  metrics: Metric[];
  recentActivity: Activity[];
  notifications: Notification[];
}

export interface Metric {
  id: string;
  name: string;
  value: number;
  change: number;
  trend: 'up' | 'down' | 'stable';
}

export interface Activity {
  id: string;
  type: string;
  description: string;
  timestamp: string;
  user: { id: string; name: string };
}

export interface Notification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  message: string;
  read: boolean;
  created_at: string;
}

export class BackendServiceClient extends BaseApiClient {
  constructor() {
    super(config.services.backend.url, 'backend');
  }
  
  // Dashboard endpoints
  async getDashboardData(): Promise<DashboardData> {
    const response = await this.instance.get<DashboardData>('/api/dashboard');
    return response.data;
  }
  
  // Business logic endpoints
  async getProjects(params?: {
    page?: number;
    limit?: number;
    status?: string;
  }): Promise<{ projects: any[]; total: number }> {
    const response = await this.instance.get('/api/projects', { params });
    return response.data;
  }
  
  async getProject(projectId: string): Promise<any> {
    const response = await this.instance.get(`/api/projects/${projectId}`);
    return response.data;
  }
  
  async createProject(data: any): Promise<any> {
    const response = await this.instance.post('/api/projects', data);
    return response.data;
  }
  
  async updateProject(projectId: string, data: any): Promise<any> {
    const response = await this.instance.patch(`/api/projects/${projectId}`, data);
    return response.data;
  }
  
  async deleteProject(projectId: string): Promise<void> {
    await this.instance.delete(`/api/projects/${projectId}`);
  }
}

// Export singleton instance
export const backendClient = new BackendServiceClient();
```

## Authentication Flow

### 1. Token Manager

```typescript
// src/services/auth/token-manager.ts
import { jwtDecode } from 'jwt-decode';

interface JWTPayload {
  sub: string;
  exp: number;
  iat: number;
  roles: string[];
  permissions: string[];
}

export class TokenManager {
  private static instance: TokenManager;
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private refreshTimer: NodeJS.Timeout | null = null;
  
  private constructor() {
    this.loadTokensFromStorage();
  }
  
  static getInstance(): TokenManager {
    if (!TokenManager.instance) {
      TokenManager.instance = new TokenManager();
    }
    return TokenManager.instance;
  }
  
  setTokens(accessToken: string, refreshToken: string): void {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    
    // Store refresh token in httpOnly cookie (via backend)
    // Only store access token in memory
    sessionStorage.setItem('has_session', 'true');
    
    this.scheduleTokenRefresh();
  }
  
  getAccessToken(): string | null {
    return this.accessToken;
  }
  
  getRefreshToken(): string | null {
    return this.refreshToken;
  }
  
  clearTokens(): void {
    this.accessToken = null;
    this.refreshToken = null;
    sessionStorage.removeItem('has_session');
    
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
      this.refreshTimer = null;
    }
  }
  
  async refreshToken(): Promise<void> {
    if (!this.refreshToken) {
      throw new Error('No refresh token available');
    }
    
    const { identityClient } = await import('./identity-client');
    const response = await identityClient.refreshToken(this.refreshToken);
    
    this.setTokens(response.access_token, response.refresh_token);
  }
  
  private scheduleTokenRefresh(): void {
    if (!this.accessToken) return;
    
    try {
      const payload = jwtDecode<JWTPayload>(this.accessToken);
      const expiresIn = payload.exp * 1000 - Date.now();
      const refreshTime = Math.max(0, expiresIn - 60000); // Refresh 1 min before expiry
      
      if (this.refreshTimer) {
        clearTimeout(this.refreshTimer);
      }
      
      this.refreshTimer = setTimeout(async () => {
        try {
          await this.refreshToken();
        } catch (error) {
          console.error('Token refresh failed:', error);
          this.clearTokens();
          window.location.href = '/login';
        }
      }, refreshTime);
    } catch (error) {
      console.error('Failed to decode token:', error);
      this.clearTokens();
    }
  }
  
  private loadTokensFromStorage(): void {
    // Check if user has active session
    const hasSession = sessionStorage.getItem('has_session');
    if (hasSession) {
      // Tokens should be restored from backend on page load
      // This is handled by the auth initialization flow
    }
  }
  
  isTokenExpired(): boolean {
    if (!this.accessToken) return true;
    
    try {
      const payload = jwtDecode<JWTPayload>(this.accessToken);
      return payload.exp * 1000 < Date.now();
    } catch {
      return true;
    }
  }
}
```

### 2. Authentication Hook

```typescript
// src/hooks/useAuth.ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { identityClient } from '@/services/api/identity-client';
import { TokenManager } from '@/services/auth/token-manager';
import { useAuthStore } from '@/stores/auth-store';

export function useAuth() {
  const queryClient = useQueryClient();
  const tokenManager = TokenManager.getInstance();
  const { setUser, clearUser } = useAuthStore();
  
  // Get current user
  const { data: user, isLoading } = useQuery({
    queryKey: ['auth', 'user'],
    queryFn: async () => {
      if (!tokenManager.getAccessToken()) {
        return null;
      }
      return identityClient.getCurrentUser();
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false,
  });
  
  // Login mutation
  const loginMutation = useMutation({
    mutationFn: async (credentials: { email: string; password: string }) => {
      const response = await identityClient.login(credentials);
      tokenManager.setTokens(response.access_token, response.refresh_token);
      setUser(response.user);
      return response;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auth'] });
    },
  });
  
  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: async () => {
      await identityClient.logout();
      tokenManager.clearTokens();
      clearUser();
    },
    onSuccess: () => {
      queryClient.clear();
      window.location.href = '/login';
    },
  });
  
  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    login: loginMutation.mutate,
    logout: logoutMutation.mutate,
    isLoggingIn: loginMutation.isPending,
    isLoggingOut: logoutMutation.isPending,
    loginError: loginMutation.error,
  };
}
```

## Cross-Service Data Aggregation

### Pattern 1: Parallel Fetching

```typescript
// src/hooks/useDashboardData.ts
import { useQueries } from '@tanstack/react-query';
import { identityClient } from '@/services/api/identity-client';
import { backendClient } from '@/services/api/backend-client';

export function useDashboardData() {
  const queries = useQueries({
    queries: [
      {
        queryKey: ['users', 'stats'],
        queryFn: () => identityClient.getUsers({ limit: 0 }), // Get count only
        select: (data) => ({ totalUsers: data.total }),
      },
      {
        queryKey: ['dashboard', 'metrics'],
        queryFn: () => backendClient.getDashboardData(),
        select: (data) => data.metrics,
      },
      {
        queryKey: ['projects', 'recent'],
        queryFn: () => backendClient.getProjects({ limit: 5 }),
        select: (data) => data.projects,
      },
    ],
  });
  
  const isLoading = queries.some((query) => query.isLoading);
  const isError = queries.some((query) => query.isError);
  
  return {
    userStats: queries[0].data,
    metrics: queries[1].data,
    recentProjects: queries[2].data,
    isLoading,
    isError,
  };
}
```

### Pattern 2: Sequential Fetching with Dependencies

```typescript
// src/hooks/useUserProjects.ts
import { useQuery } from '@tanstack/react-query';
import { identityClient } from '@/services/api/identity-client';
import { backendClient } from '@/services/api/backend-client';

export function useUserProjects(userId: string) {
  // First, get user details
  const { data: user } = useQuery({
    queryKey: ['users', userId],
    queryFn: () => identityClient.getUser(userId),
    enabled: !!userId,
  });
  
  // Then, get projects for user's organization
  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects', 'by-org', user?.organization?.id],
    queryFn: () => backendClient.getProjects({ 
      organization_id: user!.organization!.id 
    }),
    enabled: !!user?.organization?.id,
  });
  
  return {
    user,
    projects,
    isLoading,
  };
}
```

## Error Handling Patterns

### Global Error Handler

```typescript
// src/components/ErrorHandler.tsx
import React from 'react';
import { useQueryErrorResetBoundary } from '@tanstack/react-query';
import { ErrorBoundary } from 'react-error-boundary';
import { ApiError } from '@/services/api/base-client';

function ErrorFallback({ 
  error, 
  resetErrorBoundary 
}: { 
  error: ApiError; 
  resetErrorBoundary: () => void;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
        <h2 className="text-2xl font-bold text-red-600 mb-4">
          Oops! Something went wrong
        </h2>
        <div className="bg-red-50 border border-red-200 rounded p-4 mb-4">
          <p className="text-sm text-red-800">
            {error.message || 'An unexpected error occurred'}
          </p>
          {error.code && (
            <p className="text-xs text-red-600 mt-2">
              Error Code: {error.code}
            </p>
          )}
        </div>
        <button
          onClick={resetErrorBoundary}
          className="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600"
        >
          Try Again
        </button>
      </div>
    </div>
  );
}

export function AppErrorBoundary({ children }: { children: React.ReactNode }) {
  const { reset } = useQueryErrorResetBoundary();
  
  return (
    <ErrorBoundary
      FallbackComponent={ErrorFallback}
      onReset={reset}
      onError={(error, errorInfo) => {
        // Log to error tracking service
        console.error('Error boundary caught:', error, errorInfo);
      }}
    >
      {children}
    </ErrorBoundary>
  );
}
```

## CORS Configuration

### Development Setup

For local development, configure CORS on each service:

**Identity Service (FastAPI)**:
```python
# services/identity-service/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Django Backend**:
```python
# backend/config/settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]
CORS_ALLOW_CREDENTIALS = True
```

### Production Setup

In production, use a reverse proxy or API gateway to avoid CORS issues:

```nginx
# nginx.conf
location /api/identity/ {
    proxy_pass http://identity-service:8001/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

location /api/backend/ {
    proxy_pass http://backend-service:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## Testing API Integration

### Unit Tests

```typescript
// src/services/api/__tests__/identity-client.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import axios from 'axios';
import { IdentityServiceClient } from '../identity-client';

vi.mock('axios');

describe('IdentityServiceClient', () => {
  let client: IdentityServiceClient;
  
  beforeEach(() => {
    client = new IdentityServiceClient();
  });
  
  describe('login', () => {
    it('should return login response on success', async () => {
      const mockResponse = {
        data: {
          access_token: 'token',
          refresh_token: 'refresh',
          user: { id: '1', email: 'test@example.com' },
        },
      };
      
      (axios.post as any).mockResolvedValue(mockResponse);
      
      const result = await client.login({
        email: 'test@example.com',
        password: 'password',
      });
      
      expect(result).toEqual(mockResponse.data);
    });
    
    it('should handle login error', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { message: 'Invalid credentials' },
        },
      };
      
      (axios.post as any).mockRejectedValue(mockError);
      
      await expect(
        client.login({
          email: 'test@example.com',
          password: 'wrong',
        })
      ).rejects.toThrow('Invalid credentials');
    });
  });
});
```

### Integration Tests

```typescript
// src/services/api/__tests__/integration.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { setupServer } from 'msw/node';
import { rest } from 'msw';
import { identityClient } from '../identity-client';

const server = setupServer(
  rest.post('http://localhost:8001/auth/login', (req, res, ctx) => {
    return res(
      ctx.json({
        access_token: 'test-token',
        refresh_token: 'test-refresh',
        user: { id: '1', email: 'test@example.com' },
      })
    );
  })
);

beforeAll(() => server.listen());
afterAll(() => server.close());

describe('API Integration', () => {
  it('should handle complete login flow', async () => {
    const response = await identityClient.login({
      email: 'test@example.com',
      password: 'password',
    });
    
    expect(response.access_token).toBe('test-token');
    expect(response.user.email).toBe('test@example.com');
  });
});
```

## Best Practices

### 1. Type Safety

Always generate TypeScript types from OpenAPI specs:

```bash
# Generate types from OpenAPI
npx openapi-typescript http://localhost:8001/openapi.json -o src/types/identity-api.ts
npx openapi-typescript http://localhost:8000/openapi.json -o src/types/backend-api.ts
```

### 2. Error Handling

- Always provide user-friendly error messages
- Log errors for debugging but don't expose sensitive data
- Implement retry logic for transient failures
- Use error boundaries to catch component errors

### 3. Performance

- Use React Query for caching and deduplication
- Implement pagination for large datasets
- Use optimistic updates for better UX
- Lazy load components and routes

### 4. Security

- Never store tokens in localStorage
- Use httpOnly cookies for refresh tokens
- Implement CSRF protection
- Validate all user inputs
- Sanitize data before rendering

### 5. Developer Experience

- Provide clear API documentation
- Use consistent naming conventions
- Implement comprehensive logging
- Create reusable hooks for common patterns

---

**Document maintained by**: Technical Lead Agent  
**For**: Frontend Agent  
**Last updated**: September 10, 2025  
**Next review**: October 10, 2025