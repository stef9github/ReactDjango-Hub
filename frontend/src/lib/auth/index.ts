/**
 * Auth Module Barrel Export
 * Centralized exports for authentication system
 */

// Context and provider
export {
  AuthProvider,
  useAuth,
  useRequireAuth,
  useGuestOnly,
} from './auth-context';

export type {
  AuthProviderProps,
} from './auth-context';

// Hooks
export {
  useForm,
  useLoginForm,
  useRegisterForm,
  useEmailVerification,
  useForgotPassword,
  useResetPassword,
  useChangePassword,
  usePasswordStrength,
  useAutoLogout,
  useLocalStorageSync,
} from './hooks';

// Re-export types for convenience
export type {
  AuthState,
  AuthContextType,
  UseFormReturn,
  FormError,
  ValidationResult,
  PasswordStrength,
} from '@/types/auth';