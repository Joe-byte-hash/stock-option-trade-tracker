"""Unit tests for data models (TDD approach)."""

from datetime import datetime, date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from trade_tracker.models.trade import (
    Trade,
    TradeType,
    AssetType,
    TradeStatus,
    OptionType,
    StockTrade,
    OptionTrade,
)
from trade_tracker.models.account import Account, BrokerType
from trade_tracker.models.position import Position, PositionStatus


class TestTradeEnums:
    """Test trade enumeration types."""

    def test_asset_type_values(self):
        """Test AssetType enum has required values."""
        assert AssetType.STOCK == "stock"
        assert AssetType.OPTION == "option"

    def test_trade_type_values(self):
        """Test TradeType enum has required values."""
        assert TradeType.BUY == "buy"
        assert TradeType.SELL == "sell"
        assert TradeType.BUY_TO_OPEN == "buy_to_open"
        assert TradeType.SELL_TO_CLOSE == "sell_to_close"
        assert TradeType.BUY_TO_CLOSE == "buy_to_close"
        assert TradeType.SELL_TO_OPEN == "sell_to_open"

    def test_trade_status_values(self):
        """Test TradeStatus enum has required values."""
        assert TradeStatus.OPEN == "open"
        assert TradeStatus.CLOSED == "closed"
        assert TradeStatus.CANCELLED == "cancelled"

    def test_option_type_values(self):
        """Test OptionType enum has required values."""
        assert OptionType.CALL == "call"
        assert OptionType.PUT == "put"


class TestStockTrade:
    """Test StockTrade model."""

    def test_create_stock_trade_valid(self, sample_trade_data):
        """Test creating a valid stock trade."""
        trade = StockTrade(**sample_trade_data)
        assert trade.symbol == "AAPL"
        assert trade.asset_type == AssetType.STOCK
        assert trade.quantity == 100
        assert trade.price == Decimal("150.50")
        assert trade.commission == Decimal("1.00")

    def test_stock_trade_cost_calculation(self, sample_trade_data):
        """Test stock trade total cost calculation."""
        trade = StockTrade(**sample_trade_data)
        # For buy: cost = quantity * price + commission
        expected_cost = Decimal("100") * Decimal("150.50") + Decimal("1.00")
        assert trade.total_cost == expected_cost

    def test_stock_trade_negative_quantity_fails(self, sample_trade_data):
        """Test that negative quantity raises validation error."""
        sample_trade_data["quantity"] = -100
        with pytest.raises(ValidationError):
            StockTrade(**sample_trade_data)

    def test_stock_trade_negative_price_fails(self, sample_trade_data):
        """Test that negative price raises validation error."""
        sample_trade_data["price"] = -150.50
        with pytest.raises(ValidationError):
            StockTrade(**sample_trade_data)

    def test_stock_trade_empty_symbol_fails(self, sample_trade_data):
        """Test that empty symbol raises validation error."""
        sample_trade_data["symbol"] = ""
        with pytest.raises(ValidationError):
            StockTrade(**sample_trade_data)


class TestOptionTrade:
    """Test OptionTrade model."""

    def test_create_option_trade_valid(self, sample_option_data):
        """Test creating a valid option trade."""
        trade = OptionTrade(**sample_option_data)
        assert trade.symbol == "AAPL"
        assert trade.asset_type == AssetType.OPTION
        assert trade.quantity == 10
        assert trade.price == Decimal("5.50")
        assert trade.strike == Decimal("155.00")
        assert trade.option_type == OptionType.CALL

    def test_option_trade_cost_calculation(self, sample_option_data):
        """Test option trade total cost calculation."""
        trade = OptionTrade(**sample_option_data)
        # For options: cost = quantity * price * 100 (contract multiplier) + commission
        expected_cost = Decimal("10") * Decimal("5.50") * Decimal("100") + Decimal("6.50")
        assert trade.total_cost == expected_cost

    def test_option_trade_requires_strike(self, sample_option_data):
        """Test that option trade requires strike price."""
        del sample_option_data["strike"]
        with pytest.raises(ValidationError):
            OptionTrade(**sample_option_data)

    def test_option_trade_requires_expiry(self, sample_option_data):
        """Test that option trade requires expiry date."""
        del sample_option_data["expiry"]
        with pytest.raises(ValidationError):
            OptionTrade(**sample_option_data)

    def test_option_trade_requires_option_type(self, sample_option_data):
        """Test that option trade requires option type (call/put)."""
        del sample_option_data["option_type"]
        with pytest.raises(ValidationError):
            OptionTrade(**sample_option_data)


class TestAccount:
    """Test Account model."""

    def test_create_account_valid(self):
        """Test creating a valid account."""
        account = Account(
            name="My IBKR Account",
            broker=BrokerType.IBKR,
            account_number="U1234567",
        )
        assert account.name == "My IBKR Account"
        assert account.broker == BrokerType.IBKR
        assert account.account_number == "U1234567"
        assert account.is_active is True

    def test_account_empty_name_fails(self):
        """Test that empty account name raises validation error."""
        with pytest.raises(ValidationError):
            Account(
                name="",
                broker=BrokerType.IBKR,
                account_number="U1234567",
            )

    def test_account_supports_multiple_brokers(self):
        """Test that account supports multiple broker types."""
        assert BrokerType.IBKR == "ibkr"
        assert BrokerType.MOOMOO == "moomoo"
        assert BrokerType.QUESTRADE == "questrade"


class TestPosition:
    """Test Position model."""

    def test_create_position_valid(self):
        """Test creating a valid position."""
        position = Position(
            symbol="AAPL",
            asset_type=AssetType.STOCK,
            quantity=100,
            average_price=Decimal("150.00"),
            account_id=1,
        )
        assert position.symbol == "AAPL"
        assert position.quantity == 100
        assert position.average_price == Decimal("150.00")
        assert position.status == PositionStatus.OPEN

    def test_position_unrealized_pnl_calculation(self):
        """Test unrealized P/L calculation for open position."""
        position = Position(
            symbol="AAPL",
            asset_type=AssetType.STOCK,
            quantity=100,
            average_price=Decimal("150.00"),
            current_price=Decimal("160.00"),
            account_id=1,
        )
        # Unrealized P/L = (current_price - average_price) * quantity
        expected_pnl = (Decimal("160.00") - Decimal("150.00")) * 100
        assert position.unrealized_pnl == expected_pnl

    def test_position_negative_quantity_for_short(self):
        """Test position with negative quantity (short position)."""
        position = Position(
            symbol="AAPL",
            asset_type=AssetType.STOCK,
            quantity=-100,
            average_price=Decimal("150.00"),
            account_id=1,
        )
        assert position.quantity == -100
        assert position.is_short is True
