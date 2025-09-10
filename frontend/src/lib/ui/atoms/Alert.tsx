/**
 * Alert Component - Foundational UI Atom
 * Accessible notification component for various message types
 */

import React, { forwardRef } from 'react';
import { cn } from '@/lib/utils/cn';

// Alert icons
const InfoIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    fill="none"
    height="20"
    viewBox="0 0 24 24"
    width="20"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
    <path d="M12 16v-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    <path d="m12 8 .01 0" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

const SuccessIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    fill="none"
    height="20"
    viewBox="0 0 24 24"
    width="20"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
  </svg>
);

const WarningIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    fill="none"
    height="20"
    viewBox="0 0 24 24"
    width="20"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    <line x1="12" x2="12" y1="9" y2="13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    <line x1="12" x2="12.01" y1="17" y2="17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

const ErrorIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    fill="none"
    height="20"
    viewBox="0 0 24 24"
    width="20"
    xmlns="http://www.w3.org/2000/svg"
  >
    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
    <line x1="15" x2="9" y1="9" y2="15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    <line x1="9" x2="15" y1="9" y2="15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

const CloseIcon = ({ className }: { className?: string }) => (
  <svg
    className={className}
    fill="none"
    height="16"
    viewBox="0 0 24 24"
    width="16"
    xmlns="http://www.w3.org/2000/svg"
  >
    <line x1="18" x2="6" y1="6" y2="18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    <line x1="6" x2="18" y1="6" y2="18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

// Alert variant definitions
const alertVariants = {
  variant: {
    info: [
      'bg-[var(--colors-semantic-info-50)]',
      'border-[var(--colors-semantic-info-200)]',
      'text-[var(--colors-semantic-info-800)]',
      '[&>svg]:text-[var(--colors-semantic-info-500)]',
    ].join(' '),
    success: [
      'bg-[var(--colors-semantic-success-50)]',
      'border-[var(--colors-semantic-success-200)]',
      'text-[var(--colors-semantic-success-800)]',
      '[&>svg]:text-[var(--colors-semantic-success-500)]',
    ].join(' '),
    warning: [
      'bg-[var(--colors-semantic-warning-50)]',
      'border-[var(--colors-semantic-warning-200)]',
      'text-[var(--colors-semantic-warning-800)]',
      '[&>svg]:text-[var(--colors-semantic-warning-500)]',
    ].join(' '),
    error: [
      'bg-[var(--colors-semantic-error-50)]',
      'border-[var(--colors-semantic-error-200)]',
      'text-[var(--colors-semantic-error-800)]',
      '[&>svg]:text-[var(--colors-semantic-error-500)]',
    ].join(' '),
    neutral: [
      'bg-[var(--colors-surface-surface-variant)]',
      'border-[var(--colors-border-default)]',
      'text-[var(--colors-text-on-surface)]',
      '[&>svg]:text-[var(--colors-text-on-surface-variant)]',
    ].join(' '),
  },
  size: {
    sm: 'p-3 text-sm',
    md: 'p-4 text-sm',
    lg: 'p-5 text-base',
  },
};

// Icon mapping
const iconMap = {
  info: InfoIcon,
  success: SuccessIcon,
  warning: WarningIcon,
  error: ErrorIcon,
  neutral: InfoIcon,
};

// Alert Props Interface
export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: keyof typeof alertVariants.variant;
  size?: keyof typeof alertVariants.size;
  title?: string;
  description?: React.ReactNode;
  icon?: React.ReactNode | boolean;
  closeable?: boolean;
  onClose?: () => void;
  actions?: React.ReactNode;
}

// Alert Component
export const Alert = forwardRef<HTMLDivElement, AlertProps>(
  (
    {
      className,
      variant = 'info',
      size = 'md',
      title,
      description,
      icon,
      closeable = false,
      onClose,
      actions,
      children,
      ...props
    },
    ref
  ) => {
    const IconComponent = iconMap[variant];
    const showIcon = icon !== false;
    const iconElement = icon === true || icon === undefined ? <IconComponent /> : icon;

    return (
      <div
        ref={ref}
        role="alert"
        className={cn(
          // Base styles
          'relative border rounded-[var(--border-radius-lg)] flex gap-3',
          
          // Variant styles
          alertVariants.variant[variant],
          
          // Size styles
          alertVariants.size[size],
          
          className
        )}
        {...props}
      >
        {/* Icon */}
        {showIcon && iconElement && (
          <div className="flex-shrink-0 mt-0.5">
            {iconElement}
          </div>
        )}
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          {title && (
            <h3 className="font-semibold mb-1 leading-tight">
              {title}
            </h3>
          )}
          
          {description && (
            <div className="leading-relaxed">
              {typeof description === 'string' ? (
                <p>{description}</p>
              ) : (
                description
              )}
            </div>
          )}
          
          {children && (
            <div className={cn('leading-relaxed', (title || description) && 'mt-2')}>
              {children}
            </div>
          )}
          
          {actions && (
            <div className="mt-3 flex gap-2">
              {actions}
            </div>
          )}
        </div>
        
        {/* Close Button */}
        {closeable && onClose && (
          <button
            type="button"
            onClick={onClose}
            className={cn(
              'flex-shrink-0 -mt-1 -mr-1 p-1 rounded-md',
              'hover:bg-black/5 focus:outline-none focus:bg-black/5',
              'transition-colors duration-200'
            )}
            aria-label="Close alert"
          >
            <CloseIcon />
          </button>
        )}
      </div>
    );
  }
);

Alert.displayName = 'Alert';

// Alert Title Component
export const AlertTitle = forwardRef<HTMLHeadingElement, React.HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn('font-semibold mb-1 leading-tight', className)}
      {...props}
    />
  )
);

AlertTitle.displayName = 'AlertTitle';

// Alert Description Component
export const AlertDescription = forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('leading-relaxed opacity-90', className)}
      {...props}
    />
  )
);

AlertDescription.displayName = 'AlertDescription';

// Alert Actions Component
export const AlertActions = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('mt-3 flex gap-2', className)}
      {...props}
    />
  )
);

AlertActions.displayName = 'AlertActions';

// Export alert utilities
export const alertUtils = {
  variants: alertVariants,
  getVariantClasses: (variant: keyof typeof alertVariants.variant) => 
    alertVariants.variant[variant],
  getSizeClasses: (size: keyof typeof alertVariants.size) => 
    alertVariants.size[size],
  iconMap,
};