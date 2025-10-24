"""Tests for dashboard filter functionality."""

from datetime import datetime
from decimal import Decimal
import pytest

from trade_tracker.models.trade import Trade, AssetType, TradeType, TradingStrategy
from trade_tracker.visualization.dashboard import TradeDashboard


class TestDashboardFilters:
    """Test dashboard filtering functionality."""

    @pytest.fixture
    def sample_trades(self):
        """Create sample trades for filter testing."""
        return [
            Trade(
                id=1,
                symbol="AAPL",
                asset_type=AssetType.STOCK,
                trade_type=TradeType.BUY,
                quantity=100,
                price=Decimal("150.00"),
                commission=Decimal("1.00"),
                trade_date=datetime(2024, 1, 15),
                strategy=TradingStrategy.DAY_TRADE
            ),
            Trade(
                id=2,
                symbol="TSLA",
                asset_type=AssetType.STOCK,
                trade_type=TradeType.BUY,
                quantity=50,
                price=Decimal("200.00"),
                commission=Decimal("1.00"),
                trade_date=datetime(2024, 2, 10),
                strategy=TradingStrategy.SWING_TRADE
            ),
            Trade(
                id=3,
                symbol="AAPL",
                asset_type=AssetType.STOCK,
                trade_type=TradeType.SELL,
                quantity=100,
                price=Decimal("155.00"),
                commission=Decimal("1.00"),
                trade_date=datetime(2024, 3, 20),
                strategy=TradingStrategy.DAY_TRADE
            ),
            Trade(
                id=4,
                symbol="MSFT",
                asset_type=AssetType.STOCK,
                trade_type=TradeType.BUY,
                quantity=75,
                price=Decimal("300.00"),
                commission=Decimal("1.00"),
                trade_date=datetime(2024, 4, 5),
                strategy=TradingStrategy.MOMENTUM
            ),
        ]

    def test_apply_date_range_filter(self, sample_trades, tmp_path):
        """Test date range filtering."""
        dashboard = TradeDashboard(db_path=str(tmp_path / "test.db"))

        # Filter for February only
        filtered = dashboard._apply_filters(
            sample_trades,
            start_date="2024-02-01",
            end_date="2024-02-28",
            symbols_filter=None,
            strategies_filter=None
        )

        assert len(filtered) == 1
        assert filtered[0].symbol == "TSLA"
        assert filtered[0].trade_date.month == 2

    def test_apply_symbol_filter(self, sample_trades, tmp_path):
        """Test symbol filtering."""
        dashboard = TradeDashboard(db_path=str(tmp_path / "test.db"))

        # Filter for AAPL only
        filtered = dashboard._apply_filters(
            sample_trades,
            start_date=None,
            end_date=None,
            symbols_filter=["AAPL"],
            strategies_filter=None
        )

        assert len(filtered) == 2
        assert all(trade.symbol == "AAPL" for trade in filtered)

    def test_apply_strategy_filter(self, sample_trades, tmp_path):
        """Test strategy filtering."""
        dashboard = TradeDashboard(db_path=str(tmp_path / "test.db"))

        # Filter for day trades only
        filtered = dashboard._apply_filters(
            sample_trades,
            start_date=None,
            end_date=None,
            symbols_filter=None,
            strategies_filter=["day_trade"]
        )

        assert len(filtered) == 2
        assert all(trade.strategy == TradingStrategy.DAY_TRADE for trade in filtered)

    def test_apply_multiple_filters(self, sample_trades, tmp_path):
        """Test combining multiple filters."""
        dashboard = TradeDashboard(db_path=str(tmp_path / "test.db"))

        # Filter for AAPL day trades in January
        filtered = dashboard._apply_filters(
            sample_trades,
            start_date="2024-01-01",
            end_date="2024-01-31",
            symbols_filter=["AAPL"],
            strategies_filter=["day_trade"]
        )

        assert len(filtered) == 1
        assert filtered[0].symbol == "AAPL"
        assert filtered[0].strategy == TradingStrategy.DAY_TRADE
        assert filtered[0].trade_date.month == 1

    def test_apply_multi_symbol_filter(self, sample_trades, tmp_path):
        """Test filtering with multiple symbols."""
        dashboard = TradeDashboard(db_path=str(tmp_path / "test.db"))

        # Filter for AAPL and MSFT
        filtered = dashboard._apply_filters(
            sample_trades,
            start_date=None,
            end_date=None,
            symbols_filter=["AAPL", "MSFT"],
            strategies_filter=None
        )

        assert len(filtered) == 3
        assert set(trade.symbol for trade in filtered) == {"AAPL", "MSFT"}

    def test_apply_multi_strategy_filter(self, sample_trades, tmp_path):
        """Test filtering with multiple strategies."""
        dashboard = TradeDashboard(db_path=str(tmp_path / "test.db"))

        # Filter for day trade and swing trade
        filtered = dashboard._apply_filters(
            sample_trades,
            start_date=None,
            end_date=None,
            symbols_filter=None,
            strategies_filter=["day_trade", "swing_trade"]
        )

        assert len(filtered) == 3
        assert set(trade.strategy for trade in filtered) == {
            TradingStrategy.DAY_TRADE, TradingStrategy.SWING_TRADE
        }

    def test_no_filters_returns_all(self, sample_trades, tmp_path):
        """Test that no filters returns all trades."""
        dashboard = TradeDashboard(db_path=str(tmp_path / "test.db"))

        filtered = dashboard._apply_filters(
            sample_trades,
            start_date=None,
            end_date=None,
            symbols_filter=None,
            strategies_filter=None
        )

        assert len(filtered) == len(sample_trades)
        assert filtered == sample_trades

    def test_filters_return_empty_when_no_matches(self, sample_trades, tmp_path):
        """Test that filters return empty list when no trades match."""
        dashboard = TradeDashboard(db_path=str(tmp_path / "test.db"))

        # Filter for a date range with no trades
        filtered = dashboard._apply_filters(
            sample_trades,
            start_date="2025-01-01",
            end_date="2025-12-31",
            symbols_filter=None,
            strategies_filter=None
        )

        assert len(filtered) == 0

    def test_invalid_strategy_filter_skipped(self, sample_trades, tmp_path):
        """Test that invalid strategy values are skipped."""
        dashboard = TradeDashboard(db_path=str(tmp_path / "test.db"))

        # Include an invalid strategy value
        filtered = dashboard._apply_filters(
            sample_trades,
            start_date=None,
            end_date=None,
            symbols_filter=None,
            strategies_filter=["day_trade", "invalid_strategy"]
        )

        # Should only match day_trade
        assert len(filtered) == 2
        assert all(trade.strategy == TradingStrategy.DAY_TRADE for trade in filtered)
