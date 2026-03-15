import os
import unittest
import logging
from unittest.mock import patch, MagicMock
from sqlalchemy import select, delete
from app import create_app
from app.models.models import Security, TradeTransaction
from app.extensions import db
from lib.db_utils import DatabaseInserter

# Configure test logger
test_logger = logging.getLogger("test_routes")
test_logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
test_logger.addHandler(handler)
filter_symbol = "FILT1"

# Global data structure for test tickers and names
TEST_SECURITIES = {
    "FAKE1": "Fake Company One",
    "FAKE2": "Fake Company Two",
    "FAKE3": "Fake Company Three",
    filter_symbol: "Fake Filter Trade 1",
}


TRANSACTION_KEYS = [
    "id",
    "symbol",
    "action",
    "trade_type",
    "label",
    "trade_date",
    "expiration_date",
    "reason",
    "quantity",
    "price",
    "target_price",
    "amount",
    "initial_stop_price",
    "projected_sell_price",
    "account",
]


class TestAppRoutes(unittest.TestCase):
    def setUp(self):
        # Ensure API auth is bypassed in dev mode regardless of shell environment
        os.environ["FLASK_ENV"] = "dev"

        # Create test app with testing configuration
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.client = self.app.test_client()

        # Push application context
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create database schema
        db.create_all()
        self.db_inserter = DatabaseInserter(db=db)

        # Insert test data
        for symbol, name in TEST_SECURITIES.items():
            self.db_inserter.insert_security({"symbol": symbol, "name": name})

        # Insert test transactions
        transaction_rows = [
            {
                "symbol": "FAKE1",
                "action": "B",
                "label": "",
                "trade_type": "L",
                "trade_date": "2024-06-26 10:30",
                "expiration_date": "2024-06-26 10:30",
                "reason": "Test Buy FAKE1",
                "quantity": 100,
                "price": 150.50,
                "amount": 15050.0,
                "target_price": None,
                "initial_stop_price": 142.975,
                "projected_sell_price": 165.525,
                "account": "C",
            },
            {
                "symbol": "FAKE1",
                "action": "S",
                "label": "",
                "trade_type": "L",
                "trade_date": "2024-07-21 10:30",
                "expiration_date": "2024-07-21 10:30",
                "reason": "Test Sell FAKE1",
                "quantity": 100,
                "price": 150.50,
                "amount": 15050.0,
                "target_price": None,
                "initial_stop_price": 142.95,
                "projected_sell_price": 165.525,
                "account": "C",
            },
            {
                "symbol": "FAKE2",
                "action": "B",
                "label": "",
                "trade_type": "L",
                "trade_date": "2024-07-28 14:15",
                "expiration_date": "2024-07-28 14:15",
                "reason": "Test Buy FAKE2",
                "quantity": 50,
                "price": 120.25,
                "amount": 6012.5,
                "target_price": None,
                "initial_stop_price": None,
                "projected_sell_price": None,
                "account": "C",
            },
            {
                "symbol": "FAKE2",
                "action": "S",
                "label": "",
                "trade_type": "L",
                "trade_date": "2024-08-13 14:15",
                "expiration_date": "2024-08-13 14:15",
                "reason": "Test Sell FAKE2",
                "quantity": 50,
                "price": 120.25,
                "amount": 6012.5,
                "target_price": None,
                "initial_stop_price": None,
                "projected_sell_price": None,
                "account": "C",
            },
            {
                "symbol": filter_symbol,
                "action": "B",
                "label": "",
                "trade_type": "L",
                "trade_date": "2025-02-01 10:30",
                "reason": f"Filtered Buy {filter_symbol}",
                "quantity": 50,
                "price": 160.00,
                "amount": 8000.0,
                "target_price": None,
                "initial_stop_price": None,
                "projected_sell_price": None,
                "account": "O",
            },
            {
                "symbol": filter_symbol,
                "action": "S",
                "label": "",
                "trade_type": "L",
                "trade_date": "2025-02-02 10:30",
                "reason": f"Filtered Sell {filter_symbol}",
                "quantity": 50,
                "price": 165.00,
                "amount": 8250.0,
                "target_price": None,
                "initial_stop_price": None,
                "projected_sell_price": None,
                "account": "O",
            },
            # Open stock position for FAKE3 (no sell)
            {
                "symbol": "FAKE3",
                "action": "B",
                "label": "",
                "trade_type": "L",
                "trade_date": "2025-03-01 10:00",
                "expiration_date": "2025-03-01 10:00",
                "reason": "Test Buy FAKE3 Open",
                "quantity": 25,
                "price": 200.00,
                "amount": 5000.0,
                "target_price": None,
                "initial_stop_price": None,
                "projected_sell_price": None,
                "account": "C",
            },
            # Option trades for FAKE1
            {
                "symbol": "FAKE1",
                "action": "BO",
                "label": "FAKE1 01/17/2025 50.00 C",
                "trade_type": "C",
                "trade_date": "2024-06-26 11:00",
                "expiration_date": "2025-01-17",
                "reason": "Test Buy Option FAKE1",
                "quantity": 1,
                "price": 5.00,
                "amount": -500.0,
                "target_price": 50.0,
                "initial_stop_price": None,
                "projected_sell_price": None,
                "account": "C",
            },
            {
                "symbol": "FAKE1",
                "action": "SC",
                "label": "FAKE1 01/17/2025 50.00 C",
                "trade_type": "C",
                "trade_date": "2024-12-15 11:00",
                "expiration_date": "2025-01-17",
                "reason": "Test Sell Option FAKE1",
                "quantity": 1,
                "price": 8.00,
                "amount": 800.0,
                "target_price": 50.0,
                "initial_stop_price": None,
                "projected_sell_price": None,
                "account": "C",
            },
        ]

        for row in transaction_rows:
            self.db_inserter.insert_transaction(row)
            test_logger.info(
                f"Inserted transaction: {row['symbol']} {row['action']} {row['reason']}"
            )

        # Retrieve the ID of the first inserted transaction
        self.first_transaction = db.session.execute(
            select(TradeTransaction).filter_by(reason="Test Buy FAKE1")
        ).scalars().first()

        test_logger.info("Test setup completed")

    def tearDown(self):
        # Clean up database

        db.session.execute(
            delete(TradeTransaction).where(TradeTransaction.symbol.in_(["FAKE1", "FAKE2"]))
        )
        db.session.execute(
            delete(Security).where(Security.symbol.in_(TEST_SECURITIES.keys()))
        )

        db.session.commit()
        db.session.remove()
        self.app_context.pop()
        test_logger.info("Test teardown completed")

    # @unittest.skip("Skipping test_index_route")
    def test_index_route(self):
        """Test the home page route returns successfully"""
        response = self.client.get("/")
        self.assertEqual(
            response.status_code,
            200,
            f"Expected status 200, got {response.status_code}",
        )
        self.assertIn(
            b"Trade Tracker",
            response.data,
            "Page title 'Trade Tracker' not found in response",
        )

    # @unittest.skip("Skipping test_recent_trades_route")
    def test_recent_trades_route(self):
        """Test recent trades route returns successfully"""
        response = self.client.get("/recent_trades/5")
        self.assertEqual(
            response.status_code,
            200,
            f"Expected status 200, got {response.status_code}",
        )
        self.assertIn(
            b"Recent Trades",
            response.data,
            "'Recent Trades' heading not found in response",
        )

    # @unittest.skip("Skipping test_trades_by_symbol_route")
    def test_trades_by_symbol_route(self):
        """Test trades by symbol route returns successfully"""
        get_fake_url = "/trades/FAKE1"
        response = self.client.get(get_fake_url)
        self.assertEqual(
            response.status_code,
            200,
            f"Expected status 200 from {get_fake_url}, got {response.status_code}",
        )

        self.assertIn(b"FAKE1", response.data, "Symbol 'FAKE1' not found in response")

    # @unittest.skip("Skipping test_update_transaction_route")
    def test_update_transaction_route(self):
        """Test updating a transaction works correctly"""
        data = {
            "reason": "No real reason",
            "initial_stop_price": "123.45",
            "projected_sell_price": "150.00",
        }

        # Get transaction ID

        self.first_transaction = db.session.execute(
            select(TradeTransaction).filter_by(reason="Test Buy FAKE1")
        ).scalars().first()

        transaction_id = self.first_transaction.id
        original_transaction = db.session.get(TradeTransaction, transaction_id)
        test_logger.info(f"Original Transaction: {vars(original_transaction)}")

        # Send update request
        response = self.client.post(
            f"/update_transaction/{transaction_id}",
            data=data,
            follow_redirects=True,
        )

        # Verify response
        self.assertEqual(
            response.status_code,
            200,
            f"Expected status 200 after redirect, got {response.status_code}",
        )

        # Verify database update
        updated_transaction = db.session.get(TradeTransaction, transaction_id)

        test_logger.info(f"Updated Transaction: {vars(updated_transaction)}")

        self.assertIsInstance(
            updated_transaction,
            TradeTransaction,
            "Expected 'updated_transactions' to be a TradeTransaction object",
        )

        self.assertEqual(
            updated_transaction.reason,
            data.get("reason"),
            f"Expected reason '{data.get("reason")}', got '{updated_transaction.reason}'",
        )
        self.assertEqual(
            float(updated_transaction.initial_stop_price),
            123.45,
            f"Expected stop price {data.get('initial_stop_price')}, got {updated_transaction.initial_stop_price}",
        )
        self.assertEqual(
            float(updated_transaction.projected_sell_price),
            150.00,
            f"Expected sell price {data.get('projected_sell_price')}, got {updated_transaction.projected_sell_price}",
        )

    # @unittest.skip("Skip test_api_trades_route")
    def test_api_trades_route(self):
        """Test API trades endpoint returns correct data"""
        response = self.client.get("/api/trades/all/json/FAKE1")
        self.assertEqual(
            response.status_code,
            200,
            f"Expected status 200, got {response.status_code}",
        )

        trades_data = response.json

        # Verify response structure
        self.assertEqual(
            trades_data["stock_symbol"],
            "FAKE1",
            f"Expected stock_symbol 'FAKE1', got {trades_data['stock_symbol']}",
        )
        self.assertEqual(
            trades_data["requested"],
            "all_trades",
            f"Expected requested 'all_trades', got {trades_data['requested']}",
        )

        # Verify transaction data
        transaction_stats = trades_data["transaction_stats"]
        self.assertIsInstance(
            transaction_stats, dict, "transaction_stats should be a dictionary"
        )

        # "all_trades" is the flattened BuyTrades and SellTrades
        stock_trades = transaction_stats["stock"]["all_trades"]
        self.assertEqual(
            len(stock_trades), 2, f"Expected 2 stock trades, got {len(stock_trades)}"
        )

        stock_buy_trade = stock_trades[0]
        stock_sell_trade = stock_trades[1]
        self.assertEqual(
            stock_buy_trade["current_sold_qty"],
            100.00,
            f"Expected current_sold_qty == 100, got {stock_buy_trade['current_sold_qty']}",
        )

        self.assertEqual(
            stock_sell_trade["price"],
            150.50,
            f"Expected sell price == 150.5, got {stock_sell_trade['price']}",
        )

        self.assertEqual(
            stock_sell_trade["amount"],
            15050.0,
            f"Expected sell amount == 1505.50, got {stock_sell_trade['amount']}",
        )

        self.assertTrue(
            stock_buy_trade["is_done"],
            f"Expected is_done == True, got {stock_buy_trade['is_done']}",
        )

        stock_sell_trades = stock_buy_trade["sells"]

        self.assertEqual(
            len(stock_sell_trades),
            1,
            f"Expected 1 stock sell trade, got {len(stock_sell_trades)}",
        )

        stock_sell_trade = stock_sell_trades[0]

        self.assertEqual(
            stock_sell_trade["quantity"],
            100,
            f"Expected stock sell trade quantity == 100, got {stock_sell_trade['quantity']}",
        )

        # test_logger.info(f"Stock Trades: {stock_trades}")

        option_trades = transaction_stats["option"]["all_trades"]

        self.assertEqual(
            len(option_trades), 2, f"Expected 2 option trades, got {len(option_trades)}"
        )

        # Verify summary data
        stock_summary = transaction_stats["stock"]["summary"]

        self.assertIsInstance(
            stock_summary, dict, "Stock summary should be a dictionary"
        )

        self.assertEqual(
            stock_summary["profit_loss"],
            0.0,
            f"Expected stock_summary[profit_loss] == 0.0, got {stock_summary['profit_loss']}",
        )

    # @unittest.skip("Skip test_api_current_holdings")
    def test_api_current_holdings(self):
        """Test API current holdings endpoint returns correctly"""
        response = self.client.get("/api/trade/current_holdings_json")
        self.assertEqual(
            response.status_code,
            200,
            f"Expected status 200, got {response.status_code}",
        )

        holdings = response.json
        self.assertIsInstance(holdings, list, "Response should be a list")
        self.assertGreater(len(holdings), 0, "Holdings should not be empty")

        # Verify holdings data structure
        for holding in holdings:
            self.assertIn("symbol", holding, "Holding missing 'symbol' field")
            self.assertIn("trade_type", holding, "Holding missing 'trade_type' field")
            self.assertIn("shares", holding, "Holding missing 'shares' field")
            self.assertIn(
                "average_price", holding, "Holding missing 'average_price' field"
            )
            self.assertIn("profit_loss", holding, "Holding missing 'profit_loss' field")
            self.assertIn("name", holding, "Holding missing 'name' field")

        # Verify FAKE3 open position is in holdings
        fake3_holdings = [h for h in holdings if h["symbol"] == "FAKE3"]
        self.assertEqual(len(fake3_holdings), 1, "FAKE3 should have 1 open holding")
        self.assertEqual(fake3_holdings[0]["shares"], 25)
        self.assertEqual(fake3_holdings[0]["trade_type"], "L")

    # @unittest.skip("Skip test_api_symbols")
    def test_api_symbols(self):
        """Test API symbols endpoint returns correctly"""
        response = self.client.get("/api/trade/symbols_json")
        self.assertEqual(
            response.status_code,
            200,
            f"Expected status 200, got {response.status_code}",
        )

        symbols = response.json or []
        self.assertIsInstance(symbols, list, "Response should be a list")

        # Verify expected symbols are present
        symbol_names = [s[0] for s in symbols]
        for symbol in TEST_SECURITIES.keys():
            self.assertIn(
                symbol, symbol_names, f"Test symbol {symbol} missing from response"
            )

    # Testp POST filtered_trades
    def test_api_filtered_trades_route(self):
        """Test filtered trades endpoint with account and date filters"""

        response = self.client.post(
            f"/api/trades/all/json/{filter_symbol}/filtered", json={"account": "O"}
        )
        self.assertEqual(
            response.status_code,
            200,
            f"Expected status 200, got {response.status_code}",
        )

        trades_data = response.json
        self.assertEqual(
            trades_data["filters"]["account"],
            "O",
            f"Expected account filter: O, got {trades_data['filters']['account']}",
        )

        # Verify only O trades are returned
        stock_trades = trades_data["transaction_stats"]["stock"]["all_trades"]
        self.assertEqual(
            len(stock_trades),
            2,
            f"Expected 2 trades for account O, got {len(stock_trades)}",
        )
        for trade in stock_trades:
            self.assertEqual(
                trade["account"], "O", f"Expected account O, got {trade['account']}"
            )

    def test_api_filtered_trades_date_account(self):
        """Test filtered trades with date and account filters"""
        # Test with both filters
        response = self.client.post(
            f"/api/trades/all/json/{filter_symbol}/filtered",
            json={"after_date": "2025-01-01", "account": "O"},
        )
        self.assertEqual(
            response.status_code,
            200,
            f"Expected status 200, got {response.status_code}",
        )

        trades_data = response.json
        self.assertEqual(
            trades_data["filters"]["after_date"],
            "2025-01-01",
            f"Expected after_date filter: 2025-01-01, got {trades_data['filters']['after_date']}",
        )
        self.assertEqual(
            trades_data["filters"]["account"],
            "O",
            f"Expected account filter: O, got {trades_data['filters']['account']}",
        )

        # Verify only matching trades are returned
        stock_trades = trades_data["transaction_stats"]["stock"]["all_trades"]

        test_logger.debug(f"stock_trades: {trades_data}")

        self.assertEqual(
            len(stock_trades),
            2,
            f"Expected 2 trades after 2025-01-01 for account O, got {len(stock_trades)}",
        )

        for trade in stock_trades:
            self.assertEqual(
                trade["account"], "O", f"Expected account O, got {trade['account']}"
            )
            self.assertGreaterEqual(
                trade["trade_date"],
                "2025-01-01",
                f"Trade date {trade['trade_date']} is before filter date",
            )

    def test_api_filtered_trades_invalid_scope(self):
        """Test filtered trades with invalid scope parameter"""
        response = self.client.post(
            f"/api/trades/invalid/json/{filter_symbol}/filtered",
            json={"account": "O"},
        )
        self.assertEqual(
            response.status_code,
            400,
            f"Expected status 400 for invalid scope, got {response.status_code}",
        )
        error_data = response.json
        self.assertIn("error", error_data, "Response should contain 'error' field")
        self.assertIn(
            "Invalid scope",
            error_data["error"],
            f"Expected 'Invalid scope' error, got {error_data['error']}",
        )

    def test_api_filtered_trades_no_filters(self):
        """Test filtered trades endpoint with no filters applied"""
        response = self.client.post(
            f"/api/trades/all/json/{filter_symbol}/filtered", json={}
        )
        self.assertEqual(
            response.status_code,
            200,
            f"Expected status 200, got {response.status_code}",
        )

        trades_data = response.json
        # Should return all trades for FILT1
        stock_trades = trades_data["transaction_stats"]["stock"]["all_trades"]
        self.assertEqual(
            len(stock_trades),
            2,
            f"Expected 2 trades without filters, got {len(stock_trades)}",
        )

    def test_api_filtered_trades_account_no_matches(self):
        """Test filtered trades with valid account that has no matching trades"""
        response = self.client.post(
            f"/api/trades/all/json/{filter_symbol}/filtered",
            json={"account": "I"},
        )
        self.assertEqual(
            response.status_code,
            200,
            f"Expected status 200, got {response.status_code}",
        )

        trades_data = response.json
        stock_trades = trades_data["transaction_stats"]["stock"]["all_trades"]
        self.assertEqual(
            len(stock_trades),
            0,
            f"Expected 0 trades for account with no matches, got {len(stock_trades)}",
        )

    def test_api_filtered_trades_invalid_account(self):
        """Test filtered trades with invalid account returns 400"""
        response = self.client.post(
            f"/api/trades/all/json/{filter_symbol}/filtered",
            json={"account": "NONEXISTENT"},
        )
        self.assertEqual(
            response.status_code,
            400,
            f"Expected status 400, got {response.status_code}",
        )

    # Tests for GET query parameter filtering on /api/trades/<scope>/json/<symbol>

    def test_api_positions_with_after_date(self):
        """Test GET with after_date query param filters trades by date"""
        response = self.client.get(
            f"/api/trades/all/json/{filter_symbol}?after_date=2025-01-01"
        )
        self.assertEqual(response.status_code, 200)

        trades_data = response.json
        self.assertEqual(trades_data["filters"]["after_date"], "2025-01-01")

        stock_trades = trades_data["transaction_stats"]["stock"]["all_trades"]
        self.assertEqual(
            len(stock_trades), 2,
            f"Expected 2 trades after 2025-01-01, got {len(stock_trades)}",
        )
        for trade in stock_trades:
            self.assertGreaterEqual(trade["trade_date"], "2025-01-01")

    def test_api_positions_with_invalid_after_date(self):
        """Test GET with invalid after_date returns 400"""
        response = self.client.get(
            f"/api/trades/all/json/{filter_symbol}?after_date=not-a-date"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("after_date", response.json["error"])

    def test_api_positions_with_account_filter(self):
        """Test GET with account query param filters by account"""
        response = self.client.get(
            f"/api/trades/all/json/{filter_symbol}?account=O"
        )
        self.assertEqual(response.status_code, 200)

        trades_data = response.json
        self.assertEqual(trades_data["filters"]["account"], "O")

        stock_trades = trades_data["transaction_stats"]["stock"]["all_trades"]
        self.assertEqual(len(stock_trades), 2)
        for trade in stock_trades:
            self.assertEqual(trade["account"], "O")

    def test_api_positions_with_both_filters(self):
        """Test GET with both after_date and account query params"""
        response = self.client.get(
            f"/api/trades/all/json/{filter_symbol}?after_date=2025-01-01&account=O"
        )
        self.assertEqual(response.status_code, 200)

        trades_data = response.json
        self.assertEqual(trades_data["filters"]["after_date"], "2025-01-01")
        self.assertEqual(trades_data["filters"]["account"], "O")

        stock_trades = trades_data["transaction_stats"]["stock"]["all_trades"]
        self.assertEqual(len(stock_trades), 2)
        for trade in stock_trades:
            self.assertEqual(trade["account"], "O")
            self.assertGreaterEqual(trade["trade_date"], "2025-01-01")

    def test_api_positions_without_filters_no_filters_key(self):
        """Test GET without query params does not include filters key"""
        response = self.client.get("/api/trades/all/json/FAKE1")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("filters", response.json)

    def test_api_positions_with_invalid_account(self):
        """Test GET with invalid account returns 400"""
        response = self.client.get(
            f"/api/trades/all/json/{filter_symbol}?account=INVALID"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("account", response.json["error"])

    # Tests for PATCH /api/trade/update/<id>

    def test_api_update_trade(self):
        """PATCH with all three editable fields updates the database record."""
        transaction_id = self.first_transaction.id
        payload = {
            "reason": "Updated reason",
            "initial_stop_price": 130.00,
            "projected_sell_price": 175.00,
        }

        response = self.client.patch(
            f"/api/trade/update/{transaction_id}",
            json=payload,
        )
        self.assertEqual(
            response.status_code, 200,
            f"Expected 200, got {response.status_code}: {response.json}",
        )

        body = response.json
        self.assertTrue(body["success"])
        self.assertEqual(body["updated"]["reason"], "Updated reason")
        self.assertEqual(body["updated"]["initial_stop_price"], 130.00)
        self.assertEqual(body["updated"]["projected_sell_price"], 175.00)

        # Confirm the DB was actually written
        updated = db.session.get(TradeTransaction, transaction_id)
        self.assertEqual(updated.reason, "Updated reason")
        self.assertAlmostEqual(updated.initial_stop_price, 130.00)
        self.assertAlmostEqual(updated.projected_sell_price, 175.00)

    def test_api_update_trade_partial(self):
        """PATCH with only reason leaves the price fields unchanged."""
        transaction_id = self.first_transaction.id
        original_stop = self.first_transaction.initial_stop_price

        response = self.client.patch(
            f"/api/trade/update/{transaction_id}",
            json={"reason": "Partial update only"},
        )
        self.assertEqual(response.status_code, 200)

        updated = db.session.get(TradeTransaction, transaction_id)
        self.assertEqual(updated.reason, "Partial update only")
        # Price fields must be untouched
        self.assertEqual(updated.initial_stop_price, original_stop)

    def test_api_update_trade_clear_fields(self):
        """PATCH with null values clears optional fields."""
        transaction_id = self.first_transaction.id

        response = self.client.patch(
            f"/api/trade/update/{transaction_id}",
            json={"reason": None, "initial_stop_price": None},
        )
        self.assertEqual(response.status_code, 200)

        updated = db.session.get(TradeTransaction, transaction_id)
        self.assertIsNone(updated.reason)
        self.assertIsNone(updated.initial_stop_price)

    def test_api_update_trade_not_found(self):
        """PATCH with a non-existent trade ID returns 404."""
        response = self.client.patch(
            "/api/trade/update/999999",
            json={"reason": "Ghost trade"},
        )
        self.assertEqual(
            response.status_code, 404,
            f"Expected 404, got {response.status_code}",
        )
        self.assertIn("error", response.json)

    def test_api_update_trade_no_valid_fields(self):
        """PATCH with a body containing no allowed fields returns 400."""
        transaction_id = self.first_transaction.id
        response = self.client.patch(
            f"/api/trade/update/{transaction_id}",
            json={"symbol": "HACKED", "price": 0.01},
        )
        self.assertEqual(
            response.status_code, 400,
            f"Expected 400, got {response.status_code}",
        )
        self.assertIn("error", response.json)

    def test_api_update_trade_no_json_body(self):
        """PATCH with a non-JSON body returns 400."""
        transaction_id = self.first_transaction.id
        response = self.client.patch(
            f"/api/trade/update/{transaction_id}",
            data="not json",
            content_type="text/plain",
        )
        self.assertEqual(
            response.status_code, 400,
            f"Expected 400, got {response.status_code}",
        )
        self.assertIn("error", response.json)

    def test_api_update_trade_reason_too_long(self):
        """PATCH with reason exceeding 500 chars returns 422."""
        transaction_id = self.first_transaction.id
        response = self.client.patch(
            f"/api/trade/update/{transaction_id}",
            json={"reason": "x" * 501},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("reason", response.json["fields"])

    def test_api_update_trade_negative_stop_price(self):
        """PATCH with a negative initial_stop_price returns 422."""
        transaction_id = self.first_transaction.id
        response = self.client.patch(
            f"/api/trade/update/{transaction_id}",
            json={"initial_stop_price": -10.0},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("initial_stop_price", response.json["fields"])

    def test_api_update_trade_zero_target_price(self):
        """PATCH with projected_sell_price of zero returns 422."""
        transaction_id = self.first_transaction.id
        response = self.client.patch(
            f"/api/trade/update/{transaction_id}",
            json={"projected_sell_price": 0},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("projected_sell_price", response.json["fields"])

    def test_api_update_trade_non_numeric_price(self):
        """PATCH with a non-numeric price string returns 422."""
        transaction_id = self.first_transaction.id
        response = self.client.patch(
            f"/api/trade/update/{transaction_id}",
            json={"initial_stop_price": "not-a-number"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("initial_stop_price", response.json["fields"])

    def test_api_update_trade_multiple_validation_errors(self):
        """PATCH with multiple invalid fields returns all errors in one 422."""
        transaction_id = self.first_transaction.id
        response = self.client.patch(
            f"/api/trade/update/{transaction_id}",
            json={
                "reason": "y" * 501,
                "initial_stop_price": -5.0,
                "projected_sell_price": 0,
            },
        )
        self.assertEqual(response.status_code, 422)
        fields = response.json["fields"]
        self.assertIn("reason", fields)
        self.assertIn("initial_stop_price", fields)
        self.assertIn("projected_sell_price", fields)

    # Tests for asset_type query parameter

    def test_api_positions_asset_type_stock(self):
        """Test GET with asset_type=stock returns only stock section"""
        response = self.client.get("/api/trades/all/json/FAKE1?asset_type=stock")
        self.assertEqual(response.status_code, 200)

        trades_data = response.json
        transaction_stats = trades_data["transaction_stats"]
        self.assertIn("stock", transaction_stats, "Response should have 'stock' key")
        self.assertNotIn("option", transaction_stats, "Response should not have 'option' key")
        self.assertEqual(trades_data["filters"]["asset_type"], "stock")

    def test_api_positions_asset_type_option(self):
        """Test GET with asset_type=option returns only option section"""
        response = self.client.get("/api/trades/all/json/FAKE1?asset_type=option")
        self.assertEqual(response.status_code, 200)

        trades_data = response.json
        transaction_stats = trades_data["transaction_stats"]
        self.assertIn("option", transaction_stats, "Response should have 'option' key")
        self.assertNotIn("stock", transaction_stats, "Response should not have 'stock' key")
        self.assertEqual(trades_data["filters"]["asset_type"], "option")

        # Verify option trades exist for FAKE1
        option_trades = transaction_stats["option"]["all_trades"]
        self.assertGreater(len(option_trades), 0, "FAKE1 should have option trades")

    def test_api_positions_asset_type_all(self):
        """Test GET with asset_type=all (or omitted) returns both sections"""
        # Explicit asset_type=all
        response = self.client.get("/api/trades/all/json/FAKE1?asset_type=all")
        self.assertEqual(response.status_code, 200)

        trades_data = response.json
        transaction_stats = trades_data["transaction_stats"]
        self.assertIn("stock", transaction_stats)
        self.assertIn("option", transaction_stats)
        self.assertNotIn("filters", trades_data, "asset_type=all should not add filters")

        # Omitted asset_type (default)
        response2 = self.client.get("/api/trades/all/json/FAKE1")
        self.assertEqual(response2.status_code, 200)
        trades_data2 = response2.json
        self.assertIn("stock", trades_data2["transaction_stats"])
        self.assertIn("option", trades_data2["transaction_stats"])

    def test_api_positions_asset_type_invalid(self):
        """Test GET with invalid asset_type returns 400"""
        response = self.client.get("/api/trades/all/json/FAKE1?asset_type=futures")
        self.assertEqual(response.status_code, 400)
        self.assertIn("asset_type", response.json["error"])

    def test_api_get_stock_data(self):
        """GET /api/get_stock_data/<symbol> returns JSON from YahooFinance."""
        mock_data = {"currentPrice": 150.0, "symbol": "FAKE1", "quoteType": "EQUITY"}
        with patch("app.routes.api_routes.YahooFinance") as MockYF:
            instance = MockYF.return_value
            instance.get_stock_data.return_value = None
            instance.get_results.return_value = mock_data

            response = self.client.get("/api/get_stock_data/FAKE1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, mock_data)

    def test_api_current_holdings_symbols_json(self):
        """GET /api/trade/current_holdings_symbols_json returns deduplicated [symbol, name] pairs."""
        response = self.client.get("/api/trade/current_holdings_symbols_json")
        self.assertEqual(response.status_code, 200)

        symbols = response.json
        self.assertIsInstance(symbols, list)
        # Each entry must be a two-element list of [symbol, name]
        for entry in symbols:
            self.assertEqual(len(entry), 2, f"Expected [symbol, name] pair, got {entry}")
        # FAKE1 has both stock and option open positions — should appear only once
        symbol_names = [entry[0] for entry in symbols]
        self.assertEqual(len(symbol_names), len(set(symbol_names)), "Symbols should be deduplicated")

    # --- Web route tests ---

    def test_web_view_transaction(self):
        """GET /transaction/<id> returns 200 for an existing transaction."""
        transaction_id = self.first_transaction.id
        response = self.client.get(f"/transaction/{transaction_id}")
        self.assertEqual(response.status_code, 200)

    def test_web_view_transaction_not_found(self):
        """GET /transaction/<id> returns 404 for a non-existent ID."""
        response = self.client.get("/transaction/999999")
        self.assertEqual(response.status_code, 404)

    def test_web_trade_stats_summary(self):
        """GET /trade_stats_summary returns 200 and renders without error."""
        response = self.client.get("/trade_stats_summary")
        self.assertEqual(response.status_code, 200)

    def test_web_open_trades(self):
        """GET /open_trades/<symbol> returns 200 (route handles missing method gracefully)."""
        response = self.client.get("/open_trades/FAKE3")
        self.assertEqual(response.status_code, 200)


class TestAPIAuth(unittest.TestCase):
    """Tests that the API key enforcement works when not in dev mode."""

    def setUp(self):
        # Remove dev bypass so auth is enforced
        self._prev_flask_env = os.environ.pop("FLASK_ENV", None)
        os.environ["API_SECRET_KEY"] = "test-secret-key"

        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        self.client = self.app.test_client()

        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        self.app_context.pop()
        if self._prev_flask_env is not None:
            os.environ["FLASK_ENV"] = self._prev_flask_env
        os.environ.pop("API_SECRET_KEY", None)

    def test_missing_api_key_returns_401(self):
        """Request without X-API-KEY returns 401."""
        response = self.client.get("/api/trade/symbols_json")
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json)

    def test_wrong_api_key_returns_401(self):
        """Request with incorrect X-API-KEY returns 401."""
        response = self.client.get(
            "/api/trade/symbols_json",
            headers={"X-API-KEY": "wrong-key"},
        )
        self.assertEqual(response.status_code, 401)

    def test_correct_api_key_returns_200(self):
        """Request with correct X-API-KEY returns 200."""
        response = self.client.get(
            "/api/trade/symbols_json",
            headers={"X-API-KEY": "test-secret-key"},
        )
        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main(failfast=True)
