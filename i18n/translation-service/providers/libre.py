"""
LibreTranslate API Provider (Open Source)

Version: 1.0
License: MIT
"""

import logging
import requests
from typing import List, Dict, Any, Optional
from ..core.translator import TranslationProvider

logger = logging.getLogger(__name__)


class LibreTranslateProvider(TranslationProvider):
    """
    LibreTranslate API provider (Open Source, Self-Hosted)
    
    Features:
    - FREE (self-hosted)
    - 30+ languages
    - Privacy-friendly (your own server)
    - Lower quality than commercial options
    
    Setup:
    Option 1 - Use public API (limited):
    - api_url: https://libretranslate.com
    - Free tier: 20 requests/day
    
    Option 2 - Self-hosted (recommended):
    - Docker: docker run -ti --rm -p 5000:5000 libretranslate/libretranslate
    - api_url: http://localhost:5000
    - Unlimited usage
    
    Option 3 - Managed hosting:
    - Get API key from libretranslate.com
    - Pay for usage
    """
    
    def _initialize(self):
        """Initialize LibreTranslate client"""
        # API endpoint
        self.api_url = self.config.get('api_url', 'https://libretranslate.com')
        if not self.api_url.endswith('/'):
            self.api_url += '/'
        
        # API key (optional for self-hosted)
        self.api_key = self.api_key or self.config.get('api_key')
        
        self.characters_translated = 0
        self.api_calls = 0
        
        # Test connection
        try:
            response = requests.get(
                f"{self.api_url}languages",
                timeout=5
            )
            response.raise_for_status()
            logger.info(f"LibreTranslate provider initialized: {self.api_url}")
        except Exception as e:
            logger.warning(f"Could not connect to LibreTranslate: {e}")
            logger.info("Proceeding anyway - will fail on first translation if unreachable")
    
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
            # Prepare request
            data = {
                'q': text,
                'source': source_lang,
                'target': target_lang,
                'format': 'text'
            }
            
            # Add API key if available
            if self.api_key:
                data['api_key'] = self.api_key
            
            # Make request
            response = requests.post(
                f"{self.api_url}translate",
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            self.api_calls += 1
            self.characters_translated += len(text)
            
            return result['translatedText']
            
        except requests.exceptions.RequestException as e:
            logger.error(f"LibreTranslate API error: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"LibreTranslate error: {e}")
            raise
    
    def translate_batch(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str
    ) -> List[str]:
        """
        Translate multiple texts
        
        Note: LibreTranslate doesn't have native batch support,
        so we translate one by one (less efficient)
        """
        if not texts:
            return []
        
        translated = []
        
        for text in texts:
            if not text or not text.strip():
                translated.append(text)
            else:
                try:
                    result = self.translate_text(text, source_lang, target_lang)
                    translated.append(result)
                except Exception as e:
                    logger.error(f"Failed to translate: {text[:50]}...")
                    # Keep original on error
                    translated.append(text)
        
        return translated
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        try:
            response = requests.get(
                f"{self.api_url}languages",
                timeout=10
            )
            response.raise_for_status()
            
            languages = response.json()
            return [lang['code'] for lang in languages]
            
        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            return []
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "provider": "LibreTranslate",
            "api_url": self.api_url,
            "api_calls": self.api_calls,
            "characters_translated": self.characters_translated,
            "estimated_cost_usd": 0.0,  # Free (self-hosted)
            "note": "Self-hosted = free, Public API = limited"
        }
    
    def estimate_cost(self, char_count: int) -> float:
        """
        Estimate cost for character count
        
        LibreTranslate:
        - Self-hosted: Free
        - Public API: Free tier then paid
        """
        if self.api_url == "https://libretranslate.com":
            # Using public API - has paid tiers
            return (char_count / 1_000_000) * 10.0
        else:
            # Self-hosted - free
            return 0.0


__all__ = ['LibreTranslateProvider']
