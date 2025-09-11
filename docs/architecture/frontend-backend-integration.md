# Frontend-Backend Integration Guide

## Overview

This guide defines the integration patterns between the React frontend and the microservices backend architecture accessed through Kong API Gateway. It provides concrete implementation patterns, error handling strategies, and best practices for seamless service integration.

## Architecture Overview (Production Deployment)

```
┌─────────────┐
│   Frontend  │
│   (React)   │
│ Port 3000/  │
│    5173     │
└──────┬──────┘
       │
       ▼ Port 8000 (Proxy) / 8445 (Admin)
┌─────────────────────────────────────┐
│         Kong API Gateway            │
│   - JWT validation                  │
│   - Rate limiting                   │
│   - CORS handling                   │
│   - Load balancing                  │
│   - Health monitoring               │
└─────────────┬───────────────────────┘
              │
  ┌───────────┼───────────┬───────────┬───────────┐
  ▼           ▼           ▼           ▼           ▼
┌──────────┐┌──────────┐┌──────────┐┌──────────┐
│ Identity ││  Content ││  Comm.   ││ Workflow │
│ Service  ││ Service  ││ Service  ││ Service  │
│Port 8001 ││Port 8002 ││Port 8003 ││Port 8004 │
├──────────┤├──────────┤├──────────┤├──────────┤
│PostgreSQL││PostgreSQL││PostgreSQL││PostgreSQL│
│Port 5433 ││Port 5434 ││Port 5435 ││Port 5436 │
├──────────┤├──────────┤├──────────┤├──────────┤
│  Redis   ││  Redis   ││  Redis   ││  Redis   │
│Port 6380 ││Port 6381 ││Port 6382 ││Port 6383 │
└──────────┘└──────────┘└──────────┘└──────────┘
```

## Kong API Gateway Integration

### Gateway Configuration (Aligned with Coordinator Deployment)
```typescript
// frontend/src/config/api.config.ts
export const API_CONFIG = {
  gateway: {
    baseUrl: import.meta.env.VITE_KONG_URL || 'http://localhost:8000',
    adminUrl: import.meta.env.VITE_KONG_ADMIN_URL || 'http://localhost:8445',
    wsUrl: import.meta.env.VITE_KONG_WS_URL || 'ws://localhost:8000',
    timeout: 30000,
    retries: 3,
  },
  services: {
    // Identity Service Routes (Port 8001)
    auth: '/api/v1/auth',
    users: '/api/v1/users',
    organizations: '/api/v1/organizations',
    mfa: '/api/v1/mfa',
    
    // Content Service Routes (Port 8002)
    documents: '/api/v1/documents',
    search: '/api/v1/search',
    
    // Communication Service Routes (Port 8003)
    notifications: '/api/v1/notifications',
    messages: '/api/v1/messages',
    
    // Workflow Intelligence Routes (Port 8004)
    workflows: '/api/v1/workflows',
    ai: '/api/v1/ai',
    
    // Django Backend (if integrated)
    business: '/api/v1/business',
  },
  
  // Direct service access (development only)
  directServices: {
    identity: 'http://localhost:8001',
    content: 'http://localhost:8002',
    communication: 'http://localhost:8003',
    workflow: 'http://localhost:8004',
  },
};
```

### Service Discovery Pattern
```typescript
// frontend/src/services/api/service-discovery.ts
export class ServiceDiscovery {
  private static instance: ServiceDiscovery;
  private serviceMap: Map<string, ServiceEndpoint> = new Map();
  
  private constructor() {
    this.initializeServices();
  }
  
  static getInstance(): ServiceDiscovery {
    if (!ServiceDiscovery.instance) {
      ServiceDiscovery.instance = new ServiceDiscovery();
    }
    return ServiceDiscovery.instance;
  }
  
  private initializeServices() {
    // Register all services with their Kong routes
    this.serviceMap.set('identity', {
      name: 'Identity Service',
      baseRoute: '/api/v1/auth',
      healthCheck: '/api/v1/auth/health',
      version: 'v1',
    });
    
    this.serviceMap.set('communication', {
      name: 'Communication Service',
      baseRoute: '/api/v1/notifications',
      healthCheck: '/api/v1/notifications/health',
      version: 'v1',
    });
    
    // ... register other services
  }
  
  getServiceEndpoint(service: string): ServiceEndpoint {
    const endpoint = this.serviceMap.get(service);
    if (!endpoint) {
      throw new Error(`Service ${service} not found in registry`);
    }
    return endpoint;
  }
  
  async checkServiceHealth(service: string): Promise<boolean> {
    try {
      const endpoint = this.getServiceEndpoint(service);
      const response = await fetch(
        `${API_CONFIG.gateway.baseUrl}${endpoint.healthCheck}`
      );
      return response.ok;
    } catch (error) {
      console.error(`Health check failed for ${service}:`, error);
      return false;
    }
  }
}
```

## Authentication Flow

### JWT Token Management
```typescript
// frontend/src/services/auth/token-manager.ts
export class TokenManager {
  private static ACCESS_TOKEN_KEY = 'access_token';
  private static REFRESH_TOKEN_KEY = 'refresh_token';
  private static TOKEN_EXPIRY_KEY = 'token_expiry';
  
  static setTokens(accessToken: string, refreshToken: string, expiresIn: number) {
    // Store in memory for security
    sessionStorage.setItem(this.ACCESS_TOKEN_KEY, accessToken);
    
    // Store refresh token in httpOnly cookie via backend
    this.sendRefreshTokenToCookie(refreshToken);
    
    // Calculate and store expiry
    const expiry = Date.now() + (expiresIn * 1000);
    sessionStorage.setItem(this.TOKEN_EXPIRY_KEY, expiry.toString());
  }
  
  static getAccessToken(): string | null {
    const token = sessionStorage.getItem(this.ACCESS_TOKEN_KEY);
    const expiry = sessionStorage.getItem(this.TOKEN_EXPIRY_KEY);
    
    if (token && expiry) {
      if (Date.now() < parseInt(expiry)) {
        return token;
      }
      // Token expired, trigger refresh
      this.refreshAccessToken();
    }
    
    return null;
  }
  
  static async refreshAccessToken(): Promise<string> {
    try {
      const response = await fetch(`${API_CONFIG.gateway.baseUrl}/api/v1/auth/refresh`, {
        method: 'POST',
        credentials: 'include', // Include httpOnly cookies
      });
      
      if (!response.ok) {
        throw new Error('Token refresh failed');
      }
      
      const data = await response.json();
      this.setTokens(data.access_token, data.refresh_token, data.expires_in);
      return data.access_token;
    } catch (error) {
      // Refresh failed, redirect to login
      window.location.href = '/login';
      throw error;
    }
  }
  
  private static async sendRefreshTokenToCookie(refreshToken: string) {
    // Backend endpoint to set httpOnly cookie
    await fetch(`${API_CONFIG.gateway.baseUrl}/api/v1/auth/set-refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
      credentials: 'include',
    });
  }
}
```

### Authentication Interceptor
```typescript
// frontend/src/services/api/auth-interceptor.ts
import axios, { AxiosInstance } from 'axios';
import { TokenManager } from '../auth/token-manager';

export function setupAuthInterceptor(axiosInstance: AxiosInstance) {
  // Request interceptor
  axiosInstance.interceptors.request.use(
    async (config) => {
      const token = TokenManager.getAccessToken();
      
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      
      // Add Kong-specific headers
      config.headers['X-Kong-Request-Id'] = generateRequestId();
      config.headers['X-Client-Version'] = process.env.VITE_APP_VERSION;
      
      return config;
    },
    (error) => Promise.reject(error)
  );
  
  // Response interceptor
  axiosInstance.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;
      
      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;
        
        try {
          const newToken = await TokenManager.refreshAccessToken();
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return axiosInstance(originalRequest);
        } catch (refreshError) {
          // Refresh failed, user will be redirected to login
          return Promise.reject(refreshError);
        }
      }
      
      // Handle Kong-specific errors
      if (error.response?.headers['x-kong-error']) {
        console.error('Kong Gateway Error:', error.response.headers['x-kong-error']);
      }
      
      return Promise.reject(error);
    }
  );
}
```

## Real-time Updates with WebSocket

### WebSocket Connection Management
```typescript
// frontend/src/services/realtime/websocket-client.ts
import { io, Socket } from 'socket.io-client';
import { TokenManager } from '../auth/token-manager';

export class WebSocketClient {
  private sockets: Map<string, Socket> = new Map();
  private reconnectAttempts: Map<string, number> = new Map();
  private maxReconnectAttempts = 5;
  
  connect(service: 'communication' | 'workflow'): Socket {
    const existingSocket = this.sockets.get(service);
    if (existingSocket?.connected) {
      return existingSocket;
    }
    
    const socket = io(`${API_CONFIG.gateway.wsUrl}/${service}`, {
      auth: {
        token: TokenManager.getAccessToken(),
      },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: this.maxReconnectAttempts,
    });
    
    this.setupEventHandlers(socket, service);
    this.sockets.set(service, socket);
    
    return socket;
  }
  
  private setupEventHandlers(socket: Socket, service: string) {
    socket.on('connect', () => {
      console.log(`Connected to ${service} WebSocket`);
      this.reconnectAttempts.set(service, 0);
      
      // Re-authenticate on reconnect
      socket.emit('authenticate', {
        token: TokenManager.getAccessToken(),
      });
    });
    
    socket.on('disconnect', (reason) => {
      console.log(`Disconnected from ${service}: ${reason}`);
      
      if (reason === 'io server disconnect') {
        // Server disconnected, try to reconnect
        this.handleReconnection(service);
      }
    });
    
    socket.on('error', (error) => {
      console.error(`WebSocket error for ${service}:`, error);
      
      if (error.type === 'authentication_error') {
        // Token expired or invalid, refresh and reconnect
        this.refreshAndReconnect(service);
      }
    });
    
    socket.on('notification', (data) => {
      // Handle real-time notifications
      this.handleNotification(data);
    });
  }
  
  private async refreshAndReconnect(service: string) {
    try {
      await TokenManager.refreshAccessToken();
      this.disconnect(service);
      this.connect(service);
    } catch (error) {
      console.error('Failed to refresh token for WebSocket:', error);
    }
  }
  
  private handleReconnection(service: string) {
    const attempts = this.reconnectAttempts.get(service) || 0;
    
    if (attempts < this.maxReconnectAttempts) {
      this.reconnectAttempts.set(service, attempts + 1);
      
      setTimeout(() => {
        console.log(`Attempting to reconnect to ${service} (attempt ${attempts + 1})`);
        this.connect(service);
      }, Math.min(1000 * Math.pow(2, attempts), 30000)); // Exponential backoff
    } else {
      console.error(`Max reconnection attempts reached for ${service}`);
      // Notify user of connection failure
      this.notifyConnectionFailure(service);
    }
  }
  
  disconnect(service: string) {
    const socket = this.sockets.get(service);
    if (socket) {
      socket.disconnect();
      this.sockets.delete(service);
    }
  }
  
  disconnectAll() {
    this.sockets.forEach((socket, service) => {
      socket.disconnect();
    });
    this.sockets.clear();
  }
}
```

## Document Handling with Content Service

### File Upload Pattern
```typescript
// frontend/src/services/content/file-upload.ts
export class FileUploadService {
  private uploadQueue: Map<string, UploadTask> = new Map();
  
  async uploadFile(
    file: File,
    options: UploadOptions = {}
  ): Promise<UploadResult> {
    const uploadId = this.generateUploadId();
    const formData = new FormData();
    
    formData.append('file', file);
    formData.append('metadata', JSON.stringify({
      filename: file.name,
      mimeType: file.type,
      size: file.size,
      ...options.metadata,
    }));
    
    const uploadTask: UploadTask = {
      id: uploadId,
      file,
      progress: 0,
      status: 'pending',
      cancelToken: axios.CancelToken.source(),
    };
    
    this.uploadQueue.set(uploadId, uploadTask);
    
    try {
      const response = await axios.post(
        `${API_CONFIG.gateway.baseUrl}/api/v1/documents/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total!
            );
            this.updateProgress(uploadId, progress);
            options.onProgress?.(progress);
          },
          cancelToken: uploadTask.cancelToken.token,
        }
      );
      
      uploadTask.status = 'completed';
      uploadTask.result = response.data;
      
      return response.data;
    } catch (error) {
      uploadTask.status = 'failed';
      uploadTask.error = error;
      throw error;
    } finally {
      // Clean up after delay
      setTimeout(() => {
        this.uploadQueue.delete(uploadId);
      }, 5000);
    }
  }
  
  async uploadMultiple(
    files: File[],
    options: UploadOptions = {}
  ): Promise<UploadResult[]> {
    const uploads = files.map(file => this.uploadFile(file, options));
    return Promise.all(uploads);
  }
  
  cancelUpload(uploadId: string) {
    const task = this.uploadQueue.get(uploadId);
    if (task && task.status === 'pending') {
      task.cancelToken.cancel('Upload cancelled by user');
      task.status = 'cancelled';
    }
  }
  
  private updateProgress(uploadId: string, progress: number) {
    const task = this.uploadQueue.get(uploadId);
    if (task) {
      task.progress = progress;
      task.status = 'uploading';
    }
  }
  
  private generateUploadId(): string {
    return `upload_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}
```

## Workflow Integration Patterns

### Workflow Execution
```typescript
// frontend/src/services/workflow/workflow-executor.ts
export class WorkflowExecutor {
  private activeWorkflows: Map<string, WorkflowExecution> = new Map();
  
  async startWorkflow(
    workflowId: string,
    parameters: Record<string, any>
  ): Promise<WorkflowExecution> {
    const response = await axios.post(
      `${API_CONFIG.gateway.baseUrl}/api/v1/workflows/${workflowId}/execute`,
      { parameters }
    );
    
    const execution: WorkflowExecution = {
      id: response.data.execution_id,
      workflowId,
      status: 'running',
      startTime: new Date(),
      steps: response.data.steps,
    };
    
    this.activeWorkflows.set(execution.id, execution);
    
    // Subscribe to real-time updates
    this.subscribeToUpdates(execution.id);
    
    return execution;
  }
  
  private subscribeToUpdates(executionId: string) {
    const wsClient = new WebSocketClient();
    const socket = wsClient.connect('workflow');
    
    socket.on(`workflow:${executionId}:update`, (update) => {
      this.handleWorkflowUpdate(executionId, update);
    });
    
    socket.on(`workflow:${executionId}:complete`, (result) => {
      this.handleWorkflowComplete(executionId, result);
    });
    
    socket.on(`workflow:${executionId}:error`, (error) => {
      this.handleWorkflowError(executionId, error);
    });
  }
  
  private handleWorkflowUpdate(executionId: string, update: any) {
    const execution = this.activeWorkflows.get(executionId);
    if (execution) {
      execution.currentStep = update.step;
      execution.progress = update.progress;
      
      // Notify UI components
      this.notifySubscribers(executionId, 'update', execution);
    }
  }
  
  private handleWorkflowComplete(executionId: string, result: any) {
    const execution = this.activeWorkflows.get(executionId);
    if (execution) {
      execution.status = 'completed';
      execution.result = result;
      execution.endTime = new Date();
      
      // Notify UI components
      this.notifySubscribers(executionId, 'complete', execution);
      
      // Clean up
      setTimeout(() => {
        this.activeWorkflows.delete(executionId);
      }, 60000); // Keep for 1 minute
    }
  }
  
  private handleWorkflowError(executionId: string, error: any) {
    const execution = this.activeWorkflows.get(executionId);
    if (execution) {
      execution.status = 'failed';
      execution.error = error;
      execution.endTime = new Date();
      
      // Notify UI components
      this.notifySubscribers(executionId, 'error', execution);
    }
  }
}
```

## Error Handling and Retry Strategies

### Unified Error Handler
```typescript
// frontend/src/services/error/error-handler.ts
export class ErrorHandler {
  private static retryConfig = {
    maxRetries: 3,
    retryDelay: 1000,
    backoffMultiplier: 2,
  };
  
  static async handleApiError(error: any): Promise<void> {
    if (error.response) {
      // Server responded with error
      switch (error.response.status) {
        case 400:
          this.handleBadRequest(error.response.data);
          break;
        case 401:
          this.handleUnauthorized();
          break;
        case 403:
          this.handleForbidden(error.response.data);
          break;
        case 404:
          this.handleNotFound(error.response.data);
          break;
        case 429:
          this.handleRateLimited(error.response);
          break;
        case 500:
        case 502:
        case 503:
        case 504:
          this.handleServerError(error.response);
          break;
        default:
          this.handleGenericError(error);
      }
    } else if (error.request) {
      // Request made but no response
      this.handleNetworkError(error);
    } else {
      // Request setup error
      this.handleRequestError(error);
    }
  }
  
  private static handleRateLimited(response: any) {
    const retryAfter = response.headers['retry-after'];
    const message = `Rate limited. Please retry after ${retryAfter} seconds`;
    
    // Show user notification
    showNotification({
      type: 'warning',
      message,
      duration: parseInt(retryAfter) * 1000,
    });
    
    // Optionally implement automatic retry
    if (retryAfter) {
      setTimeout(() => {
        // Retry the request
        this.retryRequest(response.config);
      }, parseInt(retryAfter) * 1000);
    }
  }
  
  static async retryRequest(
    config: any,
    attempt: number = 1
  ): Promise<any> {
    if (attempt > this.retryConfig.maxRetries) {
      throw new Error('Max retry attempts exceeded');
    }
    
    const delay = this.retryConfig.retryDelay * 
      Math.pow(this.retryConfig.backoffMultiplier, attempt - 1);
    
    await new Promise(resolve => setTimeout(resolve, delay));
    
    try {
      return await axios.request(config);
    } catch (error) {
      return this.retryRequest(config, attempt + 1);
    }
  }
}
```

## Performance Optimization

### Request Batching
```typescript
// frontend/src/services/optimization/request-batcher.ts
export class RequestBatcher {
  private batchQueue: Map<string, BatchRequest[]> = new Map();
  private batchTimers: Map<string, NodeJS.Timeout> = new Map();
  private batchSize = 10;
  private batchDelay = 50; // ms
  
  async addToBatch(
    endpoint: string,
    request: BatchRequest
  ): Promise<any> {
    if (!this.batchQueue.has(endpoint)) {
      this.batchQueue.set(endpoint, []);
    }
    
    const queue = this.batchQueue.get(endpoint)!;
    queue.push(request);
    
    // Return promise that resolves when batch is processed
    return new Promise((resolve, reject) => {
      request.resolve = resolve;
      request.reject = reject;
      
      // Process batch if size limit reached
      if (queue.length >= this.batchSize) {
        this.processBatch(endpoint);
      } else {
        // Schedule batch processing
        this.scheduleBatch(endpoint);
      }
    });
  }
  
  private scheduleBatch(endpoint: string) {
    // Clear existing timer
    const existingTimer = this.batchTimers.get(endpoint);
    if (existingTimer) {
      clearTimeout(existingTimer);
    }
    
    // Set new timer
    const timer = setTimeout(() => {
      this.processBatch(endpoint);
    }, this.batchDelay);
    
    this.batchTimers.set(endpoint, timer);
  }
  
  private async processBatch(endpoint: string) {
    const queue = this.batchQueue.get(endpoint);
    if (!queue || queue.length === 0) return;
    
    // Clear queue and timer
    this.batchQueue.set(endpoint, []);
    const timer = this.batchTimers.get(endpoint);
    if (timer) {
      clearTimeout(timer);
      this.batchTimers.delete(endpoint);
    }
    
    try {
      // Send batch request
      const response = await axios.post(
        `${API_CONFIG.gateway.baseUrl}${endpoint}/batch`,
        {
          requests: queue.map(r => r.data),
        }
      );
      
      // Resolve individual promises
      response.data.results.forEach((result: any, index: number) => {
        if (result.error) {
          queue[index].reject(result.error);
        } else {
          queue[index].resolve(result.data);
        }
      });
    } catch (error) {
      // Reject all promises in batch
      queue.forEach(request => request.reject(error));
    }
  }
}
```

## Testing Integration Points

### Integration Test Example
```typescript
// frontend/src/tests/integration/kong-integration.test.ts
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { KongApiClient } from '@/services/api/kong-client';
import { TokenManager } from '@/services/auth/token-manager';

describe('Kong API Gateway Integration', () => {
  let apiClient: KongApiClient;
  
  beforeAll(async () => {
    apiClient = new KongApiClient();
    
    // Mock authentication
    const mockToken = 'test-jwt-token';
    TokenManager.setTokens(mockToken, 'refresh-token', 3600);
  });
  
  afterAll(() => {
    TokenManager.clearTokens();
  });
  
  it('should route requests through Kong to identity service', async () => {
    const response = await apiClient.get('/api/v1/auth/health');
    
    expect(response.status).toBe(200);
    expect(response.headers['x-kong-proxy-latency']).toBeDefined();
    expect(response.data.service).toBe('identity-service');
  });
  
  it('should handle Kong rate limiting', async () => {
    // Make multiple requests to trigger rate limit
    const requests = Array(101).fill(null).map(() => 
      apiClient.get('/api/v1/users')
    );
    
    try {
      await Promise.all(requests);
    } catch (error: any) {
      expect(error.response.status).toBe(429);
      expect(error.response.headers['retry-after']).toBeDefined();
    }
  });
  
  it('should retry failed requests with exponential backoff', async () => {
    // Mock network failure
    const mockError = new Error('Network error');
    mockError.code = 'ECONNREFUSED';
    
    const startTime = Date.now();
    
    try {
      await apiClient.getWithRetry('/api/v1/users', {
        maxRetries: 3,
        retryDelay: 100,
      });
    } catch (error) {
      const elapsed = Date.now() - startTime;
      
      // Should have tried 3 times with exponential backoff
      // 100ms + 200ms + 400ms = 700ms minimum
      expect(elapsed).toBeGreaterThan(700);
    }
  });
});
```

## Monitoring and Observability

### Request Tracking
```typescript
// frontend/src/services/monitoring/request-tracker.ts
export class RequestTracker {
  private static requests: Map<string, RequestMetrics> = new Map();
  
  static trackRequest(config: any): string {
    const requestId = this.generateRequestId();
    
    const metrics: RequestMetrics = {
      id: requestId,
      method: config.method,
      url: config.url,
      timestamp: Date.now(),
      service: this.extractService(config.url),
    };
    
    this.requests.set(requestId, metrics);
    
    // Add tracking headers
    config.headers['X-Request-Id'] = requestId;
    config.headers['X-Client-Timestamp'] = metrics.timestamp.toString();
    
    return requestId;
  }
  
  static trackResponse(requestId: string, response: any) {
    const metrics = this.requests.get(requestId);
    if (metrics) {
      metrics.responseTime = Date.now() - metrics.timestamp;
      metrics.status = response.status;
      metrics.kongLatency = response.headers['x-kong-proxy-latency'];
      metrics.upstreamLatency = response.headers['x-kong-upstream-latency'];
      
      // Send metrics to analytics
      this.sendMetrics(metrics);
      
      // Clean up old requests
      if (this.requests.size > 1000) {
        this.cleanupOldRequests();
      }
    }
  }
  
  private static sendMetrics(metrics: RequestMetrics) {
    // Send to analytics service
    if (window.analytics) {
      window.analytics.track('api_request', {
        ...metrics,
        performance: {
          total: metrics.responseTime,
          kong: metrics.kongLatency,
          upstream: metrics.upstreamLatency,
        },
      });
    }
  }
  
  private static extractService(url: string): string {
    const match = url.match(/\/api\/v1\/(\w+)/);
    return match ? match[1] : 'unknown';
  }
  
  private static generateRequestId(): string {
    return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}
```

## Best Practices

### 1. Always Use Kong Gateway
- Never bypass Kong to directly access services
- All API calls should go through `http://localhost:8000`
- Use service discovery patterns for dynamic routing

### 2. Handle Authentication Properly
- Store JWT tokens in memory or sessionStorage
- Use httpOnly cookies for refresh tokens
- Implement automatic token refresh

### 3. Implement Proper Error Handling
- Handle all HTTP status codes appropriately
- Implement retry logic with exponential backoff
- Provide user-friendly error messages

### 4. Optimize Performance
- Batch requests when possible
- Implement request deduplication
- Use caching strategies with TanStack Query

### 5. Monitor Everything
- Track all API requests and responses
- Monitor WebSocket connection health
- Send metrics to observability platform

### 6. Test Integration Points
- Write integration tests for all service connections
- Test error scenarios and edge cases
- Validate Kong-specific features (rate limiting, etc.)

---

**Document Status**: COMPLETE
**Created**: September 11, 2025
**Maintained by**: Technical Lead Agent
**For**: Frontend and Backend Agents