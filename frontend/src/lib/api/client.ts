/**
 * API Client for Identity Service
 * Handles all HTTP communication with the identity service at localhost:8001
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import type {
  RegisterRequest,
  RegisterResponse,
  LoginRequest,
  TokenResponse,
  VerifyEmailRequest,
  ResendVerificationRequest,
  MessageResponse,
  User,
  ApiResponse,
  ApiError,
  AuthApiClient,
  ApiClientConfig,
} from '@/types/auth';

// Default API configuration
const DEFAULT_CONFIG: ApiClientConfig = {
  baseURL: import.meta.env.VITE_AUTH_API_URL || 'http://localhost:8001',
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
};

// Custom error class for API errors
export class ApiException extends Error {
  public status: number;
  public details?: Record<string, any>;
  public endpoint?: string;

  constructor(
    message: string,
    status: number = 500,
    details?: Record<string, any>,
    endpoint?: string
  ) {
    super(message);
    this.name = 'ApiException';
    this.status = status;
    this.details = details;
    this.endpoint = endpoint;
  }
}

// Token storage interface
interface TokenStorage {
  getAccessToken(): string | null;
  getRefreshToken(): string | null;
  setTokens(accessToken: string, refreshToken: string): void;
  clearTokens(): void;
}

// Default token storage implementation using localStorage
class LocalStorageTokenStorage implements TokenStorage {
  private readonly ACCESS_TOKEN_KEY = 'auth_access_token';
  private readonly REFRESH_TOKEN_KEY = 'auth_refresh_token';

  getAccessToken(): string | null {
    try {
      return localStorage.getItem(this.ACCESS_TOKEN_KEY);
    } catch {
      return null;
    }
  }

  getRefreshToken(): string | null {
    try {
      return localStorage.getItem(this.REFRESH_TOKEN_KEY);
    } catch {
      return null;
    }
  }

  setTokens(accessToken: string, refreshToken: string): void {
    try {
      localStorage.setItem(this.ACCESS_TOKEN_KEY, accessToken);
      localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
    } catch (error) {
      console.warn('Failed to store tokens:', error);
    }
  }

  clearTokens(): void {
    try {
      localStorage.removeItem(this.ACCESS_TOKEN_KEY);
      localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    } catch (error) {
      console.warn('Failed to clear tokens:', error);
    }
  }
}

// API Client class
export class ApiClient implements AuthApiClient {
  private axiosInstance: AxiosInstance;
  private tokenStorage: TokenStorage;
  private isRefreshingToken = false;
  private refreshTokenPromise: Promise<TokenResponse> | null = null;

  constructor(
    config: Partial<ApiClientConfig> = {},
    tokenStorage?: TokenStorage
  ) {
    const finalConfig = { ...DEFAULT_CONFIG, ...config };
    
    this.axiosInstance = axios.create({
      baseURL: finalConfig.baseURL,
      timeout: finalConfig.timeout,
      headers: finalConfig.headers,
    });

    this.tokenStorage = tokenStorage || new LocalStorageTokenStorage();
    
    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor to add auth token
    this.axiosInstance.interceptors.request.use(
      (config) => {
        const token = this.tokenStorage.getAccessToken();
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling and token refresh
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

        // Handle 401 errors with token refresh
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            const refreshToken = this.tokenStorage.getRefreshToken();
            if (refreshToken && !this.isRefreshingToken) {
              const newTokens = await this.refreshAccessToken(refreshToken);
              this.tokenStorage.setTokens(newTokens.access_token, newTokens.refresh_token);
              
              // Retry original request with new token
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${newTokens.access_token}`;
              }
              return this.axiosInstance(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, clear tokens and redirect to login
            this.tokenStorage.clearTokens();
            this.handleAuthError(refreshError as AxiosError);
          }
        }

        return Promise.reject(this.handleApiError(error));
      }
    );
  }

  private handleApiError(error: AxiosError): ApiException {
    const response = error.response;
    const request = error.request;
    
    let message = 'An unexpected error occurred';
    let status = 500;
    let details: Record<string, any> = {};
    let endpoint = error.config?.url;

    if (response) {
      // Server responded with error status
      status = response.status;
      const responseData = response.data as any;
      
      if (responseData?.detail) {
        message = responseData.detail;
      } else if (responseData?.message) {
        message = responseData.message;
      } else if (typeof responseData === 'string') {
        message = responseData;
      }
      
      details = responseData || {};
      
      // Handle specific status codes
      switch (status) {
        case 400:
          message = message || 'Invalid request data';
          break;
        case 401:
          message = message || 'Authentication required';
          break;
        case 403:
          message = message || 'Access forbidden';
          break;
        case 404:
          message = message || 'Resource not found';
          break;
        case 422:
          message = message || 'Validation error';
          break;
        case 423:
          message = message || 'Account locked';
          break;
        case 429:
          message = message || 'Too many requests';
          break;
        case 500:
          message = message || 'Server error';
          break;
      }
    } else if (request) {
      // Network error
      message = 'Network error - please check your connection';
      status = 0;
    } else {
      // Request configuration error
      message = error.message || 'Request failed';
    }

    return new ApiException(message, status, details, endpoint);
  }

  private handleAuthError(error: AxiosError): void {
    // Emit auth error event for global handling
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('auth:error', { detail: error }));
    }
  }

  private async refreshAccessToken(refreshToken: string): Promise<TokenResponse> {
    if (this.refreshTokenPromise) {
      return this.refreshTokenPromise;
    }

    this.isRefreshingToken = true;
    this.refreshTokenPromise = this.makeRequest<TokenResponse>('POST', '/auth/refresh', {
      refresh_token: refreshToken,
    });

    try {
      const tokens = await this.refreshTokenPromise;
      return tokens;
    } finally {
      this.isRefreshingToken = false;
      this.refreshTokenPromise = null;
    }
  }

  private async makeRequest<T>(
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH',
    endpoint: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    try {
      let response: AxiosResponse<T>;

      switch (method) {
        case 'GET':
          response = await this.axiosInstance.get(endpoint, config);
          break;
        case 'POST':
          response = await this.axiosInstance.post(endpoint, data, config);
          break;
        case 'PUT':
          response = await this.axiosInstance.put(endpoint, data, config);
          break;
        case 'DELETE':
          response = await this.axiosInstance.delete(endpoint, config);
          break;
        case 'PATCH':
          response = await this.axiosInstance.patch(endpoint, data, config);
          break;
      }

      return response.data;
    } catch (error) {
      throw this.handleApiError(error as AxiosError);
    }
  }

  // Authentication endpoints
  async register(data: RegisterRequest): Promise<RegisterResponse> {
    return this.makeRequest<RegisterResponse>('POST', '/auth/register', data);
  }

  async login(data: LoginRequest): Promise<TokenResponse> {
    const response = await this.makeRequest<TokenResponse>('POST', '/auth/login', data);
    
    // Store tokens after successful login
    this.tokenStorage.setTokens(response.access_token, response.refresh_token);
    
    return response;
  }

  async verifyEmail(token: string): Promise<MessageResponse> {
    return this.makeRequest<MessageResponse>('POST', '/auth/verify-email', { token });
  }

  async resendVerification(email: string): Promise<MessageResponse> {
    return this.makeRequest<MessageResponse>('POST', '/auth/resend-verification', { email });
  }

  async forgotPassword(email: string): Promise<MessageResponse> {
    return this.makeRequest<MessageResponse>('POST', '/auth/forgot-password', { email });
  }

  async resetPassword(data: { token: string; password: string; password_confirm: string }): Promise<MessageResponse> {
    return this.makeRequest<MessageResponse>('POST', '/auth/reset-password', data);
  }

  async changePassword(data: { current_password: string; new_password: string; password_confirm: string }): Promise<MessageResponse> {
    return this.makeRequest<MessageResponse>('POST', '/auth/change-password', data);
  }

  // User endpoints
  async getCurrentUser(): Promise<User> {
    return this.makeRequest<User>('GET', '/auth/me');
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    return this.makeRequest<User>('PATCH', '/auth/profile', data);
  }

  async deleteAccount(): Promise<MessageResponse> {
    const response = await this.makeRequest<MessageResponse>('DELETE', '/auth/account');
    
    // Clear tokens after account deletion
    this.tokenStorage.clearTokens();
    
    return response;
  }

  // Token management
  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    return this.refreshAccessToken(refreshToken);
  }

  async revokeToken(token: string): Promise<MessageResponse> {
    const response = await this.makeRequest<MessageResponse>('POST', '/auth/revoke', { token });
    
    // Clear stored tokens
    this.tokenStorage.clearTokens();
    
    return response;
  }

  // Utility methods
  async logout(): Promise<void> {
    try {
      const refreshToken = this.tokenStorage.getRefreshToken();
      if (refreshToken) {
        await this.revokeToken(refreshToken);
      }
    } catch (error) {
      // Ignore errors during logout
      console.warn('Error during logout:', error);
    } finally {
      // Always clear tokens
      this.tokenStorage.clearTokens();
    }
  }

  // Health check
  async healthCheck(): Promise<{ status: string; service: string; version: string }> {
    return this.makeRequest<{ status: string; service: string; version: string }>('GET', '/health');
  }

  // Service info
  async getServiceInfo(): Promise<any> {
    return this.makeRequest<any>('GET', '/');
  }

  // Get current configuration
  getConfig(): ApiClientConfig {
    return {
      baseURL: this.axiosInstance.defaults.baseURL || DEFAULT_CONFIG.baseURL,
      timeout: this.axiosInstance.defaults.timeout || DEFAULT_CONFIG.timeout,
      headers: this.axiosInstance.defaults.headers as Record<string, string>,
    };
  }

  // Update configuration
  updateConfig(config: Partial<ApiClientConfig>): void {
    if (config.baseURL) {
      this.axiosInstance.defaults.baseURL = config.baseURL;
    }
    if (config.timeout) {
      this.axiosInstance.defaults.timeout = config.timeout;
    }
    if (config.headers) {
      this.axiosInstance.defaults.headers = { ...this.axiosInstance.defaults.headers, ...config.headers };
    }
  }
}

// Default API client instance
export const apiClient = new ApiClient();

// Utility functions for error handling
export function isApiException(error: any): error is ApiException {
  return error instanceof ApiException;
}

export function getErrorMessage(error: any): string {
  if (isApiException(error)) {
    return error.message;
  }
  if (error?.message) {
    return error.message;
  }
  return 'An unexpected error occurred';
}

export function getErrorDetails(error: any): Record<string, any> {
  if (isApiException(error)) {
    return error.details || {};
  }
  return {};
}

// HTTP status code utilities
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  UNPROCESSABLE_ENTITY: 422,
  LOCKED: 423,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
} as const;

// Export types and utilities
export type { ApiException as ApiError };
export { LocalStorageTokenStorage };
export type { TokenStorage };