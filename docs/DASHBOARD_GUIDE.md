# Dashboard User Guide

## Overview

The Trade Tracker Dashboard provides an interactive web interface for visualizing your trading performance, analyzing P/L, and reviewing trade history.

## Quick Start

### Launch the Dashboard

```bash
# With demo data
python examples/dashboard_demo.py

# With your own database
python -c "from trade_tracker.visualization.dashboard import TradeDashboard; TradeDashboard('path/to/your/trades.db').run()"
```

The dashboard will be available at: **http://127.0.0.1:8050**

## Dashboard Components

### 1. Metrics Cards

At the top of the dashboard, you'll see key performance indicators:

- **Total P/L**: Overall profit/loss across all trades
- **Win Rate**: Percentage of winning trades
- **Total Trades**: Number of completed trade pairs
- **Profit Factor**: Ratio of gross profit to gross loss
- **Average Win**: Mean profit from winning trades

**Color Coding:**
- Green: Positive P/L
- Red: Negative P/L
- Blue: Informational metrics

### 2. Portfolio Equity Curve

**Location:** Top-left chart

**Description:** Shows how your portfolio value has changed over time.

**Features:**
- Line chart with area fill
- Hover to see exact equity at any point
- Starting from $100,000 initial capital (configurable)
- Tracks cumulative P/L

**Use Case:** Identify growth trends and periods of drawdown

### 3. P/L Distribution

**Location:** Top-right chart

**Description:** Histogram showing the distribution of your wins and losses.

**Features:**
- Green bars: Winning trades
- Red bars: Losing trades
- X-axis: P/L amount in dollars
- Y-axis: Number of trades

**Use Case:** Understand the range and frequency of your gains and losses

### 4. Monthly P/L Chart

**Location:** Bottom-left chart

**Description:** Bar chart showing monthly profit and loss.

**Features:**
- One bar per month
- Green bars: Profitable months
- Red bars: Losing months
- Hover for exact P/L amount
- Shows last 12 months (or all available)

**Use Case:** Track monthly performance trends

### 5. Win Rate by Symbol

**Location:** Bottom-right chart

**Description:** Shows win rate percentage for each traded symbol.

**Features:**
- Blue bars showing win rate (0-100%)
- Labels on top of each bar
- Sorted by symbol name
- Includes both stocks and options

**Use Case:** Identify which symbols you trade most successfully

### 6. Trade History Table

**Location:** Bottom of dashboard

**Description:** Detailed table of all your trades with sortable columns.

**Columns:**
- **Date**: Trade execution date
- **Symbol**: Stock or option symbol
- **Type**: Buy/Sell (or Buy to Open/Sell to Close for options)
- **Quantity**: Number of shares/contracts
- **Price**: Execution price
- **P/L**: Realized profit/loss
- **Return**: Percentage return

**Features:**
- Pagination (10 trades per page)
- Sortable by clicking column headers
- Alternating row colors for readability

## Dashboard Controls

### Refresh Button

Click the **🔄 Refresh Data** button to reload all data from the database.

**When to use:**
- After adding new trades manually
- After importing trades from a broker
- To see updated analytics

## Data Flow

```
Database (trades.db)
    ↓
Load all trades
    ↓
Calculate P/L for each trade pair
    ↓
Compute portfolio metrics
    ↓
Generate visualizations
    ↓
Display on dashboard
```

## Customization

### Change Port

```python
from trade_tracker.visualization.dashboard import TradeDashboard

dashboard = TradeDashboard()
dashboard.run(host='127.0.0.1', port=8080)  # Change port
```

### Use Different Database

```python
dashboard = TradeDashboard(db_path='path/to/your/trades.db')
dashboard.run()
```

### Disable Debug Mode

```python
dashboard.run(debug=False)  # Production mode
```

## Chart Interactions

All charts support:

- **Zoom**: Click and drag to zoom into a region
- **Pan**: Shift + click and drag to pan
- **Reset**: Double-click to reset view
- **Hover**: Hover over data points for details
- **Legend**: Click legend items to show/hide data series

## Performance Tips

1. **Pagination**: Trade history table shows 10 records at a time for better performance
2. **Refresh**: Click refresh only when needed; dashboard auto-loads on start
3. **Database Size**: Dashboard performs well with thousands of trades
4. **Browser**: Use Chrome, Firefox, or Safari for best performance

## Troubleshooting

### Dashboard Won't Start

**Error:** Port already in use

**Solution:**
```python
dashboard.run(port=8051)  # Use different port
```

### No Data Showing

**Problem:** Dashboard shows "No trade data available"

**Solutions:**
1. Check database path is correct
2. Verify trades exist: `sqlite3 data/trades.db "SELECT COUNT(*) FROM trades;"`
3. Run `python examples/dashboard_demo.py` to create sample data

### Charts Not Displaying

**Problem:** Empty charts or error messages

**Solutions:**
1. Ensure trades have matching buy/sell pairs
2. Check trade dates are valid
3. Verify P/L calculations are not failing

## Example Workflow

### Daily Trading Routine

1. **Morning**: Review overnight P/L on dashboard
2. **During Day**: Execute trades via your broker
3. **Evening**:
   - Import trades to database
   - Click refresh button
   - Review updated metrics
   - Analyze daily performance

### Weekly Review

1. Check **Monthly P/L Chart** for weekly trends
2. Review **Win Rate by Symbol** to identify best performers
3. Examine **Equity Curve** for drawdown periods
4. Use **Trade History Table** to review individual trades

### Monthly Analysis

1. Review full **Monthly P/L Chart**
2. Calculate Sharpe ratio (coming soon in dashboard)
3. Export data for detailed analysis
4. Adjust trading strategy based on metrics

## Data Security

- Dashboard runs **locally only** (127.0.0.1)
- **No data sent to external servers**
- Database remains **encrypted at rest**
- Close browser tab to stop viewing

## Advanced Features

### Keyboard Shortcuts

- **F5** or **Ctrl+R**: Refresh browser (not same as data refresh)
- **Ctrl+Shift+I**: Open browser developer tools
- **Esc**: Exit fullscreen mode (if charts are expanded)

### Export Charts

Right-click any chart and select:
- **Download plot as PNG**
- Save for reports or presentations

### URL Parameters

Access specific views:
- `http://127.0.0.1:8050/` - Full dashboard

## Future Enhancements

Coming soon:
- [ ] Real-time price updates
- [ ] Advanced filtering (date range, symbol)
- [ ] Compare multiple symbols side-by-side
- [ ] Export to CSV/Excel
- [ ] Custom color themes
- [ ] Mobile-responsive design
- [ ] Trade notes/annotations
- [ ] Performance benchmarking

## Support

For issues or questions:
- Check the main README: `../README.md`
- Review example code: `../examples/dashboard_demo.py`
- Report bugs on GitHub

## Summary

The Trade Tracker Dashboard provides:
- ✅ Real-time portfolio analytics
- ✅ Interactive visualizations
- ✅ Comprehensive trade history
- ✅ Easy-to-understand metrics
- ✅ Local and secure
- ✅ Fast and responsive

**Start trading smarter with visual insights!** 📊
