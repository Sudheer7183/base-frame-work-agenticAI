"""
Translation Service Providers
"""

from .google_translate import GoogleTranslateProvider
from .deepl import DeepLProvider
from .libre import LibreTranslateProvider

# Placeholder imports for Azure and AWS
# These would be implemented similarly if needed

try:
    from .azure import AzureTranslatorProvider
except ImportError:
    class AzureTranslatorProvider:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError(
                "Azure Translator not implemented yet. "
                "Use Google, DeepL, or LibreTranslate for now."
            )

try:
    from .aws import AWSTranslateProvider
except ImportError:
    class AWSTranslateProvider:
        def __init__(self, *args, **kwargs):
            raise NotImplementedError(
                "AWS Translate not implemented yet. "
                "Use Google, DeepL, or LibreTranslate for now."
            )


__all__ = [
    'GoogleTranslateProvider',
    'DeepLProvider',
    'LibreTranslateProvider',
    'AzureTranslatorProvider',
    'AWSTranslateProvider',
]
