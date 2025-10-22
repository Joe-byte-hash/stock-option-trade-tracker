"""Database encryption module using AES-256."""

import base64
import os
from pathlib import Path
from typing import Union

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class DatabaseEncryption:
    """Handles database encryption and decryption using AES-256."""

    @staticmethod
    def generate_key() -> bytes:
        """
        Generate a new random 256-bit encryption key.

        Returns:
            bytes: 32-byte encryption key
        """
        return os.urandom(32)

    @staticmethod
    def derive_key_from_password(password: str, salt: bytes, iterations: int = 100000) -> bytes:
        """
        Derive an encryption key from a password using PBKDF2.

        Args:
            password: User password
            salt: Random salt (should be at least 16 bytes)
            iterations: Number of PBKDF2 iterations (default: 100000)

        Returns:
            bytes: 32-byte derived key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend(),
        )
        return kdf.derive(password.encode())

    @staticmethod
    def save_key(key: bytes, key_file: Union[str, Path]) -> None:
        """
        Save encryption key to a file.

        Args:
            key: Encryption key to save
            key_file: Path to key file

        Note:
            The key file should be kept secure and not committed to version control.
        """
        key_path = Path(key_file)
        key_path.parent.mkdir(parents=True, exist_ok=True)

        with open(key_path, "wb") as f:
            f.write(key)

        # Set restrictive permissions (owner read/write only)
        os.chmod(key_path, 0o600)

    @staticmethod
    def load_key(key_file: Union[str, Path]) -> bytes:
        """
        Load encryption key from a file.

        Args:
            key_file: Path to key file

        Returns:
            bytes: Encryption key
        """
        with open(key_file, "rb") as f:
            return f.read()

    @staticmethod
    def encrypt_data(plaintext: bytes, key: bytes) -> bytes:
        """
        Encrypt data using AES-256-GCM.

        Args:
            plaintext: Data to encrypt
            key: 32-byte encryption key

        Returns:
            bytes: IV (12 bytes) + tag (16 bytes) + ciphertext

        Note:
            Uses AES-GCM for authenticated encryption.
        """
        # Generate random IV (12 bytes for GCM)
        iv = os.urandom(12)

        # Create cipher
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # Encrypt
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()

        # Return IV + tag + ciphertext
        return iv + encryptor.tag + ciphertext

    @staticmethod
    def decrypt_data(ciphertext_with_iv: bytes, key: bytes) -> bytes:
        """
        Decrypt data using AES-256-GCM.

        Args:
            ciphertext_with_iv: IV + tag + ciphertext
            key: 32-byte encryption key

        Returns:
            bytes: Decrypted plaintext

        Raises:
            Exception: If decryption fails (wrong key or tampered data)
        """
        # Extract IV, tag, and ciphertext
        iv = ciphertext_with_iv[:12]
        tag = ciphertext_with_iv[12:28]
        ciphertext = ciphertext_with_iv[28:]

        # Create cipher
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()

        # Decrypt
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext

    @staticmethod
    def encrypt_string(plaintext: str, key: bytes) -> str:
        """
        Encrypt a string and return base64-encoded ciphertext.

        Args:
            plaintext: String to encrypt
            key: 32-byte encryption key

        Returns:
            str: Base64-encoded ciphertext
        """
        ciphertext = DatabaseEncryption.encrypt_data(plaintext.encode(), key)
        return base64.b64encode(ciphertext).decode("utf-8")

    @staticmethod
    def decrypt_string(ciphertext_b64: str, key: bytes) -> str:
        """
        Decrypt a base64-encoded ciphertext to string.

        Args:
            ciphertext_b64: Base64-encoded ciphertext
            key: 32-byte encryption key

        Returns:
            str: Decrypted plaintext string
        """
        ciphertext = base64.b64decode(ciphertext_b64)
        plaintext = DatabaseEncryption.decrypt_data(ciphertext, key)
        return plaintext.decode("utf-8")
