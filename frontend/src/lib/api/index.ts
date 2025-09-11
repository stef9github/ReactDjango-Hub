/**
 * API Module Barrel Export
 * Centralized exports for API client and utilities including microservices through Kong Gateway
 */

// Main API client (Identity Service)
export {
  ApiClient,
  ApiException,
  apiClient,
  LocalStorageTokenStorage,
  HTTP_STATUS,
} from './client';

// Utility functions
export {
  isApiException,
  getErrorMessage,
  getErrorDetails,
} from './client';

// Types
export type {
  ApiError,
  TokenStorage,
} from './client';

// Re-export auth types for convenience
export type {
  RegisterRequest,
  RegisterResponse,
  LoginRequest,
  TokenResponse,
  VerifyEmailRequest,
  ResendVerificationRequest,
  MessageResponse,
  User,
  ApiResponse,
  AuthApiClient,
  ApiClientConfig,
} from '@/types/auth';

// Microservices API clients (through Kong Gateway)
export {
  BaseServiceClient,
  CommunicationServiceClient,
  communicationClient,
  ContentServiceClient,
  contentClient,
  WorkflowServiceClient,
  workflowClient,
  ServicesClient,
  servicesClient,
} from './services';

// Microservices types
export type {
  BaseServiceConfig,
  // Communication Service types
  Notification,
  Message,
  Conversation,
  CreateNotificationRequest,
  SendMessageRequest,
  CreateConversationRequest,
  // Content Service types
  Document,
  DocumentVersion,
  SearchResult,
  CreateDocumentRequest,
  UpdateDocumentRequest,
  SearchDocumentsRequest,
  UploadResponse,
  // Workflow Service types
  Workflow,
  WorkflowStep,
  WorkflowExecution,
  WorkflowStepExecution,
  AITask,
  AITaskExecution,
  CreateWorkflowRequest,
  UpdateWorkflowRequest,
  ExecuteWorkflowRequest,
  CreateAITaskRequest,
} from './services';