/**
 * Agentic AI Platform - React i18n Package
 * Main export file
 * 
 * Version: 3.0
 * License: MIT
 */

// Core i18n configuration
export { default as i18n } from './config/i18n';
export { SUPPORTED_LANGUAGES, NAMESPACES, RTL_LANGUAGES } from './config/i18n';
export type { SupportedLanguageCode, SupportedLanguage, Namespace } from './config/i18n';

// Components
export { LanguageSelector } from './components/LanguageSelector';
export type { LanguageSelectorProps } from './components/LanguageSelector';

// Re-export react-i18next hooks and components for convenience
export {
  useTranslation,
  Trans,
  Translation,
  I18nextProvider,
  useSSR,
  withTranslation,
  withSSR,
} from 'react-i18next';

// Type exports
export type { TFunction, i18n as I18n } from 'i18next';
