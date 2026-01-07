/**
 * React i18next Configuration for Agentic AI Platform
 * 
 * Version: 3.0 - FIXED for single-file translations
 * License: MIT
 */

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';
import Backend from 'i18next-http-backend';

// Import types
import type { InitOptions } from 'i18next';

// =============================================================================
// Configuration
// =============================================================================

export const SUPPORTED_LANGUAGES = [
  {
    code: 'en',
    name: 'English',
    nativeName: 'English',
    flag: '🇺🇸',
    direction: 'ltr'
  },
  {
    code: 'es',
    name: 'Spanish',
    nativeName: 'Español',
    flag: '🇪🇸',
    direction: 'ltr'
  },
  {
    code: 'fr',
    name: 'French',
    nativeName: 'Français',
    flag: '🇫🇷',
    direction: 'ltr'
  },
  {
    code: 'de',
    name: 'German',
    nativeName: 'Deutsch',
    flag: '🇩🇪',
    direction: 'ltr'
  },
  {
    code: 'ar',
    name: 'Arabic',
    nativeName: 'العربية',
    flag: '🇸🇦',
    direction: 'rtl'
  },
  {
    code: 'ja',
    name: 'Japanese',
    nativeName: '日本語',
    flag: '🇯🇵',
    direction: 'ltr'
  },
  {
    code: 'zh',
    name: 'Chinese',
    nativeName: '中文',
    flag: '🇨🇳',
    direction: 'ltr'
  },
] as const;

export type SupportedLanguageCode = typeof SUPPORTED_LANGUAGES[number]['code'];
export type SupportedLanguage = typeof SUPPORTED_LANGUAGES[number];

// Namespaces - keeping for reference but not used in backend loading
export const NAMESPACES = [
  'common',
  'admin',
  'agents',
  'hitl',
  'errors',
  'auth',
  'workflows',
  'monitoring',
  'notifications'
] as const;

export type Namespace = typeof NAMESPACES[number];

// RTL Languages
export const RTL_LANGUAGES: SupportedLanguageCode[] = ['ar'];

// =============================================================================
// i18next Configuration
// =============================================================================

const isDevelopment = process.env.NODE_ENV === 'development';
const isProduction = process.env.NODE_ENV === 'production';

const i18nConfig: InitOptions = {
  // Fallback language
  fallbackLng: 'en',
  
  // Supported languages
  supportedLngs: SUPPORTED_LANGUAGES.map(lang => lang.code),
  
  // FIXED: Remove namespace configuration for single-file translations
  // The JSON files contain all namespaces in one file (en.json, es.json, etc.)
  // ns: NAMESPACES,           // ❌ REMOVED - causes 404 errors
  // defaultNS: 'common',      // ❌ REMOVED - not needed for single files
  
  // Debug mode (only in development)
  debug: false, // Set to true to see translation loading logs
  
  // Language detection options
  detection: {
    // Order of detection methods
    order: [
      'querystring',
      'cookie',
      'localStorage',
      'sessionStorage',
      'navigator',
      'htmlTag'
    ],
    
    // Lookup keys
    lookupQuerystring: 'locale',
    lookupCookie: 'i18next',
    lookupLocalStorage: 'i18nextLng',
    lookupSessionStorage: 'i18nextLng',
    
    // Cache user language
    caches: ['localStorage', 'cookie'],
    
    // Cookie options
    cookieOptions: {
      path: '/',
      sameSite: 'strict',
      secure: isProduction,
    },
  },
  
  // Backend options (for loading translations from server)
  backend: {
    // FIXED: Single file per language (not separated by namespace)
    loadPath: '/locales/{{lng}}.json', // ✅ Changed from /locales/{{lng}}/{{ns}}.json
    
    // Disable multiloading since we have single files
    allowMultiLoading: false,
    
    // Request options
    requestOptions: {
      mode: 'cors',
      credentials: 'same-origin',
      cache: 'default',
    },
    
    // Custom headers
    customHeaders: {
      'Accept': 'application/json',
    },
  },
  
  // Interpolation options
  interpolation: {
    // React already escapes values
    escapeValue: false,
    
    // Custom format function
    format: (value: any, format: string | undefined, lng: string | undefined) => {
      // String formatting
      if (typeof value === 'string') {
        if (format === 'uppercase') return value.toUpperCase();
        if (format === 'lowercase') return value.toLowerCase();
        if (format === 'capitalize') {
          return value.charAt(0).toUpperCase() + value.slice(1);
        }
      }
      
      // Date formatting
      if (value instanceof Date && lng) {
        if (format === 'short') {
          return new Intl.DateTimeFormat(lng, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
          }).format(value);
        }
        if (format === 'medium') {
          return new Intl.DateTimeFormat(lng, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          }).format(value);
        }
        if (format === 'long') {
          return new Intl.DateTimeFormat(lng, {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
          }).format(value);
        }
        if (format === 'full') {
          return new Intl.DateTimeFormat(lng, {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
          }).format(value);
        }
      }
      
      // Number formatting
      if (typeof value === 'number' && lng) {
        if (format === 'number') {
          return new Intl.NumberFormat(lng).format(value);
        }
        
        // Currency formatting
        if (format?.startsWith('currency:')) {
          const currency = format.split(':')[1] || 'USD';
          return new Intl.NumberFormat(lng, {
            style: 'currency',
            currency: currency,
          }).format(value);
        }
        
        // Percentage formatting
        if (format === 'percent') {
          return new Intl.NumberFormat(lng, {
            style: 'percent',
            minimumFractionDigits: 0,
            maximumFractionDigits: 2,
          }).format(value / 100);
        }
      }
      
      return value;
    },
  },
  
  // React options
  react: {
    // Use Suspense for loading
    useSuspense: true,
    
    // Bind i18n instance
    bindI18n: 'languageChanged loaded',
    bindI18nStore: 'added removed',
    
    // Trans component options
    transKeepBasicHtmlNodesFor: ['br', 'strong', 'i', 'em', 'span', 'p'],
    transSupportBasicHtmlNodes: true,
    transWrapTextNodes: '',
  },
  
  // Performance optimizations
  load: 'languageOnly', // Only load 'en' not 'en-US'
  preload: ['en'], // Preload default language
  
  // Missing key handling
  saveMissing: isDevelopment,
  missingKeyHandler: (lngs, ns, key, fallbackValue) => {
    if (isDevelopment) {
      console.warn(`[i18n] Missing translation: [${lngs}] ${ns}:${key}`);
    }
  },
  
  // FIXED: No fallback namespace since we don't use namespaces in backend loading
  // fallbackNS: 'common',  // ❌ REMOVED
  
  // Return objects for nested translations (IMPORTANT: keep this true for nested structure)
  returnObjects: true, // ✅ Changed to true - allows accessing nested keys like t('common.app.title')
  
  // Join arrays
  joinArrays: ' ',
  
  // Key separator (for accessing nested keys)
  keySeparator: '.',      // Allows: t('common.nav.dashboard')
  nsSeparator: ':',       // Allows: t('common:nav.dashboard') - but not needed with single files
  
  // Pluralization
  pluralSeparator: '_',
  contextSeparator: '_',
  
  // Non-explicit support
  nonExplicitSupportedLngs: false,
};

// =============================================================================
// Initialize i18next
// =============================================================================

i18n
  .use(Backend)
  .use(LanguageDetector)
  .use(initReactI18next)
  .init(i18nConfig);

// =============================================================================
// Event Handlers
// =============================================================================

// Apply RTL on language change
i18n.on('languageChanged', (lng) => {
  const language = SUPPORTED_LANGUAGES.find(l => l.code === lng);
  const isRTL = language?.direction === 'rtl';
  
  // Update document direction
  document.documentElement.setAttribute('dir', isRTL ? 'rtl' : 'ltr');
  document.documentElement.setAttribute('lang', lng);
  
  // Update body class for CSS styling
  document.body.classList.toggle('rtl', isRTL);
  document.body.classList.toggle('ltr', !isRTL);
  
  console.log(`[i18n] Language changed to: ${lng} (${isRTL ? 'RTL' : 'LTR'})`);
});

// Initialize RTL on load
const initLanguage = SUPPORTED_LANGUAGES.find(l => l.code === i18n.language);
if (initLanguage?.direction === 'rtl') {
  document.documentElement.setAttribute('dir', 'rtl');
  document.body.classList.add('rtl');
} else {
  document.documentElement.setAttribute('dir', 'ltr');
  document.body.classList.add('ltr');
}

// Log initialization
console.log('[i18n] Initialized with language:', i18n.language);

// Log translation file loading (for debugging)
i18n.on('loaded', (loaded) => {
  console.log('[i18n] Translations loaded:', Object.keys(loaded));
});

i18n.on('failedLoading', (lng, ns, msg) => {
  console.error(`[i18n] Failed to load ${lng}/${ns}:`, msg);
});

export default i18n;