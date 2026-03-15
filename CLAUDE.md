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

### Production Systemd Services
Service files live in `util/`. After editing, copy to `/etc/systemd/system/` and reload:
```bash
sudo cp util/trade_tracker.service /etc/systemd/system/
sudo cp util/trade_tracker_front.service /etc/systemd/system/
sudo systemctl daemon-reload

sudo systemctl start trade_tracker        # Flask/gunicorn backend on port 3000
sudo systemctl start trade_tracker_front  # Vite preview frontend on port 4173
sudo systemctl status trade_tracker
sudo systemctl status trade_tracker_front
journalctl -u trade_tracker -f            # Real-time backend logs
journalctl -u trade_tracker_front -f      # Real-time frontend logs
```
- **`util/trade_tracker.service`** — runs `gunicorn --bind 127.0.0.1:3000` with `FLASK_ENV=production`
- **`util/trade_tracker_front.service`** — runs `pnpm run preview` (Vite preview, `strictPort: true` on 4173)
- Production frontend is built with `pnpm build` (from `frontend/`), which picks up `frontend/.env.production` setting `VITE_API_BASE_URL=http://localhost:3000/api`
- Dev frontend (`pnpm dev`) uses the default `src/config.js` URL (`http://localhost:5000/api`)

## Architecture

**Flask backend + Vue 3 frontend + SQLite database**

### Backend (Python/Flask)
- **Entry point:** `trading.py` → `app/__init__.py` (`create_app()` factory pattern)
- **Routes split into two blueprints:**
  - `app/routes/web_routes.py` — HTML template rendering (Jinja2)
  - `app/routes/api_routes.py` — JSON API endpoints under `/api` prefix
- **ORM models:** `app/models/models.py` — `Security` and `TradeTransaction` tables, plus query helpers like `get_trade_data_for_analysis_new()`. `get_current_holdings()` returns `(symbol, trade_type, quantity, avg_price, cost_basis, name)` tuples, joining on both `symbol` and `trade_type` to correctly handle symbols with both stock and option positions. `get_current_holdings_symbols()` deduplicates so each symbol appears once.
- **Database:** SQLite at `data/stock_trades.db`
- **API authentication:** `X-API-KEY` header checked against `API_SECRET_KEY` env var; bypassed when `FLASK_ENV=dev`
- **Logging:** Rotating file handler, 2MB, 5 backups. Filename is env-specific: `logs/trading_app_dev.log` (dev) or `logs/trading_app_production.log` (production). Level controlled by `LOG_LEVEL` env var. JSON logging optional via `JSON_LOGGING=Y`.

### Core Library (`lib/`)
- `trading_analyzer.py` — Main analysis engine: converts transaction dicts → Trade objects, matches buys to sells, calculates P&L. Expects **lowercase dict keys** (`id`, `symbol`, `action`, etc.).
- `models/Trade.py` — `Trade` base class with `BuyTrade` and `SellTrade` subclasses. BuyTrade holds matched `sells` list. Supports field aliases: `id`↔`trade_id`, `label`↔`trade_label`. `BuyTrade.apply_sell_trade()` rounds `applied_qty` to 4 decimal places and rounds `sell_trade.quantity` after each subtraction to prevent floating-point drift across partial fills. `BuyTrade.closed_date` is set to `sell_trade.trade_date` when `is_done` becomes `True` (guarded with `closed_date is None` so only the closing sell's date is captured).
- `models/Trades.py` — Collection class that groups trades by account (`sells_by_account` dict), separates stocks from options
- `models/TradeSummary.py` — Aggregates statistics (avg price, total P&L, share counts) from trade collections. Uses `dataclasses_json`.
- `models/ActionMapping.py` — Maps action codes (B, S, BO, SC, etc.) to descriptions and trade types. `is_buy_type_action()` / `is_sell_type_action()` for classification.
- `csv_processing_utils.py` — Parses Schwab CSV exports. Uses `logging` module (not print).
- `db_utils.py` — `DatabaseInserter` helper for bulk inserts with parameterized SQL
- `yfinance.py` — Yahoo Finance integration. File-based JSON caching (60min TTL) in `data/yfinance/`. Does **not** pass a custom session to `yf.Ticker` (yfinance requires its own `curl_cffi` session internally). `ticker_class` param allows injection for testing.

### Frontend (`frontend/`)
- Vue 3 + Vite + Bootstrap 5 + Axios
- **API config:** `src/config.js` reads `VITE_API_BASE_URL` env var (default: `http://localhost:5000/api`). Set via `frontend/.env` (gitignored).
- Key views: `TradeHome.vue` (symbol search + current stock/option holdings tables with All/Stocks/Options filter toggle), `AllTrades.vue` (trade display), `TransactionSummary.vue` (stats)
- **Composables:**
  - `composables/useFetchTrades.js` — shared data fetching with loading/error state
  - `composables/useSymbolSearch.js` — shared symbol search/filter/dropdown logic (used by TradeHome + BSNavBarTop)
- `utils/tradeUtils.js` — `formatCurrency` (standard `-$x.xx`, no accounting parentheses), `formatValue`, `profitLossClass`, `formatTradeType`, etc.
- `components/BSNavBarTop.vue` — Main navbar with symbol dropdowns, All/Open/Closed scope toggle, and Stock/Option/All asset type toggle. Scope and asset type toggles are hidden on the home page.
- `components/TradeCard.vue` — Card-based buy trade display. Flex layout with labeled groups (Opened/Closed dates, Qty@Price=Cost, Qty Sold/Proceeds, P/L/P/L%). Left accent border by trade type. Expandable detail panel shows: matched sells (div-based grid rows), metrics bar (Live Price for open trades only, Stop, Target, Reason), and edit form for `reason`/`initial_stop_price`/`projected_sell_price`. Edit form calls `PATCH /api/trade/update/<id>`.

### Data Flow
1. Schwab CSV → `bin/process_schwab_transactions.py` → SQLite
2. API request → `get_trade_data_for_analysis_new()` → raw transaction dicts (lowercase keys, includes `reason`, `initial_stop_price`, `projected_sell_price`)
3. `TradingAnalyzer.analyze_trades(status, account, after_date)` → converts to Trade objects, matches buys/sells, computes P&L
4. `get_profit_loss_data_json()` → JSON-serializable dict with `stock` and `option` sections
5. JSON response → Vue frontend renders with TradeCard components

### Trade Update API
`PATCH /api/trade/update/<id>` — updates `reason`, `initial_stop_price`, `projected_sell_price` on a `TradeTransaction`.
Server-side validation: `reason` max 500 chars; prices must be positive floats (null clears them). Returns `422` with `fields` dict on validation failure.

## Testing Patterns
- **Framework:** unittest (not pytest). No conftest.py.
- **Database:** Tests use in-memory SQLite (`sqlite:///:memory:`) with `DatabaseInserter` for test data
- **Flask routes:** Tested via `app.test_client()` with mock data inserted per test. `FLASK_ENV=testing` and `FLASK_ENV=dev` set in test setUp.
- **External APIs:** Mocked with `unittest.mock.patch()`
- **Trade models:** Tested with real-world trading scenarios (partial fills, multi-account, options)
- **No known flaky tests** — `test_yfinance` tests now use mocked `yfinance.Ticker` with `max_age_minutes=0` to bypass file cache; no live API calls
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
