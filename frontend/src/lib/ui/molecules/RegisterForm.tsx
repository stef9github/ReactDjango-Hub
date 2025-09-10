/**
 * RegisterForm Component - Authentication Molecule
 * Complete registration form with validation and password strength
 */

import React, { forwardRef, useState } from 'react';
import { 
  Button, 
  Input, 
  Alert, 
  Badge,
  cn 
} from '@/lib/ui/atoms';
import { useRegisterForm, usePasswordStrength } from '@/lib/auth';
import type { RegisterFormProps, PasswordStrength } from '@/types/auth';

// Password strength indicator
const PasswordStrengthIndicator = ({ strength }: { strength: PasswordStrength }) => {
  const getStrengthLabel = (score: number): string => {
    switch (score) {
      case 0: return 'Very weak';
      case 1: return 'Weak';
      case 2: return 'Fair';
      case 3: return 'Good';
      case 4: return 'Strong';
      default: return 'Very weak';
    }
  };

  const getStrengthColor = (score: number): 'error' | 'warning' | 'info' | 'success' => {
    switch (score) {
      case 0:
      case 1: return 'error';
      case 2: return 'warning';
      case 3: return 'info';
      case 4: return 'success';
      default: return 'error';
    }
  };

  const getStrengthWidth = (score: number): string => {
    return `${(score / 4) * 100}%`;
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs text-[var(--colors-text-on-surface-variant)]">
          Password strength
        </span>
        <Badge 
          variant={getStrengthColor(strength.score)}
          size="xs"
        >
          {getStrengthLabel(strength.score)}
        </Badge>
      </div>
      
      {/* Progress bar */}
      <div className="w-full bg-[var(--colors-border-muted)] rounded-full h-2">
        <div
          className={cn(
            'h-2 rounded-full transition-all duration-300',
            {
              'bg-[var(--colors-semantic-error-500)]': strength.score <= 1,
              'bg-[var(--colors-semantic-warning-500)]': strength.score === 2,
              'bg-[var(--colors-semantic-info-500)]': strength.score === 3,
              'bg-[var(--colors-semantic-success-500)]': strength.score === 4,
            }
          )}
          style={{ width: getStrengthWidth(strength.score) }}
        />
      </div>
      
      {/* Feedback */}
      {strength.feedback.length > 0 && (
        <ul className="text-xs text-[var(--colors-text-on-surface-variant)] space-y-1">
          {strength.feedback.map((feedback, index) => (
            <li key={index} className="flex items-center gap-1">
              <span className="text-[var(--colors-semantic-warning-500)]">•</span>
              {feedback}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export const RegisterForm = forwardRef<HTMLFormElement, RegisterFormProps>(
  (
    {
      onSubmit,
      onError,
      onSuccess,
      onLogin,
      isLoading: externalLoading = false,
      showPasswordStrength = true,
      requirePhoneNumber = false,
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
      handleRegister,
    } = useRegisterForm();

    const passwordStrength = usePasswordStrength(data.password);
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
          const result = await handleRegister(e);
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
            title="Registration Failed"
            description={generalErrors[0].message}
          />
        )}

        {/* Name Fields */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input
            type="text"
            label="First name"
            placeholder="Enter your first name"
            value={data.first_name}
            onChange={(e) => handleChange('first_name')(e.target.value)}
            onBlur={handleBlur('first_name')}
            errorText={getFieldError('first_name')}
            disabled={loading}
            isRequired
            autoComplete="given-name"
          />

          <Input
            type="text"
            label="Last name"
            placeholder="Enter your last name"
            value={data.last_name}
            onChange={(e) => handleChange('last_name')(e.target.value)}
            onBlur={handleBlur('last_name')}
            errorText={getFieldError('last_name')}
            disabled={loading}
            isRequired
            autoComplete="family-name"
          />
        </div>

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

        {/* Phone Number Field */}
        <Input
          type="tel"
          label="Phone number"
          placeholder="Enter your phone number"
          value={data.phone_number || ''}
          onChange={(e) => handleChange('phone_number')(e.target.value)}
          onBlur={handleBlur('phone_number')}
          errorText={getFieldError('phone_number')}
          disabled={loading}
          isRequired={requirePhoneNumber}
          autoComplete="tel"
          leftIcon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" 
                d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
          }
          helperText={!requirePhoneNumber ? "Optional" : undefined}
        />

        {/* Password Field */}
        <Input
          type="password"
          label="Password"
          placeholder="Create a strong password"
          value={data.password}
          onChange={(e) => handleChange('password')(e.target.value)}
          onBlur={handleBlur('password')}
          errorText={getFieldError('password')}
          disabled={loading}
          isRequired
          autoComplete="new-password"
          showPasswordToggle
          leftIcon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" 
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          }
        />

        {/* Password Strength Indicator */}
        {showPasswordStrength && data.password && (
          <PasswordStrengthIndicator strength={passwordStrength} />
        )}

        {/* Confirm Password Field */}
        <Input
          type="password"
          label="Confirm password"
          placeholder="Confirm your password"
          value={data.password_confirm}
          onChange={(e) => handleChange('password_confirm')(e.target.value)}
          onBlur={handleBlur('password_confirm')}
          errorText={getFieldError('password_confirm')}
          disabled={loading}
          isRequired
          autoComplete="new-password"
          showPasswordToggle
          leftIcon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" 
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />

        {/* Terms and Conditions */}
        <div className="flex items-start">
          <input
            type="checkbox"
            id="terms"
            required
            className="mt-1 w-4 h-4 text-[var(--colors-semantic-primary-500)] 
                     border-[var(--colors-border-default)] rounded 
                     focus:ring-[var(--colors-semantic-primary-500)] focus:ring-2"
            disabled={loading}
          />
          <label htmlFor="terms" className="ml-3 text-sm text-[var(--colors-text-on-surface-variant)]">
            I agree to the{' '}
            <a 
              href="/terms" 
              className="font-medium text-[var(--colors-semantic-primary-500)] hover:text-[var(--colors-semantic-primary-600)] focus:outline-none focus:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              Terms of Service
            </a>{' '}
            and{' '}
            <a 
              href="/privacy" 
              className="font-medium text-[var(--colors-semantic-primary-500)] hover:text-[var(--colors-semantic-primary-600)] focus:outline-none focus:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              Privacy Policy
            </a>
          </label>
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          variant="primary"
          size="lg"
          fullWidth
          loading={loading}
          loadingText="Creating account..."
          disabled={loading}
        >
          Create account
        </Button>

        {/* Login Link */}
        {onLogin && (
          <div className="text-center">
            <span className="text-sm text-[var(--colors-text-on-surface-variant)]">
              Already have an account?{' '}
              <button
                type="button"
                onClick={onLogin}
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
                Sign in
              </button>
            </span>
          </div>
        )}
      </form>
    );
  }
);

RegisterForm.displayName = 'RegisterForm';