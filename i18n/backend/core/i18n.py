"""
Backend Internationalization Module for Agentic AI Platform
Provides translation support using Babel for API responses, emails, and notifications

Version: 3.0
License: MIT
"""

import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from contextvars import ContextVar
from datetime import datetime, date
from decimal import Decimal

try:
    from babel import Locale
    from babel.support import Translations, NullTranslations
    from babel.dates import format_date as babel_format_date
    from babel.dates import format_datetime as babel_format_datetime
    from babel.dates import format_time as babel_format_time
    from babel.numbers import format_decimal, format_currency as babel_format_currency
    from babel.numbers import format_percent
except ImportError:
    raise ImportError(
        "Babel is required for i18n support. Install it with: pip install babel"
    )

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

# Context variable for current locale (thread-safe)
_current_locale: ContextVar[str] = ContextVar("locale", default="en")

# Translation cache for performance
_translations_cache: Dict[str, Translations] = {}

# Supported locales (ISO 639-1 language codes)
SUPPORTED_LOCALES = ["en", "es", "fr", "de", "ar", "ja", "zh"]

# Default locale
DEFAULT_LOCALE = "en"

# RTL (Right-to-Left) languages
RTL_LOCALES = ["ar"]

# Translations directory
TRANSLATIONS_DIR = Path(__file__).parent.parent / "translations"

# Domain for message catalogs
DOMAIN = "messages"


# =============================================================================
# Locale Configuration Class
# =============================================================================

class LocaleConfig:
    """Configuration for locale-specific settings"""
    
    LOCALE_INFO = {
        "en": {
            "name": "English",
            "native_name": "English",
            "direction": "ltr",
            "plural_forms": 2,
            "locale": "en_US"
        },
        "es": {
            "name": "Spanish",
            "native_name": "Español",
            "direction": "ltr",
            "plural_forms": 2,
            "locale": "es_ES"
        },
        "fr": {
            "name": "French",
            "native_name": "Français",
            "direction": "ltr",
            "plural_forms": 2,
            "locale": "fr_FR"
        },
        "de": {
            "name": "German",
            "native_name": "Deutsch",
            "direction": "ltr",
            "plural_forms": 2,
            "locale": "de_DE"
        },
        "ar": {
            "name": "Arabic",
            "native_name": "العربية",
            "direction": "rtl",
            "plural_forms": 6,
            "locale": "ar_SA"
        },
        "ja": {
            "name": "Japanese",
            "native_name": "日本語",
            "direction": "ltr",
            "plural_forms": 1,
            "locale": "ja_JP"
        },
        "zh": {
            "name": "Chinese",
            "native_name": "中文",
            "direction": "ltr",
            "plural_forms": 1,
            "locale": "zh_CN"
        }
    }
    
    @classmethod
    def get_info(cls, locale: str) -> Dict[str, Any]:
        """Get information about a locale"""
        return cls.LOCALE_INFO.get(locale, cls.LOCALE_INFO[DEFAULT_LOCALE])
    
    @classmethod
    def is_rtl(cls, locale: str) -> bool:
        """Check if locale uses RTL direction"""
        return cls.LOCALE_INFO.get(locale, {}).get("direction") == "rtl"
    
    @classmethod
    def get_babel_locale(cls, locale: str) -> str:
        """Get Babel-compatible locale string"""
        return cls.LOCALE_INFO.get(locale, {}).get("locale", "en_US")


config = LocaleConfig()


# =============================================================================
# Core Translation Functions
# =============================================================================

def get_current_locale() -> str:
    """
    Get current locale from context
    
    Returns:
        str: Current locale code (e.g., 'en', 'es', 'fr')
    """
    return _current_locale.get()


def set_locale(locale: str) -> None:
    """
    Set locale in context
    
    Args:
        locale: Language code (e.g., 'en', 'es', 'fr')
        
    Note:
        If locale is not supported, falls back to DEFAULT_LOCALE
    """
    if locale not in SUPPORTED_LOCALES:
        logger.warning(
            f"Unsupported locale: {locale}, falling back to {DEFAULT_LOCALE}"
        )
        locale = DEFAULT_LOCALE
    _current_locale.set(locale)
    logger.debug(f"Locale set to: {locale}")


def get_translations(locale: str) -> Translations:
    """
    Get translations for a locale with caching
    
    Args:
        locale: Language code
        
    Returns:
        Babel Translations object
        
    Note:
        Translations are cached for performance
    """
    if locale not in _translations_cache:
        try:
            translations = Translations.load(
                dirname=str(TRANSLATIONS_DIR),
                locales=[locale],
                domain=DOMAIN
            )
            _translations_cache[locale] = translations
            logger.info(f"Loaded translations for locale: {locale}")
        except Exception as e:
            logger.error(f"Failed to load translations for {locale}: {e}")
            logger.warning(f"Using NullTranslations for {locale}")
            _translations_cache[locale] = NullTranslations()
    
    return _translations_cache[locale]


def clear_translations_cache() -> None:
    """Clear the translations cache (useful for testing or hot-reload)"""
    global _translations_cache
    _translations_cache.clear()
    logger.info("Translations cache cleared")


# =============================================================================
# Translation Functions
# =============================================================================

def gettext(message: str, locale: Optional[str] = None) -> str:
    """
    Translate a message
    
    Args:
        message: Message to translate
        locale: Override locale (uses context if not provided)
        
    Returns:
        Translated message
        
    Example:
        >>> gettext("Hello, World!")
        "¡Hola, Mundo!"  # if locale is 'es'
    """
    if locale is None:
        locale = get_current_locale()
    
    translations = get_translations(locale)
    return translations.gettext(message)


def ngettext(
    singular: str,
    plural: str,
    n: int,
    locale: Optional[str] = None,
    **kwargs
) -> str:
    """
    Translate a message with plural support
    
    Args:
        singular: Singular form
        plural: Plural form
        n: Count
        locale: Override locale
        **kwargs: Additional format variables
        
    Returns:
        Translated message in correct plural form
        
    Example:
        >>> ngettext("You have {n} message", "You have {n} messages", 5)
        "Tienes 5 mensajes"  # if locale is 'es'
    """
    if locale is None:
        locale = get_current_locale()
    
    translations = get_translations(locale)
    message = translations.ngettext(singular, plural, n)
    
    # Format with provided kwargs, including n
    format_vars = {"n": n}
    format_vars.update(kwargs)
    return message.format(**format_vars)


def pgettext(context: str, message: str, locale: Optional[str] = None) -> str:
    """
    Translate a message with context
    
    Args:
        context: Translation context (e.g., 'button', 'menu', 'error')
        message: Message to translate
        locale: Override locale
        
    Returns:
        Translated message
        
    Example:
        >>> pgettext("button", "Save")
        "Guardar"  # if locale is 'es'
        
        >>> pgettext("menu", "Save")
        "Guardar Como"  # Different context, different translation
    """
    if locale is None:
        locale = get_current_locale()
    
    translations = get_translations(locale)
    return translations.pgettext(context, message)


# =============================================================================
# Formatting Functions
# =============================================================================

def format_date(
    date_obj: Any,
    format: str = "medium",
    locale: Optional[str] = None
) -> str:
    """
    Format a date according to locale
    
    Args:
        date_obj: datetime or date object
        format: 'short', 'medium', 'long', 'full' or custom format
        locale: Override locale
        
    Returns:
        Formatted date string
        
    Example:
        >>> format_date(datetime(2024, 12, 25), "long", "es")
        "25 de diciembre de 2024"
    """
    if locale is None:
        locale = get_current_locale()
    
    babel_locale = config.get_babel_locale(locale)
    return babel_format_date(date_obj, format=format, locale=babel_locale)


def format_datetime(
    dt_obj: Any,
    format: str = "medium",
    locale: Optional[str] = None
) -> str:
    """
    Format a datetime according to locale
    
    Args:
        dt_obj: datetime object
        format: 'short', 'medium', 'long', 'full' or custom format
        locale: Override locale
        
    Returns:
        Formatted datetime string
        
    Example:
        >>> format_datetime(datetime(2024, 12, 25, 14, 30), "long", "fr")
        "25 décembre 2024 à 14:30:00"
    """
    if locale is None:
        locale = get_current_locale()
    
    babel_locale = config.get_babel_locale(locale)
    return babel_format_datetime(dt_obj, format=format, locale=babel_locale)


def format_time(
    time_obj: Any,
    format: str = "medium",
    locale: Optional[str] = None
) -> str:
    """
    Format a time according to locale
    
    Args:
        time_obj: time object
        format: 'short', 'medium', 'long', 'full'
        locale: Override locale
        
    Returns:
        Formatted time string
    """
    if locale is None:
        locale = get_current_locale()
    
    babel_locale = config.get_babel_locale(locale)
    return babel_format_time(time_obj, format=format, locale=babel_locale)


def format_number(number: float, locale: Optional[str] = None) -> str:
    """
    Format a number according to locale
    
    Args:
        number: Number to format
        locale: Override locale
        
    Returns:
        Formatted number string
        
    Example:
        >>> format_number(1234567.89, "de")
        "1.234.567,89"
    """
    if locale is None:
        locale = get_current_locale()
    
    babel_locale = config.get_babel_locale(locale)
    return format_decimal(number, locale=babel_locale)


def format_currency(
    amount: float,
    currency: str = "USD",
    locale: Optional[str] = None
) -> str:
    """
    Format a currency amount according to locale
    
    Args:
        amount: Amount to format
        currency: Currency code (e.g., 'USD', 'EUR', 'JPY')
        locale: Override locale
        
    Returns:
        Formatted currency string
        
    Example:
        >>> format_currency(99.99, "EUR", "fr")
        "99,99 €"
    """
    if locale is None:
        locale = get_current_locale()
    
    babel_locale = config.get_babel_locale(locale)
    return babel_format_currency(amount, currency, locale=babel_locale)


def format_percentage(value: float, locale: Optional[str] = None) -> str:
    """
    Format a percentage according to locale
    
    Args:
        value: Value to format (e.g., 0.945 for 94.5%)
        locale: Override locale
        
    Returns:
        Formatted percentage string
    """
    if locale is None:
        locale = get_current_locale()
    
    babel_locale = config.get_babel_locale(locale)
    return format_percent(value, locale=babel_locale)


# =============================================================================
# Convenience Aliases
# =============================================================================

# Short aliases for common functions
_ = gettext
_n = ngettext
_p = pgettext


# =============================================================================
# Utility Functions
# =============================================================================

def get_available_locales() -> List[str]:
    """Get list of available locales"""
    return SUPPORTED_LOCALES.copy()


def is_rtl(locale: Optional[str] = None) -> bool:
    """
    Check if locale uses RTL (right-to-left) text direction
    
    Args:
        locale: Locale to check (uses current if not provided)
        
    Returns:
        True if RTL, False otherwise
    """
    if locale is None:
        locale = get_current_locale()
    return config.is_rtl(locale)


def get_locale_info(locale: Optional[str] = None) -> Dict[str, Any]:
    """
    Get information about a locale
    
    Args:
        locale: Locale to get info for (uses current if not provided)
        
    Returns:
        Dict with locale information (name, direction, etc.)
    """
    if locale is None:
        locale = get_current_locale()
    return config.get_info(locale)


# =============================================================================
# Initialization
# =============================================================================

def init_i18n() -> None:
    """
    Initialize i18n system
    Should be called on application startup
    
    This function:
    - Creates translations directory if needed
    - Pre-loads default locale
    - Logs configuration info
    """
    logger.info("=" * 70)
    logger.info("Initializing Agentic AI Platform i18n system v3.0")
    logger.info("=" * 70)
    logger.info(f"Supported locales: {', '.join(SUPPORTED_LOCALES)}")
    logger.info(f"Default locale: {DEFAULT_LOCALE}")
    logger.info(f"RTL languages: {', '.join(RTL_LOCALES)}")
    logger.info(f"Translations directory: {TRANSLATIONS_DIR}")
    
    # Create translations directory if it doesn't exist
    TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured translations directory exists: {TRANSLATIONS_DIR}")
    
    # Pre-load default locale for performance
    try:
        get_translations(DEFAULT_LOCALE)
        logger.info(f"Pre-loaded default locale: {DEFAULT_LOCALE}")
    except Exception as e:
        logger.error(f"Failed to pre-load default locale: {e}")
    
    logger.info("i18n system initialized successfully ✓")
    logger.info("=" * 70)


# =============================================================================
# Translation Metrics (for monitoring)
# =============================================================================

class TranslationMetrics:
    """Track translation usage for monitoring and analytics"""
    
    def __init__(self):
        self.translation_counts: Dict[str, int] = {}
        self.missing_translations: set = set()
        self.errors: List[Dict[str, Any]] = []
    
    def record_translation(self, message: str, locale: str) -> None:
        """Record a translation request"""
        key = f"{locale}:{message}"
        self.translation_counts[key] = self.translation_counts.get(key, 0) + 1
    
    def record_missing(self, message: str, locale: str) -> None:
        """Record a missing translation"""
        self.missing_translations.add(f"{locale}:{message}")
        logger.warning(f"Missing translation [{locale}]: {message}")
    
    def record_error(self, error: str, locale: str, context: Dict[str, Any]) -> None:
        """Record a translation error"""
        self.errors.append({
            "error": error,
            "locale": locale,
            "context": context,
            "timestamp": datetime.now()
        })
        logger.error(f"Translation error [{locale}]: {error}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get translation statistics"""
        return {
            "total_translations": sum(self.translation_counts.values()),
            "unique_keys": len(self.translation_counts),
            "missing_count": len(self.missing_translations),
            "missing_keys": list(self.missing_translations),
            "error_count": len(self.errors),
            "errors": self.errors[-10:]  # Last 10 errors
        }
    
    def reset(self) -> None:
        """Reset all metrics"""
        self.translation_counts.clear()
        self.missing_translations.clear()
        self.errors.clear()


# Global metrics instance
metrics = TranslationMetrics()


# =============================================================================
# Export All Public Functions
# =============================================================================

__all__ = [
    # Core functions
    "init_i18n",
    "get_current_locale",
    "set_locale",
    "get_translations",
    "clear_translations_cache",
    
    # Translation functions
    "gettext",
    "ngettext",
    "pgettext",
    "_",
    "_n",
    "_p",
    
    # Formatting functions
    "format_date",
    "format_datetime",
    "format_time",
    "format_number",
    "format_currency",
    "format_percentage",
    
    # Utility functions
    "get_available_locales",
    "is_rtl",
    "get_locale_info",
    
    # Constants
    "SUPPORTED_LOCALES",
    "DEFAULT_LOCALE",
    "RTL_LOCALES",
    
    # Classes
    "LocaleConfig",
    "TranslationMetrics",
    
    # Metrics
    "metrics",
]
