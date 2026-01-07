"""
Translation Service Core Module
Unified interface for multiple translation providers

Version: 1.0
License: MIT
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
import hashlib
import json

logger = logging.getLogger(__name__)


# =============================================================================
# Base Translation Provider Interface
# =============================================================================

class TranslationProvider(ABC):
    """Abstract base class for translation providers"""
    
    def __init__(self, api_key: Optional[str] = None, **config):
        """
        Initialize translation provider
        
        Args:
            api_key: API key for the service
            **config: Additional configuration options
        """
        self.api_key = api_key
        self.config = config
        self.provider_name = self.__class__.__name__
        self._initialize()
    
    @abstractmethod
    def _initialize(self):
        """Initialize provider-specific settings"""
        pass
    
    @abstractmethod
    def translate_text(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """
        Translate a single text string
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Translated text
        """
        pass
    
    @abstractmethod
    def translate_batch(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str
    ) -> List[str]:
        """
        Translate multiple texts in batch (more efficient)
        
        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            List of translated texts
        """
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """Get list of supported language codes"""
        pass
    
    @abstractmethod
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics (characters translated, cost, etc.)"""
        pass
    
    def estimate_cost(self, char_count: int) -> float:
        """
        Estimate cost for translating character count
        
        Args:
            char_count: Number of characters
            
        Returns:
            Estimated cost in USD
        """
        # Default implementation - override in provider
        return 0.0


# =============================================================================
# Translation Manager
# =============================================================================

class TranslationManager:
    """
    Main translation manager with caching and multiple provider support
    """
    
    def __init__(
        self,
        provider: TranslationProvider,
        cache_dir: Optional[Path] = None,
        enable_cache: bool = True
    ):
        """
        Initialize translation manager
        
        Args:
            provider: Translation provider instance
            cache_dir: Directory for caching translations
            enable_cache: Enable/disable caching
        """
        self.provider = provider
        self.enable_cache = enable_cache
        
        # Setup cache directory
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / "cache"
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache file
        self.cache_file = self.cache_dir / "translation_cache.json"
        self._load_cache()
        
        # Statistics
        self.stats = {
            "translations_requested": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "characters_translated": 0,
            "api_calls": 0,
            "errors": 0
        }
        
        logger.info(f"TranslationManager initialized with {provider.provider_name}")
        logger.info(f"Cache enabled: {enable_cache}, Cache dir: {self.cache_dir}")
    
    def _load_cache(self):
        """Load translation cache from file"""
        self.cache = {}
        if self.cache_file.exists() and self.enable_cache:
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                logger.info(f"Loaded {len(self.cache)} cached translations")
            except Exception as e:
                logger.error(f"Failed to load cache: {e}")
                self.cache = {}
    
    def _save_cache(self):
        """Save translation cache to file"""
        if not self.enable_cache:
            return
        
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved {len(self.cache)} translations to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _get_cache_key(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """Generate cache key for translation"""
        # Use hash for efficient lookup
        content = f"{source_lang}:{target_lang}:{text}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        use_cache: bool = True
    ) -> str:
        """
        Translate a single text with caching
        
        Args:
            text: Text to translate
            source_lang: Source language code
            target_lang: Target language code
            use_cache: Use cache if available
            
        Returns:
            Translated text
        """
        self.stats["translations_requested"] += 1
        
        # Check cache first
        if use_cache and self.enable_cache:
            cache_key = self._get_cache_key(text, source_lang, target_lang)
            if cache_key in self.cache:
                self.stats["cache_hits"] += 1
                logger.debug(f"Cache hit for: {text[:50]}...")
                return self.cache[cache_key]
            self.stats["cache_misses"] += 1
        
        # Translate via API
        try:
            translated = self.provider.translate_text(text, source_lang, target_lang)
            self.stats["api_calls"] += 1
            self.stats["characters_translated"] += len(text)
            
            # Cache result
            if self.enable_cache:
                cache_key = self._get_cache_key(text, source_lang, target_lang)
                self.cache[cache_key] = translated
                self._save_cache()
            
            logger.debug(f"Translated: {text[:50]}... -> {translated[:50]}...")
            return translated
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Translation failed: {e}")
            raise
    
    def translate_batch(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str,
        use_cache: bool = True
    ) -> List[str]:
        """
        Translate multiple texts efficiently with caching
        
        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            use_cache: Use cache if available
            
        Returns:
            List of translated texts
        """
        if not texts:
            return []
        
        results = []
        to_translate = []
        to_translate_indices = []
        
        # Check cache for each text
        for i, text in enumerate(texts):
            self.stats["translations_requested"] += 1
            
            if use_cache and self.enable_cache:
                cache_key = self._get_cache_key(text, source_lang, target_lang)
                if cache_key in self.cache:
                    results.append(self.cache[cache_key])
                    self.stats["cache_hits"] += 1
                    continue
                self.stats["cache_misses"] += 1
            
            # Mark for translation
            to_translate.append(text)
            to_translate_indices.append(i)
            results.append(None)  # Placeholder
        
        # Translate uncached texts in batch
        if to_translate:
            try:
                translated = self.provider.translate_batch(
                    to_translate,
                    source_lang,
                    target_lang
                )
                self.stats["api_calls"] += 1
                self.stats["characters_translated"] += sum(len(t) for t in to_translate)
                
                # Insert translated texts and cache them
                for i, idx in enumerate(to_translate_indices):
                    results[idx] = translated[i]
                    
                    if self.enable_cache:
                        cache_key = self._get_cache_key(
                            to_translate[i],
                            source_lang,
                            target_lang
                        )
                        self.cache[cache_key] = translated[i]
                
                # Save cache after batch
                if self.enable_cache:
                    self._save_cache()
                
                logger.info(f"Batch translated {len(to_translate)} texts")
                
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"Batch translation failed: {e}")
                raise
        
        return results
    
    def translate_dict(
        self,
        translations: Dict[str, str],
        source_lang: str,
        target_lang: str,
        skip_existing: bool = True
    ) -> Dict[str, str]:
        """
        Translate a dictionary of key-value pairs
        
        Args:
            translations: Dict of translation keys and source texts
            source_lang: Source language code
            target_lang: Target language code
            skip_existing: Skip keys that already have translations
            
        Returns:
            Dict with translated values
        """
        if not translations:
            return {}
        
        # Prepare batch
        keys = []
        texts = []
        
        for key, text in translations.items():
            if skip_existing and text:
                continue  # Skip if already translated
            keys.append(key)
            texts.append(text)
        
        if not texts:
            logger.info("No texts to translate (all already exist)")
            return translations
        
        # Translate batch
        logger.info(f"Translating {len(texts)} keys from {source_lang} to {target_lang}")
        translated_texts = self.translate_batch(texts, source_lang, target_lang)
        
        # Build result dict
        result = translations.copy()
        for i, key in enumerate(keys):
            result[key] = translated_texts[i]
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """Get translation statistics"""
        stats = self.stats.copy()
        
        # Add cache efficiency
        total_requests = stats["translations_requested"]
        if total_requests > 0:
            stats["cache_hit_rate"] = (stats["cache_hits"] / total_requests) * 100
        else:
            stats["cache_hit_rate"] = 0.0
        
        # Add provider stats
        try:
            stats["provider_stats"] = self.provider.get_usage_stats()
        except Exception as e:
            logger.warning(f"Could not get provider stats: {e}")
            stats["provider_stats"] = {}
        
        # Add cost estimate
        stats["estimated_cost_usd"] = self.provider.estimate_cost(
            stats["characters_translated"]
        )
        
        return stats
    
    def clear_cache(self):
        """Clear translation cache"""
        self.cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
        logger.info("Translation cache cleared")
    
    def export_cache(self, output_file: Path):
        """Export cache to file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, ensure_ascii=False)
        logger.info(f"Cache exported to {output_file}")


# =============================================================================
# Convenience Functions
# =============================================================================

def create_translation_manager(
    provider_name: str,
    api_key: Optional[str] = None,
    **config
) -> TranslationManager:
    """
    Factory function to create translation manager
    
    Args:
        provider_name: Name of provider ('google', 'deepl', 'azure', 'aws', 'libre')
        api_key: API key for the service
        **config: Additional configuration
        
    Returns:
        TranslationManager instance
    """
    from .providers import (
        GoogleTranslateProvider,
        DeepLProvider,
        AzureTranslatorProvider,
        AWSTranslateProvider,
        LibreTranslateProvider
    )
    
    providers = {
        'google': GoogleTranslateProvider,
        'deepl': DeepLProvider,
        'azure': AzureTranslatorProvider,
        'aws': AWSTranslateProvider,
        'libre': LibreTranslateProvider
    }
    
    if provider_name.lower() not in providers:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available: {', '.join(providers.keys())}"
        )
    
    provider_class = providers[provider_name.lower()]
    provider = provider_class(api_key=api_key, **config)
    
    return TranslationManager(provider)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    'TranslationProvider',
    'TranslationManager',
    'create_translation_manager',
]
