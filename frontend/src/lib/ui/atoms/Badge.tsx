/**
 * Badge Component - Foundational UI Atom
 * Small status indicator component with multiple variants
 */

import React, { forwardRef } from 'react';
import { cn } from '@/lib/utils/cn';

// Badge variant definitions
const badgeVariants = {
  variant: {
    default: [
      'bg-[var(--colors-surface-surface-container)]',
      'text-[var(--colors-text-on-surface)]',
      'border-[var(--colors-border-default)]',
    ].join(' '),
    primary: [
      'bg-[var(--colors-semantic-primary-500)]',
      'text-[var(--colors-text-on-primary)]',
      'border-[var(--colors-semantic-primary-500)]',
    ].join(' '),
    secondary: [
      'bg-[var(--colors-semantic-secondary-100)]',
      'text-[var(--colors-semantic-secondary-700)]',
      'border-[var(--colors-semantic-secondary-200)]',
    ].join(' '),
    success: [
      'bg-[var(--colors-semantic-success-100)]',
      'text-[var(--colors-semantic-success-700)]',
      'border-[var(--colors-semantic-success-200)]',
    ].join(' '),
    warning: [
      'bg-[var(--colors-semantic-warning-100)]',
      'text-[var(--colors-semantic-warning-700)]',
      'border-[var(--colors-semantic-warning-200)]',
    ].join(' '),
    error: [
      'bg-[var(--colors-semantic-error-100)]',
      'text-[var(--colors-semantic-error-700)]',
      'border-[var(--colors-semantic-error-200)]',
    ].join(' '),
    info: [
      'bg-[var(--colors-semantic-info-100)]',
      'text-[var(--colors-semantic-info-700)]',
      'border-[var(--colors-semantic-info-200)]',
    ].join(' '),
    outline: [
      'bg-transparent',
      'text-[var(--colors-text-on-surface)]',
      'border-[var(--colors-border-default)]',
    ].join(' '),
  },
  size: {
    xs: 'px-1.5 py-0.5 text-xs h-4 min-w-[1rem]',
    sm: 'px-2 py-0.5 text-xs h-5 min-w-[1.25rem]',
    md: 'px-2.5 py-1 text-sm h-6 min-w-[1.5rem]',
    lg: 'px-3 py-1 text-sm h-7 min-w-[1.75rem]',
  },
  shape: {
    rounded: 'rounded-[var(--border-radius-base)]',
    pill: 'rounded-full',
    square: 'rounded-none',
  },
};

// Dot indicator component
const DotIndicator = ({ className, variant }: { className?: string; variant: keyof typeof badgeVariants.variant }) => {
  const dotColors = {
    default: 'bg-[var(--colors-text-on-surface)]',
    primary: 'bg-[var(--colors-semantic-primary-500)]',
    secondary: 'bg-[var(--colors-semantic-secondary-500)]',
    success: 'bg-[var(--colors-semantic-success-500)]',
    warning: 'bg-[var(--colors-semantic-warning-500)]',
    error: 'bg-[var(--colors-semantic-error-500)]',
    info: 'bg-[var(--colors-semantic-info-500)]',
    outline: 'bg-[var(--colors-text-on-surface)]',
  };

  return (
    <span className={cn('w-2 h-2 rounded-full', dotColors[variant], className)} />
  );
};

// Badge Props Interface
export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: keyof typeof badgeVariants.variant;
  size?: keyof typeof badgeVariants.size;
  shape?: keyof typeof badgeVariants.shape;
  dot?: boolean;
  children: React.ReactNode;
}

// Badge Component
export const Badge = forwardRef<HTMLDivElement, BadgeProps>(
  (
    {
      className,
      variant = 'default',
      size = 'md',
      shape = 'pill',
      dot = false,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={cn(
          // Base styles
          'inline-flex items-center justify-center gap-1',
          'font-medium border',
          'whitespace-nowrap',
          
          // Variant styles
          badgeVariants.variant[variant],
          
          // Size styles
          badgeVariants.size[size],
          
          // Shape styles
          badgeVariants.shape[shape],
          
          className
        )}
        {...props}
      >
        {dot && <DotIndicator variant={variant} />}
        <span className="truncate">{children}</span>
      </div>
    );
  }
);

Badge.displayName = 'Badge';

// Number Badge Component (for counts, notifications)
export interface NumberBadgeProps extends Omit<BadgeProps, 'children'> {
  value: number;
  max?: number;
  showZero?: boolean;
}

export const NumberBadge = forwardRef<HTMLDivElement, NumberBadgeProps>(
  ({ value, max = 99, showZero = false, ...props }, ref) => {
    if (value === 0 && !showZero) {
      return null;
    }
    
    const displayValue = max && value > max ? `${max}+` : value.toString();
    
    return (
      <Badge ref={ref} size="xs" shape="pill" {...props}>
        {displayValue}
      </Badge>
    );
  }
);

NumberBadge.displayName = 'NumberBadge';

// Status Badge Component (for status indicators)
export interface StatusBadgeProps extends Omit<BadgeProps, 'variant' | 'children'> {
  status: 'active' | 'inactive' | 'pending' | 'success' | 'error' | 'warning';
  showDot?: boolean;
  labels?: Record<string, string>;
}

export const StatusBadge = forwardRef<HTMLDivElement, StatusBadgeProps>(
  ({ 
    status, 
    showDot = true, 
    labels = {
      active: 'Active',
      inactive: 'Inactive', 
      pending: 'Pending',
      success: 'Success',
      error: 'Error',
      warning: 'Warning',
    },
    ...props 
  }, ref) => {
    const statusVariants = {
      active: 'success' as const,
      inactive: 'secondary' as const,
      pending: 'warning' as const,
      success: 'success' as const,
      error: 'error' as const,
      warning: 'warning' as const,
    };
    
    return (
      <Badge 
        ref={ref}
        variant={statusVariants[status]}
        dot={showDot}
        {...props}
      >
        {labels[status] || status}
      </Badge>
    );
  }
);

StatusBadge.displayName = 'StatusBadge';

// Removable Badge Component (with close button)
export interface RemovableBadgeProps extends BadgeProps {
  onRemove?: () => void;
  removeLabel?: string;
}

const CloseIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    fill="none"
    height="12"
    viewBox="0 0 24 24"
    width="12"
    xmlns="http://www.w3.org/2000/svg"
  >
    <line x1="18" x2="6" y1="6" y2="18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    <line x1="6" x2="18" y1="6" y2="18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

export const RemovableBadge = forwardRef<HTMLDivElement, RemovableBadgeProps>(
  ({ 
    children, 
    onRemove, 
    removeLabel = 'Remove',
    className,
    ...props 
  }, ref) => {
    return (
      <Badge
        ref={ref}
        className={cn('pr-1', className)}
        {...props}
      >
        <span className="truncate">{children}</span>
        {onRemove && (
          <button
            type="button"
            onClick={onRemove}
            className={cn(
              'ml-1 p-0.5 rounded-full',
              'hover:bg-black/10 focus:outline-none focus:bg-black/10',
              'transition-colors duration-150'
            )}
            aria-label={removeLabel}
          >
            <CloseIcon />
          </button>
        )}
      </Badge>
    );
  }
);

RemovableBadge.displayName = 'RemovableBadge';

// Interactive Badge Component (clickable)
export interface InteractiveBadgeProps extends BadgeProps {
  onClick?: () => void;
  href?: string;
  target?: string;
  disabled?: boolean;
}

export const InteractiveBadge = forwardRef<HTMLElement, InteractiveBadgeProps>(
  ({ 
    onClick, 
    href, 
    target, 
    disabled = false,
    className,
    children,
    ...props 
  }, ref) => {
    const Component = href ? 'a' : 'button';
    const isClickable = onClick || href;
    
    return (
      <Component
        ref={ref as any}
        href={href}
        target={target}
        onClick={disabled ? undefined : onClick}
        disabled={disabled}
        className={cn(
          // Base badge styles
          'inline-flex items-center justify-center gap-1',
          'font-medium border whitespace-nowrap',
          
          // Variant styles
          badgeVariants.variant[props.variant || 'default'],
          
          // Size styles
          badgeVariants.size[props.size || 'md'],
          
          // Shape styles
          badgeVariants.shape[props.shape || 'pill'],
          
          // Interactive styles
          isClickable && !disabled && [
            'cursor-pointer transition-all duration-150',
            'hover:scale-105 active:scale-95',
            'focus:outline-none focus:ring-2 focus:ring-[var(--colors-border-focus)]/20',
          ],
          
          // Disabled styles
          disabled && 'opacity-50 cursor-not-allowed',
          
          className
        )}
        type={Component === 'button' ? 'button' : undefined}
      >
        {props.dot && <DotIndicator variant={props.variant || 'default'} />}
        <span className="truncate">{children}</span>
      </Component>
    );
  }
);

InteractiveBadge.displayName = 'InteractiveBadge';

// Export badge utilities
export const badgeUtils = {
  variants: badgeVariants,
  getVariantClasses: (variant: keyof typeof badgeVariants.variant) => 
    badgeVariants.variant[variant],
  getSizeClasses: (size: keyof typeof badgeVariants.size) => 
    badgeVariants.size[size],
  getShapeClasses: (shape: keyof typeof badgeVariants.shape) => 
    badgeVariants.shape[shape],
};