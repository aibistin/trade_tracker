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

    # Sync just one stock (and its options) — defaults to the full ~1-year
    # lookback window regardless of the watermark; combine with --start-date/
    # --end-date for a narrower range. Does not advance the sync watermark.
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
from datetime import datetime, timedelta, timezone
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

from lib.schwab_transactions import (
    MAX_API_WINDOW_DAYS,
    SYNC_WATERMARK_KEY,
    SchwabTransactionFetcher,
    load_account_map,
    save_watermark,
)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'stock_trades.db')
DB_PATH = os.path.normpath(DB_PATH)


def _resolve_start_date(db, end_date):
    """
    Pick the sync start date:
    1. Config watermark minus a 2-day overlap for late-arriving fills
       (API-to-API dedupe is exact, so overlap is safe).
    2. Else the day after the newest DB trade — CSV rows aggregate partial
       fills into one row while the API reports each fill, so re-fetching
       CSV-covered days would double-count positions.
    3. Else the full API window.
    Always capped to MAX_API_WINDOW_DAYS.
    """
    earliest = end_date - timedelta(days=MAX_API_WINDOW_DAYS)
    db.cursor.execute('SELECT value FROM config WHERE key = ?', (SYNC_WATERMARK_KEY,))
    row = db.cursor.fetchone()
    if row:
        start = datetime.fromisoformat(row[0]) - timedelta(days=2)
    else:
        db.cursor.execute('SELECT MAX(substr(trade_date, 1, 10)) FROM trade_transaction')
        row = db.cursor.fetchone()
        if row and row[0]:
            start = datetime.strptime(row[0], '%Y-%m-%d').replace(tzinfo=timezone.utc) + timedelta(days=1)
            log.info('First API sync — starting after newest DB trade date %s', row[0])
        else:
            start = earliest
    return max(start, earliest)


def list_accounts(client):
    """Print account hashes and numbers to help build the account map."""
    resp = client.get_account_numbers()
    resp.raise_for_status()
    accounts = resp.json()
    print('\nAccount hashes (use these in data/schwab_account_map.json):')
    for acct in accounts:
        print(f"  Hash: {acct.get('hashValue')}  →  Account: {acct.get('accountNumber')}")
    print()


def sync(start_date=None, end_date=None, dry_run=False, symbol=None):
    """
    symbol: if given, only sync transactions for this stock (and any options on
    it). Schwab's own `symbol` query param matches the literal instrument
    string, which for options is a padded OCC-ish code (e.g. "QBTS  260717C00
    025000") rather than the underlying ticker — so it can't be used to filter
    server-side without missing option legs. Instead we fetch normally and
    filter locally against the symbol our own mapping resolves to (underlying
    ticker for options, ticker for stocks).

    A symbol-filtered run does not cover all symbols, so it never advances the
    sync watermark and defaults to the full lookback window rather than
    resuming from it (an explicit --start-date/--end-date still narrows it).

    A range wider than Schwab's ~1-year per-request cap (e.g. a full manual
    backfill from account inception) is walked internally in
    MAX_API_WINDOW_DAYS-sized chunks by SchwabTransactionFetcher — callers
    never need to split a long range themselves.
    """
    from lib.schwab_client import get_client
    from lib.db_utils import DatabaseInserter

    if end_date is None:
        end_date = datetime.now(timezone.utc)

    client = get_client()
    account_map = load_account_map()

    # Fetch account hashes
    resp = client.get_account_numbers()
    resp.raise_for_status()
    accounts = resp.json()

    fetcher = SchwabTransactionFetcher(client, accounts, account_map)

    inserted = 0
    skipped_existing = 0

    with DatabaseInserter(db_path=DB_PATH) as db:
        if start_date is None:
            start_date = (
                end_date - timedelta(days=MAX_API_WINDOW_DAYS) if symbol
                else _resolve_start_date(db, end_date)
            )

        for window_end, records in fetcher.fetch(start_date, end_date, symbol=symbol):
            for record in records:
                if dry_run:
                    log.info('[DRY RUN] Would insert: %s %s %s qty=%s price=%s',
                             record['trade_date'], record['action'],
                             record['symbol'], record['quantity'], record['price'])
                    inserted += 1
                    continue

                # Ensure security exists
                db.insert_security({
                    'symbol': record['symbol'],
                    'name': record.get('security_name') or record['symbol'],
                })

                if db.transaction_exists(record):
                    skipped_existing += 1
                    log.debug('Already exists: %s %s %s', record['trade_date'],
                              record['symbol'], record['action'])
                    continue

                db.insert_transaction(record)
                inserted += 1
                log.info('Inserted: %s %s %s qty=%s',
                         record['trade_date'], record['action'],
                         record['symbol'], record['quantity'])

            # Checkpoint after every window (not just the last) so an
            # interrupted multi-window backfill resumes near where it left
            # off instead of re-fetching from the original start date.
            if not dry_run and not symbol:
                save_watermark(db, window_end)

    skipped_invalid = fetcher.stats['skipped_non_trade'] + fetcher.stats['skipped_invalid_leg']
    log.info('Sync complete. Inserted: %d, Already existed: %d, Skipped invalid: %d',
             inserted, skipped_existing, skipped_invalid)


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
                        help='Only sync this stock and its options (default date range: full '
                             '~1-year lookback, ignoring the watermark; does not advance it)')
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

        sync(start_date=start, end_date=end, dry_run=args.dry_run, symbol=args.symbol)
    except Exception as exc:
        _report_fatal_error(exc)
        sys.exit(1)


if __name__ == '__main__':
    main()
