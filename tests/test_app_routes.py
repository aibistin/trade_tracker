import unittest
from app import app
from app.models.models import (
    Security,
    TradeTransaction,
)

# Make sure to import your db instance here
from app.extensions import db
from lib.db_utils import DatabaseInserter


print(__file__)

# Global data structure for test tickers and names
TEST_SECURITIES = {
    "FAKE1": "Fake Company One",
    "FAKE2": "Fake Company Two",
    "FAKE3": "Fake Company Three",
}
STOCK_TRADES_DB = "data/stock_trades.db"


class TestAppRoutes(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        # self.db_inserter = DatabaseInserter(STOCK_TRADES_DB)

        # Use the same db instance from your Flask app
        with app.app_context():
            db.create_all()  # Create tables in the in-memory database
            self.db_inserter = DatabaseInserter(db=db)

        # Insert test data into the security table using the global data structure
        for symbol, name in TEST_SECURITIES.items():
            self.db_inserter.insert_security({"symbol": symbol, "name": name})

        # Insert test data into the trade_transaction table
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
            # print(f"Inserted transaction: {row}")

        # Retrieve the ID of the first inserted transaction
        with app.app_context():
            self.first_transaction_id = TradeTransaction.query.filter_by(
                reason="Test Buy FAKE1"
            ).first()


    def tearDown(self):
        # Clean up the test database

        with app.app_context():
            # Delete test transactions
            db.session.query(TradeTransaction).filter(
                TradeTransaction.reason.in_(
                    [
                        "Test Buy FAKE1",
                        "Test Buy FAKE2",
                        "Test Sell FAKE1",
                        "Test Sell FAKE2",
                    ]
                )
            ).delete()

            # Delete test securities using the global data structure
            db.session.query(Security).filter(
                Security.symbol.in_(TEST_SECURITIES.keys())
            ).delete()

            # db.session.remove()
            # db.drop_all()
            db.session.commit()
            db.session.remove()

    def test_index_route(self):
        response = self.app.get("/")  # Test the index route
        self.assertEqual(response.status_code, 200)
        # Check if the title is in the response
        self.assertIn(b"Trade Tracker", response.data)

    def test_recent_trades_route(self):
        response = self.app.get("/recent_trades/5")  # Test with 5 days
        self.assertEqual(response.status_code, 200)
        # Add more assertions to check the content of the response based on your expected data

    def test_trades_by_symbol_route(self):
        response = self.app.get("/trades/ABC")  # Test with symbol ABC
        self.assertEqual(response.status_code, 200)
        # Add more assertions

    def test_update_transaction_route(self):
        # Test the POST request to update a transaction
        data = {
            "reason": "Test Update",
            "initial_stop_price": "123.45",
            "projected_sell_price": "150.00",
        }
        transaction_id = self.first_transaction_id.id
        print("Test update using transaction id: " + str(transaction_id))
        response = self.app.post( "/update_transaction/" + str(transaction_id), data=data)

        # Route is redirected to view_transaction route
        self.assertEqual(response.status_code, 302)
        # You might need to query the database to verify the update

    # Add more test methods for other routes and error handling


if __name__ == "__main__":
    unittest.main()
