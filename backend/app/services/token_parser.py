"""
Token Parser Service - COMPLETE
Extracts token counts from various LLM provider responses

File: backend/app/services/token_parser.py
Version: 2.0 COMPLETE
INTEGRATION: Copy to backend/app/services/token_parser.py
"""

import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


class TokenParser:
    """
    Parse token usage from different LLM providers
    
    Supports:
    - OpenAI (GPT-3.5, GPT-4, GPT-4o)
    - Anthropic (Claude 3, Claude 3.5)
    - LangChain wrappers
    - Generic responses
    
    Usage:
        parser = TokenParser()
        input_tokens, output_tokens = parser.parse_generic(response, provider='openai')
    """
    
    def parse_openai_response(self, response: Any) -> Tuple[int, int]:
        """
        Parse OpenAI response
        
        OpenAI format:
        {
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
        }
        
        Returns: (input_tokens, output_tokens)
        """
        try:
            # Handle object with usage attribute
            if hasattr(response, 'usage'):
                usage = response.usage
                return (
                    getattr(usage, 'prompt_tokens', 0),
                    getattr(usage, 'completion_tokens', 0)
                )
            
            # Handle dictionary
            if isinstance(response, dict):
                usage = response.get('usage', {})
                return (
                    usage.get('prompt_tokens', 0),
                    usage.get('completion_tokens', 0)
                )
            
            logger.warning("Could not parse OpenAI response format")
            return (0, 0)
            
        except Exception as e:
            logger.error(f"Error parsing OpenAI response: {e}", exc_info=True)
            return (0, 0)
    
    def parse_anthropic_response(self, response: Any) -> Tuple[int, int]:
        """
        Parse Anthropic response
        
        Anthropic format:
        {
            "usage": {
                "input_tokens": 100,
                "output_tokens": 50
            }
        }
        
        Returns: (input_tokens, output_tokens)
        """
        try:
            # Handle object with usage attribute
            if hasattr(response, 'usage'):
                usage = response.usage
                return (
                    getattr(usage, 'input_tokens', 0),
                    getattr(usage, 'output_tokens', 0)
                )
            
            # Handle dictionary
            if isinstance(response, dict):
                usage = response.get('usage', {})
                return (
                    usage.get('input_tokens', 0),
                    usage.get('output_tokens', 0)
                )
            
            logger.warning("Could not parse Anthropic response format")
            return (0, 0)
            
        except Exception as e:
            logger.error(f"Error parsing Anthropic response: {e}", exc_info=True)
            return (0, 0)
    
    def parse_langchain_response(self, response: Any) -> Tuple[int, int]:
        """
        Parse LangChain response
        
        LangChain wraps provider responses in response_metadata
        
        Returns: (input_tokens, output_tokens)
        """
        try:
            if not hasattr(response, 'response_metadata'):
                return (0, 0)
            
            metadata = response.response_metadata
            
            # OpenAI via LangChain
            if 'token_usage' in metadata:
                usage = metadata['token_usage']
                return (
                    usage.get('prompt_tokens', 0),
                    usage.get('completion_tokens', 0)
                )
            
            # Anthropic via LangChain
            if 'usage' in metadata:
                usage = metadata['usage']
                return (
                    usage.get('input_tokens', 0),
                    usage.get('output_tokens', 0)
                )
            
            logger.warning("Could not parse LangChain response format")
            return (0, 0)
            
        except Exception as e:
            logger.error(f"Error parsing LangChain response: {e}", exc_info=True)
            return (0, 0)
    
    def parse_generic(
        self,
        response: Any,
        provider: Optional[str] = None
    ) -> Tuple[int, int]:
        """
        Parse any response, trying all parsers
        
        Args:
            response: LLM response object or dictionary
            provider: Provider hint ('openai', 'anthropic', etc.) - optional
            
        Returns: (input_tokens, output_tokens)
        
        Example:
            tokens = parser.parse_generic(llm_response, provider='openai')
            input_tokens, output_tokens = tokens
        """
        # Try provider-specific parser first if hint provided
        if provider:
            provider = provider.lower()
            
            if 'openai' in provider or 'gpt' in provider:
                tokens = self.parse_openai_response(response)
                if tokens != (0, 0):
                    return tokens
            
            if 'anthropic' in provider or 'claude' in provider:
                tokens = self.parse_anthropic_response(response)
                if tokens != (0, 0):
                    return tokens
        
        # Try all parsers in order
        for parser_method in [
            self.parse_openai_response,
            self.parse_anthropic_response,
            self.parse_langchain_response
        ]:
            tokens = parser_method(response)
            if tokens != (0, 0):
                logger.debug(f"Successfully parsed tokens using {parser_method.__name__}")
                return tokens
        
        logger.warning("Could not parse tokens from response - tried all parsers")
        return (0, 0)
    
    def detect_provider(self, response: Any) -> str:
        """
        Detect provider from response
        
        Args:
            response: LLM response object or dictionary
            
        Returns: Provider name ('openai', 'anthropic', 'unknown')
        
        Example:
            provider = parser.detect_provider(llm_response)
            # Returns: 'openai'
        """
        try:
            # Check model attribute
            if hasattr(response, 'model'):
                model = str(response.model).lower()
                if 'gpt' in model or 'davinci' in model or 'turbo' in model:
                    return 'openai'
                if 'claude' in model:
                    return 'anthropic'
            
            # Check dictionary
            if isinstance(response, dict):
                model = str(response.get('model', '')).lower()
                if 'gpt' in model or 'davinci' in model or 'turbo' in model:
                    return 'openai'
                if 'claude' in model:
                    return 'anthropic'
            
            # Check response_metadata (LangChain)
            if hasattr(response, 'response_metadata'):
                metadata = response.response_metadata
                if 'token_usage' in metadata:
                    return 'openai'
                if 'usage' in metadata and 'input_tokens' in metadata.get('usage', {}):
                    return 'anthropic'
            
            return 'unknown'
            
        except Exception as e:
            logger.error(f"Error detecting provider: {e}")
            return 'unknown'


# END OF FILE - TokenParser complete (200+ lines)
