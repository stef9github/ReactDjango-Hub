/**
 * Microservices API Clients
 * Centralized exports for all service API clients that communicate through Kong Gateway
 */

// Base service client
export { BaseServiceClient } from './base';
export type { BaseServiceConfig, TokenStorage } from './base';

// Communication Service
export { CommunicationServiceClient, communicationClient } from './communication';
export type {
  Notification,
  Message,
  Conversation,
  CreateNotificationRequest,
  SendMessageRequest,
  CreateConversationRequest,
} from './communication';

// Content Service
export { ContentServiceClient, contentClient } from './content';
export type {
  Document,
  DocumentVersion,
  SearchResult,
  CreateDocumentRequest,
  UpdateDocumentRequest,
  SearchDocumentsRequest,
  UploadResponse,
} from './content';

// Workflow Intelligence Service
export { WorkflowServiceClient, workflowClient } from './workflow';
export type {
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
} from './workflow';

// Unified services client that provides access to all microservices
export class ServicesClient {
  public readonly communication: CommunicationServiceClient;
  public readonly content: ContentServiceClient;
  public readonly workflow: WorkflowServiceClient;

  constructor() {
    this.communication = communicationClient;
    this.content = contentClient;
    this.workflow = workflowClient;
  }

  // Health check all services
  async healthCheckAll(): Promise<Record<string, any>> {
    const results: Record<string, any> = {};

    try {
      results.communication = await this.communication.healthCheck();
    } catch (error) {
      results.communication = { status: 'error', error: error instanceof Error ? error.message : 'Unknown error' };
    }

    try {
      results.content = await this.content.healthCheck();
    } catch (error) {
      results.content = { status: 'error', error: error instanceof Error ? error.message : 'Unknown error' };
    }

    try {
      results.workflow = await this.workflow.healthCheck();
    } catch (error) {
      results.workflow = { status: 'error', error: error instanceof Error ? error.message : 'Unknown error' };
    }

    return results;
  }
}

// Default unified services client instance
export const servicesClient = new ServicesClient();