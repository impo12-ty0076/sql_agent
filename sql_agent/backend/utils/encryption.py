"""
Encryption utilities for securely storing sensitive information
"""
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)

# Get encryption key from environment variable or use a default for development
# In production, this should be set as an environment variable
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', 'default_encryption_key_for_development_only')
SALT = os.environ.get('ENCRYPTION_SALT', 'default_salt_for_development_only').encode()

# Generate a key from the encryption key and salt
def get_encryption_key():
    """
    Generate an encryption key from the environment variable
    
    Returns:
        Fernet key
    """
    try:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=SALT,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(ENCRYPTION_KEY.encode()))
        return key
    except Exception as e:
        logger.error(f"Error generating encryption key: {str(e)}")
        # In case of error, return a default key (this should never happen in production)
        return Fernet.generate_key()

# Initialize Fernet cipher with the key
cipher_suite = Fernet(get_encryption_key())

def encrypt_data(data: str) -> str:
    """
    Encrypt data
    
    Args:
        data: Data to encrypt
        
    Returns:
        Encrypted data as string
    """
    try:
        encrypted_data = cipher_suite.encrypt(data.encode())
        return encrypted_data.decode()
    except Exception as e:
        logger.error(f"Error encrypting data: {str(e)}")
        # Return the original data if encryption fails (this should never happen in production)
        return f"ENCRYPTION_FAILED:{data}"

def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypt data
    
    Args:
        encrypted_data: Encrypted data
        
    Returns:
        Decrypted data
    """
    try:
        # Check if encryption failed
        if encrypted_data.startswith("ENCRYPTION_FAILED:"):
            return encrypted_data[18:]  # Return the original data
            
        decrypted_data = cipher_suite.decrypt(encrypted_data.encode())
        return decrypted_data.decode()
    except Exception as e:
        logger.error(f"Error decrypting data: {str(e)}")
        return "DECRYPTION_FAILED"