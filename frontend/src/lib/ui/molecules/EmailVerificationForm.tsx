/**
 * EmailVerificationForm Component - Authentication Molecule
 * Email verification form with resend functionality
 */

import React, { forwardRef, useState, useEffect } from 'react';
import { 
  Button, 
  Input, 
  Alert, 
  cn 
} from '@/lib/ui/atoms';
import { useEmailVerification } from '@/lib/auth';
import type { VerifyEmailFormProps } from '@/types/auth';

export const EmailVerificationForm = forwardRef<HTMLFormElement, VerifyEmailFormProps>(
  (
    {
      onSubmit,
      onError,
      onSuccess,
      onResendVerification,
      email,
      isLoading: externalLoading = false,
      className,
      ...props
    },
    ref
  ) => {
    const { verifyEmail, resendVerification, isResending } = useEmailVerification();
    const [token, setToken] = useState('');
    const [errors, setErrors] = useState<string[]>([]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [resendCooldown, setResendCooldown] = useState(0);

    const loading = externalLoading || isSubmitting;

    // Resend cooldown timer
    useEffect(() => {
      let interval: NodeJS.Timeout;
      if (resendCooldown > 0) {
        interval = setInterval(() => {
          setResendCooldown(prev => prev - 1);
        }, 1000);
      }
      return () => clearInterval(interval);
    }, [resendCooldown]);

    const handleFormSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      setErrors([]);
      
      if (!token.trim()) {
        setErrors(['Verification token is required']);
        return;
      }

      setIsSubmitting(true);
      
      try {
        if (onSubmit) {
          await onSubmit({ token });
        } else {
          const result = await verifyEmail(token);
          onSuccess?.(result);
        }
      } catch (error: any) {
        const errorMessage = error.message || 'Verification failed';
        setErrors([errorMessage]);
        onError?.(error);
      } finally {
        setIsSubmitting(false);
      }
    };

    const handleResendVerification = async () => {
      if (!email) {
        setErrors(['Email address is required to resend verification']);
        return;
      }

      setErrors([]);
      
      try {
        if (onResendVerification) {
          await onResendVerification(email);
        } else {
          await resendVerification(email);
        }
        
        // Start cooldown timer (60 seconds)
        setResendCooldown(60);
        
        // Show success message
        setErrors([]);
      } catch (error: any) {
        const errorMessage = error.message || 'Failed to resend verification email';
        setErrors([errorMessage]);
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
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="mx-auto w-12 h-12 bg-[var(--colors-semantic-info-100)] rounded-full flex items-center justify-center">
            <svg className="w-6 h-6 text-[var(--colors-semantic-info-500)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" 
                d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          
          <h2 className="text-xl font-semibold text-[var(--colors-text-on-surface)]">
            Verify your email
          </h2>
          
          <div className="space-y-1">
            <p className="text-[var(--colors-text-on-surface-variant)]">
              We've sent a verification link to:
            </p>
            {email && (
              <p className="font-medium text-[var(--colors-text-on-surface)]">
                {email}
              </p>
            )}
            <p className="text-sm text-[var(--colors-text-on-surface-variant)]">
              Click the link in the email or enter the verification code below.
            </p>
          </div>
        </div>

        {/* Errors */}
        {errors.length > 0 && (
          <Alert 
            variant="error" 
            title="Verification Failed"
            description={errors[0]}
          />
        )}

        {/* Success message for resend */}
        {resendCooldown > 0 && (
          <Alert
            variant="success"
            title="Email Sent"
            description="A new verification email has been sent. Please check your inbox."
          />
        )}

        {/* Verification Token Field */}
        <Input
          type="text"
          label="Verification code"
          placeholder="Enter the verification code"
          value={token}
          onChange={(e) => {
            setToken(e.target.value);
            setErrors([]);
          }}
          disabled={loading}
          isRequired
          autoFocus
          leftIcon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" 
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          helperText="Check your email for the verification code"
        />

        {/* Submit Button */}
        <Button
          type="submit"
          variant="primary"
          size="lg"
          fullWidth
          loading={loading}
          loadingText="Verifying..."
          disabled={loading}
        >
          Verify email
        </Button>

        {/* Resend Email */}
        <div className="text-center space-y-2">
          <p className="text-sm text-[var(--colors-text-on-surface-variant)]">
            Didn't receive the email?
          </p>
          
          {email && (
            <div className="flex items-center justify-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleResendVerification}
                disabled={loading || isResending || resendCooldown > 0}
                loading={isResending}
                loadingText="Sending..."
              >
                {resendCooldown > 0 
                  ? `Resend in ${resendCooldown}s` 
                  : 'Resend email'
                }
              </Button>
            </div>
          )}

          <div className="text-xs text-[var(--colors-text-on-surface-variant)] space-y-1">
            <p>• Check your spam folder</p>
            <p>• Make sure {email} is correct</p>
            <p>• The link expires in 24 hours</p>
          </div>
        </div>

        {/* Help Section */}
        <Alert
          variant="info"
          title="Need help?"
          description="If you continue to have problems, please contact our support team."
          actions={
            <Button variant="ghost" size="sm">
              Contact Support
            </Button>
          }
        />
      </form>
    );
  }
);

EmailVerificationForm.displayName = 'EmailVerificationForm';