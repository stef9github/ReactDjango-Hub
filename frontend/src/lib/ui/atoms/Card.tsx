/**
 * Card Component - Foundational UI Atom
 * Flexible container component with multiple variants and compositional structure
 */

import React, { forwardRef } from 'react';
import { cn } from '@/lib/utils/cn';

// Card variant definitions
const cardVariants = {
  variant: {
    default: [
      'bg-[var(--colors-surface-surface)]',
      'border-[var(--colors-border-default)]',
      'text-[var(--colors-text-on-surface)]',
    ].join(' '),
    elevated: [
      'bg-[var(--colors-surface-surface)]',
      'border-[var(--colors-border-muted)]',
      'shadow-[var(--box-shadow-md)]',
      'text-[var(--colors-text-on-surface)]',
    ].join(' '),
    outline: [
      'bg-[var(--colors-surface-background)]',
      'border-[var(--colors-border-default)]',
      'text-[var(--colors-text-on-surface)]',
    ].join(' '),
    filled: [
      'bg-[var(--colors-surface-surface-variant)]',
      'border-[var(--colors-border-muted)]',
      'text-[var(--colors-text-on-surface)]',
    ].join(' '),
    ghost: [
      'bg-transparent',
      'border-transparent',
      'text-[var(--colors-text-on-surface)]',
    ].join(' '),
  },
  size: {
    sm: 'p-3 rounded-[var(--border-radius-base)]',
    md: 'p-4 rounded-[var(--border-radius-md)]',
    lg: 'p-6 rounded-[var(--border-radius-lg)]',
    xl: 'p-8 rounded-[var(--border-radius-xl)]',
  },
  interactive: {
    true: [
      'cursor-pointer transition-all duration-200',
      'hover:shadow-[var(--box-shadow-lg)]',
      'hover:border-[var(--colors-border-focus)]',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--colors-border-focus)]',
      'active:scale-[0.98]',
    ].join(' '),
    false: '',
  },
};

// Card Props Interface
export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: keyof typeof cardVariants.variant;
  size?: keyof typeof cardVariants.size;
  interactive?: boolean;
  asChild?: boolean;
}

// Main Card Component
export const Card = forwardRef<HTMLDivElement, CardProps>(
  (
    {
      className,
      variant = 'default',
      size = 'md',
      interactive = false,
      asChild = false,
      ...props
    },
    ref
  ) => {
    const Component = asChild ? 'div' : 'div';
    
    return (
      <Component
        ref={ref}
        className={cn(
          // Base styles
          'border border-solid',
          
          // Variant styles
          cardVariants.variant[variant],
          
          // Size styles
          cardVariants.size[size],
          
          // Interactive styles
          cardVariants.interactive[interactive],
          
          className
        )}
        tabIndex={interactive ? 0 : undefined}
        role={interactive ? 'button' : undefined}
        {...props}
      />
    );
  }
);

Card.displayName = 'Card';

// Card Header Component
export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  divider?: boolean;
}

export const CardHeader = forwardRef<HTMLDivElement, CardHeaderProps>(
  ({ className, divider = false, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'flex flex-col space-y-1.5',
        divider && 'border-b border-[var(--colors-border-default)] pb-4 mb-4',
        className
      )}
      {...props}
    />
  )
);

CardHeader.displayName = 'CardHeader';

// Card Title Component
export interface CardTitleProps extends React.HTMLAttributes<HTMLHeadingElement> {
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
}

export const CardTitle = forwardRef<HTMLHeadingElement, CardTitleProps>(
  ({ className, as: Component = 'h3', ...props }, ref) => (
    <Component
      ref={ref}
      className={cn(
        'text-lg font-semibold leading-none tracking-tight',
        'text-[var(--colors-text-on-surface)]',
        className
      )}
      {...props}
    />
  )
);

CardTitle.displayName = 'CardTitle';

// Card Description Component
export const CardDescription = forwardRef<HTMLParagraphElement, React.HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn(
        'text-sm text-[var(--colors-text-on-surface-variant)]',
        'leading-relaxed',
        className
      )}
      {...props}
    />
  )
);

CardDescription.displayName = 'CardDescription';

// Card Content Component
export const CardContent = forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div
      ref={ref}
      className={cn('flex flex-col gap-3', className)}
      {...props}
    />
  )
);

CardContent.displayName = 'CardContent';

// Card Footer Component
export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  divider?: boolean;
  justify?: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly';
}

export const CardFooter = forwardRef<HTMLDivElement, CardFooterProps>(
  ({ className, divider = false, justify = 'end', ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'flex items-center gap-2',
        divider && 'border-t border-[var(--colors-border-default)] pt-4 mt-4',
        {
          'justify-start': justify === 'start',
          'justify-center': justify === 'center',
          'justify-end': justify === 'end',
          'justify-between': justify === 'between',
          'justify-around': justify === 'around',
          'justify-evenly': justify === 'evenly',
        },
        className
      )}
      {...props}
    />
  )
);

CardFooter.displayName = 'CardFooter';

// Card Image Component
export interface CardImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  aspectRatio?: 'square' | 'video' | 'auto';
  position?: 'top' | 'bottom';
}

export const CardImage = forwardRef<HTMLImageElement, CardImageProps>(
  ({ className, aspectRatio = 'auto', position = 'top', ...props }, ref) => (
    <div
      className={cn(
        'overflow-hidden',
        position === 'top' ? '-mt-4 -mx-4 mb-4' : '-mb-4 -mx-4 mt-4',
        position === 'top' ? 'rounded-t-[var(--border-radius-md)]' : 'rounded-b-[var(--border-radius-md)]',
        aspectRatio === 'square' && 'aspect-square',
        aspectRatio === 'video' && 'aspect-video'
      )}
    >
      <img
        ref={ref}
        className={cn(
          'w-full h-full object-cover transition-transform duration-300',
          'group-hover:scale-105',
          className
        )}
        {...props}
      />
    </div>
  )
);

CardImage.displayName = 'CardImage';

// Card Actions Component (for buttons/links)
export interface CardActionsProps extends React.HTMLAttributes<HTMLDivElement> {
  orientation?: 'horizontal' | 'vertical';
  size?: 'sm' | 'md' | 'lg';
}

export const CardActions = forwardRef<HTMLDivElement, CardActionsProps>(
  ({ className, orientation = 'horizontal', size = 'md', ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'flex',
        orientation === 'horizontal' ? 'flex-row gap-2' : 'flex-col gap-1',
        {
          'text-xs': size === 'sm',
          'text-sm': size === 'md',
          'text-base': size === 'lg',
        },
        className
      )}
      {...props}
    />
  )
);

CardActions.displayName = 'CardActions';

// Specialized Card Variants

// Authentication Card (for login/register forms)
export interface AuthCardProps extends Omit<CardProps, 'variant' | 'size'> {
  title?: string;
  description?: string;
  showLogo?: boolean;
  logoSrc?: string;
  logoAlt?: string;
}

export const AuthCard = forwardRef<HTMLDivElement, AuthCardProps>(
  ({ 
    title, 
    description, 
    showLogo = false, 
    logoSrc, 
    logoAlt = 'Logo',
    children, 
    className,
    ...props 
  }, ref) => (
    <Card
      ref={ref}
      variant="elevated"
      size="lg"
      className={cn('w-full max-w-md mx-auto', className)}
      {...props}
    >
      {(showLogo || title || description) && (
        <CardHeader className="text-center">
          {showLogo && logoSrc && (
            <div className="flex justify-center mb-4">
              <img
                src={logoSrc}
                alt={logoAlt}
                className="h-12 w-auto"
              />
            </div>
          )}
          {title && (
            <CardTitle as="h1" className="text-xl">
              {title}
            </CardTitle>
          )}
          {description && (
            <CardDescription className="mt-2">
              {description}
            </CardDescription>
          )}
        </CardHeader>
      )}
      <CardContent>
        {children}
      </CardContent>
    </Card>
  )
);

AuthCard.displayName = 'AuthCard';

// Stats Card (for dashboard metrics)
export interface StatsCardProps extends Omit<CardProps, 'children'> {
  title: string;
  value: string | number;
  description?: string;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  color?: 'default' | 'success' | 'warning' | 'error' | 'info';
}

export const StatsCard = forwardRef<HTMLDivElement, StatsCardProps>(
  ({ 
    title, 
    value, 
    description, 
    icon, 
    trend, 
    trendValue,
    color = 'default',
    className,
    ...props 
  }, ref) => (
    <Card
      ref={ref}
      variant="elevated"
      className={cn('p-4', className)}
      {...props}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-[var(--colors-text-on-surface-variant)]">
            {title}
          </p>
          <p className="text-2xl font-bold text-[var(--colors-text-on-surface)] mt-1">
            {value}
          </p>
          {description && (
            <p className="text-xs text-[var(--colors-text-on-surface-variant)] mt-1">
              {description}
            </p>
          )}
          {trend && trendValue && (
            <p className={cn(
              'text-xs font-medium mt-1 flex items-center gap-1',
              trend === 'up' && 'text-[var(--colors-semantic-success-500)]',
              trend === 'down' && 'text-[var(--colors-semantic-error-500)]',
              trend === 'neutral' && 'text-[var(--colors-text-on-surface-variant)]'
            )}>
              <span>{trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'}</span>
              {trendValue}
            </p>
          )}
        </div>
        {icon && (
          <div className={cn(
            'w-12 h-12 rounded-lg flex items-center justify-center',
            color === 'success' && 'bg-[var(--colors-semantic-success-100)] text-[var(--colors-semantic-success-600)]',
            color === 'warning' && 'bg-[var(--colors-semantic-warning-100)] text-[var(--colors-semantic-warning-600)]',
            color === 'error' && 'bg-[var(--colors-semantic-error-100)] text-[var(--colors-semantic-error-600)]',
            color === 'info' && 'bg-[var(--colors-semantic-info-100)] text-[var(--colors-semantic-info-600)]',
            color === 'default' && 'bg-[var(--colors-surface-surface-variant)] text-[var(--colors-text-on-surface-variant)]'
          )}>
            {icon}
          </div>
        )}
      </div>
    </Card>
  )
);

StatsCard.displayName = 'StatsCard';

// Export card utilities
export const cardUtils = {
  variants: cardVariants,
  getVariantClasses: (variant: keyof typeof cardVariants.variant) => 
    cardVariants.variant[variant],
  getSizeClasses: (size: keyof typeof cardVariants.size) => 
    cardVariants.size[size],
};