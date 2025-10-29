"""Tests for risk management calculator."""

from decimal import Decimal
import pytest

from trade_tracker.analytics.risk import RiskCalculator, RiskMetrics
from trade_tracker.analytics.pnl import PositionPnL


class TestRiskCalculator:
    """Test risk metric calculations."""

    @pytest.fixture
    def sample_pnl_results(self):
        """Create sample P/L results for testing."""
        return [
            PositionPnL(symbol="AAPL", realized_pnl=Decimal("500")),
            PositionPnL(symbol="TSLA", realized_pnl=Decimal("-200")),
            PositionPnL(symbol="MSFT", realized_pnl=Decimal("300")),
            PositionPnL(symbol="GOOGL", realized_pnl=Decimal("-150")),
            PositionPnL(symbol="AMZN", realized_pnl=Decimal("400")),
        ]

    @pytest.fixture
    def winning_streak_pnl(self):
        """Create P/L results with a winning streak."""
        return [
            PositionPnL(symbol="AAPL", realized_pnl=Decimal("100")),
            PositionPnL(symbol="TSLA", realized_pnl=Decimal("200")),
            PositionPnL(symbol="MSFT", realized_pnl=Decimal("150")),
            PositionPnL(symbol="GOOGL", realized_pnl=Decimal("250")),
            PositionPnL(symbol="AMZN", realized_pnl=Decimal("-100")),
        ]

    @pytest.fixture
    def losing_streak_pnl(self):
        """Create P/L results with a losing streak."""
        return [
            PositionPnL(symbol="AAPL", realized_pnl=Decimal("-100")),
            PositionPnL(symbol="TSLA", realized_pnl=Decimal("-200")),
            PositionPnL(symbol="MSFT", realized_pnl=Decimal("-150")),
            PositionPnL(symbol="GOOGL", realized_pnl=Decimal("250")),
            PositionPnL(symbol="AMZN", realized_pnl=Decimal("300")),
        ]

    def test_create_calculator(self):
        """Test calculator instantiation."""
        calc = RiskCalculator()
        assert calc is not None
        assert calc.risk_free_rate == 0.02

        calc_custom = RiskCalculator(risk_free_rate=0.03)
        assert calc_custom.risk_free_rate == 0.03

    def test_calculate_basic_metrics(self, sample_pnl_results):
        """Test basic risk metrics calculation."""
        calc = RiskCalculator()
        metrics = calc.calculate_risk_metrics(sample_pnl_results)

        assert metrics is not None
        assert metrics.total_trades == 5
        assert metrics.winning_trades == 3
        assert metrics.losing_trades == 2
        assert metrics.win_rate == 60.0

    def test_empty_pnl_results(self):
        """Test handling of empty P/L results."""
        calc = RiskCalculator()
        metrics = calc.calculate_risk_metrics([])

        assert metrics.total_trades == 0
        assert metrics.sharpe_ratio is None
        assert metrics.max_drawdown is None

    def test_calculate_sharpe_ratio(self, sample_pnl_results):
        """Test Sharpe ratio calculation."""
        calc = RiskCalculator()
        metrics = calc.calculate_risk_metrics(sample_pnl_results)

        assert metrics.sharpe_ratio is not None
        assert isinstance(metrics.sharpe_ratio, float)

    def test_calculate_max_drawdown(self, sample_pnl_results):
        """Test maximum drawdown calculation."""
        calc = RiskCalculator()
        metrics = calc.calculate_risk_metrics(sample_pnl_results)

        assert metrics.max_drawdown is not None
        assert metrics.max_drawdown >= 0
        assert metrics.max_drawdown_percent is not None
        assert metrics.max_drawdown_percent >= 0

    def test_calculate_winning_streak(self, winning_streak_pnl):
        """Test winning streak calculation."""
        calc = RiskCalculator()
        metrics = calc.calculate_risk_metrics(winning_streak_pnl)

        assert metrics.longest_winning_streak == 4
        assert metrics.longest_losing_streak == 1

    def test_calculate_losing_streak(self, losing_streak_pnl):
        """Test losing streak calculation."""
        calc = RiskCalculator()
        metrics = calc.calculate_risk_metrics(losing_streak_pnl)

        assert metrics.longest_winning_streak == 2
        assert metrics.longest_losing_streak == 3

    def test_current_streak(self, winning_streak_pnl):
        """Test current streak tracking."""
        calc = RiskCalculator()
        metrics = calc.calculate_risk_metrics(winning_streak_pnl)

        # Last trade is a loss
        assert metrics.current_streak == 1
        assert metrics.current_streak_type == 'loss'

    def test_calculate_volatility(self, sample_pnl_results):
        """Test volatility calculation."""
        calc = RiskCalculator()
        metrics = calc.calculate_risk_metrics(sample_pnl_results)

        assert metrics.volatility is not None
        assert metrics.volatility > 0

    def test_calculate_profit_factor(self, sample_pnl_results):
        """Test profit factor calculation."""
        calc = RiskCalculator()
        metrics = calc.calculate_risk_metrics(sample_pnl_results)

        # Profit factor = Gross Profit / Gross Loss
        # Gross Profit = 500 + 300 + 400 = 1200
        # Gross Loss = 200 + 150 = 350
        # Profit Factor = 1200 / 350 = 3.43
        assert metrics.profit_factor is not None
        assert metrics.profit_factor > 1  # Should be profitable

    def test_calculate_expectancy(self, sample_pnl_results):
        """Test expectancy calculation."""
        calc = RiskCalculator()
        metrics = calc.calculate_risk_metrics(sample_pnl_results)

        # Expectancy = Average P/L per trade
        # (500 - 200 + 300 - 150 + 400) / 5 = 170
        assert metrics.expectancy is not None
        assert metrics.expectancy > 0

    def test_calculate_risk_reward_ratio(self, sample_pnl_results):
        """Test risk/reward ratio calculation."""
        calc = RiskCalculator()
        metrics = calc.calculate_risk_metrics(sample_pnl_results)

        # Risk/Reward = Average Win / Average Loss
        # Average Win = (500 + 300 + 400) / 3 = 400
        # Average Loss = (200 + 150) / 2 = 175
        # Risk/Reward = 400 / 175 = 2.29
        assert metrics.risk_reward_ratio is not None
        assert metrics.risk_reward_ratio > 1

    def test_calculate_average_win_loss(self, sample_pnl_results):
        """Test average win/loss calculation."""
        calc = RiskCalculator()
        metrics = calc.calculate_risk_metrics(sample_pnl_results)

        assert metrics.average_win is not None
        assert metrics.average_win > 0
        assert metrics.average_loss is not None
        assert metrics.average_loss < 0

    def test_calculate_largest_win_loss(self, sample_pnl_results):
        """Test largest win/loss calculation."""
        calc = RiskCalculator()
        metrics = calc.calculate_risk_metrics(sample_pnl_results)

        assert metrics.largest_win == Decimal("500")
        assert metrics.largest_loss == Decimal("-200")

    def test_calculate_recovery_factor(self, sample_pnl_results):
        """Test recovery factor calculation."""
        calc = RiskCalculator()
        metrics = calc.calculate_risk_metrics(sample_pnl_results)

        # Recovery Factor = Net Profit / Max Drawdown
        assert metrics.recovery_factor is not None

    def test_single_trade(self):
        """Test with single trade."""
        calc = RiskCalculator()
        single_trade = [PositionPnL(symbol="AAPL", realized_pnl=Decimal("100"))]
        metrics = calc.calculate_risk_metrics(single_trade)

        assert metrics.total_trades == 1
        assert metrics.winning_trades == 1
        assert metrics.losing_trades == 0
        # Sharpe ratio requires at least 2 data points
        assert metrics.sharpe_ratio is None

    def test_all_winning_trades(self):
        """Test with all winning trades."""
        calc = RiskCalculator()
        all_wins = [
            PositionPnL(symbol="AAPL", realized_pnl=Decimal("100")),
            PositionPnL(symbol="TSLA", realized_pnl=Decimal("200")),
            PositionPnL(symbol="MSFT", realized_pnl=Decimal("150")),
        ]
        metrics = calc.calculate_risk_metrics(all_wins)

        assert metrics.winning_trades == 3
        assert metrics.losing_trades == 0
        assert metrics.win_rate == 100.0
        # Profit factor is None when there are no losses
        assert metrics.profit_factor is None

    def test_all_losing_trades(self):
        """Test with all losing trades."""
        calc = RiskCalculator()
        all_losses = [
            PositionPnL(symbol="AAPL", realized_pnl=Decimal("-100")),
            PositionPnL(symbol="TSLA", realized_pnl=Decimal("-200")),
            PositionPnL(symbol="MSFT", realized_pnl=Decimal("-150")),
        ]
        metrics = calc.calculate_risk_metrics(all_losses)

        assert metrics.winning_trades == 0
        assert metrics.losing_trades == 3
        assert metrics.win_rate == 0.0
        assert metrics.average_win is None
        assert metrics.largest_win is None

    def test_sortino_ratio(self, sample_pnl_results):
        """Test Sortino ratio calculation."""
        calc = RiskCalculator()
        metrics = calc.calculate_risk_metrics(sample_pnl_results)

        assert metrics.sortino_ratio is not None
        assert isinstance(metrics.sortino_ratio, float)

    def test_downside_deviation(self, sample_pnl_results):
        """Test downside deviation calculation."""
        calc = RiskCalculator()
        metrics = calc.calculate_risk_metrics(sample_pnl_results)

        assert metrics.downside_deviation is not None
        assert metrics.downside_deviation > 0
