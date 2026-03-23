"""
Translation Service Module (Optional Add-on)
Auto-translation capabilities for the i18n package

Version: 1.0
License: MIT
"""

from .core.translator import (
    TranslationProvider,
    TranslationManager,
    create_translation_manager
)

__version__ = '1.0.0'

__all__ = [
    'TranslationProvider',
    'TranslationManager',
    'create_translation_manager',
]
