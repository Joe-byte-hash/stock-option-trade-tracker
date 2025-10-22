"""Basic usage examples for Trade Tracker."""

import os
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path

from trade_tracker.database.connection import DatabaseManager
from trade_tracker.database.encryption import DatabaseEncryption
from trade_tracker.database.repository import TradeRepository, AccountRepository, PositionRepository
from trade_tracker.models.trade import StockTrade, OptionTrade, TradeType, OptionType
from trade_tracker.models.account import Account, BrokerType
from trade_tracker.models.position import Position, AssetType
from trade_tracker.analytics.pnl import PnLCalculator
from trade_tracker.analytics.metrics import MetricsCalculator


def setup_database():
    """Initialize encrypted database."""
    # Setup database path
    db_path = Path("data/trades.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize database
    db = DatabaseManager(str(db_path))
    db.create_tables()

    print(f"✓ Database created at {db_path}")
    return db


def create_account_example(db: DatabaseManager):
    """Example: Create a trading account."""
    with db.get_session() as session:
        repo = AccountRepository(session)

        # Create IBKR account
        account = Account(
            name="My Interactive Brokers Account",
            broker=BrokerType.IBKR,
            account_number="U1234567",
            is_active=True,
        )

        saved_account = repo.create(account)
        print(f"\n✓ Created account: {saved_account.name} (ID: {saved_account.id})")
        return saved_account.id


def add_stock_trades_example(db: DatabaseManager, account_id: int):
    """Example: Add stock trades."""
    with db.get_session() as session:
        repo = TradeRepository(session)

        # Buy AAPL
        buy_trade = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.BUY,
            quantity=100,
            price=Decimal("150.50"),
            commission=Decimal("1.00"),
            trade_date=datetime(2024, 1, 1, 10, 30),
            account_id=account_id,
            notes="Bought on dip after earnings",
        )

        saved_buy = repo.create(buy_trade)
        print(f"\n✓ Created buy trade: {saved_buy.symbol} x{saved_buy.quantity} @ ${saved_buy.price}")

        # Sell AAPL
        sell_trade = StockTrade(
            symbol="AAPL",
            trade_type=TradeType.SELL,
            quantity=100,
            price=Decimal("165.75"),
            commission=Decimal("1.00"),
            trade_date=datetime(2024, 1, 15, 14, 20),
            account_id=account_id,
            notes="Sold at resistance level",
        )

        saved_sell = repo.create(sell_trade)
        print(f"✓ Created sell trade: {saved_sell.symbol} x{saved_sell.quantity} @ ${saved_sell.price}")

        return saved_buy, saved_sell


def add_option_trades_example(db: DatabaseManager, account_id: int):
    """Example: Add option trades."""
    with db.get_session() as session:
        repo = TradeRepository(session)

        # Buy TSLA call options
        buy_option = OptionTrade(
            symbol="TSLA",
            trade_type=TradeType.BUY_TO_OPEN,
            quantity=10,
            price=Decimal("8.50"),
            strike=Decimal("250.00"),
            expiry=date(2024, 3, 15),
            option_type=OptionType.CALL,
            commission=Decimal("6.50"),
            trade_date=datetime(2024, 1, 1, 10, 0),
            account_id=account_id,
            notes="Bullish on TSLA, expecting breakout",
        )

        saved_buy_option = repo.create(buy_option)
        print(f"\n✓ Created option buy: {saved_buy_option.symbol} {saved_buy_option.option_type} "
              f"${saved_buy_option.strike} x{saved_buy_option.quantity}")

        # Sell to close
        sell_option = OptionTrade(
            symbol="TSLA",
            trade_type=TradeType.SELL_TO_CLOSE,
            quantity=10,
            price=Decimal("12.00"),
            strike=Decimal("250.00"),
            expiry=date(2024, 3, 15),
            option_type=OptionType.CALL,
            commission=Decimal("6.50"),
            trade_date=datetime(2024, 1, 10, 15, 30),
            account_id=account_id,
            notes="Taking profit at 41% gain",
        )

        saved_sell_option = repo.create(sell_option)
        print(f"✓ Created option sell: {saved_sell_option.symbol} {saved_sell_option.option_type} "
              f"${saved_sell_option.strike} x{saved_sell_option.quantity}")

        return saved_buy_option, saved_sell_option


def calculate_pnl_example(buy_trade, sell_trade):
    """Example: Calculate P/L for a trade pair."""
    calculator = PnLCalculator()

    # Calculate stock P/L
    if isinstance(buy_trade, StockTrade):
        pnl = calculator.calculate_stock_pnl(buy_trade, sell_trade)
        print(f"\n📊 Stock Trade P/L Analysis:")
    else:
        pnl = calculator.calculate_option_pnl(buy_trade, sell_trade)
        print(f"\n📊 Option Trade P/L Analysis:")

    print(f"  Symbol: {pnl.symbol}")
    print(f"  Cost Basis: ${pnl.cost_basis:,.2f}")
    print(f"  Proceeds: ${pnl.proceeds:,.2f}")
    print(f"  Realized P/L: ${pnl.realized_pnl:,.2f}")
    print(f"  Return: {pnl.return_percentage}%")
    print(f"  Holding Period: {pnl.holding_period_days} days")

    return pnl


def calculate_metrics_example(pnl_results):
    """Example: Calculate portfolio metrics."""
    calculator = MetricsCalculator()

    # Trade statistics
    stats = calculator.calculate_trade_statistics(pnl_results)

    print(f"\n📈 Portfolio Metrics:")
    print(f"  Total Trades: {stats.total_trades}")
    print(f"  Winning Trades: {stats.winning_trades}")
    print(f"  Losing Trades: {stats.losing_trades}")
    print(f"  Win Rate: {stats.win_rate}%")
    print(f"  Average Win: ${stats.average_win:,.2f}")
    print(f"  Average Loss: ${stats.average_loss:,.2f}")
    print(f"  Largest Win: ${stats.largest_win:,.2f}")
    print(f"  Largest Loss: ${stats.largest_loss:,.2f}")
    print(f"  Profit Factor: {stats.profit_factor}")

    # Total P/L
    total_pnl = sum(p.realized_pnl for p in pnl_results)
    print(f"\n  💰 Total P/L: ${total_pnl:,.2f}")


def query_trades_example(db: DatabaseManager):
    """Example: Query trades from database."""
    with db.get_session() as session:
        repo = TradeRepository(session)

        # Get all AAPL trades
        aapl_trades = repo.get_by_symbol("AAPL")
        print(f"\n🔍 Found {len(aapl_trades)} AAPL trades")

        # Get all trades
        all_trades = repo.get_all()
        print(f"🔍 Total trades in database: {len(all_trades)}")


def main():
    """Run all examples."""
    print("=" * 60)
    print("Trade Tracker - Basic Usage Examples")
    print("=" * 60)

    # Setup
    db = setup_database()

    # Create account
    account_id = create_account_example(db)

    # Add stock trades
    stock_buy, stock_sell = add_stock_trades_example(db, account_id)

    # Add option trades
    option_buy, option_sell = add_option_trades_example(db, account_id)

    # Calculate P/L
    stock_pnl = calculate_pnl_example(stock_buy, stock_sell)
    option_pnl = calculate_pnl_example(option_buy, option_sell)

    # Calculate metrics
    all_pnl = [stock_pnl, option_pnl]
    calculate_metrics_example(all_pnl)

    # Query trades
    query_trades_example(db)

    print("\n" + "=" * 60)
    print("✓ Examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
