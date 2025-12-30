
"""Secrets Manager"""

import time
from typing import Optional, Any
from .providers import SecretsProvider
from .encryption import SecretEncryption
from .audit import SecretsAuditLogger


class SecretsManager:
    """Main secrets management class"""
    
    def __init__(
        self,
        provider: SecretsProvider,
        audit_logger: SecretsAuditLogger = None,
        encryption: SecretEncryption = None,
        cache_ttl: int = 300,
        enable_encryption: bool = False
    ):
        self.provider = provider
        self.audit_logger = audit_logger or SecretsAuditLogger()
        self.encryption = encryption if enable_encryption else None
        self.cache_ttl = cache_ttl
        self.cache = {}
    
    def get_secret(
        self,
        key: str,
        default: Any = None,
        required: bool = False,
        use_cache: bool = False
    ) -> Optional[str]:
        """Get a secret value"""
        # Check cache
        if use_cache and key in self.cache:
            cached_value, cached_time = self.cache[key]
            if time.time() - cached_time < self.cache_ttl:
                self.audit_logger.log_access(key, "get", success=True)
                return cached_value
        
        # Get from provider
        try:
            value = self.provider.get_secret(key)
            
            if value is None:
                if required:
                    raise ValueError(f"Required secret '{key}' not found")
                value = default
            
            # Decrypt if needed
            if value and self.encryption:
                try:
                    value = self.encryption.decrypt(value)
                except:
                    pass  # Not encrypted
            
            # Cache if requested
            if use_cache and value is not None:
                self.cache[key] = (value, time.time())
            
            self.audit_logger.log_access(key, "get", success=True)
            return value
            
        except Exception as e:
            self.audit_logger.log_access(key, "get", success=False)
            if required:
                raise
            return default
    
    def set_secret(self, key: str, value: str, encrypt: bool = None) -> bool:
        """Set a secret value"""
        try:
            # Encrypt if needed
            if encrypt is None:
                encrypt = self.encryption is not None
            
            if encrypt and self.encryption:
                value = self.encryption.encrypt(value)
            
            success = self.provider.set_secret(key, value)
            
            # Clear cache
            if key in self.cache:
                del self.cache[key]
            
            self.audit_logger.log_modification(key, "set", success=success)
            return success
            
        except Exception as e:
            self.audit_logger.log_modification(key, "set", success=False)
            return False
    
    def delete_secret(self, key: str) -> bool:
        """Delete a secret"""
        try:
            success = self.provider.delete_secret(key)
            
            # Clear cache
            if key in self.cache:
                del self.cache[key]
            
            self.audit_logger.log_modification(key, "delete", success=success)
            return success
            
        except Exception as e:
            self.audit_logger.log_modification(key, "delete", success=False)
            return False
    
    def list_secrets(self, prefix: str = None) -> list[str]:
        """List all secret keys"""
        return self.provider.list_secrets(prefix=prefix)
    
    def rotate_secret(self, key: str, new_value: str) -> bool:
        """Rotate a secret to a new value"""
        return self.set_secret(key, new_value)
    
    def clear_cache(self, key: str = None):
        """Clear cache for a specific key or all keys"""
        if key:
            if key in self.cache:
                del self.cache[key]
        else:
            self.cache.clear()
    
    def health_check(self) -> dict:
        """Check health of secrets manager"""
        try:
            # Try to list secrets
            keys = self.provider.list_secrets()
            return {
                "provider": self.provider.__class__.__name__,
                "cache_size": len(self.cache),
                "provider_healthy": True,
                "secrets_count": len(keys)
            }
        except Exception as e:
            return {
                "provider": self.provider.__class__.__name__,
                "cache_size": len(self.cache),
                "provider_healthy": False,
                "error": str(e)
            }