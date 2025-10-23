"""Interactive dashboard for trade tracking and analytics."""

import dash
from dash import dcc, html, dash_table, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
from typing import List, Dict, Any

from trade_tracker.database.connection import DatabaseManager
from trade_tracker.database.repository import TradeRepository, AccountRepository
from trade_tracker.analytics.pnl import PnLCalculator
from trade_tracker.analytics.metrics import MetricsCalculator


class TradeDashboard:
    """Interactive dashboard for trade tracking and analytics."""

    def __init__(self, db_path: str = "data/trades.db"):
        """
        Initialize dashboard.

        Args:
            db_path: Path to database file
        """
        self.db = DatabaseManager(db_path)
        self.app = dash.Dash(__name__, suppress_callback_exceptions=True)
        self._setup_layout()
        self._setup_callbacks()

    def _setup_layout(self):
        """Setup dashboard layout."""
        self.app.layout = html.Div([
            # Header
            html.Div([
                html.H1("📊 Trade Tracker Dashboard",
                       style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': '30px'}),
                html.Hr(),
            ], style={'marginBottom': '20px'}),

            # Metrics Cards Row
            html.Div(id='metrics-cards', children=[],
                    style={'marginBottom': '30px'}),

            # Charts Row 1: Portfolio Performance
            html.Div([
                html.Div([
                    html.H3("Portfolio Equity Curve", style={'textAlign': 'center'}),
                    dcc.Graph(id='equity-curve-chart'),
                ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),

                html.Div([
                    html.H3("P/L Distribution", style={'textAlign': 'center'}),
                    dcc.Graph(id='pnl-distribution-chart'),
                ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),
            ]),

            # Charts Row 2: Time Period Analysis
            html.Div([
                html.Div([
                    html.H3("Monthly P/L", style={'textAlign': 'center'}),
                    dcc.Graph(id='monthly-pnl-chart'),
                ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),

                html.Div([
                    html.H3("Win Rate by Symbol", style={'textAlign': 'center'}),
                    dcc.Graph(id='symbol-performance-chart'),
                ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),
            ]),

            # Trade History Table
            html.Div([
                html.H3("Trade History", style={'textAlign': 'center', 'marginTop': '30px'}),
                html.Div(id='trade-table'),
            ], style={'marginTop': '30px'}),

            # Refresh Button
            html.Div([
                html.Button('🔄 Refresh Data', id='refresh-button', n_clicks=0,
                          style={'marginTop': '20px', 'padding': '10px 20px',
                                'fontSize': '16px', 'cursor': 'pointer'}),
            ], style={'textAlign': 'center'}),

            # Hidden div for data storage
            dcc.Store(id='trade-data-store'),
        ], style={'padding': '20px', 'fontFamily': 'Arial, sans-serif'})

    def _setup_callbacks(self):
        """Setup dashboard callbacks."""

        @self.app.callback(
            [Output('trade-data-store', 'data'),
             Output('metrics-cards', 'children'),
             Output('equity-curve-chart', 'figure'),
             Output('pnl-distribution-chart', 'figure'),
             Output('monthly-pnl-chart', 'figure'),
             Output('symbol-performance-chart', 'figure'),
             Output('trade-table', 'children')],
            [Input('refresh-button', 'n_clicks')]
        )
        def update_dashboard(n_clicks):
            """Update all dashboard components."""
            # Load data
            with self.db.get_session() as session:
                trade_repo = TradeRepository(session)
                all_trades = trade_repo.get_all()

            if not all_trades:
                # Return empty components if no trades
                empty_fig = go.Figure()
                empty_fig.add_annotation(
                    text="No trade data available",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=20, color="gray")
                )
                return {}, [], empty_fig, empty_fig, empty_fig, empty_fig, html.Div("No trades found")

            # Calculate P/L for all trades
            pnl_calculator = PnLCalculator()
            pnl_results = self._calculate_pnl_for_trades(all_trades, pnl_calculator)

            # Calculate metrics
            metrics_calc = MetricsCalculator()
            stats = metrics_calc.calculate_trade_statistics(pnl_results)

            # Generate components
            metrics_cards = self._create_metrics_cards(stats, pnl_results)
            equity_curve = self._create_equity_curve(pnl_results)
            pnl_dist = self._create_pnl_distribution(pnl_results)
            monthly_pnl = self._create_monthly_pnl_chart(all_trades, pnl_results)
            symbol_perf = self._create_symbol_performance_chart(pnl_results)
            trade_table = self._create_trade_table(all_trades, pnl_results)

            return {}, metrics_cards, equity_curve, pnl_dist, monthly_pnl, symbol_perf, trade_table

    def _calculate_pnl_for_trades(self, trades, calculator):
        """Calculate P/L for trade pairs."""
        pnl_results = []

        # Group trades by symbol
        trades_by_symbol = {}
        for trade in trades:
            if trade.symbol not in trades_by_symbol:
                trades_by_symbol[trade.symbol] = []
            trades_by_symbol[trade.symbol].append(trade)

        # Match buy/sell pairs
        for symbol, symbol_trades in trades_by_symbol.items():
            # Sort by date
            symbol_trades.sort(key=lambda x: x.trade_date)

            # Simple FIFO matching
            buys = [t for t in symbol_trades if 'buy' in t.trade_type.value.lower()]
            sells = [t for t in symbol_trades if 'sell' in t.trade_type.value.lower()]

            for buy in buys[:len(sells)]:
                sell = sells[buys.index(buy)]
                try:
                    if hasattr(buy, 'strike'):  # Option trade
                        pnl = calculator.calculate_option_pnl(buy, sell)
                    else:  # Stock trade
                        pnl = calculator.calculate_stock_pnl(buy, sell)
                    pnl_results.append(pnl)
                except Exception:
                    continue

        return pnl_results

    def _create_metrics_cards(self, stats, pnl_results):
        """Create metrics summary cards."""
        total_pnl = sum(p.realized_pnl for p in pnl_results if p.realized_pnl)

        card_style = {
            'padding': '20px',
            'margin': '10px',
            'borderRadius': '10px',
            'boxShadow': '0 4px 6px rgba(0,0,0,0.1)',
            'textAlign': 'center',
            'width': '200px',
            'display': 'inline-block'
        }

        cards = [
            html.Div([
                html.H4("Total P/L", style={'color': '#7f8c8d'}),
                html.H2(f"${total_pnl:,.2f}",
                       style={'color': '#27ae60' if total_pnl > 0 else '#e74c3c'}),
            ], style={**card_style, 'backgroundColor': '#ecf0f1'}),

            html.Div([
                html.H4("Win Rate", style={'color': '#7f8c8d'}),
                html.H2(f"{stats.win_rate}%", style={'color': '#3498db'}),
            ], style={**card_style, 'backgroundColor': '#ecf0f1'}),

            html.Div([
                html.H4("Total Trades", style={'color': '#7f8c8d'}),
                html.H2(f"{stats.total_trades}", style={'color': '#34495e'}),
            ], style={**card_style, 'backgroundColor': '#ecf0f1'}),

            html.Div([
                html.H4("Profit Factor", style={'color': '#7f8c8d'}),
                html.H2(f"{stats.profit_factor}", style={'color': '#9b59b6'}),
            ], style={**card_style, 'backgroundColor': '#ecf0f1'}),

            html.Div([
                html.H4("Avg Win", style={'color': '#7f8c8d'}),
                html.H2(f"${stats.average_win:,.2f}", style={'color': '#27ae60'}),
            ], style={**card_style, 'backgroundColor': '#ecf0f1'}),
        ]

        return html.Div(cards, style={'textAlign': 'center'})

    def _create_equity_curve(self, pnl_results):
        """Create equity curve chart."""
        if not pnl_results:
            return go.Figure()

        initial_capital = Decimal("100000")
        equity = [float(initial_capital)]
        dates = [datetime.now() - timedelta(days=len(pnl_results))]

        for i, pnl in enumerate(pnl_results):
            equity.append(equity[-1] + float(pnl.realized_pnl))
            dates.append(datetime.now() - timedelta(days=len(pnl_results) - i - 1))

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=equity,
            mode='lines+markers',
            name='Equity',
            line=dict(color='#3498db', width=2),
            fill='tozeroy',
            fillcolor='rgba(52, 152, 219, 0.1)'
        ))

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Equity ($)",
            hovermode='x unified',
            template='plotly_white',
            height=400
        )

        return fig

    def _create_pnl_distribution(self, pnl_results):
        """Create P/L distribution chart."""
        if not pnl_results:
            return go.Figure()

        wins = [float(p.realized_pnl) for p in pnl_results if p.realized_pnl > 0]
        losses = [float(p.realized_pnl) for p in pnl_results if p.realized_pnl < 0]

        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=wins,
            name='Wins',
            marker_color='#27ae60',
            opacity=0.7
        ))
        fig.add_trace(go.Histogram(
            x=losses,
            name='Losses',
            marker_color='#e74c3c',
            opacity=0.7
        ))

        fig.update_layout(
            barmode='overlay',
            xaxis_title="P/L ($)",
            yaxis_title="Frequency",
            template='plotly_white',
            height=400
        )

        return fig

    def _create_monthly_pnl_chart(self, trades, pnl_results):
        """Create monthly P/L bar chart."""
        if not trades or not pnl_results:
            return go.Figure()

        # Group by month
        monthly_data = {}
        for trade, pnl in zip(trades, pnl_results):
            month_key = trade.trade_date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = Decimal("0")
            monthly_data[month_key] += pnl.realized_pnl

        months = sorted(monthly_data.keys())
        values = [float(monthly_data[m]) for m in months]
        colors = ['#27ae60' if v > 0 else '#e74c3c' for v in values]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=months,
            y=values,
            marker_color=colors,
            text=[f'${v:,.0f}' for v in values],
            textposition='outside'
        ))

        fig.update_layout(
            xaxis_title="Month",
            yaxis_title="P/L ($)",
            template='plotly_white',
            height=400,
            showlegend=False
        )

        return fig

    def _create_symbol_performance_chart(self, pnl_results):
        """Create symbol performance chart."""
        if not pnl_results:
            return go.Figure()

        # Group by symbol
        symbol_stats = {}
        for pnl in pnl_results:
            if pnl.symbol not in symbol_stats:
                symbol_stats[pnl.symbol] = {'wins': 0, 'total': 0, 'pnl': Decimal("0")}

            symbol_stats[pnl.symbol]['total'] += 1
            symbol_stats[pnl.symbol]['pnl'] += pnl.realized_pnl
            if pnl.realized_pnl > 0:
                symbol_stats[pnl.symbol]['wins'] += 1

        symbols = list(symbol_stats.keys())
        win_rates = [stats['wins'] / stats['total'] * 100 for stats in symbol_stats.values()]
        pnls = [float(stats['pnl']) for stats in symbol_stats.values()]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=symbols,
            y=win_rates,
            name='Win Rate (%)',
            marker_color='#3498db',
            text=[f'{wr:.1f}%' for wr in win_rates],
            textposition='outside'
        ))

        fig.update_layout(
            xaxis_title="Symbol",
            yaxis_title="Win Rate (%)",
            template='plotly_white',
            height=400
        )

        return fig

    def _create_trade_table(self, trades, pnl_results):
        """Create trade history table."""
        if not trades:
            return html.Div("No trades found")

        # Prepare data
        table_data = []
        for i, (trade, pnl) in enumerate(zip(trades[:len(pnl_results)], pnl_results)):
            table_data.append({
                'Date': trade.trade_date.strftime('%Y-%m-%d'),
                'Symbol': trade.symbol,
                'Type': trade.trade_type.value,
                'Quantity': trade.quantity,
                'Price': f'${float(trade.price):.2f}',
                'P/L': f'${float(pnl.realized_pnl):,.2f}',
                'Return': f'{float(pnl.return_percentage):.2f}%',
            })

        return dash_table.DataTable(
            data=table_data,
            columns=[{'name': col, 'id': col} for col in table_data[0].keys()],
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={
                'backgroundColor': '#34495e',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#ecf0f1'
                }
            ],
            page_size=10,
        )

    def run(self, host='127.0.0.1', port=8050, debug=True):
        """
        Run the dashboard server.

        Args:
            host: Host address
            port: Port number
            debug: Debug mode
        """
        print(f"\n📊 Starting Trade Tracker Dashboard...")
        print(f"🌐 Access at: http://{host}:{port}")
        print(f"📈 Database: {self.db.db_path}\n")

        self.app.run_server(host=host, port=port, debug=debug)


def main():
    """Run the dashboard."""
    dashboard = TradeDashboard()
    dashboard.run()


if __name__ == '__main__':
    main()
