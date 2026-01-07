"""
Streamlit Internationalization Module
Provides translation support for Streamlit HITL interface

Version: 3.0
License: MIT
"""

import streamlit as st
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime, date

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

SUPPORTED_LOCALES = ["en", "es", "fr", "de", "ar", "ja", "zh"]
DEFAULT_LOCALE = "en"
RTL_LOCALES = ["ar"]

# Session state key for locale
SESSION_LOCALE_KEY = "locale"

# Translations dictionary (loaded from files)
_translations: Dict[str, Dict[str, str]] = {}


# =============================================================================
# Locale Configuration
# =============================================================================

class LocaleConfig:
    """Locale configuration and info"""
    
    LOCALE_INFO = {
        "en": {"name": "English", "native_name": "English", "direction": "ltr", "flag": "🇺🇸"},
        "es": {"name": "Spanish", "native_name": "Español", "direction": "ltr", "flag": "🇪🇸"},
        "fr": {"name": "French", "native_name": "Français", "direction": "ltr", "flag": "🇫🇷"},
        "de": {"name": "German", "native_name": "Deutsch", "direction": "ltr", "flag": "🇩🇪"},
        "ar": {"name": "Arabic", "native_name": "العربية", "direction": "rtl", "flag": "🇸🇦"},
        "ja": {"name": "Japanese", "native_name": "日本語", "direction": "ltr", "flag": "🇯🇵"},
        "zh": {"name": "Chinese", "native_name": "中文", "direction": "ltr", "flag": "🇨🇳"},
    }
    
    @classmethod
    def get_info(cls, locale: str) -> Dict[str, str]:
        return cls.LOCALE_INFO.get(locale, cls.LOCALE_INFO[DEFAULT_LOCALE])
    
    @classmethod
    def is_rtl(cls, locale: str) -> bool:
        return cls.LOCALE_INFO.get(locale, {}).get("direction") == "rtl"


config = LocaleConfig()


# =============================================================================
# Session State Management
# =============================================================================

def init_session_state() -> None:
    """Initialize session state for i18n"""
    if SESSION_LOCALE_KEY not in st.session_state:
        st.session_state[SESSION_LOCALE_KEY] = DEFAULT_LOCALE


def get_current_locale() -> str:
    """Get current locale from session state"""
    init_session_state()
    return st.session_state.get(SESSION_LOCALE_KEY, DEFAULT_LOCALE)


def set_locale(locale: str) -> None:
    """Set locale in session state"""
    if locale not in SUPPORTED_LOCALES:
        logger.warning(f"Unsupported locale: {locale}, using {DEFAULT_LOCALE}")
        locale = DEFAULT_LOCALE
    
    st.session_state[SESSION_LOCALE_KEY] = locale
    logger.info(f"Locale set to: {locale}")


# =============================================================================
# Translation Loading
# =============================================================================

def load_translations(locale: str) -> Dict[str, str]:
    """
    Load translations for a locale
    
    In production, this would load from PO/MO files or JSON
    For now, returns empty dict (translations added via update_translations)
    """
    if locale not in _translations:
        _translations[locale] = {}
        logger.info(f"Initialized translations for: {locale}")
    
    return _translations[locale]


def update_translations(locale: str, translations: Dict[str, str]) -> None:
    """Update translations for a locale"""
    if locale not in _translations:
        _translations[locale] = {}
    
    _translations[locale].update(translations)
    logger.info(f"Updated {len(translations)} translations for {locale}")


# =============================================================================
# Translation Functions
# =============================================================================

def gettext(message: str, locale: Optional[str] = None) -> str:
    """
    Translate a message
    
    Args:
        message: Message to translate
        locale: Override locale (uses current if not provided)
        
    Returns:
        Translated message
    """
    if locale is None:
        locale = get_current_locale()
    
    translations = load_translations(locale)
    return translations.get(message, message)


def ngettext(singular: str, plural: str, n: int, locale: Optional[str] = None) -> str:
    """
    Translate with plural support
    
    Args:
        singular: Singular form
        plural: Plural form
        n: Count
        locale: Override locale
        
    Returns:
        Translated message in correct plural form
    """
    if locale is None:
        locale = get_current_locale()
    
    # Simple English-style pluralization
    # For more complex, use Babel's plural rules
    message = singular if n == 1 else plural
    translations = load_translations(locale)
    translated = translations.get(message, message)
    
    return translated.format(n=n)


# Convenience aliases
_ = gettext
_n = ngettext


# =============================================================================
# Formatting Functions
# =============================================================================

def format_date_i18n(date_obj: Any, format: str = "medium", locale: Optional[str] = None) -> str:
    """Format date according to locale"""
    if locale is None:
        locale = get_current_locale()
    
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    
    # Simple formatting (in production, use Babel)
    if format == "short":
        return date_obj.strftime("%m/%d/%Y")
    elif format == "long":
        return date_obj.strftime("%B %d, %Y")
    else:  # medium
        return date_obj.strftime("%b %d, %Y")


def format_datetime_i18n(dt_obj: datetime, format: str = "medium", locale: Optional[str] = None) -> str:
    """Format datetime according to locale"""
    if locale is None:
        locale = get_current_locale()
    
    if format == "short":
        return dt_obj.strftime("%m/%d/%Y %H:%M")
    elif format == "long":
        return dt_obj.strftime("%B %d, %Y %H:%M:%S")
    else:  # medium
        return dt_obj.strftime("%b %d, %Y %H:%M")


def format_number_i18n(number: float, locale: Optional[str] = None) -> str:
    """Format number according to locale"""
    if locale is None:
        locale = get_current_locale()
    
    # Simple formatting (use Babel in production)
    return f"{number:,.2f}"


def format_currency_i18n(amount: float, currency: str = "USD", locale: Optional[str] = None) -> str:
    """Format currency according to locale"""
    if locale is None:
        locale = get_current_locale()
    
    # Simple formatting
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥"}
    symbol = symbols.get(currency, currency)
    
    return f"{symbol}{amount:,.2f}"


# =============================================================================
# Utility Functions
# =============================================================================

def is_rtl(locale: Optional[str] = None) -> bool:
    """Check if locale uses RTL"""
    if locale is None:
        locale = get_current_locale()
    return config.is_rtl(locale)


def get_locale_info(locale: Optional[str] = None) -> Dict[str, str]:
    """Get locale information"""
    if locale is None:
        locale = get_current_locale()
    return config.get_info(locale)


def get_available_locales() -> list:
    """Get list of available locales"""
    return SUPPORTED_LOCALES.copy()


# =============================================================================
# RTL Support
# =============================================================================

def apply_rtl_if_needed() -> None:
    """Apply RTL styling if current locale uses RTL"""
    if is_rtl():
        st.markdown(
            """
            <style>
            .main { direction: rtl; text-align: right; }
            .stTextInput > div > div > input { text-align: right; }
            .stSelectbox > div > div > select { text-align: right; }
            </style>
            """,
            unsafe_allow_html=True
        )


# =============================================================================
# Initialization
# =============================================================================

def init_i18n() -> None:
    """Initialize i18n system for Streamlit"""
    init_session_state()
    logger.info("Streamlit i18n initialized")
    logger.info(f"Current locale: {get_current_locale()}")
    logger.info(f"Supported locales: {', '.join(SUPPORTED_LOCALES)}")


# =============================================================================
# Default English Translations
# =============================================================================

DEFAULT_TRANSLATIONS_EN = {
    # Common
    "Agentic AI Platform": "Agentic AI Platform",
    "Welcome": "Welcome",
    "Loading": "Loading",
    "Save": "Save",
    "Cancel": "Cancel",
    "Delete": "Delete",
    "Edit": "Edit",
    "Create": "Create",
    "Confirm": "Confirm",
    "Search": "Search",
    "Filter": "Filter",
    "Status": "Status",
    "Active": "Active",
    "Inactive": "Inactive",
    "Actions": "Actions",
    
    # HITL
    "Human-in-the-Loop Console": "Human-in-the-Loop Console",
    "Pending Reviews": "Pending Reviews",
    "Approve": "Approve",
    "Reject": "Reject",
    "Priority": "Priority",
    "Agent": "Agent",
    
    # Agents
    "Agent Management": "Agent Management",
    "Create Agent": "Create Agent",
    "Agent List": "Agent List",
    "Workflow": "Workflow",
    "Executions": "Executions",
    "Success Rate": "Success Rate",
    "Last Run": "Last Run",
}

# Initialize with default English translations
update_translations("en", DEFAULT_TRANSLATIONS_EN)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "init_i18n",
    "get_current_locale",
    "set_locale",
    "gettext",
    "ngettext",
    "_",
    "_n",
    "format_date_i18n",
    "format_datetime_i18n",
    "format_number_i18n",
    "format_currency_i18n",
    "is_rtl",
    "get_locale_info",
    "get_available_locales",
    "apply_rtl_if_needed",
    "update_translations",
    "SUPPORTED_LOCALES",
    "DEFAULT_LOCALE",
    "RTL_LOCALES",
]
