import unittest
from unittest.mock import patch

from app.extensions import db
from app.repositories import trade_repository as repo
from lib.db_utils import DatabaseInserter
from tests.helpers import create_test_app


def stock_txn(**overrides):
    txn = {
        "symbol": "KEEP",
        "action": "B",
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


class TestIgnoredSymbolsFiltering(unittest.TestCase):
    """
    An ignored symbol (patched here to 'HIDE') must vanish from every
    repository read function, even when its rows are still in the DB.
    """

    def setUp(self):
        self.app = create_test_app(flask_env="dev")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.inserter = DatabaseInserter(db=db)
        self.inserter.insert_security({"symbol": "KEEP", "name": "Keep Co"})
        self.inserter.insert_security({"symbol": "HIDE", "name": "Hide Co"})
        self.inserter.insert_transaction(stock_txn(symbol="KEEP"))
        self.inserter.insert_transaction(stock_txn(symbol="HIDE"))

        patcher = patch.object(repo, "get_ignored_symbols", return_value={"HIDE"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def test_get_all_traded_symbols_excludes_ignored(self):
        symbols = repo.get_all_traded_symbols()
        self.assertIn("KEEP", symbols)
        self.assertNotIn("HIDE", symbols)

    def test_get_all_securities_excludes_ignored(self):
        symbols = [s for s, _ in repo.get_all_securities()]
        self.assertIn("KEEP", symbols)
        self.assertNotIn("HIDE", symbols)

    def test_get_current_holdings_excludes_ignored(self):
        symbols = [row.symbol for row in repo.get_current_holdings()]
        self.assertIn("KEEP", symbols)
        self.assertNotIn("HIDE", symbols)

    def test_get_current_holdings_direct_lookup_of_ignored_returns_empty(self):
        self.assertEqual(repo.get_current_holdings(symbol="HIDE"), [])
        self.assertEqual(len(repo.get_current_holdings(symbol="KEEP")), 1)

    def test_get_raw_trade_data_returns_empty_for_ignored(self):
        self.assertEqual(repo.get_raw_trade_data("HIDE"), [])
        self.assertEqual(len(repo.get_raw_trade_data("KEEP")), 1)

    def test_get_trade_data_for_analysis_returns_empty_for_ignored(self):
        self.assertEqual(repo.get_trade_data_for_analysis("HIDE"), [])

    def test_get_trade_stats_summary_excludes_ignored(self):
        # HIDE has an unmatched buy so it wouldn't appear anyway (buy != sell
        # quantity); add a matching sell so it WOULD appear if not filtered.
        self.inserter.insert_transaction(stock_txn(symbol="HIDE", action="S", amount=1000.0))
        self.inserter.insert_transaction(stock_txn(symbol="KEEP", action="S", amount=1000.0))
        symbols = [row.symbol for row in repo.get_trade_stats_summary()]
        self.assertIn("KEEP", symbols)
        self.assertNotIn("HIDE", symbols)


if __name__ == "__main__":
    unittest.main()
