/**
 * API Module Barrel Export
 * Centralized exports for API client and utilities
 */

// Main API client
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