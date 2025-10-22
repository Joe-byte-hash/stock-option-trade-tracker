"""Position data models."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, computed_field, ConfigDict

from trade_tracker.models.trade import AssetType


class PositionStatus(str, Enum):
    """Position status enumeration."""

    OPEN = "open"
    CLOSED = "closed"


class Position(BaseModel):
    """Position model representing current holdings."""

    id: Optional[int] = None
    symbol: str = Field(..., min_length=1, max_length=10)
    asset_type: AssetType
    quantity: int  # Can be negative for short positions
    average_price: Decimal = Field(..., ge=0)
    current_price: Optional[Decimal] = Field(default=None, ge=0)
    account_id: int
    status: PositionStatus = PositionStatus.OPEN
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @field_validator("average_price", "current_price", mode="before")
    @classmethod
    def convert_to_decimal(cls, v):
        """Convert numeric values to Decimal."""
        if v is None:
            return v
        if isinstance(v, (int, float, str)):
            return Decimal(str(v))
        return v

    @computed_field
    @property
    def is_short(self) -> bool:
        """Check if position is short (negative quantity)."""
        return self.quantity < 0

    @computed_field
    @property
    def unrealized_pnl(self) -> Optional[Decimal]:
        """
        Calculate unrealized P/L for open position.

        Returns None if current_price is not set.
        For long positions: (current_price - average_price) * quantity
        For short positions: (average_price - current_price) * abs(quantity)
        """
        if self.current_price is None or self.status != PositionStatus.OPEN:
            return None

        if self.is_short:
            # Short position: profit when price goes down
            return (self.average_price - self.current_price) * abs(self.quantity)
        else:
            # Long position: profit when price goes up
            return (self.current_price - self.average_price) * self.quantity

    @computed_field
    @property
    def market_value(self) -> Optional[Decimal]:
        """Calculate current market value of position."""
        if self.current_price is None:
            return None
        return self.current_price * abs(self.quantity)

    model_config = ConfigDict(from_attributes=True, use_enum_values=False)
