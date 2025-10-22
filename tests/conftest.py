"""Pytest configuration and fixtures."""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_db_path() -> Generator[Path, None, None]:
    """Create a temporary database file path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    yield tmp_path

    # Cleanup
    if tmp_path.exists():
        tmp_path.unlink()


@pytest.fixture
def encryption_key() -> bytes:
    """Generate a test encryption key."""
    # Must be exactly 32 bytes for AES-256
    return b"12345678901234567890123456789012"


@pytest.fixture
def sample_trade_data() -> dict:
    """Sample trade data for testing."""
    return {
        "symbol": "AAPL",
        "asset_type": "stock",
        "trade_type": "buy",
        "quantity": 100,
        "price": 150.50,
        "commission": 1.00,
        "trade_date": "2024-01-15T10:30:00",
    }


@pytest.fixture
def sample_option_data() -> dict:
    """Sample option trade data for testing."""
    return {
        "symbol": "AAPL",
        "asset_type": "option",
        "trade_type": "buy_to_open",
        "quantity": 10,
        "price": 5.50,
        "strike": 155.00,
        "expiry": "2024-03-15",
        "option_type": "call",
        "commission": 6.50,
        "trade_date": "2024-01-15T10:30:00",
    }
