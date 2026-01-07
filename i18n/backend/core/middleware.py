"""
FastAPI Middleware for Locale Detection and Management

Version: 3.0
License: MIT
"""

import logging
from typing import Optional, List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .i18n import set_locale, SUPPORTED_LOCALES, DEFAULT_LOCALE

logger = logging.getLogger(__name__)


class LocaleMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware to detect and set locale from request
    
    Detection order (configurable):
    1. Query parameter (?locale=en)
    2. X-Locale header
    3. Cookie (locale=en)
    4. Accept-Language header
    5. Default locale
    
    Usage:
        from fastapi import FastAPI
        from backend.core.middleware import LocaleMiddleware
        
        app = FastAPI()
        app.add_middleware(LocaleMiddleware)
    """
    
    def __init__(
        self,
        app,
        detection_order: Optional[List[str]] = None,
        cookie_name: str = "locale",
        query_param: str = "locale",
        header_name: str = "x-locale"
    ):
        """
        Initialize middleware
        
        Args:
            app: FastAPI application
            detection_order: Order of detection methods
            cookie_name: Name of locale cookie
            query_param: Name of query parameter
            header_name: Name of custom header
        """
        super().__init__(app)
        
        self.detection_order = detection_order or [
            "query",
            "header",
            "cookie",
            "accept-language"
        ]
        self.cookie_name = cookie_name
        self.query_param = query_param
        self.header_name = header_name
        
        logger.info(f"LocaleMiddleware initialized with order: {self.detection_order}")
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and detect locale
        
        Args:
            request: Starlette Request object
            call_next: Next middleware/handler
            
        Returns:
            Response with locale set in context
        """
        locale = self._detect_locale(request)
        
        # Set locale in context for this request
        set_locale(locale)
        
        # Add locale to request state for easy access
        request.state.locale = locale
        
        logger.debug(f"Request locale set to: {locale} for {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Optionally set locale in response headers
        response.headers["Content-Language"] = locale
        
        return response
    
    def _detect_locale(self, request: Request) -> str:
        """
        Detect locale from request using configured detection order
        
        Args:
            request: Starlette Request object
            
        Returns:
            Detected locale code
        """
        for method in self.detection_order:
            locale = None
            
            if method == "query":
                locale = self._from_query(request)
            elif method == "header":
                locale = self._from_header(request)
            elif method == "cookie":
                locale = self._from_cookie(request)
            elif method == "accept-language":
                locale = self._from_accept_language(request)
            
            # If valid locale found, return it
            if locale and locale in SUPPORTED_LOCALES:
                logger.debug(f"Locale detected from {method}: {locale}")
                return locale
        
        # Fallback to default
        logger.debug(f"Using default locale: {DEFAULT_LOCALE}")
        return DEFAULT_LOCALE
    
    def _from_query(self, request: Request) -> Optional[str]:
        """Extract locale from query parameter"""
        locale = request.query_params.get(self.query_param)
        if locale:
            # Extract language code (e.g., 'en' from 'en-US')
            return locale.split("-")[0].lower()
        return None
    
    def _from_header(self, request: Request) -> Optional[str]:
        """Extract locale from X-Locale header"""
        locale = request.headers.get(self.header_name)
        if locale:
            return locale.split("-")[0].lower()
        return None
    
    def _from_cookie(self, request: Request) -> Optional[str]:
        """Extract locale from cookie"""
        locale = request.cookies.get(self.cookie_name)
        if locale:
            return locale.split("-")[0].lower()
        return None
    
    def _from_accept_language(self, request: Request) -> Optional[str]:
        """
        Extract locale from Accept-Language header
        
        Parses Accept-Language header with quality values
        Example: "en-US,en;q=0.9,es;q=0.8,fr;q=0.7"
        """
        accept_language = request.headers.get("accept-language")
        if not accept_language:
            return None
        
        # Parse Accept-Language header
        # Format: "lang;q=quality,lang;q=quality,..."
        languages = []
        for lang_entry in accept_language.split(","):
            parts = lang_entry.strip().split(";")
            lang = parts[0].strip()
            
            # Extract quality value (default 1.0)
            quality = 1.0
            if len(parts) > 1:
                try:
                    quality = float(parts[1].split("=")[1])
                except (IndexError, ValueError):
                    quality = 1.0
            
            # Extract language code
            lang_code = lang.split("-")[0].lower()
            languages.append((lang_code, quality))
        
        # Sort by quality (highest first)
        languages.sort(key=lambda x: x[1], reverse=True)
        
        # Return first supported language
        for lang_code, _ in languages:
            if lang_code in SUPPORTED_LOCALES:
                return lang_code
        
        return None


class LocaleHeaderMiddleware:
    """
    Simpler ASGI middleware that only adds locale to response headers
    
    Usage:
        app.add_middleware(LocaleHeaderMiddleware)
    """
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """ASGI interface"""
        if scope["type"] == "http":
            # Wrap send to add headers
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    headers = dict(message.get("headers", []))
                    
                    # Get locale from context
                    from .i18n import get_current_locale
                    locale = get_current_locale()
                    
                    # Add Content-Language header
                    headers[b"content-language"] = locale.encode("utf-8")
                    
                    # Update message
                    message["headers"] = list(headers.items())
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)


# =============================================================================
# Dependency for FastAPI Routes
# =============================================================================

def get_locale_dependency(request: Request) -> str:
    """
    FastAPI dependency to get current locale
    
    Usage:
        @app.get("/api/data")
        async def get_data(locale: str = Depends(get_locale_dependency)):
            return {"locale": locale}
    """
    return getattr(request.state, "locale", DEFAULT_LOCALE)


# =============================================================================
# Response Models
# =============================================================================

from pydantic import BaseModel
from typing import Dict, Any


class LocalizedResponse(BaseModel):
    """Base response model with locale information"""
    locale: str
    data: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "locale": "en",
                "data": {
                    "message": "Hello, World!"
                }
            }
        }


# =============================================================================
# Utility Functions
# =============================================================================

def get_client_locale(request: Request) -> str:
    """
    Get client locale from request
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Client locale code
    """
    return getattr(request.state, "locale", DEFAULT_LOCALE)


def set_response_locale(response: Response, locale: str) -> None:
    """
    Set locale in response headers
    
    Args:
        response: FastAPI Response object
        locale: Locale code to set
    """
    response.headers["Content-Language"] = locale


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "LocaleMiddleware",
    "LocaleHeaderMiddleware",
    "get_locale_dependency",
    "LocalizedResponse",
    "get_client_locale",
    "set_response_locale",
]
