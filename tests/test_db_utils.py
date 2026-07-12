import unittest

from lib.db_utils import DatabaseConnection, DatabaseInserter

SCHEMA = """
CREATE TABLE security (
    symbol TEXT PRIMARY KEY NOT NULL,
    name TEXT NOT NULL
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
    account TEXT NOT NULL
);
"""


def stock_txn(**overrides):
    txn = {
        "symbol": "FAKE",
        "action": "Buy",
        "label": None,
        "trade_type": "L",
        "trade_date": "2026-01-05",
        "quantity": 10.0,
        "price": 100.0,
        "amount": -1000.0,
        "account": "C",
    }
    txn.update(overrides)
    return txn


class DbUtilsTestCase(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseInserter(db_path=":memory:")
        self.db.cursor.executescript(SCHEMA)

    def tearDown(self):
        self.db.close()


class TestDatabaseConnection(DbUtilsTestCase):
    def test_context_manager_closes_connection(self):
        with DatabaseInserter(db_path=":memory:") as db:
            self.assertIsNotNone(db.connection)
        with self.assertRaises(ConnectionError):
            db.connection

    def test_cursor_after_close_raises(self):
        conn = DatabaseConnection(db_path=":memory:")
        conn.close()
        with self.assertRaises(ConnectionError):
            conn.cursor

    def test_double_close_is_safe(self):
        conn = DatabaseConnection(db_path=":memory:")
        conn.close()
        conn.close()  # Should not raise


class TestInsertSecurity(DbUtilsTestCase):
    def test_insert_and_ignore_duplicate(self):
        self.db.insert_security({"symbol": "FAKE", "name": "Fake Co"})
        self.db.insert_security({"symbol": "FAKE", "name": "Renamed Co"})
        self.db.cursor.execute("SELECT name FROM security WHERE symbol = 'FAKE'")
        # INSERT OR IGNORE keeps the original row
        self.assertEqual(self.db.cursor.fetchone()[0], "Fake Co")


class TestTransactionExists(DbUtilsTestCase):
    def test_missing_transaction_returns_false(self):
        self.assertFalse(self.db.transaction_exists(stock_txn()))

    def test_existing_transaction_returns_true(self):
        self.db.insert_transaction(stock_txn())
        self.assertTrue(self.db.transaction_exists(stock_txn()))

    def test_null_label_matches_null(self):
        """Stock trades store label=NULL — dedupe must match via IS, not =."""
        self.db.insert_transaction(stock_txn(label=None))
        self.assertTrue(self.db.transaction_exists(stock_txn(label=None)))

    def test_different_quantity_is_not_duplicate(self):
        self.db.insert_transaction(stock_txn())
        self.assertFalse(self.db.transaction_exists(stock_txn(quantity=99.0)))

    def test_option_label_must_match(self):
        option = stock_txn(
            action="Buy to Open", label="FAKE 01/16/2026 5.00 C", trade_type="C"
        )
        self.db.insert_transaction(option)
        self.assertTrue(self.db.transaction_exists(option))
        other = dict(option, label="FAKE 01/16/2026 10.00 C")
        self.assertFalse(self.db.transaction_exists(other))


class TestInsertTransaction(DbUtilsTestCase):
    def test_insert_converts_action_name_to_acronym(self):
        self.db.insert_transaction(stock_txn(action="Buy"))
        self.db.cursor.execute("SELECT action FROM trade_transaction")
        self.assertEqual(self.db.cursor.fetchone()[0], "B")

    def test_insert_keeps_existing_acronym(self):
        self.db.insert_transaction(stock_txn(action="B"))
        self.db.cursor.execute("SELECT action FROM trade_transaction")
        self.assertEqual(self.db.cursor.fetchone()[0], "B")

    def test_unknown_action_becomes_uk(self):
        self.db.insert_transaction(stock_txn(action="Weird New Action"))
        self.db.cursor.execute("SELECT action FROM trade_transaction")
        self.assertEqual(self.db.cursor.fetchone()[0], "UK")

    def test_insert_error_raises_runtime_error(self):
        # Break the schema so the insert fails
        self.db.cursor.execute("DROP TABLE trade_transaction")
        with self.assertRaises(RuntimeError):
            self.db.insert_transaction(stock_txn())


class TestParsePrice(DbUtilsTestCase):
    def test_dollar_string(self):
        self.assertEqual(self.db._parse_price("$12.50"), 12.5)

    def test_float_passthrough(self):
        self.assertEqual(self.db._parse_price(7.25), 7.25)

    def test_none_returns_none(self):
        self.assertIsNone(self.db._parse_price(None))

    def test_empty_string_returns_none(self):
        self.assertIsNone(self.db._parse_price(""))

    def test_empty_price_defaults_to_zero_for_expired(self):
        self.assertEqual(self.db._parse_price(None, action="EXP"), 0.0)
        self.assertEqual(self.db._parse_price("", action="EE"), 0.0)

    def test_invalid_price_raises(self):
        with self.assertRaises(ValueError):
            self.db._parse_price("not-a-price")


if __name__ == "__main__":
    unittest.main()
