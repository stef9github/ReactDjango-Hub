/**
 * Authentication Types for ReactDjango Hub
 * Comprehensive type definitions for all auth flows and API responses
 */

// Base API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  details?: Record<string, any>;
}

export interface ApiError {
  message: string;
  status?: number;
  details?: Record<string, any>;
}

// User Related Types
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
  bio?: string;
  avatar_url?: string;
  timezone: string;
  language: string;
  is_verified: boolean;
  status: 'active' | 'inactive' | 'suspended' | 'pending';
  last_login_at?: string;
  created_at: string;
  updated_at: string;
}

export interface UserProfile extends User {
  display_name?: string;
  full_name: string;
}

// Authentication Request Types
export interface RegisterRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  phone_number?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface VerifyEmailRequest {
  token: string;
}

export interface ResendVerificationRequest {
  email: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  password: string;
  password_confirm: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
  password_confirm: string;
}

// Authentication Response Types
export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_id: string;
  user: User;
}

export interface RegisterResponse {
  message: string;
  user_id: string;
  email: string;
  verification_required: boolean;
  verification_token?: string; // Only for testing
  next_step: string;
}

export interface MessageResponse {
  message: string;
  details?: Record<string, any>;
}

// Authentication State Types
export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  token: string | null;
  refreshToken: string | null;
  isInitialized: boolean;
}

// Form State Types
export interface FormError {
  field?: string;
  message: string;
}

export interface FormState<T> {
  data: T;
  errors: FormError[];
  isSubmitting: boolean;
  isValid: boolean;
  touched: Record<keyof T, boolean>;
}

// Validation Types
export interface ValidationResult {
  isValid: boolean;
  errors: FormError[];
}

export interface PasswordStrength {
  score: 0 | 1 | 2 | 3 | 4; // Very weak to very strong
  feedback: string[];
  hasMinLength: boolean;
  hasUppercase: boolean;
  hasLowercase: boolean;
  hasNumbers: boolean;
  hasSpecialChars: boolean;
}

// Authentication Context Types
export interface AuthContextType {
  // State
  ...AuthState;
  
  // Actions
  login: (credentials: LoginRequest) => Promise<TokenResponse>;
  register: (userData: RegisterRequest) => Promise<RegisterResponse>;
  logout: () => Promise<void>;
  verifyEmail: (token: string) => Promise<MessageResponse>;
  resendVerification: (email: string) => Promise<MessageResponse>;
  forgotPassword: (email: string) => Promise<MessageResponse>;
  resetPassword: (data: ResetPasswordRequest) => Promise<MessageResponse>;
  changePassword: (data: ChangePasswordRequest) => Promise<MessageResponse>;
  refreshTokens: () => Promise<TokenResponse>;
  getCurrentUser: () => Promise<User>;
  updateProfile: (data: Partial<User>) => Promise<User>;
  
  // Utilities
  clearError: () => void;
  checkPasswordStrength: (password: string) => PasswordStrength;
}

// Component Prop Types
export interface AuthFormProps {
  onSubmit: (data: any) => Promise<void>;
  onError?: (error: ApiError) => void;
  onSuccess?: (data: any) => void;
  isLoading?: boolean;
  className?: string;
}

export interface LoginFormProps extends AuthFormProps {
  onSubmit: (data: LoginRequest) => Promise<void>;
  showRememberMe?: boolean;
  showForgotPassword?: boolean;
  onForgotPassword?: () => void;
  onRegister?: () => void;
}

export interface RegisterFormProps extends AuthFormProps {
  onSubmit: (data: RegisterRequest) => Promise<void>;
  onLogin?: () => void;
  showPasswordStrength?: boolean;
  requirePhoneNumber?: boolean;
}

export interface VerifyEmailFormProps extends AuthFormProps {
  onSubmit: (data: VerifyEmailRequest) => Promise<void>;
  onResendVerification?: (email: string) => Promise<void>;
  email?: string;
}

export interface ForgotPasswordFormProps extends AuthFormProps {
  onSubmit: (data: ForgotPasswordRequest) => Promise<void>;
  onBackToLogin?: () => void;
}

export interface ResetPasswordFormProps extends AuthFormProps {
  onSubmit: (data: ResetPasswordRequest) => Promise<void>;
  token: string;
  showPasswordStrength?: boolean;
}

// Hook Types
export interface UseAuthReturn extends AuthContextType {}

export interface UseFormReturn<T> {
  data: T;
  setData: (data: Partial<T>) => void;
  errors: FormError[];
  setErrors: (errors: FormError[]) => void;
  isSubmitting: boolean;
  setIsSubmitting: (loading: boolean) => void;
  touched: Record<keyof T, boolean>;
  setTouched: (field: keyof T, touched?: boolean) => void;
  isValid: boolean;
  handleSubmit: (onSubmit: (data: T) => Promise<void>) => (e: React.FormEvent) => Promise<void>;
  handleChange: (field: keyof T) => (value: any) => void;
  handleBlur: (field: keyof T) => () => void;
  resetForm: (newData?: Partial<T>) => void;
  validateField: (field: keyof T, value: any) => ValidationResult;
  validateForm: () => ValidationResult;
}

// API Client Types
export interface ApiClientConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
}

export interface AuthApiClient {
  // Authentication endpoints
  register: (data: RegisterRequest) => Promise<RegisterResponse>;
  login: (data: LoginRequest) => Promise<TokenResponse>;
  verifyEmail: (token: string) => Promise<MessageResponse>;
  resendVerification: (email: string) => Promise<MessageResponse>;
  forgotPassword: (email: string) => Promise<MessageResponse>;
  resetPassword: (data: ResetPasswordRequest) => Promise<MessageResponse>;
  changePassword: (data: ChangePasswordRequest) => Promise<MessageResponse>;
  
  // User endpoints
  getCurrentUser: () => Promise<User>;
  updateProfile: (data: Partial<User>) => Promise<User>;
  deleteAccount: () => Promise<MessageResponse>;
  
  // Token management
  refreshToken: (refreshToken: string) => Promise<TokenResponse>;
  revokeToken: (token: string) => Promise<MessageResponse>;
}

// Storage Types
export interface AuthStorage {
  getToken: () => string | null;
  setToken: (token: string) => void;
  removeToken: () => void;
  getRefreshToken: () => string | null;
  setRefreshToken: (token: string) => void;
  removeRefreshToken: () => void;
  getUser: () => User | null;
  setUser: (user: User) => void;
  removeUser: () => void;
  clear: () => void;
}

// Security Types
export interface DeviceInfo {
  ip_address?: string;
  user_agent?: string;
  device_type: 'web' | 'mobile' | 'desktop';
  device_id?: string;
}

export interface SecurityEvent {
  type: 'login' | 'logout' | 'password_change' | 'email_verify' | 'failed_login';
  timestamp: string;
  device_info?: DeviceInfo;
  ip_address?: string;
  success: boolean;
  details?: Record<string, any>;
}

// Multi-factor Authentication Types (for future extension)
export interface MfaSetupRequest {
  method: 'totp' | 'sms' | 'email';
  phone_number?: string;
}

export interface MfaVerifyRequest {
  method: 'totp' | 'sms' | 'email';
  code: string;
  backup_code?: string;
}

export interface MfaResponse {
  enabled: boolean;
  methods: ('totp' | 'sms' | 'email')[];
  backup_codes?: string[];
  qr_code?: string; // For TOTP setup
}

// Organization Types (for multi-tenant features)
export interface Organization {
  id: string;
  name: string;
  slug: string;
  description?: string;
  avatar_url?: string;
  plan: string;
  status: 'active' | 'inactive' | 'suspended';
  created_at: string;
  updated_at: string;
}

export interface UserOrganizationRole {
  organization_id: string;
  user_id: string;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  permissions: string[];
  joined_at: string;
}

// Export all types for easy importing
export type {
  // Re-export commonly used types for convenience
  User as AuthUser,
  AuthState as AuthenticationState,
  LoginRequest as LoginCredentials,
  RegisterRequest as RegistrationData,
  TokenResponse as AuthTokens
};