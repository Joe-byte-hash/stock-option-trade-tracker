"""
Trade charting functionality with entry/exit point visualization.

Provides interactive price charts showing:
- Candlestick/OHLC price data
- Entry and exit points overlaid on chart
- P/L zones color-coded
- Trade details on hover
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from trade_tracker.models.trade import StockTrade, OptionTrade, TradeType

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    yf = None
    YFINANCE_AVAILABLE = False


class TradeChartBuilder:
    """
    Build interactive charts showing price action with trade entry/exit points.

    Features:
    - Candlestick charts with OHLC data
    - Entry points marked with green triangles
    - Exit points marked with red/green triangles (based on P/L)
    - Hover annotations with trade details
    - P/L zones shaded
    - Multiple timeframe support
    """

    def __init__(self, require_yfinance: bool = True, yfinance_module=None):
        """
        Initialize chart builder.

        Args:
            require_yfinance: If True, raises ImportError when yfinance not available.
                             Set to False for testing with mocks.
            yfinance_module: Optional yfinance module to use (for testing).
        """
        if yfinance_module:
            self.yf = yfinance_module
        elif YFINANCE_AVAILABLE:
            self.yf = yf
        elif require_yfinance:
            raise ImportError(
                "yfinance is required for charting. Install with: pip install yfinance"
            )
        else:
            self.yf = None

    def fetch_price_data(
        self,
        symbol: str,
        period: str = "3mo",
        interval: str = "1d"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch historical price data from Yahoo Finance.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            period: Time period (1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)

        Returns:
            DataFrame with OHLC data or None if error
        """
        try:
            ticker = self.yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)

            if data.empty:
                return None

            return data

        except Exception as e:
            print(f"Error fetching price data for {symbol}: {e}")
            return None

    def create_trade_chart(
        self,
        symbol: str,
        trades: List[StockTrade],
        period: str = "3mo",
        interval: str = "1d"
    ) -> Optional[go.Figure]:
        """
        Create interactive chart with price data and trade markers.

        Args:
            symbol: Stock symbol to chart
            trades: List of trades for this symbol
            period: Time period to display
            interval: Data interval

        Returns:
            Plotly Figure object or None if error
        """
        # Fetch price data
        price_data = self.fetch_price_data(symbol, period, interval)

        if price_data is None or price_data.empty:
            return None

        # Create figure with candlestick chart
        fig = go.Figure()

        # Add candlestick trace
        fig.add_trace(go.Candlestick(
            x=price_data.index,
            open=price_data['Open'],
            high=price_data['High'],
            low=price_data['Low'],
            close=price_data['Close'],
            name=symbol,
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ))

        # Add trade markers if trades provided
        if trades:
            self._add_trade_markers(fig, trades, price_data)

        # Update layout
        fig.update_layout(
            title=f"{symbol} - Price Chart with Trade Entry/Exit Points",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            template="plotly_white",
            hovermode='x unified',
            xaxis_rangeslider_visible=False,
            height=600,
            showlegend=True,
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        return fig

    def _add_trade_markers(
        self,
        fig: go.Figure,
        trades: List[StockTrade],
        price_data: pd.DataFrame
    ) -> None:
        """
        Add entry/exit markers to chart.

        Args:
            fig: Plotly figure to add markers to
            trades: List of trades
            price_data: Price data DataFrame
        """
        # Separate buy and sell trades
        buy_trades = [t for t in trades if t.trade_type in [TradeType.BUY, "buy"]]
        sell_trades = [t for t in trades if t.trade_type in [TradeType.SELL, "sell"]]

        # Add buy markers (entry points)
        if buy_trades:
            buy_dates = [t.trade_date for t in buy_trades]
            buy_prices = [float(t.price) for t in buy_trades]
            buy_hover_texts = [
                f"BUY<br>Date: {t.trade_date.strftime('%Y-%m-%d')}<br>"
                f"Price: ${float(t.price):.2f}<br>"
                f"Quantity: {t.quantity}<br>"
                f"Cost: ${float(t.total_cost):.2f}"
                for t in buy_trades
            ]

            fig.add_trace(go.Scatter(
                x=buy_dates,
                y=buy_prices,
                mode='markers',
                name='Buy (Entry)',
                marker=dict(
                    symbol='triangle-up',
                    size=15,
                    color='#2ecc71',
                    line=dict(color='white', width=2)
                ),
                hovertext=buy_hover_texts,
                hoverinfo='text'
            ))

        # Add sell markers (exit points)
        if sell_trades:
            # Try to match sells with corresponding buys for P/L calculation
            sell_dates = [t.trade_date for t in sell_trades]
            sell_prices = [float(t.price) for t in sell_trades]

            # Calculate P/L for coloring
            sell_colors = []
            sell_hover_texts = []

            for sell_trade in sell_trades:
                # Find matching buy (simplistic - first buy before this sell)
                matching_buy = None
                for buy_trade in buy_trades:
                    if buy_trade.trade_date < sell_trade.trade_date:
                        matching_buy = buy_trade
                        break

                if matching_buy:
                    pnl = self._calculate_trade_pnl(matching_buy, sell_trade)
                    color = '#2ecc71' if pnl > 0 else '#e74c3c'  # Green if profit, red if loss
                    pnl_text = f"<br>P/L: ${float(pnl):.2f}"
                else:
                    color = '#95a5a6'  # Gray if no match
                    pnl_text = ""

                sell_colors.append(color)
                sell_hover_texts.append(
                    f"SELL<br>Date: {sell_trade.trade_date.strftime('%Y-%m-%d')}<br>"
                    f"Price: ${float(sell_trade.price):.2f}<br>"
                    f"Quantity: {sell_trade.quantity}{pnl_text}"
                )

            fig.add_trace(go.Scatter(
                x=sell_dates,
                y=sell_prices,
                mode='markers',
                name='Sell (Exit)',
                marker=dict(
                    symbol='triangle-down',
                    size=15,
                    color=sell_colors,
                    line=dict(color='white', width=2)
                ),
                hovertext=sell_hover_texts,
                hoverinfo='text'
            ))

    def _calculate_trade_pnl(
        self,
        buy_trade: StockTrade,
        sell_trade: StockTrade
    ) -> Decimal:
        """
        Calculate P/L for a matched buy/sell pair.

        Args:
            buy_trade: Entry trade
            sell_trade: Exit trade

        Returns:
            P/L in dollars
        """
        # Simple P/L: (sell_price - buy_price) * quantity - total commissions
        price_diff = sell_trade.price - buy_trade.price
        gross_pnl = price_diff * min(buy_trade.quantity, sell_trade.quantity)
        total_commissions = buy_trade.commission + sell_trade.commission

        return gross_pnl - total_commissions

    def create_symbol_chart_with_all_trades(
        self,
        symbol: str,
        all_trades: List[StockTrade],
        period: str = "1y"
    ) -> Optional[go.Figure]:
        """
        Create chart for a symbol with all its trades.

        Args:
            symbol: Symbol to chart
            all_trades: All trades (will be filtered by symbol)
            period: Time period

        Returns:
            Plotly Figure or None
        """
        # Filter trades for this symbol
        symbol_trades = [t for t in all_trades if t.symbol == symbol]

        if not symbol_trades:
            return None

        return self.create_trade_chart(symbol, symbol_trades, period)

    def create_multi_symbol_charts(
        self,
        symbols: List[str],
        all_trades: List[StockTrade],
        period: str = "6mo"
    ) -> Dict[str, go.Figure]:
        """
        Create charts for multiple symbols.

        Args:
            symbols: List of symbols to chart
            all_trades: All trades
            period: Time period

        Returns:
            Dictionary mapping symbol to Figure
        """
        charts = {}

        for symbol in symbols:
            fig = self.create_symbol_chart_with_all_trades(
                symbol, all_trades, period
            )
            if fig:
                charts[symbol] = fig

        return charts
