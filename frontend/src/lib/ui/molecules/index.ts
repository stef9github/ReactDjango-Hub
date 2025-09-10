/**
 * Molecules - Authentication UI Components Barrel Export
 * Compound components built from atoms for specific authentication flows
 */

// Authentication forms
export { LoginForm } from './LoginForm';
export { RegisterForm } from './RegisterForm';
export { ForgotPasswordForm } from './ForgotPasswordForm';
export { EmailVerificationForm } from './EmailVerificationForm';

// Re-export form prop types
export type {
  LoginFormProps,
  RegisterFormProps,
  ForgotPasswordFormProps,
  VerifyEmailFormProps,
} from '@/types/auth';