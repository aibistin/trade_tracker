"""Tests for new API endpoints added during the trading-revamp.

Follows the existing test patterns from test_app_routes.py:
- unittest framework (not pytest)
- In-memory SQLite with DatabaseInserter for test data
- FLASK_ENV=dev to bypass API auth
- Mocked external APIs (yfinance) — no live network calls
"""

import os
import unittest
import logging
from unittest.mock import patch, MagicMock
from app import create_app
from app.extensions import db
from lib.db_utils import DatabaseInserter

test_logger = logging.getLogger("test_new_api_routes")
test_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
test_logger.addHandler(handler)

# Test securities
TEST_SECURITIES = {
    "HOLD1": "Holdings Test Stock One",
    "HOLD2": "Holdings Test Stock Two",
    "CLOSED1": "Fully Closed Stock",
}


class TestHoldingsEndpoint(unittest.TestCase):
    """Tests for GET /api/holdings — genuinely open positions via TradingAnalyzer."""

    def setUp(self):
        # Use testing env for in-memory SQLite, then also set dev bypass for API auth
        os.environ["FLASK_ENV"] = "testing"

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        self.app_context = self.app.app_context()
        self.app_context.push()

        # Bypass API key auth for convenience in these tests
        os.environ["FLASK_ENV"] = "dev"

        self.db_inserter = DatabaseInserter(db=db)

        for symbol, name in TEST_SECURITIES.items():
            self.db_inserter.insert_security({"symbol": symbol, "name": name})

        # HOLD1: open stock position (buy 100, no sell)
        self.db_inserter.insert_transaction({
            "symbol": "HOLD1",
            "action": "B",
            "label": "",
            "trade_type": "L",
            "trade_date": "2025-01-15 10:00",
            "expiration_date": "2025-01-15 10:00",
            "reason": "Test open stock HOLD1",
            "quantity": 100,
            "price": 50.00,
            "amount": 5000.0,
            "target_price": None,
            "initial_stop_price": None,
            "projected_sell_price": None,
            "account": "C",
        })

        # HOLD1: open option position (buy to open 2 contracts, no sell)
        self.db_inserter.insert_transaction({
            "symbol": "HOLD1",
            "action": "BO",
            "label": "HOLD1 03/21/2025 60.00 C",
            "trade_type": "C",
            "trade_date": "2025-01-20 11:00",
            "expiration_date": "2025-03-21",
            "reason": "Test open option HOLD1",
            "quantity": 2,
            "price": 3.50,
            "amount": -700.0,
            "target_price": 60.0,
            "initial_stop_price": None,
            "projected_sell_price": None,
            "account": "C",
        })

        # HOLD2: partially closed stock (buy 100, sell 40 — 60 remain open)
        self.db_inserter.insert_transaction({
            "symbol": "HOLD2",
            "action": "B",
            "label": "",
            "trade_type": "L",
            "trade_date": "2025-02-01 09:30",
            "expiration_date": "2025-02-01 09:30",
            "reason": "Test partial close HOLD2",
            "quantity": 100,
            "price": 120.00,
            "amount": 12000.0,
            "target_price": None,
            "initial_stop_price": 110.00,
            "projected_sell_price": 140.00,
            "account": "R",
        })
        self.db_inserter.insert_transaction({
            "symbol": "HOLD2",
            "action": "S",
            "label": "",
            "trade_type": "L",
            "trade_date": "2025-02-15 14:00",
            "expiration_date": "2025-02-15 14:00",
            "reason": "Test partial sell HOLD2",
            "quantity": 40,
            "price": 130.00,
            "amount": 5200.0,
            "target_price": None,
            "initial_stop_price": None,
            "projected_sell_price": None,
            "account": "R",
        })

        # CLOSED1: fully closed stock (buy 50, sell 50 — should NOT appear in holdings)
        self.db_inserter.insert_transaction({
            "symbol": "CLOSED1",
            "action": "B",
            "label": "",
            "trade_type": "L",
            "trade_date": "2025-01-05 10:00",
            "expiration_date": "2025-01-05 10:00",
            "reason": "Test closed position CLOSED1",
            "quantity": 50,
            "price": 200.00,
            "amount": 10000.0,
            "target_price": None,
            "initial_stop_price": None,
            "projected_sell_price": None,
            "account": "C",
        })
        self.db_inserter.insert_transaction({
            "symbol": "CLOSED1",
            "action": "S",
            "label": "",
            "trade_type": "L",
            "trade_date": "2025-01-20 10:00",
            "expiration_date": "2025-01-20 10:00",
            "reason": "Test sell closed CLOSED1",
            "quantity": 50,
            "price": 210.00,
            "amount": 10500.0,
            "target_price": None,
            "initial_stop_price": None,
            "projected_sell_price": None,
            "account": "C",
        })

        test_logger.info("TestHoldingsEndpoint setup completed")

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()
        test_logger.info("TestHoldingsEndpoint teardown completed")

    def _mock_yfinance(self):
        """Return a patcher that mocks YahooFinance for all calls.

        Option prices are keyed by OCC-format ticker (label_to_occ converts the label
        before calling yfinance). "HOLD1 03/21/2025 60.00 C" → "HOLD1250321C00060000".
        """
        patcher = patch("app.routes.api_routes.YahooFinance")
        mock_yf_class = patcher.start()

        def side_effect(symbol):
            instance = MagicMock()
            instance.get_stock_data.return_value = None
            prices = {
                "HOLD1": {"currentPrice": 55.00, "regularMarketPrice": 55.00},
                "HOLD2": {"currentPrice": 125.00, "regularMarketPrice": 125.00},
                # OCC format for "HOLD1 03/21/2025 60.00 C"
                "HOLD1250321C00060000": {"lastPrice": 4.20, "regularMarketPrice": 4.20},
            }
            instance.get_results.return_value = prices.get(symbol, {})
            return instance

        mock_yf_class.side_effect = side_effect
        return patcher

    def test_holdings_returns_200(self):
        """GET /api/holdings returns 200."""
        patcher = self._mock_yfinance()
        try:
            response = self.client.get("/api/holdings")
            self.assertEqual(response.status_code, 200)
        finally:
            patcher.stop()

    def test_holdings_top_level_structure(self):
        """Response has stock and option top-level keys with correct sub-keys."""
        patcher = self._mock_yfinance()
        try:
            response = self.client.get("/api/holdings")
            data = response.get_json()

            self.assertIn("stock", data)
            self.assertIn("option", data)

            for section in ("stock", "option"):
                self.assertIn("positions", data[section])
                self.assertIn("total_cost_basis", data[section])
                self.assertIn("total_market_value", data[section])
                self.assertIn("total_unrealized_pnl", data[section])
        finally:
            patcher.stop()

    def test_holdings_excludes_closed_positions(self):
        """Fully closed positions must NOT appear in holdings."""
        patcher = self._mock_yfinance()
        try:
            response = self.client.get("/api/holdings")
            data = response.get_json()

            all_symbols = [p["symbol"] for p in data["stock"]["positions"]]
            all_symbols += [p["symbol"] for p in data["option"]["positions"]]

            self.assertNotIn(
                "CLOSED1", all_symbols,
                "CLOSED1 is fully closed and should not appear in holdings"
            )
        finally:
            patcher.stop()

    def test_holdings_includes_open_stock_position(self):
        """HOLD1 stock (100 shares bought, none sold) must appear."""
        patcher = self._mock_yfinance()
        try:
            response = self.client.get("/api/holdings")
            data = response.get_json()

            hold1_stocks = [
                p for p in data["stock"]["positions"] if p["symbol"] == "HOLD1"
            ]
            self.assertEqual(
                len(hold1_stocks), 1,
                f"Expected 1 HOLD1 stock position, got {len(hold1_stocks)}"
            )

            pos = hold1_stocks[0]
            self.assertEqual(pos["quantity"], 100)
            self.assertEqual(pos["avg_cost"], 50.00)
            self.assertEqual(pos["trade_type"], "L")
            self.assertEqual(pos["name"], "Holdings Test Stock One")
        finally:
            patcher.stop()

    def test_holdings_includes_open_option_position(self):
        """HOLD1 option (2 contracts bought, none sold) must appear."""
        patcher = self._mock_yfinance()
        try:
            response = self.client.get("/api/holdings")
            data = response.get_json()

            hold1_options = [
                p for p in data["option"]["positions"] if p["symbol"] == "HOLD1"
            ]
            self.assertEqual(
                len(hold1_options), 1,
                f"Expected 1 HOLD1 option position, got {len(hold1_options)}"
            )

            pos = hold1_options[0]
            self.assertEqual(pos["quantity"], 2)
            self.assertEqual(pos["avg_cost"], 3.50)
            self.assertEqual(pos["trade_type"], "C")
            self.assertIn("HOLD1", pos["label"])
        finally:
            patcher.stop()

    def test_holdings_partial_close_remaining_quantity(self):
        """HOLD2 (bought 100, sold 40) should show 60 remaining shares."""
        patcher = self._mock_yfinance()
        try:
            response = self.client.get("/api/holdings")
            data = response.get_json()

            hold2_stocks = [
                p for p in data["stock"]["positions"] if p["symbol"] == "HOLD2"
            ]
            self.assertEqual(
                len(hold2_stocks), 1,
                f"Expected 1 HOLD2 stock position, got {len(hold2_stocks)}"
            )

            pos = hold2_stocks[0]
            self.assertEqual(
                pos["quantity"], 60,
                f"Expected 60 remaining shares, got {pos['quantity']}"
            )
        finally:
            patcher.stop()

    def test_holdings_position_fields(self):
        """Each position must have all expected fields.

        Positions are aggregated (no per-trade trade_date/account since multiple
        buy lots are merged into one row). Options additionally carry occ_ticker.
        """
        patcher = self._mock_yfinance()
        try:
            response = self.client.get("/api/holdings")
            data = response.get_json()

            common_fields = {
                "symbol", "name", "trade_type", "label", "quantity",
                "avg_cost", "cost_basis", "current_price", "market_value",
                "unrealized_pnl", "pnl_pct",
            }

            for pos in data["stock"]["positions"]:
                for field in common_fields:
                    self.assertIn(field, pos, f"Stock position missing '{field}': {pos.get('symbol')}")

            for pos in data["option"]["positions"]:
                for field in common_fields | {"occ_ticker"}:
                    self.assertIn(field, pos, f"Option position missing '{field}': {pos.get('symbol')}")
        finally:
            patcher.stop()

    def test_holdings_stock_current_price_populated(self):
        """Stock positions should have current_price filled in from yfinance."""
        patcher = self._mock_yfinance()
        try:
            response = self.client.get("/api/holdings")
            data = response.get_json()

            hold1_stocks = [
                p for p in data["stock"]["positions"] if p["symbol"] == "HOLD1"
            ]
            self.assertEqual(len(hold1_stocks), 1)

            pos = hold1_stocks[0]
            self.assertEqual(
                pos["current_price"], 55.00,
                f"Expected current_price=55.00, got {pos['current_price']}"
            )
            # market_value = price * quantity
            self.assertEqual(pos["market_value"], 5500.00)
            # unrealized P&L = market_value - cost_basis
            # cost_basis = 50.00 * 100 = 5000.00
            self.assertEqual(pos["cost_basis"], 5000.00)
            self.assertEqual(pos["unrealized_pnl"], 500.00)
        finally:
            patcher.stop()

    def test_holdings_option_current_price_via_label(self):
        """Option positions should fetch current price using their label (OCC ticker)."""
        patcher = self._mock_yfinance()
        try:
            response = self.client.get("/api/holdings")
            data = response.get_json()

            hold1_options = [
                p for p in data["option"]["positions"] if p["symbol"] == "HOLD1"
            ]
            self.assertEqual(len(hold1_options), 1)

            pos = hold1_options[0]
            self.assertEqual(
                pos["current_price"], 4.20,
                f"Expected option current_price=4.20, got {pos['current_price']}"
            )
            # Option: market_value = price * quantity * 100 (multiplier)
            self.assertEqual(pos["market_value"], 840.00)
            # cost_basis = 3.50 * 2 * 100 = 700.00
            self.assertEqual(pos["cost_basis"], 700.00)
            self.assertEqual(pos["unrealized_pnl"], 140.00)
        finally:
            patcher.stop()

    def test_holdings_option_cost_basis_uses_multiplier(self):
        """Option cost_basis must use the 100x multiplier."""
        patcher = self._mock_yfinance()
        try:
            response = self.client.get("/api/holdings")
            data = response.get_json()

            hold1_options = [
                p for p in data["option"]["positions"] if p["symbol"] == "HOLD1"
            ]
            pos = hold1_options[0]
            # 3.50 * 2 contracts * 100 multiplier = 700.00
            self.assertEqual(
                pos["cost_basis"], 700.00,
                f"Option cost_basis should use 100x multiplier: expected 700.00, got {pos['cost_basis']}"
            )
        finally:
            patcher.stop()

    def test_holdings_totals_computed_correctly(self):
        """Stock and option section totals should sum position values."""
        patcher = self._mock_yfinance()
        try:
            response = self.client.get("/api/holdings")
            data = response.get_json()

            # Verify stock totals
            stock = data["stock"]
            expected_cost = sum(p["cost_basis"] for p in stock["positions"])
            expected_value = sum(
                p["market_value"] for p in stock["positions"]
                if p["market_value"] is not None
            )

            self.assertAlmostEqual(stock["total_cost_basis"], expected_cost, places=2)
            self.assertAlmostEqual(stock["total_market_value"], expected_value, places=2)
            self.assertAlmostEqual(
                stock["total_unrealized_pnl"],
                expected_value - expected_cost,
                places=2,
            )

            # Verify option totals
            option = data["option"]
            expected_opt_cost = sum(p["cost_basis"] for p in option["positions"])
            expected_opt_value = sum(
                p["market_value"] for p in option["positions"]
                if p["market_value"] is not None
            )

            self.assertAlmostEqual(option["total_cost_basis"], expected_opt_cost, places=2)
            self.assertAlmostEqual(option["total_market_value"], expected_opt_value, places=2)
        finally:
            patcher.stop()

    def test_holdings_pnl_pct_calculated(self):
        """P&L percentage should be (unrealized_pnl / cost_basis) * 100."""
        patcher = self._mock_yfinance()
        try:
            response = self.client.get("/api/holdings")
            data = response.get_json()

            hold1_stocks = [
                p for p in data["stock"]["positions"] if p["symbol"] == "HOLD1"
            ]
            pos = hold1_stocks[0]
            # unrealized_pnl=500, cost_basis=5000 => 10%
            self.assertAlmostEqual(pos["pnl_pct"], 10.0, places=2)
        finally:
            patcher.stop()

    def test_holdings_yfinance_failure_graceful(self):
        """If yfinance throws, positions still appear but with null price fields."""
        with patch("app.routes.api_routes.YahooFinance") as MockYF:
            instance = MagicMock()
            instance.get_stock_data.side_effect = Exception("API down")
            MockYF.return_value = instance

            response = self.client.get("/api/holdings")
            self.assertEqual(response.status_code, 200)

            data = response.get_json()
            # Positions should still be present
            all_positions = (
                data["stock"]["positions"] + data["option"]["positions"]
            )
            self.assertGreater(len(all_positions), 0)

            # Prices should be null when fetch fails
            for pos in all_positions:
                self.assertIsNone(
                    pos["current_price"],
                    f"current_price should be None when yfinance fails: {pos['symbol']}"
                )

    def test_holdings_excludes_fully_closed_from_results(self):
        """CLOSED1 (buy 50 + sell 50) must not appear — only truly open positions remain."""
        patcher = self._mock_yfinance()
        try:
            response = self.client.get("/api/holdings")
            data = response.get_json()

            # Only HOLD1 and HOLD2 should have open positions, not CLOSED1
            all_symbols = set(
                p["symbol"]
                for p in data["stock"]["positions"] + data["option"]["positions"]
            )
            self.assertNotIn("CLOSED1", all_symbols)
            # Verify we do have the expected open positions
            self.assertIn("HOLD1", all_symbols)
            self.assertIn("HOLD2", all_symbols)
        finally:
            patcher.stop()

    def test_holdings_no_per_trade_account_field(self):
        """Aggregated positions do not carry a per-trade account field.

        Stock positions may span multiple buy lots across different accounts, so
        the account field is not present at the aggregated position level.
        """
        patcher = self._mock_yfinance()
        try:
            response = self.client.get("/api/holdings")
            data = response.get_json()

            hold1_stocks = [
                p for p in data["stock"]["positions"] if p["symbol"] == "HOLD1"
            ]
            self.assertEqual(len(hold1_stocks), 1)
            # Aggregated positions don't carry per-trade account; verify not present
            self.assertNotIn("account", hold1_stocks[0])
        finally:
            patcher.stop()

    def test_holdings_no_per_trade_trade_date_field(self):
        """Aggregated positions do not carry a per-trade trade_date field.

        Multiple lots may have different dates; the aggregated row omits this field.
        """
        patcher = self._mock_yfinance()
        try:
            response = self.client.get("/api/holdings")
            data = response.get_json()

            hold1_stocks = [
                p for p in data["stock"]["positions"] if p["symbol"] == "HOLD1"
            ]
            self.assertEqual(len(hold1_stocks), 1)
            self.assertNotIn("trade_date", hold1_stocks[0])
        finally:
            patcher.stop()


class TestHoldingsAuth(unittest.TestCase):
    """Holdings endpoint should respect API key auth when not in dev mode."""

    def setUp(self):
        # Use testing env for in-memory DB, then remove dev bypass
        os.environ["FLASK_ENV"] = "testing"
        os.environ["API_SECRET_KEY"] = "test-secret-key"

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        self.app_context = self.app.app_context()
        self.app_context.push()

        # Remove the dev bypass so auth is enforced
        os.environ.pop("FLASK_ENV", None)

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()
        os.environ.pop("API_SECRET_KEY", None)
        os.environ.pop("FLASK_ENV", None)

    def test_holdings_without_api_key_returns_401(self):
        """GET /api/holdings without X-API-KEY returns 401."""
        response = self.client.get("/api/holdings")
        self.assertEqual(response.status_code, 401)

    def test_holdings_with_correct_api_key_returns_200(self):
        """GET /api/holdings with correct X-API-KEY returns 200."""
        with patch("app.routes.api_routes.YahooFinance") as MockYF:
            instance = MagicMock()
            instance.get_stock_data.return_value = None
            instance.get_results.return_value = {}
            MockYF.return_value = instance

            response = self.client.get(
                "/api/holdings",
                headers={"X-API-KEY": "test-secret-key"},
            )
            self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main(failfast=True)
