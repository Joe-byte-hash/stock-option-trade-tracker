"""Integration manager for orchestrating broker imports."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from decimal import Decimal

from trade_tracker.database.connection import DatabaseManager
from trade_tracker.database.repository import TradeRepository, PositionRepository
from trade_tracker.integrations.base import BaseBroker
from trade_tracker.integrations.exceptions import (
    BrokerConnectionError,
    BrokerIntegrationError,
)
from trade_tracker.models.trade import Trade
from trade_tracker.models.position import Position


class IntegrationManager:
    """
    Manages broker integrations and imports.

    Handles:
    - Trade imports from brokers
    - Position synchronization
    - Duplicate detection
    - Import history tracking
    """

    def __init__(self, db_path: str = "data/trades.db"):
        """
        Initialize integration manager.

        Args:
            db_path: Path to SQLite database
        """
        self.db = DatabaseManager(db_path)
        self.db.create_tables()  # Ensure database tables are created
        self._import_history_file = Path(db_path).parent / "import_history.json"
        self._import_history_file.parent.mkdir(parents=True, exist_ok=True)

    def import_trades(
        self,
        broker: BaseBroker,
        account_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        symbol: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Import trades from broker.

        Args:
            broker: Broker instance to import from
            account_id: Account ID to assign to trades
            start_date: Optional start date filter
            end_date: Optional end date filter
            symbol: Optional symbol filter

        Returns:
            Dictionary with import results:
            {
                'success': bool,
                'imported_count': int,
                'duplicate_count': int,
                'error_count': int,
                'error': str (if success=False)
            }

        Raises:
            BrokerConnectionError: If broker is not connected
        """
        if not broker.is_connected():
            raise BrokerConnectionError("Broker is not connected")

        result = {
            'success': False,
            'imported_count': 0,
            'duplicate_count': 0,
            'error_count': 0,
        }

        try:
            # Fetch trades from broker
            try:
                trades = broker.fetch_trades(
                    start_date=start_date,
                    end_date=end_date,
                    symbol=symbol
                )
            except (BrokerConnectionError, BrokerIntegrationError) as e:
                result['success'] = False
                result['error'] = str(e)
                return result

            # Import trades to database
            with self.db.get_session() as session:
                trade_repo = TradeRepository(session)

                for trade in trades:
                    if trade is None:
                        result['error_count'] += 1
                        continue

                    # Set account_id
                    trade.account_id = account_id

                    # Check for duplicates
                    if self._is_duplicate_trade(trade, trade_repo):
                        result['duplicate_count'] += 1
                        continue

                    # Import trade
                    try:
                        trade_repo.create(trade)
                        result['imported_count'] += 1
                    except Exception as e:
                        result['error_count'] += 1
                        print(f"Error importing trade {trade.symbol}: {str(e)}")

                session.commit()

            result['success'] = True

            # Log import
            self._log_import(
                broker_name=broker.__class__.__name__,
                account_id=account_id,
                imported_count=result['imported_count'],
                duplicate_count=result['duplicate_count'],
                error_count=result['error_count']
            )

            return result

        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            return result

    def sync_positions(
        self,
        broker: BaseBroker,
        account_id: int
    ) -> Dict[str, Any]:
        """
        Synchronize positions from broker.

        Args:
            broker: Broker instance
            account_id: Account ID

        Returns:
            Dictionary with sync results:
            {
                'success': bool,
                'synced_count': int,
                'error': str (if success=False)
            }

        Raises:
            BrokerConnectionError: If broker is not connected
        """
        if not broker.is_connected():
            raise BrokerConnectionError("Broker is not connected")

        result = {
            'success': False,
            'synced_count': 0,
        }

        try:
            # Fetch positions from broker
            positions = broker.fetch_positions()

            # Sync to database
            with self.db.get_session() as session:
                position_repo = PositionRepository(session)

                for position in positions:
                    position.account_id = account_id

                    # Check if position exists
                    existing = position_repo.get_by_symbol(
                        symbol=position.symbol,
                        account_id=account_id
                    )

                    if existing:
                        # Update existing position
                        position.id = existing.id
                        position_repo.update(position)
                    else:
                        # Create new position
                        position_repo.create(position)

                    result['synced_count'] += 1

                session.commit()

            result['success'] = True
            return result

        except BrokerConnectionError:
            raise
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            return result

    def _is_duplicate_trade(
        self,
        trade: Trade,
        trade_repo: TradeRepository
    ) -> bool:
        """
        Check if trade is a duplicate.

        A trade is considered duplicate if there exists a trade with:
        - Same symbol
        - Same trade date (within same minute)
        - Same price
        - Same quantity
        - Same trade type

        Args:
            trade: Trade to check
            trade_repo: Trade repository

        Returns:
            True if duplicate exists
        """
        # Get trades for same symbol around same time
        from datetime import timedelta

        start_date = trade.trade_date - timedelta(minutes=1)
        end_date = trade.trade_date + timedelta(minutes=1)

        existing_trades = trade_repo.get_by_date_range(
            start_date=start_date,
            end_date=end_date
        )

        # Check for exact match
        for existing in existing_trades:
            if (existing.symbol == trade.symbol and
                existing.trade_type == trade.trade_type and
                abs(existing.price - trade.price) < Decimal('0.01') and
                existing.quantity == trade.quantity):
                return True

        return False

    def _log_import(
        self,
        broker_name: str,
        account_id: int,
        imported_count: int,
        duplicate_count: int,
        error_count: int
    ) -> None:
        """
        Log import to history file.

        Args:
            broker_name: Name of broker
            account_id: Account ID
            imported_count: Number of trades imported
            duplicate_count: Number of duplicates skipped
            error_count: Number of errors
        """
        import_record = {
            'timestamp': datetime.now().isoformat(),
            'broker': broker_name,
            'account_id': account_id,
            'imported_count': imported_count,
            'duplicate_count': duplicate_count,
            'error_count': error_count
        }

        # Load existing history
        history = []
        if self._import_history_file.exists():
            try:
                with open(self._import_history_file, 'r') as f:
                    history = json.load(f)
            except:
                history = []

        # Add new record
        history.insert(0, import_record)  # Newest first

        # Keep only last 100 imports
        history = history[:100]

        # Save history
        with open(self._import_history_file, 'w') as f:
            json.dump(history, f, indent=2)

    def get_import_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent import history.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of import records (newest first)
        """
        if not self._import_history_file.exists():
            return []

        try:
            with open(self._import_history_file, 'r') as f:
                history = json.load(f)
                return history[:limit]
        except:
            return []

    def get_total_trades_imported(self, broker_name: Optional[str] = None) -> int:
        """
        Get total number of trades imported.

        Args:
            broker_name: Optional broker name filter

        Returns:
            Total count of imported trades
        """
        history = self.get_import_history(limit=100)

        total = 0
        for record in history:
            if broker_name is None or record['broker'] == broker_name:
                total += record.get('imported_count', 0)

        return total
