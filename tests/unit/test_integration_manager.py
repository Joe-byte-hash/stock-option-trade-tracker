"""Tests for broker integration manager."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
import tempfile
import shutil

from trade_tracker.integrations.manager import IntegrationManager
from trade_tracker.integrations.exceptions import (
    BrokerConnectionError,
    DuplicateTradeError,
)
from trade_tracker.models.trade import StockTrade, TradeType
from trade_tracker.models.position import Position
from trade_tracker.models.account import Account


@pytest.fixture
def temp_db_path():
    """Create temporary database path."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_trades.db"
    yield db_path
    shutil.rmtree(temp_dir)


@pytest.fixture
def integration_manager(temp_db_path):
    """Create integration manager with temporary database."""
    return IntegrationManager(db_path=str(temp_db_path))


@pytest.fixture
def mock_broker():
    """Create mock broker."""
    broker = Mock()
    broker.is_connected.return_value = True
    return broker


@pytest.fixture
def sample_trades():
    """Create sample trades."""
    return [
        StockTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY,
            quantity=100,
            price=Decimal("150.00"),
            commission=Decimal("1.00"),
            trade_date=datetime(2024, 1, 15, 10, 30),
            account_id=1
        ),
        StockTrade(
            symbol="AAPL",
            trade_type=TradeType.SELL,
            quantity=100,
            price=Decimal("155.00"),
            commission=Decimal("1.00"),
            trade_date=datetime(2024, 1, 20, 14, 30),
            account_id=1
        ),
    ]


class TestIntegrationManager:
    """Test IntegrationManager class."""

    def test_create_integration_manager(self, integration_manager):
        """Test creating integration manager."""
        assert integration_manager is not None
        assert integration_manager.db is not None

    def test_import_trades_from_broker(self, integration_manager, mock_broker, sample_trades):
        """Test importing trades from broker."""
        # Mock broker to return sample trades
        mock_broker.fetch_trades.return_value = sample_trades

        # Import trades
        result = integration_manager.import_trades(mock_broker, account_id=1)

        assert result['success'] is True
        assert result['imported_count'] == 2
        assert result['duplicate_count'] == 0
        assert result['error_count'] == 0

    def test_import_trades_detects_duplicates(self, integration_manager, mock_broker, sample_trades):
        """Test that duplicate trades are detected."""
        # Import trades first time
        mock_broker.fetch_trades.return_value = sample_trades
        result1 = integration_manager.import_trades(mock_broker, account_id=1)
        assert result1['imported_count'] == 2

        # Import same trades again - should detect duplicates
        result2 = integration_manager.import_trades(mock_broker, account_id=1)
        assert result2['imported_count'] == 0
        assert result2['duplicate_count'] == 2

    def test_import_trades_with_date_filter(self, integration_manager, mock_broker, sample_trades):
        """Test importing trades with date filter."""
        mock_broker.fetch_trades.return_value = sample_trades

        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        result = integration_manager.import_trades(
            mock_broker,
            account_id=1,
            start_date=start_date,
            end_date=end_date
        )

        # Verify broker was called with date filter
        mock_broker.fetch_trades.assert_called_once()
        call_kwargs = mock_broker.fetch_trades.call_args.kwargs
        assert 'start_date' in call_kwargs or len(mock_broker.fetch_trades.call_args.args) > 0

        assert result['success'] is True

    def test_import_trades_when_broker_not_connected_fails(self, integration_manager, mock_broker):
        """Test that import fails when broker not connected."""
        mock_broker.is_connected.return_value = False

        with pytest.raises(BrokerConnectionError, match="not connected"):
            integration_manager.import_trades(mock_broker, account_id=1)

    def test_import_positions_from_broker(self, integration_manager, mock_broker):
        """Test importing positions from broker."""
        # Mock positions
        from trade_tracker.models.trade import AssetType
        mock_positions = [
            Position(
                symbol="AAPL",
                asset_type=AssetType.STOCK,
                quantity=100,
                average_price=Decimal("150.00"),
                current_price=Decimal("155.00"),
                account_id=1
            )
        ]
        mock_broker.fetch_positions.return_value = mock_positions

        result = integration_manager.sync_positions(mock_broker, account_id=1)

        assert result['success'] is True
        assert result['synced_count'] == 1

    def test_import_with_connection_failure_returns_error(self, integration_manager, mock_broker):
        """Test that connection failures are handled gracefully."""
        mock_broker.fetch_trades.side_effect = BrokerConnectionError("Connection lost")

        result = integration_manager.import_trades(mock_broker, account_id=1)

        assert result['success'] is False
        assert 'error' in result
        assert 'Connection lost' in result['error']

    def test_duplicate_detection_by_symbol_date_price(self, integration_manager, mock_broker):
        """Test that duplicates are detected by symbol, date, and price."""
        trade1 = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY,
            quantity=100,
            price=Decimal("150.00"),
            commission=Decimal("1.00"),
            trade_date=datetime(2024, 1, 15, 10, 30),
            account_id=1
        )

        # Same trade (duplicate)
        trade2 = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY,
            quantity=100,
            price=Decimal("150.00"),
            commission=Decimal("1.00"),
            trade_date=datetime(2024, 1, 15, 10, 30),
            account_id=1
        )

        # Different trade (different price)
        trade3 = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY,
            quantity=100,
            price=Decimal("151.00"),  # Different price
            commission=Decimal("1.00"),
            trade_date=datetime(2024, 1, 15, 10, 30),
            account_id=1
        )

        # Import first trade
        mock_broker.fetch_trades.return_value = [trade1]
        result1 = integration_manager.import_trades(mock_broker, account_id=1)
        assert result1['imported_count'] == 1

        # Import duplicate - should be skipped
        mock_broker.fetch_trades.return_value = [trade2]
        result2 = integration_manager.import_trades(mock_broker, account_id=1)
        assert result2['duplicate_count'] == 1

        # Import different trade - should be imported
        mock_broker.fetch_trades.return_value = [trade3]
        result3 = integration_manager.import_trades(mock_broker, account_id=1)
        assert result3['imported_count'] == 1

    def test_get_import_history(self, integration_manager, mock_broker, sample_trades):
        """Test getting import history."""
        # Import some trades
        mock_broker.fetch_trades.return_value = sample_trades
        integration_manager.import_trades(mock_broker, account_id=1)

        # Get history
        history = integration_manager.get_import_history(limit=10)

        assert len(history) > 0
        assert 'timestamp' in history[0]
        assert 'broker' in history[0]
        assert 'imported_count' in history[0]

    def test_import_with_invalid_trades_skips_them(self, integration_manager, mock_broker):
        """Test that invalid trades are skipped without crashing."""
        # Mix of valid and invalid trades
        valid_trade = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY,
            quantity=100,
            price=Decimal("150.00"),
            commission=Decimal("1.00"),
            trade_date=datetime(2024, 1, 15),
            account_id=1
        )

        mock_broker.fetch_trades.return_value = [valid_trade, None]  # One valid, one None

        result = integration_manager.import_trades(mock_broker, account_id=1)

        # Should import the valid one and skip the invalid
        assert result['imported_count'] == 1

    def test_import_trades_with_symbol_filter(self, integration_manager, mock_broker):
        """Test importing trades with symbol filter."""
        aapl_trade = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY,
            quantity=100,
            price=Decimal("150.00"),
            commission=Decimal("1.00"),
            trade_date=datetime.now(),
            account_id=1
        )

        mock_broker.fetch_trades.return_value = [aapl_trade]

        result = integration_manager.import_trades(
            mock_broker,
            account_id=1,
            symbol="AAPL"
        )

        # Verify broker was called with symbol filter
        mock_broker.fetch_trades.assert_called_once()
        call_kwargs = mock_broker.fetch_trades.call_args.kwargs
        assert call_kwargs.get('symbol') == "AAPL"

        assert result['success'] is True
        assert result['imported_count'] == 1
