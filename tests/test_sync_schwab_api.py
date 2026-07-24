import os
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

from bin.sync_schwab_api import (
    MAX_API_WINDOW_DAYS,
    SYNC_WATERMARK_KEY,
    build_option_label,
    build_transaction_record,
    determine_action,
    determine_trade_type,
    extract_trade_legs,
    iter_windows,
    parse_date,
    sync,
    _resolve_start_date,
    _save_watermark,
)
from lib.db_utils import DatabaseInserter

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


def option_instrument(**overrides):
    instrument = {
        "assetType": "OPTION",
        "underlyingSymbol": "QBTS",
        "expirationDate": "2026-07-17T00:00:00+0000",
        "strikePrice": 25.0,
        "putCall": "CALL",
    }
    instrument.update(overrides)
    return instrument


def trade_txn(amount, position_effect=None, asset_type="EQUITY", **txn_overrides):
    leg = {
        "instrument": {"assetType": asset_type, "symbol": "FAKE"},
        "amount": amount,
        "cost": -abs(amount) * 10.0 if amount > 0 else abs(amount) * 10.0,
        "price": 10.0,
    }
    if position_effect:
        leg["positionEffect"] = position_effect
    if asset_type == "OPTION":
        leg["instrument"] = option_instrument()
    txn = {
        "activityId": 1,
        "type": "TRADE",
        "tradeDate": "2026-07-10T04:00:00+0000",
        "description": "test",
        # Real Schwab TRADE transactions always carry a netAmount matching the
        # leg's cost; only "System transfer"-style transactions have netAmount
        # of exactly 0 despite a nonzero leg cost.
        "netAmount": leg["cost"],
        "transferItems": [leg],
    }
    txn.update(txn_overrides)
    return txn, leg


class TestParseDate(unittest.TestCase):
    def test_iso_with_offset(self):
        self.assertEqual(parse_date("2026-07-10T04:00:00+00:00"), "2026-07-10")

    def test_zulu_suffix(self):
        self.assertEqual(parse_date("2026-07-10T04:00:00Z"), "2026-07-10")

    def test_plain_date(self):
        self.assertEqual(parse_date("2026-07-10"), "2026-07-10")

    def test_none_returns_none(self):
        self.assertIsNone(parse_date(None))

    def test_unparseable_falls_back_to_prefix(self):
        self.assertEqual(parse_date("2026-07-10Xjunk"), "2026-07-10")


class TestDetermineTradeType(unittest.TestCase):
    def test_call(self):
        self.assertEqual(determine_trade_type(option_instrument()), "C")

    def test_put(self):
        self.assertEqual(determine_trade_type(option_instrument(putCall="PUT")), "P")

    def test_equity_is_long(self):
        self.assertEqual(determine_trade_type({"assetType": "EQUITY"}), "L")


class TestBuildOptionLabel(unittest.TestCase):
    def test_call_label(self):
        self.assertEqual(
            build_option_label(option_instrument()), "QBTS 07/17/2026 25.00 C"
        )

    def test_put_label(self):
        self.assertEqual(
            build_option_label(option_instrument(putCall="PUT")),
            "QBTS 07/17/2026 25.00 P",
        )

    def test_missing_field_returns_none(self):
        self.assertIsNone(build_option_label(option_instrument(underlyingSymbol=None)))


class TestDetermineAction(unittest.TestCase):
    def test_equity_buy(self):
        txn, leg = trade_txn(amount=100)
        self.assertEqual(determine_action(txn, leg, "EQUITY"), "Buy")

    def test_equity_sell(self):
        txn, leg = trade_txn(amount=-100)
        self.assertEqual(determine_action(txn, leg, "EQUITY"), "Sell")

    def test_option_buy_to_open(self):
        txn, leg = trade_txn(amount=2, position_effect="OPENING", asset_type="OPTION")
        self.assertEqual(determine_action(txn, leg, "OPTION"), "Buy to Open")

    def test_option_sell_to_close(self):
        txn, leg = trade_txn(amount=-2, position_effect="CLOSING", asset_type="OPTION")
        self.assertEqual(determine_action(txn, leg, "OPTION"), "Sell to Close")

    def test_option_without_effect_falls_back_on_sign(self):
        txn, leg = trade_txn(amount=-2, asset_type="OPTION")
        self.assertEqual(determine_action(txn, leg, "OPTION"), "Sell to Close")

    def test_zero_amount_returns_none(self):
        txn, leg = trade_txn(amount=0)
        self.assertIsNone(determine_action(txn, leg, "EQUITY"))

    def test_receive_and_deliver_expiration(self):
        txn, leg = trade_txn(amount=-1, type="RECEIVE_AND_DELIVER",
                             description="Expiration of option contract")
        self.assertEqual(determine_action(txn, leg, "OPTION"), "Expired")

    def test_receive_and_deliver_assignment(self):
        txn, leg = trade_txn(amount=-1, type="RECEIVE_AND_DELIVER",
                             description="Assignment of option")
        self.assertEqual(determine_action(txn, leg, "OPTION"), "Exchange or Exercise")

    def test_receive_and_deliver_journal_returns_none(self):
        # Sub-account journals (e.g. CASH -> MARGIN moves) are not trades
        txn, leg = trade_txn(amount=-1900, type="RECEIVE_AND_DELIVER",
                             description="CAPSTONE ENERGY+ INC")
        self.assertIsNone(determine_action(txn, leg, "EQUITY"))

    def test_dividend_reinvest_is_reinvest_shares(self):
        txn, leg = trade_txn(amount=10, description="Dividend Reinvest")
        self.assertEqual(determine_action(txn, leg, "EQUITY"), "Reinvest Shares")

    def test_zero_net_trade_returns_none(self):
        # "System transfer" moves existing shares between sub-accounts/books
        # with no real cash-settled purchase, despite a real-looking leg cost.
        txn, leg = trade_txn(amount=100, description="System transfer", netAmount=0.0)
        self.assertIsNone(determine_action(txn, leg, "EQUITY"))

    def test_nonzero_net_trade_is_not_treated_as_transfer(self):
        txn, leg = trade_txn(amount=100)
        self.assertEqual(determine_action(txn, leg, "EQUITY"), "Buy")


class TestExtractTradeLegs(unittest.TestCase):
    def test_filters_currency_legs(self):
        items = [
            {"instrument": {"assetType": "CURRENCY"}, "amount": -1000.0},
            {"instrument": {"assetType": "EQUITY", "symbol": "FAKE"}, "amount": 100},
            {"instrument": {"assetType": "COLLECTIVE_INVESTMENT", "symbol": "SPY"}, "amount": 5},
        ]
        legs = extract_trade_legs(items)
        self.assertEqual(len(legs), 2)
        self.assertEqual(legs[0]["instrument"]["symbol"], "FAKE")

    def test_empty_items(self):
        self.assertEqual(extract_trade_legs([]), [])


class TestBuildTransactionRecord(unittest.TestCase):
    def test_equity_buy_record(self):
        txn, leg = trade_txn(amount=100)
        leg["cost"] = -1000.0
        record = build_transaction_record(txn, leg, "C")
        self.assertEqual(record["symbol"], "FAKE")
        self.assertEqual(record["action"], "Buy")
        self.assertEqual(record["trade_type"], "L")
        self.assertIsNone(record["label"])
        self.assertEqual(record["trade_date"], "2026-07-10")
        self.assertEqual(record["quantity"], 100.0)
        self.assertEqual(record["amount"], -1000.0)
        self.assertEqual(record["account"], "C")

    def test_option_record_uses_underlying_and_label(self):
        txn, leg = trade_txn(amount=2, position_effect="OPENING", asset_type="OPTION")
        record = build_transaction_record(txn, leg, "R")
        self.assertEqual(record["symbol"], "QBTS")
        self.assertEqual(record["label"], "QBTS 07/17/2026 25.00 C")
        self.assertEqual(record["trade_type"], "C")
        self.assertEqual(record["target_price"], 25.0)

    def test_journal_leg_returns_none(self):
        txn, leg = trade_txn(amount=-1900, type="RECEIVE_AND_DELIVER",
                             description="CAPSTONE ENERGY+ INC", netAmount=0.0)
        leg["cost"] = 0.0
        self.assertIsNone(build_transaction_record(txn, leg, "R"))

    def test_expiration_recorded_on_expiration_date_with_zero_value(self):
        txn, leg = trade_txn(amount=-1, type="RECEIVE_AND_DELIVER",
                             description="Expiration of option", asset_type="OPTION")
        record = build_transaction_record(txn, leg, "C")
        self.assertEqual(record["action"], "Expired")
        self.assertEqual(record["trade_date"], "2026-07-17")  # expiration, not trade date
        self.assertEqual(record["price"], 0.0)
        self.assertEqual(record["amount"], 0.0)

    def test_record_carries_activity_id_and_leg_index(self):
        txn, leg = trade_txn(amount=100, activityId=555)
        record = build_transaction_record(txn, leg, "C", leg_index=1)
        self.assertEqual(record["activity_id"], 555)
        self.assertEqual(record["leg_index"], 1)

    def test_leg_index_defaults_to_zero(self):
        txn, leg = trade_txn(amount=100)
        record = build_transaction_record(txn, leg, "C")
        self.assertEqual(record["leg_index"], 0)

    def test_cusip_symbol_is_rejected(self):
        # Corporate-action legs (mergers, reverse splits) sometimes report a
        # 9-character CUSIP as the instrument symbol instead of a ticker.
        txn, leg = trade_txn(amount=200)
        leg["instrument"]["symbol"] = "873379101"
        self.assertIsNone(build_transaction_record(txn, leg, "C"))

    def test_system_transfer_is_skipped(self):
        txn, leg = trade_txn(amount=100, description="System transfer", netAmount=0.0)
        self.assertIsNone(build_transaction_record(txn, leg, "C"))


class TestWatermark(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseInserter(db_path=":memory:")
        self.db.cursor.executescript(SCHEMA)
        self.end_date = datetime(2026, 7, 11, tzinfo=timezone.utc)

    def tearDown(self):
        self.db.close()

    def test_resolves_from_watermark_minus_overlap(self):
        _save_watermark(self.db, datetime(2026, 7, 9, tzinfo=timezone.utc))
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

    def test_save_watermark_upserts(self):
        _save_watermark(self.db, datetime(2026, 7, 9, tzinfo=timezone.utc))
        _save_watermark(self.db, datetime(2026, 7, 11, tzinfo=timezone.utc))
        self.db.cursor.execute(
            "SELECT value FROM config WHERE key = ?", (SYNC_WATERMARK_KEY,)
        )
        self.assertEqual(
            self.db.cursor.fetchone()[0], "2026-07-11T00:00:00+00:00"
        )

    def test_watermark_capped_to_max_window(self):
        _save_watermark(self.db, datetime(2020, 1, 1, tzinfo=timezone.utc))
        start = _resolve_start_date(self.db, self.end_date)
        self.assertEqual(start, self.end_date - timedelta(days=MAX_API_WINDOW_DAYS))


class TestIterWindows(unittest.TestCase):
    def test_short_range_yields_one_window_spanning_the_whole_thing(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 3, 1, tzinfo=timezone.utc)
        windows = list(iter_windows(start, end))
        self.assertEqual(windows, [(start, end)])

    def test_long_range_is_split_into_multiple_windows(self):
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 1, 1, tzinfo=timezone.utc)  # ~2 years
        windows = list(iter_windows(start, end))
        self.assertGreater(len(windows), 1)
        # Contiguous, no gaps or overlaps, and covers the full range exactly
        self.assertEqual(windows[0][0], start)
        self.assertEqual(windows[-1][1], end)
        for (_, prev_end), (next_start, _) in zip(windows, windows[1:]):
            self.assertEqual(prev_end, next_start)
        for window_start, window_end in windows:
            self.assertLessEqual((window_end - window_start).days, MAX_API_WINDOW_DAYS)

    def test_eleven_year_range_matches_expected_window_count(self):
        start = datetime(2015, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 7, 23, tzinfo=timezone.utc)
        windows = list(iter_windows(start, end))
        total_days = (end - start).days
        self.assertEqual(len(windows), -(-total_days // MAX_API_WINDOW_DAYS))  # ceil div

    def test_zero_length_range_yields_no_windows(self):
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(list(iter_windows(start, start)), [])


class TestSyncWindowing(unittest.TestCase):
    """
    sync() used to reject any --start-date/--end-date range wider than
    Schwab's ~1-year per-request cap. It now walks a range of any length
    internally via iter_windows() — these tests drive sync() end-to-end with
    a mocked Schwab client (never a real network call) against a real
    temp-file DB, so watermark checkpointing behavior is exercised too.
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


if __name__ == "__main__":
    unittest.main()
