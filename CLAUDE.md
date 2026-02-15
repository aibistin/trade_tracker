# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Python Environment Setup
```bash
source python_setup.sh            # Create pyenv venv + install requirements (gitignored, lives locally)
```

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
- **API authentication:** `X-API-KEY` header checked against `API_SECRET_KEY` env var; bypassed when `FLASK_ENV=dev`
- **Logging:** Rotating file handler (`logs/trading_app.log`, 2MB, 5 backups). Level controlled by `LOG_LEVEL` env var. JSON logging optional via `JSON_LOGGING=Y`.

### Core Library (`lib/`)
- `trading_analyzer.py` — Main analysis engine: converts transaction dicts → Trade objects, matches buys to sells, calculates P&L. Expects **lowercase dict keys** (`id`, `symbol`, `action`, etc.).
- `models/Trade.py` — `Trade` base class with `BuyTrade` and `SellTrade` subclasses. BuyTrade holds matched `sells` list. Supports field aliases: `id`↔`trade_id`, `label`↔`trade_label`.
- `models/Trades.py` — Collection class that groups trades by account (`sells_by_account` dict), separates stocks from options
- `models/TradeSummary.py` — Aggregates statistics (avg price, total P&L, share counts) from trade collections. Uses `dataclasses_json`.
- `models/ActionMapping.py` — Maps action codes (B, S, BO, SC, etc.) to descriptions and trade types. `is_buy_type_action()` / `is_sell_type_action()` for classification.
- `csv_processing_utils.py` — Parses Schwab CSV exports. Uses `logging` module (not print).
- `db_utils.py` — `DatabaseInserter` helper for bulk inserts with parameterized SQL
- `yfinance.py` — Yahoo Finance integration with `requests_cache` (SQLite-backed) and `requests_ratelimiter` (2 req/5s). File-based JSON caching (60min TTL) in `data/yfinance/`.

### Frontend (`frontend/`)
- Vue 3 + Vite + Bootstrap 5 + Axios
- **API config:** `src/config.js` reads `VITE_API_BASE_URL` env var (default: `http://localhost:5000/api`). Set via `frontend/.env` (gitignored).
- Key views: `TradeHome.vue` (symbol picker), `AllTrades.vue` (trade display), `TransactionSummary.vue` (stats)
- **Composables:**
  - `composables/useFetchTrades.js` — shared data fetching with loading/error state
  - `composables/useSymbolSearch.js` — shared symbol search/filter/dropdown logic (used by TradeHome + BSNavBarTop)
- `utils/tradeUtils.js` — `formatCurrency`, `formatValue`, `profitLossClass`, `formatAction`, `formatTradeType`, etc.
- `components/BSNavBarTop.vue` — Main navbar with symbol dropdowns for All/Open/Closed trades + search bar

### Data Flow
1. Schwab CSV → `bin/process_schwab_transactions.py` → SQLite
2. API request → `get_trade_data_for_analysis_new()` → raw transaction dicts (lowercase keys)
3. `TradingAnalyzer.analyze_trades(status, account, after_date)` → converts to Trade objects, matches buys/sells, computes P&L
4. `get_profit_loss_data_json()` → JSON-serializable dict with `stock` and `option` sections
5. JSON response → Vue frontend renders with trade tables

## Testing Patterns
- **Framework:** unittest (not pytest). No conftest.py.
- **Database:** Tests use in-memory SQLite (`sqlite:///:memory:`) with `DatabaseInserter` for test data
- **Flask routes:** Tested via `app.test_client()` with mock data inserted per test. `FLASK_ENV=testing` and `FLASK_ENV=dev` set in test setUp.
- **External APIs:** Mocked with `unittest.mock.patch()`
- **Trade models:** Tested with real-world trading scenarios (partial fills, multi-account, options)
- **Known flaky test:** `test_yfinance.test_get_stock_data` depends on live Yahoo Finance API
- **Skipped tests:** 5 `get_open_trades_*` tests are skipped pending integration with new code

## Key Conventions
- Trade types: L=Long, S=Short, C=Call, P=Put, O=Other (exercise/expiration)
- Account codes: C, R, I, O (different brokerage accounts). Validated on filtered API endpoint.
- Action codes: B=Buy, S=Sell, BO=Buy to Open, SC=Sell to Close, EE=Exchange/Exercise, EXP=Expired, RS=Reinvest Shares
- EXP and EE actions are normalized to SC (Sell to Close) internally by Trade.__init__
- Python version managed via pyenv virtualenv named "Trading" (see `.python-version`)
- `python_setup.sh` is gitignored — it auto-detects the best pyenv Python version and installs requirements
- Frontend env files (`.env`) are gitignored; defaults live in `src/config.js`

## Environment Variables
| Variable | Where | Purpose |
|---|---|---|
| `FLASK_ENV` | Backend | `dev` (skip API key), `testing` (in-memory DB), `production` (stricter logging) |
| `SECRET_KEY` | Backend | Flask session key (auto-generated if not set) |
| `API_SECRET_KEY` | Backend | Expected value for `X-API-KEY` header |
| `LOG_LEVEL` | Backend | Python logging level (default: INFO) |
| `JSON_LOGGING` | Backend | Set to `Y` for JSON-formatted log output |
| `VITE_API_BASE_URL` | Frontend | API base URL (default: `http://localhost:5000/api`) |
