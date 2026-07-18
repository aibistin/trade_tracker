#!/usr/bin/env python3
"""
One-time schema migration: add activity_id/leg_index to trade_transaction and
replace the business-field unique indexes with an activity_id-based one.

Why: the old unique indexes (symbol, action, trade_type, trade_date, quantity,
price, amount, account) can't tell apart two genuinely separate Schwab fills
that happen to share the same price/quantity on the same day (a single order
filling in identical-sized chunks) — the second fill gets silently treated as
"already exists" and dropped. Schwab's own activity_id (plus leg_index, for
the rare multi-leg transaction) is the real per-row identity.

Idempotent — safe to run more than once; each step checks current schema
state first. Backs up the database before making any change.

Usage:
    python bin/migrate_add_activity_id.py
"""
import logging
import os
import shutil
import sqlite3
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

DB_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'data', 'stock_trades.db')
)

OLD_INDEXES = (
    'unique_trade_transaction_option_index',
    'unique_trade_transaction_stock_index',
)
NEW_INDEX = 'unique_trade_transaction_activity_index'


def _columns(cursor):
    cursor.execute("PRAGMA table_info(trade_transaction)")
    return {row[1] for row in cursor.fetchall()}


def _indexes(cursor):
    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'index'")
    return {row[0] for row in cursor.fetchall()}


def migrate(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        columns = _columns(cursor)
        indexes = _indexes(cursor)

        if 'activity_id' in columns and NEW_INDEX in indexes:
            log.info('Already migrated — nothing to do.')
            return

        if 'activity_id' not in columns:
            cursor.execute('ALTER TABLE trade_transaction ADD COLUMN activity_id INTEGER')
            log.info('Added column activity_id')
        if 'leg_index' not in columns:
            cursor.execute('ALTER TABLE trade_transaction ADD COLUMN leg_index INTEGER')
            log.info('Added column leg_index')

        indexes = _indexes(cursor)
        for index_name in OLD_INDEXES:
            if index_name in indexes:
                cursor.execute(f'DROP INDEX {index_name}')
                log.info('Dropped index %s', index_name)

        if NEW_INDEX not in indexes:
            cursor.execute(
                f'CREATE UNIQUE INDEX {NEW_INDEX} '
                'ON trade_transaction (activity_id, leg_index) '
                'WHERE activity_id IS NOT NULL'
            )
            log.info('Created index %s', NEW_INDEX)

        conn.commit()
        log.info('Migration complete.')
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def main():
    if not os.path.exists(DB_PATH):
        log.error('Database not found at %s', DB_PATH)
        return
    backup_path = f'{DB_PATH}.bak-migrate-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    shutil.copy2(DB_PATH, backup_path)
    log.info('Backed up database to %s', backup_path)
    migrate()


if __name__ == '__main__':
    main()
