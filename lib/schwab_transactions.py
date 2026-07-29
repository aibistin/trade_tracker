"""
Schwab API transaction parsing, mapping, and fetching.

Converts raw Schwab API transaction payloads into our DatabaseInserter
record format, and walks account x time-window pairs to fetch them —
shared by bin/sync_schwab_api.py (incremental sync) and
util/rebuild_trade_transactions.py (full rebuild).

Note on history: Schwab's actual limit (verified against the live API,
2026-07-07) is a maximum 1-year span between startDate and endDate per
request. Requesting a wider range returns HTTP 400. iter_windows() and
SchwabTransactionFetcher walk any longer range internally in
MAX_API_WINDOW_DAYS-sized chunks, so callers never need to split a range
themselves.
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone

log = logging.getLogger(__name__)

ACCOUNT_MAP_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'data', 'schwab_account_map.json')
)

DB_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'data', 'stock_trades.db')
)

# Only process these Schwab transaction types.
# TRADE = buys/sells; RECEIVE_AND_DELIVER = option expirations/assignments.
PROCESSED_TRANSACTION_TYPES = {'TRADE', 'RECEIVE_AND_DELIVER'}

# Asset types we care about (COLLECTIVE_INVESTMENT = ETFs, traded like stocks)
EQUITY_TYPES = {'EQUITY', 'OPTION', 'COLLECTIVE_INVESTMENT'}

SYNC_WATERMARK_KEY = 'schwab_api_last_sync'

# Schwab's actual limit (verified against the live API): startDate/endDate must
# be no more than 1 year apart, or the request returns HTTP 400. Use 364 rather
# than 365 to leave a one-day margin for timezone/rounding.
MAX_API_WINDOW_DAYS = 364


def load_account_map():
    """Load the Schwab account hash -> single-letter code mapping, or {} if unset."""
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
        if item.get('instrument', {}).get('assetType') in EQUITY_TYPES
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


def iter_windows(start_date, end_date, max_days=MAX_API_WINDOW_DAYS):
    """
    Yield sequential (window_start, window_end) pairs covering
    [start_date, end_date] in chunks no wider than max_days, so a range of
    any length can be walked through Schwab's per-request 1-year cap. A
    range already within max_days yields exactly one pair spanning the
    whole thing.
    """
    window_start = start_date
    while window_start < end_date:
        window_end = min(window_start + timedelta(days=max_days), end_date)
        yield window_start, window_end
        window_start = window_end


def _watermark_key(symbol=None):
    """Global sync watermark key, or a per-symbol variant (e.g. 'schwab_api_last_sync:AAPL')."""
    return f'{SYNC_WATERMARK_KEY}:{symbol.upper()}' if symbol else SYNC_WATERMARK_KEY


def save_watermark(db, end_date, symbol=None):
    """Upsert the sync watermark (config table) to end_date (UTC). Per-symbol if symbol is given."""
    key = _watermark_key(symbol)
    description = (
        f'Last successful Schwab API sync for {symbol.upper()} (UTC)' if symbol
        else 'Last successful Schwab API sync (UTC)'
    )
    with db.transaction():
        db.cursor.execute(
            'INSERT INTO config (key, value, description) VALUES (?, ?, ?) '
            'ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP',
            (key, end_date.isoformat(), description),
        )


def get_last_sync(db_path=None, symbol=None):
    """Read the last successful sync watermark (global, or per-symbol), or None if never synced."""
    import sqlite3
    key = _watermark_key(symbol)
    conn = sqlite3.connect(db_path or DB_PATH, timeout=10)
    try:
        row = conn.execute('SELECT value FROM config WHERE key = ?', (key,)).fetchone()
    finally:
        conn.close()
    return datetime.fromisoformat(row[0]) if row else None


def _resolve_start_date(db, end_date, symbol=None):
    """
    Pick the sync start date:
    1. Config watermark (global, or per-symbol if symbol is given) minus a
       2-day overlap for late-arriving fills (API-to-API dedupe is exact, so
       overlap is safe).
    2. Else, for a global sync, the day after the newest DB trade — CSV rows
       aggregate partial fills into one row while the API reports each fill,
       so re-fetching CSV-covered days would double-count positions. A
       per-symbol sync with no watermark yet has no equivalent signal, so it
       falls straight through to the full API window (a one-time backfill
       for that symbol).
    3. Else the full API window.
    Always capped to MAX_API_WINDOW_DAYS.
    """
    earliest = end_date - timedelta(days=MAX_API_WINDOW_DAYS)
    db.cursor.execute('SELECT value FROM config WHERE key = ?', (_watermark_key(symbol),))
    row = db.cursor.fetchone()
    if row:
        start = datetime.fromisoformat(row[0]) - timedelta(days=2)
        return max(start, earliest)

    if symbol:
        return earliest

    db.cursor.execute('SELECT MAX(substr(trade_date, 1, 10)) FROM trade_transaction')
    row = db.cursor.fetchone()
    if row and row[0]:
        start = datetime.strptime(row[0], '%Y-%m-%d').replace(tzinfo=timezone.utc) + timedelta(days=1)
        log.info('First API sync — starting after newest DB trade date %s', row[0])
    else:
        start = earliest
    return max(start, earliest)


def sync(start_date=None, end_date=None, dry_run=False, symbol=None, db_path=None):
    """
    Sync Schwab API transactions into the local SQLite database.

    symbol: if given, only sync transactions for this stock (and any options on
    it). Schwab's own `symbol` query param matches the literal instrument
    string, which for options is a padded OCC-ish code (e.g. "QBTS  260717C00
    025000") rather than the underlying ticker — so it can't be used to filter
    server-side without missing option legs. Instead we fetch normally and
    filter locally against the symbol our own mapping resolves to (underlying
    ticker for options, ticker for stocks).

    A symbol-filtered run tracks its own per-symbol watermark (see
    _resolve_start_date/save_watermark) independently of the global one, so it
    resumes from where it last left off for that symbol without touching the
    global sync's progress.

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

    with DatabaseInserter(db_path=db_path or DB_PATH) as db:
        if start_date is None:
            start_date = _resolve_start_date(db, end_date, symbol=symbol)

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
            if not dry_run:
                save_watermark(db, window_end, symbol=symbol)

    skipped_invalid = fetcher.stats['skipped_non_trade'] + fetcher.stats['skipped_invalid_leg']
    log.info('Sync complete. Inserted: %d, Already existed: %d, Skipped invalid: %d',
             inserted, skipped_existing, skipped_invalid)
    return {
        'inserted': inserted,
        'skipped_existing': skipped_existing,
        'skipped_invalid': skipped_invalid,
    }


class SchwabTransactionFetcher:
    """
    Walks Schwab transaction history across account x time-window pairs,
    turning each API leg into a database-ready record via
    build_transaction_record().

    Callers drive what happens with the results: bin/sync_schwab_api.py
    inserts as it goes and checkpoints the watermark once per window;
    util/rebuild_trade_transactions.py collects everything into one list
    before touching the database. Neither concern belongs here.
    """

    def __init__(self, client, accounts, account_map):
        self.client = client
        self.accounts = accounts
        self.account_codes = build_account_codes(accounts, account_map)
        self.stats = {'skipped_non_trade': 0, 'skipped_invalid_leg': 0}

    def fetch(self, start_date, end_date, symbol=None):
        """
        Yield (window_end, records) per time window covering
        [start_date, end_date], records pooling every account for that
        window (each record already carries its own 'account' code). If
        symbol is given, only records resolving to that ticker (underlying
        ticker for options) are kept — legs for other symbols are silently
        dropped, not counted as skipped.
        """
        symbol = symbol.upper() if symbol else None
        windows = list(iter_windows(start_date, end_date))
        if len(windows) > 1:
            log.info('Range spans %d windows of up to %d days each',
                     len(windows), MAX_API_WINDOW_DAYS)

        for window_num, (window_start, window_end) in enumerate(windows, start=1):
            if len(windows) > 1:
                log.info('=== Window %d/%d: %s to %s ===', window_num, len(windows),
                         window_start.strftime('%Y-%m-%d'), window_end.strftime('%Y-%m-%d'))

            records = []
            for acct in self.accounts:
                hash_val = acct.get('hashValue')
                code = self.account_codes[hash_val]
                records.extend(
                    self._fetch_account_window(hash_val, code, window_start, window_end, symbol)
                )

            yield window_end, records

    def _fetch_account_window(self, account_hash, account_code, window_start, window_end, symbol):
        log.info('Fetching transactions for account %s (code=%s) from %s to %s%s',
                 account_hash[:8] + '...', account_code,
                 window_start.strftime('%Y-%m-%d'), window_end.strftime('%Y-%m-%d'),
                 f' (filtering to {symbol})' if symbol else '')

        resp = self.client.get_transactions(
            account_hash=account_hash,
            start_date=window_start,
            end_date=window_end,
            transaction_types=[
                self.client.Transactions.TransactionType.TRADE,
                self.client.Transactions.TransactionType.RECEIVE_AND_DELIVER,
            ],
        )
        resp.raise_for_status()
        transactions = resp.json()
        log.info('  Retrieved %d transactions', len(transactions))

        records = []
        for txn in transactions:
            if txn.get('type', '') not in PROCESSED_TRANSACTION_TYPES:
                self.stats['skipped_non_trade'] += 1
                continue
            legs = extract_trade_legs(txn.get('transferItems', []))
            if not legs:
                self.stats['skipped_non_trade'] += 1
                continue
            for i, leg in enumerate(legs):
                record = build_transaction_record(txn, leg, account_code, leg_index=i)
                if record is None:
                    self.stats['skipped_invalid_leg'] += 1
                elif symbol and record['symbol'] != symbol:
                    continue
                else:
                    records.append(record)
        return records
