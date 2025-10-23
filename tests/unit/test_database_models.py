"""Unit tests for database models and ORM (TDD approach)."""

import tempfile
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from trade_tracker.database.models import Base, TradeDB, AccountDB, PositionDB
from trade_tracker.models.trade import TradeType, AssetType, TradeStatus, OptionType
from trade_tracker.models.account import BrokerType
from trade_tracker.models.position import PositionStatus


@pytest.fixture
def db_session():
    """Create a temporary in-memory database session for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session
        session.rollback()


class TestAccountDB:
    """Test AccountDB ORM model."""

    def test_create_account(self, db_session):
        """Test creating and persisting an account."""
        account = AccountDB(
            name="Test IBKR Account",
            broker=BrokerType.IBKR.value,
            account_number="U1234567",
            is_active=True,
        )

        db_session.add(account)
        db_session.commit()

        # Query back
        result = db_session.execute(select(AccountDB)).scalar_one()
        assert result.name == "Test IBKR Account"
        assert result.broker == "ibkr"
        assert result.account_number == "U1234567"
        assert result.is_active is True
        assert result.id is not None
        assert result.created_at is not None

    def test_account_relationships(self, db_session):
        """Test account relationships with trades and positions."""
        account = AccountDB(
            name="Test Account",
            broker=BrokerType.IBKR.value,
            account_number="U1234567",
        )
        db_session.add(account)
        db_session.flush()

        # Add trades
        trade = TradeDB(
            symbol="AAPL",
            asset_type=AssetType.STOCK.value,
            trade_type=TradeType.BUY.value,
            quantity=100,
            price=Decimal("150.50"),
            trade_date=datetime.now(),
            account_id=account.id,
        )
        db_session.add(trade)
        db_session.commit()

        # Check relationship
        assert len(account.trades) == 1
        assert account.trades[0].symbol == "AAPL"


class TestTradeDB:
    """Test TradeDB ORM model."""

    def test_create_stock_trade(self, db_session):
        """Test creating and persisting a stock trade."""
        trade = TradeDB(
            symbol="AAPL",
            asset_type=AssetType.STOCK.value,
            trade_type=TradeType.BUY.value,
            quantity=100,
            price=Decimal("150.50"),
            commission=Decimal("1.00"),
            trade_date=datetime.now(),
            status=TradeStatus.OPEN.value,
        )

        db_session.add(trade)
        db_session.commit()

        # Query back
        result = db_session.execute(select(TradeDB)).scalar_one()
        assert result.symbol == "AAPL"
        assert result.asset_type == "stock"
        assert result.quantity == 100
        assert result.price == Decimal("150.50")
        assert result.id is not None

    def test_create_option_trade(self, db_session):
        """Test creating and persisting an option trade."""
        trade = TradeDB(
            symbol="AAPL",
            asset_type=AssetType.OPTION.value,
            trade_type=TradeType.BUY_TO_OPEN.value,
            quantity=10,
            price=Decimal("5.50"),
            commission=Decimal("6.50"),
            trade_date=datetime.now(),
            strike=Decimal("155.00"),
            expiry=date(2024, 3, 15),
            option_type=OptionType.CALL.value,
            multiplier=100,
        )

        db_session.add(trade)
        db_session.commit()

        # Query back
        result = db_session.execute(select(TradeDB)).scalar_one()
        assert result.symbol == "AAPL"
        assert result.asset_type == "option"
        assert result.strike == Decimal("155.00")
        assert result.option_type == "call"

    def test_trade_with_notes(self, db_session):
        """Test trade with notes field."""
        trade = TradeDB(
            symbol="AAPL",
            asset_type=AssetType.STOCK.value,
            trade_type=TradeType.BUY.value,
            quantity=100,
            price=Decimal("150.50"),
            trade_date=datetime.now(),
            notes="Buying the dip on strong earnings",
        )

        db_session.add(trade)
        db_session.commit()

        result = db_session.execute(select(TradeDB)).scalar_one()
        assert result.notes == "Buying the dip on strong earnings"

    def test_query_trades_by_symbol(self, db_session):
        """Test querying trades by symbol."""
        trades = [
            TradeDB(symbol="AAPL", asset_type="stock", trade_type="buy",
                   quantity=100, price=Decimal("150"), trade_date=datetime.now()),
            TradeDB(symbol="AAPL", asset_type="stock", trade_type="sell",
                   quantity=50, price=Decimal("155"), trade_date=datetime.now()),
            TradeDB(symbol="TSLA", asset_type="stock", trade_type="buy",
                   quantity=10, price=Decimal("200"), trade_date=datetime.now()),
        ]

        for trade in trades:
            db_session.add(trade)
        db_session.commit()

        # Query AAPL trades
        aapl_trades = db_session.execute(
            select(TradeDB).where(TradeDB.symbol == "AAPL")
        ).scalars().all()

        assert len(aapl_trades) == 2
        assert all(t.symbol == "AAPL" for t in aapl_trades)


class TestPositionDB:
    """Test PositionDB ORM model."""

    def test_create_position(self, db_session):
        """Test creating and persisting a position."""
        # Create account first
        account = AccountDB(
            name="Test Account",
            broker=BrokerType.IBKR.value,
            account_number="U1234567",
        )
        db_session.add(account)
        db_session.flush()

        position = PositionDB(
            symbol="AAPL",
            asset_type=AssetType.STOCK.value,
            quantity=100,
            average_price=Decimal("150.00"),
            current_price=Decimal("160.00"),
            account_id=account.id,
            status=PositionStatus.OPEN.value,
        )

        db_session.add(position)
        db_session.commit()

        # Query back
        result = db_session.execute(select(PositionDB)).scalar_one()
        assert result.symbol == "AAPL"
        assert result.quantity == 100
        assert result.average_price == Decimal("150.00")
        assert result.current_price == Decimal("160.00")

    def test_position_relationships(self, db_session):
        """Test position relationship with account."""
        account = AccountDB(
            name="Test Account",
            broker=BrokerType.IBKR.value,
            account_number="U1234567",
        )
        db_session.add(account)
        db_session.flush()

        position = PositionDB(
            symbol="AAPL",
            asset_type=AssetType.STOCK.value,
            quantity=100,
            average_price=Decimal("150.00"),
            account_id=account.id,
        )
        db_session.add(position)
        db_session.commit()

        # Check relationship
        assert len(account.positions) == 1
        assert account.positions[0].symbol == "AAPL"
        assert position.account.name == "Test Account"

    def test_query_open_positions(self, db_session):
        """Test querying only open positions."""
        account = AccountDB(
            name="Test Account",
            broker=BrokerType.IBKR.value,
            account_number="U1234567",
        )
        db_session.add(account)
        db_session.flush()

        positions = [
            PositionDB(symbol="AAPL", asset_type="stock", quantity=100,
                      average_price=Decimal("150"), account_id=account.id,
                      status=PositionStatus.OPEN.value),
            PositionDB(symbol="TSLA", asset_type="stock", quantity=50,
                      average_price=Decimal("200"), account_id=account.id,
                      status=PositionStatus.CLOSED.value),
            PositionDB(symbol="MSFT", asset_type="stock", quantity=75,
                      average_price=Decimal("300"), account_id=account.id,
                      status=PositionStatus.OPEN.value),
        ]

        for pos in positions:
            db_session.add(pos)
        db_session.commit()

        # Query open positions
        open_positions = db_session.execute(
            select(PositionDB).where(PositionDB.status == PositionStatus.OPEN.value)
        ).scalars().all()

        assert len(open_positions) == 2
        assert all(p.status == "open" for p in open_positions)
