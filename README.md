# Trade Tracker

Track stock and options trades made on the Schwab brokerage platform.

## Stack

- **Backend:** Python, Flask, SQLAlchemy, SQLite
- **Frontend:** Vue 3, Vite, Tailwind CSS v4, Axios
- **Data sources:** Live Schwab API sync (last year) + Schwab transaction CSV exports (older history)

## Features

- **Dashboard:** Summary cards, P&L bar chart, cumulative P&L line, win-rate trend, portfolio heatmap, and aggregated holdings — all in one view, dark trading-terminal theme
- **History page:** Closed-trade performance by symbol (wins, losses, win rate, realized P&L) with sortable columns and a totals row
- **Stock holdings:** One aggregated row per ticker; shows current price, market value, and unrealized P&L fetched from Yahoo Finance
- **Option holdings:** Grouped by underlying symbol with expand/collapse; live option prices fetched via OCC-format tickers from Yahoo Finance
- **Trade view:** All, open, or closed positions for any symbol, with per-trade P&L
- **Live pricing per trade:** Expand any open trade card to see live price, cost, market value, diff, and diff% (options use ×100 multiplier)
- **Filtering:** Filter by date, account, and asset type (stock vs option)
- **Home page:** Current holdings tables with All/Stocks/Options toggle; symbol search dropdown
- **Live Schwab API sync:** Pulls the latest transactions directly from your Schwab account (up to 1 year per request); runs automatically on startup
- **Schwab CSV import:** Process brokerage exports directly into the database for history older than 1 year

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/aibistin/trade_tracker.git
cd trade_tracker
```

### 2. Backend — Python environment

```bash
source python_setup.sh   # creates pyenv virtualenv "Trading" and installs requirements
```

### 3. Backend — Database

```bash
echo ./util/create_stock_trades.sql | sqlite3 ./data/stock_trades.db
```

### 4. Frontend

```bash
cd frontend
pnpm install
pnpm build        # production build
# or
pnpm dev          # Vite dev server with hot reload
```

### 5. Run the app

```bash
./run_dev.sh                 # syncs Schwab API, starts backend + frontend in the background, opens the browser
./run_dev.sh status          # check whether backend/frontend are running
./run_dev.sh stop            # stop backend + frontend
# or
./run_flask.sh              # Flask dev server only, on localhost:5000
# or
docker-compose up           # gunicorn on port 5002
```

`run_dev.sh start` detaches immediately — the servers keep running after the terminal closes. It opens <http://localhost:5173/dashboard> automatically and logs to `.run/backend.log` / `.run/frontend.log`; the startup Schwab sync output is also appended to `.run/schwab_sync.log`. Each start prunes empty log files and gzipped logs older than 90 days from `logs/` and `.run/`.

## Importing Schwab Data

Two complementary sources feed the same database — use both:

### Live API sync (last 1 year, automatic)

```bash
python bin/schwab_login.py       # one-time OAuth login (needs SCHWAB_API_KEY / SCHWAB_APP_SECRET in .env)
python bin/sync_schwab_api.py --list-accounts   # get account hashes, then fill in data/schwab_account_map.json
python bin/sync_schwab_api.py                   # sync latest transactions (also runs automatically via run_dev.sh)
```

Schwab caps each API request at a 1-year `startDate`↔`endDate` span. The sync script tracks its own progress (a watermark in the database) and only re-runs from where it left off, so this rarely matters day to day — it's only a limit if you pass a manual `--start-date`/`--end-date` range wider than a year.

### CSV import (historical, > 1 year old)

```bash
./bin/run_process_schwab_data.sh   # process a Schwab transaction CSV export
```

## Running Tests

### Backend (Python/unittest)

```bash
python -m unittest discover -v                                           # all tests
python -m unittest tests.test_trading_analyzer                           # single module
python -m unittest tests.test_app_routes.TestAppRoutes.test_index_route  # single test
```

### Frontend (Vitest unit tests)

```bash
cd frontend
pnpm test:unit            # run once
pnpm test:unit:watch      # watch mode
pnpm test:unit:coverage   # with coverage report
```

### Frontend (Playwright end-to-end tests)

```bash
cd frontend
npx playwright install    # first run only — installs browsers
pnpm test:e2e             # run all E2E tests
pnpm test:e2e --project=chromium  # Chromium only
pnpm test:e2e --debug     # debug mode
```

## Environment Variables

| Variable | Purpose |
|---|---|
| `FLASK_ENV` | `dev` (skip API key check), `testing` (in-memory DB), `production` |
| `API_SECRET_KEY` | Expected value of the `X-API-KEY` request header |
| `SECRET_KEY` | Flask session secret (auto-generated if unset) |
| `LOG_LEVEL` | Python logging level (default: INFO) |
| `JSON_LOGGING` | Set to `Y` for JSON-formatted log output |
| `VITE_API_BASE_URL` | Frontend API base URL (default: `http://localhost:5000/api`) |
| `SCHWAB_API_KEY` | App key from developer.schwab.com |
| `SCHWAB_APP_SECRET` | App secret from developer.schwab.com |
| `SCHWAB_CALLBACK_URL` | OAuth callback URL (default: `https://127.0.0.1:8182`) |

## License

MIT
