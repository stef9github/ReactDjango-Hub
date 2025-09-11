# ServiceOrchestrator Documentation

The ServiceOrchestrator is a client-side coordination layer that orchestrates complex operations across multiple microservices in the ReactDjango Hub. It provides a unified interface for cross-service workflows while maintaining proper service boundaries.

## Overview

The ServiceOrchestrator handles:

- **Cross-service operations**: Coordinate workflows that span multiple services
- **Error handling**: Centralized error handling with retry mechanisms
- **Health monitoring**: Track service availability and system health
- **Metrics collection**: Monitor operation performance and success rates
- **Event management**: Emit and handle orchestration events

## Basic Usage

### Creating an Orchestrator Instance

```typescript
import { createServiceOrchestrator, serviceOrchestrator } from '@/services/integration';

// Use the default instance (recommended)
const orchestrator = serviceOrchestrator;

// Or create a custom instance
const customOrchestrator = createServiceOrchestrator({
  retryAttempts: 5,
  timeout: 60000,
  enableMetrics: true,
});
```

### Configuration Options

```typescript
const config = {
  retryAttempts: 3,        // Number of retry attempts for failed operations
  retryDelay: 1000,        // Delay between retries (ms)
  timeout: 30000,          // Operation timeout (ms)
  enableBatching: true,    // Enable operation batching
  batchSize: 10,           // Maximum batch size
  enableMetrics: true,     // Enable metrics collection
  enableLogging: true,     // Enable operation logging
};
```

## Core Operations

### 1. User Onboarding

Complete user onboarding across all services:

```typescript
const result = await orchestrator.onboardNewUser({
  email: 'user@example.com',
  password: 'securePassword123',
  first_name: 'John',
  last_name: 'Doe',
});

if (result.success) {
  const { user, welcomeNotification, defaultDocuments, initialWorkflows } = result.data;
  console.log('User onboarded successfully:', user.email);
} else {
  console.error('Onboarding failed:', result.error);
}
```

### 2. Document AI Processing

Process documents through AI workflows with notifications:

```typescript
const result = await orchestrator.processDocumentWithAI(
  'document-id-123',
  'ai-workflow-id-456',
  ['user-1', 'user-2'] // Users to notify
);

if (result.success) {
  const { document, workflow, execution, notifications } = result.data;
  console.log('AI processing started:', execution.id);
}
```

### 3. Search and Workflow Triggering

Search content and automatically trigger relevant workflows:

```typescript
const result = await orchestrator.searchAndTriggerWorkflows(
  'important documents',
  true, // Enable workflow triggering
  ['user-1'] // Users to notify about results
);

if (result.success) {
  const { searchResults, workflowsTriggered, notificationsSent } = result.data;
  console.log(`Found ${searchResults.total} results, triggered ${workflowsTriggered.length} workflows`);
}
```

### 4. Collaboration Setup

Set up collaborative workspaces for documents:

```typescript
const result = await orchestrator.setupCollaborativeWorkspace(
  'document-id-123',
  ['user1@example.com', 'user2@example.com'],
  'collaboration-workflow-template' // Optional workflow template
);

if (result.success) {
  const { document, conversation, notifications } = result.data;
  console.log('Collaboration workspace created:', conversation.id);
}
```

## Health Monitoring

### System Health Check

```typescript
const health = await orchestrator.performHealthCheck();

console.log('Overall system health:', health.overall);
console.log('Service statuses:', {
  identity: health.identity.status,
  communication: health.communication.status,
  content: health.content.status,
  workflow: health.workflow.status,
});
```

### Metrics Monitoring

```typescript
const metrics = orchestrator.getMetrics();

console.log('Orchestrator metrics:', {
  totalOperations: metrics.totalOperations,
  successRate: (metrics.successfulOperations / metrics.totalOperations) * 100,
  averageTime: metrics.averageOperationTime,
  uptime: metrics.uptime,
  serviceAvailability: metrics.serviceAvailability,
});
```

## Event Handling

### Listening to Orchestrator Events

```typescript
orchestrator.addEventListener((event) => {
  switch (event.type) {
    case 'operation_start':
      console.log('Operation started:', event.operationId);
      break;
    case 'operation_complete':
      console.log('Operation completed:', event.operationId);
      break;
    case 'operation_error':
      console.error('Operation failed:', event.error);
      break;
    case 'service_health_change':
      console.log('Service health changed:', event.data);
      break;
  }
});
```

## React Integration Example

### Custom Hook for Orchestrator Operations

```typescript
// hooks/useOrchestrator.ts
import { useState, useCallback } from 'react';
import { serviceOrchestrator } from '@/services/integration';
import type { OperationResult } from '@/services/integration';

export function useOrchestrator() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const executeOperation = useCallback(async <T>(
    operation: () => Promise<OperationResult<T>>
  ): Promise<T | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await operation();
      if (result.success) {
        return result.data || null;
      } else {
        setError(result.error || 'Operation failed');
        return null;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const onboardUser = useCallback((userData: any) => {
    return executeOperation(() => serviceOrchestrator.onboardNewUser(userData));
  }, [executeOperation]);

  const processDocument = useCallback((documentId: string, workflowId: string, notifyUsers: string[]) => {
    return executeOperation(() => serviceOrchestrator.processDocumentWithAI(documentId, workflowId, notifyUsers));
  }, [executeOperation]);

  const searchAndTrigger = useCallback((query: string, enableWorkflows: boolean, notifyUsers: string[]) => {
    return executeOperation(() => serviceOrchestrator.searchAndTriggerWorkflows(query, enableWorkflows, notifyUsers));
  }, [executeOperation]);

  return {
    isLoading,
    error,
    onboardUser,
    processDocument,
    searchAndTrigger,
    orchestrator: serviceOrchestrator,
  };
}
```

### Component Usage

```typescript
// components/UserOnboarding.tsx
import React, { useState } from 'react';
import { useOrchestrator } from '@/hooks/useOrchestrator';

export function UserOnboarding() {
  const { onboardUser, isLoading, error } = useOrchestrator();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const result = await onboardUser(formData);
    if (result) {
      console.log('User onboarded successfully:', result);
      // Handle success (redirect, show success message, etc.)
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Form fields */}
      <button type="submit" disabled={isLoading}>
        {isLoading ? 'Creating Account...' : 'Create Account'}
      </button>
      {error && <div className="error">{error}</div>}
    </form>
  );
}
```

## Error Handling

The ServiceOrchestrator provides comprehensive error handling:

```typescript
// All operations return OperationResult<T>
interface OperationResult<T> {
  success: boolean;
  data?: T;
  error?: string;
  details?: Record<string, any>;
  duration?: number;
  serviceErrors?: Record<string, string>; // Per-service error details
}
```

### Retry Logic

Operations automatically retry on failure based on configuration:

```typescript
const orchestrator = createServiceOrchestrator({
  retryAttempts: 3,    // Retry up to 3 times
  retryDelay: 1000,    // Wait 1 second between retries
  timeout: 30000,      // 30 second timeout per operation
});
```

## Best Practices

1. **Use the default instance**: `serviceOrchestrator` is pre-configured and ready to use
2. **Handle errors gracefully**: Always check the `success` property of operation results
3. **Monitor metrics**: Use `getMetrics()` for monitoring and alerting
4. **Listen to events**: Implement event listeners for better user experience
5. **Clean up resources**: Call `dispose()` when the orchestrator is no longer needed
6. **Configure appropriately**: Adjust timeouts and retry settings based on your use case

## Service Boundaries

The ServiceOrchestrator respects service boundaries:

- **Identity Service**: Authentication, user management, tokens
- **Communication Service**: Notifications, messaging, conversations
- **Content Service**: Document management, search, file operations
- **Workflow Service**: Process automation, AI tasks, workflow execution

Each service maintains its own API and data models, while the orchestrator coordinates cross-service operations without violating service independence.

## Performance Considerations

- Operations are executed asynchronously with proper error boundaries
- Failed operations in one service don't block others
- Metrics collection helps identify performance bottlenecks
- Batching can be enabled for high-throughput scenarios
- Health monitoring ensures degraded services are handled gracefully

## Cleanup

Always dispose of the orchestrator when it's no longer needed:

```typescript
// In component cleanup or app shutdown
orchestrator.dispose();
```

This stops health monitoring intervals and clears event listeners to prevent memory leaks.