#!/usr/bin/env python3
"""
Sync transactions from the Schwab API into the local SQLite database.

Usage:
    # One-time login (opens browser):
    python bin/schwab_login.py

    # Sync since the last watermark (or since the newest DB trade on first run):
    python bin/sync_schwab_api.py

    # Sync a specific date range (start/end must be no more than 1 year apart):
    python bin/sync_schwab_api.py --start-date 2026-01-01 --end-date 2026-03-31

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
    be more than a year"). For history older than 1 year, use the CSV export
    pipeline.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
log = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'stock_trades.db')
DB_PATH = os.path.normpath(DB_PATH)

ACCOUNT_MAP_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'data', 'schwab_account_map.json'
)
ACCOUNT_MAP_PATH = os.path.normpath(ACCOUNT_MAP_PATH)

# Only process these Schwab transaction types.
# TRADE = buys/sells; RECEIVE_AND_DELIVER = option expirations/assignments.
_TRADE_TYPES = {'TRADE', 'RECEIVE_AND_DELIVER'}

# Asset types we care about (COLLECTIVE_INVESTMENT = ETFs, traded like stocks)
_EQUITY_TYPES = {'EQUITY', 'OPTION', 'COLLECTIVE_INVESTMENT'}


def load_account_map():
    if not os.path.exists(ACCOUNT_MAP_PATH):
        log.warning(
            'No account map found at %s — using auto-assigned codes. '
            'Copy data/schwab_account_map.json.example to set up your mapping.',
            ACCOUNT_MAP_PATH,
        )
        return {}
    with open(ACCOUNT_MAP_PATH) as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith('_comment')}


def parse_date(date_str):
    """Parse ISO date string from Schwab API to YYYY-MM-DD."""
    if not date_str:
        return None
    # Handle both '2024-01-15T00:00:00+0000' and '2024-01-15' formats
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        return date_str[:10]


def determine_trade_type(instrument):
    """Map Schwab instrument to our trade_type code."""
    asset_type = instrument.get('assetType', '')
    if asset_type == 'OPTION':
        put_call = instrument.get('putCall', '').upper()
        return 'C' if put_call in ('CALL', 'C') else 'P'
    # EQUITY
    return 'L'


def build_option_label(instrument):
    """
    Build the Schwab CSV-style option label stored in our DB,
    e.g. "QBTS 07/17/2026 25.00 C". Returns None if fields are missing.
    """
    underlying = instrument.get('underlyingSymbol') or ''
    exp = parse_date(instrument.get('expirationDate'))
    strike = instrument.get('strikePrice')
    put_call = (instrument.get('putCall') or '').upper()
    if not (underlying and exp and strike is not None and put_call):
        return None
    year, month, day = exp.split('-')
    pc = 'C' if put_call == 'CALL' else 'P'
    return f'{underlying} {month}/{day}/{year} {float(strike):.2f} {pc}'


def determine_action(txn, leg, asset_type):
    """
    Map a Schwab transaction + instrument leg to an ActionMapping full name.

    The API does not provide an explicit instruction field: the leg's signed
    `amount` (shares/contracts received vs delivered) plus `positionEffect`
    determine the action. Expirations/assignments arrive as RECEIVE_AND_DELIVER
    transactions identified by their description text.
    """
    desc = (txn.get('description') or '').lower()
    if txn.get('type') == 'RECEIVE_AND_DELIVER':
        if 'expiration' in desc:
            return 'Expired'
        if 'assignment' in desc or 'exercise' in desc:
            return 'Exchange or Exercise'
        if 'removal of worthless' in desc:
            # Broker removes a worthless position — economically a total-loss
            # close, same as an expiration.
            return 'Expired'
        return None

    if txn.get('type') == 'TRADE' and not float(txn.get('netAmount') or 0):
        # Zero-net "System transfer" trades move existing shares between
        # sub-accounts/internal books with no real cash-settled purchase — the
        # leg still carries a real-looking cost/price, but treating it as an
        # ordinary buy either flips the sign (cost positive on a "Buy") or
        # phantom-duplicates a position already recorded elsewhere. Skip it,
        # same as a zero-value RECEIVE_AND_DELIVER journal.
        return None

    signed_qty = float(leg.get('amount') or 0)
    if signed_qty == 0:
        return None
    if 'dividend reinvest' in desc and signed_qty > 0:
        # Reinvestment purchases must keep the CSV pipeline's RS action code —
        # mapping them to plain Buy would double-count against existing RS rows.
        return 'Reinvest Shares'
    if asset_type == 'OPTION':
        effect = (leg.get('positionEffect') or '').upper()
        if effect == 'OPENING':
            return 'Buy to Open' if signed_qty > 0 else 'Sell to Open'
        if effect == 'CLOSING':
            return 'Sell to Close' if signed_qty < 0 else 'Buy to Close'
        return 'Buy to Open' if signed_qty > 0 else 'Sell to Close'
    return 'Buy' if signed_qty > 0 else 'Sell'


def extract_trade_legs(transfer_items):
    """
    Return all equity/option legs from transferItems, ignoring cash/currency
    fee legs. Multi-leg option orders (spreads) produce multiple legs.
    """
    return [
        item for item in transfer_items
        if item.get('instrument', {}).get('assetType') in _EQUITY_TYPES
    ]


def _log_skipped_leg(txn, leg):
    """
    Log a leg that couldn't be mapped to an action, with enough detail to see
    why. Any transaction with zero net cash impact — a RECEIVE_AND_DELIVER
    sub-account journal (e.g. CASH<->MARGIN moves) or a TRADE-type "System
    transfer" — is not a real trade, so skipping it is correct and logged at
    INFO. Anything else unmapped is unexpected and stays a WARNING.
    """
    instrument = leg.get('instrument', {})
    detail = (
        f"type={txn.get('type')} desc=\"{txn.get('description', '')}\" "
        f"date={parse_date(txn.get('tradeDate') or txn.get('time'))} "
        f"subAccount={txn.get('subAccount')} netAmount={txn.get('netAmount')} | "
        f"leg: {instrument.get('symbol')} {instrument.get('assetType')} "
        f"amount={leg.get('amount')} cost={leg.get('cost')} "
        f"price={leg.get('price')} positionEffect={leg.get('positionEffect')}"
    )
    is_journal = not float(txn.get('netAmount') or 0)
    if is_journal:
        log.info('Skipping transaction %s — sub-account journal/corporate action, '
                 'not a trade (%s)', txn.get('activityId'), detail)
    else:
        log.warning('Skipping transaction %s — could not determine action (%s)',
                    txn.get('activityId'), detail)


def _looks_like_ticker(symbol):
    """
    Real Schwab equity/ETF tickers are short. Some corporate-action legs
    (mergers, reverse splits, bankruptcy conversions) report a 9-character
    CUSIP as the instrument symbol instead of a resolvable ticker — reject
    those rather than creating a garbage security for a CUSIP.
    """
    return len(symbol) <= 6


def build_transaction_record(txn, leg, account_code, leg_index=0):
    """
    Convert one instrument leg of a Schwab API transaction to our
    DatabaseInserter format. Returns None if the leg should be skipped.
    """
    instrument = leg.get('instrument', {})
    asset_type = instrument.get('assetType', '')

    action_name = determine_action(txn, leg, asset_type)
    if not action_name:
        _log_skipped_leg(txn, leg)
        return None

    trade_type = determine_trade_type(instrument)
    expiration_date = parse_date(instrument.get('expirationDate'))

    # Symbol: use underlyingSymbol for options, symbol for stocks.
    # Stock labels stay None to match the CSV pipeline's NULL labels.
    if asset_type == 'OPTION':
        symbol = instrument.get('underlyingSymbol', '')
        label = build_option_label(instrument)
        target_price = instrument.get('strikePrice')
        security_name = symbol
    else:
        symbol = instrument.get('symbol', '')
        label = None
        target_price = None
        security_name = instrument.get('description') or symbol

    if not symbol:
        log.warning('Skipping transaction with no symbol: %s', txn.get('activityId'))
        return None

    if not _looks_like_ticker(symbol):
        log.warning('Skipping transaction %s — symbol %r looks like a CUSIP, not a '
                    'ticker (likely an unmapped corporate action)',
                    txn.get('activityId'), symbol)
        return None

    if action_name in ('Expired', 'Exchange or Exercise'):
        # CSV pipeline records these on the option's expiration date with zero
        # price/amount — mirror that so the dedupe check matches. Equity events
        # (worthless-security removals) have no expiration date, so fall back
        # to the transaction date.
        trade_date = expiration_date or parse_date(txn.get('tradeDate') or txn.get('time'))
        price = 0.0
        amount = 0.0
    else:
        trade_date = parse_date(txn.get('tradeDate') or txn.get('time'))
        price = float(leg.get('price') or 0)
        # Leg cost is the signed gross amount: negative for buys, positive for
        # sells — same convention as the CSV pipeline's amount column.
        amount = float(leg.get('cost') or 0)
        if action_name == 'Reinvest Shares':
            # CSV pipeline stores RS amounts as positive — keep that convention
            amount = abs(amount)

    if not trade_date:
        log.warning('Skipping transaction with no trade date: %s', txn.get('activityId'))
        return None

    quantity = abs(float(leg.get('amount') or 0))

    return {
        'symbol': symbol.upper(),
        'action': action_name,
        'label': label,
        'trade_type': trade_type,
        'trade_date': trade_date,
        'expiration_date': expiration_date,
        'quantity': quantity,
        'price': price,
        'amount': amount,
        'target_price': target_price,
        'initial_stop_price': None,
        'projected_sell_price': None,
        'reason': '',
        'account': account_code,
        'security_name': security_name,
        'activity_id': txn.get('activityId'),
        'leg_index': leg_index,
    }


SYNC_WATERMARK_KEY = 'schwab_api_last_sync'

# Schwab's actual limit (verified against the live API): startDate/endDate must
# be no more than 1 year apart, or the request returns HTTP 400. Use 364 rather
# than 365 to leave a one-day margin for timezone/rounding.
MAX_API_WINDOW_DAYS = 364


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


def _save_watermark(db, end_date):
    with db.transaction():
        db.cursor.execute(
            'INSERT INTO config (key, value, description) VALUES (?, ?, ?) '
            'ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP',
            (SYNC_WATERMARK_KEY, end_date.isoformat(), 'Last successful Schwab API sync (UTC)'),
        )


def build_account_codes(accounts, account_map):
    """
    Resolve each account hash to its mapped single-letter code, auto-assigning
    U, V, W, ... in encounter order for any hash missing from account_map.
    """
    codes = {}
    counter = 0
    for acct in accounts:
        hash_val = acct.get('hashValue')
        if hash_val in account_map:
            codes[hash_val] = account_map[hash_val]
        else:
            code = chr(ord('U') + counter)
            counter += 1
            log.warning('No mapping for account hash %s — assigning code %s', hash_val, code)
            codes[hash_val] = code
    return codes


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
    """
    from lib.schwab_client import get_client
    from lib.db_utils import DatabaseInserter

    if end_date is None:
        end_date = datetime.now(timezone.utc)

    if start_date is not None and (end_date - start_date).days > MAX_API_WINDOW_DAYS:
        raise ValueError(
            f'Date range too wide: {(end_date - start_date).days} days requested, '
            f'Schwab caps requests at ~1 year ({MAX_API_WINDOW_DAYS} days). '
            'Split the range into multiple syncs, or use the CSV export pipeline '
            'for history beyond 1 year.'
        )

    client = get_client()
    account_map = load_account_map()

    # Fetch account hashes
    resp = client.get_account_numbers()
    resp.raise_for_status()
    accounts = resp.json()

    account_codes = build_account_codes(accounts, account_map)

    inserted = 0
    skipped_existing = 0
    skipped_invalid = 0

    symbol = symbol.upper() if symbol else None

    with DatabaseInserter(db_path=DB_PATH) as db:
        if start_date is None:
            start_date = (
                end_date - timedelta(days=MAX_API_WINDOW_DAYS) if symbol
                else _resolve_start_date(db, end_date)
            )

        for acct in accounts:
            hash_val = acct.get('hashValue')
            code = account_codes[hash_val]
            log.info('Fetching transactions for account %s (code=%s) from %s to %s%s',
                     hash_val[:8] + '...', code,
                     start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'),
                     f' (filtering to {symbol})' if symbol else '')

            resp = client.get_transactions(
                account_hash=hash_val,
                start_date=start_date,
                end_date=end_date,
                transaction_types=[
                    client.Transactions.TransactionType.TRADE,
                    client.Transactions.TransactionType.RECEIVE_AND_DELIVER,
                ],
            )
            resp.raise_for_status()
            transactions = resp.json()
            log.info('  Retrieved %d transactions', len(transactions))

            records = []
            for txn in transactions:
                if txn.get('type', '') not in _TRADE_TYPES:
                    skipped_invalid += 1
                    continue
                legs = extract_trade_legs(txn.get('transferItems', []))
                if not legs:
                    skipped_invalid += 1
                    continue
                for i, leg in enumerate(legs):
                    record = build_transaction_record(txn, leg, code, leg_index=i)
                    if record is None:
                        skipped_invalid += 1
                    elif symbol and record['symbol'] != symbol:
                        continue
                    else:
                        records.append(record)

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

        if not dry_run and not symbol:
            _save_watermark(db, end_date)

    log.info('Sync complete. Inserted: %d, Already existed: %d, Skipped invalid: %d',
             inserted, skipped_existing, skipped_invalid)


def main():
    parser = argparse.ArgumentParser(description='Sync Schwab API transactions to local DB')
    parser.add_argument('--start-date', help='Start date YYYY-MM-DD (default: since last sync watermark)')
    parser.add_argument('--end-date', help='End date YYYY-MM-DD (default: today)')
    parser.add_argument('--dry-run', action='store_true', help='Preview without inserting')
    parser.add_argument('--list-accounts', action='store_true',
                        help='Print account hashes for account map setup')
    parser.add_argument('--symbol',
                        help='Only sync this stock and its options (default date range: full '
                             '~1-year lookback, ignoring the watermark; does not advance it)')
    args = parser.parse_args()

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


if __name__ == '__main__':
    main()
