"""Secrets Providers"""

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

try:
    import hvac
    HVAC_AVAILABLE = True
except ImportError:
    HVAC_AVAILABLE = False


class SecretsProvider(ABC):
    """Base class for secrets providers"""
    
    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        """Get a secret value"""
        pass
    
    @abstractmethod
    def set_secret(self, key: str, value: str) -> bool:
        """Set a secret value"""
        pass
    
    @abstractmethod
    def delete_secret(self, key: str) -> bool:
        """Delete a secret"""
        pass
    
    @abstractmethod
    def list_secrets(self, prefix: str = None) -> list[str]:
        """List all secret keys"""
        pass


class LocalSecretsProvider(SecretsProvider):
    """Local .env file provider"""
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = Path(env_file)
        self.secrets = {}
        self._load()
    
    def _load(self):
        """Load secrets from .env file"""
        if not self.env_file.exists():
            return
        
        with open(self.env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes
                    value = value.strip('"').strip("'")
                    self.secrets[key.strip()] = value
    
    def _save(self):
        """Save secrets to .env file"""
        self.env_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.env_file, 'w') as f:
            for key, value in sorted(self.secrets.items()):
                f.write(f'{key}={value}\n')
    
    def get_secret(self, key: str) -> Optional[str]:
        """Get a secret"""
        return self.secrets.get(key)
    
    def set_secret(self, key: str, value: str) -> bool:
        """Set a secret"""
        self.secrets[key] = value
        self._save()
        return True
    
    def delete_secret(self, key: str) -> bool:
        """Delete a secret"""
        if key in self.secrets:
            del self.secrets[key]
            self._save()
            return True
        return False
    
    def list_secrets(self, prefix: str = None) -> list[str]:
        """List secret keys"""
        keys = list(self.secrets.keys())
        if prefix:
            keys = [k for k in keys if k.startswith(prefix)]
        return keys


class VaultSecretsProvider(SecretsProvider):
    """HashiCorp Vault secrets provider"""
    
    def __init__(self, vault_url: str, token: str, namespace: str = "", mount_point: str = "secret"):
        """
        Initialize Vault provider
        
        Args:
            vault_url: Vault server URL (e.g., http://localhost:8200)
            token: Vault authentication token
            namespace: Path prefix for secrets (e.g., agentic-ai-platform/development)
            mount_point: KV mount point (default: secret)
        """
        if not HVAC_AVAILABLE:
            raise ImportError("hvac library is required for Vault support. Install with: pip install hvac")
        
        self.vault_url = vault_url
        self.token = token
        self.namespace = namespace
        self.mount_point = mount_point
        
        # Initialize Vault client
        self.client = hvac.Client(url=vault_url, token=token)
        
        # Verify connection
        if not self.client.is_authenticated():
            raise ConnectionError(f"Failed to authenticate to Vault at {vault_url}")
        
        print(f"✓ Connected to Vault at {vault_url}")
    
    def _get_secret_path(self, key: str) -> tuple[str, str]:
        """
        Convert flat key to Vault path and field name
        
        Examples:
            DB_PASSWORD → (database, password)
            SECRET_KEY → (application, secret_key)
            KEYCLOAK_CLIENT_SECRET → (keycloak, client_secret)
        """
        # Map common keys to Vault paths
        key_mapping = {
            'DB_PASSWORD': ('database', 'password'),
            'DB_USER': ('database', 'user'),
            'DB_HOST': ('database', 'host'),
            'DB_PORT': ('database', 'port'),
            'DB_NAME': ('database', 'name'),
            
            'REDIS_PASSWORD': ('redis', 'password'),
            
            'SECRET_KEY': ('application', 'secret_key'),
            'JWT_SECRET_KEY': ('application', 'jwt_secret_key'),
            
            'KEYCLOAK_CLIENT_SECRET': ('keycloak', 'client_secret'),
            'KEYCLOAK_ADMIN_PASSWORD': ('keycloak', 'admin_password'),
            
            'OPENAI_API_KEY': ('llm', 'openai_api_key'),
            'ANTHROPIC_API_KEY': ('llm', 'anthropic_api_key'),
            
            'SMTP_USER': ('email', 'smtp_user'),
            'SMTP_PASSWORD': ('email', 'smtp_password'),
        }
        
        if key in key_mapping:
            return key_mapping[key]
        
        # Default: use key as-is
        # Convert KEY_NAME to (general, key_name)
        return ('general', key.lower())
    
    def _build_vault_path(self, secret_path: str) -> str:
        """Build full Vault path"""
        if self.namespace:
            return f"{self.namespace}/{secret_path}"
        return secret_path
    
    def get_secret(self, key: str) -> Optional[str]:
        """Get a secret from Vault"""
        try:
            secret_path, field_name = self._get_secret_path(key)
            vault_path = self._build_vault_path(secret_path)
            
            # Read from Vault KV v2
            response = self.client.secrets.kv.v2.read_secret_version(
                path=vault_path,
                mount_point=self.mount_point
            )
            
            if response and 'data' in response and 'data' in response['data']:
                data = response['data']['data']
                value = data.get(field_name)
                if value:
                    print(f"✓ Retrieved {key} from Vault (path: {vault_path}/{field_name})")
                return value
            
            print(f"⚠ Secret {key} not found in Vault (path: {vault_path}/{field_name})")
            return None
            
        except hvac.exceptions.InvalidPath:
            # Secret doesn't exist
            print(f"⚠ Path not found in Vault: {vault_path}")
            return None
        except Exception as e:
            print(f"✗ Error reading secret {key} from Vault: {e}")
            return None
    
    def set_secret(self, key: str, value: str) -> bool:
        """Set a secret in Vault"""
        try:
            secret_path, field_name = self._get_secret_path(key)
            vault_path = self._build_vault_path(secret_path)
            
            # Try to read existing data first
            try:
                response = self.client.secrets.kv.v2.read_secret_version(
                    path=vault_path,
                    mount_point=self.mount_point
                )
                existing_data = response['data']['data'] if response else {}
            except hvac.exceptions.InvalidPath:
                existing_data = {}
            
            # Update with new value
            existing_data[field_name] = value
            
            # Write to Vault KV v2
            self.client.secrets.kv.v2.create_or_update_secret(
                path=vault_path,
                secret=existing_data,
                mount_point=self.mount_point
            )
            
            return True
            
        except Exception as e:
            print(f"Error writing secret {key} to Vault: {e}")
            return False
    
    def delete_secret(self, key: str) -> bool:
        """Delete a secret from Vault"""
        try:
            secret_path, field_name = self._get_secret_path(key)
            vault_path = self._build_vault_path(secret_path)
            
            # Read existing data
            response = self.client.secrets.kv.v2.read_secret_version(
                path=vault_path,
                mount_point=self.mount_point
            )
            
            if response and 'data' in response and 'data' in response['data']:
                data = response['data']['data']
                
                # Remove the specific field
                if field_name in data:
                    del data[field_name]
                    
                    # If no fields left, delete the entire secret
                    if not data:
                        self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                            path=vault_path,
                            mount_point=self.mount_point
                        )
                    else:
                        # Update with remaining fields
                        self.client.secrets.kv.v2.create_or_update_secret(
                            path=vault_path,
                            secret=data,
                            mount_point=self.mount_point
                        )
                    
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting secret {key} from Vault: {e}")
            return False
    
    def list_secrets(self, prefix: str = None) -> list[str]:
        """List all secret keys"""
        try:
            keys = []
            
            # List all paths under namespace
            vault_path = self.namespace if self.namespace else ""
            
            try:
                response = self.client.secrets.kv.v2.list_secrets(
                    path=vault_path,
                    mount_point=self.mount_point
                )
                
                if response and 'data' in response and 'keys' in response['data']:
                    paths = response['data']['keys']
                    
                    # For each path, read and get field names
                    for path in paths:
                        full_path = f"{vault_path}/{path}" if vault_path else path
                        
                        secret_response = self.client.secrets.kv.v2.read_secret_version(
                            path=full_path.rstrip('/'),
                            mount_point=self.mount_point
                        )
                        
                        if secret_response and 'data' in secret_response and 'data' in secret_response['data']:
                            data = secret_response['data']['data']
                            
                            # Convert back to flat keys
                            for field in data.keys():
                                # Try to find the original key name
                                key_name = f"{path.upper().replace('/', '_')}_{field.upper()}"
                                keys.append(key_name)
            
            except hvac.exceptions.InvalidPath:
                # No secrets at this path
                pass
            
            # Filter by prefix if provided
            if prefix:
                keys = [k for k in keys if k.startswith(prefix)]
            
            return keys
            
        except Exception as e:
            print(f"Error listing secrets from Vault: {e}")
            return []


class AWSSecretsProvider(SecretsProvider):
    """AWS Secrets Manager provider (stub for now)"""
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
    
    def get_secret(self, key: str) -> Optional[str]:
        raise NotImplementedError("AWS provider not yet implemented")
    
    def set_secret(self, key: str, value: str) -> bool:
        raise NotImplementedError("AWS provider not yet implemented")
    
    def delete_secret(self, key: str) -> bool:
        raise NotImplementedError("AWS provider not yet implemented")
    
    def list_secrets(self, prefix: str = None) -> list[str]:
        raise NotImplementedError("AWS provider not yet implemented")