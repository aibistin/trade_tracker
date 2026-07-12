import unittest
from unittest.mock import patch

from app.extensions import db
from app.services import analysis_service
from app.services.analysis_service import analyze_symbol_safe, clear_analysis_cache
from lib.db_utils import DatabaseInserter
from tests.helpers import create_test_app


def stock_txn(**overrides):
    txn = {
        "symbol": "CACHE1",
        "action": "B",
        "label": "",
        "trade_type": "L",
        "trade_date": "2026-01-05",
        "quantity": 10,
        "price": 100.0,
        "amount": -1000.0,
        "account": "C",
    }
    txn.update(overrides)
    return txn


class TestAnalysisCache(unittest.TestCase):
    def setUp(self):
        self.app = create_test_app(flask_env="dev")
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.db_inserter = DatabaseInserter(db=db)
        self.db_inserter.insert_security({"symbol": "CACHE1", "name": "Cache Test Co"})
        self.db_inserter.insert_transaction(stock_txn())

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()

    def test_second_call_is_served_from_cache(self):
        first = analyze_symbol_safe("CACHE1")
        with patch.object(analysis_service, "TradingAnalyzer") as MockAnalyzer:
            second = analyze_symbol_safe("CACHE1")
        MockAnalyzer.assert_not_called()
        self.assertIs(second, first)

    def test_different_status_is_a_separate_entry(self):
        all_result = analyze_symbol_safe("CACHE1", status="all")
        open_result = analyze_symbol_safe("CACHE1", status="open")
        self.assertIsNot(all_result, open_result)

    def test_insert_invalidates_cache(self):
        first = analyze_symbol_safe("CACHE1")
        # New row changes the (MAX(id), COUNT(*)) data-version token
        self.db_inserter.insert_transaction(
            stock_txn(action="S", trade_date="2026-02-01", amount=1100.0, price=110.0)
        )
        second = analyze_symbol_safe("CACHE1")
        self.assertIsNot(second, first)
        # The sell now closes the position
        self.assertEqual(second["stock"]["summary"]["sold_quantity"], 10)

    def test_clear_analysis_cache_forces_recompute(self):
        first = analyze_symbol_safe("CACHE1")
        clear_analysis_cache()
        second = analyze_symbol_safe("CACHE1")
        self.assertIsNot(second, first)

    def test_ttl_expiry_forces_recompute(self):
        first = analyze_symbol_safe("CACHE1")
        real_monotonic = analysis_service.time.monotonic
        with patch.object(
            analysis_service.time, "monotonic",
            side_effect=lambda: real_monotonic() + analysis_service.CACHE_TTL_SECONDS + 1,
        ):
            second = analyze_symbol_safe("CACHE1")
        self.assertIsNot(second, first)

    def test_empty_symbol_result_is_cached(self):
        self.db_inserter.insert_security({"symbol": "EMPTY", "name": "No Trades Co"})
        self.assertIsNone(analyze_symbol_safe("EMPTY"))
        with patch.object(analysis_service, "get_trade_data_for_analysis") as mock_fetch:
            self.assertIsNone(analyze_symbol_safe("EMPTY"))
        mock_fetch.assert_not_called()

    def test_error_result_is_not_cached(self):
        clear_analysis_cache()
        with patch.object(
            analysis_service, "get_trade_data_for_analysis",
            side_effect=Exception("db hiccup"),
        ):
            self.assertIsNone(analyze_symbol_safe("CACHE1"))
        # After the transient failure, a real result is computed and returned
        self.assertIsNotNone(analyze_symbol_safe("CACHE1"))

    def test_trade_update_endpoint_clears_cache(self):
        first = analyze_symbol_safe("CACHE1")
        trade_id = 1
        response = self.client.patch(
            f"/api/trade/update/{trade_id}", json={"reason": "cache test"}
        )
        self.assertEqual(response.status_code, 200)
        second = analyze_symbol_safe("CACHE1")
        self.assertIsNot(second, first)


if __name__ == "__main__":
    unittest.main()
