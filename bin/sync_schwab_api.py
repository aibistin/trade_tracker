#!/usr/bin/env python3
"""
Sync transactions from the Schwab API into the local SQLite database.

Usage:
    # One-time login (opens browser):
    python bin/schwab_login.py

    # Sync since the last watermark (or since the newest DB trade on first run):
    python bin/sync_schwab_api.py

    # Sync a specific date range — any length works; ranges over Schwab's
    # ~1-year per-request cap are walked internally in <1-year windows:
    python bin/sync_schwab_api.py --start-date 2026-01-01 --end-date 2026-03-31
    python bin/sync_schwab_api.py --start-date 2015-01-01 --end-date 2026-07-23

    # Sync just one stock (and its options) — resumes from that symbol's own
    # watermark, or does a full ~1-year lookback the first time it's synced.
    python bin/sync_schwab_api.py --symbol AAPL

    # Preview without inserting:
    python bin/sync_schwab_api.py --dry-run

    # List account hashes to build data/schwab_account_map.json:
    python bin/sync_schwab_api.py --list-accounts

Environment variables:
    SCHWAB_API_KEY      — App key from developer.schwab.com
    SCHWAB_APP_SECRET   — App secret from developer.schwab.com
    SCHWAB_CALLBACK_URL — Callback URL registered with your app (default: https://127.0.0.1:8182)

Account mapping:
    Copy data/schwab_account_map.json.example to data/schwab_account_map.json
    and fill in your account hashes with single-letter codes (C, R, I, O).
    If no mapping exists, accounts are labeled U1, U2, ... in insertion order.

Note on history:
    Verified directly against the live API (2026-07-07): Schwab's actual limit
    is a maximum 1-year span between startDate and endDate per request — not the
    60 days suggested by schwab-py's default-argument docstring. Requesting a
    range over 1 year returns HTTP 400 ("difference between the dates must not
    be more than a year"). This script walks any longer range internally in
    <1-year windows (see lib.schwab_transactions.iter_windows), so
    --start-date/--end-date accept any span without the caller needing to
    split it up.
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

from authlib.integrations.base_client.errors import OAuthError

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

LOGS_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOGS_DIR, 'sync_schwab_api.log')

_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
_file_handler = RotatingFileHandler(LOG_PATH, maxBytes=2 * 1024 * 1024, backupCount=5)
_file_handler.setFormatter(_formatter)
_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_formatter)

logging.basicConfig(level=logging.INFO, handlers=[_file_handler, _console_handler])
log = logging.getLogger(__name__)

# Full tracebacks (authlib/httpx internals) are noise on the terminal — send
# them to the log file only. A separate, non-propagating logger lets us do
# that without also silencing normal console output from `log`.
_diagnostics_log = logging.getLogger(f'{__name__}.diagnostics')
_diagnostics_log.setLevel(logging.ERROR)
_diagnostics_log.addHandler(_file_handler)
_diagnostics_log.propagate = False


def _report_fatal_error(exc):
    """
    Log the full traceback to file only, then print a short, actionable
    message to the terminal. Raw authlib/httpx tracebacks bury their one
    useful line (e.g. the OAuth error_description) at the very bottom.
    """
    _diagnostics_log.error('Sync failed', exc_info=True)

    if isinstance(exc, OAuthError) or 'invalid_grant' in str(exc):
        friendly = (
            'Schwab login has expired or been revoked. Fix:\n'
            '  python bin/schwab_login.py --force'
        )
    else:
        friendly = f'Sync failed: {exc}'

    log.error('%s\n(Full error details logged to %s)', friendly, LOG_PATH)

from lib.schwab_transactions import sync

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'stock_trades.db')
DB_PATH = os.path.normpath(DB_PATH)


def list_accounts(client):
    """Print account hashes and numbers to help build the account map."""
    resp = client.get_account_numbers()
    resp.raise_for_status()
    accounts = resp.json()
    print('\nAccount hashes (use these in data/schwab_account_map.json):')
    for acct in accounts:
        print(f"  Hash: {acct.get('hashValue')}  →  Account: {acct.get('accountNumber')}")
    print()


def main():
    parser = argparse.ArgumentParser(description='Sync Schwab API transactions to local DB')
    parser.add_argument('--start-date',
                        help='Start date YYYY-MM-DD (default: since last sync watermark). '
                             'Any span works — ranges over ~1 year are walked internally '
                             'in <1-year windows.')
    parser.add_argument('--end-date', help='End date YYYY-MM-DD (default: today)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without inserting')
    parser.add_argument('--list-accounts', action='store_true',
                        help='Print account hashes for account map setup')
    parser.add_argument('--symbol',
                        help='Only sync this stock and its options, resuming from that '
                             'symbol\'s own watermark (default date range on first run: '
                             'full ~1-year lookback)')
    args = parser.parse_args()

    try:
        if args.list_accounts:
            from lib.schwab_client import get_client
            list_accounts(get_client())
            return

        start = None
        end = None
        if args.start_date:
            start = datetime.strptime(args.start_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        if args.end_date:
            end = datetime.strptime(args.end_date, '%Y-%m-%d').replace(tzinfo=timezone.utc)

        sync(start_date=start, end_date=end, dry_run=args.dry_run, symbol=args.symbol, db_path=DB_PATH)
    except Exception as exc:
        _report_fatal_error(exc)
        sys.exit(1)


if __name__ == '__main__':
    main()
