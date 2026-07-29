"""
Tests for app/services/sync_service.py — background Schwab sync jobs.

Uses a real temp-file SQLite DB for the sync_job table (matches how
get_job_status/start_sync open their own sqlite3 connections — a :memory:
DatabaseInserter wouldn't be visible to them). lib.schwab_transactions.sync
is mocked throughout so no real Schwab API/network call is ever made.
"""
import os
import sqlite3
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from app.services import sync_service

SCHEMA = """
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
);
"""


class TestSyncService(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        conn = sqlite3.connect(self.db_path)
        conn.executescript(SCHEMA)
        conn.commit()
        conn.close()
        self.addCleanup(os.remove, self.db_path)

    def _wait_for_job(self, job_id, timeout=2):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            job = sync_service.get_job_status(job_id, db_path=self.db_path)
            if job['status'] != 'running':
                return job
            time.sleep(0.01)
        self.fail(f'Job {job_id} did not finish within {timeout}s')

    def test_start_sync_runs_job_to_success(self):
        with patch.object(sync_service, 'sync', return_value={
            'inserted': 3, 'skipped_existing': 1, 'skipped_invalid': 0,
        }) as mock_sync:
            job_id = sync_service.start_sync(db_path=self.db_path)
            job = self._wait_for_job(job_id)

        mock_sync.assert_called_once_with(symbol=None, db_path=self.db_path)
        self.assertEqual(job['status'], 'success')
        self.assertEqual(job['inserted'], 3)
        self.assertEqual(job['skipped_existing'], 1)
        self.assertIsNone(job['symbol'])
        self.assertIsNotNone(job['finished_at'])

    def test_start_sync_with_symbol_uppercases_and_scopes_the_job(self):
        with patch.object(sync_service, 'sync', return_value={
            'inserted': 0, 'skipped_existing': 0, 'skipped_invalid': 0,
        }) as mock_sync:
            job_id = sync_service.start_sync(symbol='aapl', db_path=self.db_path)
            job = self._wait_for_job(job_id)

        mock_sync.assert_called_once_with(symbol='AAPL', db_path=self.db_path)
        self.assertEqual(job['symbol'], 'AAPL')

    def test_failed_sync_records_error_status_and_message(self):
        with patch.object(sync_service, 'sync', side_effect=RuntimeError('token expired')):
            job_id = sync_service.start_sync(db_path=self.db_path)
            job = self._wait_for_job(job_id)

        self.assertEqual(job['status'], 'error')
        self.assertIn('token expired', job['error_message'])
        self.assertIsNone(job['inserted'])

    def test_duplicate_global_sync_returns_the_running_jobs_id(self):
        # sync() blocks until released, so the first job stays 'running' long
        # enough for a second start_sync() call to see it and reuse its id.
        release = threading.Event()

        def slow_sync(**kwargs):
            release.wait(timeout=2)
            return {'inserted': 0, 'skipped_existing': 0, 'skipped_invalid': 0}

        with patch.object(sync_service, 'sync', side_effect=slow_sync):
            job_id_1 = sync_service.start_sync(db_path=self.db_path)
            job_id_2 = sync_service.start_sync(db_path=self.db_path)
            release.set()
            self._wait_for_job(job_id_1)

        self.assertEqual(job_id_1, job_id_2)

    def test_different_symbol_scopes_do_not_block_each_other(self):
        release = threading.Event()

        def slow_sync(**kwargs):
            release.wait(timeout=2)
            return {'inserted': 0, 'skipped_existing': 0, 'skipped_invalid': 0}

        with patch.object(sync_service, 'sync', side_effect=slow_sync):
            job_aapl = sync_service.start_sync(symbol='AAPL', db_path=self.db_path)
            job_msft = sync_service.start_sync(symbol='MSFT', db_path=self.db_path)
            release.set()
            self._wait_for_job(job_aapl)
            self._wait_for_job(job_msft)

        self.assertNotEqual(job_aapl, job_msft)

    def test_symbol_sync_does_not_block_a_concurrent_global_sync(self):
        release = threading.Event()

        def slow_sync(**kwargs):
            release.wait(timeout=2)
            return {'inserted': 0, 'skipped_existing': 0, 'skipped_invalid': 0}

        with patch.object(sync_service, 'sync', side_effect=slow_sync):
            job_symbol = sync_service.start_sync(symbol='AAPL', db_path=self.db_path)
            job_global = sync_service.start_sync(db_path=self.db_path)
            release.set()
            self._wait_for_job(job_symbol)
            self._wait_for_job(job_global)

        self.assertNotEqual(job_symbol, job_global)

    def test_get_job_status_unknown_id_returns_none(self):
        self.assertIsNone(sync_service.get_job_status(999, db_path=self.db_path))


if __name__ == '__main__':
    unittest.main()
