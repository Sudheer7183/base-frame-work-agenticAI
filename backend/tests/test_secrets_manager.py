"""
Test Suite for Secrets Management

Tests all components of the secrets management system.

Run with:
    pytest tests/test_secrets_manager.py -v
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from app.core.secrets.manager import SecretsManager
from app.core.secrets.providers import LocalSecretsProvider, VaultSecretsProvider, AWSSecretsProvider
from app.core.secrets.encryption import SecretEncryption
from app.core.secrets.audit import SecretsAuditLogger


class TestSecretEncryption:
    """Test secret encryption and decryption"""
    
    def test_encrypt_decrypt_string(self):
        """Test basic encryption and decryption"""
        encryption = SecretEncryption()
        
        original = "my-secret-password"
        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == original
        assert encrypted != original
    
    def test_encrypt_decrypt_bytes(self):
        """Test encryption with bytes"""
        encryption = SecretEncryption()
        
        original = b"binary-secret-data"
        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)
        
        assert decrypted == original.decode()
    
    def test_invalid_decryption(self):
        """Test decryption with wrong key fails"""
        encryption1 = SecretEncryption()
        encryption2 = SecretEncryption()  # Different key
        
        encrypted = encryption1.encrypt("secret")
        
        with pytest.raises(ValueError):
            encryption2.decrypt(encrypted)
    
    def test_generate_key(self):
        """Test key generation"""
        key = SecretEncryption.generate_key()
        assert isinstance(key, str)
        assert len(key) > 0
        
        # Should be valid Fernet key
        encryption = SecretEncryption(master_key=key)
        assert encryption is not None
    
    def test_derive_key_from_password(self):
        """Test key derivation from password"""
        password = "my-strong-password"
        key1, salt1 = SecretEncryption.derive_key(password)
        key2, salt2 = SecretEncryption.derive_key(password, salt=salt1)
        
        # Same password and salt should produce same key
        assert key1 == key2
        
        # Different salt should produce different key
        key3, salt3 = SecretEncryption.derive_key(password)
        assert key1 != key3


class TestLocalSecretsProvider:
    """Test local .env file provider"""
    
    def test_load_env_file(self):
        """Test loading secrets from .env file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("TEST_KEY=test_value\n")
            f.write("ANOTHER_KEY=another_value\n")
            f.write("# Comment\n")
            f.write('QUOTED="quoted value"\n')
            env_file = f.name
        
        try:
            provider = LocalSecretsProvider(env_file=env_file)
            
            assert provider.get_secret("TEST_KEY") == "test_value"
            assert provider.get_secret("ANOTHER_KEY") == "another_value"
            assert provider.get_secret("QUOTED") == "quoted value"
            assert provider.get_secret("NONEXISTENT") is None
        finally:
            os.unlink(env_file)
    
    def test_set_secret(self):
        """Test setting a new secret"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("EXISTING=value\n")
            env_file = f.name
        
        try:
            provider = LocalSecretsProvider(env_file=env_file)
            
            # Set new secret
            assert provider.set_secret("NEW_KEY", "new_value")
            assert provider.get_secret("NEW_KEY") == "new_value"
            
            # Update existing secret
            assert provider.set_secret("EXISTING", "updated")
            assert provider.get_secret("EXISTING") == "updated"
        finally:
            os.unlink(env_file)
    
    def test_delete_secret(self):
        """Test deleting a secret"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("TO_DELETE=value\n")
            env_file = f.name
        
        try:
            provider = LocalSecretsProvider(env_file=env_file)
            
            assert provider.get_secret("TO_DELETE") == "value"
            assert provider.delete_secret("TO_DELETE")
            assert provider.get_secret("TO_DELETE") is None
        finally:
            os.unlink(env_file)
    
    def test_list_secrets(self):
        """Test listing secrets"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("DATABASE_HOST=localhost\n")
            f.write("DATABASE_PORT=5432\n")
            f.write("REDIS_HOST=localhost\n")
            env_file = f.name
        
        try:
            provider = LocalSecretsProvider(env_file=env_file)
            
            all_keys = provider.list_secrets()
            assert "DATABASE_HOST" in all_keys
            assert "DATABASE_PORT" in all_keys
            assert "REDIS_HOST" in all_keys
            
            # Test prefix filter
            db_keys = provider.list_secrets(prefix="DATABASE")
            assert "DATABASE_HOST" in db_keys
            assert "DATABASE_PORT" in db_keys
            assert "REDIS_HOST" not in db_keys
        finally:
            os.unlink(env_file)


class TestSecretsAuditLogger:
    """Test secrets audit logging"""
    
    def test_log_access(self):
        """Test logging secret access"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log"
            logger = SecretsAuditLogger(log_file=str(log_file))
            
            logger.log_access("database/password", "get", success=True)
            
            assert log_file.exists()
            content = log_file.read_text()
            assert "database/password" in content
            assert "access" in content
    
    def test_log_modification(self):
        """Test logging secret modification"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log"
            logger = SecretsAuditLogger(log_file=str(log_file))
            
            logger.log_modification("api/key", "set", success=True)
            
            content = log_file.read_text()
            assert "api/key" in content
            assert "modification" in content
    
    def test_get_audit_trail(self):
        """Test retrieving audit trail"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log"
            logger = SecretsAuditLogger(log_file=str(log_file))
            
            logger.log_access("key1", "get")
            logger.log_access("key2", "get")
            logger.log_modification("key1", "set")
            
            # Get all events
            trail = logger.get_audit_trail()
            assert len(trail) == 3
            
            # Filter by key
            key1_trail = logger.get_audit_trail(key="key1")
            assert len(key1_trail) == 2
            
            # Filter by event type
            access_trail = logger.get_audit_trail(event_type="access")
            assert len(access_trail) == 2
    
    def test_get_statistics(self):
        """Test audit statistics"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "audit.log"
            logger = SecretsAuditLogger(log_file=str(log_file))
            
            logger.log_access("key1", "get", success=True)
            logger.log_access("key2", "get", success=True)
            logger.log_modification("key1", "set", success=True)
            logger.log_access("key3", "get", success=False)
            
            stats = logger.get_statistics(hours=24)
            
            assert stats["total_events"] == 4
            assert stats["access_events"] == 3
            assert stats["modification_events"] == 1
            assert stats["failed_events"] == 1
            assert stats["unique_keys"] == 3


class TestSecretsManager:
    """Test secrets manager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.env_file = Path(self.temp_dir) / ".env"
        self.env_file.write_text("TEST_SECRET=test_value\n")
        
        self.provider = LocalSecretsProvider(env_file=str(self.env_file))
        self.audit_log = Path(self.temp_dir) / "audit.log"
        self.audit_logger = SecretsAuditLogger(log_file=str(self.audit_log))
        
        self.manager = SecretsManager(
            provider=self.provider,
            audit_logger=self.audit_logger,
            cache_ttl=300,
            enable_encryption=False  # Disable for simpler testing
        )
    
    def test_get_secret(self):
        """Test getting a secret"""
        value = self.manager.get_secret("TEST_SECRET")
        assert value == "test_value"
        
        # Check audit log
        trail = self.audit_logger.get_audit_trail(key="TEST_SECRET")
        assert len(trail) > 0
    
    def test_get_secret_with_default(self):
        """Test getting secret with default value"""
        value = self.manager.get_secret("NONEXISTENT", default="default_value")
        assert value == "default_value"
    
    def test_get_secret_required(self):
        """Test required secret raises exception if not found"""
        with pytest.raises(ValueError):
            self.manager.get_secret("NONEXISTENT", required=True)
    
    def test_set_secret(self):
        """Test setting a secret"""
        assert self.manager.set_secret("NEW_KEY", "new_value")
        assert self.manager.get_secret("NEW_KEY") == "new_value"
    
    def test_delete_secret(self):
        """Test deleting a secret"""
        self.manager.set_secret("TO_DELETE", "value")
        assert self.manager.delete_secret("TO_DELETE")
        assert self.manager.get_secret("TO_DELETE") is None
    
    def test_cache(self):
        """Test secrets caching"""
        # First call - cache miss
        value1 = self.manager.get_secret("TEST_SECRET", use_cache=True)
        
        # Modify underlying value
        self.provider.set_secret("TEST_SECRET", "new_value")
        
        # Second call - cache hit (should return old value)
        value2 = self.manager.get_secret("TEST_SECRET", use_cache=True)
        assert value2 == value1
        
        # Clear cache
        self.manager.clear_cache("TEST_SECRET")
        
        # Third call - cache miss (should return new value)
        value3 = self.manager.get_secret("TEST_SECRET", use_cache=True)
        assert value3 == "new_value"
    
    def test_list_secrets(self):
        """Test listing secrets"""
        self.manager.set_secret("database/host", "localhost")
        self.manager.set_secret("database/port", "5432")
        self.manager.set_secret("redis/host", "localhost")
        
        all_keys = self.manager.list_secrets()
        assert "database/host" in all_keys
        
        db_keys = self.manager.list_secrets(prefix="database")
        assert "database/host" in db_keys
        assert "redis/host" not in db_keys
    
    def test_health_check(self):
        """Test health check"""
        health = self.manager.health_check()
        
        assert "provider" in health
        assert "cache_size" in health
        assert "provider_healthy" in health
        assert health["provider_healthy"] is True


class TestIntegration:
    """Integration tests"""
    
    def test_full_workflow(self):
        """Test complete workflow"""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_file = Path(tmpdir) / ".env"
            audit_log = Path(tmpdir) / "audit.log"
            
            # Create provider and manager
            provider = LocalSecretsProvider(env_file=str(env_file))
            audit_logger = SecretsAuditLogger(log_file=str(audit_log))
            manager = SecretsManager(
                provider=provider,
                audit_logger=audit_logger,
                enable_encryption=False
            )
            
            # Set secrets
            assert manager.set_secret("db/host", "localhost")
            assert manager.set_secret("db/password", "secret123")
            
            # Get secrets
            assert manager.get_secret("db/host") == "localhost"
            assert manager.get_secret("db/password") == "secret123"
            
            # List secrets
            keys = manager.list_secrets()
            assert "db/host" in keys
            assert "db/password" in keys
            
            # Rotate secret
            assert manager.rotate_secret("db/password", "new_secret456")
            assert manager.get_secret("db/password") == "new_secret456"
            
            # Check audit trail
            trail = audit_logger.get_audit_trail()
            assert len(trail) > 0
            
            # Check statistics
            stats = audit_logger.get_statistics(hours=24)
            assert stats["total_events"] > 0
            assert stats["unique_keys"] >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])