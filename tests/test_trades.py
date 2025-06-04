import unittest
from datetime import datetime
import json
from typing import List, cast
from lib.models.Trades import Trades, BuyTrades
from lib.models.Trade import Trade, BuyTrade, SellTrade


class TestTradesClasses(unittest.TestCase):
    def setUp(self):
        # Create sample trades

        self.trade1 = BuyTrade(
            {
                "trade_id": "T1",
                "symbol": "TEST",
                "action": "B",
                "trade_date": datetime(2023, 5, 15),
                "quantity": 100,
                "price": 50.0,
            }  # type: ignore
        )

        self.trade2 = SellTrade(
            {
                "trade_id": "S1",
                "symbol": "TEST",
                "action": "S",
                "trade_date": datetime(2023, 5, 16),
                "quantity": 50,
                "price": 55.0,
            }  # type: ignore
        )

        self.trade3 = BuyTrade(
            {
                "trade_id": "B1",
                "symbol": "TEST",
                "action": "B",
                "trade_date": datetime(2023, 5, 17),
                "quantity": 200,
                "price": 52.0,
            }  # type: ignore
        )

        # Create trades collection
        self.trades = Trades(security_type="stock")
        self.trades.add_trade(self.trade1)
        self.trades.add_trade(self.trade2)
        self.trades.add_trade(self.trade3)

    def test_add_trades(self):
        """Test adding different trade types"""
        self.assertEqual(len(self.trades.trades), 3)
        self.assertEqual(len(self.trades.buy_trades), 2)
        self.assertEqual(len(self.trades.sell_trades), 1)

        # Verify correct types
        self.assertIsInstance(self.trades.buy_trades[0], BuyTrade)
        self.assertIsInstance(self.trades.sell_trades[0], SellTrade)

    def test_sort_trades(self):
        """Test trade sorting functionality"""
        # Add trades in reverse date order
        self.trades.trades = []
        self.trades.buy_trades = []
        self.trades.sell_trades = []

        self.trades.add_trade(self.trade3)  # May 17
        self.trades.add_trade(self.trade2)  # May 16
        self.trades.add_trade(self.trade1)  # May 15

        # Sort trades
        self.trades.sort_trades()

        # Verify date order
        self.assertEqual(self.trades.trades[0].trade_id, "T1")
        self.assertEqual(self.trades.trades[1].trade_id, "S1")
        self.assertEqual(self.trades.trades[2].trade_id, "B1")

        # Verify buy trades order
        self.assertEqual(self.trades.buy_trades[0].trade_id, "T1")
        self.assertEqual(self.trades.buy_trades[1].trade_id, "B1")

    def test_json_serialization(self):
        """Test trades collection serialization to JSON"""
        trade_dict = self.trades.to_dict()

        # Verify top-level structure
        self.assertEqual(trade_dict["security_type"], "stock")
        self.assertEqual(len(trade_dict["trades"]), 3)
        self.assertEqual(len(trade_dict["buy_trades"]), 2)
        self.assertEqual(len(trade_dict["sell_trades"]), 1)

        # Verify trade content
        self.assertEqual(trade_dict["trades"][0]["trade_id"], "T1")
        self.assertEqual(trade_dict["buy_trades"][1]["trade_id"], "B1")
        self.assertEqual(trade_dict["sell_trades"][0]["trade_id"], "S1")

        # Test full JSON serialization
        import json

        json_str = json.dumps(trade_dict)
        self.assertIsInstance(json_str, str)
        reconstructed = json.loads(json_str)
        self.assertEqual(len(reconstructed["trades"]), 3)


class TestBuyTradesClass(unittest.TestCase):
    def setUp(self):
        # Create sample buy trades with different dates
        self.buy1 = BuyTrade(
            {
                "trade_id": "B1",
                "symbol": "TEST",
                "action": "B",
                "trade_date": datetime(2023, 5, 10),
                "quantity": 100,
                "price": 50.0,
            }  # type: ignore
        )

        self.buy2 = BuyTrade(
            {
                "trade_id": "B2",
                "symbol": "TEST",
                "action": "B",
                "trade_date": datetime(2023, 5, 15),
                "quantity": 200,
                "price": 52.0,
            }  # type: ignore
        )

        self.buy3 = BuyTrade(
            {
                "trade_id": "B3",
                "symbol": "TEST",
                "action": "B",
                "trade_date": datetime(2023, 5, 20),
                "quantity": 150,
                "price": 53.0,
            }  # type: ignore
        )

        # Create buy trades collection with date filter
        self.buy_trades = BuyTrades(security_type="stock", after_date_str="2023-05-15")

        # Add trades
        self.buy_trades.add_trade(self.buy1)  # Before filter date
        self.buy_trades.add_trade(self.buy2)  # On filter date
        self.buy_trades.add_trade(self.buy3)  # After filter date

    def test_date_filtering(self):
        """Test date-based filtering of buy trades"""

        # Test explicit filtering
        self.buy_trades.filter_buy_trades()
        self.assertEqual(
            len(self.buy_trades.buy_trades),
            2,
            f"Expected 2 trades after filtering, got {len(self.buy_trades.buy_trades)}",
        )


    def test_add_trade_validation(self):
        """Test type validation when adding trades"""
        with self.assertRaises(TypeError):
            # Try to add non-BuyTrade
            self.buy_trades.add_trade(
                Trade(
                    {
                        "trade_id": "T1",
                        "symbol": "TEST",
                        "action": "S",
                        "trade_date": datetime(2023, 5, 18),
                        "quantity": 50,
                        "price": 51.0,
                    }  # type: ignore
                )
            )

    def test_json_serialization(self):
        """Test buy trades collection serialization"""

        self.buy_trades.filter_buy_trades()

        trade_dict = self.buy_trades.to_dict()

        self.assertEqual(
            trade_dict["security_type"],
            "stock",
            f"Expected security_type 'stock', got {trade_dict['security_type']}",
        )
        self.assertEqual(
            len(trade_dict["buy_trades"]),
            2,
            f"Expected 2 buy trades, got {len(trade_dict['buy_trades'])}",
        )
        self.assertEqual(
            trade_dict["after_date_str"],
            "2023-05-15",
            f"Expected after_date_str '2023-05-15', got {trade_dict['after_date_str']}",
        )

        # Verify date filtering in serialized data
        trade_ids = [t["trade_id"] for t in trade_dict["buy_trades"]]
        self.assertIn("B2", trade_ids, f"Expected B2 in trade_ids, got {trade_ids}")
        self.assertIn("B3", trade_ids, f"Expected B3 in trade_ids, got {trade_ids}")
        self.assertNotIn(
            "B1", trade_ids, f"Expected B1 not to be in trade_ids, got {trade_ids}"
        )

        json_str = json.dumps(trade_dict)
        reconstructed = json.loads(json_str)
        self.assertEqual(
            len(reconstructed["buy_trades"]),
            2,
            f"Expected 2 buy trades after JSON serialization, got {len(reconstructed['buy_trades'])}",
        )


if __name__ == "__main__":
    unittest.main()
