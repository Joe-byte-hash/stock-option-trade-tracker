"""
Strategy analytics for trade performance by strategy.

Provides analysis of trading performance grouped by strategy tags.
"""

from typing import List, Dict, Any, Optional
from decimal import Decimal
from collections import defaultdict

from trade_tracker.models.trade import Trade, TradingStrategy
from trade_tracker.analytics.pnl import PositionPnL


class StrategyAnalyzer:
    """
    Analyze trading performance by strategy.

    Provides insights into which trading strategies are most profitable,
    win rates by strategy, and comparisons across different approaches.
    """

    def __init__(self):
        """Initialize strategy analyzer."""
        pass

    def analyze_by_strategy(
        self,
        trades: List[Trade],
        pnl_results: List[PositionPnL]
    ) -> List[Dict[str, Any]]:
        """
        Analyze performance metrics grouped by strategy.

        Args:
            trades: List of all trades
            pnl_results: List of P/L results

        Returns:
            List of dictionaries with strategy metrics:
            {
                'strategy': TradingStrategy,
                'strategy_name': str,
                'total_trades': int,
                'winning_trades': int,
                'losing_trades': int,
                'win_rate': float,
                'total_pnl': Decimal,
                'average_pnl': Decimal,
                'max_win': Decimal,
                'max_loss': Decimal
            }
        """
        if not trades:
            return []

        # Group trades by strategy
        strategy_groups = defaultdict(list)
        for trade in trades:
            strategy = trade.strategy or TradingStrategy.UNTAGGED
            strategy_groups[strategy].append(trade)

        # Create symbol to P/L mapping for quick lookup
        symbol_pnl = {pnl.symbol: pnl for pnl in pnl_results}

        results = []

        for strategy, strategy_trades in strategy_groups.items():
            # Get unique symbols (completed positions)
            symbols = set()
            for trade in strategy_trades:
                if trade.symbol in symbol_pnl:
                    symbols.add(trade.symbol)

            if not symbols:
                # No completed positions for this strategy
                continue

            # Calculate metrics (total P/L = realized + unrealized)
            strategy_pnls = []
            for symbol in symbols:
                pnl_result = symbol_pnl[symbol]
                total_pnl = (pnl_result.realized_pnl or Decimal("0")) + (pnl_result.unrealized_pnl or Decimal("0"))
                strategy_pnls.append(total_pnl)

            winning_pnls = [pnl for pnl in strategy_pnls if pnl > 0]
            losing_pnls = [pnl for pnl in strategy_pnls if pnl < 0]

            total_trades = len(symbols)
            winning_trades = len(winning_pnls)
            losing_trades = len(losing_pnls)
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

            total_pnl = sum(strategy_pnls, Decimal("0"))
            average_pnl = total_pnl / total_trades if total_trades > 0 else Decimal("0")

            max_win = max(strategy_pnls, default=Decimal("0"))
            max_loss = min(strategy_pnls, default=Decimal("0"))

            results.append({
                'strategy': strategy,
                'strategy_name': self._format_strategy_name(strategy),
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': round(win_rate, 2),
                'total_pnl': total_pnl,
                'average_pnl': average_pnl,
                'max_win': max_win,
                'max_loss': max_loss
            })

        # Sort by total P/L descending
        results.sort(key=lambda x: x['total_pnl'], reverse=True)

        return results

    def get_best_strategy(
        self,
        trades: List[Trade],
        pnl_results: List[PositionPnL]
    ) -> Optional[Dict[str, Any]]:
        """
        Get the best performing strategy by total P/L.

        Args:
            trades: List of all trades
            pnl_results: List of P/L results

        Returns:
            Dictionary with best strategy metrics, or None if no data
        """
        results = self.analyze_by_strategy(trades, pnl_results)

        if not results:
            return None

        # Results are already sorted by total P/L descending
        return results[0]

    def get_worst_strategy(
        self,
        trades: List[Trade],
        pnl_results: List[PositionPnL]
    ) -> Optional[Dict[str, Any]]:
        """
        Get the worst performing strategy by total P/L.

        Args:
            trades: List of all trades
            pnl_results: List of P/L results

        Returns:
            Dictionary with worst strategy metrics, or None if no data
        """
        results = self.analyze_by_strategy(trades, pnl_results)

        if not results:
            return None

        # Results are sorted by total P/L descending, so last is worst
        return results[-1]

    def compare_strategies(
        self,
        trades: List[Trade],
        pnl_results: List[PositionPnL]
    ) -> Dict[str, Any]:
        """
        Compare all strategies side by side.

        Args:
            trades: List of all trades
            pnl_results: List of P/L results

        Returns:
            Dictionary with comparison data:
            {
                'strategies': List[Dict],
                'best_strategy': Dict,
                'worst_strategy': Dict,
                'total_strategies': int,
                'most_used_strategy': Dict
            }
        """
        results = self.analyze_by_strategy(trades, pnl_results)

        if not results:
            return {
                'strategies': [],
                'best_strategy': None,
                'worst_strategy': None,
                'total_strategies': 0,
                'most_used_strategy': None
            }

        # Find most used strategy
        most_used = max(results, key=lambda x: x['total_trades'])

        return {
            'strategies': results,
            'best_strategy': results[0],  # Highest P/L
            'worst_strategy': results[-1],  # Lowest P/L
            'total_strategies': len(results),
            'most_used_strategy': most_used
        }

    def get_strategy_summary(
        self,
        trades: List[Trade],
        pnl_results: List[PositionPnL]
    ) -> Dict[str, Any]:
        """
        Get summary statistics for strategy usage.

        Args:
            trades: List of all trades
            pnl_results: List of P/L results

        Returns:
            Dictionary with summary stats
        """
        results = self.analyze_by_strategy(trades, pnl_results)

        if not results:
            return {
                'total_strategies_used': 0,
                'average_win_rate': 0.0,
                'best_win_rate': 0.0,
                'strategies_with_positive_pnl': 0
            }

        total_strategies = len(results)
        avg_win_rate = sum(r['win_rate'] for r in results) / total_strategies
        best_win_rate = max(r['win_rate'] for r in results)
        positive_pnl_count = sum(1 for r in results if r['total_pnl'] > 0)

        return {
            'total_strategies_used': total_strategies,
            'average_win_rate': round(avg_win_rate, 2),
            'best_win_rate': round(best_win_rate, 2),
            'strategies_with_positive_pnl': positive_pnl_count
        }

    def _format_strategy_name(self, strategy: TradingStrategy) -> str:
        """
        Format strategy enum to human-readable name.

        Args:
            strategy: TradingStrategy enum

        Returns:
            Formatted string
        """
        # Convert from snake_case to Title Case
        return strategy.value.replace('_', ' ').title()
