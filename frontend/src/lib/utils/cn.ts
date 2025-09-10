/**
 * Class Name Utility
 * Combines clsx with Tailwind CSS merge for optimal class handling
 */

import { clsx, type ClassValue } from 'clsx';

// Simple Tailwind merge implementation for class deduplication
function twMerge(...inputs: ClassValue[]): string {
  const classes = clsx(inputs);
  
  // For now, we'll use a simple approach
  // In a production app, you might want to use tailwind-merge package
  return classes;
}

/**
 * Combines class names with proper handling of conditionals and deduplication
 * Usage: cn('base-class', condition && 'conditional-class', { 'object-class': condition })
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

// Variant utility for creating component variants
export function createVariants<T extends Record<string, Record<string, string>>>(
  variants: T
) {
  return (variantKey: keyof T, value: string) => {
    return variants[variantKey]?.[value] || '';
  };
}

// Compound variants utility for complex component styling
export interface CompoundVariant {
  [key: string]: string | boolean | undefined;
  className: string;
}

export function createCompoundVariants(
  compoundVariants: CompoundVariant[]
) {
  return (props: Record<string, any>) => {
    return compoundVariants
      .filter((variant) => {
        return Object.entries(variant).every(([key, value]) => {
          if (key === 'className') return true;
          return props[key] === value;
        });
      })
      .map((variant) => variant.className);
  };
}

// Responsive utility for creating responsive classes
export function responsive(
  base: string,
  sm?: string,
  md?: string,
  lg?: string,
  xl?: string
): string {
  const classes = [base];
  if (sm) classes.push(`sm:${sm}`);
  if (md) classes.push(`md:${md}`);
  if (lg) classes.push(`lg:${lg}`);
  if (xl) classes.push(`xl:${xl}`);
  return classes.join(' ');
}

// Focus ring utility
export const focusRing = 'focus:outline-none focus:ring-2 focus:ring-[var(--colors-border-focus)] focus:ring-offset-2';

// Screen reader only utility
export const srOnly = 'sr-only';

// Disabled state utility
export const disabled = 'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none';