#!/usr/bin/env python3
"""
One-time schema migration: add the sync_job table.

Why: the frontend triggers Schwab syncs as background jobs (POST
/api/schwab/sync, polled via GET /api/schwab/sync/<job_id>). Job status has
to be visible to every gunicorn worker process, not just the one that
started the job, so it's tracked in SQLite rather than an in-memory dict.

Idempotent — safe to run more than once. Backs up the database first.

Usage:
    python bin/migrate_add_sync_job.py
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


def migrate(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'sync_job'")
        if cursor.fetchone():
            log.info('Already migrated — nothing to do.')
            return

        cursor.execute('''
            CREATE TABLE sync_job (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                status TEXT NOT NULL,
                started_at DATETIME NOT NULL,
                finished_at DATETIME,
                inserted INTEGER,
                skipped_existing INTEGER,
                skipped_invalid INTEGER,
                error_message TEXT
            )
        ''')
        log.info('Created table sync_job')

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
