"""
Secret Encryption Utilities

Provides encryption/decryption for sensitive values using Fernet (AES-128-CBC).

File: backend/app/core/secrets/encryption.py
"""

import os
import base64
import logging
from typing import Union
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

logger = logging.getLogger(__name__)


class SecretEncryption:
    """
    Encrypt and decrypt secrets using Fernet symmetric encryption
    
    Uses a master key from environment variable or generates one.
    """
    
    def __init__(self, master_key: str = None):
        """
        Initialize encryption with master key
        
        Args:
            master_key: Base64-encoded Fernet key, or None to load from env
        """
        if master_key:
            self.key = master_key.encode()
        else:
            # Load from environment or generate
            self.key = self._get_or_generate_key()
        
        try:
            self.cipher = Fernet(self.key)
            logger.info("Secret encryption initialized")
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise ValueError("Invalid encryption key")
    
    def _get_or_generate_key(self) -> bytes:
        """Get master key from environment or generate new one"""
        env_key = os.getenv("SECRETS_MASTER_KEY")
        
        if env_key:
            try:
                # Validate it's a proper Fernet key
                Fernet(env_key.encode())
                return env_key.encode()
            except Exception as e:
                logger.warning(f"Invalid master key in environment: {e}")
        
        # Generate new key
        logger.warning("No valid master key found, generating new one")
        logger.warning("Set SECRETS_MASTER_KEY environment variable to persist encryption")
        new_key = Fernet.generate_key()
        logger.info(f"Generated master key (save this!): {new_key.decode()}")
        
        return new_key
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet key"""
        return Fernet.generate_key().decode()
    
    @staticmethod
    def derive_key(password: str, salt: bytes = None) -> tuple[str, bytes]:
        """
        Derive a Fernet key from a password
        
        Args:
            password: Password to derive from
            salt: Salt for derivation (generates new if None)
            
        Returns:
            Tuple of (base64_key, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        return key.decode(), salt
    
    def encrypt(self, value: Union[str, bytes]) -> str:
        """
        Encrypt a value
        
        Args:
            value: Value to encrypt (string or bytes)
            
        Returns:
            Base64-encoded encrypted value
        """
        try:
            if isinstance(value, str):
                value = value.encode()
            
            encrypted = self.cipher.encrypt(value)
            return encrypted.decode()
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError("Failed to encrypt value")
    
    def decrypt(self, encrypted_value: Union[str, bytes]) -> str:
        """
        Decrypt a value
        
        Args:
            encrypted_value: Encrypted value to decrypt
            
        Returns:
            Decrypted string value
            
        Raises:
            ValueError: If decryption fails
        """
        try:
            if isinstance(encrypted_value, str):
                encrypted_value = encrypted_value.encode()
            
            decrypted = self.cipher.decrypt(encrypted_value)
            return decrypted.decode()
            
        except InvalidToken:
            logger.error("Decryption failed: Invalid token or key")
            raise ValueError("Invalid encrypted value or wrong decryption key")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError("Failed to decrypt value")
    
    def rotate_key(self, new_key: str, old_values: dict) -> dict:
        """
        Rotate encryption key by re-encrypting all values
        
        Args:
            new_key: New Fernet key to use
            old_values: Dict of encrypted values to re-encrypt
            
        Returns:
            Dict of re-encrypted values
        """
        # Create new cipher with new key
        new_cipher = Fernet(new_key.encode())
        
        rotated = {}
        for key, encrypted_value in old_values.items():
            try:
                # Decrypt with old key
                decrypted = self.decrypt(encrypted_value)
                
                # Re-encrypt with new key
                re_encrypted = new_cipher.encrypt(decrypted.encode())
                rotated[key] = re_encrypted.decode()
                
            except Exception as e:
                logger.error(f"Failed to rotate key for {key}: {e}")
                # Keep old value if rotation fails
                rotated[key] = encrypted_value
        
        # Update cipher to new key
        self.key = new_key.encode()
        self.cipher = new_cipher
        
        logger.info(f"Rotated encryption key for {len(rotated)} values")
        return rotated


def generate_master_key() -> str:
    """Generate a new master encryption key"""
    return SecretEncryption.generate_key()


def derive_key_from_password(password: str) -> tuple[str, str]:
    """
    Derive an encryption key from a password
    
    Returns:
        Tuple of (key, salt) both as base64 strings
    """
    key, salt = SecretEncryption.derive_key(password)
    return key, base64.b64encode(salt).decode()