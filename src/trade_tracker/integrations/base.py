"""Base broker integration interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional

from trade_tracker.models.trade import Trade
from trade_tracker.models.position import Position


class BaseBroker(ABC):
    """
    Abstract base class for broker integrations.

    All broker integrations must implement this interface.
    All operations are read-only - no order placement supported.
    """

    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize broker integration.

        Args:
            credentials: Broker-specific credentials (encrypted)
        """
        self.credentials = credentials
        self._connected = False

    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to broker.

        Returns:
            True if connection successful

        Raises:
            BrokerConnectionError: If connection fails
            BrokerAuthenticationError: If authentication fails
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from broker."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if currently connected to broker.

        Returns:
            True if connected
        """
        pass

    @abstractmethod
    def fetch_trades(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        symbol: Optional[str] = None
    ) -> List[Trade]:
        """
        Fetch executed trades from broker.

        Args:
            start_date: Filter trades from this date (inclusive)
            end_date: Filter trades to this date (inclusive)
            symbol: Filter trades for specific symbol

        Returns:
            List of Trade objects (StockTrade or OptionTrade)

        Raises:
            BrokerConnectionError: If not connected
            BrokerDataError: If data cannot be parsed
        """
        pass

    @abstractmethod
    def fetch_positions(self) -> List[Position]:
        """
        Fetch current open positions from broker.

        Returns:
            List of Position objects

        Raises:
            BrokerConnectionError: If not connected
            BrokerDataError: If data cannot be parsed
        """
        pass

    @abstractmethod
    def fetch_account_info(self) -> Dict[str, Any]:
        """
        Fetch account information.

        Returns:
            Dictionary with account details (balance, buying power, etc.)

        Raises:
            BrokerConnectionError: If not connected
        """
        pass

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
