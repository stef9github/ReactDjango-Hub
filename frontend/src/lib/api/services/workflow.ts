/**
 * Workflow Intelligence Service API Client
 * Handles workflow automation, process management, and AI integrations through Kong Gateway
 */

import { BaseServiceClient, BaseServiceConfig, TokenStorage } from './base';

// Workflow Service Types
export interface Workflow {
  id: string;
  name: string;
  description?: string;
  status: 'draft' | 'active' | 'paused' | 'archived';
  trigger_type: 'manual' | 'scheduled' | 'event' | 'webhook';
  trigger_config: Record<string, any>;
  steps: WorkflowStep[];
  metadata: Record<string, any>;
  owner_id: string;
  organization_id: string;
  created_at: string;
  updated_at: string;
  last_run_at?: string;
  next_run_at?: string;
}

export interface WorkflowStep {
  id: string;
  workflow_id: string;
  name: string;
  type: 'action' | 'condition' | 'loop' | 'parallel' | 'ai_task';
  order: number;
  config: Record<string, any>;
  depends_on?: string[];
  created_at: string;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  status: 'running' | 'completed' | 'failed' | 'cancelled';
  started_at: string;
  completed_at?: string;
  error_message?: string;
  input_data: Record<string, any>;
  output_data?: Record<string, any>;
  steps_executed: WorkflowStepExecution[];
}

export interface WorkflowStepExecution {
  id: string;
  step_id: string;
  execution_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  started_at?: string;
  completed_at?: string;
  input_data: Record<string, any>;
  output_data?: Record<string, any>;
  error_message?: string;
  logs: string[];
}

export interface AITask {
  id: string;
  name: string;
  description?: string;
  task_type: 'text_generation' | 'classification' | 'extraction' | 'analysis' | 'translation';
  model_config: Record<string, any>;
  input_schema: Record<string, any>;
  output_schema: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface AITaskExecution {
  id: string;
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  input_data: Record<string, any>;
  output_data?: Record<string, any>;
  error_message?: string;
  execution_time_ms?: number;
  created_at: string;
  completed_at?: string;
}

export interface CreateWorkflowRequest {
  name: string;
  description?: string;
  trigger_type: 'manual' | 'scheduled' | 'event' | 'webhook';
  trigger_config: Record<string, any>;
  steps: Omit<WorkflowStep, 'id' | 'workflow_id' | 'created_at'>[];
  metadata?: Record<string, any>;
}

export interface UpdateWorkflowRequest {
  name?: string;
  description?: string;
  status?: 'draft' | 'active' | 'paused' | 'archived';
  trigger_config?: Record<string, any>;
  steps?: Omit<WorkflowStep, 'id' | 'workflow_id' | 'created_at'>[];
  metadata?: Record<string, any>;
}

export interface ExecuteWorkflowRequest {
  input_data: Record<string, any>;
  execution_mode?: 'synchronous' | 'asynchronous';
}

export interface CreateAITaskRequest {
  name: string;
  description?: string;
  task_type: 'text_generation' | 'classification' | 'extraction' | 'analysis' | 'translation';
  model_config: Record<string, any>;
  input_schema: Record<string, any>;
  output_schema: Record<string, any>;
}

// Workflow Service Client
export class WorkflowServiceClient extends BaseServiceClient {
  constructor(
    config?: Partial<BaseServiceConfig>,
    tokenStorage?: TokenStorage
  ) {
    const defaultConfig: BaseServiceConfig = {
      baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8080',
      timeout: 60000, // Longer timeout for AI/workflow operations
      headers: {
        'Content-Type': 'application/json',
      },
    };

    super({ ...defaultConfig, ...config }, tokenStorage);
  }

  // Workflow endpoints
  async getWorkflows(limit?: number, offset?: number, status?: string): Promise<Workflow[]> {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    if (status) params.append('status', status);
    
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.makeRequest<Workflow[]>('GET', `/api/v1/workflows${query}`);
  }

  async getWorkflowById(id: string): Promise<Workflow> {
    return this.makeRequest<Workflow>('GET', `/api/v1/workflows/${id}`);
  }

  async createWorkflow(data: CreateWorkflowRequest): Promise<Workflow> {
    return this.makeRequest<Workflow>('POST', '/api/v1/workflows', data);
  }

  async updateWorkflow(id: string, data: UpdateWorkflowRequest): Promise<Workflow> {
    return this.makeRequest<Workflow>('PATCH', `/api/v1/workflows/${id}`, data);
  }

  async deleteWorkflow(id: string): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('DELETE', `/api/v1/workflows/${id}`);
  }

  async duplicateWorkflow(id: string, newName: string): Promise<Workflow> {
    return this.makeRequest<Workflow>('POST', `/api/v1/workflows/${id}/duplicate`, { name: newName });
  }

  // Workflow execution endpoints
  async executeWorkflow(id: string, data: ExecuteWorkflowRequest): Promise<WorkflowExecution> {
    return this.makeRequest<WorkflowExecution>('POST', `/api/v1/workflows/${id}/execute`, data);
  }

  async getWorkflowExecutions(workflowId: string, limit?: number, offset?: number): Promise<WorkflowExecution[]> {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.makeRequest<WorkflowExecution[]>('GET', `/api/v1/workflows/${workflowId}/executions${query}`);
  }

  async getWorkflowExecution(executionId: string): Promise<WorkflowExecution> {
    return this.makeRequest<WorkflowExecution>('GET', `/api/v1/workflows/executions/${executionId}`);
  }

  async cancelWorkflowExecution(executionId: string): Promise<WorkflowExecution> {
    return this.makeRequest<WorkflowExecution>('POST', `/api/v1/workflows/executions/${executionId}/cancel`);
  }

  async retryWorkflowExecution(executionId: string): Promise<WorkflowExecution> {
    return this.makeRequest<WorkflowExecution>('POST', `/api/v1/workflows/executions/${executionId}/retry`);
  }

  async getWorkflowExecutionLogs(executionId: string): Promise<{ logs: string[] }> {
    return this.makeRequest<{ logs: string[] }>('GET', `/api/v1/workflows/executions/${executionId}/logs`);
  }

  // Workflow step endpoints
  async getWorkflowStep(stepId: string): Promise<WorkflowStep> {
    return this.makeRequest<WorkflowStep>('GET', `/api/v1/workflows/steps/${stepId}`);
  }

  async updateWorkflowStep(stepId: string, data: Partial<WorkflowStep>): Promise<WorkflowStep> {
    return this.makeRequest<WorkflowStep>('PATCH', `/api/v1/workflows/steps/${stepId}`, data);
  }

  async testWorkflowStep(stepId: string, inputData: Record<string, any>): Promise<{ output: Record<string, any> }> {
    return this.makeRequest<{ output: Record<string, any> }>('POST', `/api/v1/workflows/steps/${stepId}/test`, {
      input_data: inputData,
    });
  }

  // AI Task endpoints
  async getAITasks(limit?: number, offset?: number, taskType?: string): Promise<AITask[]> {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    if (taskType) params.append('task_type', taskType);
    
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.makeRequest<AITask[]>('GET', `/api/v1/ai/tasks${query}`);
  }

  async getAITaskById(id: string): Promise<AITask> {
    return this.makeRequest<AITask>('GET', `/api/v1/ai/tasks/${id}`);
  }

  async createAITask(data: CreateAITaskRequest): Promise<AITask> {
    return this.makeRequest<AITask>('POST', '/api/v1/ai/tasks', data);
  }

  async updateAITask(id: string, data: Partial<CreateAITaskRequest>): Promise<AITask> {
    return this.makeRequest<AITask>('PATCH', `/api/v1/ai/tasks/${id}`, data);
  }

  async deleteAITask(id: string): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>('DELETE', `/api/v1/ai/tasks/${id}`);
  }

  // AI Task execution endpoints
  async executeAITask(taskId: string, inputData: Record<string, any>): Promise<AITaskExecution> {
    return this.makeRequest<AITaskExecution>('POST', `/api/v1/ai/tasks/${taskId}/execute`, {
      input_data: inputData,
    });
  }

  async getAITaskExecutions(taskId: string, limit?: number, offset?: number): Promise<AITaskExecution[]> {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    if (offset) params.append('offset', offset.toString());
    
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.makeRequest<AITaskExecution[]>('GET', `/api/v1/ai/tasks/${taskId}/executions${query}`);
  }

  async getAITaskExecution(executionId: string): Promise<AITaskExecution> {
    return this.makeRequest<AITaskExecution>('GET', `/api/v1/ai/executions/${executionId}`);
  }

  // AI Models and capabilities
  async getAvailableModels(): Promise<any[]> {
    return this.makeRequest<any[]>('GET', '/api/v1/ai/models');
  }

  async getModelCapabilities(modelName: string): Promise<any> {
    return this.makeRequest<any>('GET', `/api/v1/ai/models/${modelName}/capabilities`);
  }

  // Workflow templates
  async getWorkflowTemplates(): Promise<any[]> {
    return this.makeRequest<any[]>('GET', '/api/v1/workflows/templates');
  }

  async createWorkflowFromTemplate(templateId: string, name: string, config?: Record<string, any>): Promise<Workflow> {
    return this.makeRequest<Workflow>('POST', `/api/v1/workflows/templates/${templateId}/create`, {
      name,
      config: config || {},
    });
  }

  // Analytics and monitoring
  async getWorkflowAnalytics(workflowId: string, period?: string): Promise<any> {
    const params = new URLSearchParams();
    if (period) params.append('period', period);
    
    const query = params.toString() ? `?${params.toString()}` : '';
    return this.makeRequest<any>('GET', `/api/v1/workflows/${workflowId}/analytics${query}`);
  }

  async getSystemMetrics(): Promise<any> {
    return this.makeRequest<any>('GET', '/api/v1/workflows/metrics');
  }
}

// Default client instance
export const workflowClient = new WorkflowServiceClient();