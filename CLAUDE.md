# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Running the App
```bash
./run_flask.sh                    # Flask dev server on localhost:5000
```

### Frontend (from frontend/ directory)
```bash
pnpm install                      # Install dependencies
pnpm dev                          # Vite dev server
pnpm build                        # Production build
pnpm lint                         # ESLint with auto-fix
pnpm test:e2e                     # Playwright end-to-end tests
```

### Tests (unittest, no pytest)
```bash
python -m unittest discover -v                                          # All tests
python -m unittest tests.test_trading_analyzer                          # Single file
python -m unittest tests.test_app_routes.TestAppRoutes.test_index_route # Single test
```

### Data Processing
```bash
./bin/run_process_schwab_data.sh  # Process Schwab transaction CSV exports
```

### Docker
```bash
docker-compose up                 # Runs on port 5002 with gunicorn
```

## Architecture

**Flask backend + Vue 3 frontend + SQLite database**

### Backend (Python/Flask)
- **Entry point:** `trading.py` → `app/__init__.py` (`create_app()` factory pattern)
- **Routes split into two blueprints:**
  - `app/routes/web_routes.py` — HTML template rendering (Jinja2)
  - `app/routes/api_routes.py` — JSON API endpoints under `/api` prefix
- **ORM models:** `app/models/models.py` — `Security` and `TradeTransaction` tables, plus query helpers like `get_trade_data_for_analysis_new()`
- **Database:** SQLite at `data/stock_trades.db`

### Core Library (`lib/`)
- `trading_analyzer.py` — Main analysis engine: converts transaction dicts → Trade objects, matches buys to sells, calculates P&L
- `models/Trade.py` — `Trade` base dataclass with `BuyTrade` and `SellTrade` subclasses. BuyTrade holds matched sell_trades list.
- `models/Trades.py` — Collection class that groups trades by account, separates stocks from options
- `models/TradeSummary.py` — Aggregates statistics (avg price, total P&L, share counts) from trade collections
- `models/ActionMapping.py` — Maps action codes (B, S, BO, SC, etc.) to descriptions and trade types
- `csv_processing_utils.py` — Parses Schwab CSV exports
- `db_utils.py` — `DatabaseInserter` helper for bulk inserts
- `yfinance.py` — Yahoo Finance integration with file-based caching (60min TTL) and rate limiting

### Frontend (`frontend/`)
- Vue 3 + Vite + Bootstrap 5 + Axios
- Key views: `TradeHome.vue` (symbol picker), `AllTrades.vue` (trade display), `TransactionSummary.vue` (stats)
- `composables/useFetchTrades.js` — shared data fetching logic
- `utils/tradeUtils.js` — formatting and styling helpers

### Data Flow
1. Schwab CSV → `bin/process_schwab_transactions.py` → SQLite
2. API request → `get_trade_data_for_analysis_new()` → raw transaction dicts
3. `TradingAnalyzer.analyze_trades(status)` → converts to Trade objects, matches buys/sells, computes P&L
4. JSON response → Vue frontend renders with trade tables

## Testing Patterns
- **Framework:** unittest (not pytest). No conftest.py.
- **Database:** Tests use in-memory SQLite (`sqlite:///:memory:`) with `DatabaseInserter` for test data
- **Flask routes:** Tested via `app.test_client()` with mock data inserted per test
- **External APIs:** Mocked with `unittest.mock.patch()`
- **Trade models:** Tested with real-world trading scenarios (partial fills, multi-account, options)

## Key Conventions
- Trade types: L=Long, S=Short, C=Call, P=Put
- Account codes: C, R, I, O (different brokerage accounts)
- Action codes: B=Buy, S=Sell, BO=Buy to Open, SC=Sell to Close, etc.
- Python 3.12 (managed via pyenv, see `.python-version`)
