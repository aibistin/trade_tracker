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
            # Option trades for FAKE1 (closed)
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
            # Open option position for FAKE3 (no sell)
            {
                "symbol": "FAKE3",
                "action": "BO",
                "label": "FAKE3 06/20/2025 220.00 C",
                "trade_type": "C",
                "trade_date": "2025-03-15 11:00",
                "expiration_date": "2025-06-20",
                "reason": "Test Buy Option FAKE3 Open",
                "quantity": 2,
                "price": 3.50,
                "amount": -700.0,
                "target_price": 220.0,
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

        # Verify FAKE3 open positions are in holdings (stock + option)
        fake3_holdings = [h for h in holdings if h["symbol"] == "FAKE3"]
        self.assertEqual(len(fake3_holdings), 2, "FAKE3 should have 2 open holdings (stock + option)")
        fake3_stock = [h for h in fake3_holdings if h["trade_type"] == "L"]
        self.assertEqual(len(fake3_stock), 1, "FAKE3 should have 1 open stock holding")
        self.assertEqual(fake3_stock[0]["shares"], 25)
        self.assertEqual(fake3_stock[0]["trade_type"], "L")

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

    def test_web_trade_detail_by_symbol(self):
        """GET /trade/detail/<symbol> renders the stock summary and trades."""
        response = self.client.get("/trade/detail/FAKE1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"FAKE1", response.data)

    def test_web_trade_detail_no_stock_trades_returns_404(self):
        """GET /trade/detail/<symbol> returns 404 for a symbol with no stock trades."""
        response = self.client.get("/trade/detail/NOSUCH")
        self.assertEqual(response.status_code, 404)

    def test_web_update_transaction_not_found(self):
        """POST /update_transaction/<id> returns 404 for a non-existent ID."""
        response = self.client.post("/update_transaction/999999", data={"reason": "x"})
        self.assertEqual(response.status_code, 404)

    def test_web_update_transaction_validation_error_redirects(self):
        """POST /update_transaction/<id> with an invalid price redirects back."""
        transaction_id = db.session.execute(
            select(TradeTransaction.id).limit(1)
        ).scalar()
        response = self.client.post(
            f"/update_transaction/{transaction_id}",
            data={"initial_stop_price": "-5"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(f"transaction/{transaction_id}", response.headers["Location"])

    def test_dashboard_summary_structure(self):
        """Dashboard summary returns correct top-level structure."""
        response = self.client.get("/api/dashboard/summary")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("overall", data)
        self.assertIn("by_symbol", data)

        overall = data["overall"]
        for key in ("total_realized_pnl", "total_winning_trades", "total_losing_trades",
                    "batting_average", "symbols_traded"):
            self.assertIn(key, overall, f"Missing key in overall: {key}")

    def test_dashboard_summary_overall_types(self):
        """Dashboard summary overall values have correct types and FAKE1 option is a win."""
        response = self.client.get("/api/dashboard/summary")
        data = response.get_json()
        overall = data["overall"]

        # Type checks
        self.assertIsInstance(overall["total_winning_trades"], int)
        self.assertIsInstance(overall["total_losing_trades"], int)
        self.assertIsInstance(overall["total_realized_pnl"], float)
        self.assertIsInstance(overall["batting_average"], float)
        self.assertIsInstance(overall["symbols_traded"], int)
        self.assertGreaterEqual(overall["total_winning_trades"], 0)
        self.assertGreaterEqual(overall["total_losing_trades"], 0)
        self.assertGreaterEqual(overall["batting_average"], 0.0)
        self.assertLessEqual(overall["batting_average"], 1.0)

        # FAKE1 option (buy $5, sell $8) should show as a win in by_symbol
        fake1 = next((e for e in data["by_symbol"] if e["symbol"] == "FAKE1"), None)
        self.assertIsNotNone(fake1, "FAKE1 should appear in by_symbol")
        self.assertIsNotNone(fake1["option"], "FAKE1 should have option stats")
        self.assertEqual(fake1["option"]["winning_trades_count"], 1)
        self.assertEqual(fake1["option"]["losing_trades_count"], 0)

    def test_dashboard_summary_by_symbol_entries(self):
        """Each by_symbol entry has required fields."""
        response = self.client.get("/api/dashboard/summary")
        data = response.get_json()
        self.assertTrue(len(data["by_symbol"]) > 0)

        entry = data["by_symbol"][0]
        self.assertIn("symbol", entry)
        self.assertIn("name", entry)
        self.assertIn("combined", entry)
        combined = entry["combined"]
        for key in ("winning_trades_count", "losing_trades_count", "batting_average", "profit_loss"):
            self.assertIn(key, combined, f"Missing combined key: {key}")

    def test_dashboard_pnl_over_time_structure(self):
        """pnl_over_time returns monthly and quarterly lists with required keys."""
        response = self.client.get("/api/dashboard/pnl_over_time")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn("monthly", data)
        self.assertIn("quarterly", data)

        required_keys = ("period", "label", "winning_trades", "losing_trades",
                         "batting_average", "pnl_dollars", "pnl_pct_avg")
        for bucket_list in (data["monthly"], data["quarterly"]):
            self.assertIsInstance(bucket_list, list)
            if bucket_list:
                for key in required_keys:
                    self.assertIn(key, bucket_list[0], f"Missing key in bucket: {key}")

    def test_dashboard_pnl_over_time_values(self):
        """pnl_over_time monthly and quarterly lists are sorted and well-formed.

        FAKE1 option closed 2024-12-15 → 2024-12 must appear.
        FILT1 stock  closed 2025-02-02 → 2025-02 must appear.
        """
        response = self.client.get("/api/dashboard/pnl_over_time")
        data = response.get_json()

        monthly = {b["period"]: b for b in data["monthly"]}
        quarterly = {b["period"]: b for b in data["quarterly"]}

        # Both test-data periods must be present
        self.assertIn("2024-12", monthly)
        self.assertIn("2025-02", monthly)
        self.assertIn("2024-Q4", quarterly)
        self.assertIn("2025-Q1", quarterly)

        # Verify list is chronologically sorted
        periods = [b["period"] for b in data["monthly"]]
        self.assertEqual(periods, sorted(periods))

        # FAKE1 option win must be counted in 2024-12
        self.assertGreaterEqual(monthly["2024-12"]["winning_trades"], 1)

        # Each bucket has valid types
        bucket = data["monthly"][0]
        self.assertIsInstance(bucket["winning_trades"], int)
        self.assertIsInstance(bucket["losing_trades"], int)
        self.assertIsInstance(bucket["pnl_dollars"], float)
        self.assertIsInstance(bucket["batting_average"], float)

    def test_dashboard_pnl_over_time_asset_type_filter(self):
        """asset_type filter changes results: stock-only total differs from all."""
        all_resp = self.client.get("/api/dashboard/pnl_over_time?asset_type=all")
        stock_resp = self.client.get("/api/dashboard/pnl_over_time?asset_type=stock")
        self.assertEqual(all_resp.status_code, 200)
        self.assertEqual(stock_resp.status_code, 200)

        all_total = sum(b["winning_trades"] for b in all_resp.get_json()["monthly"])
        stock_total = sum(b["winning_trades"] for b in stock_resp.get_json()["monthly"])
        # Stock-only should have fewer wins than all (options excluded)
        self.assertLess(stock_total, all_total)

    def test_dashboard_pnl_over_time_invalid_asset_type(self):
        """Invalid asset_type returns 400."""
        response = self.client.get("/api/dashboard/pnl_over_time?asset_type=bad")
        self.assertEqual(response.status_code, 400)

    # --- Holdings endpoint tests (GET /api/holdings) ---

    @patch("lib.yfinance.YahooFinance")
    def test_api_holdings_structure(self, MockYF):
        """GET /api/holdings returns stock and option sections with correct structure."""
        instance = MockYF.return_value
        instance.get_stock_data.return_value = None
        instance.get_results.return_value = {"currentPrice": 210.0, "quoteType": "EQUITY"}

        response = self.client.get("/api/holdings")
        self.assertEqual(response.status_code, 200)

        data = response.json
        self.assertIn("stock", data)
        self.assertIn("option", data)
        for section_key in ("stock", "option"):
            section = data[section_key]
            self.assertIn("positions", section)
            self.assertIn("total_cost_basis", section)
            self.assertIn("total_market_value", section)
            self.assertIn("total_unrealized_pnl", section)

    @patch("lib.yfinance.YahooFinance")
    def test_api_holdings_shows_only_open_positions(self, MockYF):
        """Holdings endpoint only returns genuinely open positions (FAKE3 stock, not FAKE1/FAKE2)."""
        instance = MockYF.return_value
        instance.get_stock_data.return_value = None
        instance.get_results.return_value = {"currentPrice": 210.0, "quoteType": "EQUITY"}

        response = self.client.get("/api/holdings")
        self.assertEqual(response.status_code, 200)

        data = response.json
        stock_positions = data["stock"]["positions"]
        stock_symbols = [p["symbol"] for p in stock_positions]

        # FAKE3 has an open stock position (buy, no sell)
        self.assertIn("FAKE3", stock_symbols, "FAKE3 should be in open stock holdings")
        # FAKE1 stock is fully closed (buy 100, sell 100)
        self.assertNotIn("FAKE1", stock_symbols, "FAKE1 stock should not be in open holdings")
        # FAKE2 stock is fully closed
        self.assertNotIn("FAKE2", stock_symbols, "FAKE2 stock should not be in open holdings")

    @patch("lib.yfinance.YahooFinance")
    def test_api_holdings_stock_position_fields(self, MockYF):
        """Each stock position has all required fields with correct values."""
        instance = MockYF.return_value
        instance.get_stock_data.return_value = None
        instance.get_results.return_value = {"currentPrice": 210.0, "quoteType": "EQUITY"}

        response = self.client.get("/api/holdings")
        data = response.json

        stock_positions = data["stock"]["positions"]
        fake3 = next((p for p in stock_positions if p["symbol"] == "FAKE3"), None)
        self.assertIsNotNone(fake3, "FAKE3 should be in stock positions")

        required_fields = [
            "symbol", "name", "trade_type", "quantity", "avg_cost",
            "cost_basis", "current_price", "market_value", "unrealized_pnl", "pnl_pct",
        ]
        for field in required_fields:
            self.assertIn(field, fake3, f"Missing field: {field}")

        self.assertEqual(fake3["quantity"], 25)
        self.assertEqual(fake3["avg_cost"], 200.0)
        self.assertEqual(fake3["cost_basis"], 5000.0)
        self.assertEqual(fake3["current_price"], 210.0)
        self.assertEqual(fake3["market_value"], 5250.0)
        self.assertEqual(fake3["unrealized_pnl"], 250.0)
        self.assertEqual(fake3["pnl_pct"], 5.0)

    @patch("lib.yfinance.YahooFinance")
    def test_api_holdings_option_open_positions(self, MockYF):
        """FAKE3 open option position appears in option section, FAKE1 closed option does not."""
        instance = MockYF.return_value
        instance.get_stock_data.return_value = None
        instance.get_results.return_value = {"lastPrice": 4.50, "quoteType": "OPTION"}

        response = self.client.get("/api/holdings")
        data = response.json

        option_positions = data["option"]["positions"]
        option_symbols = [p["symbol"] for p in option_positions]

        # FAKE3 has an open option (BO, no SC)
        self.assertIn("FAKE3", option_symbols, "FAKE3 should have an open option position")
        # FAKE1 option is fully closed (BO + SC)
        fake1_options = [p for p in option_positions if p["symbol"] == "FAKE1"]
        self.assertEqual(len(fake1_options), 0, "FAKE1 option should be closed")

        fake3_opt = next(p for p in option_positions if p["symbol"] == "FAKE3")
        self.assertEqual(fake3_opt["quantity"], 2)
        self.assertEqual(fake3_opt["avg_cost"], 3.50)
        self.assertEqual(fake3_opt["cost_basis"], 700.0)  # 3.50 * 2 * 100

    @patch("lib.yfinance.YahooFinance")
    def test_api_holdings_totals(self, MockYF):
        """Holdings totals include values from open positions and are consistent."""
        instance = MockYF.return_value
        instance.get_stock_data.return_value = None
        instance.get_results.return_value = {"currentPrice": 210.0, "quoteType": "EQUITY"}

        response = self.client.get("/api/holdings")
        data = response.json

        stock = data["stock"]
        # total_cost_basis should include FAKE3's 5000.0 (plus any real DB data)
        self.assertGreaterEqual(stock["total_cost_basis"], 5000.0)
        # Totals should be internally consistent
        self.assertAlmostEqual(
            stock["total_unrealized_pnl"],
            stock["total_market_value"] - stock["total_cost_basis"],
            places=2,
        )

    @patch("lib.yfinance.YahooFinance")
    def test_api_holdings_price_fetch_failure(self, MockYF):
        """Holdings still returns positions when price fetch fails (prices are None)."""
        instance = MockYF.return_value
        instance.get_stock_data.side_effect = Exception("API down")

        response = self.client.get("/api/holdings")
        self.assertEqual(response.status_code, 200)

        data = response.json
        stock_positions = data["stock"]["positions"]
        fake3 = next((p for p in stock_positions if p["symbol"] == "FAKE3"), None)
        self.assertIsNotNone(fake3)
        self.assertIsNone(fake3["current_price"])
        self.assertIsNone(fake3["market_value"])

    # --- Sparkline / ticker history endpoint tests ---

    @patch("app.routes.api_routes.yf_lib")
    def test_api_ticker_history_structure(self, mock_yf):
        """GET /api/ticker/history/<symbol> returns prices and trades arrays."""
        import pandas as pd
        mock_ticker = MagicMock()
        mock_yf.Ticker.return_value = mock_ticker
        mock_ticker.history.return_value = pd.DataFrame({
            "Open": [100.0, 101.0],
            "High": [102.0, 103.0],
            "Low": [99.0, 100.0],
            "Close": [101.0, 102.0],
            "Volume": [1000, 2000],
        }, index=pd.to_datetime(["2025-03-01", "2025-03-02"]))

        response = self.client.get("/api/ticker/history/FAKE3")
        self.assertEqual(response.status_code, 200)

        data = response.json
        self.assertIn("symbol", data)
        self.assertIn("prices", data)
        self.assertIn("trades", data)
        self.assertEqual(data["symbol"], "FAKE3")
        self.assertEqual(len(data["prices"]), 2)

        # Verify price point structure
        price = data["prices"][0]
        for field in ("date", "open", "high", "low", "close", "volume"):
            self.assertIn(field, price, f"Missing price field: {field}")

    @patch("app.routes.api_routes.yf_lib")
    def test_api_ticker_history_trades_included(self, mock_yf):
        """Trade annotations are included in the response."""
        import pandas as pd
        mock_ticker = MagicMock()
        mock_yf.Ticker.return_value = mock_ticker
        mock_ticker.history.return_value = pd.DataFrame(
            columns=["Open", "High", "Low", "Close", "Volume"],
            index=pd.DatetimeIndex([]),
        )

        response = self.client.get("/api/ticker/history/FAKE3")
        data = response.json

        # FAKE3 has a buy stock + buy option in test data
        self.assertGreaterEqual(len(data["trades"]), 1)
        trade = data["trades"][0]
        for field in ("date", "action", "price", "quantity"):
            self.assertIn(field, trade, f"Missing trade field: {field}")

    @patch("app.routes.api_routes.yf_lib")
    def test_api_ticker_history_invalid_period(self, mock_yf):
        """Invalid period returns 400."""
        response = self.client.get("/api/ticker/history/FAKE3?period=invalid")
        self.assertEqual(response.status_code, 400)
        self.assertIn("period", response.json["error"])

    @patch("app.routes.api_routes.yf_lib")
    def test_api_ticker_history_invalid_interval(self, mock_yf):
        """Invalid interval returns 400."""
        response = self.client.get("/api/ticker/history/FAKE3?interval=invalid")
        self.assertEqual(response.status_code, 400)
        self.assertIn("interval", response.json["error"])

    @patch("app.routes.api_routes.yf_lib")
    def test_api_ticker_history_custom_params(self, mock_yf):
        """Custom period and interval params are accepted."""
        import pandas as pd
        mock_ticker = MagicMock()
        mock_yf.Ticker.return_value = mock_ticker
        mock_ticker.history.return_value = pd.DataFrame(
            columns=["Open", "High", "Low", "Close", "Volume"],
            index=pd.DatetimeIndex([]),
        )

        response = self.client.get("/api/ticker/history/FAKE3?period=1y&interval=1wk")
        self.assertEqual(response.status_code, 200)
        mock_ticker.history.assert_called_once_with(period="1y", interval="1wk")


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
