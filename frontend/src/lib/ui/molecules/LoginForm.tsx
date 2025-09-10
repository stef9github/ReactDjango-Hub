/**
 * LoginForm Component - Authentication Molecule
 * Complete login form with validation and error handling
 */

import React, { forwardRef } from 'react';
import { 
  Button, 
  Input, 
  Alert, 
  cn 
} from '@/lib/ui/atoms';
import { useLoginForm } from '@/lib/auth';
import type { LoginFormProps } from '@/types/auth';

// Eye icon for password visibility
const EyeIcon = ({ className }: { className?: string }) => (
  <svg className={className} fill="none" height="20" viewBox="0 0 24 24" width="20">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

export const LoginForm = forwardRef<HTMLFormElement, LoginFormProps>(
  (
    {
      onSubmit,
      onError,
      onSuccess,
      isLoading: externalLoading = false,
      showRememberMe = true,
      showForgotPassword = true,
      onForgotPassword,
      onRegister,
      className,
      ...props
    },
    ref
  ) => {
    const {
      data,
      errors,
      isSubmitting,
      touched,
      handleChange,
      handleBlur,
      handleLogin,
    } = useLoginForm();

    const loading = externalLoading || isSubmitting;
    
    // Get field-specific errors
    const getFieldError = (field: string) => {
      const error = errors.find(e => e.field === field);
      return error?.message;
    };

    // Get general (non-field) errors
    const generalErrors = errors.filter(e => !e.field);

    const handleFormSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      
      try {
        if (onSubmit) {
          await onSubmit(data);
        } else {
          const result = await handleLogin(e);
          onSuccess?.(result);
        }
      } catch (error: any) {
        onError?.(error);
      }
    };

    return (
      <form
        ref={ref}
        onSubmit={handleFormSubmit}
        className={cn('space-y-6', className)}
        noValidate
        {...props}
      >
        {/* General Errors */}
        {generalErrors.length > 0 && (
          <Alert 
            variant="error" 
            title="Login Failed"
            description={generalErrors[0].message}
          />
        )}

        {/* Email Field */}
        <Input
          type="email"
          label="Email address"
          placeholder="Enter your email"
          value={data.email}
          onChange={(e) => handleChange('email')(e.target.value)}
          onBlur={handleBlur('email')}
          errorText={getFieldError('email')}
          disabled={loading}
          isRequired
          autoComplete="email"
          leftIcon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" 
                d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
            </svg>
          }
        />

        {/* Password Field */}
        <Input
          type="password"
          label="Password"
          placeholder="Enter your password"
          value={data.password}
          onChange={(e) => handleChange('password')(e.target.value)}
          onBlur={handleBlur('password')}
          errorText={getFieldError('password')}
          disabled={loading}
          isRequired
          autoComplete="current-password"
          showPasswordToggle
          leftIcon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" 
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          }
        />

        {/* Remember Me & Forgot Password */}
        <div className="flex items-center justify-between">
          {showRememberMe && (
            <label className="flex items-center">
              <input
                type="checkbox"
                className="w-4 h-4 text-[var(--colors-semantic-primary-500)] 
                         border-[var(--colors-border-default)] rounded 
                         focus:ring-[var(--colors-semantic-primary-500)] focus:ring-2"
                disabled={loading}
              />
              <span className="ml-2 text-sm text-[var(--colors-text-on-surface-variant)]">
                Remember me
              </span>
            </label>
          )}

          {showForgotPassword && (
            <button
              type="button"
              onClick={onForgotPassword}
              disabled={loading}
              className={cn(
                'text-sm font-medium',
                'text-[var(--colors-semantic-primary-500)]',
                'hover:text-[var(--colors-semantic-primary-600)]',
                'focus:outline-none focus:underline',
                'transition-colors duration-200',
                loading && 'opacity-50 cursor-not-allowed'
              )}
            >
              Forgot password?
            </button>
          )}
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          variant="primary"
          size="lg"
          fullWidth
          loading={loading}
          loadingText="Signing in..."
          disabled={loading}
        >
          Sign in
        </Button>

        {/* Register Link */}
        {onRegister && (
          <div className="text-center">
            <span className="text-sm text-[var(--colors-text-on-surface-variant)]">
              Don't have an account?{' '}
              <button
                type="button"
                onClick={onRegister}
                disabled={loading}
                className={cn(
                  'font-medium',
                  'text-[var(--colors-semantic-primary-500)]',
                  'hover:text-[var(--colors-semantic-primary-600)]',
                  'focus:outline-none focus:underline',
                  'transition-colors duration-200',
                  loading && 'opacity-50 cursor-not-allowed'
                )}
              >
                Sign up
              </button>
            </span>
          </div>
        )}
      </form>
    );
  }
);

LoginForm.displayName = 'LoginForm';