/**
 * ServiceOrchestrator Tests
 * Basic tests to verify ServiceOrchestrator functionality
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ServiceOrchestrator } from './ServiceOrchestrator';
import type { ServiceClients, OrchestratorConfig } from './types';

// Mock service clients
const mockIdentityClient = {
  getCurrentUser: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  refreshToken: vi.fn(),
};

const mockCommunicationClient = {
  getNotifications: vi.fn(),
  createNotification: vi.fn(),
  sendMessage: vi.fn(),
  getConversations: vi.fn(),
};

const mockContentClient = {
  getDocuments: vi.fn(),
  searchDocuments: vi.fn(),
  uploadFile: vi.fn(),
  getDocumentVersions: vi.fn(),
};

const mockWorkflowClient = {
  getWorkflows: vi.fn(),
  executeWorkflow: vi.fn(),
  getAITasks: vi.fn(),
  executeAITask: vi.fn(),
};

describe('ServiceOrchestrator', () => {
  let orchestrator: ServiceOrchestrator;
  let config: OrchestratorConfig;

  beforeEach(() => {
    config = {
      retryAttempts: 1,
      retryDelay: 100,
      timeout: 5000,
      enableBatching: false,
      batchSize: 5,
      enableMetrics: true,
      enableLogging: false,
    };

    orchestrator = new ServiceOrchestrator(
      mockIdentityClient as any,
      mockCommunicationClient as any,
      mockContentClient as any,
      mockWorkflowClient as any,
      config
    );

    // Reset all mocks
    vi.clearAllMocks();
  });

  afterEach(() => {
    orchestrator.dispose();
  });

  describe('initialization', () => {
    it('should initialize with default configuration', () => {
      const newOrchestrator = new ServiceOrchestrator(
        mockIdentityClient as any,
        mockCommunicationClient as any,
        mockContentClient as any,
        mockWorkflowClient as any
      );

      const actualConfig = newOrchestrator.getConfig();
      expect(actualConfig.retryAttempts).toBe(3);
      expect(actualConfig.enableMetrics).toBe(true);
      
      newOrchestrator.dispose();
    });

    it('should initialize with custom configuration', () => {
      const customConfig = { retryAttempts: 5, enableMetrics: false };
      const newOrchestrator = new ServiceOrchestrator(
        mockIdentityClient as any,
        mockCommunicationClient as any,
        mockContentClient as any,
        mockWorkflowClient as any,
        customConfig
      );

      const actualConfig = newOrchestrator.getConfig();
      expect(actualConfig.retryAttempts).toBe(5);
      expect(actualConfig.enableMetrics).toBe(false);
      
      newOrchestrator.dispose();
    });
  });

  describe('health check', () => {
    it('should perform health check across all services', async () => {
      const healthResult = await orchestrator.performHealthCheck();

      expect(healthResult).toHaveProperty('identity');
      expect(healthResult).toHaveProperty('communication');
      expect(healthResult).toHaveProperty('content');
      expect(healthResult).toHaveProperty('workflow');
      expect(healthResult).toHaveProperty('overall');
      expect(healthResult).toHaveProperty('timestamp');
      
      expect(['healthy', 'degraded', 'unhealthy']).toContain(healthResult.overall);
    });
  });

  describe('metrics', () => {
    it('should track metrics correctly', () => {
      const initialMetrics = orchestrator.getMetrics();
      
      expect(initialMetrics).toHaveProperty('totalOperations');
      expect(initialMetrics).toHaveProperty('successfulOperations');
      expect(initialMetrics).toHaveProperty('failedOperations');
      expect(initialMetrics).toHaveProperty('averageOperationTime');
      expect(initialMetrics).toHaveProperty('serviceAvailability');
      expect(initialMetrics).toHaveProperty('uptime');
      
      expect(initialMetrics.totalOperations).toBe(0);
      expect(initialMetrics.successfulOperations).toBe(0);
      expect(initialMetrics.failedOperations).toBe(0);
    });
  });

  describe('event management', () => {
    it('should add and remove event listeners', () => {
      const listener = vi.fn();
      
      orchestrator.addEventListener(listener);
      orchestrator.removeEventListener(listener);
      
      // No easy way to test this without triggering an operation
      // but at least we verify the methods don't throw
      expect(true).toBe(true);
    });
  });

  describe('configuration management', () => {
    it('should update configuration', () => {
      const newConfig = { retryAttempts: 10, timeout: 15000 };
      
      orchestrator.updateConfig(newConfig);
      const updatedConfig = orchestrator.getConfig();
      
      expect(updatedConfig.retryAttempts).toBe(10);
      expect(updatedConfig.timeout).toBe(15000);
      // Should preserve other config values
      expect(updatedConfig.enableMetrics).toBe(true);
    });
  });

  describe('user onboarding operation', () => {
    it('should handle successful user onboarding', async () => {
      // Mock successful responses
      mockIdentityClient.login.mockResolvedValue({
        access_token: 'test-token',
        refresh_token: 'test-refresh',
        user: {
          id: 'user-1',
          first_name: 'John',
          last_name: 'Doe',
          email: 'john@example.com',
        },
      });

      mockCommunicationClient.createNotification.mockResolvedValue({
        id: 'notif-1',
        type: 'success',
        title: 'Welcome to ReactDjango Hub!',
        message: 'Hello John, welcome to your new workspace.',
      });

      mockContentClient.getDocuments.mockResolvedValue([
        { id: 'doc-1', title: 'Template 1', is_template: true },
      ]);

      mockWorkflowClient.getWorkflows.mockResolvedValue([
        { id: 'wf-1', name: 'Onboarding Workflow', status: 'template' },
      ]);

      const result = await orchestrator.onboardNewUser({
        email: 'john@example.com',
        password: 'password123',
        first_name: 'John',
        last_name: 'Doe',
      });

      expect(result.success).toBe(true);
      expect(result.data).toHaveProperty('user');
      expect(result.data).toHaveProperty('welcomeNotification');
      expect(result.data).toHaveProperty('defaultDocuments');
      expect(result.data).toHaveProperty('initialWorkflows');
      expect(result.duration).toBeGreaterThan(0);

      // Verify service calls
      expect(mockIdentityClient.login).toHaveBeenCalledWith({
        email: 'john@example.com',
        password: 'password123',
      });
      expect(mockCommunicationClient.createNotification).toHaveBeenCalled();
      expect(mockContentClient.getDocuments).toHaveBeenCalled();
      expect(mockWorkflowClient.getWorkflows).toHaveBeenCalled();
    });

    it('should handle failed user onboarding', async () => {
      // Mock failed login
      mockIdentityClient.login.mockRejectedValue(new Error('Invalid credentials'));

      const result = await orchestrator.onboardNewUser({
        email: 'john@example.com',
        password: 'wrong-password',
        first_name: 'John',
        last_name: 'Doe',
      });

      expect(result.success).toBe(false);
      expect(result.error).toContain('Invalid credentials');
      expect(result.duration).toBeGreaterThan(0);
    });
  });

  describe('search and trigger operation', () => {
    it('should handle successful search and trigger', async () => {
      // Mock successful responses
      mockContentClient.searchDocuments.mockResolvedValue({
        documents: [
          { id: 'doc-1', title: 'Document 1' },
          { id: 'doc-2', title: 'Document 2' },
        ],
        total: 2,
        page: 1,
        limit: 20,
        query: 'test search',
      });

      mockWorkflowClient.getWorkflows.mockResolvedValue([
        {
          id: 'wf-1',
          name: 'Search Workflow',
          status: 'active',
          trigger_type: 'event',
          trigger_config: { event_type: 'search_results' },
        },
      ]);

      mockWorkflowClient.executeWorkflow.mockResolvedValue({
        id: 'exec-1',
        workflow_id: 'wf-1',
        status: 'running',
      });

      mockCommunicationClient.createNotification.mockResolvedValue({
        id: 'notif-1',
        type: 'info',
        title: 'Search Results Available',
      });

      const result = await orchestrator.searchAndTriggerWorkflows(
        'test search',
        true,
        ['user-1']
      );

      expect(result.success).toBe(true);
      expect(result.data).toHaveProperty('searchResults');
      expect(result.data).toHaveProperty('relevantDocuments');
      expect(result.data).toHaveProperty('notificationsSent');
      expect(result.data).toHaveProperty('workflowsTriggered');

      // Verify service calls
      expect(mockContentClient.searchDocuments).toHaveBeenCalledWith({
        query: 'test search',
        limit: 20,
        sort_by: 'relevance',
        sort_order: 'desc',
      });
      expect(mockWorkflowClient.getWorkflows).toHaveBeenCalled();
      expect(mockWorkflowClient.executeWorkflow).toHaveBeenCalled();
      expect(mockCommunicationClient.createNotification).toHaveBeenCalled();
    });
  });
});