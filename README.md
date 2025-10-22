# Stock & Options Trade Tracker

A comprehensive stock and options trade tracking software with encrypted local database, broker integrations, and advanced analytics dashboard for traders.

## Features

### Core Functionality
- **Trade Tracking**: Track stock and option trades with full details
  - Stocks: Buy/sell with commission tracking
  - Options: Calls/puts with strike, expiry, and Greeks
  - Support for complex option strategies

- **Encrypted Local Database**:
  - AES-256-GCM encryption for all trade data
  - Password-based key derivation (PBKDF2)
  - No third-party access to your sensitive trading data

- **P/L Analytics**:
  - Per-trade profit/loss calculations
  - Maximum drawdown analysis
  - Daily, weekly, quarterly, and yearly P/L
  - Percentage and absolute dollar returns

- **Position Management**:
  - Real-time position tracking
  - Long and short positions
  - Unrealized P/L calculation
  - Position history

### Visualization Dashboard
- Interactive charts powered by Plotly/Dash
- Entry/exit points on daily/weekly charts
- P/L trends over time
- Win rate and other performance metrics
- Drawdown visualization

### Broker Integrations (Read-Only)
- **Interactive Brokers (IBKR)**: Sync trades automatically
- **Moomoo**: Import trade history
- **Questrade**: Read account data
- **Security**: Read-only access, credentials encrypted locally

## Installation

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Setup

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/stock-option-trade-tracker.git
cd stock-option-trade-tracker
```

2. **Create a virtual environment** (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Install in development mode**:
```bash
pip install -e .
```

## Quick Start

### 1. Initialize Encrypted Database

```python
from trade_tracker.database.encryption import DatabaseEncryption
from trade_tracker.database.connection import DatabaseManager

# Generate encryption key (store this securely!)
key = DatabaseEncryption.generate_key()
DatabaseEncryption.save_key(key, "path/to/secure/location/.key")

# Or derive from password
password = "your_strong_password"
salt = os.urandom(16)  # Store this
key = DatabaseEncryption.derive_key_from_password(password, salt)
```

### 2. Track Your First Trade

```python
from trade_tracker.models.trade import StockTrade
from datetime import datetime

# Create a stock trade
trade = StockTrade(
    symbol="AAPL",
    trade_type="buy",
    quantity=100,
    price=150.50,
    commission=1.00,
    trade_date=datetime.now()
)

print(f"Total cost: ${trade.total_cost}")
```

### 3. Track Options

```python
from trade_tracker.models.trade import OptionTrade
from datetime import date

# Create an option trade
option = OptionTrade(
    symbol="AAPL",
    trade_type="buy_to_open",
    quantity=10,
    price=5.50,
    strike=155.00,
    expiry=date(2024, 3, 15),
    option_type="call",
    commission=6.50,
    trade_date=datetime.now()
)

print(f"Total cost: ${option.total_cost}")
```

## Project Structure

```
stock-option-trade-tracker/
├── src/
│   └── trade_tracker/
│       ├── models/              # Data models (Trade, Account, Position)
│       ├── database/            # Encrypted database layer
│       ├── analytics/           # P/L and metrics calculators
│       ├── visualization/       # Dashboard and charts
│       ├── integrations/        # Broker API integrations
│       └── utils/               # Utility functions
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── conftest.py              # Pytest configuration
├── docs/                        # Documentation
├── data/                        # Data storage (gitignored)
├── config/                      # Configuration files
├── requirements.txt             # Python dependencies
├── pyproject.toml              # Project metadata
└── README.md                    # This file
```

## Development

### Testing

This project follows **Test-Driven Development (TDD)** principles.

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=trade_tracker --cov-report=html
```

Run specific test file:
```bash
pytest tests/unit/test_models.py -v
```

### Code Quality

Format code with Black:
```bash
black src/ tests/
```

Sort imports with isort:
```bash
isort src/ tests/
```

Type checking with mypy:
```bash
mypy src/
```

## Security

### Data Encryption
- All trade data is encrypted at rest using AES-256-GCM
- Encryption keys are never stored in the codebase
- Use password-based key derivation for user-friendly security
- Keys can be stored in secure key files with restricted permissions (0600)

### Broker API Security
- All broker integrations are **read-only**
- API credentials are encrypted in the local database
- No data is sent to third parties
- You maintain full control of your trading data

### Best Practices
1. **Never commit** your encryption keys or API credentials
2. Store keys in secure locations outside the repository
3. Use strong passwords for key derivation
4. Regularly backup your encrypted database
5. Keep dependencies updated for security patches

## Configuration

Create a `.env` file in the project root:

```env
# Database
DB_PATH=./data/trades.db
DB_KEY_PATH=./config/.db_encryption.key

# Broker API Keys (encrypted at rest)
IBKR_ACCOUNT=
IBKR_API_KEY=

MOOMOO_ACCOUNT=
MOOMOO_API_KEY=

QUESTRADE_ACCOUNT=
QUESTRADE_API_KEY=

# Dashboard
DASHBOARD_PORT=8050
DASHBOARD_HOST=localhost
```

## Roadmap

- [x] Core data models (Trade, Account, Position)
- [x] Encrypted database layer
- [x] Test-driven development setup
- [ ] Database connection and ORM
- [ ] P/L calculation engine
- [ ] Analytics module (drawdown, metrics)
- [ ] Interactive dashboard
- [ ] IBKR integration
- [ ] Moomoo integration
- [ ] Questrade integration
- [ ] Advanced charting (entry/exit visualization)
- [ ] Export to CSV/Excel
- [ ] Tax reporting features
- [ ] Mobile app (future)

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes (TDD approach)
4. Ensure all tests pass (`pytest`)
5. Format code (`black src/ tests/`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Disclaimer

This software is for educational and personal use only. Not financial advice.
Trading stocks and options involves risk. Past performance does not guarantee future results.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check the documentation in `/docs`
- Review existing issues and discussions

## Acknowledgments

- Built with Python, FastAPI, Plotly, and SQLAlchemy
- Encryption powered by the `cryptography` library
- Testing with pytest
- Inspired by the trading community

---

**Happy Trading!** 📈
