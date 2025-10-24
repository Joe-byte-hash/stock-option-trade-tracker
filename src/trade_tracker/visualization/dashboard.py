"""Interactive dashboard for trade tracking and analytics."""

import dash
from dash import dcc, html, dash_table, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
from typing import List, Dict, Any
from pathlib import Path
import tempfile

from trade_tracker.database.connection import DatabaseManager
from trade_tracker.database.repository import TradeRepository, AccountRepository
from trade_tracker.analytics.pnl import PnLCalculator
from trade_tracker.analytics.metrics import MetricsCalculator
from trade_tracker.analytics.strategy import StrategyAnalyzer
from trade_tracker.utils.export import TradeExporter
from trade_tracker.integrations.manager import IntegrationManager
from trade_tracker.integrations.ibkr import IBKRBroker
from trade_tracker.integrations.credentials import CredentialManager


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
                html.P("Click on a strategy cell to change the trading strategy for a trade.",
                      style={'textAlign': 'center', 'color': '#7f8c8d', 'fontSize': '14px'}),
                html.Div(id='trade-table'),
                html.Div(id='strategy-update-status'),  # Status messages for strategy updates
            ], style={'marginTop': '30px'}),

            # Refresh and Export Buttons
            html.Div([
                html.Button('🔄 Refresh Data', id='refresh-button', n_clicks=0,
                          style={'margin': '20px 10px 0 10px', 'padding': '10px 20px',
                                'fontSize': '16px', 'cursor': 'pointer',
                                'backgroundColor': '#3498db', 'color': 'white',
                                'border': 'none', 'borderRadius': '5px'}),
                html.Button('📊 Export to CSV', id='export-csv-button', n_clicks=0,
                          style={'margin': '20px 10px 0 10px', 'padding': '10px 20px',
                                'fontSize': '16px', 'cursor': 'pointer',
                                'backgroundColor': '#27ae60', 'color': 'white',
                                'border': 'none', 'borderRadius': '5px'}),
                html.Button('📈 Export to Excel', id='export-excel-button', n_clicks=0,
                          style={'margin': '20px 10px 0 10px', 'padding': '10px 20px',
                                'fontSize': '16px', 'cursor': 'pointer',
                                'backgroundColor': '#27ae60', 'color': 'white',
                                'border': 'none', 'borderRadius': '5px'}),
                html.Button('📅 Monthly Summary', id='export-monthly-button', n_clicks=0,
                          style={'margin': '20px 10px 0 10px', 'padding': '10px 20px',
                                'fontSize': '16px', 'cursor': 'pointer',
                                'backgroundColor': '#9b59b6', 'color': 'white',
                                'border': 'none', 'borderRadius': '5px'}),
                html.Button('🧾 Tax Report', id='export-tax-button', n_clicks=0,
                          style={'margin': '20px 10px 0 10px', 'padding': '10px 20px',
                                'fontSize': '16px', 'cursor': 'pointer',
                                'backgroundColor': '#e67e22', 'color': 'white',
                                'border': 'none', 'borderRadius': '5px'}),
            ], style={'textAlign': 'center', 'marginBottom': '30px'}),

            # Broker Import Section
            html.Hr(style={'marginTop': '40px', 'marginBottom': '30px'}),
            html.Div([
                html.H2("🔌 Broker Integration", style={'textAlign': 'center', 'color': '#2c3e50'}),

                # Broker selection and connection
                html.Div([
                    html.Div([
                        html.Label("Broker:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                        dcc.Dropdown(
                            id='broker-dropdown',
                            options=[
                                {'label': '📈 Interactive Brokers (IBKR)', 'value': 'ibkr'},
                                {'label': '🐂 Moomoo (Coming Soon)', 'value': 'moomoo', 'disabled': True},
                                {'label': '🍁 Questrade (Coming Soon)', 'value': 'questrade', 'disabled': True},
                            ],
                            value='ibkr',
                            style={'width': '300px', 'display': 'inline-block'}
                        ),
                    ], style={'marginBottom': '20px'}),

                    # IBKR Connection Settings
                    html.Div([
                        html.H4("Connection Settings", style={'marginBottom': '15px'}),
                        html.Div([
                            html.Div([
                                html.Label("Host:"),
                                dcc.Input(id='broker-host', type='text', value='127.0.0.1',
                                         style={'width': '100%', 'padding': '8px', 'marginTop': '5px'}),
                            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '20px'}),

                            html.Div([
                                html.Label("Port:"),
                                dcc.Input(id='broker-port', type='number', value=7497,
                                         style={'width': '100%', 'padding': '8px', 'marginTop': '5px'}),
                                html.Small("7497=Paper, 7496=Live TWS, 4001=Gateway",
                                          style={'color': '#7f8c8d'}),
                            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '20px'}),

                            html.Div([
                                html.Label("Client ID:"),
                                dcc.Input(id='broker-client-id', type='number', value=1,
                                         style={'width': '100%', 'padding': '8px', 'marginTop': '5px'}),
                            ], style={'width': '20%', 'display': 'inline-block'}),
                        ]),
                    ], id='broker-settings', style={'marginBottom': '20px', 'padding': '15px',
                                                     'backgroundColor': '#ecf0f1', 'borderRadius': '5px'}),

                    # Import Filters
                    html.Div([
                        html.H4("Import Filters (Optional)", style={'marginBottom': '15px'}),
                        html.Div([
                            html.Div([
                                html.Label("Start Date:"),
                                dcc.DatePickerSingle(
                                    id='import-start-date',
                                    placeholder='Select start date',
                                    date=None,
                                    display_format='YYYY-MM-DD',
                                    style={'width': '100%'}
                                ),
                                html.Small("Leave empty to import all historical trades",
                                          style={'color': '#7f8c8d', 'display': 'block', 'marginTop': '5px'}),
                            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '20px', 'verticalAlign': 'top'}),

                            html.Div([
                                html.Label("End Date:"),
                                dcc.DatePickerSingle(
                                    id='import-end-date',
                                    placeholder='Select end date',
                                    date=None,
                                    display_format='YYYY-MM-DD',
                                    style={'width': '100%'}
                                ),
                                html.Small("Leave empty to import up to today",
                                          style={'color': '#7f8c8d', 'display': 'block', 'marginTop': '5px'}),
                            ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '20px', 'verticalAlign': 'top'}),

                            html.Div([
                                html.Label("Symbol Filter:"),
                                dcc.Input(
                                    id='import-symbol-filter',
                                    type='text',
                                    placeholder='e.g., AAPL',
                                    value='',
                                    style={'width': '100%', 'padding': '8px', 'marginTop': '5px'}
                                ),
                                html.Small("Leave empty to import all symbols",
                                          style={'color': '#7f8c8d', 'display': 'block', 'marginTop': '5px'}),
                            ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'}),
                        ]),
                    ], id='import-filters', style={'marginBottom': '20px', 'padding': '15px',
                                                    'backgroundColor': '#e8f5e9', 'borderRadius': '5px'}),

                    # Import Controls
                    html.Div([
                        html.Button('🔌 Connect & Import Trades', id='import-trades-button', n_clicks=0,
                                  style={'padding': '12px 30px', 'fontSize': '16px', 'cursor': 'pointer',
                                        'backgroundColor': '#2ecc71', 'color': 'white',
                                        'border': 'none', 'borderRadius': '5px', 'marginRight': '10px'}),
                        html.Button('💼 Sync Positions', id='sync-positions-button', n_clicks=0,
                                  style={'padding': '12px 30px', 'fontSize': '16px', 'cursor': 'pointer',
                                        'backgroundColor': '#3498db', 'color': 'white',
                                        'border': 'none', 'borderRadius': '5px'}),
                    ], style={'marginTop': '20px', 'textAlign': 'center'}),

                    # Import Results
                    html.Div(id='import-results', style={'marginTop': '30px', 'padding': '15px',
                                                         'borderRadius': '5px', 'minHeight': '50px'}),

                    # Import History
                    html.Div([
                        html.H4("Recent Imports", style={'marginTop': '30px', 'marginBottom': '15px'}),
                        html.Div(id='import-history-table'),
                    ]),
                ], style={'maxWidth': '1000px', 'margin': '0 auto', 'padding': '20px'}),
            ]),

            # Strategy Performance Section
            html.Hr(style={'marginTop': '40px', 'marginBottom': '30px'}),
            html.Div([
                html.H2("🎯 Strategy Performance", style={'textAlign': 'center', 'color': '#2c3e50'}),
                html.P("Analyze which trading strategies are most profitable",
                      style={'textAlign': 'center', 'color': '#7f8c8d', 'marginBottom': '30px'}),

                html.Div([
                    # Strategy metrics cards
                    html.Div(id='strategy-metrics-cards', style={'marginBottom': '30px'}),

                    # Strategy comparison chart
                    html.Div([
                        html.H4("P/L by Strategy", style={'marginBottom': '15px'}),
                        dcc.Graph(id='strategy-pnl-chart'),
                    ], style={'marginBottom': '30px'}),

                    # Strategy performance table
                    html.Div([
                        html.H4("Detailed Strategy Breakdown", style={'marginBottom': '15px'}),
                        html.Div(id='strategy-performance-table'),
                    ]),
                ], style={'maxWidth': '1200px', 'margin': '0 auto', 'padding': '20px'}),
            ]),

            # Download components
            dcc.Download(id='download-csv'),
            dcc.Download(id='download-excel'),
            dcc.Download(id='download-monthly'),
            dcc.Download(id='download-tax'),

            # Hidden div for data storage
            dcc.Store(id='trade-data-store'),
            dcc.Store(id='pnl-data-store'),
            dcc.Interval(id='import-status-interval', interval=1000, disabled=True),
        ], style={'padding': '20px', 'fontFamily': 'Arial, sans-serif'})

    def _setup_callbacks(self):
        """Setup dashboard callbacks."""

        @self.app.callback(
            [Output('trade-data-store', 'data'),
             Output('pnl-data-store', 'data'),
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
                return {}, {}, [], empty_fig, empty_fig, empty_fig, empty_fig, html.Div("No trades found")

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

            # Store data for export callbacks
            trade_data = {'trades': all_trades, 'pnl_results': pnl_results}
            pnl_data = {'pnl_results': pnl_results, 'trades': all_trades}

            return {}, pnl_data, metrics_cards, equity_curve, pnl_dist, monthly_pnl, symbol_perf, trade_table

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
        """Create trade history table with editable strategy column."""
        if not trades:
            return html.Div("No trades found")

        # Import TradingStrategy enum for dropdown options
        from trade_tracker.models.trade import TradingStrategy

        # Prepare data
        table_data = []
        for i, (trade, pnl) in enumerate(zip(trades[:len(pnl_results)], pnl_results)):
            # Get strategy name (convert enum to readable format)
            strategy_value = trade.strategy.value if trade.strategy else "untagged"
            strategy_name = strategy_value.replace('_', ' ').title()

            table_data.append({
                'id': trade.id,  # Hidden column for updates
                'Date': trade.trade_date.strftime('%Y-%m-%d'),
                'Symbol': trade.symbol,
                'Type': trade.trade_type.value,
                'Quantity': trade.quantity,
                'Price': f'${float(trade.price):.2f}',
                'Strategy': strategy_name,
                'P/L': f'${float(pnl.realized_pnl):,.2f}',
                'Return': f'{float(pnl.return_percentage):.2f}%',
            })

        # Create dropdown options for strategy column
        strategy_options = [
            {'label': strategy.value.replace('_', ' ').title(), 'value': strategy.value}
            for strategy in TradingStrategy
        ]

        return dash_table.DataTable(
            id='trade-history-table',
            data=table_data,
            columns=[
                {'name': 'ID', 'id': 'id', 'hidden': True},  # Hidden for updates
                {'name': 'Date', 'id': 'Date', 'editable': False},
                {'name': 'Symbol', 'id': 'Symbol', 'editable': False},
                {'name': 'Type', 'id': 'Type', 'editable': False},
                {'name': 'Quantity', 'id': 'Quantity', 'editable': False},
                {'name': 'Price', 'id': 'Price', 'editable': False},
                {
                    'name': 'Strategy',
                    'id': 'Strategy',
                    'editable': True,
                    'presentation': 'dropdown'
                },
                {'name': 'P/L', 'id': 'P/L', 'editable': False},
                {'name': 'Return', 'id': 'Return', 'editable': False},
            ],
            dropdown={
                'Strategy': {
                    'options': strategy_options
                }
            },
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
            editable=True,
        )

        # Export callbacks
        @self.app.callback(
            Output('download-csv', 'data'),
            Input('export-csv-button', 'n_clicks'),
            prevent_initial_call=True
        )
        def export_csv(n_clicks):
            """Export trade history to CSV."""
            # Load data
            with self.db.get_session() as session:
                trade_repo = TradeRepository(session)
                all_trades = trade_repo.get_all()

            if not all_trades:
                return None

            # Calculate P/L
            pnl_calculator = PnLCalculator()
            pnl_results = self._calculate_pnl_for_trades(all_trades, pnl_calculator)

            # Export to temp file
            temp_dir = Path(tempfile.mkdtemp())
            output_file = temp_dir / "trade_history.csv"

            exporter = TradeExporter()
            exporter.export_trades_to_csv(all_trades, pnl_results, output_file)

            return dcc.send_file(str(output_file))

        @self.app.callback(
            Output('download-excel', 'data'),
            Input('export-excel-button', 'n_clicks'),
            prevent_initial_call=True
        )
        def export_excel(n_clicks):
            """Export trade history to Excel."""
            # Load data
            with self.db.get_session() as session:
                trade_repo = TradeRepository(session)
                all_trades = trade_repo.get_all()

            if not all_trades:
                return None

            # Calculate P/L
            pnl_calculator = PnLCalculator()
            pnl_results = self._calculate_pnl_for_trades(all_trades, pnl_calculator)

            # Export to temp file
            temp_dir = Path(tempfile.mkdtemp())
            output_file = temp_dir / "trade_history.xlsx"

            exporter = TradeExporter()
            exporter.export_trades_to_excel(all_trades, pnl_results, output_file)

            return dcc.send_file(str(output_file))

        @self.app.callback(
            Output('download-monthly', 'data'),
            Input('export-monthly-button', 'n_clicks'),
            prevent_initial_call=True
        )
        def export_monthly(n_clicks):
            """Export monthly summary to CSV."""
            # Load data
            with self.db.get_session() as session:
                trade_repo = TradeRepository(session)
                all_trades = trade_repo.get_all()

            if not all_trades:
                return None

            # Calculate P/L
            pnl_calculator = PnLCalculator()
            pnl_results = self._calculate_pnl_for_trades(all_trades, pnl_calculator)

            # Export to temp file
            temp_dir = Path(tempfile.mkdtemp())
            output_file = temp_dir / "monthly_summary.csv"

            exporter = TradeExporter()
            exporter.export_monthly_summary_to_csv(pnl_results, output_file)

            return dcc.send_file(str(output_file))

        @self.app.callback(
            Output('download-tax', 'data'),
            Input('export-tax-button', 'n_clicks'),
            prevent_initial_call=True
        )
        def export_tax(n_clicks):
            """Export tax report for current year."""
            # Load data
            with self.db.get_session() as session:
                trade_repo = TradeRepository(session)
                all_trades = trade_repo.get_all()

            if not all_trades:
                return None

            # Calculate P/L
            pnl_calculator = PnLCalculator()
            pnl_results = self._calculate_pnl_for_trades(all_trades, pnl_calculator)

            # Export to temp file
            current_year = datetime.now().year
            temp_dir = Path(tempfile.mkdtemp())
            output_file = temp_dir / f"tax_report_{current_year}.csv"

            exporter = TradeExporter()
            exporter.export_tax_report(all_trades, pnl_results, current_year, output_file)

            return dcc.send_file(str(output_file))

        # Strategy Update Callback
        @self.app.callback(
            Output('strategy-update-status', 'children'),
            Input('trade-history-table', 'data'),
            State('trade-history-table', 'data_previous'),
            prevent_initial_call=True
        )
        def update_trade_strategy(current_data, previous_data):
            """Update trade strategy when changed in table."""
            if not current_data or not previous_data:
                return ""

            # Import TradingStrategy enum
            from trade_tracker.models.trade import TradingStrategy

            # Find which row changed
            for i, (current_row, previous_row) in enumerate(zip(current_data, previous_data)):
                if current_row['Strategy'] != previous_row['Strategy']:
                    # Extract trade ID and new strategy
                    trade_id = current_row['id']
                    new_strategy_label = current_row['Strategy']

                    # Convert label back to enum value (e.g., "Day Trade" -> "day_trade")
                    new_strategy_value = new_strategy_label.lower().replace(' ', '_')

                    # Validate strategy exists
                    try:
                        new_strategy = TradingStrategy(new_strategy_value)
                    except ValueError:
                        return html.Div(f"Invalid strategy: {new_strategy_label}",
                                      style={'color': '#e74c3c', 'textAlign': 'center', 'marginTop': '10px'})

                    # Update in database
                    try:
                        with self.db.get_session() as session:
                            trade_repo = TradeRepository(session)
                            trade = trade_repo.get_by_id(trade_id)

                            if trade:
                                # Update strategy
                                trade.strategy = new_strategy
                                trade_repo.update(trade)
                                session.commit()

                                return html.Div(
                                    f"✅ Updated strategy for trade #{trade_id} to {new_strategy_label}",
                                    style={'color': '#2ecc71', 'textAlign': 'center', 'marginTop': '10px'}
                                )
                            else:
                                return html.Div(f"Trade #{trade_id} not found",
                                              style={'color': '#e74c3c', 'textAlign': 'center', 'marginTop': '10px'})
                    except Exception as e:
                        return html.Div(f"Error updating strategy: {str(e)}",
                                      style={'color': '#e74c3c', 'textAlign': 'center', 'marginTop': '10px'})

            return ""

        # Broker Import Callbacks
        @self.app.callback(
            Output('import-results', 'children'),
            [Input('import-trades-button', 'n_clicks')],
            [State('broker-host', 'value'),
             State('broker-port', 'value'),
             State('broker-client-id', 'value'),
             State('broker-dropdown', 'value'),
             State('import-start-date', 'date'),
             State('import-end-date', 'date'),
             State('import-symbol-filter', 'value')],
            prevent_initial_call=True
        )
        def import_trades(n_clicks, host, port, client_id, broker_type, start_date, end_date, symbol):
            """Import trades from broker."""
            if broker_type != 'ibkr':
                return html.Div("Only IBKR is currently supported.",
                              style={'color': '#e74c3c', 'textAlign': 'center'})

            try:
                # Create broker connection
                credentials = {
                    'host': host,
                    'port': int(port),
                    'client_id': int(client_id)
                }

                broker = IBKRBroker(credentials)

                # Show connecting message
                connecting_msg = html.Div([
                    html.Div("🔌 Connecting to IBKR...", style={'fontSize': '18px', 'marginBottom': '10px'}),
                    html.Div("Please ensure TWS or IB Gateway is running and accepting API connections.",
                            style={'color': '#7f8c8d', 'fontSize': '14px'})
                ], style={'textAlign': 'center', 'color': '#3498db'})

                try:
                    # Connect to broker
                    broker.connect()

                    # Parse filter parameters
                    start_dt = None
                    end_dt = None
                    if start_date:
                        start_dt = datetime.fromisoformat(start_date)
                    if end_date:
                        end_dt = datetime.fromisoformat(end_date)

                    # Clean up symbol filter (strip whitespace, None if empty)
                    symbol_filter = symbol.strip() if symbol else None

                    # Import trades using IntegrationManager
                    manager = IntegrationManager(db_path=str(self.db.db_path))
                    result = manager.import_trades(
                        broker,
                        account_id=1,
                        start_date=start_dt,
                        end_date=end_dt,
                        symbol=symbol_filter
                    )

                    # Disconnect
                    broker.disconnect()

                    # Format results
                    if result['success']:
                        # Build filter description
                        filter_desc = []
                        if start_dt:
                            filter_desc.append(f"From: {start_dt.strftime('%Y-%m-%d')}")
                        if end_dt:
                            filter_desc.append(f"To: {end_dt.strftime('%Y-%m-%d')}")
                        if symbol_filter:
                            filter_desc.append(f"Symbol: {symbol_filter}")

                        filter_info = html.Div(
                            f"Filters: {', '.join(filter_desc) if filter_desc else 'None (imported all)'}",
                            style={'fontSize': '14px', 'color': '#7f8c8d', 'marginBottom': '10px', 'fontStyle': 'italic'}
                        )

                        return html.Div([
                            html.H4("✅ Import Successful!", style={'color': '#27ae60', 'marginBottom': '15px'}),
                            filter_info,
                            html.Div([
                                html.Div(f"📥 Imported: {result['imported_count']} trades",
                                       style={'fontSize': '16px', 'marginBottom': '5px'}),
                                html.Div(f"🔄 Duplicates skipped: {result['duplicate_count']}",
                                       style={'fontSize': '16px', 'marginBottom': '5px'}),
                                html.Div(f"⚠️ Errors: {result['error_count']}",
                                       style={'fontSize': '16px'}),
                            ]),
                            html.Div("Click 'Refresh Data' above to see imported trades in the dashboard.",
                                   style={'marginTop': '15px', 'fontSize': '14px', 'color': '#7f8c8d',
                                         'fontStyle': 'italic'})
                        ], style={'backgroundColor': '#d5f4e6', 'padding': '20px',
                                'borderRadius': '5px', 'textAlign': 'center'})
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        return html.Div([
                            html.H4("❌ Import Failed", style={'color': '#e74c3c', 'marginBottom': '10px'}),
                            html.Div(f"Error: {error_msg}", style={'fontSize': '14px'})
                        ], style={'backgroundColor': '#fadbd8', 'padding': '20px',
                                'borderRadius': '5px', 'textAlign': 'center'})

                except Exception as e:
                    broker.disconnect()
                    return html.Div([
                        html.H4("❌ Connection Failed", style={'color': '#e74c3c', 'marginBottom': '10px'}),
                        html.Div(f"Error: {str(e)}", style={'fontSize': '14px', 'marginBottom': '10px'}),
                        html.Div("Make sure TWS/IB Gateway is running and configured to accept API connections.",
                               style={'fontSize': '12px', 'color': '#7f8c8d'})
                    ], style={'backgroundColor': '#fadbd8', 'padding': '20px',
                            'borderRadius': '5px', 'textAlign': 'center'})

            except Exception as e:
                return html.Div([
                    html.H4("❌ Error", style={'color': '#e74c3c', 'marginBottom': '10px'}),
                    html.Div(str(e), style={'fontSize': '14px'})
                ], style={'backgroundColor': '#fadbd8', 'padding': '20px',
                        'borderRadius': '5px', 'textAlign': 'center'})

        @self.app.callback(
            Output('import-results', 'children', allow_duplicate=True),
            [Input('sync-positions-button', 'n_clicks')],
            [State('broker-host', 'value'),
             State('broker-port', 'value'),
             State('broker-client-id', 'value'),
             State('broker-dropdown', 'value')],
            prevent_initial_call=True
        )
        def sync_positions(n_clicks, host, port, client_id, broker_type):
            """Sync positions from broker."""
            if broker_type != 'ibkr':
                return html.Div("Only IBKR is currently supported.",
                              style={'color': '#e74c3c', 'textAlign': 'center'})

            try:
                # Create broker connection
                credentials = {
                    'host': host,
                    'port': int(port),
                    'client_id': int(client_id)
                }

                broker = IBKRBroker(credentials)

                try:
                    # Connect to broker
                    broker.connect()

                    # Sync positions
                    manager = IntegrationManager(db_path=str(self.db.db_path))
                    result = manager.sync_positions(broker, account_id=1)

                    # Disconnect
                    broker.disconnect()

                    # Format results
                    if result['success']:
                        return html.Div([
                            html.H4("✅ Position Sync Successful!",
                                  style={'color': '#27ae60', 'marginBottom': '15px'}),
                            html.Div(f"💼 Synced: {result['synced_count']} positions",
                                   style={'fontSize': '16px'}),
                        ], style={'backgroundColor': '#d5f4e6', 'padding': '20px',
                                'borderRadius': '5px', 'textAlign': 'center'})
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        return html.Div([
                            html.H4("❌ Sync Failed", style={'color': '#e74c3c', 'marginBottom': '10px'}),
                            html.Div(f"Error: {error_msg}", style={'fontSize': '14px'})
                        ], style={'backgroundColor': '#fadbd8', 'padding': '20px',
                                'borderRadius': '5px', 'textAlign': 'center'})

                except Exception as e:
                    broker.disconnect()
                    return html.Div([
                        html.H4("❌ Connection Failed", style={'color': '#e74c3c', 'marginBottom': '10px'}),
                        html.Div(f"Error: {str(e)}", style={'fontSize': '14px'})
                    ], style={'backgroundColor': '#fadbd8', 'padding': '20px',
                            'borderRadius': '5px', 'textAlign': 'center'})

            except Exception as e:
                return html.Div([
                    html.H4("❌ Error", style={'color': '#e74c3c', 'marginBottom': '10px'}),
                    html.Div(str(e), style={'fontSize': '14px'})
                ], style={'backgroundColor': '#fadbd8', 'padding': '20px',
                        'borderRadius': '5px', 'textAlign': 'center'})

        @self.app.callback(
            Output('import-history-table', 'children'),
            [Input('import-trades-button', 'n_clicks'),
             Input('sync-positions-button', 'n_clicks')],
            prevent_initial_call=False
        )
        def update_import_history(import_clicks, sync_clicks):
            """Update import history table."""
            try:
                manager = IntegrationManager(db_path=str(self.db.db_path))
                history = manager.get_import_history(limit=10)

                if not history:
                    return html.Div("No import history yet. Import trades to see history here.",
                                  style={'textAlign': 'center', 'color': '#7f8c8d', 'fontStyle': 'italic'})

                # Create table data
                table_data = []
                for record in history:
                    table_data.append({
                        'Time': record['timestamp'][:19],  # Remove microseconds
                        'Broker': record['broker'],
                        'Imported': record['imported_count'],
                        'Duplicates': record['duplicate_count'],
                        'Errors': record['error_count']
                    })

                return dash_table.DataTable(
                    data=table_data,
                    columns=[{'name': col, 'id': col} for col in table_data[0].keys()],
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '10px',
                        'fontSize': '14px',
                    },
                    style_header={
                        'backgroundColor': '#3498db',
                        'color': 'white',
                        'fontWeight': 'bold',
                        'textAlign': 'center',
                    },
                    style_data_conditional=[
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': '#ecf0f1'
                        }
                    ],
                    page_size=10,
                )

            except Exception as e:
                return html.Div(f"Error loading history: {str(e)}",
                              style={'color': '#e74c3c', 'textAlign': 'center'})

        # Strategy Performance Callbacks
        @self.app.callback(
            [Output('strategy-metrics-cards', 'children'),
             Output('strategy-pnl-chart', 'figure'),
             Output('strategy-performance-table', 'children')],
            [Input('refresh-button', 'n_clicks')]
        )
        def update_strategy_performance(n_clicks):
            """Update strategy performance visualizations."""
            try:
                with self.db.get_session() as session:
                    trade_repo = TradeRepository(session)
                    all_trades = trade_repo.get_all()

                    if not all_trades:
                        empty_msg = html.Div("No trades available for strategy analysis",
                                           style={'textAlign': 'center', 'color': '#7f8c8d', 'padding': '50px'})
                        return empty_msg, {}, empty_msg

                    # Calculate P/L
                    pnl_calc = PnLCalculator()
                    pnl_results = []
                    for trade in all_trades:
                        if trade.asset_type.value == 'stock':
                            pnl = pnl_calc.calculate_stock_pnl([trade])
                            if pnl:
                                pnl_results.append(pnl)

                    # Analyze strategies
                    strategy_analyzer = StrategyAnalyzer()
                    strategy_results = strategy_analyzer.analyze_by_strategy(all_trades, pnl_results)

                    if not strategy_results:
                        empty_msg = html.Div("No completed trades to analyze",
                                           style={'textAlign': 'center', 'color': '#7f8c8d', 'padding': '50px'})
                        return empty_msg, {}, empty_msg

                    # Create metrics cards
                    comparison = strategy_analyzer.compare_strategies(all_trades, pnl_results)
                    cards = self._create_strategy_cards(comparison)

                    # Create P/L chart
                    chart = self._create_strategy_pnl_chart(strategy_results)

                    # Create performance table
                    table = self._create_strategy_table(strategy_results)

                    return cards, chart, table

            except Exception as e:
                error_msg = html.Div(f"Error analyzing strategies: {str(e)}",
                                   style={'color': '#e74c3c', 'textAlign': 'center', 'padding': '50px'})
                return error_msg, {}, error_msg

    def _create_strategy_cards(self, comparison: Dict[str, Any]) -> html.Div:
        """Create strategy summary cards."""
        best = comparison.get('best_strategy')
        worst = comparison.get('worst_strategy')
        most_used = comparison.get('most_used_strategy')

        cards = []

        if best:
            cards.append(html.Div([
                html.H5("🏆 Best Strategy", style={'color': '#27ae60', 'marginBottom': '10px'}),
                html.P(best['strategy_name'], style={'fontSize': '20px', 'fontWeight': 'bold'}),
                html.P(f"P/L: ${float(best['total_pnl']):.2f}", style={'fontSize': '16px'}),
                html.P(f"Win Rate: {best['win_rate']:.1f}%", style={'fontSize': '14px', 'color': '#7f8c8d'}),
            ], style={'flex': '1', 'padding': '20px', 'backgroundColor': '#d5f4e6',
                     'borderRadius': '10px', 'marginRight': '10px', 'textAlign': 'center'}))

        if worst:
            cards.append(html.Div([
                html.H5("📉 Worst Strategy", style={'color': '#e74c3c', 'marginBottom': '10px'}),
                html.P(worst['strategy_name'], style={'fontSize': '20px', 'fontWeight': 'bold'}),
                html.P(f"P/L: ${float(worst['total_pnl']):.2f}", style={'fontSize': '16px'}),
                html.P(f"Win Rate: {worst['win_rate']:.1f}%", style={'fontSize': '14px', 'color': '#7f8c8d'}),
            ], style={'flex': '1', 'padding': '20px', 'backgroundColor': '#fadbd8',
                     'borderRadius': '10px', 'marginRight': '10px', 'textAlign': 'center'}))

        if most_used:
            cards.append(html.Div([
                html.H5("📊 Most Used", style={'color': '#3498db', 'marginBottom': '10px'}),
                html.P(most_used['strategy_name'], style={'fontSize': '20px', 'fontWeight': 'bold'}),
                html.P(f"Trades: {most_used['total_trades']}", style={'fontSize': '16px'}),
                html.P(f"Win Rate: {most_used['win_rate']:.1f}%", style={'fontSize': '14px', 'color': '#7f8c8d'}),
            ], style={'flex': '1', 'padding': '20px', 'backgroundColor': '#d6eaf8',
                     'borderRadius': '10px', 'textAlign': 'center'}))

        return html.Div(cards, style={'display': 'flex', 'justifyContent': 'space-around'})

    def _create_strategy_pnl_chart(self, strategy_results: List[Dict[str, Any]]) -> go.Figure:
        """Create strategy P/L comparison bar chart."""
        strategies = [r['strategy_name'] for r in strategy_results]
        pnls = [float(r['total_pnl']) for r in strategy_results]

        colors = ['#2ecc71' if pnl > 0 else '#e74c3c' for pnl in pnls]

        fig = go.Figure(data=[
            go.Bar(
                x=strategies,
                y=pnls,
                marker_color=colors,
                text=[f"${pnl:.2f}" for pnl in pnls],
                textposition='auto',
            )
        ])

        fig.update_layout(
            title="Total P/L by Strategy",
            xaxis_title="Strategy",
            yaxis_title="P/L ($)",
            template="plotly_white",
            height=400,
            showlegend=False
        )

        return fig

    def _create_strategy_table(self, strategy_results: List[Dict[str, Any]]) -> dash_table.DataTable:
        """Create detailed strategy performance table."""
        table_data = []
        for result in strategy_results:
            table_data.append({
                'Strategy': result['strategy_name'],
                'Trades': result['total_trades'],
                'Wins': result['winning_trades'],
                'Losses': result['losing_trades'],
                'Win Rate': f"{result['win_rate']:.1f}%",
                'Total P/L': f"${float(result['total_pnl']):.2f}",
                'Avg P/L': f"${float(result['average_pnl']):.2f}",
                'Max Win': f"${float(result['max_win']):.2f}",
                'Max Loss': f"${float(result['max_loss']):.2f}",
            })

        return dash_table.DataTable(
            data=table_data,
            columns=[{'name': col, 'id': col} for col in table_data[0].keys() if table_data],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '12px',
                'fontSize': '14px',
            },
            style_header={
                'backgroundColor': '#3498db',
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center',
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#ecf0f1'
                },
                {
                    'if': {
                        'filter_query': '{Total P/L} contains "-"',
                        'column_id': 'Total P/L'
                    },
                    'color': '#e74c3c',
                    'fontWeight': 'bold'
                },
                {
                    'if': {
                        'filter_query': '{Total P/L} contains "$" && {Total P/L} !contains "-"',
                        'column_id': 'Total P/L'
                    },
                    'color': '#27ae60',
                    'fontWeight': 'bold'
                },
            ],
            page_size=15,
            sort_action='native',
            filter_action='native',
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
