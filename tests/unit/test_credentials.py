"""Tests for broker credential manager."""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from trade_tracker.integrations.credentials import CredentialManager
from trade_tracker.integrations.exceptions import CredentialError


@pytest.fixture
def temp_credential_dir():
    """Create temporary directory for credential storage."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def credential_manager(temp_credential_dir):
    """Create credential manager with temporary storage."""
    return CredentialManager(storage_dir=temp_credential_dir)


class TestCredentialManager:
    """Test CredentialManager class."""

    def test_create_credential_manager(self, credential_manager):
        """Test creating credential manager."""
        assert credential_manager is not None
        assert credential_manager.storage_dir.exists()

    def test_store_credentials(self, credential_manager):
        """Test storing broker credentials."""
        credentials = {
            "broker": "ibkr",
            "username": "testuser",
            "password": "testpass123",
            "api_key": "test_api_key_xyz"
        }
        password = "master_password_123"

        credential_manager.store_credentials("ibkr", credentials, password)

        # Verify credentials file was created
        cred_file = credential_manager.storage_dir / "ibkr.cred"
        assert cred_file.exists()

    def test_retrieve_credentials(self, credential_manager):
        """Test retrieving stored credentials."""
        credentials = {
            "broker": "ibkr",
            "username": "testuser",
            "password": "testpass123",
            "api_key": "test_api_key_xyz"
        }
        password = "master_password_123"

        # Store credentials
        credential_manager.store_credentials("ibkr", credentials, password)

        # Retrieve credentials
        retrieved = credential_manager.retrieve_credentials("ibkr", password)

        assert retrieved == credentials
        assert retrieved["username"] == "testuser"
        assert retrieved["password"] == "testpass123"

    def test_retrieve_with_wrong_password_fails(self, credential_manager):
        """Test that retrieving with wrong password fails."""
        credentials = {
            "broker": "ibkr",
            "username": "testuser",
            "password": "testpass123"
        }
        password = "master_password_123"
        wrong_password = "wrong_password"

        # Store credentials
        credential_manager.store_credentials("ibkr", credentials, password)

        # Try to retrieve with wrong password
        with pytest.raises(CredentialError, match="decryption failed|incorrect password"):
            credential_manager.retrieve_credentials("ibkr", wrong_password)

    def test_retrieve_nonexistent_broker_fails(self, credential_manager):
        """Test retrieving credentials for non-existent broker."""
        with pytest.raises(CredentialError, match="not found|does not exist"):
            credential_manager.retrieve_credentials("nonexistent", "password")

    def test_list_configured_brokers(self, credential_manager):
        """Test listing configured brokers."""
        # Initially empty
        assert credential_manager.list_brokers() == []

        # Add some brokers
        credential_manager.store_credentials(
            "ibkr",
            {"username": "user1"},
            "password1"
        )
        credential_manager.store_credentials(
            "moomoo",
            {"username": "user2"},
            "password2"
        )

        # List should contain both
        brokers = credential_manager.list_brokers()
        assert len(brokers) == 2
        assert "ibkr" in brokers
        assert "moomoo" in brokers

    def test_delete_credentials(self, credential_manager):
        """Test deleting stored credentials."""
        credentials = {"username": "testuser"}
        password = "password123"

        # Store credentials
        credential_manager.store_credentials("ibkr", credentials, password)
        assert "ibkr" in credential_manager.list_brokers()

        # Delete credentials
        credential_manager.delete_credentials("ibkr")
        assert "ibkr" not in credential_manager.list_brokers()

    def test_delete_nonexistent_broker_fails(self, credential_manager):
        """Test deleting non-existent broker credentials."""
        with pytest.raises(CredentialError, match="not found|does not exist"):
            credential_manager.delete_credentials("nonexistent")

    def test_update_credentials(self, credential_manager):
        """Test updating existing credentials."""
        old_credentials = {"username": "olduser", "password": "oldpass"}
        new_credentials = {"username": "newuser", "password": "newpass"}
        password = "master_password"

        # Store initial credentials
        credential_manager.store_credentials("ibkr", old_credentials, password)

        # Update credentials
        credential_manager.store_credentials("ibkr", new_credentials, password)

        # Retrieve and verify
        retrieved = credential_manager.retrieve_credentials("ibkr", password)
        assert retrieved["username"] == "newuser"
        assert retrieved["password"] == "newpass"

    def test_credentials_are_encrypted(self, credential_manager):
        """Test that credentials are encrypted on disk."""
        credentials = {"username": "testuser", "password": "secret123"}
        password = "master_password"

        credential_manager.store_credentials("ibkr", credentials, password)

        # Read file directly
        cred_file = credential_manager.storage_dir / "ibkr.cred"
        with open(cred_file, 'rb') as f:
            file_content = f.read()

        # Verify that plaintext credentials are not in file
        assert b"testuser" not in file_content
        assert b"secret123" not in file_content

    def test_store_empty_credentials_fails(self, credential_manager):
        """Test that storing empty credentials fails."""
        with pytest.raises(CredentialError, match="empty|invalid"):
            credential_manager.store_credentials("ibkr", {}, "password")

    def test_store_with_empty_password_fails(self, credential_manager):
        """Test that storing with empty password fails."""
        credentials = {"username": "testuser"}

        with pytest.raises(CredentialError, match="[Pp]assword.*empty|[Pp]assword.*required"):
            credential_manager.store_credentials("ibkr", credentials, "")

    def test_multiple_brokers_independent(self, credential_manager):
        """Test that multiple broker credentials are independent."""
        ibkr_creds = {"username": "ibkr_user", "api_key": "ibkr_key"}
        moomoo_creds = {"username": "moomoo_user", "token": "moomoo_token"}
        password = "master_password"

        # Store different credentials for different brokers
        credential_manager.store_credentials("ibkr", ibkr_creds, password)
        credential_manager.store_credentials("moomoo", moomoo_creds, password)

        # Retrieve and verify they're independent
        ibkr_retrieved = credential_manager.retrieve_credentials("ibkr", password)
        moomoo_retrieved = credential_manager.retrieve_credentials("moomoo", password)

        assert ibkr_retrieved == ibkr_creds
        assert moomoo_retrieved == moomoo_creds
        assert "api_key" in ibkr_retrieved
        assert "token" in moomoo_retrieved
