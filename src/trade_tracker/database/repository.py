"""Repository pattern for database operations."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from trade_tracker.database.models import AccountDB, TradeDB, PositionDB
from trade_tracker.models.account import Account
from trade_tracker.models.trade import Trade, StockTrade, OptionTrade, AssetType
from trade_tracker.models.position import Position, PositionStatus


class AccountRepository:
    """Repository for Account CRUD operations."""

    def __init__(self, session: Session):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def create(self, account: Account) -> Account:
        """
        Create a new account.

        Args:
            account: Account model to create

        Returns:
            Created account with ID
        """
        db_account = AccountDB(
            name=account.name,
            broker=account.broker.value,
            account_number=account.account_number,
            is_active=account.is_active,
            api_key=account.api_key,
            api_secret=account.api_secret,
        )

        self.session.add(db_account)
        self.session.commit()
        self.session.refresh(db_account)

        return self._to_model(db_account)

    def get_by_id(self, account_id: int) -> Optional[Account]:
        """
        Get account by ID.

        Args:
            account_id: Account ID

        Returns:
            Account if found, None otherwise
        """
        db_account = self.session.get(AccountDB, account_id)
        if db_account:
            return self._to_model(db_account)
        return None

    def get_all(self) -> List[Account]:
        """
        Get all accounts.

        Returns:
            List of all accounts
        """
        db_accounts = self.session.execute(select(AccountDB)).scalars().all()
        return [self._to_model(acc) for acc in db_accounts]

    def get_active(self) -> List[Account]:
        """
        Get all active accounts.

        Returns:
            List of active accounts
        """
        db_accounts = self.session.execute(
            select(AccountDB).where(AccountDB.is_active == True)
        ).scalars().all()
        return [self._to_model(acc) for acc in db_accounts]

    def update(self, account: Account) -> Account:
        """
        Update an existing account.

        Args:
            account: Account model with updated data

        Returns:
            Updated account
        """
        db_account = self.session.get(AccountDB, account.id)
        if not db_account:
            raise ValueError(f"Account with ID {account.id} not found")

        db_account.name = account.name
        db_account.broker = account.broker.value
        db_account.account_number = account.account_number
        db_account.is_active = account.is_active
        db_account.api_key = account.api_key
        db_account.api_secret = account.api_secret

        self.session.commit()
        self.session.refresh(db_account)

        return self._to_model(db_account)

    def delete(self, account_id: int) -> None:
        """
        Delete an account.

        Args:
            account_id: Account ID to delete
        """
        db_account = self.session.get(AccountDB, account_id)
        if db_account:
            self.session.delete(db_account)
            self.session.commit()

    @staticmethod
    def _to_model(db_account: AccountDB) -> Account:
        """Convert database model to Pydantic model."""
        return Account(
            id=db_account.id,
            name=db_account.name,
            broker=db_account.broker,
            account_number=db_account.account_number,
            is_active=db_account.is_active,
            api_key=db_account.api_key,
            api_secret=db_account.api_secret,
            created_at=db_account.created_at,
            updated_at=db_account.updated_at,
        )


class TradeRepository:
    """Repository for Trade CRUD operations."""

    def __init__(self, session: Session):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def create(self, trade: Trade) -> Trade:
        """
        Create a new trade.

        Args:
            trade: Trade model to create

        Returns:
            Created trade with ID
        """
        # Common fields
        db_trade = TradeDB(
            symbol=trade.symbol,
            asset_type=trade.asset_type.value,
            trade_type=trade.trade_type.value,
            quantity=trade.quantity,
            price=trade.price,
            commission=trade.commission,
            trade_date=trade.trade_date,
            account_id=trade.account_id,
            status=trade.status.value,
            notes=trade.notes,
        )

        # Option-specific fields
        if isinstance(trade, OptionTrade):
            db_trade.strike = trade.strike
            db_trade.expiry = trade.expiry
            db_trade.option_type = trade.option_type.value
            db_trade.multiplier = trade.multiplier

        self.session.add(db_trade)
        self.session.commit()
        self.session.refresh(db_trade)

        return self._to_model(db_trade)

    def get_by_id(self, trade_id: int) -> Optional[Trade]:
        """
        Get trade by ID.

        Args:
            trade_id: Trade ID

        Returns:
            Trade if found, None otherwise
        """
        db_trade = self.session.get(TradeDB, trade_id)
        if db_trade:
            return self._to_model(db_trade)
        return None

    def get_all(self) -> List[Trade]:
        """
        Get all trades.

        Returns:
            List of all trades
        """
        db_trades = self.session.execute(select(TradeDB)).scalars().all()
        return [self._to_model(t) for t in db_trades]

    def get_by_symbol(self, symbol: str) -> List[Trade]:
        """
        Get all trades for a specific symbol.

        Args:
            symbol: Stock/option symbol

        Returns:
            List of trades for the symbol
        """
        db_trades = self.session.execute(
            select(TradeDB).where(TradeDB.symbol == symbol)
        ).scalars().all()
        return [self._to_model(t) for t in db_trades]

    def get_by_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> List[Trade]:
        """
        Get trades within a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of trades within the date range
        """
        db_trades = self.session.execute(
            select(TradeDB).where(
                TradeDB.trade_date >= start_date,
                TradeDB.trade_date <= end_date
            )
        ).scalars().all()
        return [self._to_model(t) for t in db_trades]

    def get_by_account(self, account_id: int) -> List[Trade]:
        """
        Get all trades for a specific account.

        Args:
            account_id: Account ID

        Returns:
            List of trades for the account
        """
        db_trades = self.session.execute(
            select(TradeDB).where(TradeDB.account_id == account_id)
        ).scalars().all()
        return [self._to_model(t) for t in db_trades]

    def update(self, trade: Trade) -> Trade:
        """
        Update an existing trade.

        Args:
            trade: Trade model with updated data

        Returns:
            Updated trade
        """
        db_trade = self.session.get(TradeDB, trade.id)
        if not db_trade:
            raise ValueError(f"Trade with ID {trade.id} not found")

        # Update common fields
        db_trade.symbol = trade.symbol
        db_trade.asset_type = trade.asset_type.value
        db_trade.trade_type = trade.trade_type.value
        db_trade.quantity = trade.quantity
        db_trade.price = trade.price
        db_trade.commission = trade.commission
        db_trade.trade_date = trade.trade_date
        db_trade.account_id = trade.account_id
        db_trade.status = trade.status.value
        db_trade.notes = trade.notes

        # Update option fields if applicable
        if isinstance(trade, OptionTrade):
            db_trade.strike = trade.strike
            db_trade.expiry = trade.expiry
            db_trade.option_type = trade.option_type.value
            db_trade.multiplier = trade.multiplier

        self.session.commit()
        self.session.refresh(db_trade)

        return self._to_model(db_trade)

    def delete(self, trade_id: int) -> None:
        """
        Delete a trade.

        Args:
            trade_id: Trade ID to delete
        """
        db_trade = self.session.get(TradeDB, trade_id)
        if db_trade:
            self.session.delete(db_trade)
            self.session.commit()

    @staticmethod
    def _to_model(db_trade: TradeDB) -> Trade:
        """Convert database model to Pydantic model."""
        if db_trade.asset_type == AssetType.OPTION.value:
            return OptionTrade(
                id=db_trade.id,
                symbol=db_trade.symbol,
                trade_type=db_trade.trade_type,
                quantity=db_trade.quantity,
                price=db_trade.price,
                commission=db_trade.commission,
                trade_date=db_trade.trade_date,
                account_id=db_trade.account_id,
                status=db_trade.status,
                notes=db_trade.notes,
                strike=db_trade.strike,
                expiry=db_trade.expiry,
                option_type=db_trade.option_type,
                multiplier=db_trade.multiplier,
                created_at=db_trade.created_at,
                updated_at=db_trade.updated_at,
            )
        else:
            return StockTrade(
                id=db_trade.id,
                symbol=db_trade.symbol,
                trade_type=db_trade.trade_type,
                quantity=db_trade.quantity,
                price=db_trade.price,
                commission=db_trade.commission,
                trade_date=db_trade.trade_date,
                account_id=db_trade.account_id,
                status=db_trade.status,
                notes=db_trade.notes,
                created_at=db_trade.created_at,
                updated_at=db_trade.updated_at,
            )


class PositionRepository:
    """Repository for Position CRUD operations."""

    def __init__(self, session: Session):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy session
        """
        self.session = session

    def create(self, position: Position) -> Position:
        """
        Create a new position.

        Args:
            position: Position model to create

        Returns:
            Created position with ID
        """
        db_position = PositionDB(
            symbol=position.symbol,
            asset_type=position.asset_type.value,
            quantity=position.quantity,
            average_price=position.average_price,
            current_price=position.current_price,
            account_id=position.account_id,
            status=position.status.value,
            opened_at=position.opened_at,
            closed_at=position.closed_at,
        )

        self.session.add(db_position)
        self.session.commit()
        self.session.refresh(db_position)

        return self._to_model(db_position)

    def get_by_id(self, position_id: int) -> Optional[Position]:
        """
        Get position by ID.

        Args:
            position_id: Position ID

        Returns:
            Position if found, None otherwise
        """
        db_position = self.session.get(PositionDB, position_id)
        if db_position:
            return self._to_model(db_position)
        return None

    def get_by_symbol(self, symbol: str) -> Optional[Position]:
        """
        Get position by symbol.

        Args:
            symbol: Stock/option symbol

        Returns:
            Position if found, None otherwise
        """
        db_position = self.session.execute(
            select(PositionDB).where(
                PositionDB.symbol == symbol,
                PositionDB.status == PositionStatus.OPEN.value
            )
        ).scalar_one_or_none()

        if db_position:
            return self._to_model(db_position)
        return None

    def get_all(self) -> List[Position]:
        """
        Get all positions.

        Returns:
            List of all positions
        """
        db_positions = self.session.execute(select(PositionDB)).scalars().all()
        return [self._to_model(p) for p in db_positions]

    def get_open_positions(self) -> List[Position]:
        """
        Get all open positions.

        Returns:
            List of open positions
        """
        db_positions = self.session.execute(
            select(PositionDB).where(PositionDB.status == PositionStatus.OPEN.value)
        ).scalars().all()
        return [self._to_model(p) for p in db_positions]

    def get_by_account(self, account_id: int) -> List[Position]:
        """
        Get all positions for a specific account.

        Args:
            account_id: Account ID

        Returns:
            List of positions for the account
        """
        db_positions = self.session.execute(
            select(PositionDB).where(PositionDB.account_id == account_id)
        ).scalars().all()
        return [self._to_model(p) for p in db_positions]

    def update(self, position: Position) -> Position:
        """
        Update an existing position.

        Args:
            position: Position model with updated data

        Returns:
            Updated position
        """
        db_position = self.session.get(PositionDB, position.id)
        if not db_position:
            raise ValueError(f"Position with ID {position.id} not found")

        db_position.symbol = position.symbol
        db_position.asset_type = position.asset_type.value
        db_position.quantity = position.quantity
        db_position.average_price = position.average_price
        db_position.current_price = position.current_price
        db_position.account_id = position.account_id
        db_position.status = position.status.value
        db_position.opened_at = position.opened_at
        db_position.closed_at = position.closed_at

        self.session.commit()
        self.session.refresh(db_position)

        return self._to_model(db_position)

    def delete(self, position_id: int) -> None:
        """
        Delete a position.

        Args:
            position_id: Position ID to delete
        """
        db_position = self.session.get(PositionDB, position_id)
        if db_position:
            self.session.delete(db_position)
            self.session.commit()

    @staticmethod
    def _to_model(db_position: PositionDB) -> Position:
        """Convert database model to Pydantic model."""
        return Position(
            id=db_position.id,
            symbol=db_position.symbol,
            asset_type=db_position.asset_type,
            quantity=db_position.quantity,
            average_price=db_position.average_price,
            current_price=db_position.current_price,
            account_id=db_position.account_id,
            status=db_position.status,
            opened_at=db_position.opened_at,
            closed_at=db_position.closed_at,
            created_at=db_position.created_at,
            updated_at=db_position.updated_at,
        )
