/**
 * Kong Gateway Integration Test
 * Tests API client configuration for Kong Gateway integration
 */

import { apiClient, servicesClient } from './index';
import { ApiException } from './client';

export interface KongIntegrationTestResult {
  service: string;
  endpoint: string;
  status: 'success' | 'error' | 'not_tested';
  response?: any;
  error?: string;
  timestamp: string;
}

export class KongIntegrationTester {
  private results: KongIntegrationTestResult[] = [];

  async testAuthService(): Promise<KongIntegrationTestResult> {
    const result: KongIntegrationTestResult = {
      service: 'Identity Service',
      endpoint: '/api/v1/auth/health',
      status: 'not_tested',
      timestamp: new Date().toISOString(),
    };

    try {
      const response = await apiClient.healthCheck();
      result.status = 'success';
      result.response = response;
    } catch (error) {
      result.status = 'error';
      result.error = error instanceof ApiException ? error.message : 'Unknown error';
    }

    this.results.push(result);
    return result;
  }

  async testCommunicationService(): Promise<KongIntegrationTestResult> {
    const result: KongIntegrationTestResult = {
      service: 'Communication Service',
      endpoint: '/api/v1/notifications/health',
      status: 'not_tested',
      timestamp: new Date().toISOString(),
    };

    try {
      const response = await servicesClient.communication.healthCheck();
      result.status = 'success';
      result.response = response;
    } catch (error) {
      result.status = 'error';
      result.error = error instanceof ApiException ? error.message : 'Unknown error';
    }

    this.results.push(result);
    return result;
  }

  async testContentService(): Promise<KongIntegrationTestResult> {
    const result: KongIntegrationTestResult = {
      service: 'Content Service',
      endpoint: '/api/v1/documents/health',
      status: 'not_tested',
      timestamp: new Date().toISOString(),
    };

    try {
      const response = await servicesClient.content.healthCheck();
      result.status = 'success';
      result.response = response;
    } catch (error) {
      result.status = 'error';
      result.error = error instanceof ApiException ? error.message : 'Unknown error';
    }

    this.results.push(result);
    return result;
  }

  async testWorkflowService(): Promise<KongIntegrationTestResult> {
    const result: KongIntegrationTestResult = {
      service: 'Workflow Intelligence Service',
      endpoint: '/api/v1/workflows/health',
      status: 'not_tested',
      timestamp: new Date().toISOString(),
    };

    try {
      const response = await servicesClient.workflow.healthCheck();
      result.status = 'success';
      result.response = response;
    } catch (error) {
      result.status = 'error';
      result.error = error instanceof ApiException ? error.message : 'Unknown error';
    }

    this.results.push(result);
    return result;
  }

  async testAllServices(): Promise<KongIntegrationTestResult[]> {
    console.log('🧪 Starting Kong Gateway Integration Tests...');
    
    const authResult = await this.testAuthService();
    console.log(`✓ Auth Service: ${authResult.status}`, authResult.error ? `- ${authResult.error}` : '');
    
    const commResult = await this.testCommunicationService();
    console.log(`✓ Communication Service: ${commResult.status}`, commResult.error ? `- ${commResult.error}` : '');
    
    const contentResult = await this.testContentService();
    console.log(`✓ Content Service: ${contentResult.status}`, contentResult.error ? `- ${contentResult.error}` : '');
    
    const workflowResult = await this.testWorkflowService();
    console.log(`✓ Workflow Service: ${workflowResult.status}`, workflowResult.error ? `- ${workflowResult.error}` : '');

    this.generateReport();
    return this.results;
  }

  private generateReport(): void {
    const successful = this.results.filter(r => r.status === 'success').length;
    const failed = this.results.filter(r => r.status === 'error').length;
    const total = this.results.length;

    console.log('\n📊 Kong Integration Test Report:');
    console.log(`   Successful: ${successful}/${total}`);
    console.log(`   Failed: ${failed}/${total}`);
    
    if (failed > 0) {
      console.log('\n❌ Failed Tests:');
      this.results
        .filter(r => r.status === 'error')
        .forEach(r => {
          console.log(`   - ${r.service}: ${r.error}`);
        });
    }

    if (successful === total) {
      console.log('\n🎉 All services are accessible through Kong Gateway!');
    } else {
      console.log('\n⚠️  Some services are not accessible. Check Kong configuration.');
    }
  }

  getResults(): KongIntegrationTestResult[] {
    return [...this.results];
  }

  clearResults(): void {
    this.results = [];
  }
}

// Export a default tester instance
export const kongTester = new KongIntegrationTester();

// Utility function for quick testing
export async function quickKongTest(): Promise<void> {
  await kongTester.testAllServices();
}

// Test configuration validation
export function validateKongConfiguration(): void {
  const apiUrl = import.meta.env.VITE_API_URL;
  const authUrl = import.meta.env.VITE_AUTH_API_URL;
  const useKong = import.meta.env.VITE_USE_KONG_GATEWAY;

  console.log('🔧 Kong Configuration Validation:');
  console.log(`   VITE_API_URL: ${apiUrl}`);
  console.log(`   VITE_AUTH_API_URL: ${authUrl}`);
  console.log(`   VITE_USE_KONG_GATEWAY: ${useKong}`);

  if (!apiUrl) {
    console.warn('⚠️  VITE_API_URL is not set');
  }

  if (apiUrl !== 'http://localhost:8080') {
    console.warn('⚠️  VITE_API_URL is not pointing to Kong Gateway (expected: http://localhost:8080)');
  }

  if (!useKong || useKong !== 'true') {
    console.warn('⚠️  VITE_USE_KONG_GATEWAY is not enabled');
  }
}