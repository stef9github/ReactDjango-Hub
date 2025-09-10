/**
 * ForgotPasswordForm Component - Authentication Molecule
 * Password reset request form with validation
 */

import React, { forwardRef, useState } from 'react';
import { 
  Button, 
  Input, 
  Alert, 
  cn 
} from '@/lib/ui/atoms';
import { useForgotPassword } from '@/lib/auth';
import type { ForgotPasswordFormProps } from '@/types/auth';

export const ForgotPasswordForm = forwardRef<HTMLFormElement, ForgotPasswordFormProps>(
  (
    {
      onSubmit,
      onError,
      onSuccess,
      onBackToLogin,
      isLoading: externalLoading = false,
      className,
      ...props
    },
    ref
  ) => {
    const {
      data,
      errors,
      isSubmitting,
      handleChange,
      handleBlur,
      handleForgotPassword,
    } = useForgotPassword();

    const [isSubmitted, setIsSubmitted] = useState(false);
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
          const result = await handleForgotPassword(e);
          onSuccess?.(result);
        }
        setIsSubmitted(true);
      } catch (error: any) {
        onError?.(error);
      }
    };

    // Show success state after submission
    if (isSubmitted) {
      return (
        <div className={cn('space-y-6 text-center', className)}>
          <div className="mx-auto w-12 h-12 bg-[var(--colors-semantic-success-100)] rounded-full flex items-center justify-center">
            <svg className="w-6 h-6 text-[var(--colors-semantic-success-500)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-[var(--colors-text-on-surface)]">
              Check your email
            </h3>
            <p className="text-[var(--colors-text-on-surface-variant)]">
              We've sent password reset instructions to{' '}
              <span className="font-medium text-[var(--colors-text-on-surface)]">
                {data.email}
              </span>
            </p>
          </div>

          <Alert
            variant="info"
            description="If you don't see the email in your inbox, check your spam folder."
          />

          <div className="space-y-3">
            <Button
              type="button"
              variant="outline"
              size="lg"
              fullWidth
              onClick={() => setIsSubmitted(false)}
            >
              Try different email
            </Button>

            {onBackToLogin && (
              <Button
                type="button"
                variant="ghost"
                size="md"
                fullWidth
                onClick={onBackToLogin}
              >
                Back to sign in
              </Button>
            )}
          </div>
        </div>
      );
    }

    return (
      <form
        ref={ref}
        onSubmit={handleFormSubmit}
        className={cn('space-y-6', className)}
        noValidate
        {...props}
      >
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="mx-auto w-12 h-12 bg-[var(--colors-semantic-primary-100)] rounded-full flex items-center justify-center">
            <svg className="w-6 h-6 text-[var(--colors-semantic-primary-500)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" 
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          
          <h2 className="text-xl font-semibold text-[var(--colors-text-on-surface)]">
            Reset your password
          </h2>
          
          <p className="text-[var(--colors-text-on-surface-variant)]">
            Enter your email address and we'll send you a link to reset your password.
          </p>
        </div>

        {/* General Errors */}
        {generalErrors.length > 0 && (
          <Alert 
            variant="error" 
            title="Request Failed"
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
          autoFocus
          leftIcon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" 
                d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
            </svg>
          }
        />

        {/* Submit Button */}
        <Button
          type="submit"
          variant="primary"
          size="lg"
          fullWidth
          loading={loading}
          loadingText="Sending reset link..."
          disabled={loading}
        >
          Send reset link
        </Button>

        {/* Back to Login */}
        {onBackToLogin && (
          <div className="text-center">
            <button
              type="button"
              onClick={onBackToLogin}
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
              ← Back to sign in
            </button>
          </div>
        )}
      </form>
    );
  }
);

ForgotPasswordForm.displayName = 'ForgotPasswordForm';