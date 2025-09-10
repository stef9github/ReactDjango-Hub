/**
 * Theme Provider for Multi-App Theming
 * Provides theme context and CSS custom properties for dynamic theming
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { DesignTokens, ThemeVariant, defaultTokens, medicalTheme, darkTokens } from './tokens';

// Theme Context Types
export type ColorMode = 'light' | 'dark' | 'system';
export type AppTheme = 'default' | 'medical' | 'custom';

export interface ThemeConfig {
  colorMode: ColorMode;
  appTheme: AppTheme;
  customTokens?: Partial<DesignTokens>;
  customVariant?: ThemeVariant;
}

export interface ThemeContextType extends ThemeConfig {
  resolvedTheme: 'light' | 'dark';
  tokens: DesignTokens;
  setColorMode: (mode: ColorMode) => void;
  setAppTheme: (theme: AppTheme) => void;
  setCustomTokens: (tokens: Partial<DesignTokens>) => void;
  setCustomVariant: (variant: ThemeVariant) => void;
  toggleColorMode: () => void;
}

// Create context
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Theme storage key
const THEME_STORAGE_KEY = 'reactdjango-hub-theme';

// Available theme variants
const themeVariants: Record<AppTheme, ThemeVariant | null> = {
  default: null,
  medical: medicalTheme,
  custom: null, // Will be set dynamically
};

// Deep merge utility for tokens
function deepMerge<T extends Record<string, any>>(target: T, source: Partial<T>): T {
  const result = { ...target };
  
  for (const key in source) {
    if (source[key] !== undefined) {
      if (
        typeof source[key] === 'object' &&
        source[key] !== null &&
        !Array.isArray(source[key]) &&
        typeof target[key] === 'object' &&
        target[key] !== null &&
        !Array.isArray(target[key])
      ) {
        result[key] = deepMerge(target[key], source[key]);
      } else {
        result[key] = source[key] as T[Extract<keyof T, string>];
      }
    }
  }
  
  return result;
}

// Flatten tokens for CSS custom properties
function flattenTokens(tokens: DesignTokens, prefix = '--'): Record<string, string> {
  const flattened: Record<string, string> = {};
  
  function flatten(obj: any, path: string[] = []) {
    for (const [key, value] of Object.entries(obj)) {
      const newPath = [...path, key.replace(/[A-Z]/g, match => `-${match.toLowerCase()}`)];
      
      if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
        flatten(value, newPath);
      } else if (Array.isArray(value)) {
        flattened[prefix + newPath.join('-')] = value.join(', ');
      } else {
        flattened[prefix + newPath.join('-')] = String(value);
      }
    }
  }
  
  flatten(tokens);
  return flattened;
}

// Apply CSS custom properties to document
function applyCSSProperties(tokens: DesignTokens) {
  const root = document.documentElement;
  const flattened = flattenTokens(tokens);
  
  // Remove old custom properties
  Array.from(root.style).forEach(property => {
    if (property.startsWith('--')) {
      root.style.removeProperty(property);
    }
  });
  
  // Apply new custom properties
  Object.entries(flattened).forEach(([property, value]) => {
    root.style.setProperty(property, value);
  });
}

// Detect system color mode
function getSystemColorMode(): 'light' | 'dark' {
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return 'light';
}

// Resolve color mode
function resolveColorMode(mode: ColorMode): 'light' | 'dark' {
  return mode === 'system' ? getSystemColorMode() : mode;
}

// Theme Provider Props
export interface ThemeProviderProps {
  children: ReactNode;
  defaultColorMode?: ColorMode;
  defaultAppTheme?: AppTheme;
  customTokens?: Partial<DesignTokens>;
  customVariant?: ThemeVariant;
  storageKey?: string;
}

// Theme Provider Component
export function ThemeProvider({
  children,
  defaultColorMode = 'system',
  defaultAppTheme = 'default',
  customTokens,
  customVariant,
  storageKey = THEME_STORAGE_KEY,
}: ThemeProviderProps) {
  // Initialize state from localStorage or defaults
  const [themeConfig, setThemeConfig] = useState<ThemeConfig>(() => {
    if (typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem(storageKey);
        if (stored) {
          const parsed = JSON.parse(stored);
          return {
            colorMode: parsed.colorMode || defaultColorMode,
            appTheme: parsed.appTheme || defaultAppTheme,
            customTokens: parsed.customTokens || customTokens,
            customVariant: parsed.customVariant || customVariant,
          };
        }
      } catch (error) {
        console.warn('Failed to load theme from localStorage:', error);
      }
    }
    
    return {
      colorMode: defaultColorMode,
      appTheme: defaultAppTheme,
      customTokens,
      customVariant,
    };
  });
  
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>(
    resolveColorMode(themeConfig.colorMode)
  );
  
  // Compute final tokens
  const tokens = React.useMemo(() => {
    let finalTokens = { ...defaultTokens };
    
    // Apply theme variant
    const variant = themeConfig.appTheme === 'custom' 
      ? themeConfig.customVariant 
      : themeVariants[themeConfig.appTheme];
      
    if (variant?.tokens) {
      finalTokens = deepMerge(finalTokens, variant.tokens);
    }
    
    // Apply custom tokens
    if (themeConfig.customTokens) {
      finalTokens = deepMerge(finalTokens, themeConfig.customTokens);
    }
    
    // Apply dark mode tokens
    if (resolvedTheme === 'dark') {
      finalTokens = deepMerge(finalTokens, darkTokens);
    }
    
    return finalTokens;
  }, [themeConfig, resolvedTheme]);
  
  // Update CSS properties when tokens change
  useEffect(() => {
    applyCSSProperties(tokens);
  }, [tokens]);
  
  // Listen for system color mode changes
  useEffect(() => {
    if (themeConfig.colorMode !== 'system') return;
    
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      setResolvedTheme(resolveColorMode('system'));
    };
    
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [themeConfig.colorMode]);
  
  // Update resolved theme when color mode changes
  useEffect(() => {
    setResolvedTheme(resolveColorMode(themeConfig.colorMode));
  }, [themeConfig.colorMode]);
  
  // Persist theme config to localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem(storageKey, JSON.stringify(themeConfig));
      } catch (error) {
        console.warn('Failed to save theme to localStorage:', error);
      }
    }
  }, [themeConfig, storageKey]);
  
  // Add theme class to body
  useEffect(() => {
    const classes = [`theme-${resolvedTheme}`, `app-${themeConfig.appTheme}`];
    document.body.className = document.body.className
      .replace(/theme-(light|dark)/g, '')
      .replace(/app-(default|medical|custom)/g, '')
      .trim();
    document.body.classList.add(...classes);
    
    return () => {
      document.body.classList.remove(...classes);
    };
  }, [resolvedTheme, themeConfig.appTheme]);
  
  // Context value
  const contextValue: ThemeContextType = {
    ...themeConfig,
    resolvedTheme,
    tokens,
    setColorMode: (mode: ColorMode) => {
      setThemeConfig(prev => ({ ...prev, colorMode: mode }));
    },
    setAppTheme: (theme: AppTheme) => {
      setThemeConfig(prev => ({ ...prev, appTheme: theme }));
    },
    setCustomTokens: (customTokens: Partial<DesignTokens>) => {
      setThemeConfig(prev => ({ ...prev, customTokens }));
    },
    setCustomVariant: (customVariant: ThemeVariant) => {
      setThemeConfig(prev => ({ ...prev, customVariant }));
    },
    toggleColorMode: () => {
      setThemeConfig(prev => ({
        ...prev,
        colorMode: prev.colorMode === 'light' ? 'dark' : 'light',
      }));
    },
  };
  
  return <ThemeContext.Provider value={contextValue}>{children}</ThemeContext.Provider>;
}

// Custom hook to use theme
export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

// Theme class utility
export function themeClass(className: string): string {
  return `theme-${className}`;
}

// CSS custom property utility
export function cssVar(tokenPath: string): string {
  return `var(--${tokenPath.replace(/\./g, '-').replace(/[A-Z]/g, match => `-${match.toLowerCase()}`)})`;
}

// Export theme utilities
export const themeUtils = {
  cssVar,
  themeClass,
  deepMerge,
  flattenTokens,
  resolveColorMode,
  getSystemColorMode,
};