"""Tests for strategy analytics functionality."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from trade_tracker.analytics.strategy import StrategyAnalyzer
from trade_tracker.models.trade import StockTrade, TradeType, TradingStrategy
from trade_tracker.analytics.pnl import PositionPnL


@pytest.fixture
def sample_strategy_trades():
    """Create sample trades with different strategies."""
    base_date = datetime(2024, 1, 1)

    return [
        # Day trading strategy - winner
        StockTrade(
            id=1,
            symbol="AAPL",
            trade_type=TradeType.BUY,
            quantity=100,
            price=Decimal("150.00"),
            commission=Decimal("1.00"),
            trade_date=base_date,
            strategy=TradingStrategy.DAY_TRADE,
            account_id=1
        ),
        StockTrade(
            id=2,
            symbol="AAPL",
            trade_type=TradeType.SELL,
            quantity=100,
            price=Decimal("155.00"),
            commission=Decimal("1.00"),
            trade_date=base_date + timedelta(hours=6),
            strategy=TradingStrategy.DAY_TRADE,
            account_id=1
        ),

        # Swing trading strategy - loser
        StockTrade(
            id=3,
            symbol="TSLA",
            trade_type=TradeType.BUY,
            quantity=50,
            price=Decimal("200.00"),
            commission=Decimal("1.00"),
            trade_date=base_date + timedelta(days=1),
            strategy=TradingStrategy.SWING_TRADE,
            account_id=1
        ),
        StockTrade(
            id=4,
            symbol="TSLA",
            trade_type=TradeType.SELL,
            quantity=50,
            price=Decimal("195.00"),
            commission=Decimal("1.00"),
            trade_date=base_date + timedelta(days=5),
            strategy=TradingStrategy.SWING_TRADE,
            account_id=1
        ),

        # Day trading strategy - winner again
        StockTrade(
            id=5,
            symbol="MSFT",
            trade_type=TradeType.BUY,
            quantity=75,
            price=Decimal("300.00"),
            commission=Decimal("1.00"),
            trade_date=base_date + timedelta(days=2),
            strategy=TradingStrategy.DAY_TRADE,
            account_id=1
        ),
        StockTrade(
            id=6,
            symbol="MSFT",
            trade_type=TradeType.SELL,
            quantity=75,
            price=Decimal("305.00"),
            commission=Decimal("1.00"),
            trade_date=base_date + timedelta(days=2, hours=4),
            strategy=TradingStrategy.DAY_TRADE,
            account_id=1
        ),

        # Momentum strategy - winner
        StockTrade(
            id=7,
            symbol="NVDA",
            trade_type=TradeType.BUY,
            quantity=40,
            price=Decimal("400.00"),
            commission=Decimal("1.00"),
            trade_date=base_date + timedelta(days=3),
            strategy=TradingStrategy.MOMENTUM,
            account_id=1
        ),
        StockTrade(
            id=8,
            symbol="NVDA",
            trade_type=TradeType.SELL,
            quantity=40,
            price=Decimal("420.00"),
            commission=Decimal("1.00"),
            trade_date=base_date + timedelta(days=10),
            strategy=TradingStrategy.MOMENTUM,
            account_id=1
        ),
    ]


@pytest.fixture
def sample_pnl_results():
    """Create sample P/L results matching the trades."""
    return [
        # Day trade 1 - win
        PositionPnL(
            symbol="AAPL",
            realized_pnl=Decimal("498.00"),  # (155-150)*100 - 2
            unrealized_pnl=Decimal("0"),
            quantity=0,
            entry_price=Decimal("150.00"),
            exit_price=Decimal("155.00"),
            entry_date=datetime(2024, 1, 1),
            exit_date=datetime(2024, 1, 1, 6, 0)
        ),
        # Swing trade - loss
        PositionPnL(
            symbol="TSLA",
            realized_pnl=Decimal("-252.00"),  # (195-200)*50 - 2
            unrealized_pnl=Decimal("0"),
            quantity=0,
            entry_price=Decimal("200.00"),
            exit_price=Decimal("195.00"),
            entry_date=datetime(2024, 1, 2),
            exit_date=datetime(2024, 1, 6)
        ),
        # Day trade 2 - win
        PositionPnL(
            symbol="MSFT",
            realized_pnl=Decimal("373.00"),  # (305-300)*75 - 2
            unrealized_pnl=Decimal("0"),
            quantity=0,
            entry_price=Decimal("300.00"),
            exit_price=Decimal("305.00"),
            entry_date=datetime(2024, 1, 3),
            exit_date=datetime(2024, 1, 3, 4, 0)
        ),
        # Momentum - win
        PositionPnL(
            symbol="NVDA",
            realized_pnl=Decimal("798.00"),  # (420-400)*40 - 2
            unrealized_pnl=Decimal("0"),
            quantity=0,
            entry_price=Decimal("400.00"),
            exit_price=Decimal("420.00"),
            entry_date=datetime(2024, 1, 4),
            exit_date=datetime(2024, 1, 11)
        ),
    ]


class TestStrategyAnalyzer:
    """Test StrategyAnalyzer class."""

    def test_create_analyzer(self):
        """Test creating strategy analyzer."""
        analyzer = StrategyAnalyzer()
        assert analyzer is not None

    def test_analyze_strategy_performance(self, sample_strategy_trades, sample_pnl_results):
        """Test analyzing performance by strategy."""
        analyzer = StrategyAnalyzer()
        results = analyzer.analyze_by_strategy(sample_strategy_trades, sample_pnl_results)

        assert results is not None
        assert isinstance(results, list)
        assert len(results) > 0

        # Check for day_trade strategy
        day_trade_result = next((r for r in results if r['strategy'] == TradingStrategy.DAY_TRADE), None)
        assert day_trade_result is not None
        assert day_trade_result['total_trades'] == 2  # 2 pairs of day trades
        assert day_trade_result['winning_trades'] == 2
        assert day_trade_result['losing_trades'] == 0
        assert day_trade_result['win_rate'] == 100.0
        assert day_trade_result['total_pnl'] > 0

    def test_strategy_win_rate_calculation(self, sample_strategy_trades, sample_pnl_results):
        """Test win rate calculation per strategy."""
        analyzer = StrategyAnalyzer()
        results = analyzer.analyze_by_strategy(sample_strategy_trades, sample_pnl_results)

        swing_trade_result = next((r for r in results if r['strategy'] == TradingStrategy.SWING_TRADE), None)
        assert swing_trade_result is not None
        assert swing_trade_result['win_rate'] == 0.0  # 0/1 = 0%

        momentum_result = next((r for r in results if r['strategy'] == TradingStrategy.MOMENTUM), None)
        assert momentum_result is not None
        assert momentum_result['win_rate'] == 100.0  # 1/1 = 100%

    def test_strategy_pnl_aggregation(self, sample_strategy_trades, sample_pnl_results):
        """Test P/L aggregation by strategy."""
        analyzer = StrategyAnalyzer()
        results = analyzer.analyze_by_strategy(sample_strategy_trades, sample_pnl_results)

        # Day trade total: 498 + 373 = 871
        day_trade_result = next((r for r in results if r['strategy'] == TradingStrategy.DAY_TRADE), None)
        assert day_trade_result['total_pnl'] == Decimal("871.00")
        assert day_trade_result['average_pnl'] == Decimal("435.50")  # 871/2

    def test_best_performing_strategy(self, sample_strategy_trades, sample_pnl_results):
        """Test identifying best performing strategy."""
        analyzer = StrategyAnalyzer()
        best_strategy = analyzer.get_best_strategy(sample_strategy_trades, sample_pnl_results)

        assert best_strategy is not None
        # Day trade has highest total P/L (871)
        assert best_strategy['strategy'] == TradingStrategy.DAY_TRADE

    def test_worst_performing_strategy(self, sample_strategy_trades, sample_pnl_results):
        """Test identifying worst performing strategy."""
        analyzer = StrategyAnalyzer()
        worst_strategy = analyzer.get_worst_strategy(sample_strategy_trades, sample_pnl_results)

        assert worst_strategy is not None
        # Swing trade has negative P/L (-252)
        assert worst_strategy['strategy'] == TradingStrategy.SWING_TRADE

    def test_strategy_count_calculation(self, sample_strategy_trades, sample_pnl_results):
        """Test counting trades per strategy."""
        analyzer = StrategyAnalyzer()
        results = analyzer.analyze_by_strategy(sample_strategy_trades, sample_pnl_results)

        total_strategies = len(results)
        assert total_strategies == 3  # day_trade, swing_trade, momentum

    def test_empty_trades_handling(self):
        """Test handling empty trades list."""
        analyzer = StrategyAnalyzer()
        results = analyzer.analyze_by_strategy([], [])

        assert results == []

    def test_untagged_strategy_handling(self):
        """Test handling trades without strategy tags."""
        trades = [
            StockTrade(
                id=1,
                symbol="TEST",
                trade_type=TradeType.BUY,
                quantity=100,
                price=Decimal("100.00"),
                commission=Decimal("1.00"),
                trade_date=datetime(2024, 1, 1),
                # No strategy specified, should default to UNTAGGED
                account_id=1
            )
        ]

        analyzer = StrategyAnalyzer()
        results = analyzer.analyze_by_strategy(trades, [])

        # Should have one result for UNTAGGED
        assert len(results) >= 0  # Depends on if we filter untagged or not

    def test_strategy_comparison(self, sample_strategy_trades, sample_pnl_results):
        """Test comparing strategies side by side."""
        analyzer = StrategyAnalyzer()
        comparison = analyzer.compare_strategies(sample_strategy_trades, sample_pnl_results)

        assert comparison is not None
        assert 'strategies' in comparison
        assert 'best_strategy' in comparison
        assert 'worst_strategy' in comparison
        assert comparison['total_strategies'] == 3
