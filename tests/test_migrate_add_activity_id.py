import os
import sqlite3
import tempfile
import unittest

from bin.migrate_add_activity_id import migrate, NEW_INDEX, OLD_INDEXES

LEGACY_SCHEMA = """
CREATE TABLE trade_transaction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    action TEXT NOT NULL,
    label TEXT,
    trade_type TEXT,
    trade_date DATETIME NOT NULL,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    amount REAL NOT NULL,
    account TEXT NOT NULL
);
CREATE UNIQUE INDEX unique_trade_transaction_option_index
ON trade_transaction (symbol, action, label, trade_type, trade_date, quantity, price, amount, account)
WHERE trade_type IN ('C', 'P');
CREATE UNIQUE INDEX unique_trade_transaction_stock_index
ON trade_transaction (symbol, action, trade_type, trade_date, quantity, price, amount, account)
WHERE trade_type NOT IN ('C', 'P');
"""


class TestMigrateAddActivityId(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        conn = sqlite3.connect(self.db_path)
        conn.executescript(LEGACY_SCHEMA)
        conn.execute(
            "INSERT INTO trade_transaction (symbol, action, trade_type, trade_date, "
            "quantity, price, amount, account) VALUES ('FAKE', 'B', 'L', '2026-01-05', 1, 1, -1, 'C')"
        )
        conn.commit()
        conn.close()

    def tearDown(self):
        os.remove(self.db_path)

    def _columns(self):
        conn = sqlite3.connect(self.db_path)
        try:
            return {row[1] for row in conn.execute("PRAGMA table_info(trade_transaction)").fetchall()}
        finally:
            conn.close()

    def _indexes(self):
        conn = sqlite3.connect(self.db_path)
        try:
            return {
                row[0] for row in
                conn.execute("SELECT name FROM sqlite_master WHERE type = 'index'").fetchall()
            }
        finally:
            conn.close()

    def test_adds_columns_and_swaps_indexes(self):
        migrate(db_path=self.db_path)
        columns = self._columns()
        self.assertIn("activity_id", columns)
        self.assertIn("leg_index", columns)
        indexes = self._indexes()
        for old_index in OLD_INDEXES:
            self.assertNotIn(old_index, indexes)
        self.assertIn(NEW_INDEX, indexes)

    def test_preserves_existing_rows(self):
        migrate(db_path=self.db_path)
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute("SELECT symbol, activity_id FROM trade_transaction").fetchone()
        finally:
            conn.close()
        self.assertEqual(row[0], "FAKE")
        self.assertIsNone(row[1])

    def test_idempotent(self):
        migrate(db_path=self.db_path)
        migrate(db_path=self.db_path)  # should not raise
        self.assertIn("activity_id", self._columns())

    def test_new_index_allows_duplicate_business_fields_with_different_activity_id(self):
        migrate(db_path=self.db_path)
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT INTO trade_transaction (symbol, action, trade_type, trade_date, "
                "quantity, price, amount, account, activity_id, leg_index) "
                "VALUES ('NU', 'S', 'L', '2024-09-04', 100, 14.24, 1424.0, 'R', 111, 0)"
            )
            conn.execute(
                "INSERT INTO trade_transaction (symbol, action, trade_type, trade_date, "
                "quantity, price, amount, account, activity_id, leg_index) "
                "VALUES ('NU', 'S', 'L', '2024-09-04', 100, 14.24, 1424.0, 'R', 222, 0)"
            )
            conn.commit()
            count = conn.execute(
                "SELECT COUNT(*) FROM trade_transaction WHERE symbol = 'NU'"
            ).fetchone()[0]
        finally:
            conn.close()
        self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
