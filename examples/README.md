# Trade Tracker Examples

This directory contains comprehensive examples demonstrating how to use the Trade Tracker system.

## Examples Overview

### 1. Basic Usage (`basic_usage.py`)

Complete walkthrough of core functionality:
- Setting up encrypted database
- Creating trading accounts
- Recording stock trades
- Recording option trades
- Calculating P/L for individual trades
- Querying trades from database
- Basic portfolio metrics

**Run:**
```bash
python examples/basic_usage.py
```

### 2. Encryption & Security (`encryption_example.py`)

Demonstrates encryption features:
- Generating random encryption keys
- Password-based key derivation (PBKDF2)
- Encrypting and decrypting data
- Secure key storage with proper permissions
- Protection against wrong key access
- Binary data encryption

**Run:**
```bash
python examples/encryption_example.py
```

### 3. Advanced Portfolio Analysis (`portfolio_analysis.py`)

Comprehensive portfolio analytics:
- Creating sample trading portfolio
- Individual trade P/L analysis
- Win rate and profit factor calculations
- Time period analysis (daily, weekly, monthly, yearly)
- Maximum drawdown calculation
- Sharpe ratio (risk-adjusted returns)
- Equity curve visualization

**Run:**
```bash
python examples/portfolio_analysis.py
```

## Output Examples

### Basic Usage Output
```
✓ Database created at data/trades.db
✓ Created account: My Interactive Brokers Account (ID: 1)
✓ Created buy trade: AAPL x100 @ $150.50
✓ Created sell trade: AAPL x100 @ $165.75

📊 Stock Trade P/L Analysis:
  Symbol: AAPL
  Cost Basis: $15,051.00
  Proceeds: $16,574.00
  Realized P/L: $1,523.00
  Return: 10.12%
  Holding Period: 14 days

📈 Portfolio Metrics:
  Total Trades: 2
  Winning Trades: 2
  Win Rate: 100.00%
  💰 Total P/L: $5,023.00
```

### Portfolio Analysis Output
```
Symbol   Entry      Exit       P/L          Return     Days
------------------------------------------------------------
AAPL     $150       $165       $  1,498.00     9.99%   10     ✓
MSFT     $300       $320       $    998.00     6.65%   15     ✓
GOOGL    $140       $155       $    448.00    10.66%   15     ✓

📊 Trade Metrics:
  Total Trades: 5
  Winners: 3 (60.00%)
  Win Rate: 60.00%
  Profit Factor: 2.26

📉 Maximum Drawdown: 1.27%
📊 Sharpe Ratio: 2.51 (Excellent)
```

## Prerequisites

Make sure you have installed the package:

```bash
# From the project root
pip install -e .
```

## Directory Structure

```
examples/
├── README.md                 # This file
├── basic_usage.py           # Basic functionality
├── encryption_example.py    # Security features
└── portfolio_analysis.py    # Advanced analytics
```

## Next Steps

After running these examples, you can:

1. **Customize for your trades**: Modify `basic_usage.py` with your actual trade data
2. **Integrate with brokers**: Use the API integration modules (IBKR, Moomoo, Questrade)
3. **Build visualizations**: Create charts using the analytics data
4. **Export data**: Generate reports for tax purposes or analysis

## Key Concepts Demonstrated

### Database Management
- SQLite with SQLAlchemy ORM
- Encrypted data storage
- Relationship mapping
- CRUD operations

### Trade Tracking
- Stock trades (buy/sell)
- Option trades (calls/puts)
- Partial position closes
- Commission tracking

### Analytics
- Realized P/L calculations
- Unrealized P/L for open positions
- Win rate and trade statistics
- Time period aggregations
- Risk metrics (drawdown, Sharpe ratio)

### Security
- AES-256-GCM encryption
- PBKDF2 key derivation
- Secure file permissions
- Authentication tags

## Troubleshooting

### Import Errors
If you get import errors, make sure to set PYTHONPATH:
```bash
export PYTHONPATH=/path/to/stock-option-trade-tracker/src:$PYTHONPATH
```

### Database Location
Examples create the database in `data/trades.db`. The directory is created automatically.

### Encryption Keys
Encryption examples store keys in `config/` directory with restricted permissions (0600).

## Further Reading

- Main README: `../README.md`
- API Documentation: `../docs/`
- Test Suite: `../tests/`

## Questions or Issues?

Check the main repository README for support information.
