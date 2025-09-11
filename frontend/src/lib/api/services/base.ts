/**
 * Base Service Client
 * Provides common functionality for all microservice API clients
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { ApiException } from '../client';

export interface BaseServiceConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
}

export interface TokenStorage {
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

export abstract class BaseServiceClient {
  protected axiosInstance: AxiosInstance;
  protected tokenStorage: TokenStorage;

  constructor(
    config: BaseServiceConfig,
    tokenStorage?: TokenStorage
  ) {
    this.axiosInstance = axios.create({
      baseURL: config.baseURL,
      timeout: config.timeout || 10000,
      headers: config.headers || {
        'Content-Type': 'application/json',
        'X-Kong-Request-ID': '', // Kong request tracing
      },
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

    // Response interceptor for error handling
    this.axiosInstance.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
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

  protected async makeRequest<T>(
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

  // Health check (via Kong Gateway)
  async healthCheck(): Promise<{ status: string; service: string; version: string }> {
    return this.makeRequest<{ status: string; service: string; version: string }>('GET', '/health');
  }
}