"""Portfolio metrics and analytics calculations."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Tuple

from trade_tracker.analytics.pnl import PositionPnL


@dataclass
class TradeStatistics:
    """Trade statistics including win rate and averages."""

    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: Decimal = Decimal("0")
    average_win: Decimal = Decimal("0")
    average_loss: Decimal = Decimal("0")
    largest_win: Decimal = Decimal("0")
    largest_loss: Decimal = Decimal("0")
    profit_factor: Decimal = Decimal("0")


@dataclass
class DrawdownMetrics:
    """Maximum drawdown metrics."""

    max_drawdown_amount: Decimal = Decimal("0")
    max_drawdown_percent: Decimal = Decimal("0")
    peak_date: datetime | None = None
    trough_date: datetime | None = None


@dataclass
class PortfolioMetrics:
    """Comprehensive portfolio metrics."""

    total_pnl: Decimal = Decimal("0")
    total_return_percentage: Decimal = Decimal("0")
    win_rate: Decimal = Decimal("0")
    profit_factor: Decimal = Decimal("0")
    sharpe_ratio: Decimal = Decimal("0")
    max_drawdown_percent: Decimal = Decimal("0")
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0


@dataclass
class PeriodReturns:
    """Returns for a specific time period."""

    period: str
    pnl: Decimal
    return_percentage: Decimal


class MetricsCalculator:
    """Calculator for portfolio metrics and analytics."""

    def calculate_trade_statistics(self, pnl_results: List[PositionPnL]) -> TradeStatistics:
        """
        Calculate trade statistics including win rate.

        Args:
            pnl_results: List of P/L results

        Returns:
            TradeStatistics with win rate and averages
        """
        if not pnl_results:
            return TradeStatistics()

        total_trades = len(pnl_results)
        wins = [p for p in pnl_results if p.realized_pnl and p.realized_pnl > 0]
        losses = [p for p in pnl_results if p.realized_pnl and p.realized_pnl < 0]

        winning_trades = len(wins)
        losing_trades = len(losses)

        # Win rate
        win_rate = (Decimal(winning_trades) / Decimal(total_trades) * 100) if total_trades > 0 else Decimal("0")

        # Average win/loss
        average_win = sum(p.realized_pnl for p in wins) / len(wins) if wins else Decimal("0")
        average_loss = sum(p.realized_pnl for p in losses) / len(losses) if losses else Decimal("0")

        # Largest win/loss
        largest_win = max((p.realized_pnl for p in wins), default=Decimal("0"))
        largest_loss = min((p.realized_pnl for p in losses), default=Decimal("0"))

        # Profit factor
        gross_profit = sum(p.realized_pnl for p in wins)
        gross_loss = abs(sum(p.realized_pnl for p in losses))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else Decimal("0")

        return TradeStatistics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate.quantize(Decimal("0.01")),
            average_win=average_win.quantize(Decimal("0.01")),
            average_loss=average_loss.quantize(Decimal("0.01")),
            largest_win=largest_win.quantize(Decimal("0.01")),
            largest_loss=largest_loss.quantize(Decimal("0.01")),
            profit_factor=profit_factor.quantize(Decimal("0.01")),
        )

    def calculate_max_drawdown(
        self, equity_curve: List[Tuple[datetime, Decimal]]
    ) -> DrawdownMetrics:
        """
        Calculate maximum drawdown from equity curve.

        Args:
            equity_curve: List of (datetime, equity_value) tuples

        Returns:
            DrawdownMetrics with max drawdown info
        """
        if not equity_curve:
            return DrawdownMetrics()

        max_drawdown_amount = Decimal("0")
        max_drawdown_percent = Decimal("0")
        peak = equity_curve[0][1]
        peak_date = equity_curve[0][0]
        trough_date = None

        for timestamp, equity in equity_curve:
            if equity > peak:
                peak = equity
                peak_date = timestamp

            drawdown = peak - equity
            if drawdown > max_drawdown_amount:
                max_drawdown_amount = drawdown
                trough_date = timestamp
                max_drawdown_percent = (drawdown / peak * 100) if peak > 0 else Decimal("0")

        return DrawdownMetrics(
            max_drawdown_amount=max_drawdown_amount.quantize(Decimal("0.01")),
            max_drawdown_percent=max_drawdown_percent.quantize(Decimal("0.01")),
            peak_date=peak_date,
            trough_date=trough_date,
        )

    def calculate_daily_pnl(
        self, trades: List[Tuple[datetime, Decimal]]
    ) -> Dict[date, Decimal]:
        """
        Calculate daily P/L.

        Args:
            trades: List of (trade_date, pnl) tuples

        Returns:
            Dictionary mapping date to daily P/L
        """
        daily_pnl = defaultdict(Decimal)

        for trade_date, pnl in trades:
            day = trade_date.date()
            daily_pnl[day] += pnl

        return dict(daily_pnl)

    def calculate_weekly_pnl(
        self, trades: List[Tuple[datetime, Decimal]]
    ) -> Dict[Tuple[int, int], Decimal]:
        """
        Calculate weekly P/L.

        Args:
            trades: List of (trade_date, pnl) tuples

        Returns:
            Dictionary mapping (year, week_number) to weekly P/L
        """
        weekly_pnl = defaultdict(Decimal)

        for trade_date, pnl in trades:
            year, week, _ = trade_date.isocalendar()
            weekly_pnl[(year, week)] += pnl

        return dict(weekly_pnl)

    def calculate_monthly_pnl(
        self, trades: List[Tuple[datetime, Decimal]]
    ) -> Dict[Tuple[int, int], Decimal]:
        """
        Calculate monthly P/L.

        Args:
            trades: List of (trade_date, pnl) tuples

        Returns:
            Dictionary mapping (year, month) to monthly P/L
        """
        monthly_pnl = defaultdict(Decimal)

        for trade_date, pnl in trades:
            monthly_pnl[(trade_date.year, trade_date.month)] += pnl

        return dict(monthly_pnl)

    def calculate_yearly_pnl(
        self, trades: List[Tuple[datetime, Decimal]]
    ) -> Dict[int, Decimal]:
        """
        Calculate yearly P/L.

        Args:
            trades: List of (trade_date, pnl) tuples

        Returns:
            Dictionary mapping year to yearly P/L
        """
        yearly_pnl = defaultdict(Decimal)

        for trade_date, pnl in trades:
            yearly_pnl[trade_date.year] += pnl

        return dict(yearly_pnl)

    def calculate_sharpe_ratio(
        self,
        returns: List[Decimal],
        risk_free_rate: Decimal = Decimal("0.02"),
        periods_per_year: int = 252,
    ) -> Decimal:
        """
        Calculate Sharpe ratio.

        Args:
            returns: List of period returns (as decimals, e.g., 0.05 for 5%)
            risk_free_rate: Annual risk-free rate (default: 2%)
            periods_per_year: Number of periods per year (default: 252 for daily)

        Returns:
            Sharpe ratio

        Note:
            Sharpe Ratio = (Mean Return - Risk Free Rate) / Standard Deviation
        """
        if not returns or len(returns) < 2:
            return Decimal("0")

        # Calculate mean return
        mean_return = sum(returns) / len(returns)

        # Calculate standard deviation
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        std_dev = variance.sqrt() if variance > 0 else Decimal("0")

        if std_dev == 0:
            return Decimal("0")

        # Annualize
        annual_return = mean_return * periods_per_year
        annual_std_dev = std_dev * (Decimal(periods_per_year).sqrt())

        # Sharpe ratio
        sharpe = (annual_return - risk_free_rate) / annual_std_dev

        return sharpe.quantize(Decimal("0.01"))

    def calculate_portfolio_metrics(
        self,
        pnl_results: List[PositionPnL],
        initial_capital: Decimal = Decimal("10000"),
    ) -> PortfolioMetrics:
        """
        Calculate comprehensive portfolio metrics.

        Args:
            pnl_results: List of P/L results
            initial_capital: Initial portfolio capital

        Returns:
            PortfolioMetrics with comprehensive statistics
        """
        if not pnl_results:
            return PortfolioMetrics()

        # Trade statistics
        stats = self.calculate_trade_statistics(pnl_results)

        # Total P/L
        total_pnl = sum(p.realized_pnl for p in pnl_results if p.realized_pnl)

        # Total return percentage
        total_return_pct = (total_pnl / initial_capital * 100) if initial_capital > 0 else Decimal("0")

        return PortfolioMetrics(
            total_pnl=total_pnl.quantize(Decimal("0.01")),
            total_return_percentage=total_return_pct.quantize(Decimal("0.01")),
            win_rate=stats.win_rate,
            profit_factor=stats.profit_factor,
            max_drawdown_percent=Decimal("0"),  # Would need equity curve
            total_trades=stats.total_trades,
            winning_trades=stats.winning_trades,
            losing_trades=stats.losing_trades,
        )
