"""SQLAlchemy ORM models for database tables."""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import (
    String,
    Integer,
    Numeric,
    DateTime,
    Date,
    Boolean,
    Text,
    ForeignKey,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class AccountDB(Base):
    """Account table for storing trading accounts."""

    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    broker: Mapped[str] = mapped_column(String(50), nullable=False)
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    api_key: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    api_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    trades: Mapped[List["TradeDB"]] = relationship(
        "TradeDB", back_populates="account", cascade="all, delete-orphan"
    )
    positions: Mapped[List["PositionDB"]] = relationship(
        "PositionDB", back_populates="account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AccountDB(id={self.id}, name='{self.name}', broker='{self.broker}')>"


class TradeDB(Base):
    """Trade table for storing trade transactions."""

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False)
    trade_type: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    commission: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False
    )
    trade_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("accounts.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    strategy: Mapped[Optional[str]] = mapped_column(String(50), default="untagged", nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Option-specific fields
    strike: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 4), nullable=True)
    expiry: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    option_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    multiplier: Mapped[Optional[int]] = mapped_column(Integer, default=100, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    account: Mapped[Optional["AccountDB"]] = relationship(
        "AccountDB", back_populates="trades"
    )

    def __repr__(self) -> str:
        return (
            f"<TradeDB(id={self.id}, symbol='{self.symbol}', "
            f"type='{self.trade_type}', quantity={self.quantity})>"
        )


class PositionDB(Base):
    """Position table for storing current holdings."""

    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    average_price: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    current_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 4), nullable=True
    )
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    account: Mapped["AccountDB"] = relationship("AccountDB", back_populates="positions")

    def __repr__(self) -> str:
        return (
            f"<PositionDB(id={self.id}, symbol='{self.symbol}', "
            f"quantity={self.quantity}, status='{self.status}')>"
        )
