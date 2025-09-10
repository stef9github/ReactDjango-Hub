/**
 * Theme System Barrel Export
 * Centralized exports for the entire theme system
 */

// Core theme system
export {
  ThemeProvider,
  useTheme,
  themeClass,
  cssVar,
  themeUtils,
} from './theme-provider';

// Design tokens and types
export {
  defaultTokens,
  medicalTheme,
  darkTokens,
} from './tokens';

export type {
  DesignTokens,
  ThemeVariant,
  ColorScale,
  SemanticColors,
  SurfaceColors,
  TextColors,
  BorderColors,
  FontFamily,
  FontSize,
  FontWeight,
  LineHeight,
  Spacing,
  BorderRadius,
  BoxShadow,
  Duration,
  Easing,
} from './tokens';

export type {
  ColorMode,
  AppTheme,
  ThemeConfig,
  ThemeContextType,
  ThemeProviderProps,
} from './theme-provider';

// Theme preset configurations for different applications
export const themePresets = {
  // Healthcare/Medical application theme
  healthcare: {
    colorMode: 'light' as const,
    appTheme: 'medical' as const,
  },
  
  // Enterprise/Business application theme
  enterprise: {
    colorMode: 'system' as const,
    appTheme: 'default' as const,
  },
  
  // Developer/Technical application theme
  developer: {
    colorMode: 'dark' as const,
    appTheme: 'default' as const,
  },
} as const;

// Utility functions for theme integration
export const createThemeConfig = (
  preset: keyof typeof themePresets,
  overrides?: Partial<ThemeConfig>
) => ({
  ...themePresets[preset],
  ...overrides,
});

// CSS utility classes that work with our theme system
export const themeClasses = {
  // Color utilities
  surface: 'bg-[var(--colors-surface-background)]',
  surfaceVariant: 'bg-[var(--colors-surface-surface-variant)]',
  surfaceContainer: 'bg-[var(--colors-surface-surface-container)]',
  
  // Text utilities
  textPrimary: 'text-[var(--colors-text-on-background)]',
  textSecondary: 'text-[var(--colors-text-on-surface-variant)]',
  textOnPrimary: 'text-[var(--colors-text-on-primary)]',
  
  // Border utilities
  border: 'border-[var(--colors-border-default)]',
  borderMuted: 'border-[var(--colors-border-muted)]',
  borderFocus: 'border-[var(--colors-border-focus)]',
  
  // Shadow utilities
  shadow: 'shadow-[var(--box-shadow-base)]',
  shadowMd: 'shadow-[var(--box-shadow-md)]',
  shadowLg: 'shadow-[var(--box-shadow-lg)]',
  
  // Radius utilities
  rounded: 'rounded-[var(--border-radius-base)]',
  roundedMd: 'rounded-[var(--border-radius-md)]',
  roundedLg: 'rounded-[var(--border-radius-lg)]',
} as const;