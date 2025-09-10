# Internationalization (i18n) Architecture

## Overview

This document defines the comprehensive internationalization architecture for the ReactDjango Hub platform, enabling multi-language support across all microservices. Our i18n strategy must scale from 2 languages to 20+, support RTL languages, and maintain performance while providing excellent developer and translator experiences.

## Core Requirements

### Business Requirements
- Support 5 initial languages: English, Spanish, French, German, Arabic
- Add new languages without code changes
- Support regional variations (e.g., en-US vs en-GB)
- Maintain SEO optimization for all languages
- Enable A/B testing of translations

### Technical Requirements
- Lazy load translations to minimize bundle size
- Support pluralization and gender rules
- Handle date, time, number, and currency formatting
- Support RTL/LTR layouts
- Enable translation updates without deployment
- Maintain TypeScript type safety for translation keys

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Translation CDN                         │
│                  (Translation Files)                      │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│                  i18n Service Layer                       │
│              (react-i18next + i18next)                   │
└─────────────────────────────────────────────────────────┘
                            ↓
┌──────────────┬──────────────┬──────────────┬───────────┐
│   Identity   │   Backend    │Communication │  Content  │
│   Service    │   Service    │   Service    │  Service  │
│ Translations │ Translations │ Translations │Translations│
└──────────────┴──────────────┴──────────────┴───────────┘
```

## Implementation Strategy

### Library Selection: React-i18next

```typescript
// Why react-i18next?
// 1. Industry standard with excellent ecosystem
// 2. Built-in lazy loading and code splitting
// 3. Excellent TypeScript support
// 4. Rich plugin ecosystem
// 5. Support for all i18n requirements

// packages/i18n/package.json
{
  "name": "@reactdjango-hub/i18n",
  "version": "1.0.0",
  "dependencies": {
    "i18next": "^23.7.0",
    "react-i18next": "^14.0.0",
    "i18next-http-backend": "^2.4.0",
    "i18next-browser-languagedetector": "^7.2.0",
    "i18next-icu": "^2.3.0",
    "@formatjs/intl-pluralrules": "^5.2.0",
    "@formatjs/intl-relativetimeformat": "^11.2.0",
    "@formatjs/intl-numberformat": "^8.9.0",
    "@formatjs/intl-datetimeformat": "^6.12.0"
  }
}
```

### Core i18n Configuration

```typescript
// packages/i18n/src/i18n.config.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import HttpBackend from 'i18next-http-backend';
import LanguageDetector from 'i18next-browser-languagedetector';
import ICU from 'i18next-icu';

export const supportedLanguages = {
  en: { name: 'English', dir: 'ltr', locale: 'en-US' },
  es: { name: 'Español', dir: 'ltr', locale: 'es-ES' },
  fr: { name: 'Français', dir: 'ltr', locale: 'fr-FR' },
  de: { name: 'Deutsch', dir: 'ltr', locale: 'de-DE' },
  ar: { name: 'العربية', dir: 'rtl', locale: 'ar-SA' },
  zh: { name: '中文', dir: 'ltr', locale: 'zh-CN' },
  ja: { name: '日本語', dir: 'ltr', locale: 'ja-JP' },
  pt: { name: 'Português', dir: 'ltr', locale: 'pt-BR' },
} as const;

export type SupportedLanguage = keyof typeof supportedLanguages;

const i18nConfig = {
  fallbackLng: 'en',
  debug: import.meta.env.DEV,
  
  // Namespaces for organizing translations
  ns: [
    'common',      // Shared translations
    'auth',        // Authentication related
    'dashboard',   // Dashboard specific
    'errors',      // Error messages
    'validation',  // Form validation
  ],
  defaultNS: 'common',
  
  interpolation: {
    escapeValue: false, // React already escapes values
    format: (value: any, format?: string, lng?: string) => {
      // Custom formatting for dates, numbers, etc.
      if (format === 'intlDate') {
        return new Intl.DateTimeFormat(lng).format(value);
      }
      if (format === 'intlNumber') {
        return new Intl.NumberFormat(lng).format(value);
      }
      if (format === 'intlCurrency') {
        const [amount, currency] = value;
        return new Intl.NumberFormat(lng, {
          style: 'currency',
          currency,
        }).format(amount);
      }
      return value;
    },
  },
  
  // Language detection options
  detection: {
    order: ['querystring', 'cookie', 'localStorage', 'navigator', 'htmlTag'],
    caches: ['localStorage', 'cookie'],
    cookieOptions: {
      sameSite: 'strict',
      secure: true,
    },
  },
  
  // Backend configuration for loading translations
  backend: {
    loadPath: `${import.meta.env.VITE_CDN_URL}/locales/{{lng}}/{{ns}}.json`,
    crossDomain: true,
    withCredentials: false,
    requestOptions: {
      cache: 'default',
    },
  },
  
  // React specific options
  react: {
    useSuspense: true,
    bindI18n: 'languageChanged loaded',
    bindI18nStore: 'added removed',
    transEmptyNodeValue: '',
    transSupportBasicHtmlNodes: true,
    transKeepBasicHtmlNodesFor: ['br', 'strong', 'i', 'p'],
  },
  
  // Resource loading options
  load: 'languageOnly', // ignore region-specific on load
  preload: ['en'], // Preload default language
  
  // Cache options
  cache: {
    enabled: true,
    expirationTime: 7 * 24 * 60 * 60 * 1000, // 7 days
  },
};

i18n
  .use(HttpBackend)
  .use(LanguageDetector)
  .use(ICU)
  .use(initReactI18next)
  .init(i18nConfig);

export default i18n;
```

## Translation File Organization

### Directory Structure

```
locales/
├── en/
│   ├── common.json          # Shared translations
│   ├── auth.json            # Authentication
│   ├── dashboard.json       # Dashboard
│   ├── errors.json          # Error messages
│   └── validation.json      # Form validation
├── es/
│   ├── common.json
│   ├── auth.json
│   ├── dashboard.json
│   ├── errors.json
│   └── validation.json
├── ar/
│   └── ... (same structure)
└── index.ts                 # Type definitions
```

### Translation File Format

```json
// locales/en/common.json
{
  "app": {
    "name": "ReactDjango Hub",
    "tagline": "Enterprise SaaS Platform",
    "copyright": "© {year} ReactDjango Hub. All rights reserved."
  },
  "navigation": {
    "home": "Home",
    "dashboard": "Dashboard",
    "users": "Users",
    "settings": "Settings",
    "logout": "Logout"
  },
  "actions": {
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "edit": "Edit",
    "create": "Create",
    "search": "Search",
    "filter": "Filter",
    "export": "Export",
    "import": "Import",
    "confirm": "Confirm",
    "back": "Back",
    "next": "Next",
    "previous": "Previous",
    "loading": "Loading...",
    "submit": "Submit"
  },
  "status": {
    "active": "Active",
    "inactive": "Inactive",
    "pending": "Pending",
    "approved": "Approved",
    "rejected": "Rejected",
    "draft": "Draft",
    "published": "Published"
  },
  "messages": {
    "success": {
      "saved": "Successfully saved",
      "deleted": "Successfully deleted",
      "updated": "Successfully updated",
      "created": "Successfully created"
    },
    "error": {
      "generic": "An error occurred. Please try again.",
      "network": "Network error. Please check your connection.",
      "unauthorized": "You are not authorized to perform this action.",
      "notFound": "The requested resource was not found."
    },
    "confirm": {
      "delete": "Are you sure you want to delete this item?",
      "unsavedChanges": "You have unsaved changes. Are you sure you want to leave?"
    }
  },
  "plurals": {
    "items": "{count, plural, =0 {No items} one {# item} other {# items}}",
    "users": "{count, plural, =0 {No users} one {# user} other {# users}}",
    "days": "{count, plural, =0 {Today} one {# day ago} other {# days ago}}"
  },
  "formatting": {
    "date": {
      "short": "{date, date, short}",
      "medium": "{date, date, medium}",
      "long": "{date, date, long}",
      "full": "{date, date, full}"
    },
    "time": {
      "short": "{time, time, short}",
      "medium": "{time, time, medium}"
    },
    "number": {
      "decimal": "{value, number}",
      "percent": "{value, number, percent}",
      "currency": "{value, number, currency}"
    }
  }
}
```

### Complex Translation Examples

```json
// locales/en/auth.json
{
  "login": {
    "title": "Sign In",
    "subtitle": "Welcome back to {appName}",
    "email": {
      "label": "Email Address",
      "placeholder": "Enter your email",
      "error": {
        "required": "Email is required",
        "invalid": "Please enter a valid email address"
      }
    },
    "password": {
      "label": "Password",
      "placeholder": "Enter your password",
      "error": {
        "required": "Password is required",
        "minLength": "Password must be at least {min} characters",
        "maxLength": "Password must be less than {max} characters"
      }
    },
    "rememberMe": "Remember me",
    "forgotPassword": "Forgot your password?",
    "submit": "Sign In",
    "divider": "Or continue with",
    "providers": {
      "google": "Sign in with Google",
      "github": "Sign in with GitHub",
      "microsoft": "Sign in with Microsoft"
    },
    "register": {
      "prompt": "Don't have an account?",
      "link": "Sign up"
    },
    "mfa": {
      "title": "Two-Factor Authentication",
      "subtitle": "Enter the code from your authenticator app",
      "code": {
        "label": "Verification Code",
        "placeholder": "000000",
        "error": {
          "required": "Code is required",
          "invalid": "Invalid code format",
          "expired": "Code has expired"
        }
      },
      "backup": {
        "link": "Use backup code",
        "title": "Enter Backup Code",
        "placeholder": "Enter your backup code"
      }
    }
  },
  "register": {
    "title": "Create Account",
    "subtitle": "Join {count, plural, =0 {our platform} other {# other users}}",
    "terms": {
      "text": "By signing up, you agree to our",
      "termsLink": "Terms of Service",
      "and": "and",
      "privacyLink": "Privacy Policy"
    },
    "passwordStrength": {
      "weak": "Weak",
      "medium": "Medium",
      "strong": "Strong",
      "veryStrong": "Very Strong",
      "requirements": {
        "length": "At least {min} characters",
        "uppercase": "One uppercase letter",
        "lowercase": "One lowercase letter",
        "number": "One number",
        "special": "One special character"
      }
    }
  },
  "logout": {
    "title": "Sign Out",
    "message": "Are you sure you want to sign out?",
    "confirm": "Sign Out",
    "cancel": "Cancel"
  },
  "passwordReset": {
    "request": {
      "title": "Reset Password",
      "subtitle": "Enter your email to receive reset instructions",
      "submit": "Send Reset Link",
      "success": "Check your email for reset instructions",
      "backToLogin": "Back to Sign In"
    },
    "reset": {
      "title": "Create New Password",
      "subtitle": "Choose a strong password for your account",
      "submit": "Reset Password",
      "success": "Password successfully reset",
      "error": "Reset link is invalid or expired"
    }
  }
}
```

## TypeScript Integration

### Type-Safe Translations

```typescript
// packages/i18n/src/types.ts
import type common from '../locales/en/common.json';
import type auth from '../locales/en/auth.json';
import type dashboard from '../locales/en/dashboard.json';
import type errors from '../locales/en/errors.json';
import type validation from '../locales/en/validation.json';

// Define resource type
export interface Resources {
  common: typeof common;
  auth: typeof auth;
  dashboard: typeof dashboard;
  errors: typeof errors;
  validation: typeof validation;
}

// Extend react-i18next types
declare module 'react-i18next' {
  interface CustomTypeOptions {
    defaultNS: 'common';
    resources: Resources;
  }
}

// Helper types for translation keys
export type TranslationKey<NS extends keyof Resources> = DotNotation<Resources[NS]>;

// Dot notation type for nested keys
type DotNotation<T, P extends string = ''> = T extends object
  ? {
      [K in keyof T]: K extends string
        ? T[K] extends object
          ? DotNotation<T[K], P extends '' ? K : `${P}.${K}`>
          : P extends ''
          ? K
          : `${P}.${K}`
        : never;
    }[keyof T]
  : never;
```

### Type-Safe Hook Usage

```typescript
// packages/i18n/src/hooks/useTypedTranslation.ts
import { useTranslation, UseTranslationOptions } from 'react-i18next';
import type { Resources } from '../types';

export function useTypedTranslation<NS extends keyof Resources = 'common'>(
  ns?: NS,
  options?: UseTranslationOptions<NS>
) {
  const { t, i18n, ready } = useTranslation(ns, options);
  
  return {
    t: t as (key: TranslationKey<NS>, options?: any) => string,
    i18n,
    ready,
  };
}

// Usage in components
export function LoginForm() {
  const { t } = useTypedTranslation('auth');
  
  return (
    <form>
      <h1>{t('login.title')}</h1>
      {/* TypeScript will autocomplete and type-check translation keys */}
      <input placeholder={t('login.email.placeholder')} />
    </form>
  );
}
```

## Component Implementation Patterns

### Basic Translation Component

```typescript
// components/TranslatedText.tsx
import React from 'react';
import { Trans, useTranslation } from 'react-i18next';

interface TranslatedTextProps {
  i18nKey: string;
  values?: Record<string, any>;
  ns?: string;
  components?: Record<string, React.ReactElement>;
}

export function TranslatedText({ 
  i18nKey, 
  values, 
  ns = 'common',
  components 
}: TranslatedTextProps) {
  const { t } = useTranslation(ns);
  
  if (components) {
    return (
      <Trans 
        i18nKey={i18nKey} 
        values={values}
        components={components}
        ns={ns}
      />
    );
  }
  
  return <>{t(i18nKey, values)}</>;
}

// Usage with interpolation
<TranslatedText 
  i18nKey="app.copyright" 
  values={{ year: new Date().getFullYear() }}
/>

// Usage with components
<TranslatedText 
  i18nKey="register.terms.text"
  components={{
    termsLink: <Link to="/terms">{t('register.terms.termsLink')}</Link>,
    privacyLink: <Link to="/privacy">{t('register.terms.privacyLink')}</Link>,
  }}
/>
```

### Language Switcher Component

```typescript
// components/LanguageSwitcher.tsx
import React from 'react';
import { useTranslation } from 'react-i18next';
import { supportedLanguages, type SupportedLanguage } from '@/i18n/config';
import { Select } from '@/components/ui/Select';
import { Globe } from 'lucide-react';

export function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const currentLanguage = i18n.language as SupportedLanguage;
  
  const handleLanguageChange = async (lng: SupportedLanguage) => {
    await i18n.changeLanguage(lng);
    
    // Update document direction for RTL languages
    document.documentElement.dir = supportedLanguages[lng].dir;
    
    // Update HTML lang attribute
    document.documentElement.lang = lng;
    
    // Store preference
    localStorage.setItem('preferredLanguage', lng);
    
    // Optionally update user preference on backend
    if (user?.id) {
      await updateUserPreference({ language: lng });
    }
  };
  
  const options = Object.entries(supportedLanguages).map(([code, config]) => ({
    value: code,
    label: config.name,
    icon: <Globe className="w-4 h-4" />,
  }));
  
  return (
    <Select
      value={currentLanguage}
      onChange={handleLanguageChange}
      options={options}
      className="min-w-[150px]"
      aria-label="Select language"
    />
  );
}
```

### Form with Validation Messages

```typescript
// components/UserForm.tsx
import React from 'react';
import { useForm } from 'react-hook-form';
import { useTranslation } from 'react-i18next';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

export function UserForm() {
  const { t } = useTranslation(['validation', 'common']);
  
  // Create schema with translated messages
  const schema = z.object({
    email: z
      .string()
      .min(1, t('validation:email.required'))
      .email(t('validation:email.invalid')),
    password: z
      .string()
      .min(1, t('validation:password.required'))
      .min(8, t('validation:password.minLength', { min: 8 }))
      .max(100, t('validation:password.maxLength', { max: 100 })),
    age: z
      .number()
      .min(18, t('validation:age.minimum', { min: 18 }))
      .max(120, t('validation:age.maximum', { max: 120 })),
  });
  
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
  });
  
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label>{t('common:fields.email')}</label>
        <input {...register('email')} />
        {errors.email && (
          <span className="error">{errors.email.message}</span>
        )}
      </div>
      {/* More fields... */}
    </form>
  );
}
```

## Date and Number Formatting

### Locale-Aware Formatters

```typescript
// utils/formatters.ts
import { useTranslation } from 'react-i18next';

export function useFormatters() {
  const { i18n } = useTranslation();
  const locale = i18n.language;
  
  const formatDate = (date: Date | string, options?: Intl.DateTimeFormatOptions) => {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return new Intl.DateTimeFormat(locale, options).format(dateObj);
  };
  
  const formatTime = (date: Date | string, options?: Intl.DateTimeFormatOptions) => {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    return new Intl.DateTimeFormat(locale, {
      hour: '2-digit',
      minute: '2-digit',
      ...options,
    }).format(dateObj);
  };
  
  const formatNumber = (value: number, options?: Intl.NumberFormatOptions) => {
    return new Intl.NumberFormat(locale, options).format(value);
  };
  
  const formatCurrency = (
    amount: number,
    currency: string,
    options?: Intl.NumberFormatOptions
  ) => {
    return new Intl.NumberFormat(locale, {
      style: 'currency',
      currency,
      ...options,
    }).format(amount);
  };
  
  const formatPercent = (value: number, options?: Intl.NumberFormatOptions) => {
    return new Intl.NumberFormat(locale, {
      style: 'percent',
      ...options,
    }).format(value);
  };
  
  const formatRelativeTime = (date: Date | string) => {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' });
    
    const diff = dateObj.getTime() - Date.now();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (Math.abs(days) > 0) return rtf.format(days, 'day');
    if (Math.abs(hours) > 0) return rtf.format(hours, 'hour');
    if (Math.abs(minutes) > 0) return rtf.format(minutes, 'minute');
    return rtf.format(seconds, 'second');
  };
  
  const formatList = (items: string[], type: 'conjunction' | 'disjunction' = 'conjunction') => {
    return new Intl.ListFormat(locale, { type }).format(items);
  };
  
  return {
    formatDate,
    formatTime,
    formatNumber,
    formatCurrency,
    formatPercent,
    formatRelativeTime,
    formatList,
  };
}

// Usage in components
export function PriceDisplay({ amount, currency }: Props) {
  const { formatCurrency } = useFormatters();
  
  return <span>{formatCurrency(amount, currency)}</span>;
}

export function DateDisplay({ date }: Props) {
  const { formatDate, formatRelativeTime } = useFormatters();
  const [showRelative, setShowRelative] = useState(true);
  
  return (
    <time dateTime={date.toISOString()} title={formatDate(date, { dateStyle: 'full' })}>
      {showRelative ? formatRelativeTime(date) : formatDate(date)}
    </time>
  );
}
```

## Pluralization and Gender

### ICU Message Format

```typescript
// Using ICU format for complex messages
const messages = {
  // Pluralization
  itemCount: '{count, plural, =0 {No items} one {One item} other {# items}}',
  
  // Select (for gender)
  welcome: '{gender, select, male {Welcome Mr. {name}} female {Welcome Ms. {name}} other {Welcome {name}}}',
  
  // Nested pluralization with select
  taskStatus: `{gender, select,
    male {{count, plural,
      =0 {He has no tasks}
      one {He has one task}
      other {He has # tasks}
    }}
    female {{count, plural,
      =0 {She has no tasks}
      one {She has one task}
      other {She has # tasks}
    }}
    other {{count, plural,
      =0 {They have no tasks}
      one {They have one task}
      other {They have # tasks}
    }}
  }`,
  
  // Ordinal numbers
  position: '{position, selectordinal, one {#st} two {#nd} few {#rd} other {#th}} place',
  
  // Date ranges
  dateRange: '{start, date, medium} - {end, date, medium}',
  
  // Complex example with multiple variables
  meetingReminder: `{gender, select,
    male {Hi {name}, you have a meeting with {otherName} {when, select,
      today {today at {time, time, short}}
      tomorrow {tomorrow at {time, time, short}}
      other {on {date, date, medium} at {time, time, short}}
    }}
    female {Hi {name}, you have a meeting with {otherName} {when, select,
      today {today at {time, time, short}}
      tomorrow {tomorrow at {time, time, short}}
      other {on {date, date, medium} at {time, time, short}}
    }}
    other {Hi {name}, you have a meeting with {otherName} {when, select,
      today {today at {time, time, short}}
      tomorrow {tomorrow at {time, time, short}}
      other {on {date, date, medium} at {time, time, short}}
    }}
  }`,
};

// Usage
t('itemCount', { count: 5 }); // "5 items"
t('welcome', { gender: 'female', name: 'Sarah' }); // "Welcome Ms. Sarah"
t('taskStatus', { gender: 'male', count: 3 }); // "He has 3 tasks"
```

## Performance Optimization

### Lazy Loading Translations

```typescript
// Lazy load namespaces only when needed
import { useTranslation } from 'react-i18next';

export function AdvancedSettingsPage() {
  // Load 'advanced' namespace only for this page
  const { t, ready } = useTranslation('advanced', {
    useSuspense: false,
  });
  
  useEffect(() => {
    // Ensure namespace is loaded
    i18n.loadNamespaces(['advanced']);
  }, []);
  
  if (!ready) {
    return <LoadingSpinner />;
  }
  
  return <div>{t('advanced:title')}</div>;
}
```

### Translation Caching Strategy

```typescript
// Service worker for caching translations
// sw.js
self.addEventListener('fetch', (event) => {
  if (event.request.url.includes('/locales/')) {
    event.respondWith(
      caches.match(event.request).then((response) => {
        if (response) {
          // Return cached translation
          return response;
        }
        
        // Fetch and cache new translation
        return fetch(event.request).then((response) => {
          return caches.open('translations-v1').then((cache) => {
            cache.put(event.request, response.clone());
            return response;
          });
        });
      })
    );
  }
});
```

## Testing i18n

### Component Testing

```typescript
// __tests__/i18n.test.tsx
import { render, screen } from '@testing-library/react';
import { I18nextProvider } from 'react-i18next';
import i18n from '@/i18n/test-config';

const renderWithI18n = (ui: React.ReactElement, locale = 'en') => {
  i18n.changeLanguage(locale);
  return render(
    <I18nextProvider i18n={i18n}>
      {ui}
    </I18nextProvider>
  );
};

describe('LoginForm i18n', () => {
  it('renders in English', () => {
    renderWithI18n(<LoginForm />);
    expect(screen.getByText('Sign In')).toBeInTheDocument();
  });
  
  it('renders in Spanish', () => {
    renderWithI18n(<LoginForm />, 'es');
    expect(screen.getByText('Iniciar Sesión')).toBeInTheDocument();
  });
  
  it('renders in Arabic with RTL', () => {
    renderWithI18n(<LoginForm />, 'ar');
    expect(document.documentElement.dir).toBe('rtl');
    expect(screen.getByText('تسجيل الدخول')).toBeInTheDocument();
  });
});
```

## Migration Strategy

### Phase 1: Setup (Week 1)
1. Install and configure react-i18next
2. Set up translation file structure
3. Configure TypeScript types
4. Implement language detection

### Phase 2: Core Translations (Week 2)
1. Extract all hardcoded strings
2. Create English translations
3. Implement core components (LanguageSwitcher, etc.)
4. Set up translation management workflow

### Phase 3: Additional Languages (Week 3)
1. Add Spanish and French translations
2. Implement RTL support for Arabic
3. Test pluralization and formatting
4. Set up translation validation

### Phase 4: Optimization (Week 4)
1. Implement lazy loading
2. Set up CDN delivery
3. Add caching strategies
4. Performance monitoring

## Best Practices

### Do's
- ✅ Use namespaces to organize translations
- ✅ Implement proper pluralization rules
- ✅ Test all languages including RTL
- ✅ Use ICU format for complex messages
- ✅ Lazy load translations when possible
- ✅ Provide context for translators
- ✅ Use semantic translation keys

### Don'ts
- ❌ Hardcode strings in components
- ❌ Concatenate translated strings
- ❌ Assume text length is consistent
- ❌ Ignore cultural differences
- ❌ Use flags for languages
- ❌ Mix languages in one message

---

**Document maintained by**: Technical Lead Agent  
**For**: Frontend Agent, All Service Agents  
**Last updated**: December 10, 2024  
**Next review**: January 10, 2025