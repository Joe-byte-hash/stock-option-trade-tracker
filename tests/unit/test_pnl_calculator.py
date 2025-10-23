"""Unit tests for P/L calculator (TDD approach)."""

from datetime import datetime, date
from decimal import Decimal

import pytest

from trade_tracker.models.trade import StockTrade, OptionTrade, TradeType, OptionType
from trade_tracker.analytics.pnl import PnLCalculator, TradePair, PositionPnL


class TestStockPnL:
    """Test P/L calculations for stock trades."""

    def test_simple_buy_sell_profit(self):
        """Test P/L for profitable buy-sell pair."""
        buy = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY,
            quantity=100,
            price=Decimal("150.00"),
            commission=Decimal("1.00"),
            trade_date=datetime(2024, 1, 1),
        )

        sell = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.SELL,
            quantity=100,
            price=Decimal("160.00"),
            commission=Decimal("1.00"),
            trade_date=datetime(2024, 1, 15),
        )

        calculator = PnLCalculator()
        pnl = calculator.calculate_stock_pnl(buy, sell)

        # Profit = (sell_price - buy_price) * quantity - commissions
        # = (160 - 150) * 100 - 2 = 1000 - 2 = 998
        assert pnl.realized_pnl == Decimal("998.00")
        assert pnl.return_percentage > 0

    def test_simple_buy_sell_loss(self):
        """Test P/L for losing buy-sell pair."""
        buy = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY,
            quantity=100,
            price=Decimal("160.00"),
            commission=Decimal("1.00"),
            trade_date=datetime(2024, 1, 1),
        )

        sell = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.SELL,
            quantity=100,
            price=Decimal("150.00"),
            commission=Decimal("1.00"),
            trade_date=datetime(2024, 1, 15),
        )

        calculator = PnLCalculator()
        pnl = calculator.calculate_stock_pnl(buy, sell)

        # Loss = (150 - 160) * 100 - 2 = -1000 - 2 = -1002
        assert pnl.realized_pnl == Decimal("-1002.00")
        assert pnl.return_percentage < 0

    def test_partial_position_close(self):
        """Test P/L for partial position close."""
        buy = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY,
            quantity=100,
            price=Decimal("150.00"),
            commission=Decimal("1.00"),
            trade_date=datetime(2024, 1, 1),
        )

        # Sell only 50 shares
        sell = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.SELL,
            quantity=50,
            price=Decimal("160.00"),
            commission=Decimal("1.00"),
            trade_date=datetime(2024, 1, 15),
        )

        calculator = PnLCalculator()
        pnl = calculator.calculate_stock_pnl(buy, sell, quantity=50)

        # Profit for 50 shares = (160 - 150) * 50 - 1 (sell commission) - 0.5 (proportional buy commission)
        # = 500 - 1.5 = 498.5
        assert pnl.realized_pnl == Decimal("498.50")

    def test_return_percentage_calculation(self):
        """Test return percentage calculation."""
        buy = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY,
            quantity=100,
            price=Decimal("100.00"),
            commission=Decimal("0"),
            trade_date=datetime(2024, 1, 1),
        )

        sell = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.SELL,
            quantity=100,
            price=Decimal("120.00"),
            commission=Decimal("0"),
            trade_date=datetime(2024, 1, 15),
        )

        calculator = PnLCalculator()
        pnl = calculator.calculate_stock_pnl(buy, sell)

        # Return = (120 - 100) / 100 = 20%
        assert pnl.return_percentage == Decimal("20.00")


class TestOptionPnL:
    """Test P/L calculations for option trades."""

    def test_long_call_profit(self):
        """Test P/L for profitable long call."""
        buy = OptionTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY_TO_OPEN,
            quantity=10,
            price=Decimal("5.00"),
            strike=Decimal("150.00"),
            expiry=date(2024, 3, 15),
            option_type=OptionType.CALL,
            commission=Decimal("6.50"),
            trade_date=datetime(2024, 1, 1),
        )

        sell = OptionTrade(
            symbol="AAPL",
            trade_type=TradeType.SELL_TO_CLOSE,
            quantity=10,
            price=Decimal("8.00"),
            strike=Decimal("150.00"),
            expiry=date(2024, 3, 15),
            option_type=OptionType.CALL,
            commission=Decimal("6.50"),
            trade_date=datetime(2024, 1, 15),
        )

        calculator = PnLCalculator()
        pnl = calculator.calculate_option_pnl(buy, sell)

        # Profit = (8 - 5) * 10 contracts * 100 multiplier - commissions
        # = 3 * 1000 - 13 = 3000 - 13 = 2987
        assert pnl.realized_pnl == Decimal("2987.00")
        assert pnl.return_percentage > 0

    def test_long_put_loss(self):
        """Test P/L for losing long put."""
        buy = OptionTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY_TO_OPEN,
            quantity=5,
            price=Decimal("4.00"),
            strike=Decimal("145.00"),
            expiry=date(2024, 3, 15),
            option_type=OptionType.PUT,
            commission=Decimal("3.25"),
            trade_date=datetime(2024, 1, 1),
        )

        sell = OptionTrade(
            symbol="AAPL",
            trade_type=TradeType.SELL_TO_CLOSE,
            quantity=5,
            price=Decimal("2.00"),
            strike=Decimal("145.00"),
            expiry=date(2024, 3, 15),
            option_type=OptionType.PUT,
            commission=Decimal("3.25"),
            trade_date=datetime(2024, 1, 15),
        )

        calculator = PnLCalculator()
        pnl = calculator.calculate_option_pnl(buy, sell)

        # Loss = (2 - 4) * 5 * 100 - commissions
        # = -2 * 500 - 6.5 = -1000 - 6.5 = -1006.5
        assert pnl.realized_pnl == Decimal("-1006.50")
        assert pnl.return_percentage < 0

    def test_option_worthless_expiration(self):
        """Test P/L for option expiring worthless."""
        buy = OptionTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY_TO_OPEN,
            quantity=10,
            price=Decimal("3.00"),
            strike=Decimal("150.00"),
            expiry=date(2024, 3, 15),
            option_type=OptionType.CALL,
            commission=Decimal("6.50"),
            trade_date=datetime(2024, 1, 1),
        )

        calculator = PnLCalculator()
        pnl = calculator.calculate_option_expiry_pnl(buy, expired_worthless=True)

        # Total loss = premium paid + commission
        # = 3 * 10 * 100 + 6.5 = 3006.5
        assert pnl.realized_pnl == Decimal("-3006.50")
        assert pnl.return_percentage == Decimal("-100.00")


class TestMultipleTradePnL:
    """Test P/L calculations across multiple trades."""

    def test_aggregate_pnl_multiple_trades(self):
        """Test aggregate P/L across multiple trade pairs."""
        trades = [
            # Winning trade
            (
                StockTrade(symbol="AAPL", trade_type=TradeType.BUY, quantity=100,
                          price=Decimal("150"), trade_date=datetime(2024, 1, 1)),
                StockTrade(symbol="AAPL", trade_type=TradeType.SELL, quantity=100,
                          price=Decimal("160"), trade_date=datetime(2024, 1, 15)),
            ),
            # Losing trade
            (
                StockTrade(symbol="TSLA", trade_type=TradeType.BUY, quantity=50,
                          price=Decimal("200"), trade_date=datetime(2024, 1, 1)),
                StockTrade(symbol="TSLA", trade_type=TradeType.SELL, quantity=50,
                          price=Decimal("190"), trade_date=datetime(2024, 1, 15)),
            ),
        ]

        calculator = PnLCalculator()
        total_pnl = Decimal("0")

        for buy, sell in trades:
            pnl = calculator.calculate_stock_pnl(buy, sell)
            total_pnl += pnl.realized_pnl

        # AAPL: (160-150)*100 = 1000
        # TSLA: (190-200)*50 = -500
        # Total: 500
        assert total_pnl == Decimal("500.00")

    def test_holding_period_calculation(self):
        """Test holding period calculation in days."""
        buy = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY,
            quantity=100,
            price=Decimal("150.00"),
            trade_date=datetime(2024, 1, 1),
        )

        sell = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.SELL,
            quantity=100,
            price=Decimal("160.00"),
            trade_date=datetime(2024, 1, 15),
        )

        calculator = PnLCalculator()
        pnl = calculator.calculate_stock_pnl(buy, sell)

        assert pnl.holding_period_days == 14  # Jan 15 - Jan 1


class TestPositionPnL:
    """Test P/L for open positions."""

    def test_unrealized_pnl_stock(self):
        """Test unrealized P/L for open stock position."""
        buy = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY,
            quantity=100,
            price=Decimal("150.00"),
            commission=Decimal("1.00"),
            trade_date=datetime(2024, 1, 1),
        )

        calculator = PnLCalculator()
        current_price = Decimal("160.00")
        pnl = calculator.calculate_unrealized_stock_pnl(buy, current_price)

        # Unrealized profit = (160 - 150) * 100 - commission
        # = 1000 - 1 = 999
        assert pnl.unrealized_pnl == Decimal("999.00")
        assert pnl.return_percentage > 0

    def test_unrealized_pnl_option(self):
        """Test unrealized P/L for open option position."""
        buy = OptionTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY_TO_OPEN,
            quantity=10,
            price=Decimal("5.00"),
            strike=Decimal("150.00"),
            expiry=date(2024, 3, 15),
            option_type=OptionType.CALL,
            commission=Decimal("6.50"),
            trade_date=datetime(2024, 1, 1),
        )

        calculator = PnLCalculator()
        current_price = Decimal("8.00")
        pnl = calculator.calculate_unrealized_option_pnl(buy, current_price)

        # Unrealized profit = (8 - 5) * 10 * 100 - commission
        # = 3000 - 6.5 = 2993.5
        assert pnl.unrealized_pnl == Decimal("2993.50")
