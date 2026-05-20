"""
Real-time translation service for dynamic user content
WITH COMPREHENSIVE DEBUG LOGGING
"""

from typing import Optional, Dict, Any
import logging
import sys

logger = logging.getLogger(__name__)

# Force INFO level for this module
logger.setLevel(logging.INFO)

logger.info("=" * 60)
logger.info("INITIALIZING REALTIME TRANSLATION MODULE")
logger.info("=" * 60)

# ============================================================================
# Translation Service Import
# ============================================================================

_translation_service_available = False

try:
    logger.info("Attempting to import translation service...")
    # from i18n.translation_service.core.translator import create_translation_manager
    import sys
    from pathlib import Path

    # Add i18n to path
    i18n_path = Path(__file__).parent.parent.parent.parent / "i18n"
    sys.path.insert(0, str(i18n_path))

    # Now import from the hyphenated directory
    sys.path.insert(0, str(i18n_path / "translation_service"))
    from core.translator import create_translation_manager
    _translation_service_available = True
    logger.info("✓ Successfully imported translation service")
except ImportError as e:
    logger.error(f"✗ Failed to import translation service: {e}")
    logger.error(f"Python path: {sys.path[:5]}")
    
    def create_translation_manager(*args, **kwargs):
        logger.warning("Translation service not available (dummy function)")
        return None

# ============================================================================
# Import i18n helpers
# ============================================================================

try:
    from backend.core.i18n import get_current_locale
    logger.info("✓ Imported get_current_locale")
except ImportError as e:
    logger.warning(f"Failed to import get_current_locale: {e}")
    def get_current_locale():
        return "en"

# ============================================================================
# Configuration
# ============================================================================

USE_PROVIDER = "libre"
LIBRETRANSLATE_URL = "http://localhost:5000"
ENABLE_REALTIME_TRANSLATION = True

logger.info(f"Configuration:")
logger.info(f"  Provider: {USE_PROVIDER}")
logger.info(f"  URL: {LIBRETRANSLATE_URL}")
logger.info(f"  Enabled: {ENABLE_REALTIME_TRANSLATION}")
logger.info(f"  Service Available: {_translation_service_available}")

# ============================================================================
# Translation Manager Singleton
# ============================================================================

_translation_manager = None
_initialization_attempted = False


def get_translation_manager():
    """Get or create translation manager instance (singleton)"""
    global _translation_manager, _initialization_attempted

    logger.debug("get_translation_manager() called")

    if not ENABLE_REALTIME_TRANSLATION:
        logger.warning("Real-time translation is DISABLED")
        return None

    if not _translation_service_available:
        if not _initialization_attempted:
            logger.warning("Translation service module NOT AVAILABLE")
            _initialization_attempted = True
        return None

    if _translation_manager is not None:
        logger.debug("Returning cached translation manager")
        return _translation_manager

    if _initialization_attempted:
        logger.warning("Already attempted initialization and failed")
        return None

    _initialization_attempted = True

    try:
        logger.info("=" * 60)
        logger.info(f"INITIALIZING TRANSLATION MANAGER")
        logger.info(f"Provider: {USE_PROVIDER}")
        logger.info("=" * 60)

        if USE_PROVIDER == "libre":
            logger.info(f"Creating LibreTranslate manager with URL: {LIBRETRANSLATE_URL}")
            
            _translation_manager = create_translation_manager(
                provider_name="libre",
                api_url=LIBRETRANSLATE_URL,
            )
            
            if _translation_manager:
                logger.info("✓✓✓ Translation manager SUCCESSFULLY initialized! ✓✓✓")
                logger.info(f"Manager type: {type(_translation_manager)}")
            else:
                logger.error("✗✗✗ Translation manager returned None! ✗✗✗")

        else:
            logger.error(f"Unknown provider: {USE_PROVIDER}")
            return None

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗✗✗ FAILED TO INITIALIZE TRANSLATION MANAGER ✗✗✗")
        logger.error(f"Error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error("=" * 60)
        import traceback
        logger.error(traceback.format_exc())
        _translation_manager = None

    return _translation_manager


# ============================================================================
# Translation Functions
# ============================================================================

def translate_text_realtime(
    text: str,
    target_lang: Optional[str] = None,
    source_lang: str = "en",
) -> str:
    """Translate text in real-time for dynamic user content"""
    logger.info("=" * 60)
    logger.info("translate_text_realtime() CALLED")
    logger.info(f"Text: '{text[:50]}...'")
    logger.info(f"Target lang: {target_lang}")
    logger.info(f"Source lang: {source_lang}")
    target_lang = FORCE_TARGET_LANG
    if not text or not text.strip():
        logger.warning("Text is empty, returning as-is")
        return text

    if target_lang is None:
        try:
            target_lang = get_current_locale()
            logger.info(f"Auto-detected target lang: {target_lang}")
        except Exception as e:
            logger.error(f"Failed to get locale: {e}")
            target_lang = "en"

    if target_lang == source_lang:
        logger.info(f"Target ({target_lang}) == Source ({source_lang}), skipping")
        return text

    logger.info("Getting translation manager...")
    manager = get_translation_manager()
    
    if manager is None:
        logger.error("✗✗✗ Translation manager is None! ✗✗✗")
        logger.error("Real-time translation UNAVAILABLE")
        return text
    
    logger.info(f"✓ Got translation manager: {type(manager)}")

    try:
        logger.info(f"Calling manager.translate()...")
        translated = manager.translate(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
        )
        logger.info("=" * 60)
        logger.info("✓✓✓ TRANSLATION SUCCESSFUL! ✓✓✓")
        logger.info(f"Original:    '{text[:50]}...'")
        logger.info(f"Translated:  '{translated[:50]}...'")
        logger.info("=" * 60)
        return translated
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗✗✗ TRANSLATION FAILED! ✗✗✗")
        logger.error(f"Error: {e}")
        logger.error("=" * 60)
        return text


# def should_translate(target_lang: Optional[str] = None) -> bool:
#     """Check if translation should be performed"""
#     logger.info("=" * 60)
#     logger.info("should_translate() CALLED")
    
#     if not ENABLE_REALTIME_TRANSLATION:
#         logger.warning("Translation DISABLED in config")
#         return False

#     if target_lang is None:
#         try:
#             target_lang = get_current_locale()
#             logger.info(f"Current locale: {target_lang}")
#         except Exception as e:
#             logger.error(f"Failed to get locale: {e}")
#             target_lang = "en"

#     if target_lang == "en":
#         logger.info("Target is English, no translation needed")
#         return False

#     manager = get_translation_manager()
#     available = manager is not None
    
#     logger.info(f"Translation manager available: {available}")
#     logger.info("=" * 60)
    
#     return available

FORCE_TARGET_LANG = "es"
def should_translate(target_lang: Optional[str] = None) -> bool:
    logger.info("=" * 60)
    logger.info("should_translate() CALLED")

    if not ENABLE_REALTIME_TRANSLATION:
        logger.warning("Translation DISABLED in config")
        return False

    # 🔥 HARD OVERRIDE (TEMP)
    target_lang = FORCE_TARGET_LANG
    logger.info(f"FORCED target language: {target_lang}")

    if target_lang == "en":
        logger.info("Target is English, no translation needed")
        return False

    manager = get_translation_manager()
    available = manager is not None

    logger.info(f"Translation manager available: {available}")
    logger.info("=" * 60)
    return available

def translate_dict_fields(
    data: Dict[str, Any],
    fields: list[str],
    target_lang: Optional[str] = None,
    source_lang: str = "en",
) -> Dict[str, Any]:
    """Translate specific fields in a dictionary"""
    result = data.copy()

    for field in fields:
        if field in result and result[field]:
            result[field] = translate_text_realtime(
                str(result[field]),
                target_lang=target_lang,
                source_lang=source_lang,
            )

    return result


def translate_batch_realtime(
    texts: list[str],
    target_lang: Optional[str] = None,
    source_lang: str = "en",
) -> list[str]:
    """Translate multiple texts in one API call"""
    if not texts:
        return []

    if target_lang is None:
        try:
            target_lang = get_current_locale()
        except Exception:
            target_lang = "en"

    if target_lang == source_lang:
        return texts

    manager = get_translation_manager()
    if manager is None:
        return texts

    try:
        return manager.translate_batch(
            texts=texts,
            source_lang=source_lang,
            target_lang=target_lang,
        )
    except Exception as e:
        logger.error(f"Batch translation failed: {e}")
        return texts


def get_translation_stats() -> Dict[str, Any]:
    """Get translation service statistics"""
    manager = get_translation_manager()
    if manager is None:
        return {
            "enabled": False,
            "available": _translation_service_available,
            "reason": "Translation manager not initialized",
        }

    try:
        stats = manager.get_stats()
        stats["enabled"] = True
        stats["provider"] = USE_PROVIDER
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return {
            "enabled": True,
            "provider": USE_PROVIDER,
            "error": str(e),
        }


logger.info("=" * 60)
logger.info("REALTIME TRANSLATION MODULE LOADED")
logger.info("=" * 60)