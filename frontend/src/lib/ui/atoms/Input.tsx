/**
 * Input Component - Foundational UI Atom
 * Accessible and customizable input field with validation states
 */

import React, { forwardRef, useState } from 'react';
import { cn, focusRing } from '@/lib/utils/cn';

// Input variant definitions
const inputVariants = {
  variant: {
    default: [
      'bg-[var(--colors-surface-background)]',
      'border-[var(--colors-border-default)]',
      'text-[var(--colors-text-on-surface)]',
      'placeholder:text-[var(--colors-text-on-surface-variant)]',
    ].join(' '),
    filled: [
      'bg-[var(--colors-surface-surface-variant)]',
      'border-[var(--colors-border-muted)]',
      'text-[var(--colors-text-on-surface)]',
      'placeholder:text-[var(--colors-text-on-surface-variant)]',
    ].join(' '),
    flushed: [
      'bg-transparent',
      'border-t-0 border-l-0 border-r-0 border-b-2',
      'border-[var(--colors-border-default)]',
      'text-[var(--colors-text-on-surface)]',
      'placeholder:text-[var(--colors-text-on-surface-variant)]',
      'rounded-none',
    ].join(' '),
  },
  size: {
    sm: 'h-8 px-3 text-sm rounded-[var(--border-radius-sm)]',
    md: 'h-10 px-3 text-sm rounded-[var(--border-radius-base)]',
    lg: 'h-12 px-4 text-base rounded-[var(--border-radius-md)]',
  },
  state: {
    default: '',
    error: [
      'border-[var(--colors-border-error)]',
      'focus:border-[var(--colors-semantic-error-500)]',
      'focus:ring-[var(--colors-semantic-error-500)]/20',
    ].join(' '),
    success: [
      'border-[var(--colors-border-success)]',
      'focus:border-[var(--colors-semantic-success-500)]',
      'focus:ring-[var(--colors-semantic-success-500)]/20',
    ].join(' '),
    warning: [
      'border-[var(--colors-border-warning)]',
      'focus:border-[var(--colors-semantic-warning-500)]',
      'focus:ring-[var(--colors-semantic-warning-500)]/20',
    ].join(' '),
  },
};

// Eye icon components for password visibility
const EyeIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    fill="none"
    height="20"
    viewBox="0 0 24 24"
    width="20"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
    />
    <circle
      cx="12"
      cy="12"
      r="3"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
    />
  </svg>
);

const EyeOffIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    fill="none"
    height="20"
    viewBox="0 0 24 24"
    width="20"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
    />
    <line
      x1="1"
      x2="23"
      y1="1"
      y2="23"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="2"
    />
  </svg>
);

// Input Props Interface
export interface InputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size'> {
  variant?: keyof typeof inputVariants.variant;
  size?: keyof typeof inputVariants.size;
  state?: keyof typeof inputVariants.state;
  label?: string;
  helperText?: string;
  errorText?: string;
  successText?: string;
  warningText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  showPasswordToggle?: boolean;
  fullWidth?: boolean;
  isRequired?: boolean;
}

// Input Component
export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      className,
      variant = 'default',
      size = 'md',
      state = 'default',
      label,
      helperText,
      errorText,
      successText,
      warningText,
      leftIcon,
      rightIcon,
      showPasswordToggle = false,
      fullWidth = true,
      isRequired = false,
      type = 'text',
      id,
      disabled,
      ...props
    },
    ref
  ) => {
    const [showPassword, setShowPassword] = useState(false);
    const [isFocused, setIsFocused] = useState(false);
    
    // Generate unique ID if not provided
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
    
    // Determine input type
    const inputType = showPasswordToggle && type === 'password' 
      ? (showPassword ? 'text' : 'password')
      : type;
    
    // Determine state based on validation texts
    const currentState = errorText ? 'error' 
      : successText ? 'success'
      : warningText ? 'warning'
      : state;
    
    // Get validation message
    const validationMessage = errorText || successText || warningText || helperText;
    
    // Toggle password visibility
    const togglePasswordVisibility = () => {
      setShowPassword(!showPassword);
    };
    
    return (
      <div className={cn('flex flex-col gap-1.5', fullWidth ? 'w-full' : 'w-auto')}>
        {/* Label */}
        {label && (
          <label
            htmlFor={inputId}
            className={cn(
              'text-sm font-medium',
              'text-[var(--colors-text-on-surface)]',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
          >
            {label}
            {isRequired && (
              <span className="ml-1 text-[var(--colors-semantic-error-500)]" aria-label="required">
                *
              </span>
            )}
          </label>
        )}
        
        {/* Input Container */}
        <div className={cn('relative', fullWidth ? 'w-full' : 'w-auto')}>
          {/* Left Icon */}
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--colors-text-on-surface-variant)] pointer-events-none">
              {leftIcon}
            </div>
          )}
          
          {/* Input Field */}
          <input
            ref={ref}
            type={inputType}
            id={inputId}
            className={cn(
              // Base styles
              'w-full border transition-all duration-200',
              'focus:outline-none focus:ring-2 focus:ring-[var(--colors-border-focus)]/20',
              
              // Variant styles
              inputVariants.variant[variant],
              
              // Size styles
              inputVariants.size[size],
              
              // State styles
              inputVariants.state[currentState],
              
              // Icon padding
              leftIcon && 'pl-10',
              (rightIcon || showPasswordToggle) && 'pr-10',
              
              // Disabled styles
              disabled && 'opacity-50 cursor-not-allowed bg-[var(--colors-surface-surface-variant)]',
              
              // Focus styles
              isFocused && 'border-[var(--colors-border-focus)]',
              
              // Full width
              fullWidth ? 'w-full' : 'w-auto',
              
              className
            )}
            disabled={disabled}
            required={isRequired}
            onFocus={(e) => {
              setIsFocused(true);
              props.onFocus?.(e);
            }}
            onBlur={(e) => {
              setIsFocused(false);
              props.onBlur?.(e);
            }}
            {...props}
          />
          
          {/* Right Icon or Password Toggle */}
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            {showPasswordToggle && type === 'password' ? (
              <button
                type="button"
                onClick={togglePasswordVisibility}
                className={cn(
                  'text-[var(--colors-text-on-surface-variant)]',
                  'hover:text-[var(--colors-text-on-surface)]',
                  'focus:outline-none focus:text-[var(--colors-text-on-surface)]',
                  'transition-colors duration-200'
                )}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                tabIndex={-1}
              >
                {showPassword ? <EyeOffIcon /> : <EyeIcon />}
              </button>
            ) : rightIcon ? (
              <div className="text-[var(--colors-text-on-surface-variant)] pointer-events-none">
                {rightIcon}
              </div>
            ) : null}
          </div>
        </div>
        
        {/* Helper/Error/Success Text */}
        {validationMessage && (
          <p
            className={cn(
              'text-xs',
              currentState === 'error' && 'text-[var(--colors-semantic-error-500)]',
              currentState === 'success' && 'text-[var(--colors-semantic-success-500)]',
              currentState === 'warning' && 'text-[var(--colors-semantic-warning-500)]',
              currentState === 'default' && 'text-[var(--colors-text-on-surface-variant)]'
            )}
            role={currentState === 'error' ? 'alert' : undefined}
          >
            {validationMessage}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

// Textarea Component
export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  variant?: keyof typeof inputVariants.variant;
  state?: keyof typeof inputVariants.state;
  label?: string;
  helperText?: string;
  errorText?: string;
  successText?: string;
  warningText?: string;
  fullWidth?: boolean;
  isRequired?: boolean;
  resize?: 'none' | 'vertical' | 'horizontal' | 'both';
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      className,
      variant = 'default',
      state = 'default',
      label,
      helperText,
      errorText,
      successText,
      warningText,
      fullWidth = true,
      isRequired = false,
      resize = 'vertical',
      id,
      disabled,
      rows = 3,
      ...props
    },
    ref
  ) => {
    const [isFocused, setIsFocused] = useState(false);
    
    // Generate unique ID if not provided
    const inputId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`;
    
    // Determine state based on validation texts
    const currentState = errorText ? 'error' 
      : successText ? 'success'
      : warningText ? 'warning'
      : state;
    
    // Get validation message
    const validationMessage = errorText || successText || warningText || helperText;
    
    return (
      <div className={cn('flex flex-col gap-1.5', fullWidth ? 'w-full' : 'w-auto')}>
        {/* Label */}
        {label && (
          <label
            htmlFor={inputId}
            className={cn(
              'text-sm font-medium',
              'text-[var(--colors-text-on-surface)]',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
          >
            {label}
            {isRequired && (
              <span className="ml-1 text-[var(--colors-semantic-error-500)]" aria-label="required">
                *
              </span>
            )}
          </label>
        )}
        
        {/* Textarea Field */}
        <textarea
          ref={ref}
          id={inputId}
          rows={rows}
          className={cn(
            // Base styles
            'w-full border transition-all duration-200',
            'focus:outline-none focus:ring-2 focus:ring-[var(--colors-border-focus)]/20',
            'px-3 py-2 text-sm rounded-[var(--border-radius-base)]',
            
            // Resize
            resize === 'none' && 'resize-none',
            resize === 'vertical' && 'resize-y',
            resize === 'horizontal' && 'resize-x',
            resize === 'both' && 'resize',
            
            // Variant styles
            inputVariants.variant[variant],
            
            // State styles
            inputVariants.state[currentState],
            
            // Disabled styles
            disabled && 'opacity-50 cursor-not-allowed bg-[var(--colors-surface-surface-variant)]',
            
            // Focus styles
            isFocused && 'border-[var(--colors-border-focus)]',
            
            className
          )}
          disabled={disabled}
          required={isRequired}
          onFocus={(e) => {
            setIsFocused(true);
            props.onFocus?.(e);
          }}
          onBlur={(e) => {
            setIsFocused(false);
            props.onBlur?.(e);
          }}
          {...props}
        />
        
        {/* Helper/Error/Success Text */}
        {validationMessage && (
          <p
            className={cn(
              'text-xs',
              currentState === 'error' && 'text-[var(--colors-semantic-error-500)]',
              currentState === 'success' && 'text-[var(--colors-semantic-success-500)]',
              currentState === 'warning' && 'text-[var(--colors-semantic-warning-500)]',
              currentState === 'default' && 'text-[var(--colors-text-on-surface-variant)]'
            )}
            role={currentState === 'error' ? 'alert' : undefined}
          >
            {validationMessage}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

// Export input utilities
export const inputUtils = {
  variants: inputVariants,
  getVariantClasses: (variant: keyof typeof inputVariants.variant) => 
    inputVariants.variant[variant],
  getSizeClasses: (size: keyof typeof inputVariants.size) => 
    inputVariants.size[size],
  getStateClasses: (state: keyof typeof inputVariants.state) => 
    inputVariants.state[state],
};