# """
# LibreTranslate API Provider (Open Source)

# Version: 1.0
# License: MIT
# """

# import logging
# import requests
# from typing import List, Dict, Any, Optional
# # from ..core.translator import TranslationProvider
# from core.translator import TranslationProvider

# logger = logging.getLogger(__name__)


# class LibreTranslateProvider(TranslationProvider):
#     """
#     LibreTranslate API provider (Open Source, Self-Hosted)
    
#     Features:
#     - FREE (self-hosted)
#     - 30+ languages
#     - Privacy-friendly (your own server)
#     - Lower quality than commercial options
    
#     Setup:
#     Option 1 - Use public API (limited):
#     - api_url: https://libretranslate.com
#     - Free tier: 20 requests/day
    
#     Option 2 - Self-hosted (recommended):
#     - Docker: docker run -ti --rm -p 5000:5000 libretranslate/libretranslate
#     - api_url: http://localhost:5000
#     - Unlimited usage
    
#     Option 3 - Managed hosting:
#     - Get API key from libretranslate.com
#     - Pay for usage
#     """
    
#     def _initialize(self):
#         """Initialize LibreTranslate client"""
#         # API endpoint
#         self.api_url = self.config.get('api_url', 'https://libretranslate.com')
#         if not self.api_url.endswith('/'):
#             self.api_url += '/'
        
#         # API key (optional for self-hosted)
#         self.api_key = self.api_key or self.config.get('api_key')
        
#         self.characters_translated = 0
#         self.api_calls = 0
        
#         # Test connection
#         try:
#             response = requests.get(
#                 f"{self.api_url}languages",
#                 timeout=5
#             )
#             response.raise_for_status()
#             logger.info(f"LibreTranslate provider initialized: {self.api_url}")
#         except Exception as e:
#             logger.warning(f"Could not connect to LibreTranslate: {e}")
#             logger.info("Proceeding anyway - will fail on first translation if unreachable")
    
#     def translate_text(
#         self,
#         text: str,
#         source_lang: str,
#         target_lang: str
#     ) -> str:
#         """Translate single text"""
#         if not text or not text.strip():
#             return text
        
#         try:
#             # Prepare request
#             data = {
#                 'q': text,
#                 'source': source_lang,
#                 'target': target_lang,
#                 'format': 'text'
#             }
            
#             # Add API key if available
#             if self.api_key:
#                 data['api_key'] = self.api_key
            
#             # Make request
#             response = requests.post(
#                 f"{self.api_url}translate",
#                 json=data,
#                 timeout=30
#             )
#             response.raise_for_status()
            
#             result = response.json()
            
#             self.api_calls += 1
#             self.characters_translated += len(text)
            
#             return result['translatedText']
            
#         except requests.exceptions.RequestException as e:
#             logger.error(f"LibreTranslate API error: {e}")
#             if hasattr(e.response, 'text'):
#                 logger.error(f"Response: {e.response.text}")
#             raise
#         except Exception as e:
#             logger.error(f"LibreTranslate error: {e}")
#             raise
    
#     def translate_batch(
#         self,
#         texts: List[str],
#         source_lang: str,
#         target_lang: str
#     ) -> List[str]:
#         """
#         Translate multiple texts
        
#         Note: LibreTranslate doesn't have native batch support,
#         so we translate one by one (less efficient)
#         """
#         if not texts:
#             return []
        
#         translated = []
        
#         for text in texts:
#             if not text or not text.strip():
#                 translated.append(text)
#             else:
#                 try:
#                     result = self.translate_text(text, source_lang, target_lang)
#                     translated.append(result)
#                 except Exception as e:
#                     logger.error(f"Failed to translate: {text[:50]}...")
#                     # Keep original on error
#                     translated.append(text)
        
#         return translated
    
#     def get_supported_languages(self) -> List[str]:
#         """Get list of supported language codes"""
#         try:
#             response = requests.get(
#                 f"{self.api_url}languages",
#                 timeout=10
#             )
#             response.raise_for_status()
            
#             languages = response.json()
#             return [lang['code'] for lang in languages]
            
#         except Exception as e:
#             logger.error(f"Failed to get supported languages: {e}")
#             return []
    
#     def get_usage_stats(self) -> Dict[str, Any]:
#         """Get usage statistics"""
#         return {
#             "provider": "LibreTranslate",
#             "api_url": self.api_url,
#             "api_calls": self.api_calls,
#             "characters_translated": self.characters_translated,
#             "estimated_cost_usd": 0.0,  # Free (self-hosted)
#             "note": "Self-hosted = free, Public API = limited"
#         }
    
#     def estimate_cost(self, char_count: int) -> float:
#         """
#         Estimate cost for character count
        
#         LibreTranslate:
#         - Self-hosted: Free
#         - Public API: Free tier then paid
#         """
#         if self.api_url == "https://libretranslate.com":
#             # Using public API - has paid tiers
#             return (char_count / 1_000_000) * 10.0
#         else:
#             # Self-hosted - free
#             return 0.0


# __all__ = ['LibreTranslateProvider']


"""
LibreTranslate Provider with Language Code Mapping
Fixed to use ISO 639-3 codes that LibreTranslate expects
"""

import requests
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class LibreTranslateProvider:
    """LibreTranslate translation provider"""
    
    # Map ISO 639-1 codes (what we use) to LibreTranslate codes
    LANGUAGE_CODE_MAP = {
        "en": "en",     # English
        "es": "es",     # Spanish (try "es" first)
        "fr": "fr",     # French
        "de": "de",     # German
        "ar": "ar",     # Arabic
        "ja": "ja",     # Japanese
        "zh": "zh",     # Chinese
    }
    
    def __init__(self, api_key: Optional[str] = None, api_url: str = "http://localhost:5000"):
        """
        Initialize LibreTranslate provider
        
        Args:
            api_key: Optional API key (for self-hosted with auth)
            api_url: Base URL for LibreTranslate API
        """
        self.api_key = api_key
        self.api_url = api_url.rstrip('/')
        self.translate_endpoint = f"{self.api_url}/translate"
        self.languages_endpoint = f"{self.api_url}/languages"
        self.provider_name = "LibreTranslate"
        
        # Statistics
        self.chars_translated = 0
        self.requests_made = 0
        
        logger.info(f"LibreTranslate provider initialized: {self.api_url}")
        
        # Fetch and log available languages
        try:
            self._fetch_available_languages()
        except Exception as e:
            logger.warning(f"Could not fetch available languages: {e}")
    
    def _fetch_available_languages(self):
        """Fetch available languages from LibreTranslate"""
        try:
            response = requests.get(self.languages_endpoint, timeout=5)
            response.raise_for_status()
            languages = response.json()
            
            available = [lang.get('code') for lang in languages]
            logger.info(f"LibreTranslate available languages: {', '.join(available)}")
            
            # Update our mapping based on what's available
            for code in list(self.LANGUAGE_CODE_MAP.keys()):
                lt_code = self.LANGUAGE_CODE_MAP[code]
                if lt_code not in available:
                    logger.warning(f"Language {code} ({lt_code}) not available in LibreTranslate")
            
        except Exception as e:
            logger.error(f"Failed to fetch languages: {e}")
    
    def _map_language_code(self, code: str) -> str:
        """
        Map our language code to LibreTranslate code
        
        Args:
            code: ISO 639-1 code (e.g., 'es')
            
        Returns:
            LibreTranslate-compatible code
        """
        mapped = self.LANGUAGE_CODE_MAP.get(code, code)
        logger.debug(f"Mapped language code: {code} -> {mapped}")
        return mapped
    
    def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """
        Translate text using LibreTranslate
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Translated text
        """
        # Map language codes
        source_lang = self._map_language_code(source_lang)
        target_lang = self._map_language_code(target_lang)
        
        logger.info(f"Translating from {source_lang} to {target_lang}")
        logger.debug(f"Text to translate: {text[:100]}...")
        
        # Prepare request payload
        payload = {
            "q": text,
            "source": source_lang,
            "target": target_lang,
            "format": "text"
        }
        
        # Add API key if provided
        if self.api_key:
            payload["api_key"] = self.api_key
        
        try:
            # Make request
            response = requests.post(
                self.translate_endpoint,
                json=payload,
                timeout=120
            )
            
            # Check for errors
            if response.status_code != 200:
                error_msg = f"LibreTranslate API error: {response.status_code} {response.reason}"
                logger.error(error_msg)
                logger.error(f"Response: {response.text}")
                raise Exception(error_msg)
            
            # Parse response
            result = response.json()
            translated_text = result.get("translatedText", "")
            
            # Update statistics
            self.chars_translated += len(text)
            self.requests_made += 1
            
            logger.info(f"Translation successful: {translated_text[:100]}...")
            return translated_text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise
    
    def translate_batch(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str
    ) -> List[str]:
        """
        Translate multiple texts (LibreTranslate doesn't support batch, so we loop)
        
        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            List of translated texts
        """
        logger.info(f"Batch translating {len(texts)} texts")
        
        results = []
        for text in texts:
            try:
                translated = self.translate(text, source_lang, target_lang)
                results.append(translated)
            except Exception as e:
                logger.error(f"Failed to translate text in batch: {e}")
                results.append(text)  # Return original on error
        
        return results
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return list(self.LANGUAGE_CODE_MAP.keys())
    
    def get_usage_stats(self) -> dict:
        """Get usage statistics"""
        return {
            "provider": self.provider_name,
            "characters_translated": self.chars_translated,
            "requests_made": self.requests_made,
            "api_url": self.api_url
        }
    
    def estimate_cost(self, char_count: int) -> float:
        """
        Estimate cost (LibreTranslate is free)
        
        Args:
            char_count: Number of characters
            
        Returns:
            Cost in USD (always 0 for LibreTranslate)
        """
        return 0.0  # LibreTranslate is free!