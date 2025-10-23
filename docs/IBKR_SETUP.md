# Interactive Brokers (IBKR) Setup Guide

This guide walks you through setting up Interactive Brokers integration with the Stock & Options Trade Tracker to automatically import your trade history and sync positions.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [TWS/IB Gateway Setup](#twsib-gateway-setup)
3. [Enable API Access](#enable-api-access)
4. [Configure Connection Settings](#configure-connection-settings)
5. [Using the Dashboard Integration](#using-the-dashboard-integration)
6. [Troubleshooting](#troubleshooting)
7. [Security Best Practices](#security-best-practices)

## Prerequisites

Before you begin, ensure you have:

- An active Interactive Brokers account
- Trader Workstation (TWS) or IB Gateway installed
- The trade tracker dashboard running (`python -m trade_tracker.visualization.dashboard`)
- Python dependencies installed (see main README)

## TWS/IB Gateway Setup

### Which Should I Use?

**Trader Workstation (TWS)**
- Full-featured trading platform with GUI
- Recommended for active traders who use IB's trading interface
- Higher resource usage
- Includes all trading and analysis tools

**IB Gateway**
- Lightweight API-only interface
- Recommended if you only need API access for automated trading/data
- Lower resource usage
- No GUI trading interface

### Installation

Download from Interactive Brokers:
- TWS: https://www.interactivebrokers.com/en/trading/tws.php
- IB Gateway: https://www.interactivebrokers.com/en/trading/ibgateway-stable.php

Choose the appropriate version for your operating system.

## Enable API Access

### Step 1: Configure API Settings in TWS/Gateway

1. **Launch TWS or IB Gateway** and log in with your credentials

2. **Open API Settings:**
   - In TWS: Go to **File → Global Configuration → API → Settings**
   - In IB Gateway: Go to **Configure → Settings → API → Settings**

3. **Enable ActiveX and Socket Clients:**
   - Check the box for "Enable ActiveX and Socket Clients"
   - This allows external applications to connect via the API

4. **Configure Socket Port:**
   - **Paper Trading Account:** Port `7497` (default)
   - **Live Trading Account:** Port `7496` (default)
   - **IB Gateway:** Port `4001` (default for paper), `4000` (live)

   You can use custom ports if needed, just remember them for the dashboard configuration.

5. **Read-Only API:**
   - Check "Read-Only API" if you only want to import data without trading capabilities
   - **Recommended for safety** - prevents accidental order placement

6. **Trusted IP Addresses:**
   - Add `127.0.0.1` to the trusted IP addresses list
   - If running the dashboard on a different machine, add that IP address

7. **Master API Client ID:**
   - Leave blank or set to `0` (allows any client ID)
   - Or specify a specific client ID if you want to restrict access

8. **Click OK/Apply** to save settings

### Step 2: Restart TWS/Gateway

After changing settings, restart TWS or IB Gateway for changes to take effect.

## Configure Connection Settings

The dashboard needs three pieces of information to connect to IBKR:

### 1. Host
- **Default:** `127.0.0.1` (localhost)
- Use this if TWS/Gateway is running on the same machine as the dashboard
- If TWS/Gateway is on a different machine, use that machine's IP address

### 2. Port
Choose based on your setup:

| Setup | Port |
|-------|------|
| TWS - Paper Trading | 7497 |
| TWS - Live Trading | 7496 |
| IB Gateway - Paper Trading | 4001 |
| IB Gateway - Live Trading | 4000 |

**Recommendation:** Start with paper trading (port 7497 or 4001) to test the integration.

### 3. Client ID
- **Default:** `1`
- Each application connecting to TWS/Gateway needs a unique client ID
- Valid range: 0-999
- If you have multiple applications connecting, use different IDs (e.g., 1, 2, 3...)

## Using the Dashboard Integration

### Step 1: Launch the Dashboard

```bash
cd /path/to/stock-option-trade-tracker
python -m src.trade_tracker.visualization.dashboard
```

The dashboard will start at `http://127.0.0.1:8050`

### Step 2: Ensure TWS/Gateway is Running

Before importing, make sure:
1. TWS or IB Gateway is running
2. You're logged in to your account
3. API settings are configured (see above)

### Step 3: Configure Connection in Dashboard

Scroll down to the "🔌 Broker Integration" section:

1. **Select Broker:** Choose "Interactive Brokers (IBKR)" from dropdown
2. **Host:** Enter `127.0.0.1` (if running locally)
3. **Port:** Enter the appropriate port:
   - `7497` for TWS Paper
   - `7496` for TWS Live
   - `4001` for IB Gateway Paper
   - `4000` for IB Gateway Live
4. **Client ID:** Enter `1` (or another unique number)

### Step 4: Import Trades

Click the **"🔌 Connect & Import Trades"** button

The dashboard will:
1. Connect to TWS/Gateway
2. Request your trade history
3. Check for duplicates
4. Import new trades into the local database
5. Display results (imported count, duplicates skipped, errors)

**Note:** The first import may take a few moments. You'll see a "Connecting to IBKR..." message.

### Step 5: Sync Positions

Click the **"💼 Sync Positions"** button to sync your current open positions

This is useful for:
- Getting up-to-date position information
- Tracking unrealized P&L
- Ensuring your local database matches your broker account

### Step 6: View Import History

The "Recent Imports" table shows your last 10 import operations:
- Timestamp
- Broker name
- Number of trades imported
- Duplicates skipped
- Errors encountered

### Step 7: Refresh Dashboard Data

After importing trades, click the **"🔄 Refresh Data"** button at the top of the dashboard to reload the analytics with your newly imported trades.

## Troubleshooting

### Connection Failed: "Socket error"

**Cause:** TWS/Gateway is not running or not accepting connections

**Solutions:**
1. Verify TWS/IB Gateway is running and logged in
2. Check that API settings are enabled (see [Enable API Access](#enable-api-access))
3. Restart TWS/Gateway after changing settings
4. Verify the port number matches your configuration

### Connection Failed: "Not connected"

**Cause:** Wrong port number or host

**Solutions:**
1. Double-check your port number:
   - TWS Paper: 7497
   - TWS Live: 7496
   - IB Gateway Paper: 4001
   - IB Gateway Live: 4000
2. Verify host is `127.0.0.1` if running locally
3. Try pinging the host to ensure network connectivity

### Connection Failed: "Client ID already in use"

**Cause:** Another application is using the same client ID

**Solutions:**
1. Change the Client ID in the dashboard to a different number (e.g., 2, 3, 4...)
2. Close other applications connected to TWS/Gateway
3. Restart TWS/Gateway to reset connections

### Import Successful but No Trades Imported

**Cause:** No trades in the requested time range, or all trades already imported

**Solutions:**
1. Check the "Duplicates skipped" count - these trades are already in your database
2. Verify you have trades in your IBKR account for the time period
3. Check if you're connected to the correct account (paper vs. live)
4. Try manually placing a trade in TWS Paper to test the import

### Connection Refused: "Connection refused"

**Cause:** Firewall blocking the connection or IP not in trusted list

**Solutions:**
1. Add `127.0.0.1` to TWS/Gateway trusted IP addresses
2. Check firewall settings - allow TWS/Gateway to accept local connections
3. Temporarily disable firewall to test (then re-enable with proper rules)

### API Error: "FA customers must specify account value"

**Cause:** You have a Financial Advisor (FA) account with multiple sub-accounts

**Solutions:**
1. This is a limitation of the current integration - FA accounts are not fully supported yet
2. Contact the developer for FA account support

### Trades Import but with Wrong Data

**Cause:** Data mapping issue or IB API returning unexpected format

**Solutions:**
1. Check the import history table for error counts
2. Review the terminal/console output for detailed error messages
3. Report the issue with specific trade details (symbol, date, type)

## Security Best Practices

### 1. Use Read-Only API Mode

Enable "Read-Only API" in TWS/Gateway settings to prevent accidental order placement:
- Allows reading trade history and positions
- Blocks all order placement and modifications
- **Highly recommended** for data import only

### 2. Use Paper Trading for Testing

Always test with a paper trading account first:
- Port 7497 (TWS) or 4001 (IB Gateway)
- Verify the integration works correctly
- No risk to real funds
- Switch to live only after thorough testing

### 3. Restrict Trusted IPs

Only add necessary IP addresses to the trusted IP list:
- Add `127.0.0.1` if running locally
- Avoid `0.0.0.0` or wildcard entries
- Use specific IPs for remote connections

### 4. Use Unique Client IDs

Assign different client IDs to different applications:
- Trade Tracker: Client ID 1
- Other trading bots: Client IDs 2, 3, etc.
- Helps track which application made which request

### 5. Monitor Import History

Regularly check the import history table:
- Look for unexpected imports
- Monitor error counts
- Verify duplicate detection is working

### 6. Secure Your Database

The trade tracker stores data locally in an encrypted database:
- Keep your database password secure
- Don't share the database file
- Regularly backup your data

### 7. Keep TWS/Gateway Updated

Interactive Brokers regularly updates TWS/Gateway:
- Updates include security patches
- May include API improvements
- Check for updates monthly

## Advanced Configuration

### Custom Date Ranges (Coming Soon)

Future versions will support:
- Specifying start/end dates for imports
- Filtering by symbol
- Incremental imports (only new trades)

### Multiple Account Support (Coming Soon)

Support for importing from multiple IBKR accounts:
- Switch between accounts in the dashboard
- Separate databases for each account
- Consolidated view across accounts

### Scheduled Auto-Imports (Coming Soon)

Automatic periodic imports:
- Daily/weekly/monthly schedules
- Background import service
- Email notifications on completion

## Need Help?

If you encounter issues not covered in this guide:

1. Check the main README for general troubleshooting
2. Review the IBKR API documentation: https://interactivebrokers.github.io/tws-api/
3. Open an issue on the GitHub repository
4. Include:
   - TWS/Gateway version
   - Error messages (from dashboard and console)
   - Connection settings used (host, port, client ID)
   - Operating system

---

**Happy Trading!** 📈

Remember: Start with paper trading, enable read-only API, and always verify imports before relying on the data for real trading decisions.
