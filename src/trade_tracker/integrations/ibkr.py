"""Interactive Brokers (IBKR) integration."""

import threading
import time
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional

try:
    from ibapi.client import EClient
    from ibapi.wrapper import EWrapper
    from ibapi.contract import Contract
    from ibapi.execution import ExecutionFilter
    IBAPI_AVAILABLE = True
except ImportError:
    # ibapi not installed - create mock base classes for testing
    IBAPI_AVAILABLE = False

    class EClient:
        """Mock EClient for when ibapi is not installed."""
        def __init__(self, wrapper):
            pass

        def connect(self, host, port, client_id):
            pass

        def disconnect(self):
            pass

        def run(self):
            pass

        def isConnected(self):
            return False

        def reqExecutions(self, req_id, exec_filter):
            pass

        def reqPositions(self):
            pass

        def reqAccountUpdates(self, subscribe, account):
            pass

    class EWrapper:
        """Mock EWrapper for when ibapi is not installed."""
        def nextValidId(self, orderId):
            pass

        def error(self, reqId, errorCode, errorString):
            pass

        def execDetails(self, reqId, contract, execution):
            pass

        def commissionReport(self, commissionReport):
            pass

        def execDetailsEnd(self, reqId):
            pass

        def position(self, account, contract, position, avgCost):
            pass

        def positionEnd(self):
            pass

        def updateAccountValue(self, key, val, currency, accountName):
            pass

        def accountDownloadEnd(self, accountName):
            pass

    class Contract:
        """Mock Contract for when ibapi is not installed."""
        pass

    class ExecutionFilter:
        """Mock ExecutionFilter for when ibapi is not installed."""
        pass

from trade_tracker.integrations.base import BaseBroker
from trade_tracker.integrations.exceptions import (
    BrokerConnectionError,
    BrokerAuthenticationError,
    BrokerDataError,
)
from trade_tracker.models.trade import StockTrade, OptionTrade, TradeType, OptionType
from trade_tracker.models.position import Position


class IBKRApp(EWrapper, EClient):
    """
    IB API application combining EWrapper and EClient.

    This class handles the low-level IB API communication.
    """

    def __init__(self):
        """Initialize IB API application."""
        if not IBAPI_AVAILABLE:
            raise ImportError(
                "ibapi package not installed. Install with: pip install ibapi"
            )

        EClient.__init__(self, self)
        self.connected = False
        self.next_valid_id = None

        # Storage for data received from IB
        self.executions = []
        self.positions = []
        self.account_values = {}

        # Threading events for synchronization
        self.connection_event = threading.Event()
        self.executions_event = threading.Event()
        self.positions_event = threading.Event()
        self.account_event = threading.Event()

    def nextValidId(self, orderId: int):
        """Callback when connection is established."""
        super().nextValidId(orderId)
        self.next_valid_id = orderId
        self.connected = True
        self.connection_event.set()

    def error(self, reqId, errorCode, errorString):
        """Callback for errors."""
        super().error(reqId, errorCode, errorString)
        # Connection errors
        if errorCode in [502, 503, 504, 1100, 1101, 1102]:
            self.connected = False

        print(f"IB Error {errorCode}: {errorString}")

    def execDetails(self, reqId, contract, execution):
        """Callback when execution details are received."""
        super().execDetails(reqId, contract, execution)

        exec_data = {
            'symbol': contract.symbol,
            'secType': contract.secType,
            'side': execution.side,
            'shares': execution.shares,
            'price': execution.price,
            'time': execution.time,
            'commission': 0.0,  # Will be updated in commissionReport
            'execId': execution.execId,
        }

        # Add option-specific fields if applicable
        if contract.secType == 'OPT':
            exec_data['strike'] = contract.strike
            exec_data['right'] = contract.right
            exec_data['expiry'] = contract.lastTradeDateOrContractMonth

        self.executions.append(exec_data)

    def commissionReport(self, commissionReport):
        """Callback when commission report is received."""
        super().commissionReport(commissionReport)

        # Find matching execution and update commission
        for exec_data in self.executions:
            if exec_data.get('execId') == commissionReport.execId:
                exec_data['commission'] = commissionReport.commission
                break

    def execDetailsEnd(self, reqId):
        """Callback when all execution details have been received."""
        super().execDetailsEnd(reqId)
        self.executions_event.set()

    def position(self, account, contract, position, avgCost):
        """Callback when position data is received."""
        super().position(account, contract, position, avgCost)

        pos_data = {
            'symbol': contract.symbol,
            'secType': contract.secType,
            'position': position,
            'avgCost': avgCost,
            'account': account,
        }

        # Add option-specific fields if applicable
        if contract.secType == 'OPT':
            pos_data['strike'] = contract.strike
            pos_data['right'] = contract.right
            pos_data['expiry'] = contract.lastTradeDateOrContractMonth

        self.positions.append(pos_data)

    def positionEnd(self):
        """Callback when all positions have been received."""
        super().positionEnd()
        self.positions_event.set()

    def updateAccountValue(self, key, val, currency, accountName):
        """Callback when account value is updated."""
        super().updateAccountValue(key, val, currency, accountName)
        self.account_values[key] = val

    def accountDownloadEnd(self, accountName):
        """Callback when account download is complete."""
        super().accountDownloadEnd(accountName)
        self.account_event.set()


class IBKRBroker(BaseBroker):
    """
    Interactive Brokers broker integration.

    Connects to IB Trader Workstation (TWS) or IB Gateway.
    """

    def __init__(self, credentials: Dict[str, Any]):
        """
        Initialize IBKR broker.

        Args:
            credentials: Dictionary with keys:
                - host: IB Gateway/TWS host (default: 127.0.0.1)
                - port: IB Gateway/TWS port (default: 7497 for paper, 7496 for live)
                - client_id: Client ID (default: 1)
        """
        super().__init__(credentials)
        self.host = credentials.get('host', '127.0.0.1')
        self.port = credentials.get('port', 7497)
        self.client_id = credentials.get('client_id', 1)

        self.app = None
        self.api_thread = None

    def connect(self) -> bool:
        """
        Connect to IBKR.

        Returns:
            True if connection successful

        Raises:
            BrokerConnectionError: If connection fails
        """
        if self._connected:
            return True

        try:
            result = self._connect_and_wait()
            if not result:
                raise BrokerConnectionError("Failed to connect to IBKR")

            self._connected = True
            return True

        except Exception as e:
            raise BrokerConnectionError(f"IBKR connection failed: {str(e)}")

    def _connect_and_wait(self, timeout: int = 10) -> bool:
        """
        Connect to IB and wait for connection confirmation.

        Args:
            timeout: Timeout in seconds

        Returns:
            True if connected successfully
        """
        self.app = IBKRApp()

        # Connect to IB Gateway/TWS
        self.app.connect(self.host, self.port, self.client_id)

        # Start API thread
        self.api_thread = threading.Thread(target=self.app.run, daemon=True)
        self.api_thread.start()

        # Wait for connection confirmation
        connected = self.app.connection_event.wait(timeout=timeout)

        return connected and self.app.connected

    def disconnect(self) -> None:
        """Disconnect from IBKR."""
        if self.app and self.app.isConnected():
            self.app.disconnect()

        self._connected = False

    def is_connected(self) -> bool:
        """
        Check if connected to IBKR.

        Returns:
            True if connected
        """
        return bool(self._connected and self.app and self.app.connected)

    def fetch_trades(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        symbol: Optional[str] = None
    ) -> List[StockTrade | OptionTrade]:
        """
        Fetch executed trades from IBKR.

        Args:
            start_date: Filter trades from this date
            end_date: Filter trades to this date
            symbol: Filter trades for specific symbol

        Returns:
            List of Trade objects

        Raises:
            BrokerConnectionError: If not connected
            BrokerDataError: If data cannot be parsed
        """
        if not self.is_connected():
            raise BrokerConnectionError("Not connected to IBKR")

        try:
            # Fetch executions from IB
            executions = self._fetch_executions(start_date=start_date, end_date=end_date, symbol=symbol)

            # Convert to our Trade models
            trades = []
            for exec_data in executions:
                try:
                    trade = self._parse_execution_to_trade(exec_data)
                    if trade:
                        trades.append(trade)
                except Exception as e:
                    raise BrokerDataError(f"Failed to parse execution data: {str(e)}")

            return trades

        except BrokerConnectionError:
            raise
        except BrokerDataError:
            raise
        except Exception as e:
            raise BrokerDataError(f"Failed to fetch trades: {str(e)}")

    def _fetch_executions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch executions from IB API.

        Args:
            start_date: Filter from this date
            end_date: Filter to this date
            symbol: Filter by symbol

        Returns:
            List of execution dictionaries
        """
        # Clear previous data
        self.app.executions = []
        self.app.executions_event.clear()

        # Create execution filter
        exec_filter = ExecutionFilter() if ExecutionFilter else None
        if exec_filter:
            if symbol:
                exec_filter.symbol = symbol
            # Note: IB API doesn't support date filtering in ExecutionFilter
            # We'll filter by date after receiving all executions

        # Request executions
        req_id = 1
        self.app.reqExecutions(req_id, exec_filter if exec_filter else ExecutionFilter())

        # Wait for all executions to be received
        self.app.executions_event.wait(timeout=30)

        executions = self.app.executions.copy()

        # Apply date filtering if needed
        if start_date or end_date:
            filtered_executions = []
            for exec_data in executions:
                exec_time = self._parse_datetime(exec_data['time'])
                if start_date and exec_time < start_date:
                    continue
                if end_date and exec_time > end_date:
                    continue
                filtered_executions.append(exec_data)
            executions = filtered_executions

        return executions

    def _parse_execution_to_trade(self, exec_data: Dict[str, Any]) -> Optional[StockTrade | OptionTrade]:
        """
        Parse IB execution data to our Trade model.

        Args:
            exec_data: Execution data dictionary

        Returns:
            StockTrade or OptionTrade object, or None if invalid
        """
        if not exec_data.get('symbol'):
            return None

        sec_type = exec_data['secType']
        trade_date = self._parse_datetime(exec_data['time'])
        trade_type = self._map_side_to_trade_type(exec_data['side'], sec_type)

        common_fields = {
            'symbol': exec_data['symbol'],
            'trade_type': trade_type,
            'quantity': abs(int(exec_data['shares'])),
            'price': Decimal(str(exec_data['price'])),
            'commission': Decimal(str(exec_data.get('commission', 0.0))),
            'trade_date': trade_date,
            'account_id': 1,  # Will be set based on user's account setup
        }

        if sec_type == 'STK':
            return StockTrade(**common_fields)
        elif sec_type == 'OPT':
            option_fields = {
                **common_fields,
                'strike': Decimal(str(exec_data['strike'])),
                'expiry': self._parse_expiry_date(exec_data['expiry']),
                'option_type': self._map_option_right(exec_data['right']),
            }
            return OptionTrade(**option_fields)

        return None

    def fetch_positions(self) -> List[Position]:
        """
        Fetch current positions from IBKR.

        Returns:
            List of Position objects

        Raises:
            BrokerConnectionError: If not connected
        """
        if not self.is_connected():
            raise BrokerConnectionError("Not connected to IBKR")

        try:
            positions_data = self._fetch_positions_data()

            positions = []
            for pos_data in positions_data:
                position = self._parse_position_data(pos_data)
                if position:
                    positions.append(position)

            return positions

        except Exception as e:
            raise BrokerDataError(f"Failed to fetch positions: {str(e)}")

    def _fetch_positions_data(self) -> List[Dict[str, Any]]:
        """
        Fetch positions from IB API.

        Returns:
            List of position dictionaries
        """
        # Clear previous data
        self.app.positions = []
        self.app.positions_event.clear()

        # Request positions
        self.app.reqPositions()

        # Wait for all positions to be received
        self.app.positions_event.wait(timeout=30)

        return self.app.positions.copy()

    def _parse_position_data(self, pos_data: Dict[str, Any]) -> Optional[Position]:
        """
        Parse IB position data to our Position model.

        Args:
            pos_data: Position data dictionary

        Returns:
            Position object or None if invalid
        """
        if not pos_data.get('symbol'):
            return None

        # Determine asset type from security type
        from trade_tracker.models.trade import AssetType
        sec_type = pos_data.get('secType', 'STK')
        asset_type = AssetType.STOCK if sec_type == 'STK' else AssetType.OPTION

        # For now, create a simple position without all the detailed fields
        # This can be expanded to include unrealized P/L when we fetch market prices
        return Position(
            symbol=pos_data['symbol'],
            asset_type=asset_type,
            quantity=int(pos_data['position']),
            average_price=Decimal(str(pos_data['avgCost'])),
            current_price=Decimal(str(pos_data['avgCost'])),  # Placeholder
            account_id=1,
        )

    def fetch_account_info(self) -> Dict[str, Any]:
        """
        Fetch account information from IBKR.

        Returns:
            Dictionary with account details

        Raises:
            BrokerConnectionError: If not connected
        """
        if not self.is_connected():
            raise BrokerConnectionError("Not connected to IBKR")

        return self._fetch_account_data()

    def _fetch_account_data(self) -> Dict[str, Any]:
        """
        Fetch account data from IB API.

        Returns:
            Dictionary with account information
        """
        # Clear previous data
        self.app.account_values = {}
        self.app.account_event.clear()

        # Request account updates
        account_code = ""  # Empty string gets all accounts
        self.app.reqAccountUpdates(True, account_code)

        # Wait for account data
        self.app.account_event.wait(timeout=30)

        # Stop account updates
        self.app.reqAccountUpdates(False, account_code)

        # Parse account values
        return {
            'account_id': self.app.account_values.get('AccountCode', 'Unknown'),
            'net_liquidation': float(self.app.account_values.get('NetLiquidation', 0)),
            'total_cash_value': float(self.app.account_values.get('TotalCashValue', 0)),
            'buying_power': float(self.app.account_values.get('BuyingPower', 0)),
            'gross_position_value': float(self.app.account_values.get('GrossPositionValue', 0)),
        }

    def _map_side_to_trade_type(self, side: str, sec_type: str) -> TradeType:
        """
        Map IB side to our TradeType.

        Args:
            side: IB side ('BOT' or 'SLD')
            sec_type: Security type ('STK' or 'OPT')

        Returns:
            TradeType enum value
        """
        if sec_type == 'STK':
            return TradeType.BUY if side == 'BOT' else TradeType.SELL
        else:  # OPT
            return TradeType.BUY_TO_OPEN if side == 'BOT' else TradeType.SELL_TO_CLOSE

    def _map_option_right(self, right: str) -> OptionType:
        """
        Map IB option right to our OptionType.

        Args:
            right: IB option right ('C' or 'P')

        Returns:
            OptionType enum value
        """
        return OptionType.CALL if right == 'C' else OptionType.PUT

    def _parse_datetime(self, time_str: str) -> datetime:
        """
        Parse IB datetime format.

        Args:
            time_str: IB time string (format: "YYYYMMDD  HH:MM:SS")

        Returns:
            datetime object
        """
        # IB format: "20240115  10:30:00"
        time_str = time_str.strip()
        return datetime.strptime(time_str, "%Y%m%d  %H:%M:%S")

    def _parse_expiry_date(self, expiry_str: str) -> date:
        """
        Parse IB expiry date format.

        Args:
            expiry_str: IB expiry string (format: "YYYYMMDD")

        Returns:
            date object
        """
        # IB format: "20240315"
        return datetime.strptime(expiry_str, "%Y%m%d").date()
