"""Dashboard demonstration with sample data."""

from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

from trade_tracker.database.connection import DatabaseManager
from trade_tracker.database.repository import TradeRepository, AccountRepository
from trade_tracker.models.trade import StockTrade, OptionTrade, TradeType, OptionType
from trade_tracker.models.account import Account, BrokerType
from trade_tracker.visualization.dashboard import TradeDashboard


def create_sample_data():
    """Create sample trading data for dashboard demonstration."""
    print("=" * 60)
    print("Creating Sample Trading Data")
    print("=" * 60)

    # Setup database
    db_path = Path("data/trades.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)

    db = DatabaseManager(str(db_path))
    db.create_tables()

    with db.get_session() as session:
        # Create account
        account_repo = AccountRepository(session)
        account = account_repo.create(Account(
            name="Demo Trading Account",
            broker=BrokerType.IBKR,
            account_number="DEMO123456"
        ))
        print(f"✓ Created account: {account.name}")

        # Create sample trades
        trade_repo = TradeRepository(session)
        base_date = datetime.now() - timedelta(days=90)

        trades_data = [
            # Winning trades
            ("AAPL", TradeType.BUY, 100, Decimal("150.00"), 0),
            ("AAPL", TradeType.SELL, 100, Decimal("165.00"), 10),

            ("MSFT", TradeType.BUY, 50, Decimal("300.00"), 15),
            ("MSFT", TradeType.SELL, 50, Decimal("320.00"), 30),

            ("GOOGL", TradeType.BUY, 30, Decimal("140.00"), 20),
            ("GOOGL", TradeType.SELL, 30, Decimal("155.00"), 35),

            ("NVDA", TradeType.BUY, 75, Decimal("400.00"), 25),
            ("NVDA", TradeType.SELL, 75, Decimal("450.00"), 45),

            # Losing trades
            ("TSLA", TradeType.BUY, 40, Decimal("250.00"), 5),
            ("TSLA", TradeType.SELL, 40, Decimal("230.00"), 18),

            ("AMD", TradeType.BUY, 100, Decimal("100.00"), 35),
            ("AMD", TradeType.SELL, 100, Decimal("95.00"), 50),

            # More winning trades
            ("META", TradeType.BUY, 25, Decimal("320.00"), 40),
            ("META", TradeType.SELL, 25, Decimal("350.00"), 60),

            ("NFLX", TradeType.BUY, 15, Decimal("400.00"), 45),
            ("NFLX", TradeType.SELL, 15, Decimal("420.00"), 65),

            ("AMZN", TradeType.BUY, 20, Decimal("150.00"), 50),
            ("AMZN", TradeType.SELL, 20, Decimal("165.00"), 70),

            # Losing trade
            ("COIN", TradeType.BUY, 50, Decimal("80.00"), 55),
            ("COIN", TradeType.SELL, 50, Decimal("72.00"), 75),
        ]

        trades_created = 0
        for symbol, trade_type, quantity, price, days_offset in trades_data:
            trade = StockTrade(
                symbol=symbol,
                trade_type=trade_type,
                quantity=quantity,
                price=price,
                commission=Decimal("1.00"),
                trade_date=base_date + timedelta(days=days_offset),
                account_id=account.id
            )
            trade_repo.create(trade)
            trades_created += 1

        print(f"✓ Created {trades_created} sample trades")

        # Add some option trades
        option_trades = [
            # Winning call
            (OptionType.CALL, TradeType.BUY_TO_OPEN, 10, Decimal("5.00"), Decimal("250.00"), 30),
            (OptionType.CALL, TradeType.SELL_TO_CLOSE, 10, Decimal("8.00"), Decimal("250.00"), 42),

            # Losing put
            (OptionType.PUT, TradeType.BUY_TO_OPEN, 5, Decimal("6.00"), Decimal("150.00"), 35),
            (OptionType.PUT, TradeType.SELL_TO_CLOSE, 5, Decimal("4.00"), Decimal("150.00"), 48),
        ]

        for opt_type, trade_type, qty, price, strike, days_offset in option_trades:
            trade = OptionTrade(
                symbol="TSLA" if opt_type == OptionType.CALL else "AAPL",
                trade_type=trade_type,
                quantity=qty,
                price=price,
                strike=strike,
                expiry=(base_date + timedelta(days=days_offset + 30)).date(),
                option_type=opt_type,
                commission=Decimal("6.50"),
                trade_date=base_date + timedelta(days=days_offset),
                account_id=account.id
            )
            trade_repo.create(trade)

        print(f"✓ Created 4 option trades")

    print(f"✓ Sample data creation complete!")
    print("=" * 60)


def main():
    """Create sample data and launch dashboard."""
    print("\n" + "=" * 60)
    print("Trade Tracker Dashboard Demo")
    print("=" * 60 + "\n")

    # Create sample data
    create_sample_data()

    print("\n" + "=" * 60)
    print("Launching Dashboard...")
    print("=" * 60 + "\n")

    # Launch dashboard
    dashboard = TradeDashboard()
    dashboard.run(debug=False)


if __name__ == "__main__":
    main()
