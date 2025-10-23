"""Advanced portfolio analysis examples."""

from datetime import datetime, timedelta
from decimal import Decimal

from trade_tracker.models.trade import StockTrade, TradeType
from trade_tracker.analytics.pnl import PnLCalculator, PositionPnL
from trade_tracker.analytics.metrics import MetricsCalculator


def create_sample_portfolio():
    """Create a sample portfolio of trades."""
    print("=" * 60)
    print("Creating Sample Portfolio")
    print("=" * 60)

    base_date = datetime(2024, 1, 1)

    trades = [
        # Winning trades
        (
            StockTrade(symbol="AAPL", trade_type=TradeType.BUY, quantity=100,
                      price=Decimal("150"), commission=Decimal("1"),
                      trade_date=base_date),
            StockTrade(symbol="AAPL", trade_type=TradeType.SELL, quantity=100,
                      price=Decimal("165"), commission=Decimal("1"),
                      trade_date=base_date + timedelta(days=10)),
        ),
        (
            StockTrade(symbol="MSFT", trade_type=TradeType.BUY, quantity=50,
                      price=Decimal("300"), commission=Decimal("1"),
                      trade_date=base_date + timedelta(days=5)),
            StockTrade(symbol="MSFT", trade_type=TradeType.SELL, quantity=50,
                      price=Decimal("320"), commission=Decimal("1"),
                      trade_date=base_date + timedelta(days=20)),
        ),
        (
            StockTrade(symbol="GOOGL", trade_type=TradeType.BUY, quantity=30,
                      price=Decimal("140"), commission=Decimal("1"),
                      trade_date=base_date + timedelta(days=15)),
            StockTrade(symbol="GOOGL", trade_type=TradeType.SELL, quantity=30,
                      price=Decimal("155"), commission=Decimal("1"),
                      trade_date=base_date + timedelta(days=30)),
        ),
        # Losing trades
        (
            StockTrade(symbol="TSLA", trade_type=TradeType.BUY, quantity=40,
                      price=Decimal("250"), commission=Decimal("1"),
                      trade_date=base_date + timedelta(days=2)),
            StockTrade(symbol="TSLA", trade_type=TradeType.SELL, quantity=40,
                      price=Decimal("230"), commission=Decimal("1"),
                      trade_date=base_date + timedelta(days=12)),
        ),
        (
            StockTrade(symbol="NVDA", trade_type=TradeType.BUY, quantity=25,
                      price=Decimal("500"), commission=Decimal("1"),
                      trade_date=base_date + timedelta(days=8)),
            StockTrade(symbol="NVDA", trade_type=TradeType.SELL, quantity=25,
                      price=Decimal("480"), commission=Decimal("1"),
                      trade_date=base_date + timedelta(days=18)),
        ),
    ]

    print(f"✓ Created {len(trades)} trade pairs")
    return trades


def analyze_individual_trades(trades):
    """Analyze each trade pair."""
    print("\n" + "=" * 60)
    print("Individual Trade Analysis")
    print("=" * 60)

    calculator = PnLCalculator()
    pnl_results = []

    print(f"\n{'Symbol':<8} {'Entry':<10} {'Exit':<10} {'P/L':<12} {'Return':<10} {'Days':<6}")
    print("-" * 60)

    for buy, sell in trades:
        pnl = calculator.calculate_stock_pnl(buy, sell)
        pnl_results.append(pnl)

        # Format output
        symbol = pnl.symbol
        entry = f"${buy.price}"
        exit = f"${sell.price}"
        pnl_str = f"${pnl.realized_pnl:>10,.2f}"
        ret_str = f"{pnl.return_percentage:>7.2f}%"
        days = pnl.holding_period_days

        # Color code (simulate with symbols)
        indicator = "✓" if pnl.realized_pnl > 0 else "✗"

        print(f"{symbol:<8} {entry:<10} {exit:<10} {pnl_str:<12} {ret_str:<10} {days:<6} {indicator}")

    return pnl_results


def calculate_portfolio_statistics(pnl_results):
    """Calculate comprehensive portfolio statistics."""
    print("\n" + "=" * 60)
    print("Portfolio Statistics")
    print("=" * 60)

    calculator = MetricsCalculator()
    stats = calculator.calculate_trade_statistics(pnl_results)

    print(f"\n📊 Trade Metrics:")
    print(f"  Total Trades: {stats.total_trades}")
    print(f"  Winners: {stats.winning_trades} ({stats.win_rate}%)")
    print(f"  Losers: {stats.losing_trades} ({100 - stats.win_rate:.2f}%)")

    print(f"\n💰 P/L Metrics:")
    total_pnl = sum(p.realized_pnl for p in pnl_results)
    print(f"  Total P/L: ${total_pnl:,.2f}")
    print(f"  Average Win: ${stats.average_win:,.2f}")
    print(f"  Average Loss: ${stats.average_loss:,.2f}")
    print(f"  Largest Win: ${stats.largest_win:,.2f}")
    print(f"  Largest Loss: ${stats.largest_loss:,.2f}")

    print(f"\n📈 Risk Metrics:")
    print(f"  Profit Factor: {stats.profit_factor}")
    print(f"  Avg Win/Loss Ratio: {abs(stats.average_win / stats.average_loss):.2f}x" if stats.average_loss != 0 else "  Avg Win/Loss Ratio: N/A")


def analyze_by_time_period(trades):
    """Analyze returns by time period."""
    print("\n" + "=" * 60)
    print("Time Period Analysis")
    print("=" * 60)

    calculator = PnLCalculator()
    calc_metrics = MetricsCalculator()

    # Prepare trade data
    trade_dates_pnl = []
    for buy, sell in trades:
        pnl = calculator.calculate_stock_pnl(buy, sell)
        trade_dates_pnl.append((sell.trade_date, pnl.realized_pnl))

    # Daily P/L
    daily_pnl = calc_metrics.calculate_daily_pnl(trade_dates_pnl)
    print(f"\n📅 Daily P/L:")
    for day, pnl in sorted(daily_pnl.items())[:5]:  # Show first 5
        print(f"  {day}: ${pnl:>10,.2f}")
    if len(daily_pnl) > 5:
        print(f"  ... and {len(daily_pnl) - 5} more days")

    # Weekly P/L
    weekly_pnl = calc_metrics.calculate_weekly_pnl(trade_dates_pnl)
    print(f"\n📅 Weekly P/L:")
    for (year, week), pnl in sorted(weekly_pnl.items()):
        print(f"  {year}-W{week:02d}: ${pnl:>10,.2f}")

    # Monthly P/L
    monthly_pnl = calc_metrics.calculate_monthly_pnl(trade_dates_pnl)
    print(f"\n📅 Monthly P/L:")
    for (year, month), pnl in sorted(monthly_pnl.items()):
        print(f"  {year}-{month:02d}: ${pnl:>10,.2f}")


def calculate_drawdown(pnl_results):
    """Calculate and display maximum drawdown."""
    print("\n" + "=" * 60)
    print("Drawdown Analysis")
    print("=" * 60)

    # Create equity curve
    initial_capital = Decimal("100000")
    equity = initial_capital
    equity_curve = [(datetime(2024, 1, 1), initial_capital)]

    for i, pnl in enumerate(pnl_results):
        equity += pnl.realized_pnl
        # Use approximate dates
        date = datetime(2024, 1, 1) + timedelta(days=(i + 1) * 10)
        equity_curve.append((date, equity))

    calculator = MetricsCalculator()
    drawdown = calculator.calculate_max_drawdown(equity_curve)

    print(f"\n📉 Maximum Drawdown:")
    print(f"  Amount: ${drawdown.max_drawdown_amount:,.2f}")
    print(f"  Percentage: {drawdown.max_drawdown_percent}%")
    if drawdown.peak_date:
        print(f"  Peak Date: {drawdown.peak_date.date()}")
    if drawdown.trough_date:
        print(f"  Trough Date: {drawdown.trough_date.date()}")

    # Show equity curve
    print(f"\n💵 Equity Curve:")
    print(f"  Starting Capital: ${initial_capital:,.2f}")
    print(f"  Ending Equity: ${equity:,.2f}")
    print(f"  Total Return: ${equity - initial_capital:,.2f} ({(equity - initial_capital) / initial_capital * 100:.2f}%)")


def calculate_sharpe_ratio(pnl_results):
    """Calculate Sharpe ratio."""
    print("\n" + "=" * 60)
    print("Risk-Adjusted Returns (Sharpe Ratio)")
    print("=" * 60)

    # Calculate returns for each trade
    returns = [pnl.return_percentage / 100 for pnl in pnl_results if pnl.return_percentage]

    calculator = MetricsCalculator()
    sharpe = calculator.calculate_sharpe_ratio(
        returns,
        risk_free_rate=Decimal("0.04"),  # 4% annual risk-free rate
        periods_per_year=52  # Weekly trades assumption
    )

    print(f"\n📊 Sharpe Ratio: {sharpe}")
    print(f"  Risk-Free Rate: 4.0%")
    print(f"  Interpretation:")
    if sharpe > 2:
        print(f"    Excellent (>2.0)")
    elif sharpe > 1:
        print(f"    Good (1.0-2.0)")
    elif sharpe > 0:
        print(f"    Acceptable (0-1.0)")
    else:
        print(f"    Poor (<0)")


def main():
    """Run portfolio analysis."""
    print("\n" + "=" * 60)
    print("Trade Tracker - Advanced Portfolio Analysis")
    print("=" * 60)

    # Create sample portfolio
    trades = create_sample_portfolio()

    # Analyze individual trades
    pnl_results = analyze_individual_trades(trades)

    # Portfolio statistics
    calculate_portfolio_statistics(pnl_results)

    # Time period analysis
    analyze_by_time_period(trades)

    # Drawdown analysis
    calculate_drawdown(pnl_results)

    # Sharpe ratio
    calculate_sharpe_ratio(pnl_results)

    print("\n" + "=" * 60)
    print("✓ Portfolio analysis completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
