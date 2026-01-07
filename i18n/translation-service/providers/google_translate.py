"""
Google Cloud Translation API Provider

Version: 1.0
License: MIT
"""

import logging
from typing import List, Dict, Any, Optional
from ..core.translator import TranslationProvider

logger = logging.getLogger(__name__)


class GoogleTranslateProvider(TranslationProvider):
    """
    Google Cloud Translation API provider
    
    Features:
    - 100+ languages
    - Neural Machine Translation
    - High quality
    - ~$20 per 1M characters
    
    Setup:
    1. Enable Cloud Translation API in Google Cloud Console
    2. Create service account and download JSON key
    3. Set GOOGLE_APPLICATION_CREDENTIALS env var
    
    Or provide API key directly
    """
    
    def _initialize(self):
        """Initialize Google Translate client"""
        try:
            from google.cloud import translate_v2 as translate
            
            # Initialize client
            if self.api_key:
                self.client = translate.Client(api_key=self.api_key)
            else:
                # Use default credentials from environment
                self.client = translate.Client()
            
            self.characters_translated = 0
            self.api_calls = 0
            
            logger.info("Google Translate provider initialized")
            
        except ImportError:
            raise ImportError(
                "Google Cloud Translate library not installed. "
                "Install with: pip install google-cloud-translate"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Google Translate: {e}")
            raise
    
    def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """Translate single text"""
        if not text or not text.strip():
            return text
        
        try:
            result = self.client.translate(
                text,
                source_language=source_lang,
                target_language=target_lang,
                format_='text'
            )
            
            self.api_calls += 1
            self.characters_translated += len(text)
            
            return result['translatedText']
            
        except Exception as e:
            logger.error(f"Google Translate error: {e}")
            raise
    
    def translate_batch(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str
    ) -> List[str]:
        """Translate multiple texts in batch"""
        if not texts:
            return []
        
        # Filter empty texts but preserve positions
        non_empty_indices = []
        non_empty_texts = []
        
        for i, text in enumerate(texts):
            if text and text.strip():
                non_empty_indices.append(i)
                non_empty_texts.append(text)
        
        if not non_empty_texts:
            return texts
        
        try:
            # Google Translate supports batch translation
            results = self.client.translate(
                non_empty_texts,
                source_language=source_lang,
                target_language=target_lang,
                format_='text'
            )
            
            self.api_calls += 1
            self.characters_translated += sum(len(t) for t in non_empty_texts)
            
            # Build result preserving empty texts
            translated = list(texts)  # Copy original
            for i, idx in enumerate(non_empty_indices):
                translated[idx] = results[i]['translatedText']
            
            return translated
            
        except Exception as e:
            logger.error(f"Google Translate batch error: {e}")
            raise
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        try:
            results = self.client.get_languages()
            return [lang['language'] for lang in results]
        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            return []
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "provider": "Google Cloud Translation",
            "api_calls": self.api_calls,
            "characters_translated": self.characters_translated,
            "estimated_cost_usd": self.estimate_cost(self.characters_translated)
        }
    
    def estimate_cost(self, char_count: int) -> float:
        """
        Estimate cost for character count
        
        Google Cloud Translation pricing:
        - $20 per 1M characters
        """
        return (char_count / 1_000_000) * 20.0


__all__ = ['GoogleTranslateProvider']
