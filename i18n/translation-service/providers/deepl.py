"""
DeepL API Provider

Version: 1.0
License: MIT
"""

import logging
from typing import List, Dict, Any, Optional
from ..core.translator import TranslationProvider

logger = logging.getLogger(__name__)


class DeepLProvider(TranslationProvider):
    """
    DeepL API provider
    
    Features:
    - Highest quality translations
    - 30+ languages
    - Preferred by professional translators
    - €20 per 1M characters
    
    Setup:
    1. Sign up at https://www.deepl.com/pro-api
    2. Get API key from account settings
    3. Choose Free or Pro plan
    """
    
    def _initialize(self):
        """Initialize DeepL client"""
        if not self.api_key:
            raise ValueError("DeepL API key is required")
        
        try:
            import deepl
            
            # Initialize client
            self.client = deepl.Translator(self.api_key)
            
            self.characters_translated = 0
            self.api_calls = 0
            
            # Test connection
            usage = self.client.get_usage()
            logger.info(f"DeepL provider initialized")
            logger.info(f"Account limit: {usage.character.limit:,} characters")
            logger.info(f"Characters used: {usage.character.count:,}")
            
        except ImportError:
            raise ImportError(
                "DeepL library not installed. "
                "Install with: pip install deepl"
            )
        except Exception as e:
            logger.error(f"Failed to initialize DeepL: {e}")
            raise
    
    def _convert_lang_code(self, lang: str, for_source: bool = False) -> str:
        """
        Convert standard language codes to DeepL format
        
        DeepL uses specific codes:
        - EN -> EN-US or EN-GB
        - PT -> PT-BR or PT-PT
        """
        # DeepL specific mappings
        mappings = {
            'en': 'EN-US',  # Can also be EN-GB
            'pt': 'PT-PT',  # Can also be PT-BR
            'zh': 'ZH',     # Simplified Chinese
        }
        
        # For source language, some codes are different
        if for_source:
            source_mappings = {
                'en': 'EN',
                'pt': 'PT',
            }
            return source_mappings.get(lang.lower(), lang.upper())
        
        return mappings.get(lang.lower(), lang.upper())
    
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
            # Convert language codes
            source = self._convert_lang_code(source_lang, for_source=True)
            target = self._convert_lang_code(target_lang, for_source=False)
            
            result = self.client.translate_text(
                text,
                source_lang=source,
                target_lang=target,
                preserve_formatting=True
            )
            
            self.api_calls += 1
            self.characters_translated += len(text)
            
            return result.text
            
        except Exception as e:
            logger.error(f"DeepL error: {e}")
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
            # Convert language codes
            source = self._convert_lang_code(source_lang, for_source=True)
            target = self._convert_lang_code(target_lang, for_source=False)
            
            # DeepL supports batch translation
            results = self.client.translate_text(
                non_empty_texts,
                source_lang=source,
                target_lang=target,
                preserve_formatting=True
            )
            
            self.api_calls += 1
            self.characters_translated += sum(len(t) for t in non_empty_texts)
            
            # Build result preserving empty texts
            translated = list(texts)  # Copy original
            for i, idx in enumerate(non_empty_indices):
                translated[idx] = results[i].text
            
            return translated
            
        except Exception as e:
            logger.error(f"DeepL batch error: {e}")
            raise
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        try:
            # Get source and target languages
            source_langs = self.client.get_source_languages()
            target_langs = self.client.get_target_languages()
            
            # Combine and normalize
            all_langs = set()
            for lang in source_langs:
                all_langs.add(lang.code.split('-')[0].lower())
            for lang in target_langs:
                all_langs.add(lang.code.split('-')[0].lower())
            
            return sorted(list(all_langs))
            
        except Exception as e:
            logger.error(f"Failed to get supported languages: {e}")
            return []
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        stats = {
            "provider": "DeepL",
            "api_calls": self.api_calls,
            "characters_translated": self.characters_translated,
            "estimated_cost_usd": self.estimate_cost(self.characters_translated)
        }
        
        # Get account usage
        try:
            usage = self.client.get_usage()
            stats["account_limit"] = usage.character.limit
            stats["account_used"] = usage.character.count
            stats["account_remaining"] = usage.character.limit - usage.character.count
            
            if usage.character.limit:
                stats["account_usage_percent"] = (
                    usage.character.count / usage.character.limit
                ) * 100
            
        except Exception as e:
            logger.warning(f"Could not get DeepL usage stats: {e}")
        
        return stats
    
    def estimate_cost(self, char_count: int) -> float:
        """
        Estimate cost for character count
        
        DeepL pricing:
        - Free: 500,000 characters/month (free)
        - Pro: €20 per 1M characters (~$22 USD)
        """
        return (char_count / 1_000_000) * 22.0


__all__ = ['DeepLProvider']
