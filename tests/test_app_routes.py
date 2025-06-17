import unittest
import logging
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

# Global data structure for test tickers and names
TEST_SECURITIES = {
    "FAKE1": "Fake Company One",
    "FAKE2": "Fake Company Two",
    "FAKE3": "Fake Company Three",
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
        ]

        for row in transaction_rows:
            self.db_inserter.insert_transaction(row)
            test_logger.info(
                f"Inserted transaction: {row['symbol']} {row['action']} {row['reason']}"
            )

        # Retrieve the ID of the first inserted transaction
        self.first_transaction = TradeTransaction.query.filter_by(
            reason="Test Buy FAKE1"
        ).first()

        test_logger.info("Test setup completed")

    def tearDown(self):
        # Clean up database

        TradeTransaction.query.filter(
            TradeTransaction.symbol.in_(
                [
                    "FAKE1",
                    "FAKE2",
                ]
            )
        ).delete(synchronize_session=False)

        Security.query.filter(Security.symbol.in_(TEST_SECURITIES.keys())).delete(
            synchronize_session=False
        )

        db.session.commit()
        db.session.remove()
        self.app_context.pop()
        test_logger.info("Test teardown completed")

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

    def test_update_transaction_route(self):
        """Test updating a transaction works correctly"""
        data = {
            "reason": "No real reason",
            "initial_stop_price": "123.45",
            "projected_sell_price": "150.00",
        }

        # Get transaction ID

        self.first_transaction = TradeTransaction.query.filter_by(
            reason="Test Buy FAKE1"
        ).first()

        transaction_id = self.first_transaction.id
        original_transaction = TradeTransaction.query.get(transaction_id)
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
        updated_transaction = TradeTransaction.query.get(transaction_id)

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

        stock_trades = transaction_stats["stock"]["all_trades"]
        self.assertEqual(
            len(stock_trades), 1, f"Expected 1 stock trades, got {len(stock_trades)}"
        )

        stock_buy_trade = stock_trades[0]
        self.assertEqual(
            stock_buy_trade["current_sold_qty"],
            100.00,
            f"Expected current_sold_qty == 100, got {stock_buy_trade['current_sold_qty']}",
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
            len(option_trades), 0, f"Expected 0 option trades, got {len(option_trades)}"
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

        # Verify holdings data structure
        for holding in holdings:
            self.assertIn("symbol", holding, "Holding missing 'symbol' field")
            self.assertIn("shares", holding, "Holding missing 'shares' field")
            self.assertIn(
                "average_price", holding, "Holding missing 'average_price' field"
            )
            self.assertIn("profit_loss", holding, "Holding missing 'profit_loss' field")
            self.assertIn("name", holding, "Holding missing 'name' field")

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


if __name__ == "__main__":
    unittest.main(failfast=True)
