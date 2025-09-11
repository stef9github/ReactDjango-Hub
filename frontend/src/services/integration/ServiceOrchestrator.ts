/**
 * ServiceOrchestrator
 * Orchestrates cross-service operations and manages complex workflows
 * that span multiple microservices in the ReactDjango Hub
 */

import type { ApiClient } from '@/lib/api/client';
import type { CommunicationServiceClient } from '@/lib/api/services/communication';
import type { ContentServiceClient } from '@/lib/api/services/content';
import type { WorkflowServiceClient } from '@/lib/api/services/workflow';
import type {
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
import type { User } from '@/types/auth';

export class ServiceOrchestrator {
  private clients: ServiceClients;
  private config: OrchestratorConfig;
  private healthConfig: ServiceHealthConfig;
  private metrics: OrchestratorMetrics;
  private eventListeners: Array<(event: OrchestratorEvent) => void> = [];
  private operationQueue: Map<string, BatchOperation> = new Map();
  private healthCheckInterval?: NodeJS.Timeout;
  
  // Multi-vertical support per Common Platform Patterns
  private verticalContext: string = 'medical'; // Default to medical vertical
  private featureFlags: Record<string, boolean> = {};

  constructor(
    identityClient: ApiClient,
    communicationClient: CommunicationServiceClient,
    contentClient: ContentServiceClient,
    workflowClient: WorkflowServiceClient,
    config?: Partial<OrchestratorConfig>,
    healthConfig?: Partial<ServiceHealthConfig>
  ) {
    // Initialize service clients with consistent interface
    this.clients = {
      identity: {
        getCurrentUser: () => identityClient.getCurrentUser(),
        login: (credentials) => identityClient.login(credentials),
        logout: () => identityClient.logout(),
        refreshToken: (token) => identityClient.refreshToken(token),
      },
      communication: {
        getNotifications: (limit, offset) => communicationClient.getNotifications(limit, offset),
        createNotification: (data) => communicationClient.createNotification(data),
        sendMessage: (data) => communicationClient.sendMessage(data),
        getConversations: () => communicationClient.getConversations(),
        createConversation: (data) => communicationClient.createConversation(data),
      },
      content: {
        getDocuments: (limit, offset, filters) => contentClient.getDocuments(limit, offset, filters),
        searchDocuments: (searchParams) => contentClient.searchDocuments(searchParams),
        uploadFile: (file, documentData) => contentClient.uploadFile(file, documentData),
        getDocumentVersions: (documentId) => contentClient.getDocumentVersions(documentId),
      },
      workflow: {
        getWorkflows: (limit, offset, status) => workflowClient.getWorkflows(limit, offset, status),
        executeWorkflow: (id, data) => workflowClient.executeWorkflow(id, data),
        getAITasks: (limit, offset, taskType) => workflowClient.getAITasks(limit, offset, taskType),
        executeAITask: (taskId, inputData) => workflowClient.executeAITask(taskId, inputData),
      },
    };

    // Initialize configuration
    this.config = {
      retryAttempts: 3,
      retryDelay: 1000,
      timeout: 30000,
      enableBatching: true,
      batchSize: 10,
      enableMetrics: true,
      enableLogging: true,
      ...config,
    };

    this.healthConfig = {
      checkInterval: 60000, // 1 minute
      timeout: 5000,
      retryAttempts: 2,
      enableAlerts: true,
      ...healthConfig,
    };

    // Initialize metrics
    this.metrics = {
      totalOperations: 0,
      successfulOperations: 0,
      failedOperations: 0,
      averageOperationTime: 0,
      serviceAvailability: {
        identity: 100,
        communication: 100,
        content: 100,
        workflow: 100,
      },
      lastHealthCheck: new Date().toISOString(),
      uptime: Date.now(),
    };

    // Start health monitoring if enabled
    if (this.healthConfig.enableAlerts) {
      this.startHealthMonitoring();
    }
  }

  // ===========================================
  // CORE ORCHESTRATION METHODS
  // ===========================================

  /**
   * Complete user onboarding process across all services
   */
  async onboardNewUser(userData: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  }): Promise<OperationResult<UserOnboardingData>> {
    const operationId = this.generateOperationId('user_onboarding');
    const startTime = Date.now();

    try {
      this.emitEvent({
        type: 'operation_start',
        timestamp: new Date().toISOString(),
        operationId,
        data: { operation: 'user_onboarding', email: userData.email },
      });

      // Step 1: Create user account (identity service)
      const loginResult = await this.clients.identity.login({
        email: userData.email,
        password: userData.password,
      });

      const user = loginResult.user;

      // Step 2: Create welcome notification (communication service)
      const welcomeNotification = await this.clients.communication.createNotification({
        type: 'success',
        title: 'Welcome to ReactDjango Hub!',
        message: `Hello ${user.first_name}, welcome to your new workspace.`,
        data: { user_id: user.id, onboarding: true },
      });

      // Step 3: Create default documents (content service)
      const defaultDocuments = await Promise.all([
        this.clients.content.getDocuments(5, 0, { is_template: true }),
      ]);

      // Step 4: Set up initial workflows (workflow service)
      const initialWorkflows = await this.clients.workflow.getWorkflows(3, 0, 'template');

      const result: UserOnboardingData = {
        user,
        welcomeNotification,
        defaultDocuments: defaultDocuments[0] || [],
        initialWorkflows,
      };

      this.updateMetrics(true, Date.now() - startTime);
      this.emitEvent({
        type: 'operation_complete',
        timestamp: new Date().toISOString(),
        operationId,
        data: { operation: 'user_onboarding', success: true },
      });

      return { success: true, data: result, duration: Date.now() - startTime };
    } catch (error) {
      this.updateMetrics(false, Date.now() - startTime);
      this.emitEvent({
        type: 'operation_error',
        timestamp: new Date().toISOString(),
        operationId,
        error: error instanceof Error ? error.message : 'Unknown error',
      });

      return {
        success: false,
        error: error instanceof Error ? error.message : 'User onboarding failed',
        duration: Date.now() - startTime,
      };
    }
  }

  /**
   * Process document through AI workflow and notify stakeholders
   */
  async processDocumentWithAI(
    documentId: string,
    workflowId: string,
    notifyUsers: string[] = []
  ): Promise<OperationResult<DocumentWorkflowOperation>> {
    const operationId = this.generateOperationId('document_ai_processing');
    const startTime = Date.now();

    try {
      this.emitEvent({
        type: 'operation_start',
        timestamp: new Date().toISOString(),
        operationId,
        data: { operation: 'document_ai_processing', documentId, workflowId },
      });

      // Step 1: Get document details
      const document = await this.clients.content.getDocuments(1, 0, { id: documentId });
      if (!document.length) {
        throw new Error(`Document ${documentId} not found`);
      }

      // Step 2: Get workflow details
      const workflows = await this.clients.workflow.getWorkflows(1, 0);
      const workflow = workflows.find(w => w.id === workflowId);
      if (!workflow) {
        throw new Error(`Workflow ${workflowId} not found`);
      }

      // Step 3: Execute workflow
      const execution = await this.clients.workflow.executeWorkflow(workflowId, {
        input_data: {
          document_id: documentId,
          document_content: document[0],
        },
        execution_mode: 'asynchronous',
      });

      // Step 4: Send notifications to stakeholders
      const notifications = await Promise.all(
        notifyUsers.map(userId =>
          this.clients.communication.createNotification({
            type: 'info',
            title: 'Document Processing Started',
            message: `AI processing has started for document "${document[0].title}"`,
            recipient_id: userId,
            data: {
              document_id: documentId,
              workflow_id: workflowId,
              execution_id: execution.id,
            },
          })
        )
      );

      const result: DocumentWorkflowOperation = {
        document: document[0],
        workflow,
        execution,
        notifications,
      };

      this.updateMetrics(true, Date.now() - startTime);
      this.emitEvent({
        type: 'operation_complete',
        timestamp: new Date().toISOString(),
        operationId,
        data: { operation: 'document_ai_processing', success: true },
      });

      return { success: true, data: result, duration: Date.now() - startTime };
    } catch (error) {
      this.updateMetrics(false, Date.now() - startTime);
      this.emitEvent({
        type: 'operation_error',
        timestamp: new Date().toISOString(),
        operationId,
        error: error instanceof Error ? error.message : 'Unknown error',
      });

      return {
        success: false,
        error: error instanceof Error ? error.message : 'Document AI processing failed',
        duration: Date.now() - startTime,
      };
    }
  }

  /**
   * Search across all content and trigger relevant workflows
   */
  async searchAndTriggerWorkflows(
    searchQuery: string,
    triggerWorkflows: boolean = true,
    notifyUsers: string[] = []
  ): Promise<OperationResult<SearchAndNotifyOperation>> {
    const operationId = this.generateOperationId('search_and_trigger');
    const startTime = Date.now();

    try {
      this.emitEvent({
        type: 'operation_start',
        timestamp: new Date().toISOString(),
        operationId,
        data: { operation: 'search_and_trigger', query: searchQuery },
      });

      // Step 1: Search documents
      const searchResults = await this.clients.content.searchDocuments({
        query: searchQuery,
        limit: 20,
        sort_by: 'relevance',
        sort_order: 'desc',
      });

      // Step 2: Get relevant documents
      const relevantDocuments = searchResults.documents.slice(0, 5);

      // Step 3: Trigger workflows if enabled
      let workflowsTriggered: any[] = [];
      if (triggerWorkflows && relevantDocuments.length > 0) {
        const workflows = await this.clients.workflow.getWorkflows(undefined, undefined, 'active');
        const relevantWorkflows = workflows.filter(w => 
          w.trigger_type === 'event' && 
          w.trigger_config?.event_type === 'search_results'
        );

        workflowsTriggered = await Promise.all(
          relevantWorkflows.map(workflow =>
            this.clients.workflow.executeWorkflow(workflow.id, {
              input_data: {
                search_query: searchQuery,
                results: relevantDocuments,
                user_context: 'search_operation',
              },
              execution_mode: 'asynchronous',
            })
          )
        );
      }

      // Step 4: Send notifications
      const notificationsSent = await Promise.all(
        notifyUsers.map(userId =>
          this.clients.communication.createNotification({
            type: 'info',
            title: 'Search Results Available',
            message: `Found ${searchResults.total} results for "${searchQuery}"`,
            recipient_id: userId,
            data: {
              search_query: searchQuery,
              total_results: searchResults.total,
              relevant_documents: relevantDocuments.length,
              workflows_triggered: workflowsTriggered.length,
            },
          })
        )
      );

      const result: SearchAndNotifyOperation = {
        searchResults,
        relevantDocuments,
        notificationsSent,
        workflowsTriggered,
      };

      this.updateMetrics(true, Date.now() - startTime);
      this.emitEvent({
        type: 'operation_complete',
        timestamp: new Date().toISOString(),
        operationId,
        data: { operation: 'search_and_trigger', success: true },
      });

      return { success: true, data: result, duration: Date.now() - startTime };
    } catch (error) {
      this.updateMetrics(false, Date.now() - startTime);
      this.emitEvent({
        type: 'operation_error',
        timestamp: new Date().toISOString(),
        operationId,
        error: error instanceof Error ? error.message : 'Unknown error',
      });

      return {
        success: false,
        error: error instanceof Error ? error.message : 'Search and trigger operation failed',
        duration: Date.now() - startTime,
      };
    }
  }

  /**
   * Set up collaborative workspace for a document
   */
  async setupCollaborativeWorkspace(
    documentId: string,
    participantEmails: string[],
    workflowTemplate?: string
  ): Promise<OperationResult<CollaborationSetupOperation>> {
    const operationId = this.generateOperationId('collaboration_setup');
    const startTime = Date.now();

    try {
      this.emitEvent({
        type: 'operation_start',
        timestamp: new Date().toISOString(),
        operationId,
        data: { operation: 'collaboration_setup', documentId },
      });

      // Step 1: Get document
      const documents = await this.clients.content.getDocuments(1, 0, { id: documentId });
      if (!documents.length) {
        throw new Error(`Document ${documentId} not found`);
      }
      const document = documents[0];

      // Step 2: Create conversation for collaboration
      const conversation = await this.clients.communication.createConversation({
        name: `Collaboration: ${document.title}`,
        participants: participantEmails, // Assuming these will be converted to user IDs
      });

      // Step 3: Send notifications to all participants
      const notifications = await Promise.all(
        participantEmails.map(email =>
          this.clients.communication.createNotification({
            type: 'info',
            title: 'Invited to Collaborate',
            message: `You've been invited to collaborate on "${document.title}"`,
            data: {
              document_id: documentId,
              conversation_id: conversation.id,
              invitation_type: 'collaboration',
            },
          })
        )
      );

      // Step 4: Set up workflow if template provided
      let workflow;
      if (workflowTemplate) {
        const workflows = await this.clients.workflow.getWorkflows();
        const template = workflows.find(w => w.id === workflowTemplate);
        if (template) {
          workflow = await this.clients.workflow.executeWorkflow(template.id, {
            input_data: {
              document_id: documentId,
              conversation_id: conversation.id,
              participants: participantEmails,
            },
            execution_mode: 'asynchronous',
          });
        }
      }

      const result: CollaborationSetupOperation = {
        document,
        conversation,
        participants: [], // Would need to fetch user details by email
        notifications,
        workflow,
      };

      this.updateMetrics(true, Date.now() - startTime);
      this.emitEvent({
        type: 'operation_complete',
        timestamp: new Date().toISOString(),
        operationId,
        data: { operation: 'collaboration_setup', success: true },
      });

      return { success: true, data: result, duration: Date.now() - startTime };
    } catch (error) {
      this.updateMetrics(false, Date.now() - startTime);
      this.emitEvent({
        type: 'operation_error',
        timestamp: new Date().toISOString(),
        operationId,
        error: error instanceof Error ? error.message : 'Unknown error',
      });

      return {
        success: false,
        error: error instanceof Error ? error.message : 'Collaboration setup failed',
        duration: Date.now() - startTime,
      };
    }
  }

  // ===========================================
  // HEALTH AND MONITORING
  // ===========================================

  /**
   * Perform comprehensive health check across all services
   */
  async performHealthCheck(): Promise<SystemHealthCheck> {
    const timestamp = new Date().toISOString();
    
    try {
      // Check each service health in parallel
      const [identityHealth, communicationHealth, contentHealth, workflowHealth] = await Promise.allSettled([
        this.checkServiceHealth('identity'),
        this.checkServiceHealth('communication'),
        this.checkServiceHealth('content'),
        this.checkServiceHealth('workflow'),
      ]);

      const healthResults = {
        identity: this.extractHealthResult(identityHealth),
        communication: this.extractHealthResult(communicationHealth),
        content: this.extractHealthResult(contentHealth),
        workflow: this.extractHealthResult(workflowHealth),
      };

      // Determine overall health
      const healthyServices = Object.values(healthResults).filter(
        result => result.status === 'healthy'
      ).length;
      
      let overall: 'healthy' | 'degraded' | 'unhealthy';
      if (healthyServices === 4) {
        overall = 'healthy';
      } else if (healthyServices >= 2) {
        overall = 'degraded';
      } else {
        overall = 'unhealthy';
      }

      // Update service availability metrics
      Object.entries(healthResults).forEach(([service, health]) => {
        this.metrics.serviceAvailability[service] = health.status === 'healthy' ? 100 : 0;
      });

      this.metrics.lastHealthCheck = timestamp;

      return {
        ...healthResults,
        overall,
        timestamp,
      };
    } catch (error) {
      return {
        identity: { status: 'unknown', service: 'identity', version: 'unknown' },
        communication: { status: 'unknown', service: 'communication', version: 'unknown' },
        content: { status: 'unknown', service: 'content', version: 'unknown' },
        workflow: { status: 'unknown', service: 'workflow', version: 'unknown' },
        overall: 'unhealthy',
        timestamp,
      };
    }
  }

  /**
   * Get current orchestrator metrics
   */
  getMetrics(): OrchestratorMetrics {
    return {
      ...this.metrics,
      uptime: Date.now() - this.metrics.uptime,
    };
  }

  // ===========================================
  // EVENT MANAGEMENT
  // ===========================================

  /**
   * Add event listener for orchestrator events
   */
  addEventListener(listener: (event: OrchestratorEvent) => void): void {
    this.eventListeners.push(listener);
  }

  /**
   * Remove event listener
   */
  removeEventListener(listener: (event: OrchestratorEvent) => void): void {
    const index = this.eventListeners.indexOf(listener);
    if (index > -1) {
      this.eventListeners.splice(index, 1);
    }
  }

  // ===========================================
  // UTILITY AND CONFIGURATION
  // ===========================================

  /**
   * Update orchestrator configuration
   */
  updateConfig(newConfig: Partial<OrchestratorConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Get current configuration
   */
  getConfig(): OrchestratorConfig {
    return { ...this.config };
  }
  
  /**
   * Multi-vertical support methods per Common Platform Patterns
   */
  setVerticalContext(vertical: 'medical' | 'public' | string): void {
    this.verticalContext = vertical;
    this.emitEvent({
      type: 'vertical_context_change',
      timestamp: new Date().toISOString(),
      data: { vertical }
    });
  }
  
  getVerticalContext(): string {
    return this.verticalContext;
  }
  
  setFeatureFlag(feature: string, enabled: boolean): void {
    this.featureFlags[feature] = enabled;
  }
  
  isFeatureEnabled(feature: string): boolean {
    return this.featureFlags[feature] ?? false;
  }

  /**
   * Cleanup and dispose resources
   */
  dispose(): void {
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
    }
    this.eventListeners.length = 0;
    this.operationQueue.clear();
  }

  // ===========================================
  // PRIVATE METHODS
  // ===========================================

  private generateOperationId(operation: string): string {
    return `${operation}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private emitEvent(event: OrchestratorEvent): void {
    if (this.config.enableLogging) {
      console.log('[ServiceOrchestrator]', event);
    }
    this.eventListeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error('Error in event listener:', error);
      }
    });
  }

  private updateMetrics(success: boolean, duration: number): void {
    if (!this.config.enableMetrics) return;

    this.metrics.totalOperations++;
    if (success) {
      this.metrics.successfulOperations++;
    } else {
      this.metrics.failedOperations++;
    }

    // Update average operation time
    const total = this.metrics.totalOperations;
    this.metrics.averageOperationTime = 
      (this.metrics.averageOperationTime * (total - 1) + duration) / total;
  }

  private async checkServiceHealth(service: string): Promise<{ status: string; service: string; version: string }> {
    // This would call the actual health check endpoints
    // For now, returning a mock healthy response
    return {
      status: 'healthy',
      service,
      version: '1.0.0',
    };
  }

  private extractHealthResult(
    settledResult: PromiseSettledResult<{ status: string; service: string; version: string }>
  ): { status: string; service: string; version: string } {
    if (settledResult.status === 'fulfilled') {
      return settledResult.value;
    } else {
      return {
        status: 'unhealthy',
        service: 'unknown',
        version: 'unknown',
      };
    }
  }

  private startHealthMonitoring(): void {
    this.healthCheckInterval = setInterval(async () => {
      const health = await this.performHealthCheck();
      this.emitEvent({
        type: 'service_health_change',
        timestamp: new Date().toISOString(),
        data: health,
      });
    }, this.healthConfig.checkInterval);
  }
}