"""Validation utilities for tenant identifiers"""

import re
from .exceptions import InvalidTenantError

# Regex patterns
SCHEMA_NAME_PATTERN = re.compile(r'^[a-z][a-z0-9_]{2,62}$')
SLUG_PATTERN = re.compile(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$')

# Reserved names that cannot be used as tenant identifiers
RESERVED_NAMES = {
    'public', 'pg_catalog', 'information_schema', 'pg_toast',
    'admin', 'root', 'system', 'postgres', 'template0', 'template1',
    'platform', 'api', 'www', 'app', 'health', 'docs'
}


def validate_schema_name(schema: str) -> bool:
    """
    Validate PostgreSQL schema name
    
    Rules:
    - Must start with a letter
    - Can contain lowercase letters, numbers, underscores
    - Length: 3-63 characters
    - Cannot be a reserved name
    
    Args:
        schema: Schema name to validate
        
    Returns:
        True if valid
        
    Raises:
        InvalidTenantError: If validation fails
    """
    if not schema:
        raise InvalidTenantError("Schema name cannot be empty")
    
    if schema.lower() in RESERVED_NAMES:
        raise InvalidTenantError(f"Schema name '{schema}' is reserved")
    
    if not SCHEMA_NAME_PATTERN.match(schema):
        raise InvalidTenantError(
            f"Schema name must start with a letter and contain only "
            f"lowercase letters, numbers, and underscores (3-63 chars): {schema}"
        )
    
    return True


def validate_slug(slug: str) -> bool:
    """
    Validate tenant slug
    
    Rules:
    - Must start and end with alphanumeric
    - Can contain lowercase letters, numbers, hyphens
    - Length: 1-63 characters
    - Cannot be a reserved name
    
    Args:
        slug: Tenant slug to validate
        
    Returns:
        True if valid
        
    Raises:
        InvalidTenantError: If validation fails
    """
    if not slug:
        raise InvalidTenantError("Slug cannot be empty")
    
    if slug.lower() in RESERVED_NAMES:
        raise InvalidTenantError(f"Slug '{slug}' is reserved")
    
    if not SLUG_PATTERN.match(slug):
        raise InvalidTenantError(
            f"Slug must contain only lowercase letters, numbers, and hyphens, "
            f"and must start/end with alphanumeric (1-63 chars): {slug}"
        )
    
    return True


def sanitize_identifier(identifier: str) -> str:
    """
    Sanitize a string to be used as SQL identifier
    
    This is a safety measure, validation should be done first
    """
    # Remove any characters that aren't alphanumeric or underscore
    sanitized = re.sub(r'[^a-z0-9_]', '', identifier.lower())
    
    # Ensure it starts with a letter
    if sanitized and not sanitized[0].isalpha():
        sanitized = 'tenant_' + sanitized
    
    return sanitized[:63]  # PostgreSQL limit