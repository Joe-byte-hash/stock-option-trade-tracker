"""Account data models."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class BrokerType(str, Enum):
    """Broker type enumeration."""

    IBKR = "ibkr"
    MOOMOO = "moomoo"
    QUESTRADE = "questrade"
    MANUAL = "manual"


class Account(BaseModel):
    """Trading account model."""

    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    broker: BrokerType
    account_number: str = Field(..., min_length=1, max_length=50)
    is_active: bool = Field(default=True)
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True, use_enum_values=False)
