import os
import base64
from datetime import datetime, timezone
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecretEncryption:
    """Handle encryption/decryption of secrets"""
    
    def __init__(self, master_key: str = None):
        if master_key:
            # If it's a string, encode to bytes
            if isinstance(master_key, str):
                self.key = master_key.encode()
            else:
                self.key = master_key
        else:
            self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str | bytes) -> str:
        """Encrypt data"""
        if isinstance(data, str):
            data = data.encode()
        encrypted = self.cipher.encrypt(data)
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data"""
        try:
            decoded = base64.b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
    
    @staticmethod
    def generate_key() -> str:
        """Generate a new encryption key"""
        # Fernet.generate_key() already returns a base64-encoded key
        # Just decode it to string format
        return Fernet.generate_key().decode()
    
    @staticmethod
    def derive_key(password: str, salt: bytes = None) -> tuple[str, bytes]:
        """Derive encryption key from password"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode(), salt