/**
 * ServiceOrchestrator Types
 * Defines types for cross-service operations and orchestration
 */

import type { User, TokenResponse } from '@/types/auth';
import type { Notification, Message, Conversation } from '@/lib/api/services/communication';
import type { Document, DocumentVersion, SearchResult } from '@/lib/api/services/content';
import type { Workflow, WorkflowExecution, AITask, AITaskExecution } from '@/lib/api/services/workflow';

// Service client interfaces for orchestration
export interface ServiceClients {
  identity: {
    getCurrentUser(): Promise<User>;
    login(credentials: { email: string; password: string }): Promise<TokenResponse>;
    logout(): Promise<void>;
    refreshToken(token: string): Promise<TokenResponse>;
  };
  communication: {
    getNotifications(limit?: number, offset?: number): Promise<Notification[]>;
    createNotification(data: any): Promise<Notification>;
    sendMessage(data: any): Promise<Message>;
    getConversations(): Promise<Conversation[]>;
    createConversation(data: any): Promise<Conversation>;
  };
  content: {
    getDocuments(limit?: number, offset?: number, filters?: Record<string, any>): Promise<Document[]>;
    searchDocuments(searchParams: any): Promise<SearchResult>;
    uploadFile(file: File, documentData: any): Promise<any>;
    getDocumentVersions(documentId: string): Promise<DocumentVersion[]>;
  };
  workflow: {
    getWorkflows(limit?: number, offset?: number, status?: string): Promise<Workflow[]>;
    executeWorkflow(id: string, data: any): Promise<WorkflowExecution>;
    getAITasks(limit?: number, offset?: number, taskType?: string): Promise<AITask[]>;
    executeAITask(taskId: string, inputData: Record<string, any>): Promise<AITaskExecution>;
  };
}

// Cross-service operation types
export interface UserOnboardingData {
  user: User;
  welcomeNotification: Notification;
  defaultDocuments: Document[];
  initialWorkflows: Workflow[];
}

export interface DocumentWorkflowOperation {
  document: Document;
  workflow: Workflow;
  execution: WorkflowExecution;
  notifications: Notification[];
}

export interface SearchAndNotifyOperation {
  searchResults: SearchResult;
  relevantDocuments: Document[];
  notificationsSent: Notification[];
  workflowsTriggered: WorkflowExecution[];
}

export interface AIProcessingOperation {
  inputDocument: Document;
  aiTask: AITask;
  execution: AITaskExecution;
  outputDocument?: Document;
  notifications: Notification[];
}

export interface CollaborationSetupOperation {
  document: Document;
  conversation: Conversation;
  participants: User[];
  notifications: Notification[];
  workflow?: Workflow;
}

export interface SystemHealthCheck {
  identity: { status: string; service: string; version: string };
  communication: { status: string; service: string; version: string };
  content: { status: string; service: string; version: string };
  workflow: { status: string; service: string; version: string };
  overall: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
}

// Operation result types
export interface OperationResult<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  details?: Record<string, any>;
  duration?: number;
  serviceErrors?: Record<string, string>;
}

export interface BatchOperation<T = any> {
  id: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'partial';
  operations: Array<{
    service: string;
    operation: string;
    status: 'pending' | 'running' | 'completed' | 'failed';
    result?: T;
    error?: string;
  }>;
  startedAt: string;
  completedAt?: string;
  totalDuration?: number;
}

// Configuration types
export interface OrchestratorConfig {
  retryAttempts: number;
  retryDelay: number;
  timeout: number;
  enableBatching: boolean;
  batchSize: number;
  enableMetrics: boolean;
  enableLogging: boolean;
}

export interface ServiceHealthConfig {
  checkInterval: number;
  timeout: number;
  retryAttempts: number;
  enableAlerts: boolean;
}

// Event types for orchestrator
export interface OrchestratorEvent {
  type: 'operation_start' | 'operation_complete' | 'operation_error' | 'service_health_change';
  timestamp: string;
  operationId?: string;
  serviceName?: string;
  data?: Record<string, any>;
  error?: string;
}

// Orchestrator metrics
export interface OrchestratorMetrics {
  totalOperations: number;
  successfulOperations: number;
  failedOperations: number;
  averageOperationTime: number;
  serviceAvailability: Record<string, number>;
  lastHealthCheck: string;
  uptime: number;
}

// Error types
export interface ServiceError extends Error {
  service: string;
  operation: string;
  statusCode?: number;
  retryable: boolean;
  originalError?: Error;
}

export interface OrchestratorError extends Error {
  operationId: string;
  operationType: string;
  serviceErrors: ServiceError[];
  partialResults?: Record<string, any>;
}