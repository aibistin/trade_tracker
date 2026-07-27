import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from authlib.integrations.base_client.errors import OAuthError

from bin.sync_schwab_api import (
    main,
    sync,
    _report_fatal_error,
    _resolve_start_date,
)
from lib.db_utils import DatabaseInserter
from lib.schwab_transactions import MAX_API_WINDOW_DAYS, SYNC_WATERMARK_KEY, iter_windows, save_watermark

SCHEMA = """
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT,
    description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE trade_transaction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    action TEXT NOT NULL,
    label TEXT,
    trade_type TEXT,
    trade_date DATETIME NOT NULL,
    expiration_date DATETIME,
    reason TEXT,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    amount REAL NOT NULL,
    target_price REAL,
    initial_stop_price REAL,
    projected_sell_price REAL,
    account TEXT NOT NULL,
    activity_id INTEGER,
    leg_index INTEGER
);
"""


class TestResolveStartDate(unittest.TestCase):
    """
    _resolve_start_date() is sync-specific watermark-resume policy — unlike
    the fetching/mapping logic (see tests/test_schwab_transactions.py), it's
    not shared with util/rebuild_trade_transactions.py, so it stays here.
    """

    def setUp(self):
        self.db = DatabaseInserter(db_path=":memory:")
        self.db.cursor.executescript(SCHEMA)
        self.end_date = datetime(2026, 7, 11, tzinfo=timezone.utc)

    def tearDown(self):
        self.db.close()

    def test_resolves_from_watermark_minus_overlap(self):
        save_watermark(self.db, datetime(2026, 7, 9, tzinfo=timezone.utc))
        start = _resolve_start_date(self.db, self.end_date)
        self.assertEqual(start, datetime(2026, 7, 7, tzinfo=timezone.utc))

    def test_first_sync_starts_after_newest_db_trade(self):
        self.db.cursor.execute(
            "INSERT INTO trade_transaction (symbol, action, trade_type, trade_date, "
            "quantity, price, amount, account) "
            "VALUES ('FAKE', 'B', 'L', '2026-07-01', 1, 1, -1, 'C')"
        )
        start = _resolve_start_date(self.db, self.end_date)
        self.assertEqual(start, datetime(2026, 7, 2, tzinfo=timezone.utc))

    def test_empty_db_uses_full_window(self):
        start = _resolve_start_date(self.db, self.end_date)
        self.assertEqual(start, self.end_date - timedelta(days=MAX_API_WINDOW_DAYS))

    def test_watermark_capped_to_max_window(self):
        save_watermark(self.db, datetime(2020, 1, 1, tzinfo=timezone.utc))
        start = _resolve_start_date(self.db, self.end_date)
        self.assertEqual(start, self.end_date - timedelta(days=MAX_API_WINDOW_DAYS))


class TestSyncWindowing(unittest.TestCase):
    """
    sync() used to reject any --start-date/--end-date range wider than
    Schwab's ~1-year per-request cap. It now walks a range of any length
    internally via SchwabTransactionFetcher — these tests drive sync()
    end-to-end with a mocked Schwab client (never a real network call)
    against a real temp-file DB, so watermark checkpointing behavior is
    exercised too.
    """

    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        conn = sqlite3.connect(self.db_path)
        conn.executescript(SCHEMA)
        conn.commit()
        conn.close()
        patcher = patch("bin.sync_schwab_api.DB_PATH", self.db_path)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(os.remove, self.db_path)

    def _mock_client(self):
        client = MagicMock()
        accounts_resp = MagicMock()
        accounts_resp.json.return_value = [{"hashValue": "HASH1", "accountNumber": "123"}]
        client.get_account_numbers.return_value = accounts_resp
        empty_resp = MagicMock()
        empty_resp.json.return_value = []
        client.get_transactions.return_value = empty_resp
        return client

    def _run_sync(self, client, **kwargs):
        with patch("lib.schwab_client.get_client", return_value=client), \
             patch("bin.sync_schwab_api.load_account_map", return_value={"HASH1": "C"}):
            sync(**kwargs)

    def test_long_range_makes_one_api_call_per_window(self):
        client = self._mock_client()
        start = datetime(2015, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 7, 23, tzinfo=timezone.utc)
        self._run_sync(client, start_date=start, end_date=end, dry_run=True)

        expected_windows = list(iter_windows(start, end))
        self.assertEqual(client.get_transactions.call_count, len(expected_windows))
        calls = client.get_transactions.call_args_list
        self.assertEqual(calls[0].kwargs["start_date"], start)
        self.assertEqual(calls[-1].kwargs["end_date"], end)

    def test_short_range_makes_a_single_api_call(self):
        client = self._mock_client()
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 3, 1, tzinfo=timezone.utc)
        self._run_sync(client, start_date=start, end_date=end, dry_run=True)
        self.assertEqual(client.get_transactions.call_count, 1)

    def test_watermark_reflects_the_final_window_end_after_a_long_backfill(self):
        client = self._mock_client()
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 7, 23, tzinfo=timezone.utc)
        self._run_sync(client, start_date=start, end_date=end, dry_run=False)

        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT value FROM config WHERE key = ?", (SYNC_WATERMARK_KEY,)
        ).fetchone()
        conn.close()
        self.assertEqual(row[0], end.isoformat())

    def test_symbol_filter_also_loops_over_a_long_range(self):
        client = self._mock_client()
        start = datetime(2015, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 7, 23, tzinfo=timezone.utc)
        self._run_sync(client, start_date=start, end_date=end, dry_run=True, symbol="AAPL")

        expected_windows = list(iter_windows(start, end))
        self.assertEqual(client.get_transactions.call_count, len(expected_windows))

    def test_symbol_filter_does_not_advance_watermark_even_with_looping(self):
        client = self._mock_client()
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 7, 23, tzinfo=timezone.utc)
        self._run_sync(client, start_date=start, end_date=end, dry_run=False, symbol="AAPL")

        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT value FROM config WHERE key = ?", (SYNC_WATERMARK_KEY,)
        ).fetchone()
        conn.close()
        self.assertIsNone(row)


class TestReportFatalError(unittest.TestCase):
    """
    The raw authlib/httpx traceback is long and buries its one useful line
    at the bottom — _report_fatal_error() must send that mess to the log
    file only, and print a short, actionable message to the terminal.
    """

    def test_oauth_error_gives_login_instructions(self):
        exc = OAuthError(
            error="invalid_grant",
            description="Refresh token is invalid, expired or revoked",
        )
        with patch("bin.sync_schwab_api.log") as mock_log, \
             patch("bin.sync_schwab_api._diagnostics_log") as mock_diag:
            _report_fatal_error(exc)

        mock_diag.error.assert_called_once()
        self.assertTrue(mock_diag.error.call_args.kwargs.get("exc_info"))

        friendly_message = mock_log.error.call_args[0][1]
        self.assertIn("schwab_login.py", friendly_message)
        self.assertNotIn("Traceback", friendly_message)

    def test_generic_error_includes_original_message(self):
        with patch("bin.sync_schwab_api.log") as mock_log, \
             patch("bin.sync_schwab_api._diagnostics_log"):
            _report_fatal_error(ValueError("network down"))

        friendly_message = mock_log.error.call_args[0][1]
        self.assertIn("network down", friendly_message)


class TestMainErrorHandling(unittest.TestCase):
    def test_sync_failure_exits_nonzero_and_reports_friendly_error(self):
        with patch("bin.sync_schwab_api.sync", side_effect=RuntimeError("network down")), \
             patch("bin.sync_schwab_api._report_fatal_error") as mock_report, \
             patch("sys.argv", ["sync_schwab_api.py"]):
            with self.assertRaises(SystemExit) as ctx:
                main()

        self.assertEqual(ctx.exception.code, 1)
        mock_report.assert_called_once()
        self.assertIsInstance(mock_report.call_args[0][0], RuntimeError)


if __name__ == "__main__":
    unittest.main()
