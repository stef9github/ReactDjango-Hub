/**
 * Button Component - Foundational UI Atom
 * Highly customizable button with multiple variants, sizes, and states
 */

import React, { forwardRef } from 'react';
import { cn, focusRing, disabled } from '@/lib/utils/cn';

// Button variant definitions
const buttonVariants = {
  variant: {
    primary: [
      'bg-[var(--colors-semantic-primary-500)] text-[var(--colors-text-on-primary)]',
      'hover:bg-[var(--colors-semantic-primary-600)]',
      'active:bg-[var(--colors-semantic-primary-700)]',
      'border-[var(--colors-semantic-primary-500)]',
    ].join(' '),
    secondary: [
      'bg-[var(--colors-semantic-secondary-100)] text-[var(--colors-semantic-secondary-700)]',
      'hover:bg-[var(--colors-semantic-secondary-200)]',
      'active:bg-[var(--colors-semantic-secondary-300)]',
      'border-[var(--colors-semantic-secondary-200)]',
    ].join(' '),
    outline: [
      'bg-transparent text-[var(--colors-text-on-surface)]',
      'hover:bg-[var(--colors-surface-surface-variant)]',
      'active:bg-[var(--colors-surface-surface-container)]',
      'border-[var(--colors-border-default)]',
    ].join(' '),
    ghost: [
      'bg-transparent text-[var(--colors-text-on-surface)]',
      'hover:bg-[var(--colors-surface-surface-variant)]',
      'active:bg-[var(--colors-surface-surface-container)]',
      'border-transparent',
    ].join(' '),
    success: [
      'bg-[var(--colors-semantic-success-500)] text-[var(--colors-text-on-success)]',
      'hover:bg-[var(--colors-semantic-success-600)]',
      'active:bg-[var(--colors-semantic-success-700)]',
      'border-[var(--colors-semantic-success-500)]',
    ].join(' '),
    warning: [
      'bg-[var(--colors-semantic-warning-500)] text-[var(--colors-text-on-warning)]',
      'hover:bg-[var(--colors-semantic-warning-600)]',
      'active:bg-[var(--colors-semantic-warning-700)]',
      'border-[var(--colors-semantic-warning-500)]',
    ].join(' '),
    error: [
      'bg-[var(--colors-semantic-error-500)] text-[var(--colors-text-on-error)]',
      'hover:bg-[var(--colors-semantic-error-600)]',
      'active:bg-[var(--colors-semantic-error-700)]',
      'border-[var(--colors-semantic-error-500)]',
    ].join(' '),
    link: [
      'bg-transparent text-[var(--colors-semantic-primary-500)]',
      'hover:text-[var(--colors-semantic-primary-600)]',
      'active:text-[var(--colors-semantic-primary-700)]',
      'border-transparent underline-offset-4 hover:underline',
    ].join(' '),
  },
  size: {
    xs: 'h-7 px-2 text-xs rounded-[var(--border-radius-sm)]',
    sm: 'h-8 px-3 text-sm rounded-[var(--border-radius-base)]',
    md: 'h-10 px-4 text-sm rounded-[var(--border-radius-md)]',
    lg: 'h-11 px-6 text-base rounded-[var(--border-radius-md)]',
    xl: 'h-12 px-8 text-base rounded-[var(--border-radius-lg)]',
    icon: 'h-10 w-10 rounded-[var(--border-radius-md)]',
  },
  fullWidth: {
    true: 'w-full',
    false: 'w-auto',
  },
  loading: {
    true: 'cursor-wait',
    false: '',
  },
};

// Loading spinner component
const Spinner = ({ className }: { className?: string }) => (
  <svg
    className={cn('animate-spin', className)}
    fill="none"
    height="16"
    viewBox="0 0 16 16"
    width="16"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle
      className="opacity-25"
      cx="8"
      cy="8"
      r="7"
      stroke="currentColor"
      strokeWidth="2"
    />
    <path
      className="opacity-75"
      d="M15 8a7.002 7.002 0 00-7-7"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
    />
  </svg>
);

// Button Props Interface
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof buttonVariants.variant;
  size?: keyof typeof buttonVariants.size;
  fullWidth?: boolean;
  loading?: boolean;
  loadingText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  children: React.ReactNode;
}

// Button Component
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      fullWidth = false,
      loading = false,
      loadingText,
      leftIcon,
      rightIcon,
      disabled: isDisabled,
      children,
      ...props
    },
    ref
  ) => {
    const isLoading = loading;
    const isDisabledState = isDisabled || isLoading;

    return (
      <button
        ref={ref}
        className={cn(
          // Base styles
          'inline-flex items-center justify-center gap-2',
          'font-medium transition-all duration-200',
          'border border-solid',
          'cursor-pointer select-none',
          
          // Variant styles
          buttonVariants.variant[variant],
          
          // Size styles
          buttonVariants.size[size],
          
          // Full width
          buttonVariants.fullWidth[fullWidth],
          
          // Loading state
          buttonVariants.loading[isLoading],
          
          // Focus styles
          focusRing,
          
          // Disabled styles
          isDisabledState && disabled,
          
          // Custom className
          className
        )}
        disabled={isDisabledState}
        {...props}
      >
        {/* Left Icon */}
        {leftIcon && !isLoading && (
          <span className="flex-shrink-0">{leftIcon}</span>
        )}
        
        {/* Loading Spinner */}
        {isLoading && (
          <Spinner className="flex-shrink-0" />
        )}
        
        {/* Button Text */}
        <span className={cn(isLoading && loadingText && 'sr-only')}>
          {isLoading && loadingText ? loadingText : children}
        </span>
        
        {/* Loading Text (visible) */}
        {isLoading && loadingText && (
          <span>{loadingText}</span>
        )}
        
        {/* Right Icon */}
        {rightIcon && !isLoading && (
          <span className="flex-shrink-0">{rightIcon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

// Button Group Component for multiple buttons
export interface ButtonGroupProps {
  children: React.ReactNode;
  className?: string;
  size?: keyof typeof buttonVariants.size;
  orientation?: 'horizontal' | 'vertical';
  attached?: boolean;
}

export const ButtonGroup = ({
  children,
  className,
  size,
  orientation = 'horizontal',
  attached = false,
}: ButtonGroupProps) => {
  return (
    <div
      className={cn(
        'flex',
        orientation === 'horizontal' ? 'flex-row' : 'flex-col',
        attached && orientation === 'horizontal' && '[&>*:not(:first-child)]:border-l-0 [&>*:not(:first-child)]:rounded-l-none [&>*:not(:last-child)]:rounded-r-none',
        attached && orientation === 'vertical' && '[&>*:not(:first-child)]:border-t-0 [&>*:not(:first-child)]:rounded-t-none [&>*:not(:last-child)]:rounded-b-none',
        !attached && (orientation === 'horizontal' ? 'gap-2' : 'gap-1'),
        className
      )}
    >
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child) && size) {
          return React.cloneElement(child as React.ReactElement<ButtonProps>, {
            size,
          });
        }
        return child;
      })}
    </div>
  );
};

// Icon Button Component
export interface IconButtonProps extends Omit<ButtonProps, 'leftIcon' | 'rightIcon' | 'children'> {
  icon: React.ReactNode;
  'aria-label': string;
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ icon, size = 'icon', ...props }, ref) => {
    return (
      <Button ref={ref} size={size} {...props}>
        {icon}
      </Button>
    );
  }
);

IconButton.displayName = 'IconButton';

// Export button utilities
export const buttonUtils = {
  variants: buttonVariants,
  getVariantClasses: (variant: keyof typeof buttonVariants.variant) => 
    buttonVariants.variant[variant],
  getSizeClasses: (size: keyof typeof buttonVariants.size) => 
    buttonVariants.size[size],
};