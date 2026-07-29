# app/services/sync_service.py
"""
Background Schwab sync jobs, triggered from the UI (POST /api/schwab/sync).

Job status lives in the sync_job table rather than an in-process dict:
production runs gunicorn with multiple worker processes, and a dict in one
worker's memory would be invisible to the request that later polls for the
job's status if it lands on a different worker.
"""
import logging
import sqlite3
import threading
from datetime import datetime, timezone

from lib.schwab_transactions import DB_PATH, sync

log = logging.getLogger(__name__)


def _connect(db_path):
    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def _run_job(job_id, symbol, db_path):
    conn = _connect(db_path)
    try:
        result = sync(symbol=symbol, db_path=db_path)
        conn.execute(
            "UPDATE sync_job SET status = 'success', finished_at = ?, inserted = ?, "
            'skipped_existing = ?, skipped_invalid = ? WHERE id = ?',
            (
                datetime.now(timezone.utc).isoformat(),
                result['inserted'],
                result['skipped_existing'],
                result['skipped_invalid'],
                job_id,
            ),
        )
        conn.commit()
    except Exception as exc:
        log.exception('Schwab sync job %s failed', job_id)
        conn.execute(
            "UPDATE sync_job SET status = 'error', finished_at = ?, error_message = ? WHERE id = ?",
            (datetime.now(timezone.utc).isoformat(), str(exc), job_id),
        )
        conn.commit()
    finally:
        conn.close()


def start_sync(symbol=None, db_path=None):
    """
    Start a background Schwab sync (global if symbol is None, else scoped to
    that symbol) and return its job_id.

    If a job for the same scope is already running, its job_id is returned
    instead of starting a duplicate — checked against the sync_job table
    (not in-process state) so it holds across gunicorn's worker processes.
    Two requests landing on different workers within the same instant could
    both pass this check and start a duplicate sync; harmless here since
    sync() dedupes inserts by activity_id and watermark saves are idempotent,
    just wasted API calls — not worth a stricter lock for a personal app.
    """
    db_path = db_path or DB_PATH
    symbol = symbol.upper() if symbol else None

    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT id FROM sync_job WHERE status = 'running' AND symbol IS ? "
            'ORDER BY id DESC LIMIT 1',
            (symbol,),
        ).fetchone()
        if row:
            return row['id']

        cursor = conn.execute(
            'INSERT INTO sync_job (symbol, status, started_at) VALUES (?, ?, ?)',
            (symbol, 'running', datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        job_id = cursor.lastrowid
    finally:
        conn.close()

    threading.Thread(target=_run_job, args=(job_id, symbol, db_path), daemon=True).start()
    return job_id


def get_job_status(job_id, db_path=None):
    """Return the sync_job row as a dict, or None if job_id doesn't exist."""
    conn = _connect(db_path or DB_PATH)
    try:
        row = conn.execute('SELECT * FROM sync_job WHERE id = ?', (job_id,)).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None
