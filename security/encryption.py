
"""
Encryption and Hashing Utilities
Secure data encryption and password hashing
"""
import os
import bcrypt
import secrets
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import logging

logger = logging.getLogger(__name__)

class SecurityUtils:
    """Security utilities for encryption and hashing"""
    
    @staticmethod
    def generate_password_hash(password: str) -> str:
        """Generate secure password hash using bcrypt"""
        if not password:
            raise ValueError("Password cannot be empty")
        
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=12)
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        if not password or not password_hash:
            return False
        
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                password_hash.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure random token"""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_encryption_key() -> bytes:
        """Generate encryption key for Fernet"""
        return Fernet.generate_key()
    
    @staticmethod
    def encrypt_data(data: str, key: bytes) -> str:
        """Encrypt sensitive data"""
        if not data:
            return ""
        
        try:
            fernet = Fernet(key)
            encrypted_data = fernet.encrypt(data.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return ""
    
    @staticmethod
    def decrypt_data(encrypted_data: str, key: bytes) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return ""
        
        try:
            fernet = Fernet(key)
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
            decrypted_data = fernet.decrypt(decoded_data)
            return decrypted_data.decode('utf-8')
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return ""
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate CSRF token"""
        return secrets.token_hex(16)
    
    @staticmethod
    def hash_sensitive_data(data: str, salt: str = None) -> str:
        """Hash sensitive data with optional salt"""
        if not data:
            return ""
        
        if not salt:
            salt = secrets.token_hex(16)
        
        # Use PBKDF2 for key derivation
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode('utf-8'),
            iterations=100000,
        )
        key = kdf.derive(data.encode('utf-8'))
        return base64.urlsafe_b64encode(key).decode('utf-8')
