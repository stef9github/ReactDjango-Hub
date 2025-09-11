/**
 * Internationalization Configuration
 * Implementation of ADR-002: French-first i18n strategy
 */

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import ICU from 'i18next-icu';

// Language resources organized by vertical (per ADR-002)
import frCommon from './locales/fr/common.json';
import frMedical from './locales/fr/medical.json';
import frPublic from './locales/fr/public.json';

// Supported languages (French first per ADR-002)
export const supportedLanguages = ['fr', 'en', 'de', 'it', 'es'] as const;
export const defaultLanguage = 'fr'; // French first per architecture decision

// Initialize i18n with ADR-002 configuration
i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .use(ICU) // ICU Message Format for complex translations
  .init({
    resources: {
      fr: {
        common: frCommon,
        medical: frMedical,
        public: frPublic,
      },
      // Other languages loaded dynamically per ADR-002 strategy
    },
    lng: defaultLanguage,
    fallbackLng: 'fr', // French fallback per ADR-002
    defaultNS: 'common',
    ns: ['common', 'medical', 'public'], // Vertical-specific namespaces
    
    interpolation: {
      escapeValue: false,
      format: (value, format, lng) => {
        // Custom formatters per ADR-002 requirements
        if (format === 'currency') {
          return new Intl.NumberFormat(lng, {
            style: 'currency',
            currency: lng === 'fr' ? 'EUR' : 'USD',
          }).format(value);
        }
        if (format === 'date') {
          return new Intl.DateTimeFormat(lng).format(new Date(value));
        }
        return value;
      },
    },
    
    detection: {
      // Detection order per ADR-002
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
    },
  });

export default i18n;