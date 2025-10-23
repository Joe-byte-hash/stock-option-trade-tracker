"""Profit and Loss (P/L) calculation engine."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from trade_tracker.models.trade import StockTrade, OptionTrade, TradeType


@dataclass
class TradePair:
    """Represents a matched buy/sell trade pair."""

    opening_trade: StockTrade | OptionTrade
    closing_trade: StockTrade | OptionTrade
    quantity: int


@dataclass
class PositionPnL:
    """P/L result for a trade or position."""

    symbol: str
    realized_pnl: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    return_percentage: Optional[Decimal] = None
    cost_basis: Optional[Decimal] = None
    proceeds: Optional[Decimal] = None
    holding_period_days: Optional[int] = None
    quantity: Optional[int] = None
    entry_price: Optional[Decimal] = None
    exit_price: Optional[Decimal] = None
    entry_date: Optional[datetime] = None
    exit_date: Optional[datetime] = None


class PnLCalculator:
    """Calculator for profit and loss calculations."""

    def calculate_stock_pnl(
        self,
        buy_trade: StockTrade,
        sell_trade: StockTrade,
        quantity: Optional[int] = None,
    ) -> PositionPnL:
        """
        Calculate realized P/L for a stock trade pair.

        Args:
            buy_trade: Opening buy trade
            sell_trade: Closing sell trade
            quantity: Quantity to calculate (defaults to sell trade quantity)

        Returns:
            PositionPnL with realized P/L

        Example:
            >>> buy = StockTrade(symbol="AAPL", trade_type=TradeType.BUY,
            ...                  quantity=100, price=Decimal("150"))
            >>> sell = StockTrade(symbol="AAPL", trade_type=TradeType.SELL,
            ...                   quantity=100, price=Decimal("160"))
            >>> calculator = PnLCalculator()
            >>> pnl = calculator.calculate_stock_pnl(buy, sell)
            >>> print(pnl.realized_pnl)  # Profit: 1000
        """
        if quantity is None:
            quantity = sell_trade.quantity

        # Proportional commissions
        buy_commission_per_share = buy_trade.commission / buy_trade.quantity
        sell_commission_per_share = sell_trade.commission / sell_trade.quantity

        buy_cost_per_share = buy_trade.price + buy_commission_per_share
        sell_proceeds_per_share = sell_trade.price - sell_commission_per_share

        # Calculate total cost basis and proceeds
        cost_basis = buy_cost_per_share * quantity
        proceeds = sell_proceeds_per_share * quantity

        # Realized P/L
        realized_pnl = proceeds - cost_basis

        # Return percentage
        return_pct = (realized_pnl / cost_basis * 100) if cost_basis != 0 else Decimal("0")

        # Holding period
        holding_days = (sell_trade.trade_date - buy_trade.trade_date).days

        return PositionPnL(
            symbol=buy_trade.symbol,
            realized_pnl=realized_pnl.quantize(Decimal("0.01")),
            return_percentage=return_pct.quantize(Decimal("0.01")),
            cost_basis=cost_basis.quantize(Decimal("0.01")),
            proceeds=proceeds.quantize(Decimal("0.01")),
            holding_period_days=holding_days,
            quantity=quantity,
            entry_price=buy_trade.price,
            exit_price=sell_trade.price,
            entry_date=buy_trade.trade_date,
            exit_date=sell_trade.trade_date,
        )

    def calculate_option_pnl(
        self,
        buy_trade: OptionTrade,
        sell_trade: OptionTrade,
        quantity: Optional[int] = None,
    ) -> PositionPnL:
        """
        Calculate realized P/L for an option trade pair.

        Args:
            buy_trade: Opening buy trade
            sell_trade: Closing sell trade
            quantity: Number of contracts (defaults to sell trade quantity)

        Returns:
            PositionPnL with realized P/L
        """
        if quantity is None:
            quantity = sell_trade.quantity

        # Proportional commissions
        buy_commission_per_contract = buy_trade.commission / buy_trade.quantity
        sell_commission_per_contract = sell_trade.commission / sell_trade.quantity

        # Cost per contract (including multiplier)
        buy_cost_per_contract = (
            buy_trade.price * buy_trade.multiplier + buy_commission_per_contract
        )
        sell_proceeds_per_contract = (
            sell_trade.price * sell_trade.multiplier - sell_commission_per_contract
        )

        # Calculate total cost basis and proceeds
        cost_basis = buy_cost_per_contract * quantity
        proceeds = sell_proceeds_per_contract * quantity

        # Realized P/L
        realized_pnl = proceeds - cost_basis

        # Return percentage
        return_pct = (realized_pnl / cost_basis * 100) if cost_basis != 0 else Decimal("0")

        # Holding period
        holding_days = (sell_trade.trade_date - buy_trade.trade_date).days

        return PositionPnL(
            symbol=buy_trade.symbol,
            realized_pnl=realized_pnl.quantize(Decimal("0.01")),
            return_percentage=return_pct.quantize(Decimal("0.01")),
            cost_basis=cost_basis.quantize(Decimal("0.01")),
            proceeds=proceeds.quantize(Decimal("0.01")),
            holding_period_days=holding_days,
            quantity=quantity,
            entry_price=buy_trade.price,
            exit_price=sell_trade.price,
            entry_date=buy_trade.trade_date,
            exit_date=sell_trade.trade_date,
        )

    def calculate_option_expiry_pnl(
        self, buy_trade: OptionTrade, expired_worthless: bool = True
    ) -> PositionPnL:
        """
        Calculate P/L for an expired option.

        Args:
            buy_trade: Opening buy trade
            expired_worthless: Whether option expired worthless (default: True)

        Returns:
            PositionPnL with realized P/L
        """
        # Cost basis includes premium and commission
        cost_basis = (
            buy_trade.price * buy_trade.quantity * buy_trade.multiplier
            + buy_trade.commission
        )

        if expired_worthless:
            # Total loss
            realized_pnl = -cost_basis
            return_pct = Decimal("-100.00")
        else:
            # This would be intrinsic value at expiry
            # For now, we handle worthless expiration
            realized_pnl = -cost_basis
            return_pct = Decimal("-100.00")

        return PositionPnL(
            symbol=buy_trade.symbol,
            realized_pnl=realized_pnl.quantize(Decimal("0.01")),
            return_percentage=return_pct,
            cost_basis=cost_basis.quantize(Decimal("0.01")),
            proceeds=Decimal("0.00"),
        )

    def calculate_unrealized_stock_pnl(
        self, buy_trade: StockTrade, current_price: Decimal
    ) -> PositionPnL:
        """
        Calculate unrealized P/L for an open stock position.

        Args:
            buy_trade: Opening buy trade
            current_price: Current market price

        Returns:
            PositionPnL with unrealized P/L
        """
        # Cost basis includes commission
        cost_per_share = buy_trade.price + (buy_trade.commission / buy_trade.quantity)
        cost_basis = cost_per_share * buy_trade.quantity

        # Current market value
        market_value = current_price * buy_trade.quantity

        # Unrealized P/L
        unrealized_pnl = market_value - cost_basis

        # Return percentage
        return_pct = (unrealized_pnl / cost_basis * 100) if cost_basis != 0 else Decimal("0")

        return PositionPnL(
            symbol=buy_trade.symbol,
            unrealized_pnl=unrealized_pnl.quantize(Decimal("0.01")),
            return_percentage=return_pct.quantize(Decimal("0.01")),
            cost_basis=cost_basis.quantize(Decimal("0.01")),
        )

    def calculate_unrealized_option_pnl(
        self, buy_trade: OptionTrade, current_price: Decimal
    ) -> PositionPnL:
        """
        Calculate unrealized P/L for an open option position.

        Args:
            buy_trade: Opening buy trade
            current_price: Current option price

        Returns:
            PositionPnL with unrealized P/L
        """
        # Cost basis includes premium and commission
        cost_basis = (
            buy_trade.price * buy_trade.quantity * buy_trade.multiplier
            + buy_trade.commission
        )

        # Current market value
        market_value = current_price * buy_trade.quantity * buy_trade.multiplier

        # Unrealized P/L
        unrealized_pnl = market_value - cost_basis

        # Return percentage
        return_pct = (unrealized_pnl / cost_basis * 100) if cost_basis != 0 else Decimal("0")

        return PositionPnL(
            symbol=buy_trade.symbol,
            unrealized_pnl=unrealized_pnl.quantize(Decimal("0.01")),
            return_percentage=return_pct.quantize(Decimal("0.01")),
            cost_basis=cost_basis.quantize(Decimal("0.01")),
        )
