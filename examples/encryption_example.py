"""Example: Database encryption and security."""

import os
from pathlib import Path

from trade_tracker.database.encryption import DatabaseEncryption


def generate_key_example():
    """Example: Generate and save encryption key."""
    print("=" * 60)
    print("Encryption Key Generation")
    print("=" * 60)

    # Generate a random 256-bit key
    key = DatabaseEncryption.generate_key()
    print(f"\n✓ Generated 256-bit encryption key")
    print(f"  Key length: {len(key)} bytes")

    # Save key to file
    key_path = Path("config/.db_encryption.key")
    key_path.parent.mkdir(parents=True, exist_ok=True)

    DatabaseEncryption.save_key(key, str(key_path))
    print(f"✓ Saved key to: {key_path}")
    print(f"  File permissions: {oct(os.stat(key_path).st_mode)[-3:]}")

    return key, key_path


def password_based_key_example():
    """Example: Derive key from password."""
    print("\n" + "=" * 60)
    print("Password-Based Key Derivation (PBKDF2)")
    print("=" * 60)

    # User password
    password = "MySecurePassword123!"
    salt = os.urandom(16)

    print(f"\n✓ Using password-based key derivation")
    print(f"  Algorithm: PBKDF2-HMAC-SHA256")
    print(f"  Iterations: 100,000")
    print(f"  Salt length: {len(salt)} bytes")

    # Derive key
    key = DatabaseEncryption.derive_key_from_password(password, salt)
    print(f"✓ Derived 256-bit key from password")

    # Same password + salt = same key (deterministic)
    key2 = DatabaseEncryption.derive_key_from_password(password, salt)
    assert key == key2
    print(f"✓ Verified: Same password + salt = same key")

    # Different password = different key
    key3 = DatabaseEncryption.derive_key_from_password("DifferentPassword", salt)
    assert key != key3
    print(f"✓ Verified: Different password = different key")

    # Save salt (needed to derive key again)
    salt_path = Path("config/.salt")
    with open(salt_path, "wb") as f:
        f.write(salt)
    os.chmod(salt_path, 0o600)
    print(f"✓ Saved salt to: {salt_path}")

    return key, salt


def encrypt_decrypt_example(key):
    """Example: Encrypt and decrypt data."""
    print("\n" + "=" * 60)
    print("Data Encryption/Decryption")
    print("=" * 60)

    # Sensitive trade data
    plaintext = "AAPL 100 shares @ $150.50 - Profit: $1,525.00"
    print(f"\n📝 Original data: {plaintext}")

    # Encrypt
    ciphertext = DatabaseEncryption.encrypt_string(plaintext, key)
    print(f"\n🔒 Encrypted (base64): {ciphertext[:50]}...")
    print(f"  Ciphertext length: {len(ciphertext)} characters")

    # Decrypt
    decrypted = DatabaseEncryption.decrypt_string(ciphertext, key)
    print(f"\n🔓 Decrypted: {decrypted}")

    assert plaintext == decrypted
    print(f"✓ Verification: Decryption successful")


def wrong_key_example(key):
    """Example: Attempting decryption with wrong key."""
    print("\n" + "=" * 60)
    print("Security: Wrong Key Protection")
    print("=" * 60)

    # Encrypt with correct key
    plaintext = "Sensitive trading data"
    ciphertext = DatabaseEncryption.encrypt_string(plaintext, key)
    print(f"\n✓ Data encrypted with Key A")

    # Try to decrypt with wrong key
    wrong_key = DatabaseEncryption.generate_key()
    print(f"✗ Attempting to decrypt with Key B (wrong key)")

    try:
        decrypted = DatabaseEncryption.decrypt_string(ciphertext, wrong_key)
        print(f"  ERROR: Should have failed!")
    except Exception as e:
        print(f"✓ Decryption failed as expected")
        print(f"  Error: {type(e).__name__}")
        print(f"\n  🛡️  Your data is protected from unauthorized access")


def load_key_example(key_path):
    """Example: Load key from file."""
    print("\n" + "=" * 60)
    print("Loading Key from File")
    print("=" * 60)

    # Load key
    loaded_key = DatabaseEncryption.load_key(key_path)
    print(f"\n✓ Loaded encryption key from: {key_path}")
    print(f"  Key length: {len(loaded_key)} bytes")

    return loaded_key


def binary_data_example(key):
    """Example: Encrypt binary data."""
    print("\n" + "=" * 60)
    print("Binary Data Encryption")
    print("=" * 60)

    # Binary data (e.g., serialized trade data)
    binary_data = b"Binary trade data: \x00\x01\x02\x03"
    print(f"\n📦 Original binary data: {binary_data}")

    # Encrypt
    encrypted = DatabaseEncryption.encrypt_data(binary_data, key)
    print(f"🔒 Encrypted: {len(encrypted)} bytes")

    # Decrypt
    decrypted = DatabaseEncryption.decrypt_data(encrypted, key)
    print(f"🔓 Decrypted: {decrypted}")

    assert binary_data == decrypted
    print(f"✓ Binary data encryption successful")


def main():
    """Run all encryption examples."""
    print("\n" + "=" * 60)
    print("Trade Tracker - Encryption & Security Examples")
    print("=" * 60)

    # Generate and save key
    key, key_path = generate_key_example()

    # Password-based key derivation
    pwd_key, salt = password_based_key_example()

    # Encrypt/decrypt
    encrypt_decrypt_example(key)

    # Binary data
    binary_data_example(key)

    # Wrong key protection
    wrong_key_example(key)

    # Load key
    loaded_key = load_key_example(key_path)

    print("\n" + "=" * 60)
    print("✓ All encryption examples completed successfully!")
    print("\n🔐 Security Features:")
    print("  • AES-256-GCM authenticated encryption")
    print("  • PBKDF2 password-based key derivation")
    print("  • 100,000 iterations for password hashing")
    print("  • Random IV (Initialization Vector) per encryption")
    print("  • Authentication tags prevent tampering")
    print("  • Secure file permissions (0600) for key files")
    print("=" * 60)


if __name__ == "__main__":
    main()
