"""Tests for Interactive Brokers integration."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date
from decimal import Decimal

from trade_tracker.integrations.ibkr import IBKRBroker
from trade_tracker.integrations.exceptions import (
    BrokerConnectionError,
    BrokerAuthenticationError,
    BrokerDataError,
)
from trade_tracker.models.trade import StockTrade, OptionTrade, TradeType, OptionType
from trade_tracker.models.position import Position


@pytest.fixture
def ibkr_credentials():
    """Sample IBKR credentials."""
    return {
        "host": "127.0.0.1",
        "port": 7497,  # IB Gateway paper trading port
        "client_id": 1
    }


@pytest.fixture
def mock_ib_app():
    """Mock IB API app."""
    with patch('trade_tracker.integrations.ibkr.EClient') as mock_client:
        with patch('trade_tracker.integrations.ibkr.EWrapper') as mock_wrapper:
            yield mock_client, mock_wrapper


class TestIBKRConnection:
    """Test IBKR connection functionality."""

    def test_create_ibkr_broker(self, ibkr_credentials):
        """Test creating IBKR broker instance."""
        broker = IBKRBroker(ibkr_credentials)
        assert broker is not None
        assert not broker.is_connected()

    def test_connect_success(self, ibkr_credentials, mock_ib_app):
        """Test successful connection to IBKR."""
        broker = IBKRBroker(ibkr_credentials)

        # Mock successful connection
        with patch.object(broker, '_connect_and_wait', return_value=True):
            result = broker.connect()
            assert result is True
            assert broker.is_connected()

    def test_connect_failure(self, ibkr_credentials):
        """Test connection failure."""
        broker = IBKRBroker(ibkr_credentials)

        # Mock connection failure
        with patch.object(broker, '_connect_and_wait', return_value=False):
            with pytest.raises(BrokerConnectionError, match="Failed to connect"):
                broker.connect()

    def test_disconnect(self, ibkr_credentials):
        """Test disconnecting from IBKR."""
        broker = IBKRBroker(ibkr_credentials)

        # Mock connection and disconnection
        with patch.object(broker, '_connect_and_wait', return_value=True):
            broker.connect()
            assert broker.is_connected()

            broker.disconnect()
            assert not broker.is_connected()

    def test_context_manager(self, ibkr_credentials):
        """Test using IBKR broker as context manager."""
        with patch.object(IBKRBroker, '_connect_and_wait', return_value=True):
            with IBKRBroker(ibkr_credentials) as broker:
                assert broker.is_connected()

            # Should be disconnected after exiting context
            assert not broker.is_connected()


class TestIBKRTradeImport:
    """Test IBKR trade import functionality."""

    def test_fetch_stock_trades(self, ibkr_credentials):
        """Test fetching stock trades from IBKR."""
        broker = IBKRBroker(ibkr_credentials)

        # Mock executions data
        mock_executions = [
            {
                'symbol': 'AAPL',
                'secType': 'STK',
                'side': 'BOT',
                'shares': 100,
                'price': 150.50,
                'time': '20240115  10:30:00',
                'commission': 1.00
            },
            {
                'symbol': 'AAPL',
                'secType': 'STK',
                'side': 'SLD',
                'shares': 100,
                'price': 155.75,
                'time': '20240120  14:30:00',
                'commission': 1.00
            }
        ]

        with patch.object(broker, '_fetch_executions', return_value=mock_executions):
            with patch.object(broker, 'is_connected', return_value=True):
                trades = broker.fetch_trades()

                assert len(trades) == 2
                assert all(isinstance(t, StockTrade) for t in trades)
                assert trades[0].symbol == 'AAPL'
                assert trades[0].trade_type == TradeType.BUY
                assert trades[0].quantity == 100
                assert trades[0].price == Decimal('150.50')
                assert trades[1].trade_type == TradeType.SELL

    def test_fetch_option_trades(self, ibkr_credentials):
        """Test fetching option trades from IBKR."""
        broker = IBKRBroker(ibkr_credentials)

        # Mock option executions
        mock_executions = [
            {
                'symbol': 'TSLA',
                'secType': 'OPT',
                'side': 'BOT',
                'shares': 10,
                'price': 5.50,
                'strike': 250.0,
                'right': 'C',  # Call
                'expiry': '20240315',
                'time': '20240110  09:30:00',
                'commission': 6.50
            }
        ]

        with patch.object(broker, '_fetch_executions', return_value=mock_executions):
            with patch.object(broker, 'is_connected', return_value=True):
                trades = broker.fetch_trades()

                assert len(trades) == 1
                assert isinstance(trades[0], OptionTrade)
                assert trades[0].symbol == 'TSLA'
                assert trades[0].option_type == OptionType.CALL
                assert trades[0].strike == Decimal('250.0')
                assert trades[0].quantity == 10

    def test_fetch_trades_with_date_filter(self, ibkr_credentials):
        """Test fetching trades with date range filter."""
        broker = IBKRBroker(ibkr_credentials)

        start_date = datetime(2024, 1, 15)
        end_date = datetime(2024, 1, 20)

        with patch.object(broker, '_fetch_executions') as mock_fetch:
            with patch.object(broker, 'is_connected', return_value=True):
                mock_fetch.return_value = []
                broker.fetch_trades(start_date=start_date, end_date=end_date)

                # Verify that date filter was passed
                mock_fetch.assert_called_once()
                call_args = mock_fetch.call_args
                assert 'start_date' in call_args.kwargs or len(call_args.args) > 0

    def test_fetch_trades_when_not_connected_fails(self, ibkr_credentials):
        """Test that fetching trades when not connected raises error."""
        broker = IBKRBroker(ibkr_credentials)

        with pytest.raises(BrokerConnectionError, match="Not connected"):
            broker.fetch_trades()

    def test_parse_invalid_execution_data(self, ibkr_credentials):
        """Test handling of invalid execution data."""
        broker = IBKRBroker(ibkr_credentials)

        # Mock invalid/incomplete execution data
        mock_executions = [
            {
                'symbol': 'AAPL',
                # Missing required fields
            }
        ]

        with patch.object(broker, '_fetch_executions', return_value=mock_executions):
            with patch.object(broker, 'is_connected', return_value=True):
                # Should skip invalid executions or raise BrokerDataError
                with pytest.raises(BrokerDataError):
                    broker.fetch_trades()


class TestIBKRPositionSync:
    """Test IBKR position synchronization."""

    def test_fetch_positions(self, ibkr_credentials):
        """Test fetching current positions from IBKR."""
        broker = IBKRBroker(ibkr_credentials)

        # Mock position data
        mock_positions = [
            {
                'symbol': 'AAPL',
                'secType': 'STK',
                'position': 100,
                'avgCost': 150.25,
                'marketPrice': 155.50,
                'marketValue': 15550.00,
                'unrealizedPNL': 525.00
            },
            {
                'symbol': 'GOOGL',
                'secType': 'STK',
                'position': -50,  # Short position
                'avgCost': 140.00,
                'marketPrice': 138.00,
                'marketValue': -6900.00,
                'unrealizedPNL': 100.00
            }
        ]

        with patch.object(broker, '_fetch_positions_data', return_value=mock_positions):
            with patch.object(broker, 'is_connected', return_value=True):
                positions = broker.fetch_positions()

                assert len(positions) == 2
                assert all(isinstance(p, Position) for p in positions)
                assert positions[0].symbol == 'AAPL'
                assert positions[0].quantity == 100
                assert positions[0].average_cost == Decimal('150.25')
                assert positions[1].quantity == -50  # Short

    def test_fetch_positions_when_not_connected_fails(self, ibkr_credentials):
        """Test that fetching positions when not connected raises error."""
        broker = IBKRBroker(ibkr_credentials)

        with pytest.raises(BrokerConnectionError, match="Not connected"):
            broker.fetch_positions()


class TestIBKRAccountInfo:
    """Test IBKR account information."""

    def test_fetch_account_info(self, ibkr_credentials):
        """Test fetching account information."""
        broker = IBKRBroker(ibkr_credentials)

        # Mock account data
        mock_account_data = {
            'account_id': 'DU123456',
            'net_liquidation': 50000.00,
            'total_cash_value': 25000.00,
            'buying_power': 100000.00,
            'gross_position_value': 25000.00
        }

        with patch.object(broker, '_fetch_account_data', return_value=mock_account_data):
            with patch.object(broker, 'is_connected', return_value=True):
                account_info = broker.fetch_account_info()

                assert account_info['account_id'] == 'DU123456'
                assert account_info['net_liquidation'] == 50000.00
                assert account_info['buying_power'] == 100000.00


class TestIBKRDataMapping:
    """Test IBKR data mapping to our models."""

    def test_map_buy_side_to_trade_type(self, ibkr_credentials):
        """Test mapping IBKR buy/sell sides to our TradeType."""
        broker = IBKRBroker(ibkr_credentials)

        # Test stock buy/sell mapping
        assert broker._map_side_to_trade_type('BOT', 'STK') == TradeType.BUY
        assert broker._map_side_to_trade_type('SLD', 'STK') == TradeType.SELL

        # Test option buy/sell mapping
        assert broker._map_side_to_trade_type('BOT', 'OPT') == TradeType.BUY_TO_OPEN
        assert broker._map_side_to_trade_type('SLD', 'OPT') == TradeType.SELL_TO_CLOSE

    def test_map_option_right_to_option_type(self, ibkr_credentials):
        """Test mapping IBKR option right to our OptionType."""
        broker = IBKRBroker(ibkr_credentials)

        assert broker._map_option_right('C') == OptionType.CALL
        assert broker._map_option_right('P') == OptionType.PUT

    def test_parse_ibkr_datetime(self, ibkr_credentials):
        """Test parsing IBKR datetime format."""
        broker = IBKRBroker(ibkr_credentials)

        # IBKR format: "YYYYMMDD  HH:MM:SS"
        dt = broker._parse_datetime('20240115  10:30:00')

        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15
        assert dt.hour == 10
        assert dt.minute == 30
