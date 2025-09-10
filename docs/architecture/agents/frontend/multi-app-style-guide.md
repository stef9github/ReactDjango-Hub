# Multi-App Style Guide Architecture

## Overview

This document defines the architecture for managing styles, themes, and design consistency across multiple microservice UIs in the ReactDjango Hub platform. As our platform grows from 2 current services to potentially 6+ services, we need a scalable approach to maintain brand consistency while allowing service-specific customization.

## Design System Architecture

### Core Principles

1. **Single Source of Truth**: One design system, multiple implementations
2. **Progressive Enhancement**: Start simple, scale as needed
3. **Service Autonomy**: Services can extend but not break the core design
4. **Performance First**: Minimize style duplication and bundle size
5. **Developer Experience**: Easy to use, hard to misuse

### Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                    Design Tokens                         │
│        (Colors, Typography, Spacing, Breakpoints)        │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                 Core Component Library                    │
│         (@reactdjango-hub/ui-components)                 │
└─────────────────────────────────────────────────────────┘
                            ↓
┌──────────────┬──────────────┬──────────────┬───────────┐
│   Identity   │   Backend    │Communication │  Content  │
│   Service    │   Service    │   Service    │  Service  │
│   Styles     │   Styles     │   Styles     │  Styles   │
└──────────────┴──────────────┴──────────────┴───────────┘
```

## Implementation Strategy

### Phase 1: Design Tokens (Current)

```typescript
// packages/design-tokens/src/tokens.ts
export const tokens = {
  colors: {
    // Brand colors
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
    },
    secondary: {
      // Secondary palette
    },
    // Semantic colors
    success: {
      light: '#10b981',
      DEFAULT: '#059669',
      dark: '#047857',
    },
    warning: {
      light: '#f59e0b',
      DEFAULT: '#d97706',
      dark: '#b45309',
    },
    error: {
      light: '#ef4444',
      DEFAULT: '#dc2626',
      dark: '#b91c1c',
    },
    // Neutral colors
    gray: {
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
    },
  },
  typography: {
    fontFamily: {
      sans: ['Inter', 'system-ui', 'sans-serif'],
      mono: ['JetBrains Mono', 'monospace'],
    },
    fontSize: {
      xs: ['0.75rem', { lineHeight: '1rem' }],
      sm: ['0.875rem', { lineHeight: '1.25rem' }],
      base: ['1rem', { lineHeight: '1.5rem' }],
      lg: ['1.125rem', { lineHeight: '1.75rem' }],
      xl: ['1.25rem', { lineHeight: '1.75rem' }],
      '2xl': ['1.5rem', { lineHeight: '2rem' }],
      '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
      '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
      '5xl': ['3rem', { lineHeight: '1' }],
    },
    fontWeight: {
      thin: '100',
      light: '300',
      normal: '400',
      medium: '500',
      semibold: '600',
      bold: '700',
      extrabold: '800',
    },
  },
  spacing: {
    px: '1px',
    0: '0px',
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
    DEFAULT: '0.25rem',
    md: '0.375rem',
    lg: '0.5rem',
    xl: '0.75rem',
    '2xl': '1rem',
    '3xl': '1.5rem',
    full: '9999px',
  },
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
    inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
    none: 'none',
  },
  animation: {
    transition: {
      none: 'none',
      all: 'all 150ms cubic-bezier(0.4, 0, 0.2, 1)',
      DEFAULT: 'color 150ms cubic-bezier(0.4, 0, 0.2, 1), background-color 150ms cubic-bezier(0.4, 0, 0.2, 1), border-color 150ms cubic-bezier(0.4, 0, 0.2, 1), text-decoration-color 150ms cubic-bezier(0.4, 0, 0.2, 1), fill 150ms cubic-bezier(0.4, 0, 0.2, 1), stroke 150ms cubic-bezier(0.4, 0, 0.2, 1)',
      colors: 'color 150ms cubic-bezier(0.4, 0, 0.2, 1), background-color 150ms cubic-bezier(0.4, 0, 0.2, 1), border-color 150ms cubic-bezier(0.4, 0, 0.2, 1), text-decoration-color 150ms cubic-bezier(0.4, 0, 0.2, 1), fill 150ms cubic-bezier(0.4, 0, 0.2, 1), stroke 150ms cubic-bezier(0.4, 0, 0.2, 1)',
      opacity: 'opacity 150ms cubic-bezier(0.4, 0, 0.2, 1)',
      shadow: 'box-shadow 150ms cubic-bezier(0.4, 0, 0.2, 1)',
      transform: 'transform 150ms cubic-bezier(0.4, 0, 0.2, 1)',
    },
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
  },
  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
} as const;

// Type exports for TypeScript
export type ColorToken = keyof typeof tokens.colors;
export type SpacingToken = keyof typeof tokens.spacing;
export type TypographyToken = keyof typeof tokens.typography;
```

### Phase 2: Tailwind Configuration

```javascript
// packages/tailwind-config/tailwind.config.js
const { tokens } = require('@reactdjango-hub/design-tokens');

module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./node_modules/@reactdjango-hub/ui-components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: tokens.colors,
      fontFamily: tokens.typography.fontFamily,
      fontSize: tokens.typography.fontSize,
      fontWeight: tokens.typography.fontWeight,
      spacing: tokens.spacing,
      borderRadius: tokens.borderRadius,
      boxShadow: tokens.shadows,
      transitionProperty: tokens.animation.transition,
      transitionDuration: tokens.animation.duration,
      screens: tokens.breakpoints,
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/container-queries'),
  ],
};
```

### Phase 3: CSS-in-JS with Emotion (Alternative Approach)

```typescript
// packages/theme/src/theme.ts
import { tokens } from '@reactdjango-hub/design-tokens';
import { css } from '@emotion/react';

export const theme = {
  ...tokens,
  // Additional theme utilities
  utils: {
    focusRing: css`
      &:focus-visible {
        outline: 2px solid ${tokens.colors.primary[500]};
        outline-offset: 2px;
      }
    `,
    visuallyHidden: css`
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border-width: 0;
    `,
  },
};

// Theme provider setup
import { ThemeProvider as EmotionThemeProvider } from '@emotion/react';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  return (
    <EmotionThemeProvider theme={theme}>
      {children}
    </EmotionThemeProvider>
  );
}
```

## Service-Specific Customization

### Service Theme Extensions

```typescript
// services/identity-service/src/styles/theme.ts
import { theme as baseTheme } from '@reactdjango-hub/theme';
import { mergeDeep } from '@/utils/merge';

export const identityTheme = mergeDeep(baseTheme, {
  colors: {
    // Service-specific brand color for authentication
    auth: {
      primary: '#10b981', // Green for secure/authenticated
      secondary: '#f59e0b', // Orange for warnings
      danger: '#ef4444', // Red for errors/logout
    },
  },
  components: {
    // Component-specific overrides for identity service
    loginCard: {
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      borderRadius: baseTheme.borderRadius.xl,
    },
  },
});
```

### Service Style Isolation

```typescript
// Using CSS Modules for style isolation
// services/communication-service/src/components/ChatWidget/ChatWidget.module.css
.container {
  composes: card from '@reactdjango-hub/ui-components/Card.module.css';
  /* Service-specific styles */
  border-left: 4px solid var(--color-primary);
}

.message {
  /* Scoped to this component only */
  padding: var(--spacing-3);
  border-radius: var(--radius-md);
}

/* Using CSS custom properties for theming */
:root {
  --color-primary: #3b82f6;
  --spacing-3: 0.75rem;
  --radius-md: 0.375rem;
}
```

## Component Library Architecture

### Monorepo Structure

```
packages/
├── design-tokens/           # Core design tokens
│   ├── src/
│   │   ├── tokens.ts
│   │   └── index.ts
│   └── package.json
├── ui-components/          # Shared component library
│   ├── src/
│   │   ├── Button/
│   │   ├── Card/
│   │   ├── Form/
│   │   └── index.ts
│   └── package.json
├── theme/                  # Theme utilities and providers
│   ├── src/
│   │   ├── theme.ts
│   │   ├── ThemeProvider.tsx
│   │   └── index.ts
│   └── package.json
└── tailwind-config/        # Shared Tailwind configuration
    ├── tailwind.config.js
    └── package.json

services/
├── identity-service/       # Uses shared components
├── backend/               # Uses shared components
├── communication-service/ # Uses shared components
└── content-service/       # Uses shared components
```

### Component Library Setup

```typescript
// packages/ui-components/src/Button/Button.tsx
import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../utils/cn';

const buttonVariants = cva(
  // Base styles using design tokens via Tailwind
  'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
        // Service-specific variants can be added via className
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, loading, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={props.disabled || loading}
        {...props}
      />
    );
  }
);

Button.displayName = 'Button';
```

### Publishing Strategy

```json
// packages/ui-components/package.json
{
  "name": "@reactdjango-hub/ui-components",
  "version": "1.0.0",
  "main": "./dist/index.js",
  "module": "./dist/index.mjs",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.mjs",
      "require": "./dist/index.js",
      "types": "./dist/index.d.ts"
    },
    "./styles.css": "./dist/styles.css"
  },
  "scripts": {
    "build": "tsup src/index.ts --format cjs,esm --dts --external react",
    "dev": "tsup src/index.ts --format cjs,esm --dts --external react --watch",
    "lint": "eslint src/",
    "typecheck": "tsc --noEmit"
  },
  "peerDependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  },
  "dependencies": {
    "@reactdjango-hub/design-tokens": "workspace:*",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0"
  }
}
```

## Dark Mode Implementation

### System-Wide Dark Mode

```typescript
// packages/theme/src/DarkModeProvider.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  resolvedTheme: 'light' | 'dark';
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function DarkModeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window !== 'undefined') {
      return (localStorage.getItem('theme') as Theme) || 'system';
    }
    return 'system';
  });

  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    const root = window.document.documentElement;
    
    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
      root.classList.remove('light', 'dark');
      root.classList.add(systemTheme);
      setResolvedTheme(systemTheme);
    } else {
      root.classList.remove('light', 'dark');
      root.classList.add(theme);
      setResolvedTheme(theme);
    }
    
    localStorage.setItem('theme', theme);
  }, [theme]);

  // Listen for system theme changes
  useEffect(() => {
    if (theme !== 'system') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      const newTheme = e.matches ? 'dark' : 'light';
      document.documentElement.classList.remove('light', 'dark');
      document.documentElement.classList.add(newTheme);
      setResolvedTheme(newTheme);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a DarkModeProvider');
  }
  return context;
}
```

### Dark Mode Tailwind Configuration

```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class', // Use class-based dark mode
  theme: {
    extend: {
      colors: {
        // Define colors that work in both light and dark modes
        background: {
          DEFAULT: 'hsl(var(--background))',
          secondary: 'hsl(var(--background-secondary))',
        },
        foreground: {
          DEFAULT: 'hsl(var(--foreground))',
          muted: 'hsl(var(--foreground-muted))',
        },
      },
    },
  },
};

// CSS Variables for theming
// styles/globals.css
@layer base {
  :root {
    --background: 0 0% 100%;
    --background-secondary: 0 0% 98%;
    --foreground: 222.2 84% 4.9%;
    --foreground-muted: 215.4 16.3% 46.9%;
    
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
    
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;
  }
  
  .dark {
    --background: 222.2 84% 4.9%;
    --background-secondary: 217.2 32.6% 8%;
    --foreground: 210 40% 98%;
    --foreground-muted: 215 20.2% 65.1%;
    
    --primary: 217.2 91.2% 59.8%;
    --primary-foreground: 222.2 47.4% 11.2%;
    
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 224.3 76.3% 48%;
  }
}
```

## Performance Optimization

### Style Code Splitting

```typescript
// Dynamic style imports for code splitting
const loadServiceStyles = async (service: string) => {
  switch (service) {
    case 'identity':
      return import('./styles/identity.css');
    case 'communication':
      return import('./styles/communication.css');
    case 'content':
      return import('./styles/content.css');
    default:
      return import('./styles/default.css');
  }
};

// Component with dynamic styles
export function ServiceContainer({ service, children }: Props) {
  useEffect(() => {
    loadServiceStyles(service);
  }, [service]);
  
  return (
    <div className={`service-container service-${service}`}>
      {children}
    </div>
  );
}
```

### Critical CSS Extraction

```typescript
// vite.config.ts for critical CSS
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import criticalPlugin from 'vite-plugin-critical';

export default defineConfig({
  plugins: [
    react(),
    criticalPlugin({
      // Extract critical CSS for faster initial paint
      targets: [
        {
          entry: 'src/main.tsx',
          output: 'dist/index.html',
        },
      ],
    }),
  ],
  css: {
    modules: {
      localsConvention: 'camelCase',
      generateScopedName: '[name]__[local]___[hash:base64:5]',
    },
  },
});
```

## Migration Strategy

### From Current Tailwind-Only to Design System

1. **Phase 1: Extract Design Tokens** (Week 1)
   - Audit current Tailwind usage
   - Extract common values to design tokens
   - Create token documentation

2. **Phase 2: Create Component Library** (Week 2-3)
   - Build core components (Button, Card, Form, etc.)
   - Set up Storybook for documentation
   - Implement versioning strategy

3. **Phase 3: Service Migration** (Week 4-5)
   - Migrate identity service first
   - Update backend service UI
   - Document patterns and issues

4. **Phase 4: Optimization** (Week 6)
   - Implement CSS code splitting
   - Add performance monitoring
   - Optimize bundle sizes

## Best Practices

### Do's
- ✅ Use design tokens for all values
- ✅ Extend themes, don't override
- ✅ Use CSS logical properties for RTL support
- ✅ Implement proper CSS cascade layers
- ✅ Test components in all themes (light/dark)
- ✅ Use CSS custom properties for runtime theming
- ✅ Maintain style guide documentation

### Don'ts
- ❌ Hard-code colors or spacing values
- ❌ Use !important except for utilities
- ❌ Mix styling approaches (pick one)
- ❌ Create service-specific versions of core components
- ❌ Ignore accessibility color contrast requirements
- ❌ Bundle all styles in one file

## Tools and Resources

### Development Tools
- **Storybook**: Component documentation and testing
- **Chromatic**: Visual regression testing
- **Figma Tokens**: Sync design tokens with Figma
- **Style Dictionary**: Transform tokens to multiple formats

### Build Tools
- **PostCSS**: Process and optimize CSS
- **PurgeCSS**: Remove unused styles
- **CSSO**: Minify CSS
- **Critical**: Extract critical CSS

### Monitoring
- **Bundle Analyzer**: Monitor CSS bundle size
- **Lighthouse**: Performance and accessibility
- **CSS Stats**: Analyze CSS complexity

---

**Document maintained by**: Technical Lead Agent  
**For**: Frontend Agent, All Service Agents  
**Last updated**: December 10, 2024  
**Next review**: January 10, 2025