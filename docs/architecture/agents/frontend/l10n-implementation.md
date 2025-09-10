# Localization (l10n) Implementation Guide

## Overview

This document provides practical implementation patterns for localization in the ReactDjango Hub platform. While i18n provides the framework for internationalization, l10n focuses on adapting the application for specific locales, including cultural preferences, formatting conventions, and regional requirements.

## Localization Scope

### What Needs Localization

1. **Content Presentation**
   - Date and time formats
   - Number and currency formats
   - Address formats
   - Phone number formats
   - Name order (first/last vs last/first)

2. **UI Adaptations**
   - Text direction (RTL/LTR)
   - Layout adjustments for text expansion
   - Icon directions (arrows, etc.)
   - Color meanings (cultural significance)

3. **Business Logic**
   - Tax calculations
   - Shipping options
   - Payment methods
   - Legal requirements
   - Privacy regulations (GDPR, CCPA, etc.)

4. **Media Content**
   - Images with text
   - Videos with subtitles
   - Audio content
   - PDFs and documents
   - Marketing materials

## Implementation Patterns

### 1. Locale Context Provider

```typescript
// contexts/LocaleContext.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

export interface Locale {
  code: string;              // e.g., 'en-US'
  language: string;          // e.g., 'en'
  region: string;            // e.g., 'US'
  direction: 'ltr' | 'rtl';
  firstDayOfWeek: 0 | 1 | 6; // Sunday, Monday, or Saturday
  dateFormat: string;        // e.g., 'MM/DD/YYYY'
  timeFormat: '12h' | '24h';
  numberFormat: {
    decimal: string;         // e.g., '.'
    thousands: string;       // e.g., ','
  };
  currency: {
    code: string;           // e.g., 'USD'
    symbol: string;         // e.g., '$'
    position: 'before' | 'after';
  };
  phoneFormat: string;      // e.g., '+1 (XXX) XXX-XXXX'
  addressFormat: string[];  // Order of address fields
}

const localeConfigs: Record<string, Locale> = {
  'en-US': {
    code: 'en-US',
    language: 'en',
    region: 'US',
    direction: 'ltr',
    firstDayOfWeek: 0,
    dateFormat: 'MM/DD/YYYY',
    timeFormat: '12h',
    numberFormat: {
      decimal: '.',
      thousands: ',',
    },
    currency: {
      code: 'USD',
      symbol: '$',
      position: 'before',
    },
    phoneFormat: '+1 (XXX) XXX-XXXX',
    addressFormat: ['street', 'city', 'state', 'zip', 'country'],
  },
  'en-GB': {
    code: 'en-GB',
    language: 'en',
    region: 'GB',
    direction: 'ltr',
    firstDayOfWeek: 1,
    dateFormat: 'DD/MM/YYYY',
    timeFormat: '24h',
    numberFormat: {
      decimal: '.',
      thousands: ',',
    },
    currency: {
      code: 'GBP',
      symbol: '£',
      position: 'before',
    },
    phoneFormat: '+44 XXXX XXXXXX',
    addressFormat: ['street', 'city', 'county', 'postcode', 'country'],
  },
  'ar-SA': {
    code: 'ar-SA',
    language: 'ar',
    region: 'SA',
    direction: 'rtl',
    firstDayOfWeek: 6,
    dateFormat: 'DD/MM/YYYY',
    timeFormat: '12h',
    numberFormat: {
      decimal: '.',
      thousands: ',',
    },
    currency: {
      code: 'SAR',
      symbol: 'ر.س',
      position: 'after',
    },
    phoneFormat: '+966 XX XXX XXXX',
    addressFormat: ['street', 'district', 'city', 'postalCode', 'country'],
  },
  'ja-JP': {
    code: 'ja-JP',
    language: 'ja',
    region: 'JP',
    direction: 'ltr',
    firstDayOfWeek: 0,
    dateFormat: 'YYYY/MM/DD',
    timeFormat: '24h',
    numberFormat: {
      decimal: '.',
      thousands: ',',
    },
    currency: {
      code: 'JPY',
      symbol: '¥',
      position: 'before',
    },
    phoneFormat: '+81 XX-XXXX-XXXX',
    addressFormat: ['postalCode', 'prefecture', 'city', 'street'],
  },
  'de-DE': {
    code: 'de-DE',
    language: 'de',
    region: 'DE',
    direction: 'ltr',
    firstDayOfWeek: 1,
    dateFormat: 'DD.MM.YYYY',
    timeFormat: '24h',
    numberFormat: {
      decimal: ',',
      thousands: '.',
    },
    currency: {
      code: 'EUR',
      symbol: '€',
      position: 'after',
    },
    phoneFormat: '+49 XXX XXXXXXXX',
    addressFormat: ['street', 'postalCode', 'city', 'country'],
  },
};

interface LocaleContextType {
  locale: Locale;
  setLocale: (code: string) => void;
  formatters: ReturnType<typeof createFormatters>;
}

const LocaleContext = createContext<LocaleContextType | undefined>(undefined);

function createFormatters(locale: Locale) {
  return {
    formatDate: (date: Date, style: 'short' | 'medium' | 'long' | 'full' = 'medium') => {
      return new Intl.DateTimeFormat(locale.code, {
        dateStyle: style,
      }).format(date);
    },
    
    formatTime: (date: Date, includeSeconds = false) => {
      return new Intl.DateTimeFormat(locale.code, {
        hour: '2-digit',
        minute: '2-digit',
        second: includeSeconds ? '2-digit' : undefined,
        hour12: locale.timeFormat === '12h',
      }).format(date);
    },
    
    formatDateTime: (date: Date) => {
      return new Intl.DateTimeFormat(locale.code, {
        dateStyle: 'medium',
        timeStyle: 'short',
      }).format(date);
    },
    
    formatNumber: (value: number, decimals?: number) => {
      return new Intl.NumberFormat(locale.code, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }).format(value);
    },
    
    formatCurrency: (amount: number, currency?: string) => {
      return new Intl.NumberFormat(locale.code, {
        style: 'currency',
        currency: currency || locale.currency.code,
      }).format(amount);
    },
    
    formatPercent: (value: number, decimals = 0) => {
      return new Intl.NumberFormat(locale.code, {
        style: 'percent',
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      }).format(value);
    },
    
    formatPhone: (phone: string) => {
      // Simple phone formatting based on locale pattern
      const digits = phone.replace(/\D/g, '');
      const pattern = locale.phoneFormat;
      let formatted = '';
      let digitIndex = 0;
      
      for (const char of pattern) {
        if (char === 'X' && digitIndex < digits.length) {
          formatted += digits[digitIndex++];
        } else if (char !== 'X') {
          formatted += char;
        }
      }
      
      return formatted;
    },
    
    formatFileSize: (bytes: number) => {
      const units = ['B', 'KB', 'MB', 'GB', 'TB'];
      let size = bytes;
      let unitIndex = 0;
      
      while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
      }
      
      return `${new Intl.NumberFormat(locale.code, {
        maximumFractionDigits: 2,
      }).format(size)} ${units[unitIndex]}`;
    },
  };
}

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const { i18n } = useTranslation();
  const [locale, setLocaleState] = useState<Locale>(() => {
    const code = `${i18n.language}-${i18n.language === 'en' ? 'US' : i18n.language.toUpperCase()}`;
    return localeConfigs[code] || localeConfigs['en-US'];
  });
  
  const setLocale = (code: string) => {
    const newLocale = localeConfigs[code];
    if (newLocale) {
      setLocaleState(newLocale);
      i18n.changeLanguage(newLocale.language);
      
      // Update document direction
      document.documentElement.dir = newLocale.direction;
      document.documentElement.lang = newLocale.code;
      
      // Store preference
      localStorage.setItem('locale', code);
    }
  };
  
  useEffect(() => {
    // Apply locale-specific CSS classes
    document.documentElement.classList.remove('ltr', 'rtl');
    document.documentElement.classList.add(locale.direction);
    
    // Apply locale-specific data attributes
    document.documentElement.setAttribute('data-locale', locale.code);
    document.documentElement.setAttribute('data-region', locale.region);
  }, [locale]);
  
  const formatters = createFormatters(locale);
  
  return (
    <LocaleContext.Provider value={{ locale, setLocale, formatters }}>
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale() {
  const context = useContext(LocaleContext);
  if (!context) {
    throw new Error('useLocale must be used within LocaleProvider');
  }
  return context;
}
```

### 2. RTL/LTR Support

```typescript
// components/DirectionalLayout.tsx
import React from 'react';
import { useLocale } from '@/contexts/LocaleContext';
import { cn } from '@/utils/cn';

interface DirectionalLayoutProps {
  children: React.ReactNode;
  className?: string;
}

export function DirectionalLayout({ children, className }: DirectionalLayoutProps) {
  const { locale } = useLocale();
  
  return (
    <div
      className={cn(
        'transition-all duration-300',
        locale.direction === 'rtl' ? 'rtl-layout' : 'ltr-layout',
        className
      )}
    >
      {children}
    </div>
  );
}

// styles/directional.css
.rtl-layout {
  direction: rtl;
  text-align: right;
}

.ltr-layout {
  direction: ltr;
  text-align: left;
}

/* Use logical properties for automatic RTL/LTR support */
.card {
  padding-inline-start: 1rem; /* Replaces padding-left */
  padding-inline-end: 1rem;   /* Replaces padding-right */
  margin-block-start: 0.5rem; /* Replaces margin-top */
  margin-block-end: 0.5rem;   /* Replaces margin-bottom */
}

/* Flip icons and images for RTL */
[dir="rtl"] .flip-for-rtl {
  transform: scaleX(-1);
}

/* Directional arrows */
.arrow-forward::before {
  content: "→";
}

[dir="rtl"] .arrow-forward::before {
  content: "←";
}

/* Float replacements */
.float-start {
  float: inline-start;
}

.float-end {
  float: inline-end;
}

/* Flexbox directional utilities */
.flex-start {
  justify-content: flex-start;
}

[dir="rtl"] .flex-start {
  justify-content: flex-end;
}
```

### 3. Locale-Aware Form Components

```typescript
// components/LocalizedDatePicker.tsx
import React from 'react';
import DatePicker from 'react-datepicker';
import { useLocale } from '@/contexts/LocaleContext';
import { format, parse } from 'date-fns';
import { enUS, de, fr, ar, ja, zhCN } from 'date-fns/locale';

const dateLocales = {
  'en-US': enUS,
  'de-DE': de,
  'fr-FR': fr,
  'ar-SA': ar,
  'ja-JP': ja,
  'zh-CN': zhCN,
};

interface LocalizedDatePickerProps {
  value: Date | null;
  onChange: (date: Date | null) => void;
  label?: string;
  placeholder?: string;
  minDate?: Date;
  maxDate?: Date;
  disabled?: boolean;
}

export function LocalizedDatePicker({
  value,
  onChange,
  label,
  placeholder,
  minDate,
  maxDate,
  disabled,
}: LocalizedDatePickerProps) {
  const { locale } = useLocale();
  const dateLocale = dateLocales[locale.code] || enUS;
  
  const formatDateForDisplay = (date: Date) => {
    return format(date, locale.dateFormat.toLowerCase(), { locale: dateLocale });
  };
  
  return (
    <div className="date-picker-wrapper">
      {label && (
        <label className="block text-sm font-medium mb-1">
          {label}
        </label>
      )}
      <DatePicker
        selected={value}
        onChange={onChange}
        dateFormat={locale.dateFormat.toLowerCase()}
        locale={dateLocale}
        placeholderText={placeholder}
        minDate={minDate}
        maxDate={maxDate}
        disabled={disabled}
        showMonthDropdown
        showYearDropdown
        dropdownMode="select"
        calendarStartDay={locale.firstDayOfWeek}
        className="w-full px-3 py-2 border rounded-md"
        popperPlacement={locale.direction === 'rtl' ? 'bottom-end' : 'bottom-start'}
      />
    </div>
  );
}

// components/LocalizedCurrencyInput.tsx
import React, { useState, useEffect } from 'react';
import { useLocale } from '@/contexts/LocaleContext';

interface LocalizedCurrencyInputProps {
  value: number;
  onChange: (value: number) => void;
  currency?: string;
  label?: string;
  placeholder?: string;
  min?: number;
  max?: number;
  disabled?: boolean;
}

export function LocalizedCurrencyInput({
  value,
  onChange,
  currency,
  label,
  placeholder,
  min,
  max,
  disabled,
}: LocalizedCurrencyInputProps) {
  const { locale, formatters } = useLocale();
  const [displayValue, setDisplayValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  
  const currencyCode = currency || locale.currency.code;
  const currencySymbol = locale.currency.symbol;
  
  useEffect(() => {
    if (!isFocused) {
      setDisplayValue(formatters.formatCurrency(value, currencyCode));
    }
  }, [value, isFocused, currencyCode]);
  
  const handleFocus = () => {
    setIsFocused(true);
    setDisplayValue(value.toString());
  };
  
  const handleBlur = () => {
    setIsFocused(false);
    const numericValue = parseFloat(displayValue) || 0;
    onChange(numericValue);
  };
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const input = e.target.value;
    // Allow only numbers and decimal point
    if (/^\d*\.?\d*$/.test(input)) {
      setDisplayValue(input);
    }
  };
  
  return (
    <div className="currency-input-wrapper">
      {label && (
        <label className="block text-sm font-medium mb-1">
          {label}
        </label>
      )}
      <div className="relative">
        {locale.currency.position === 'before' && !isFocused && (
          <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
            {currencySymbol}
          </span>
        )}
        <input
          type="text"
          value={displayValue}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(
            'w-full px-3 py-2 border rounded-md',
            locale.currency.position === 'before' && !isFocused && 'pl-8',
            locale.currency.position === 'after' && !isFocused && 'pr-8'
          )}
        />
        {locale.currency.position === 'after' && !isFocused && (
          <span className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-500">
            {currencySymbol}
          </span>
        )}
      </div>
      {(min !== undefined || max !== undefined) && (
        <p className="text-xs text-gray-500 mt-1">
          {min !== undefined && `Min: ${formatters.formatCurrency(min, currencyCode)}`}
          {min !== undefined && max !== undefined && ' • '}
          {max !== undefined && `Max: ${formatters.formatCurrency(max, currencyCode)}`}
        </p>
      )}
    </div>
  );
}
```

### 4. Address Form Localization

```typescript
// components/LocalizedAddressForm.tsx
import React from 'react';
import { useForm, Controller } from 'react-hook-form';
import { useLocale } from '@/contexts/LocaleContext';
import { useTranslation } from 'react-i18next';

interface Address {
  street: string;
  street2?: string;
  city: string;
  state?: string;
  province?: string;
  prefecture?: string;
  county?: string;
  district?: string;
  postalCode: string;
  country: string;
}

const regionFields = {
  US: { field: 'state', label: 'State', required: true },
  CA: { field: 'province', label: 'Province', required: true },
  GB: { field: 'county', label: 'County', required: false },
  JP: { field: 'prefecture', label: 'Prefecture', required: true },
  SA: { field: 'district', label: 'District', required: true },
  DE: { field: null },
  FR: { field: null },
};

export function LocalizedAddressForm({ onSubmit }: { onSubmit: (data: Address) => void }) {
  const { locale } = useLocale();
  const { t } = useTranslation('forms');
  const { control, handleSubmit, watch, formState: { errors } } = useForm<Address>();
  
  const country = watch('country', locale.region);
  const regionConfig = regionFields[country] || {};
  
  // Reorder fields based on locale
  const getFieldOrder = () => {
    const baseFields = [
      { name: 'street', label: t('forms:address.street'), required: true },
      { name: 'street2', label: t('forms:address.street2'), required: false },
    ];
    
    const variableFields = [
      { name: 'city', label: t('forms:address.city'), required: true },
      regionConfig.field && { 
        name: regionConfig.field, 
        label: t(`forms:address.${regionConfig.field}`), 
        required: regionConfig.required 
      },
      { name: 'postalCode', label: t('forms:address.postalCode'), required: true },
      { name: 'country', label: t('forms:address.country'), required: true },
    ].filter(Boolean);
    
    // Reorder based on locale preferences
    if (locale.addressFormat) {
      return [...baseFields, ...variableFields].sort((a, b) => {
        const aIndex = locale.addressFormat.indexOf(a.name);
        const bIndex = locale.addressFormat.indexOf(b.name);
        if (aIndex === -1) return 1;
        if (bIndex === -1) return -1;
        return aIndex - bIndex;
      });
    }
    
    return [...baseFields, ...variableFields];
  };
  
  const fields = getFieldOrder();
  
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {fields.map((field) => (
        <div key={field.name}>
          <label className="block text-sm font-medium mb-1">
            {field.label}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </label>
          <Controller
            name={field.name as keyof Address}
            control={control}
            rules={{ required: field.required ? t('forms:validation.required') : false }}
            render={({ field: controllerField }) => (
              <>
                {field.name === 'country' ? (
                  <select
                    {...controllerField}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    <option value="">Select country</option>
                    <option value="US">United States</option>
                    <option value="GB">United Kingdom</option>
                    <option value="DE">Germany</option>
                    <option value="FR">France</option>
                    <option value="JP">Japan</option>
                    <option value="SA">Saudi Arabia</option>
                  </select>
                ) : (
                  <input
                    {...controllerField}
                    type="text"
                    className="w-full px-3 py-2 border rounded-md"
                    placeholder={field.name === 'postalCode' ? 
                      getPostalCodePlaceholder(country) : undefined}
                  />
                )}
                {errors[field.name as keyof Address] && (
                  <p className="text-red-500 text-sm mt-1">
                    {errors[field.name as keyof Address]?.message}
                  </p>
                )}
              </>
            )}
          />
        </div>
      ))}
      
      <button
        type="submit"
        className="w-full bg-blue-500 text-white py-2 rounded-md hover:bg-blue-600"
      >
        {t('forms:submit')}
      </button>
    </form>
  );
}

function getPostalCodePlaceholder(country: string): string {
  const placeholders = {
    US: '12345 or 12345-6789',
    GB: 'SW1A 1AA',
    DE: '12345',
    FR: '75001',
    JP: '123-4567',
    SA: '12345',
  };
  return placeholders[country] || '';
}
```

### 5. Dynamic Content Loading

```typescript
// hooks/useLocalizedContent.ts
import { useState, useEffect } from 'react';
import { useLocale } from '@/contexts/LocaleContext';

interface LocalizedContent {
  id: string;
  locale: string;
  title: string;
  content: string;
  metadata?: Record<string, any>;
}

export function useLocalizedContent(contentId: string) {
  const { locale } = useLocale();
  const [content, setContent] = useState<LocalizedContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  
  useEffect(() => {
    const loadContent = async () => {
      setLoading(true);
      setError(null);
      
      try {
        // Try to load content for specific locale
        let response = await fetch(
          `/api/content/${contentId}?locale=${locale.code}`
        );
        
        if (!response.ok) {
          // Fallback to language without region
          response = await fetch(
            `/api/content/${contentId}?locale=${locale.language}`
          );
        }
        
        if (!response.ok) {
          // Final fallback to English
          response = await fetch(
            `/api/content/${contentId}?locale=en`
          );
        }
        
        if (!response.ok) {
          throw new Error('Content not found');
        }
        
        const data = await response.json();
        setContent(data);
      } catch (err) {
        setError(err as Error);
      } finally {
        setLoading(false);
      }
    };
    
    loadContent();
  }, [contentId, locale.code]);
  
  return { content, loading, error };
}

// Usage in component
export function LocalizedArticle({ articleId }: { articleId: string }) {
  const { content, loading, error } = useLocalizedContent(articleId);
  const { locale } = useLocale();
  
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!content) return null;
  
  return (
    <article className={locale.direction === 'rtl' ? 'rtl-article' : 'ltr-article'}>
      <h1 className="text-3xl font-bold mb-4">{content.title}</h1>
      <div 
        className="prose max-w-none"
        dangerouslySetInnerHTML={{ __html: content.content }}
      />
      {content.metadata?.author && (
        <div className="mt-8 text-sm text-gray-600">
          {t('article.author')}: {content.metadata.author}
        </div>
      )}
    </article>
  );
}
```

### 6. Locale-Specific Validation

```typescript
// utils/localeValidation.ts
import { z } from 'zod';
import { useLocale } from '@/contexts/LocaleContext';

export function useLocaleValidation() {
  const { locale } = useLocale();
  
  const phoneValidation = z.string().refine((value) => {
    const patterns = {
      'en-US': /^\+?1?\s?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}$/,
      'en-GB': /^\+?44\s?7\d{3}\s?\d{6}$/,
      'de-DE': /^\+?49\s?\d{3,4}\s?\d{6,8}$/,
      'fr-FR': /^\+?33\s?[1-9]\s?\d{8}$/,
      'ja-JP': /^\+?81\s?\d{1,4}\s?\d{1,4}\s?\d{4}$/,
      'ar-SA': /^\+?966\s?5\d{8}$/,
    };
    
    const pattern = patterns[locale.code] || patterns['en-US'];
    return pattern.test(value);
  }, {
    message: t('validation:phone.invalid'),
  });
  
  const postalCodeValidation = z.string().refine((value) => {
    const patterns = {
      'en-US': /^\d{5}(-\d{4})?$/,
      'en-GB': /^[A-Z]{1,2}\d{1,2}[A-Z]?\s?\d[A-Z]{2}$/i,
      'de-DE': /^\d{5}$/,
      'fr-FR': /^\d{5}$/,
      'ja-JP': /^\d{3}-\d{4}$/,
      'ar-SA': /^\d{5}$/,
    };
    
    const pattern = patterns[locale.code] || patterns['en-US'];
    return pattern.test(value);
  }, {
    message: t('validation:postalCode.invalid'),
  });
  
  const currencyValidation = (min?: number, max?: number) => {
    return z.number()
      .min(min || 0, t('validation:currency.min', { min }))
      .max(max || Number.MAX_SAFE_INTEGER, t('validation:currency.max', { max }))
      .refine((value) => {
        // Check for currency-specific decimal places
        const decimalPlaces = {
          'JPY': 0, // Japanese Yen has no decimal places
          'KWD': 3, // Kuwaiti Dinar has 3 decimal places
        };
        
        const currency = locale.currency.code;
        const maxDecimals = decimalPlaces[currency] ?? 2;
        
        const decimals = (value.toString().split('.')[1] || '').length;
        return decimals <= maxDecimals;
      }, {
        message: t('validation:currency.decimals'),
      });
  };
  
  return {
    phoneValidation,
    postalCodeValidation,
    currencyValidation,
  };
}
```

### 7. Locale-Aware Search

```typescript
// components/LocalizedSearch.tsx
import React, { useState, useCallback } from 'react';
import { useLocale } from '@/contexts/LocaleContext';
import { useTranslation } from 'react-i18next';
import { Search } from 'lucide-react';
import debounce from 'lodash/debounce';

interface LocalizedSearchProps {
  onSearch: (query: string, locale: string) => void;
  placeholder?: string;
  suggestions?: string[];
}

export function LocalizedSearch({ 
  onSearch, 
  placeholder,
  suggestions = []
}: LocalizedSearchProps) {
  const { locale } = useLocale();
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  
  // Debounced search with locale
  const debouncedSearch = useCallback(
    debounce((searchQuery: string) => {
      onSearch(searchQuery, locale.code);
    }, 300),
    [locale.code]
  );
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    
    if (value.length >= 2) {
      debouncedSearch(value);
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };
  
  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    onSearch(suggestion, locale.code);
  };
  
  // Locale-specific search hints
  const getSearchHint = () => {
    const hints = {
      'en-US': 'Try searching for products, categories, or brands',
      'ja-JP': '商品、カテゴリー、またはブランドを検索してください',
      'ar-SA': 'جرب البحث عن المنتجات أو الفئات أو العلامات التجارية',
      'de-DE': 'Suchen Sie nach Produkten, Kategorien oder Marken',
      'fr-FR': 'Recherchez des produits, catégories ou marques',
    };
    
    return hints[locale.code] || hints['en-US'];
  };
  
  return (
    <div className="relative">
      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          placeholder={placeholder || t('common:search')}
          className={cn(
            'w-full px-4 py-2 border rounded-lg',
            locale.direction === 'rtl' ? 'pr-10 pl-4' : 'pl-10 pr-4'
          )}
          dir={locale.direction}
        />
        <Search 
          className={cn(
            'absolute top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400',
            locale.direction === 'rtl' ? 'right-3' : 'left-3'
          )}
        />
      </div>
      
      {query.length === 0 && (
        <p className="text-xs text-gray-500 mt-1">{getSearchHint()}</p>
      )}
      
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-10 w-full bg-white border rounded-lg shadow-lg mt-1">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => handleSuggestionClick(suggestion)}
              className="w-full px-4 py-2 text-left hover:bg-gray-100 first:rounded-t-lg last:rounded-b-lg"
              dir={locale.direction}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
```

## Testing Localization

### Visual Testing for Different Locales

```typescript
// __tests__/localization.visual.test.tsx
import { render } from '@testing-library/react';
import { LocaleProvider } from '@/contexts/LocaleContext';
import { I18nextProvider } from 'react-i18next';
import i18n from '@/i18n/test-config';
import { Dashboard } from '@/pages/Dashboard';

const locales = ['en-US', 'ar-SA', 'ja-JP', 'de-DE'];

describe('Localization Visual Tests', () => {
  locales.forEach((localeCode) => {
    it(`renders correctly in ${localeCode}`, async () => {
      const { container } = render(
        <I18nextProvider i18n={i18n}>
          <LocaleProvider defaultLocale={localeCode}>
            <Dashboard />
          </LocaleProvider>
        </I18nextProvider>
      );
      
      // Take screenshot for visual regression testing
      await expect(container).toMatchScreenshot(`dashboard-${localeCode}.png`);
    });
    
    it(`handles text overflow in ${localeCode}`, () => {
      // Test that long translations don't break layout
      const longText = 'A'.repeat(100);
      const { container } = render(
        <LocaleProvider defaultLocale={localeCode}>
          <div className="w-32 truncate">{longText}</div>
        </LocaleProvider>
      );
      
      const element = container.firstChild;
      expect(element).toHaveStyle({ textOverflow: 'ellipsis' });
    });
  });
  
  it('handles RTL layout correctly', () => {
    const { container } = render(
      <LocaleProvider defaultLocale="ar-SA">
        <div className="flex justify-start">
          <span>First</span>
          <span>Second</span>
        </div>
      </LocaleProvider>
    );
    
    expect(document.documentElement.dir).toBe('rtl');
    expect(container.firstChild).toHaveClass('flex-start');
  });
});
```

### Performance Testing

```typescript
// __tests__/localization.performance.test.ts
import { measureRender } from '@/utils/test-utils';

describe('Localization Performance', () => {
  it('renders within performance budget', async () => {
    const results = await measureRender(
      <LocaleProvider defaultLocale="en-US">
        <App />
      </LocaleProvider>
    );
    
    expect(results.renderTime).toBeLessThan(100); // ms
    expect(results.memoryUsage).toBeLessThan(10); // MB
  });
  
  it('switches locale without memory leaks', async () => {
    const { rerender, unmount } = render(
      <LocaleProvider defaultLocale="en-US">
        <App />
      </LocaleProvider>
    );
    
    const initialMemory = performance.memory.usedJSHeapSize;
    
    // Switch locales multiple times
    for (let i = 0; i < 10; i++) {
      rerender(
        <LocaleProvider defaultLocale={i % 2 === 0 ? 'en-US' : 'ja-JP'}>
          <App />
        </LocaleProvider>
      );
    }
    
    unmount();
    
    // Force garbage collection if available
    if (global.gc) global.gc();
    
    const finalMemory = performance.memory.usedJSHeapSize;
    const memoryIncrease = finalMemory - initialMemory;
    
    // Allow for some memory increase but flag potential leaks
    expect(memoryIncrease).toBeLessThan(1000000); // 1MB threshold
  });
});
```

## Deployment Considerations

### CDN Configuration for Localized Assets

```typescript
// config/cdn.ts
export const cdnConfig = {
  baseUrl: process.env.CDN_URL || 'https://cdn.reactdjango-hub.com',
  
  getLocalizedAssetUrl: (asset: string, locale: string) => {
    // Structure: /assets/{locale}/{type}/{filename}
    return `${cdnConfig.baseUrl}/assets/${locale}/${asset}`;
  },
  
  getTranslationUrl: (locale: string, namespace: string) => {
    return `${cdnConfig.baseUrl}/locales/${locale}/${namespace}.json`;
  },
  
  preloadLocales: ['en-US', 'en-GB'], // Preload common locales
  
  cacheControl: {
    translations: 'public, max-age=3600, s-maxage=86400', // 1 hour client, 1 day CDN
    assets: 'public, max-age=31536000, immutable', // 1 year for versioned assets
  },
};
```

### Server-Side Locale Detection

```typescript
// middleware/localeDetection.ts
import { NextRequest, NextResponse } from 'next/server';
import { match } from '@formatjs/intl-localematcher';
import Negotiator from 'negotiator';

const locales = ['en-US', 'en-GB', 'de-DE', 'fr-FR', 'ja-JP', 'ar-SA'];
const defaultLocale = 'en-US';

function getLocale(request: NextRequest): string {
  const negotiatorHeaders: Record<string, string> = {};
  request.headers.forEach((value, key) => (negotiatorHeaders[key] = value));
  
  // Check cookie first
  const cookieLocale = request.cookies.get('locale')?.value;
  if (cookieLocale && locales.includes(cookieLocale)) {
    return cookieLocale;
  }
  
  // Then check Accept-Language header
  const languages = new Negotiator({ headers: negotiatorHeaders }).languages();
  
  try {
    return match(languages, locales, defaultLocale);
  } catch {
    return defaultLocale;
  }
}

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  const pathnameIsMissingLocale = locales.every(
    (locale) => !pathname.startsWith(`/${locale}/`) && pathname !== `/${locale}`
  );
  
  if (pathnameIsMissingLocale) {
    const locale = getLocale(request);
    return NextResponse.redirect(
      new URL(`/${locale}${pathname}`, request.url)
    );
  }
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
};
```

## Best Practices

### Do's
- ✅ Use Intl API for formatting dates, numbers, currencies
- ✅ Test with real translations, not just keys
- ✅ Support text expansion (German ~30% longer than English)
- ✅ Use logical CSS properties for RTL support
- ✅ Validate locale-specific formats (phone, postal codes)
- ✅ Cache translations and locale preferences
- ✅ Provide fallbacks for missing translations

### Don'ts
- ❌ Hardcode date/time/number formats
- ❌ Assume text direction is always LTR
- ❌ Use pixel-perfect designs that break with text expansion
- ❌ Mix different locale formats in one view
- ❌ Ignore cultural color meanings
- ❌ Use machine translation without review
- ❌ Forget to test with actual multilingual content

---

**Document maintained by**: Technical Lead Agent  
**For**: Frontend Agent, All Service Agents  
**Last updated**: December 10, 2024  
**Next review**: January 10, 2025