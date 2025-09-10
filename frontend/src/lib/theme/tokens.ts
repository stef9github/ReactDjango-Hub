/**
 * Design Tokens for Multi-App Theming
 * Centralized design system tokens that can be customized per application
 */

// Color Palette Types
export interface ColorScale {
  50: string;
  100: string;
  200: string;
  300: string;
  400: string;
  500: string;
  600: string;
  700: string;
  800: string;
  900: string;
  950: string;
}

export interface SemanticColors {
  primary: ColorScale;
  secondary: ColorScale;
  accent: ColorScale;
  neutral: ColorScale;
  success: ColorScale;
  warning: ColorScale;
  error: ColorScale;
  info: ColorScale;
}

export interface SurfaceColors {
  background: string;
  surface: string;
  'surface-variant': string;
  'surface-container': string;
  'surface-container-high': string;
  'surface-container-highest': string;
  overlay: string;
}

export interface TextColors {
  'on-background': string;
  'on-surface': string;
  'on-surface-variant': string;
  'on-primary': string;
  'on-secondary': string;
  'on-accent': string;
  'on-success': string;
  'on-warning': string;
  'on-error': string;
  'on-info': string;
}

export interface BorderColors {
  default: string;
  muted: string;
  subtle: string;
  focus: string;
  error: string;
  success: string;
  warning: string;
}

// Typography Types
export interface FontFamily {
  sans: string[];
  serif: string[];
  mono: string[];
  display: string[];
}

export interface FontSize {
  xs: string;
  sm: string;
  base: string;
  lg: string;
  xl: string;
  '2xl': string;
  '3xl': string;
  '4xl': string;
  '5xl': string;
  '6xl': string;
}

export interface FontWeight {
  thin: number;
  light: number;
  normal: number;
  medium: number;
  semibold: number;
  bold: number;
  extrabold: number;
}

export interface LineHeight {
  none: number;
  tight: number;
  normal: number;
  relaxed: number;
  loose: number;
}

// Spacing and Layout Types
export interface Spacing {
  0: string;
  px: string;
  0.5: string;
  1: string;
  1.5: string;
  2: string;
  2.5: string;
  3: string;
  3.5: string;
  4: string;
  5: string;
  6: string;
  7: string;
  8: string;
  9: string;
  10: string;
  11: string;
  12: string;
  14: string;
  16: string;
  20: string;
  24: string;
  28: string;
  32: string;
  36: string;
  40: string;
  44: string;
  48: string;
  52: string;
  56: string;
  60: string;
  64: string;
  72: string;
  80: string;
  96: string;
}

export interface BorderRadius {
  none: string;
  sm: string;
  base: string;
  md: string;
  lg: string;
  xl: string;
  '2xl': string;
  '3xl': string;
  full: string;
}

export interface BoxShadow {
  none: string;
  sm: string;
  base: string;
  md: string;
  lg: string;
  xl: string;
  '2xl': string;
  inner: string;
}

// Animation Types
export interface Duration {
  75: string;
  100: string;
  150: string;
  200: string;
  300: string;
  500: string;
  700: string;
  1000: string;
}

export interface Easing {
  'ease-in': string;
  'ease-out': string;
  'ease-in-out': string;
  linear: string;
  'ease-in-back': string;
  'ease-out-back': string;
  'ease-in-out-back': string;
}

// Design Token Structure
export interface DesignTokens {
  colors: {
    semantic: SemanticColors;
    surface: SurfaceColors;
    text: TextColors;
    border: BorderColors;
  };
  typography: {
    fontFamily: FontFamily;
    fontSize: FontSize;
    fontWeight: FontWeight;
    lineHeight: LineHeight;
  };
  spacing: Spacing;
  borderRadius: BorderRadius;
  boxShadow: BoxShadow;
  animation: {
    duration: Duration;
    easing: Easing;
  };
  breakpoints: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    '2xl': string;
  };
  zIndex: {
    auto: string;
    0: string;
    10: string;
    20: string;
    30: string;
    40: string;
    50: string;
    dropdown: string;
    modal: string;
    popover: string;
    tooltip: string;
    toast: string;
  };
}

// Default Design Tokens
export const defaultTokens: DesignTokens = {
  colors: {
    semantic: {
      primary: {
        50: '#eff6ff',
        100: '#dbeafe',
        200: '#bfdbfe',
        300: '#93c5fd',
        400: '#60a5fa',
        500: '#3b82f6',
        600: '#2563eb',
        700: '#1d4ed8',
        800: '#1e40af',
        900: '#1e3a8a',
        950: '#172554',
      },
      secondary: {
        50: '#f8fafc',
        100: '#f1f5f9',
        200: '#e2e8f0',
        300: '#cbd5e1',
        400: '#94a3b8',
        500: '#64748b',
        600: '#475569',
        700: '#334155',
        800: '#1e293b',
        900: '#0f172a',
        950: '#020617',
      },
      accent: {
        50: '#fdf4ff',
        100: '#fae8ff',
        200: '#f5d0fe',
        300: '#f0abfc',
        400: '#e879f9',
        500: '#d946ef',
        600: '#c026d3',
        700: '#a21caf',
        800: '#86198f',
        900: '#701a75',
        950: '#4a044e',
      },
      neutral: {
        50: '#fafafa',
        100: '#f4f4f5',
        200: '#e4e4e7',
        300: '#d4d4d8',
        400: '#a1a1aa',
        500: '#71717a',
        600: '#52525b',
        700: '#3f3f46',
        800: '#27272a',
        900: '#18181b',
        950: '#09090b',
      },
      success: {
        50: '#f0fdf4',
        100: '#dcfce7',
        200: '#bbf7d0',
        300: '#86efac',
        400: '#4ade80',
        500: '#22c55e',
        600: '#16a34a',
        700: '#15803d',
        800: '#166534',
        900: '#14532d',
        950: '#052e16',
      },
      warning: {
        50: '#fffbeb',
        100: '#fef3c7',
        200: '#fde68a',
        300: '#fcd34d',
        400: '#fbbf24',
        500: '#f59e0b',
        600: '#d97706',
        700: '#b45309',
        800: '#92400e',
        900: '#78350f',
        950: '#451a03',
      },
      error: {
        50: '#fef2f2',
        100: '#fee2e2',
        200: '#fecaca',
        300: '#fca5a5',
        400: '#f87171',
        500: '#ef4444',
        600: '#dc2626',
        700: '#b91c1c',
        800: '#991b1b',
        900: '#7f1d1d',
        950: '#450a0a',
      },
      info: {
        50: '#f0f9ff',
        100: '#e0f2fe',
        200: '#bae6fd',
        300: '#7dd3fc',
        400: '#38bdf8',
        500: '#0ea5e9',
        600: '#0284c7',
        700: '#0369a1',
        800: '#075985',
        900: '#0c4a6e',
        950: '#082f49',
      },
    },
    surface: {
      background: '#ffffff',
      surface: '#ffffff',
      'surface-variant': '#f8fafc',
      'surface-container': '#f1f5f9',
      'surface-container-high': '#e2e8f0',
      'surface-container-highest': '#cbd5e1',
      overlay: 'rgba(0, 0, 0, 0.5)',
    },
    text: {
      'on-background': '#0f172a',
      'on-surface': '#0f172a',
      'on-surface-variant': '#475569',
      'on-primary': '#ffffff',
      'on-secondary': '#ffffff',
      'on-accent': '#ffffff',
      'on-success': '#ffffff',
      'on-warning': '#ffffff',
      'on-error': '#ffffff',
      'on-info': '#ffffff',
    },
    border: {
      default: '#e2e8f0',
      muted: '#f1f5f9',
      subtle: '#cbd5e1',
      focus: '#3b82f6',
      error: '#ef4444',
      success: '#22c55e',
      warning: '#f59e0b',
    },
  },
  typography: {
    fontFamily: {
      sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      serif: ['ui-serif', 'Georgia', 'Cambria', 'serif'],
      mono: ['ui-monospace', 'SFMono-Regular', 'Consolas', 'monospace'],
      display: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
    },
    fontSize: {
      xs: '0.75rem',
      sm: '0.875rem',
      base: '1rem',
      lg: '1.125rem',
      xl: '1.25rem',
      '2xl': '1.5rem',
      '3xl': '1.875rem',
      '4xl': '2.25rem',
      '5xl': '3rem',
      '6xl': '3.75rem',
    },
    fontWeight: {
      thin: 100,
      light: 300,
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
      extrabold: 800,
    },
    lineHeight: {
      none: 1,
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.625,
      loose: 2,
    },
  },
  spacing: {
    0: '0px',
    px: '1px',
    0.5: '0.125rem',
    1: '0.25rem',
    1.5: '0.375rem',
    2: '0.5rem',
    2.5: '0.625rem',
    3: '0.75rem',
    3.5: '0.875rem',
    4: '1rem',
    5: '1.25rem',
    6: '1.5rem',
    7: '1.75rem',
    8: '2rem',
    9: '2.25rem',
    10: '2.5rem',
    11: '2.75rem',
    12: '3rem',
    14: '3.5rem',
    16: '4rem',
    20: '5rem',
    24: '6rem',
    28: '7rem',
    32: '8rem',
    36: '9rem',
    40: '10rem',
    44: '11rem',
    48: '12rem',
    52: '13rem',
    56: '14rem',
    60: '15rem',
    64: '16rem',
    72: '18rem',
    80: '20rem',
    96: '24rem',
  },
  borderRadius: {
    none: '0px',
    sm: '0.125rem',
    base: '0.25rem',
    md: '0.375rem',
    lg: '0.5rem',
    xl: '0.75rem',
    '2xl': '1rem',
    '3xl': '1.5rem',
    full: '9999px',
  },
  boxShadow: {
    none: 'none',
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    base: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
  },
  animation: {
    duration: {
      75: '75ms',
      100: '100ms',
      150: '150ms',
      200: '200ms',
      300: '300ms',
      500: '500ms',
      700: '700ms',
      1000: '1000ms',
    },
    easing: {
      'ease-in': 'cubic-bezier(0.4, 0, 1, 1)',
      'ease-out': 'cubic-bezier(0, 0, 0.2, 1)',
      'ease-in-out': 'cubic-bezier(0.4, 0, 0.2, 1)',
      linear: 'linear',
      'ease-in-back': 'cubic-bezier(0.6, -0.28, 0.735, 0.045)',
      'ease-out-back': 'cubic-bezier(0.175, 0.885, 0.32, 1.275)',
      'ease-in-out-back': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
    },
  },
  breakpoints: {
    xs: '320px',
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
  zIndex: {
    auto: 'auto',
    0: '0',
    10: '10',
    20: '20',
    30: '30',
    40: '40',
    50: '50',
    dropdown: '1000',
    modal: '1040',
    popover: '1030',
    tooltip: '1070',
    toast: '1080',
  },
};

// Theme variant types for different applications
export interface ThemeVariant {
  name: string;
  tokens: Partial<DesignTokens>;
}

// Medical UI Theme Variant (for medical applications)
export const medicalTheme: ThemeVariant = {
  name: 'medical',
  tokens: {
    colors: {
      semantic: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9', // Medical blue
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
          950: '#082f49',
        },
      },
    },
  },
};

// Dark mode tokens
export const darkTokens: Partial<DesignTokens> = {
  colors: {
    surface: {
      background: '#09090b',
      surface: '#18181b',
      'surface-variant': '#27272a',
      'surface-container': '#3f3f46',
      'surface-container-high': '#52525b',
      'surface-container-highest': '#71717a',
      overlay: 'rgba(0, 0, 0, 0.8)',
    },
    text: {
      'on-background': '#fafafa',
      'on-surface': '#fafafa',
      'on-surface-variant': '#a1a1aa',
      'on-primary': '#ffffff',
      'on-secondary': '#ffffff',
      'on-accent': '#ffffff',
      'on-success': '#ffffff',
      'on-warning': '#ffffff',
      'on-error': '#ffffff',
      'on-info': '#ffffff',
    },
    border: {
      default: '#3f3f46',
      muted: '#27272a',
      subtle: '#52525b',
      focus: '#60a5fa',
      error: '#f87171',
      success: '#4ade80',
      warning: '#fbbf24',
    },
  },
};