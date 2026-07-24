#!/usr/bin/env python3
"""
One-time seed: insert reconstructed opening buy lots for positions whose
original acquisition predates what the Schwab API can return.

Ten symbols (BE, BMY, CGRN, DE, FFIC, FSLR, MDB, TEAM, TWLO, and formerly
TRHC — now in config/ignore_symbols.txt instead) were opened via an Internal
Transfer/Journaled Shares pair during Schwab's 2023 TD Ameritrade account
migration. That source account no longer exists anywhere in the live API
(confirmed by querying all 15 Schwab transaction types), so the rebuild in
util/rebuild_trade_transactions.py couldn't recover their true cost basis.

This script reads config/schwab_may_2023_stock_transfer_adjustments.json —
one reconstructed opening buy per position, with the real historical
acquisition date/price rather than the mechanical transfer date — and
inserts each as an ordinary Buy via DatabaseInserter, using the same
activity_id/leg_index identity as API-sourced rows so it's idempotent and
safe to re-run.

Usage:
    python bin/seed_transfer_adjustments.py [--dry-run]
"""
import argparse
import json
import logging
import os
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

DB_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'data', 'stock_trades.db')
)
ADJUSTMENTS_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'config',
                 'schwab_may_2023_stock_transfer_adjustments.json')
)


def load_adjustments(path=ADJUSTMENTS_PATH):
    with open(path) as f:
        records = json.load(f)
    for record in records:
        missing = [f for f in ('symbol', 'quantity', 'account', 'price', 'trade_date',
                                'activity_id', 'action', 'trade_type') if record.get(f) is None]
        if missing:
            raise ValueError(f'Adjustment record for {record.get("symbol")} missing: {missing}')
    return records


def build_record(adjustment):
    quantity = float(adjustment['quantity'])
    price = float(adjustment['price'])
    return {
        'symbol': adjustment['symbol'].upper(),
        'action': adjustment['action'],
        'label': None,
        'trade_type': adjustment['trade_type'],
        'trade_date': adjustment['trade_date'],
        'expiration_date': None,
        'quantity': quantity,
        'price': price,
        'amount': -round(quantity * price, 2),
        'target_price': None,
        'initial_stop_price': None,
        'projected_sell_price': None,
        'reason': 'Reconstructed opening lot — pre-dates the 2023 TDA account '
                  'migration transfer, unreachable via the Schwab API.',
        'account': adjustment['account'],
        'activity_id': int(adjustment['activity_id']),
        'leg_index': 0,
        'security_name': adjustment['symbol'].upper(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true', help='Preview only, no changes')
    args = parser.parse_args()

    from lib.db_utils import DatabaseInserter

    adjustments = load_adjustments()
    log.info('Loaded %d adjustment record(s) from %s', len(adjustments), ADJUSTMENTS_PATH)

    if args.dry_run:
        for adjustment in adjustments:
            record = build_record(adjustment)
            log.info('[DRY RUN] Would insert: %s %s qty=%s price=%s account=%s activity_id=%s',
                      record['trade_date'], record['symbol'], record['quantity'],
                      record['price'], record['account'], record['activity_id'])
        return

    backup_path = f'{DB_PATH}.bak-seed-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    shutil.copy2(DB_PATH, backup_path)
    log.info('Backed up database to %s', backup_path)

    inserted = 0
    skipped_existing = 0
    with DatabaseInserter(db_path=DB_PATH) as db:
        for adjustment in adjustments:
            record = build_record(adjustment)
            db.insert_security({'symbol': record['symbol'], 'name': record['security_name']})
            if db.transaction_exists(record):
                skipped_existing += 1
                log.info('Already seeded: %s %s', record['symbol'], record['trade_date'])
                continue
            db.insert_transaction(record)
            inserted += 1
            log.info('Inserted: %s %s qty=%s price=%s account=%s',
                      record['trade_date'], record['symbol'], record['quantity'],
                      record['price'], record['account'])

    log.info('Seed complete. Inserted: %d, Already present (skipped): %d', inserted, skipped_existing)


if __name__ == '__main__':
    main()
