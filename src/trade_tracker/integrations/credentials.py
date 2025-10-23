"""Secure credential manager for broker integrations."""

import json
from pathlib import Path
from typing import Dict, Any, List

from trade_tracker.database.encryption import DatabaseEncryption
from trade_tracker.integrations.exceptions import CredentialError


class CredentialManager:
    """
    Manages encrypted broker credentials.

    Stores broker credentials (API keys, passwords, tokens) in encrypted files.
    Each broker has its own credential file, encrypted with a user password.
    Uses AES-256-GCM encryption via DatabaseEncryption.
    """

    def __init__(self, storage_dir: Path = None):
        """
        Initialize credential manager.

        Args:
            storage_dir: Directory for storing encrypted credentials.
                        Defaults to ~/.trade_tracker/credentials/
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".trade_tracker" / "credentials"

        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def store_credentials(
        self,
        broker_name: str,
        credentials: Dict[str, Any],
        password: str
    ) -> None:
        """
        Store broker credentials encrypted with password.

        Args:
            broker_name: Broker identifier (e.g., 'ibkr', 'moomoo')
            credentials: Dictionary of credential data
            password: Master password for encryption

        Raises:
            CredentialError: If credentials are invalid or encryption fails
        """
        # Validate inputs
        if not credentials:
            raise CredentialError("Cannot store empty credentials")

        if not password or not password.strip():
            raise CredentialError("Password is required and cannot be empty")

        if not broker_name or not broker_name.strip():
            raise CredentialError("Broker name is required")

        try:
            # Convert credentials to JSON
            credentials_json = json.dumps(credentials)
            credentials_bytes = credentials_json.encode('utf-8')

            # Generate encryption key from password
            encryption_key = DatabaseEncryption.derive_key_from_password(
                password,
                salt=broker_name.encode('utf-8')  # Use broker name as salt
            )

            # Encrypt credentials
            encrypted_data = DatabaseEncryption.encrypt_data(
                credentials_bytes,
                encryption_key
            )

            # Write to file
            credential_file = self.storage_dir / f"{broker_name}.cred"
            with open(credential_file, 'wb') as f:
                f.write(encrypted_data)

        except Exception as e:
            raise CredentialError(f"Failed to store credentials: {str(e)}")

    def retrieve_credentials(
        self,
        broker_name: str,
        password: str
    ) -> Dict[str, Any]:
        """
        Retrieve and decrypt broker credentials.

        Args:
            broker_name: Broker identifier
            password: Master password for decryption

        Returns:
            Dictionary of credential data

        Raises:
            CredentialError: If credentials not found or decryption fails
        """
        credential_file = self.storage_dir / f"{broker_name}.cred"

        if not credential_file.exists():
            raise CredentialError(
                f"Credentials for broker '{broker_name}' not found"
            )

        try:
            # Read encrypted data
            with open(credential_file, 'rb') as f:
                encrypted_data = f.read()

            # Generate decryption key from password
            decryption_key = DatabaseEncryption.derive_key_from_password(
                password,
                salt=broker_name.encode('utf-8')
            )

            # Decrypt credentials
            decrypted_bytes = DatabaseEncryption.decrypt_data(
                encrypted_data,
                decryption_key
            )

            # Parse JSON
            credentials_json = decrypted_bytes.decode('utf-8')
            credentials = json.loads(credentials_json)

            return credentials

        except json.JSONDecodeError as e:
            raise CredentialError(f"Invalid credential data: {str(e)}")
        except Exception as e:
            # Could be wrong password or corrupted file
            raise CredentialError(
                f"Failed to retrieve credentials - decryption failed or incorrect password: {str(e)}"
            )

    def delete_credentials(self, broker_name: str) -> None:
        """
        Delete stored broker credentials.

        Args:
            broker_name: Broker identifier

        Raises:
            CredentialError: If credentials not found
        """
        credential_file = self.storage_dir / f"{broker_name}.cred"

        if not credential_file.exists():
            raise CredentialError(
                f"Credentials for broker '{broker_name}' not found or does not exist"
            )

        credential_file.unlink()

    def list_brokers(self) -> List[str]:
        """
        List all brokers with stored credentials.

        Returns:
            List of broker names
        """
        credential_files = self.storage_dir.glob("*.cred")
        return [f.stem for f in credential_files]

    def has_credentials(self, broker_name: str) -> bool:
        """
        Check if credentials exist for a broker.

        Args:
            broker_name: Broker identifier

        Returns:
            True if credentials exist
        """
        credential_file = self.storage_dir / f"{broker_name}.cred"
        return credential_file.exists()
