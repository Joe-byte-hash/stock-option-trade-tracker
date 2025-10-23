"""Unit tests for portfolio metrics (TDD approach)."""

from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from trade_tracker.models.trade import StockTrade, TradeType
from trade_tracker.analytics.metrics import MetricsCalculator, PortfolioMetrics, PeriodReturns
from trade_tracker.analytics.pnl import PnLCalculator, PositionPnL


class TestWinRateMetrics:
    """Test win rate and trade statistics."""

    def test_win_rate_all_winners(self):
        """Test win rate when all trades are profitable."""
        pnl_results = [
            PositionPnL(symbol="AAPL", realized_pnl=Decimal("100")),
            PositionPnL(symbol="TSLA", realized_pnl=Decimal("200")),
            PositionPnL(symbol="MSFT", realized_pnl=Decimal("50")),
        ]

        calculator = MetricsCalculator()
        metrics = calculator.calculate_trade_statistics(pnl_results)

        assert metrics.total_trades == 3
        assert metrics.winning_trades == 3
        assert metrics.losing_trades == 0
        assert metrics.win_rate == Decimal("100.00")

    def test_win_rate_mixed(self):
        """Test win rate with mix of winners and losers."""
        pnl_results = [
            PositionPnL(symbol="AAPL", realized_pnl=Decimal("100")),
            PositionPnL(symbol="TSLA", realized_pnl=Decimal("-50")),
            PositionPnL(symbol="MSFT", realized_pnl=Decimal("200")),
            PositionPnL(symbol="GOOGL", realized_pnl=Decimal("-100")),
        ]

        calculator = MetricsCalculator()
        metrics = calculator.calculate_trade_statistics(pnl_results)

        assert metrics.total_trades == 4
        assert metrics.winning_trades == 2
        assert metrics.losing_trades == 2
        assert metrics.win_rate == Decimal("50.00")

    def test_average_win_loss(self):
        """Test average win and loss calculations."""
        pnl_results = [
            PositionPnL(symbol="AAPL", realized_pnl=Decimal("100")),
            PositionPnL(symbol="TSLA", realized_pnl=Decimal("200")),
            PositionPnL(symbol="MSFT", realized_pnl=Decimal("-50")),
            PositionPnL(symbol="GOOGL", realized_pnl=Decimal("-150")),
        ]

        calculator = MetricsCalculator()
        metrics = calculator.calculate_trade_statistics(pnl_results)

        # Average win = (100 + 200) / 2 = 150
        assert metrics.average_win == Decimal("150.00")
        # Average loss = (-50 + -150) / 2 = -100
        assert metrics.average_loss == Decimal("-100.00")

    def test_profit_factor(self):
        """Test profit factor calculation."""
        pnl_results = [
            PositionPnL(symbol="AAPL", realized_pnl=Decimal("300")),
            PositionPnL(symbol="TSLA", realized_pnl=Decimal("200")),
            PositionPnL(symbol="MSFT", realized_pnl=Decimal("-100")),
        ]

        calculator = MetricsCalculator()
        metrics = calculator.calculate_trade_statistics(pnl_results)

        # Profit factor = gross_profit / abs(gross_loss)
        # = 500 / 100 = 5.0
        assert metrics.profit_factor == Decimal("5.00")


class TestDrawdownCalculation:
    """Test maximum drawdown calculations."""

    def test_maximum_drawdown_simple(self):
        """Test max drawdown with simple equity curve."""
        # Equity curve: 10000 -> 11000 -> 9000 -> 12000
        equity_curve = [
            (datetime(2024, 1, 1), Decimal("10000")),
            (datetime(2024, 1, 5), Decimal("11000")),
            (datetime(2024, 1, 10), Decimal("9000")),  # Drawdown from 11000
            (datetime(2024, 1, 15), Decimal("12000")),
        ]

        calculator = MetricsCalculator()
        max_dd = calculator.calculate_max_drawdown(equity_curve)

        # Max drawdown = (11000 - 9000) / 11000 = 18.18%
        assert max_dd.max_drawdown_amount == Decimal("2000.00")
        assert abs(max_dd.max_drawdown_percent - Decimal("18.18")) < Decimal("0.01")

    def test_maximum_drawdown_multiple_peaks(self):
        """Test max drawdown with multiple peaks and troughs."""
        equity_curve = [
            (datetime(2024, 1, 1), Decimal("10000")),
            (datetime(2024, 1, 5), Decimal("12000")),  # Peak 1
            (datetime(2024, 1, 10), Decimal("11000")),
            (datetime(2024, 1, 15), Decimal("15000")),  # Peak 2
            (datetime(2024, 1, 20), Decimal("9000")),  # Largest drawdown
            (datetime(2024, 1, 25), Decimal("13000")),
        ]

        calculator = MetricsCalculator()
        max_dd = calculator.calculate_max_drawdown(equity_curve)

        # Max drawdown from peak of 15000 to trough of 9000
        # = (15000 - 9000) / 15000 = 40%
        assert max_dd.max_drawdown_amount == Decimal("6000.00")
        assert max_dd.max_drawdown_percent == Decimal("40.00")

    def test_no_drawdown(self):
        """Test when equity curve only goes up."""
        equity_curve = [
            (datetime(2024, 1, 1), Decimal("10000")),
            (datetime(2024, 1, 5), Decimal("11000")),
            (datetime(2024, 1, 10), Decimal("12000")),
            (datetime(2024, 1, 15), Decimal("15000")),
        ]

        calculator = MetricsCalculator()
        max_dd = calculator.calculate_max_drawdown(equity_curve)

        assert max_dd.max_drawdown_amount == Decimal("0.00")
        assert max_dd.max_drawdown_percent == Decimal("0.00")


class TestPeriodReturns:
    """Test returns calculation by time period."""

    def test_daily_returns(self):
        """Test daily P/L calculation."""
        trades = [
            (datetime(2024, 1, 1), Decimal("100")),
            (datetime(2024, 1, 1), Decimal("50")),
            (datetime(2024, 1, 2), Decimal("-30")),
            (datetime(2024, 1, 3), Decimal("200")),
        ]

        calculator = MetricsCalculator()
        daily_pnl = calculator.calculate_daily_pnl(trades)

        assert daily_pnl[datetime(2024, 1, 1).date()] == Decimal("150")
        assert daily_pnl[datetime(2024, 1, 2).date()] == Decimal("-30")
        assert daily_pnl[datetime(2024, 1, 3).date()] == Decimal("200")

    def test_weekly_returns(self):
        """Test weekly P/L aggregation."""
        # Week 1: Jan 1-7, Week 2: Jan 8-14
        trades = [
            (datetime(2024, 1, 1), Decimal("100")),  # Week 1
            (datetime(2024, 1, 5), Decimal("50")),   # Week 1
            (datetime(2024, 1, 10), Decimal("200")), # Week 2
            (datetime(2024, 1, 12), Decimal("-30")), # Week 2
        ]

        calculator = MetricsCalculator()
        weekly_pnl = calculator.calculate_weekly_pnl(trades)

        # Week should be identified by year-week number
        week1 = datetime(2024, 1, 1).isocalendar()[:2]
        week2 = datetime(2024, 1, 10).isocalendar()[:2]

        assert weekly_pnl[week1] == Decimal("150")
        assert weekly_pnl[week2] == Decimal("170")

    def test_monthly_returns(self):
        """Test monthly P/L aggregation."""
        trades = [
            (datetime(2024, 1, 5), Decimal("100")),
            (datetime(2024, 1, 15), Decimal("50")),
            (datetime(2024, 2, 5), Decimal("200")),
            (datetime(2024, 2, 20), Decimal("-30")),
            (datetime(2024, 3, 10), Decimal("75")),
        ]

        calculator = MetricsCalculator()
        monthly_pnl = calculator.calculate_monthly_pnl(trades)

        assert monthly_pnl[(2024, 1)] == Decimal("150")
        assert monthly_pnl[(2024, 2)] == Decimal("170")
        assert monthly_pnl[(2024, 3)] == Decimal("75")

    def test_yearly_returns(self):
        """Test yearly P/L aggregation."""
        trades = [
            (datetime(2024, 1, 5), Decimal("1000")),
            (datetime(2024, 6, 15), Decimal("500")),
            (datetime(2024, 12, 20), Decimal("-200")),
            (datetime(2025, 3, 10), Decimal("750")),
        ]

        calculator = MetricsCalculator()
        yearly_pnl = calculator.calculate_yearly_pnl(trades)

        assert yearly_pnl[2024] == Decimal("1300")
        assert yearly_pnl[2025] == Decimal("750")


class TestSharpeRatio:
    """Test Sharpe ratio calculation."""

    def test_sharpe_ratio_positive(self):
        """Test Sharpe ratio with positive returns."""
        returns = [
            Decimal("0.05"),  # 5%
            Decimal("0.03"),  # 3%
            Decimal("0.07"),  # 7%
            Decimal("0.02"),  # 2%
            Decimal("0.04"),  # 4%
        ]

        calculator = MetricsCalculator()
        sharpe = calculator.calculate_sharpe_ratio(returns, risk_free_rate=Decimal("0.02"))

        # Should be positive for consistently positive returns
        assert sharpe > Decimal("0")

    def test_sharpe_ratio_negative(self):
        """Test Sharpe ratio with negative returns."""
        returns = [
            Decimal("-0.05"),
            Decimal("-0.03"),
            Decimal("-0.02"),
        ]

        calculator = MetricsCalculator()
        sharpe = calculator.calculate_sharpe_ratio(returns)

        # Should be negative for consistently negative returns
        assert sharpe < Decimal("0")


class TestPortfolioMetrics:
    """Test comprehensive portfolio metrics."""

    def test_portfolio_summary(self):
        """Test comprehensive portfolio metrics calculation."""
        pnl_results = [
            PositionPnL(symbol="AAPL", realized_pnl=Decimal("1000"), return_percentage=Decimal("10")),
            PositionPnL(symbol="TSLA", realized_pnl=Decimal("-500"), return_percentage=Decimal("-5")),
            PositionPnL(symbol="MSFT", realized_pnl=Decimal("750"), return_percentage=Decimal("7.5")),
        ]

        calculator = MetricsCalculator()
        metrics = calculator.calculate_portfolio_metrics(pnl_results, initial_capital=Decimal("10000"))

        assert metrics.total_pnl == Decimal("1250")
        assert metrics.total_return_percentage == Decimal("12.50")
        assert metrics.win_rate == Decimal("66.67")


class TestLargestWinLoss:
    """Test largest win and loss tracking."""

    def test_largest_win_and_loss(self):
        """Test tracking largest win and loss."""
        pnl_results = [
            PositionPnL(symbol="AAPL", realized_pnl=Decimal("1000")),
            PositionPnL(symbol="TSLA", realized_pnl=Decimal("-500")),
            PositionPnL(symbol="MSFT", realized_pnl=Decimal("2500")),
            PositionPnL(symbol="GOOGL", realized_pnl=Decimal("-1200")),
            PositionPnL(symbol="AMZN", realized_pnl=Decimal("300")),
        ]

        calculator = MetricsCalculator()
        metrics = calculator.calculate_trade_statistics(pnl_results)

        assert metrics.largest_win == Decimal("2500.00")
        assert metrics.largest_loss == Decimal("-1200.00")
