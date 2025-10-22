"""Unit tests for database encryption (TDD approach)."""

import os
from pathlib import Path

import pytest

from trade_tracker.database.encryption import DatabaseEncryption


class TestDatabaseEncryption:
    """Test database encryption functionality."""

    def test_generate_key(self):
        """Test generating a new encryption key."""
        key = DatabaseEncryption.generate_key()
        assert isinstance(key, bytes)
        assert len(key) == 32  # 256-bit key

    def test_generate_key_from_password(self):
        """Test generating a key from a password."""
        password = "test_password_123"
        salt = os.urandom(16)

        key = DatabaseEncryption.derive_key_from_password(password, salt)
        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_key_derivation_is_deterministic(self):
        """Test that same password and salt produce same key."""
        password = "test_password_123"
        salt = os.urandom(16)

        key1 = DatabaseEncryption.derive_key_from_password(password, salt)
        key2 = DatabaseEncryption.derive_key_from_password(password, salt)

        assert key1 == key2

    def test_different_passwords_produce_different_keys(self):
        """Test that different passwords produce different keys."""
        salt = os.urandom(16)

        key1 = DatabaseEncryption.derive_key_from_password("password1", salt)
        key2 = DatabaseEncryption.derive_key_from_password("password2", salt)

        assert key1 != key2

    def test_save_and_load_key(self, tmp_path):
        """Test saving and loading encryption key."""
        key_file = tmp_path / "test.key"
        original_key = DatabaseEncryption.generate_key()

        # Save key
        DatabaseEncryption.save_key(original_key, str(key_file))
        assert key_file.exists()

        # Load key
        loaded_key = DatabaseEncryption.load_key(str(key_file))
        assert loaded_key == original_key

    def test_encrypt_decrypt_data(self, encryption_key):
        """Test encrypting and decrypting data."""
        plaintext = b"Sensitive trading data: AAPL 100 shares @ $150.50"

        # Encrypt
        ciphertext = DatabaseEncryption.encrypt_data(plaintext, encryption_key)
        assert ciphertext != plaintext
        assert isinstance(ciphertext, bytes)

        # Decrypt
        decrypted = DatabaseEncryption.decrypt_data(ciphertext, encryption_key)
        assert decrypted == plaintext

    def test_decrypt_with_wrong_key_fails(self, encryption_key):
        """Test that decryption with wrong key fails."""
        plaintext = b"Sensitive trading data"
        wrong_key = DatabaseEncryption.generate_key()

        ciphertext = DatabaseEncryption.encrypt_data(plaintext, encryption_key)

        with pytest.raises(Exception):  # Should raise decryption error
            DatabaseEncryption.decrypt_data(ciphertext, wrong_key)

    def test_encrypt_string(self, encryption_key):
        """Test encrypting and decrypting string data."""
        plaintext = "AAPL 100 shares @ $150.50"

        # Encrypt
        ciphertext = DatabaseEncryption.encrypt_string(plaintext, encryption_key)
        assert isinstance(ciphertext, str)  # Base64 encoded
        assert ciphertext != plaintext

        # Decrypt
        decrypted = DatabaseEncryption.decrypt_string(ciphertext, encryption_key)
        assert decrypted == plaintext
