"""Risk management metrics calculator."""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Dict, Any
import statistics
import math

from trade_tracker.analytics.pnl import PositionPnL


@dataclass
class RiskMetrics:
    """Risk management metrics for trading performance."""

    # Core risk metrics
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    max_drawdown: Optional[Decimal] = None
    max_drawdown_percent: Optional[float] = None

    # Streak metrics
    longest_winning_streak: int = 0
    longest_losing_streak: int = 0
    current_streak: int = 0
    current_streak_type: Optional[str] = None  # 'win' or 'loss'

    # Volatility metrics
    volatility: Optional[float] = None  # Standard deviation of returns
    downside_deviation: Optional[float] = None  # Standard deviation of negative returns

    # Win/Loss metrics
    profit_factor: Optional[float] = None  # Gross profit / Gross loss
    expectancy: Optional[Decimal] = None  # Expected value per trade
    risk_reward_ratio: Optional[float] = None  # Average win / Average loss

    # Recovery metrics
    recovery_factor: Optional[float] = None  # Net profit / Max drawdown

    # Trade distribution
    average_win: Optional[Decimal] = None
    average_loss: Optional[Decimal] = None
    largest_win: Optional[Decimal] = None
    largest_loss: Optional[Decimal] = None

    # Statistical metrics
    win_rate: Optional[float] = None
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0


class RiskCalculator:
    """Calculator for risk management metrics."""

    def __init__(self, risk_free_rate: float = 0.02):
        """
        Initialize risk calculator.

        Args:
            risk_free_rate: Annual risk-free rate for Sharpe ratio (default 2%)
        """
        self.risk_free_rate = risk_free_rate

    def calculate_risk_metrics(self, pnl_results: List[PositionPnL]) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics from P/L results.

        Args:
            pnl_results: List of position P/L results

        Returns:
            RiskMetrics object with all calculated metrics
        """
        if not pnl_results:
            return RiskMetrics()

        # Extract returns
        returns = []
        winning_returns = []
        losing_returns = []

        for pnl in pnl_results:
            if pnl.realized_pnl is not None:
                returns.append(float(pnl.realized_pnl))
                if pnl.realized_pnl > 0:
                    winning_returns.append(float(pnl.realized_pnl))
                elif pnl.realized_pnl < 0:
                    losing_returns.append(float(pnl.realized_pnl))

        if not returns:
            return RiskMetrics()

        # Calculate basic statistics
        total_trades = len(returns)
        winning_trades = len(winning_returns)
        losing_trades = len(losing_returns)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # Calculate Sharpe Ratio
        sharpe = self._calculate_sharpe_ratio(returns)

        # Calculate Sortino Ratio
        sortino = self._calculate_sortino_ratio(returns)

        # Calculate Maximum Drawdown
        max_dd, max_dd_pct = self._calculate_max_drawdown(returns)

        # Calculate Win/Loss Streaks
        longest_win_streak, longest_loss_streak, current_streak, streak_type = \
            self._calculate_streaks(returns)

        # Calculate Volatility
        volatility = self._calculate_volatility(returns)
        downside_dev = self._calculate_downside_deviation(returns)

        # Calculate Profit Factor
        profit_factor = self._calculate_profit_factor(winning_returns, losing_returns)

        # Calculate Expectancy
        expectancy = self._calculate_expectancy(returns)

        # Calculate Risk/Reward Ratio
        risk_reward = self._calculate_risk_reward_ratio(winning_returns, losing_returns)

        # Calculate Recovery Factor
        recovery_factor = self._calculate_recovery_factor(returns, max_dd)

        # Calculate Average Win/Loss
        avg_win = Decimal(str(statistics.mean(winning_returns))) if winning_returns else None
        avg_loss = Decimal(str(statistics.mean(losing_returns))) if losing_returns else None

        # Calculate Largest Win/Loss
        largest_win = Decimal(str(max(winning_returns))) if winning_returns else None
        largest_loss = Decimal(str(min(losing_returns))) if losing_returns else None

        return RiskMetrics(
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_dd,
            max_drawdown_percent=max_dd_pct,
            longest_winning_streak=longest_win_streak,
            longest_losing_streak=longest_loss_streak,
            current_streak=current_streak,
            current_streak_type=streak_type,
            volatility=volatility,
            downside_deviation=downside_dev,
            profit_factor=profit_factor,
            expectancy=expectancy,
            risk_reward_ratio=risk_reward,
            recovery_factor=recovery_factor,
            average_win=avg_win,
            average_loss=avg_loss,
            largest_win=largest_win,
            largest_loss=largest_loss,
            win_rate=win_rate,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades
        )

    def _calculate_sharpe_ratio(self, returns: List[float]) -> Optional[float]:
        """
        Calculate Sharpe Ratio.

        Sharpe Ratio = (Mean Return - Risk Free Rate) / Standard Deviation

        Args:
            returns: List of returns

        Returns:
            Sharpe ratio or None if cannot calculate
        """
        if len(returns) < 2:
            return None

        try:
            mean_return = statistics.mean(returns)
            std_dev = statistics.stdev(returns)

            if std_dev == 0:
                return None

            # Annualize the Sharpe ratio (assuming daily returns)
            sharpe = (mean_return - self.risk_free_rate / 252) / std_dev
            annualized_sharpe = sharpe * math.sqrt(252)

            return round(annualized_sharpe, 2)
        except Exception:
            return None

    def _calculate_sortino_ratio(self, returns: List[float]) -> Optional[float]:
        """
        Calculate Sortino Ratio (uses downside deviation instead of total volatility).

        Args:
            returns: List of returns

        Returns:
            Sortino ratio or None if cannot calculate
        """
        if len(returns) < 2:
            return None

        try:
            mean_return = statistics.mean(returns)
            downside_dev = self._calculate_downside_deviation(returns)

            if downside_dev == 0 or downside_dev is None:
                return None

            # Annualize the Sortino ratio
            sortino = (mean_return - self.risk_free_rate / 252) / downside_dev
            annualized_sortino = sortino * math.sqrt(252)

            return round(annualized_sortino, 2)
        except Exception:
            return None

    def _calculate_max_drawdown(self, returns: List[float]) -> tuple[Optional[Decimal], Optional[float]]:
        """
        Calculate maximum drawdown (largest peak-to-trough decline).

        Args:
            returns: List of returns

        Returns:
            Tuple of (max_drawdown_amount, max_drawdown_percent)
        """
        if not returns:
            return None, None

        # Calculate cumulative returns
        cumulative = [0]
        for ret in returns:
            cumulative.append(cumulative[-1] + ret)

        # Find max drawdown
        max_dd = 0
        max_dd_pct = 0
        peak = cumulative[0]

        for value in cumulative:
            if value > peak:
                peak = value

            drawdown = peak - value
            if drawdown > max_dd:
                max_dd = drawdown
                if peak != 0:
                    max_dd_pct = (drawdown / abs(peak)) * 100

        return Decimal(str(max_dd)) if max_dd > 0 else Decimal("0"), max_dd_pct

    def _calculate_streaks(self, returns: List[float]) -> tuple[int, int, int, Optional[str]]:
        """
        Calculate winning and losing streaks.

        Args:
            returns: List of returns

        Returns:
            Tuple of (longest_win_streak, longest_loss_streak, current_streak, current_streak_type)
        """
        if not returns:
            return 0, 0, 0, None

        longest_win = 0
        longest_loss = 0
        current_win = 0
        current_loss = 0

        for ret in returns:
            if ret > 0:
                current_win += 1
                current_loss = 0
                longest_win = max(longest_win, current_win)
            elif ret < 0:
                current_loss += 1
                current_win = 0
                longest_loss = max(longest_loss, current_loss)
            else:
                # Break even trade
                current_win = 0
                current_loss = 0

        # Determine current streak
        if current_win > 0:
            return longest_win, longest_loss, current_win, 'win'
        elif current_loss > 0:
            return longest_win, longest_loss, current_loss, 'loss'
        else:
            return longest_win, longest_loss, 0, None

    def _calculate_volatility(self, returns: List[float]) -> Optional[float]:
        """Calculate volatility (standard deviation of returns)."""
        if len(returns) < 2:
            return None

        try:
            return round(statistics.stdev(returns), 2)
        except Exception:
            return None

    def _calculate_downside_deviation(self, returns: List[float]) -> Optional[float]:
        """Calculate downside deviation (standard deviation of negative returns)."""
        negative_returns = [r for r in returns if r < 0]

        if len(negative_returns) < 2:
            return None

        try:
            return round(statistics.stdev(negative_returns), 2)
        except Exception:
            return None

    def _calculate_profit_factor(self, winning_returns: List[float],
                                 losing_returns: List[float]) -> Optional[float]:
        """
        Calculate profit factor (gross profit / gross loss).

        A profit factor > 1 means profitable overall.
        """
        if not losing_returns:
            return None

        gross_profit = sum(winning_returns) if winning_returns else 0
        gross_loss = abs(sum(losing_returns))

        if gross_loss == 0:
            return None

        return round(gross_profit / gross_loss, 2)

    def _calculate_expectancy(self, returns: List[float]) -> Optional[Decimal]:
        """Calculate expectancy (expected value per trade)."""
        if not returns:
            return None

        return Decimal(str(statistics.mean(returns)))

    def _calculate_risk_reward_ratio(self, winning_returns: List[float],
                                     losing_returns: List[float]) -> Optional[float]:
        """Calculate risk/reward ratio (average win / average loss)."""
        if not winning_returns or not losing_returns:
            return None

        avg_win = statistics.mean(winning_returns)
        avg_loss = abs(statistics.mean(losing_returns))

        if avg_loss == 0:
            return None

        return round(avg_win / avg_loss, 2)

    def _calculate_recovery_factor(self, returns: List[float],
                                   max_drawdown: Optional[Decimal]) -> Optional[float]:
        """
        Calculate recovery factor (net profit / max drawdown).

        Shows how quickly losses are recovered.
        """
        if not returns or not max_drawdown or max_drawdown == 0:
            return None

        net_profit = sum(returns)

        return round(net_profit / float(max_drawdown), 2)
