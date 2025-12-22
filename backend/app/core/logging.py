"""Logging configuration"""

import logging
import sys
from typing import Optional
from app.tenancy.context import get_tenant_slug


class TenantContextFilter(logging.Filter):
    """Add tenant context to log records"""
    
    def filter(self, record):
        tenant_slug = get_tenant_slug()
        record.tenant = tenant_slug if tenant_slug else "no-tenant"
        return True


def setup_logging(level: str = "INFO"):
    """Configure application logging"""
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - [%(tenant)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(TenantContextFilter())
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(console_handler)
    
    # Suppress noisy loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
