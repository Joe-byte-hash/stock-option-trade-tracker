"""Unit tests for database repository (TDD approach)."""

from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from trade_tracker.database.models import Base
from trade_tracker.database.repository import TradeRepository, AccountRepository, PositionRepository
from trade_tracker.models.trade import StockTrade, OptionTrade, TradeType, AssetType, OptionType
from trade_tracker.models.account import Account, BrokerType
from trade_tracker.models.position import Position, PositionStatus


@pytest.fixture
def db_session():
    """Create a temporary in-memory database session for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        yield session
        session.rollback()


class TestAccountRepository:
    """Test AccountRepository CRUD operations."""

    def test_create_account(self, db_session):
        """Test creating an account through repository."""
        repo = AccountRepository(db_session)

        account = Account(
            name="My IBKR Account",
            broker=BrokerType.IBKR,
            account_number="U1234567",
        )

        created = repo.create(account)
        assert created.id is not None
        assert created.name == "My IBKR Account"
        assert created.broker == BrokerType.IBKR

    def test_get_account_by_id(self, db_session):
        """Test retrieving account by ID."""
        repo = AccountRepository(db_session)

        account = Account(
            name="My Account",
            broker=BrokerType.IBKR,
            account_number="U1234567",
        )

        created = repo.create(account)
        retrieved = repo.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "My Account"

    def test_get_all_accounts(self, db_session):
        """Test retrieving all accounts."""
        repo = AccountRepository(db_session)

        accounts = [
            Account(name="Account 1", broker=BrokerType.IBKR, account_number="U1"),
            Account(name="Account 2", broker=BrokerType.MOOMOO, account_number="M1"),
            Account(name="Account 3", broker=BrokerType.QUESTRADE, account_number="Q1"),
        ]

        for acc in accounts:
            repo.create(acc)

        all_accounts = repo.get_all()
        assert len(all_accounts) == 3
        assert all(isinstance(acc, Account) for acc in all_accounts)

    def test_update_account(self, db_session):
        """Test updating an account."""
        repo = AccountRepository(db_session)

        account = Account(
            name="Original Name",
            broker=BrokerType.IBKR,
            account_number="U1234567",
        )

        created = repo.create(account)
        created.name = "Updated Name"
        created.is_active = False

        updated = repo.update(created)
        assert updated.name == "Updated Name"
        assert updated.is_active is False

    def test_delete_account(self, db_session):
        """Test deleting an account."""
        repo = AccountRepository(db_session)

        account = Account(
            name="To Delete",
            broker=BrokerType.IBKR,
            account_number="U1234567",
        )

        created = repo.create(account)
        account_id = created.id

        repo.delete(account_id)

        deleted = repo.get_by_id(account_id)
        assert deleted is None


class TestTradeRepository:
    """Test TradeRepository CRUD operations."""

    def test_create_stock_trade(self, db_session):
        """Test creating a stock trade through repository."""
        repo = TradeRepository(db_session)

        trade = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY,
            quantity=100,
            price=Decimal("150.50"),
            commission=Decimal("1.00"),
            trade_date=datetime.now(),
        )

        created = repo.create(trade)
        assert created.id is not None
        assert created.symbol == "AAPL"
        assert created.quantity == 100

    def test_create_option_trade(self, db_session):
        """Test creating an option trade through repository."""
        repo = TradeRepository(db_session)

        trade = OptionTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY_TO_OPEN,
            quantity=10,
            price=Decimal("5.50"),
            strike=Decimal("155.00"),
            expiry=date(2024, 3, 15),
            option_type=OptionType.CALL,
            commission=Decimal("6.50"),
            trade_date=datetime.now(),
        )

        created = repo.create(trade)
        assert created.id is not None
        assert created.strike == Decimal("155.00")
        assert created.option_type == OptionType.CALL

    def test_get_trades_by_symbol(self, db_session):
        """Test retrieving trades by symbol."""
        repo = TradeRepository(db_session)

        trades = [
            StockTrade(symbol="AAPL", trade_type=TradeType.BUY, quantity=100,
                      price=Decimal("150"), trade_date=datetime.now()),
            StockTrade(symbol="AAPL", trade_type=TradeType.SELL, quantity=50,
                      price=Decimal("155"), trade_date=datetime.now()),
            StockTrade(symbol="TSLA", trade_type=TradeType.BUY, quantity=10,
                      price=Decimal("200"), trade_date=datetime.now()),
        ]

        for t in trades:
            repo.create(t)

        aapl_trades = repo.get_by_symbol("AAPL")
        assert len(aapl_trades) == 2
        assert all(t.symbol == "AAPL" for t in aapl_trades)

    def test_get_trades_by_date_range(self, db_session):
        """Test retrieving trades within a date range."""
        repo = TradeRepository(db_session)

        now = datetime.now()
        from datetime import timedelta

        trades = [
            StockTrade(symbol="AAPL", trade_type=TradeType.BUY, quantity=100,
                      price=Decimal("150"), trade_date=now - timedelta(days=10)),
            StockTrade(symbol="TSLA", trade_type=TradeType.BUY, quantity=50,
                      price=Decimal("200"), trade_date=now - timedelta(days=5)),
            StockTrade(symbol="MSFT", trade_type=TradeType.BUY, quantity=75,
                      price=Decimal("300"), trade_date=now),
        ]

        for t in trades:
            repo.create(t)

        # Get trades from last 7 days
        start_date = now - timedelta(days=7)
        recent_trades = repo.get_by_date_range(start_date, now)

        assert len(recent_trades) == 2
        assert all(t.trade_date >= start_date for t in recent_trades)

    def test_get_all_trades(self, db_session):
        """Test retrieving all trades."""
        repo = TradeRepository(db_session)

        for i in range(5):
            trade = StockTrade(
                symbol=f"STOCK{i}",
                trade_type=TradeType.BUY,
                quantity=100,
                price=Decimal("100"),
                trade_date=datetime.now(),
            )
            repo.create(trade)

        all_trades = repo.get_all()
        assert len(all_trades) == 5


class TestPositionRepository:
    """Test PositionRepository CRUD operations."""

    def test_create_position(self, db_session):
        """Test creating a position through repository."""
        # Create account first
        account_repo = AccountRepository(db_session)
        account = account_repo.create(
            Account(name="Test", broker=BrokerType.IBKR, account_number="U1")
        )

        position_repo = PositionRepository(db_session)
        position = Position(
            symbol="AAPL",
            asset_type=AssetType.STOCK,
            quantity=100,
            average_price=Decimal("150.00"),
            account_id=account.id,
        )

        created = position_repo.create(position)
        assert created.id is not None
        assert created.symbol == "AAPL"
        assert created.quantity == 100

    def test_get_open_positions(self, db_session):
        """Test retrieving only open positions."""
        account_repo = AccountRepository(db_session)
        account = account_repo.create(
            Account(name="Test", broker=BrokerType.IBKR, account_number="U1")
        )

        position_repo = PositionRepository(db_session)
        positions = [
            Position(symbol="AAPL", asset_type=AssetType.STOCK, quantity=100,
                    average_price=Decimal("150"), account_id=account.id,
                    status=PositionStatus.OPEN),
            Position(symbol="TSLA", asset_type=AssetType.STOCK, quantity=50,
                    average_price=Decimal("200"), account_id=account.id,
                    status=PositionStatus.CLOSED),
            Position(symbol="MSFT", asset_type=AssetType.STOCK, quantity=75,
                    average_price=Decimal("300"), account_id=account.id,
                    status=PositionStatus.OPEN),
        ]

        for p in positions:
            position_repo.create(p)

        open_positions = position_repo.get_open_positions()
        assert len(open_positions) == 2
        assert all(p.status == PositionStatus.OPEN for p in open_positions)

    def test_get_position_by_symbol(self, db_session):
        """Test retrieving position by symbol."""
        account_repo = AccountRepository(db_session)
        account = account_repo.create(
            Account(name="Test", broker=BrokerType.IBKR, account_number="U1")
        )

        position_repo = PositionRepository(db_session)
        position = Position(
            symbol="AAPL",
            asset_type=AssetType.STOCK,
            quantity=100,
            average_price=Decimal("150.00"),
            account_id=account.id,
        )

        position_repo.create(position)

        retrieved = position_repo.get_by_symbol("AAPL")
        assert retrieved is not None
        assert retrieved.symbol == "AAPL"

    def test_update_position_price(self, db_session):
        """Test updating position current price."""
        account_repo = AccountRepository(db_session)
        account = account_repo.create(
            Account(name="Test", broker=BrokerType.IBKR, account_number="U1")
        )

        position_repo = PositionRepository(db_session)
        position = Position(
            symbol="AAPL",
            asset_type=AssetType.STOCK,
            quantity=100,
            average_price=Decimal("150.00"),
            current_price=Decimal("150.00"),
            account_id=account.id,
        )

        created = position_repo.create(position)
        created.current_price = Decimal("160.00")

        updated = position_repo.update(created)
        assert updated.current_price == Decimal("160.00")
