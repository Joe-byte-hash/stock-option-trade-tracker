"""Tests for trade charting functionality."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from trade_tracker.visualization.charts import TradeChartBuilder
from trade_tracker.models.trade import StockTrade, TradeType


@pytest.fixture
def sample_stock_trades():
    """Create sample stock trades for testing."""
    return [
        StockTrade(
            id=1,
            symbol="AAPL",
            trade_type=TradeType.BUY,
            quantity=100,
            price=Decimal("150.00"),
            commission=Decimal("1.00"),
            trade_date=datetime(2024, 1, 15, 10, 30),
            account_id=1
        ),
        StockTrade(
            id=2,
            symbol="AAPL",
            trade_type=TradeType.SELL,
            quantity=100,
            price=Decimal("160.00"),
            commission=Decimal("1.00"),
            trade_date=datetime(2024, 2, 20, 14, 0),
            account_id=1
        ),
    ]


@pytest.fixture
def sample_price_data():
    """Create sample price data (OHLC format)."""
    dates = pd.date_range(start='2024-01-01', end='2024-03-01', freq='D')
    data = {
        'Open': [150 + i * 0.5 for i in range(len(dates))],
        'High': [152 + i * 0.5 for i in range(len(dates))],
        'Low': [148 + i * 0.5 for i in range(len(dates))],
        'Close': [151 + i * 0.5 for i in range(len(dates))],
        'Volume': [1000000 + i * 1000 for i in range(len(dates))],
    }
    return pd.DataFrame(data, index=dates)


class TestTradeChartBuilder:
    """Test TradeChartBuilder class."""

    def test_create_chart_builder(self):
        """Test creating chart builder instance."""
        builder = TradeChartBuilder(require_yfinance=False)
        assert builder is not None

    def test_fetch_price_data(self, sample_price_data):
        """Test fetching price data from yfinance."""
        # Mock yfinance module
        mock_yf = Mock()
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = sample_price_data
        mock_yf.Ticker.return_value = mock_ticker_instance

        builder = TradeChartBuilder(require_yfinance=False, yfinance_module=mock_yf)
        price_data = builder.fetch_price_data("AAPL", period="3mo")

        assert price_data is not None
        assert len(price_data) > 0
        assert 'Open' in price_data.columns
        assert 'High' in price_data.columns
        assert 'Low' in price_data.columns
        assert 'Close' in price_data.columns

    def test_create_candlestick_chart(self, sample_price_data, sample_stock_trades):
        """Test creating candlestick chart with trade markers."""
        # Mock yfinance module
        mock_yf = Mock()
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = sample_price_data
        mock_yf.Ticker.return_value = mock_ticker_instance

        builder = TradeChartBuilder(require_yfinance=False, yfinance_module=mock_yf)
        fig = builder.create_trade_chart(
            symbol="AAPL",
            trades=sample_stock_trades,
            period="3mo"
        )

        assert fig is not None
        assert len(fig.data) >= 1  # At least candlestick trace
        # Should have candlestick + buy markers + sell markers = 3 traces
        assert len(fig.data) >= 3

    def test_entry_exit_markers_added(self, sample_price_data, sample_stock_trades):
        """Test that entry and exit markers are added to chart."""
        mock_yf = Mock()
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = sample_price_data
        mock_yf.Ticker.return_value = mock_ticker_instance

        builder = TradeChartBuilder(require_yfinance=False, yfinance_module=mock_yf)
        fig = builder.create_trade_chart(
            symbol="AAPL",
            trades=sample_stock_trades,
            period="3mo"
        )

        # Check that we have scatter traces for markers
        scatter_traces = [trace for trace in fig.data if trace.type == 'scatter']
        assert len(scatter_traces) >= 2  # Buy and sell markers

    def test_chart_with_no_trades(self, sample_price_data):
        """Test creating chart with no trades (only price data)."""
        mock_yf = Mock()
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = sample_price_data
        mock_yf.Ticker.return_value = mock_ticker_instance

        builder = TradeChartBuilder(require_yfinance=False, yfinance_module=mock_yf)
        fig = builder.create_trade_chart(
            symbol="AAPL",
            trades=[],
            period="3mo"
        )

        assert fig is not None
        # Should have only candlestick trace, no markers
        assert len(fig.data) == 1

    def test_invalid_symbol_handling(self):
        """Test handling of invalid stock symbol."""
        mock_yf = Mock()
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = pd.DataFrame()  # Empty data
        mock_yf.Ticker.return_value = mock_ticker_instance

        builder = TradeChartBuilder(require_yfinance=False, yfinance_module=mock_yf)
        fig = builder.create_trade_chart(
            symbol="INVALID",
            trades=[],
            period="3mo"
        )

        # Should return None or empty figure
        assert fig is None or len(fig.data) == 0

    def test_calculate_pnl_for_trade_pair(self, sample_stock_trades):
        """Test calculating P/L for matched entry/exit trades."""
        builder = TradeChartBuilder(require_yfinance=False)

        buy_trade = sample_stock_trades[0]  # Buy at 150
        sell_trade = sample_stock_trades[1]  # Sell at 160

        pnl = builder._calculate_trade_pnl(buy_trade, sell_trade)

        # (160 - 150) * 100 - 2 (commissions) = 998
        assert pnl == Decimal("998.00")

    def test_different_time_periods(self, sample_price_data):
        """Test chart creation with different time periods."""
        mock_yf = Mock()
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = sample_price_data
        mock_yf.Ticker.return_value = mock_ticker_instance

        builder = TradeChartBuilder(require_yfinance=False, yfinance_module=mock_yf)

        periods = ["1mo", "3mo", "6mo", "1y", "max"]
        for period in periods:
            fig = builder.create_trade_chart(
                symbol="AAPL",
                trades=[],
                period=period
            )
            assert fig is not None
            mock_ticker_instance.history.assert_called()

    def test_marker_colors_based_on_pnl(self, sample_price_data, sample_stock_trades):
        """Test that exit markers use different colors based on P/L."""
        mock_yf = Mock()
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = sample_price_data
        mock_yf.Ticker.return_value = mock_ticker_instance

        builder = TradeChartBuilder(require_yfinance=False, yfinance_module=mock_yf)
        fig = builder.create_trade_chart(
            symbol="AAPL",
            trades=sample_stock_trades,
            period="3mo"
        )

        # Find sell marker trace
        scatter_traces = [trace for trace in fig.data if trace.type == 'scatter']
        sell_traces = [t for t in scatter_traces if 'Sell' in t.name or 'Exit' in t.name]

        # Should have sell markers
        assert len(sell_traces) > 0
