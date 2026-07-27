# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.
Frontend-specific guidance lives in `frontend/CLAUDE.md` (loaded automatically when working inside `frontend/`).
This file contains the current state of this project. 
The proposed new functionality can be found in `docs/PLAN.md`. This is what you need to
work on. 

## Commands

### Python Environment Setup
```bash
source python_setup.sh            # Create pyenv venv + install requirements (gitignored, lives locally)
```

### Running the App
```bash
./run_dev.sh                      # Sync Schwab API → Flask (:5000) + Vite (:5173) → opens browser at /dashboard. Detaches; terminal returns immediately.
./run_dev.sh status               # Check whether backend/frontend are running
./run_dev.sh stop                 # Stop backend + frontend
./run_flask.sh                    # Flask dev server only, on localhost:5000
```

### Tests (unittest, no pytest)
```bash
python -m unittest discover -v                                          # All tests
python -m unittest tests.test_trading_analyzer                          # Single file
python -m unittest tests.test_app_routes.TestAppRoutes.test_index_route # Single test
```

### Data Processing
```bash
./bin/run_process_schwab_data.sh  # Process Schwab transaction CSV exports (historical data > 60 days old)
python bin/schwab_login.py        # One-time OAuth login — run once before the first API sync
python bin/sync_schwab_api.py     # Pull latest transactions from the Schwab API (also runs automatically via run_dev.sh)
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
- **ORM models:** `app/models/models.py` — `Security` and `TradeTransaction` tables only. No query logic.
- **Repository layer:** `app/repositories/trade_repository.py` — all query functions (`get_current_holdings()`, `get_trade_data_for_analysis()`, etc.). `get_current_holdings()` returns `(symbol, trade_type, quantity, avg_price, cost_basis, name)` tuples, joining on both `symbol` and `trade_type` to correctly handle symbols with both stock and option positions. Every function excludes symbols from `lib.ignore_symbols.get_ignored_symbols()` (backed by `config/ignore_symbols.txt`, gitignored) — a symbol there is hidden everywhere (holdings, dashboard, history, direct symbol lookup) even if rows still exist in the DB; the sync/rebuild scripts keep ingesting it normally, so un-ignoring later needs no backfill. The two routes in `web_routes.py` that query `TradeTransaction` directly (`recent_trades`, `trades_by_symbol`) and the `/index` route apply the same filter — don't add a new symbol-listing query without it.
- **Service layer** (routes stay thin — business logic lives here):
  - `app/services/trade_service.py` — `validate_trade_update()` and `validate_positions_params()` (scope/after_date/account/asset_type request validation) shared by both route blueprints.
  - `app/services/analysis_service.py` — `analyze_symbol()` (the repository → TradingAnalyzer → JSON pipeline), `analyze_symbol_safe()` (returns None instead of raising, for cross-symbol loops), `iter_open_buy_trades()` (walks open positions in an analysis result). `analyze_symbol_safe` results are **cached** per (symbol, status): entries are validated per call against a data-version token (`MAX(id), COUNT(*)` on trade_transaction), so inserts — including from the external Schwab sync — invalidate automatically; the trade-edit routes call `clear_analysis_cache()` since field updates don't change the token; 30-min TTL backstops direct sqlite edits. Callers must treat cached results as read-only.
  - `app/services/holdings_service.py` — `build_holdings()`: full open-positions aggregation for `GET /api/holdings`, with parallel yfinance price fetching.
- **Database:** SQLite at `data/stock_trades.db`
- **API authentication:** `X-API-KEY` header checked against `API_SECRET_KEY` env var; bypassed when `FLASK_ENV=dev`
- **Logging:** Rotating file handler, 2MB, 5 backups. Filename is env-specific: `logs/trading_app_dev.log` (dev) or `logs/trading_app_production.log` (production). Level controlled by `LOG_LEVEL` env var. JSON logging optional via `JSON_LOGGING=Y`.

### Core Library (`lib/`)
- `trading_analyzer.py` — Main analysis engine: converts transaction dicts → Trade objects, matches buys to sells, calculates P&L. Expects **lowercase dict keys** (`id`, `symbol`, `action`, etc.).
- `option_utils.py` — `label_to_occ(label: str) -> str` converts a raw Schwab option label (e.g. `"UUUU 04/17/2026 23.00 C"`) to OCC format (`"UUUU260417C00023000"`) for yfinance lookups. Raises `ValueError` on malformed input.
- `models/Trade.py` — `Trade` base class with `BuyTrade` and `SellTrade` subclasses. BuyTrade holds matched `sells` list. Supports field aliases: `id`↔`trade_id`, `label`↔`trade_label`. `BuyTrade.apply_sell_trade()` rounds `applied_qty` to 4 decimal places and rounds `sell_trade.quantity` after each subtraction to prevent floating-point drift across partial fills. `BuyTrade.closed_date` is set to `sell_trade.trade_date` when `is_done` becomes `True` (guarded with `closed_date is None` so only the closing sell's date is captured).
- `models/Trades.py` — Collection class that groups trades by account (`sells_by_account` dict), separates stocks from options
- `models/TradeSummary.py` — Aggregates statistics (avg price, total P&L, share counts) from trade collections. Uses `dataclasses_json`.
- `models/ActionMapping.py` — Maps action codes (B, S, BO, SC, etc.) to descriptions and trade types. `is_buy_type_action()` / `is_sell_type_action()` for classification.
- `csv_processing_utils.py` — Parses Schwab CSV exports. Uses `logging` module (not print).
- `db_utils.py` — `DatabaseInserter` helper for bulk inserts with parameterized SQL
- `yfinance.py` — Yahoo Finance integration. File-based JSON caching (60min TTL) in `data/yfinance/`. Does **not** pass a custom session to `yf.Ticker` (yfinance requires its own `curl_cffi` session internally). `ticker_class` param allows injection for testing. Module-level helpers: `get_quote(ticker)` (info dict, `{}` on error), `extract_price(info, is_option)` (options: `lastPrice` → `regularMarketPrice` → `currentPrice`; stocks: `currentPrice` → `regularMarketPrice`), `get_market_price(ticker, is_option)`.
- `schwab_client.py` — schwab-py auth factory. `get_client()` loads the saved token (`data/schwab_token.json`); `login(interactive=False)` runs the one-time OAuth browser flow.
- `schwab_transactions.py` — Schwab API transaction parsing/mapping (`build_transaction_record()` and friends) and the `SchwabTransactionFetcher` class, which walks account × time-window pairs via `iter_windows()` and yields `(window_end, records)` per window. Shared by `bin/sync_schwab_api.py` (streaming insert, checkpoints the watermark per window) and `util/rebuild_trade_transactions.py` (collects everything before writing) — each owns its own DB-write/dedup policy on top.

### Data Flow
**The Schwab API is the sole source populating `trade_transaction` (2026-07-17 policy change).** The CSV pipeline (`bin/process_schwab_transactions.py`, `lib/csv_processing_utils.py`) is retired but left in place, unused — CSV rows carry no unique identifier (no activity id, no timestamp, date only), so they can't be reliably reconciled against API-sourced rows.
1. `bin/sync_schwab_api.py` → schwab-py `get_transactions()` → SQLite. Runs automatically at the start of `run_dev.sh`. See "Schwab API Sync" below.
2. `get_trade_data_for_analysis(symbol)` → raw transaction dicts (lowercase keys, includes `reason`, `initial_stop_price`, `projected_sell_price`)
3. `TradingAnalyzer.analyze_trades(status, account, after_date)` → converts to Trade objects, matches buys/sells, computes P&L
4. `get_profit_loss_data_json()` → JSON-serializable dict with `stock` and `option` sections
5. JSON response → Vue frontend renders with TradeCard components

### Schwab API Sync
`bin/sync_schwab_api.py` pulls transactions from the live Schwab API (unofficial `schwab-py` wrapper) into SQLite; fully idempotent via `activity_id`/`leg_index` (see "trade_transaction identity" below).
- **Auth:** `lib/schwab_client.py`. Token at `data/schwab_token.json` (gitignored, auto-refreshed). One-time setup: `python bin/schwab_login.py` (opens a browser; ~90-day token expiry — if the sync starts failing auth, run `python bin/schwab_login.py --force` to discard the stale token and log in again).
- **Account mapping:** `data/schwab_account_map.json` (gitignored) maps Schwab account hashes → single-letter account codes (C/R/I). Get hashes via `python bin/sync_schwab_api.py --list-accounts`.
- **API limitation:** Schwab caps each request's `startDate`↔`endDate` span at 1 year (verified live 2026-07-07; HTTP 400 beyond it). Both `sync()` and `util/rebuild_trade_transactions.py` (gitignored, one-off tool) walk any longer range internally in `MAX_API_WINDOW_DAYS`-sized windows via the shared `lib/schwab_transactions.SchwabTransactionFetcher` — callers never need to split a range themselves.
- **Watermark tracking:** last successful sync end-date is stored in the `config` table (key `schwab_api_last_sync`). Each run starts from `watermark - 2 days` (safe overlap; dedupe is exact).
- **Payload mapping quirks:** the API has no `instruction` field — buy/sell is derived from the leg's signed `amount` plus `positionEffect` (OPENING/CLOSING). Option `label` (e.g. `"QBTS 07/17/2026 25.00 C"`) is built from `underlyingSymbol` + `expirationDate` + `strikePrice` + `putCall` (the API's own `description` field is prose, not this format). ETFs report as `assetType: COLLECTIVE_INVESTMENT`. Expirations arrive as `RECEIVE_AND_DELIVER` transactions. Zero-net transactions (`netAmount == 0`) — sub-account journals and "System transfer" internal moves — are skipped regardless of `type`, since the leg can still carry a real-looking cost/price. A resolved `symbol` longer than 6 characters is rejected as a CUSIP (some corporate-action legs report the CUSIP instead of a ticker), not inserted as a security.
- **Flags:** `--dry-run` (preview only), `--list-accounts`, `--start-date`/`--end-date` (manual override), `--symbol SYMBOL` (sync just one stock + its options; defaults to the full 1-year lookback rather than resuming from the watermark, and never advances the watermark since it doesn't cover all symbols).
- **Known gap:** ten symbols (BE, BMY, CGRN, DE, FFIC, FSLR, MDB, TEAM, TRHC, TWLO) were opened via an Internal Transfer/Journaled Shares pair during Schwab's 2023 TD Ameritrade account migration; that source account no longer exists in the live API (confirmed by querying all 15 transaction types). Until a manual one-time re-seed (see `docs/PLANNING.md`, 2026-07-17 entry), these may show as still-open or with a negative net quantity.

### trade_transaction identity
Every row now carries `activity_id`/`leg_index` (Schwab's own transaction id + position within a multi-leg transaction), enforced by a partial unique index `WHERE activity_id IS NOT NULL`. This is the real per-row identity — a single order can fill in several legs with byte-identical symbol/quantity/price, which the old business-field uniqueness check (`symbol, action, trade_type, trade_date, quantity, price, amount, account`) couldn't tell apart, silently dropping real fills as "duplicates". `DatabaseInserter.transaction_exists()` checks `activity_id` first, falling back to the business-field match only for CSV-era rows (`activity_id IS NULL`). Schema migrated via `bin/migrate_add_activity_id.py` (idempotent, backs up the DB first).

### Trade Update API
`PATCH /api/trade/update/<id>` — updates `reason`, `initial_stop_price`, `projected_sell_price` on a `TradeTransaction`.
Server-side validation in `app/services/trade_service.py`: `reason` max 500 chars; prices must be positive floats (null clears them). Returns `422` with `fields` dict on validation failure.

### Holdings API
`GET /api/holdings` — aggregated open positions, split into `stock` and `option` sections. Each section has a `positions` list and section-level totals (`total_cost_basis`, `total_market_value`, `total_unrealized_pnl`).
- **Stocks** — one row per ticker, aggregated across all open lots. Fields: `symbol`, `name`, `trade_type`, `quantity`, `avg_cost`, `cost_basis`, `current_price`, `market_value`, `unrealized_pnl`, `pnl_pct`.
- **Options** — one row per option contract label, aggregated across lots. Same fields plus `occ_ticker` (OCC-format ticker used for yfinance). Live prices fetched via `label_to_occ()` before calling yfinance.

`GET /api/option/price?label=<schwab_label>` — fetches the live market price for a single option contract. Converts the raw Schwab label to OCC format server-side. Returns `{ price, bid, ask, occ_ticker }`. Used by the `useOptionPrice` frontend composable.

### Dashboard API
`GET /api/dashboard/summary` — cross-symbol aggregate (closed trades): `overall` stats + `by_symbol` list with `stock`, `option`, and `combined` keys per symbol.
`GET /api/dashboard/pnl_over_time?asset_type=all|stock|option` — monthly and quarterly P&L buckets (sorted by period). Both endpoints loop all traded symbols through TradingAnalyzer and skip broken symbols gracefully. Helper `_build_symbol_stats(symbol, scope)` in `api_routes.py`.

`TradeSummary` (in `lib/models/TradeSummary.py`) now includes `winning_trades_count`, `losing_trades_count`, and `batting_average`, computed from closed buy trades (`is_done=True`) at the end of `process_all_trades()`.

## Testing Patterns
- **Framework:** unittest (not pytest). No conftest.py.
- **Database:** Tests use in-memory SQLite with `DatabaseInserter` for test data. **Always create the app via `tests/helpers.py: create_test_app()`** — it passes the in-memory URI into `create_app(test_config=...)` and asserts the engine is not the file DB. Setting `app.config["SQLALCHEMY_DATABASE_URI"]` after `create_app()` returns is silently ignored (engine already bound) and tests would read/write the real `data/stock_trades.db`.
- **Flask routes:** Tested via `app.test_client()` with mock data inserted per test. `create_test_app(flask_env="dev")` bypasses the API key check; `flask_env=None` enforces it.
- **External APIs:** Mocked with `unittest.mock.patch()`
- **Trade models:** Tested with real-world trading scenarios (partial fills, multi-account, options)
- **No known flaky tests** — `test_yfinance` tests now use mocked `yfinance.Ticker` with `max_age_minutes=0` to bypass file cache; no live API calls
- **Skipped tests:** 5 `get_open_trades_*` tests are skipped pending integration with new code

## Key Conventions
- Trade types: L=Long, S=Short, C=Call, P=Put, O=Other (exercise/expiration)
- Account codes: C, R, I, O (different brokerage accounts). Validated on filtered API endpoint.
- Action codes: B=Buy, S=Sell, BO=Buy to Open, SC=Sell to Close, EE=Exchange/Exercise, EXP=Expired, RS=Reinvest Shares
- EXP and EE actions are normalized to SC (Sell to Close) internally by `Trade.__init__`
- Python version managed via pyenv virtualenv named "Trading" (see `.python-version`)
- `python_setup.sh` is gitignored — it auto-detects the best pyenv Python version and installs requirements

## Environment Variables
| Variable | Where | Purpose |
|---|---|---|
| `FLASK_ENV` | Backend | `dev` (skip API key), `testing` (in-memory DB), `production` (stricter logging) |
| `SECRET_KEY` | Backend | Flask session key (auto-generated if not set) |
| `API_SECRET_KEY` | Backend | Expected value for `X-API-KEY` header |
| `LOG_LEVEL` | Backend | Python logging level (default: INFO) |
| `JSON_LOGGING` | Backend | Set to `Y` for JSON-formatted log output |
| `VITE_API_BASE_URL` | Frontend | API base URL (default: `http://localhost:5000/api`) — see `frontend/CLAUDE.md` |
| `SCHWAB_API_KEY` | Backend | App key from developer.schwab.com — required for API sync |
| `SCHWAB_APP_SECRET` | Backend | App secret from developer.schwab.com — required for API sync |
| `SCHWAB_CALLBACK_URL` | Backend | OAuth callback URL registered with the app (default: `https://127.0.0.1:8182`) |
