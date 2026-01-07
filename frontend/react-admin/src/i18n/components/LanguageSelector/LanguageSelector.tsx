/**
 * Language Selector Component for React
 * 
 * Version: 3.0
 * License: MIT
 */

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { SUPPORTED_LANGUAGES, type SupportedLanguageCode } from '../../config/i18n';
import './LanguageSelector.css';

export interface LanguageSelectorProps {
  variant?: 'dropdown' | 'flags' | 'compact';
  showNativeNames?: boolean;
  className?: string;
}

export const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  variant = 'dropdown',
  showNativeNames = true,
  className = '',
}) => {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);

  const currentLanguage = SUPPORTED_LANGUAGES.find(
    (lang) => lang.code === i18n.language
  ) || SUPPORTED_LANGUAGES[0];

  const handleLanguageChange = (langCode: SupportedLanguageCode) => {
    i18n.changeLanguage(langCode);
    setIsOpen(false);
  };

  if (variant === 'compact') {
    return (
      <select
        value={i18n.language}
        onChange={(e) => handleLanguageChange(e.target.value as SupportedLanguageCode)}
        className={`language-selector-compact ${className}`}
        aria-label="Select language"
      >
        {SUPPORTED_LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.flag} {lang.code.toUpperCase()}
          </option>
        ))}
      </select>
    );
  }

  if (variant === 'flags') {
    return (
      <div className={`language-selector-flags ${className}`}>
        {SUPPORTED_LANGUAGES.map((lang) => (
          <button
            key={lang.code}
            onClick={() => handleLanguageChange(lang.code)}
            className={`flag-button ${lang.code === i18n.language ? 'active' : ''}`}
            title={lang.nativeName}
            aria-label={`Switch to ${lang.name}`}
          >
            {lang.flag}
          </button>
        ))}
      </div>
    );
  }

  // Default dropdown variant
  return (
    <div className={`language-selector-dropdown ${className}`}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="language-selector-button"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span className="current-language">
          {currentLanguage.flag} {showNativeNames ? currentLanguage.nativeName : currentLanguage.name}
        </span>
        <svg
          className={`dropdown-icon ${isOpen ? 'open' : ''}`}
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
        >
          <path
            d="M2 4L6 8L10 4"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>

      {isOpen && (
        <>
          <div className="dropdown-overlay" onClick={() => setIsOpen(false)} />
          <div className="dropdown-menu" role="listbox">
            {SUPPORTED_LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                onClick={() => handleLanguageChange(lang.code)}
                className={`dropdown-item ${lang.code === i18n.language ? 'active' : ''}`}
                role="option"
                aria-selected={lang.code === i18n.language}
              >
                <span className="flag">{lang.flag}</span>
                <span className="language-name">
                  {showNativeNames ? lang.nativeName : lang.name}
                </span>
                {lang.code === i18n.language && (
                  <svg
                    className="check-icon"
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="none"
                  >
                    <path
                      d="M13 4L6 11L3 8"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default LanguageSelector;
