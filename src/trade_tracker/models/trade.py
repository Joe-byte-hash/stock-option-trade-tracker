"""Trade data models."""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, computed_field, ConfigDict


class AssetType(str, Enum):
    """Asset type enumeration."""

    STOCK = "stock"
    OPTION = "option"


class TradeType(str, Enum):
    """Trade type enumeration."""

    BUY = "buy"
    SELL = "sell"
    BUY_TO_OPEN = "buy_to_open"
    SELL_TO_CLOSE = "sell_to_close"
    BUY_TO_CLOSE = "buy_to_close"
    SELL_TO_OPEN = "sell_to_open"


class TradeStatus(str, Enum):
    """Trade status enumeration."""

    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class OptionType(str, Enum):
    """Option type enumeration."""

    CALL = "call"
    PUT = "put"


class TradingStrategy(str, Enum):
    """Trading strategy enumeration."""

    # Stock strategies
    DAY_TRADE = "day_trade"
    SWING_TRADE = "swing_trade"
    POSITION_TRADE = "position_trade"
    SCALPING = "scalping"
    MOMENTUM = "momentum"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"

    # Option strategies
    COVERED_CALL = "covered_call"
    CASH_SECURED_PUT = "cash_secured_put"
    PROTECTIVE_PUT = "protective_put"
    COLLAR = "collar"
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    BULL_CALL_SPREAD = "bull_call_spread"
    BEAR_PUT_SPREAD = "bear_put_spread"
    IRON_CONDOR = "iron_condor"
    BUTTERFLY = "butterfly"
    STRADDLE = "straddle"
    STRANGLE = "strangle"
    CALENDAR_SPREAD = "calendar_spread"

    # General
    OTHER = "other"
    UNTAGGED = "untagged"


class Trade(BaseModel):
    """Base trade model."""

    id: Optional[int] = None
    symbol: str = Field(..., min_length=1, max_length=10)
    asset_type: AssetType
    trade_type: TradeType
    quantity: int = Field(..., gt=0)
    price: Decimal = Field(..., ge=0)
    commission: Decimal = Field(default=Decimal("0"), ge=0)
    trade_date: datetime
    account_id: Optional[int] = None
    status: TradeStatus = TradeStatus.OPEN
    strategy: Optional[TradingStrategy] = TradingStrategy.UNTAGGED
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("price", "commission", mode="before")
    @classmethod
    def convert_to_decimal(cls, v):
        """Convert numeric values to Decimal."""
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v

    @computed_field
    @property
    def total_cost(self) -> Decimal:
        """Calculate total cost of the trade (to be overridden by subclasses)."""
        raise NotImplementedError("Subclasses must implement total_cost")

    model_config = ConfigDict(from_attributes=True, use_enum_values=False)


class StockTrade(Trade):
    """Stock trade model."""

    asset_type: AssetType = Field(default=AssetType.STOCK, frozen=True)

    @computed_field
    @property
    def total_cost(self) -> Decimal:
        """
        Calculate total cost for stock trade.

        For buy orders: cost = quantity * price + commission
        For sell orders: proceeds = quantity * price - commission
        """
        base_cost = Decimal(str(self.quantity)) * self.price

        if self.trade_type in [TradeType.BUY]:
            return base_cost + self.commission
        else:  # SELL
            return base_cost - self.commission


class OptionTrade(Trade):
    """Option trade model."""

    asset_type: AssetType = Field(default=AssetType.OPTION, frozen=True)
    strike: Decimal = Field(..., gt=0)
    expiry: date
    option_type: OptionType
    multiplier: int = Field(default=100, gt=0)

    @field_validator("strike", mode="before")
    @classmethod
    def convert_strike_to_decimal(cls, v):
        """Convert strike to Decimal."""
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v

    @computed_field
    @property
    def total_cost(self) -> Decimal:
        """
        Calculate total cost for option trade.

        For options: cost = quantity * price * multiplier + commission
        Standard multiplier is 100 for equity options.
        """
        base_cost = Decimal(str(self.quantity)) * self.price * Decimal(str(self.multiplier))

        if self.trade_type in [TradeType.BUY_TO_OPEN, TradeType.BUY_TO_CLOSE]:
            return base_cost + self.commission
        else:  # SELL_TO_OPEN, SELL_TO_CLOSE
            return base_cost - self.commission
