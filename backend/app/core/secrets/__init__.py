"""
Secrets Management Module

Provides secure secrets management for the Agentic AI Platform.
"""

import os
from functools import lru_cache
from .manager import SecretsManager
from .providers import LocalSecretsProvider, VaultSecretsProvider, AWSSecretsProvider
from .encryption import SecretEncryption
from .audit import SecretsAuditLogger

__all__ = [
    "SecretsManager",
    "LocalSecretsProvider",
    "VaultSecretsProvider",
    "AWSSecretsProvider",
    "SecretEncryption",
    "SecretsAuditLogger",
    "get_secrets_manager",
]


@lru_cache(maxsize=1)
def get_secrets_manager() -> SecretsManager:
    """
    Get singleton instance of SecretsManager.
    
    Returns:
        SecretsManager: Configured secrets manager instance
    """
    # Determine environment
    environment = os.getenv("ENVIRONMENT", "development")
    secrets_provider = os.getenv("SECRETS_PROVIDER", "local")
    
    # Create appropriate provider
    if secrets_provider == "vault":
        vault_url = os.getenv("VAULT_ADDR")
        vault_token = os.getenv("VAULT_TOKEN")
        vault_namespace = os.getenv("VAULT_NAMESPACE", f"agentic-ai-platform/{environment}")
        
        if not vault_url or not vault_token:
            raise ValueError("VAULT_ADDR and VAULT_TOKEN required for vault provider")
        
        provider = VaultSecretsProvider(
            vault_url=vault_url,
            token=vault_token,
            namespace=vault_namespace
        )
    elif secrets_provider == "aws":
        aws_region = os.getenv("AWS_REGION", "us-east-1")
        provider = AWSSecretsProvider(region=aws_region)
    else:
        # Default to local .env file
        env_file = os.getenv("SECRETS_ENV_FILE", ".env")
        provider = LocalSecretsProvider(env_file=env_file)
    
    # Create encryption if master key provided
    encryption = None
    master_key = os.getenv("SECRETS_MASTER_KEY")
    if master_key:
        encryption = SecretEncryption(master_key=master_key)
    
    # Create audit logger
    audit_log_file = os.getenv("SECRETS_AUDIT_LOG", "logs/secrets_audit.log")
    audit_logger = SecretsAuditLogger(log_file=audit_log_file)
    
    # Create and return manager
    cache_ttl = int(os.getenv("SECRETS_CACHE_TTL", "300"))
    
    return SecretsManager(
        provider=provider,
        audit_logger=audit_logger,
        encryption=encryption,
        cache_ttl=cache_ttl,
        enable_encryption=bool(master_key)
    )