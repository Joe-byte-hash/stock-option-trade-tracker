"""Tests for strategy performance timeline chart."""

from datetime import datetime
from decimal import Decimal
import pytest

from trade_tracker.models.trade import Trade, AssetType, TradeType, TradingStrategy
from trade_tracker.visualization.dashboard import TradeDashboard


class TestStrategyTimeline:
    """Test strategy performance timeline functionality."""

    @pytest.fixture
    def sample_trades_with_dates(self):
        """Create sample trades across time for timeline testing."""
        return [
            # Day trades in January
            Trade(
                id=1,
                symbol="AAPL",
                asset_type=AssetType.STOCK,
                trade_type=TradeType.BUY,
                quantity=100,
                price=Decimal("150.00"),
                commission=Decimal("1.00"),
                trade_date=datetime(2024, 1, 5),
                strategy=TradingStrategy.DAY_TRADE
            ),
            Trade(
                id=2,
                symbol="AAPL",
                asset_type=AssetType.STOCK,
                trade_type=TradeType.SELL,
                quantity=100,
                price=Decimal("155.00"),
                commission=Decimal("1.00"),
                trade_date=datetime(2024, 1, 5),
                strategy=TradingStrategy.DAY_TRADE
            ),
            # Swing trade in February
            Trade(
                id=3,
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
                id=4,
                symbol="TSLA",
                asset_type=AssetType.STOCK,
                trade_type=TradeType.SELL,
                quantity=50,
                price=Decimal("210.00"),
                commission=Decimal("1.00"),
                trade_date=datetime(2024, 2, 15),
                strategy=TradingStrategy.SWING_TRADE
            ),
            # Another day trade in March
            Trade(
                id=5,
                symbol="MSFT",
                asset_type=AssetType.STOCK,
                trade_type=TradeType.BUY,
                quantity=75,
                price=Decimal("300.00"),
                commission=Decimal("1.00"),
                trade_date=datetime(2024, 3, 10),
                strategy=TradingStrategy.DAY_TRADE
            ),
            Trade(
                id=6,
                symbol="MSFT",
                asset_type=AssetType.STOCK,
                trade_type=TradeType.SELL,
                quantity=75,
                price=Decimal("305.00"),
                commission=Decimal("1.00"),
                trade_date=datetime(2024, 3, 10),
                strategy=TradingStrategy.DAY_TRADE
            ),
        ]

    def test_create_timeline_chart(self, sample_trades_with_dates, tmp_path):
        """Test timeline chart creation."""
        dashboard = TradeDashboard(db_path=str(tmp_path / "test.db"))

        fig = dashboard._create_strategy_timeline_chart(sample_trades_with_dates, [])

        # Check that figure is created
        assert fig is not None
        assert len(fig.data) >= 1  # Should have at least one strategy trace

        # Check chart properties
        assert fig.layout.title.text == "Cumulative P/L by Strategy Over Time"
        assert fig.layout.xaxis.title.text == "Date"
        assert fig.layout.yaxis.title.text == "Cumulative P/L ($)"

    def test_timeline_chart_multiple_strategies(self, sample_trades_with_dates, tmp_path):
        """Test timeline chart with multiple strategies."""
        dashboard = TradeDashboard(db_path=str(tmp_path / "test.db"))

        fig = dashboard._create_strategy_timeline_chart(sample_trades_with_dates, [])

        # Should have 2 traces (day_trade and swing_trade)
        assert len(fig.data) == 2

        # Get strategy names from traces
        strategy_names = [trace.name for trace in fig.data]
        assert "Day Trade" in strategy_names
        assert "Swing Trade" in strategy_names

    def test_timeline_chart_cumulative_calculation(self, sample_trades_with_dates, tmp_path):
        """Test that P/L is cumulative over time."""
        dashboard = TradeDashboard(db_path=str(tmp_path / "test.db"))

        fig = dashboard._create_strategy_timeline_chart(sample_trades_with_dates, [])

        # Find day trade trace (has 2 trades)
        day_trade_trace = None
        for trace in fig.data:
            if trace.name == "Day Trade":
                day_trade_trace = trace
                break

        assert day_trade_trace is not None

        # Y values should be cumulative (increasing over time if profitable)
        y_values = list(day_trade_trace.y)
        assert len(y_values) >= 2  # Should have at least 2 points

        # Second value should be >= first (cumulative)
        # Note: Might be equal if one trade breaks even
        assert y_values[1] >= y_values[0]

    def test_timeline_chart_chronological_order(self, sample_trades_with_dates, tmp_path):
        """Test that trades are ordered chronologically."""
        dashboard = TradeDashboard(db_path=str(tmp_path / "test.db"))

        fig = dashboard._create_strategy_timeline_chart(sample_trades_with_dates, [])

        # Check that x values (dates) are sorted
        for trace in fig.data:
            dates = list(trace.x)
            assert dates == sorted(dates), f"Dates not sorted for {trace.name}"

    def test_timeline_chart_empty_trades(self, tmp_path):
        """Test timeline chart with no trades."""
        dashboard = TradeDashboard(db_path=str(tmp_path / "test.db"))

        fig = dashboard._create_strategy_timeline_chart([], [])

        # Should still return a figure, but with no data traces
        assert fig is not None
        assert len(fig.data) == 0

    def test_timeline_chart_single_strategy(self, tmp_path):
        """Test timeline chart with only one strategy."""
        trades = [
            Trade(
                id=1,
                symbol="AAPL",
                asset_type=AssetType.STOCK,
                trade_type=TradeType.BUY,
                quantity=100,
                price=Decimal("150.00"),
                commission=Decimal("1.00"),
                trade_date=datetime(2024, 1, 5),
                strategy=TradingStrategy.MOMENTUM
            ),
            Trade(
                id=2,
                symbol="AAPL",
                asset_type=AssetType.STOCK,
                trade_type=TradeType.SELL,
                quantity=100,
                price=Decimal("155.00"),
                commission=Decimal("1.00"),
                trade_date=datetime(2024, 1, 6),
                strategy=TradingStrategy.MOMENTUM
            ),
        ]

        dashboard = TradeDashboard(db_path=str(tmp_path / "test.db"))
        fig = dashboard._create_strategy_timeline_chart(trades, [])

        # Should have exactly 1 trace
        assert len(fig.data) == 1
        assert fig.data[0].name == "Momentum"

    def test_timeline_chart_has_zero_line(self, sample_trades_with_dates, tmp_path):
        """Test that timeline chart has a horizontal line at y=0."""
        dashboard = TradeDashboard(db_path=str(tmp_path / "test.db"))

        fig = dashboard._create_strategy_timeline_chart(sample_trades_with_dates, [])

        # Check for horizontal line (shape) at y=0
        assert len(fig.layout.shapes) >= 1
        # The hline should be at y=0
        has_zero_line = any(
            shape.type == 'line' and shape.y0 == 0 and shape.y1 == 0
            for shape in fig.layout.shapes
        )
        assert has_zero_line, "Timeline chart should have a horizontal line at y=0"
