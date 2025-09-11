/**
 * ServiceOrchestrator Integration Module
 * Provides easy access to cross-service orchestration capabilities
 */

export { ServiceOrchestrator } from './ServiceOrchestrator';
export type {
  ServiceClients,
  UserOnboardingData,
  DocumentWorkflowOperation,
  SearchAndNotifyOperation,
  AIProcessingOperation,
  CollaborationSetupOperation,
  SystemHealthCheck,
  OperationResult,
  BatchOperation,
  OrchestratorConfig,
  ServiceHealthConfig,
  OrchestratorEvent,
  OrchestratorMetrics,
  ServiceError,
  OrchestratorError,
} from './types';

// Import existing service clients
import { apiClient } from '@/lib/api/client';
import { communicationClient } from '@/lib/api/services/communication';
import { contentClient } from '@/lib/api/services/content';
import { workflowClient } from '@/lib/api/services/workflow';
import { ServiceOrchestrator } from './ServiceOrchestrator';
import type { OrchestratorConfig, ServiceHealthConfig } from './types';

/**
 * Factory function to create a ServiceOrchestrator instance with default clients
 */
export function createServiceOrchestrator(
  config?: Partial<OrchestratorConfig>,
  healthConfig?: Partial<ServiceHealthConfig>
): ServiceOrchestrator {
  return new ServiceOrchestrator(
    apiClient,
    communicationClient,
    contentClient,
    workflowClient,
    config,
    healthConfig
  );
}

/**
 * Default ServiceOrchestrator instance using existing clients
 */
export const serviceOrchestrator = createServiceOrchestrator();

/**
 * Utility function to create a custom orchestrator with specific clients
 */
export function createCustomOrchestrator(
  identityClient: any,
  communicationClient: any,
  contentClient: any,
  workflowClient: any,
  config?: Partial<OrchestratorConfig>,
  healthConfig?: Partial<ServiceHealthConfig>
): ServiceOrchestrator {
  return new ServiceOrchestrator(
    identityClient,
    communicationClient,
    contentClient,
    workflowClient,
    config,
    healthConfig
  );
}

// Re-export common types for convenience
export type { User } from '@/types/auth';
export type { Notification, Message, Conversation } from '@/lib/api/services/communication';
export type { Document, DocumentVersion, SearchResult } from '@/lib/api/services/content';
export type { Workflow, WorkflowExecution, AITask, AITaskExecution } from '@/lib/api/services/workflow';