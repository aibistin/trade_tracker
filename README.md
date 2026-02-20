# Trade Tracker

Track stock and options trades made on the Schwab brokerage platform.

## Stack

- **Backend:** Python, Flask, SQLAlchemy, SQLite
- **Frontend:** Vue 3, Vite, Bootstrap 5, Axios
- **Data source:** Schwab transaction CSV exports

## Features

- **Home page:** Current stock and option holdings tables with All/Stocks/Options filter toggle; symbol search dropdown
- **Trade view:** All, open, or closed positions for any symbol, with per-trade P&L
- **Filtering:** Filter by date, account, and asset type (stock vs option)
- **Transaction detail:** Price, quantity, profit/loss, and percent P&L per trade
- **Schwab CSV import:** Process brokerage exports directly into the database

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
./run_flask.sh              # Flask dev server on localhost:5000
# or
docker-compose up           # gunicorn on port 5002
```

Open <http://localhost:5000> in a browser.

## Import Schwab Data

```bash
./bin/run_process_schwab_data.sh   # process a Schwab transaction CSV export
```

## Running Tests

```bash
python -m unittest discover -v                                           # all tests
python -m unittest tests.test_trading_analyzer                           # single module
python -m unittest tests.test_app_routes.TestAppRoutes.test_index_route  # single test
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

## License

MIT
