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
                "account": "C",
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
                "account": "C",
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
                "account": "C",
            }  # type: ignore
        )

        # No account
        self.trade4 = BuyTrade(
            {
                "trade_id": "NoAccount_1",
                "symbol": "ACCT0",
                "action": "B",
                "trade_date": datetime(2024, 1, 10),
                "quantity": 1000,
                "price": 100.0,
            }  # type: ignore
        )

        self.trade5 = SellTrade(
            {
                "trade_id": "NoAccount_2",
                "symbol": "ACCT0",
                "action": "S",
                "trade_date": datetime(2024, 2, 16),
                "quantity": 500,
                "price": 200.0,
            }  # type: ignore
        )

        # Create trades collection
        self.trades = Trades(security_type="stock")
        self.trades.add_trade(self.trade1)
        # trade2 == SellTrade
        self.trades.add_trade(self.trade2)
        self.trades.add_trade(self.trade3)
        # No Account -> Defaults to 'X';
        self.trades.add_trade(self.trade4)
        self.trades.add_trade(self.trade5)

    def test_add_trades(self):
        """Test adding different trade types"""

        self.assertEqual(len(self.trades.buy_trades), 3)
        self.assertEqual(len(self.trades.sells_by_account["C"]), 1)
        self.assertEqual(len(self.trades.sells_by_account["X"]), 1)

        # Verify correct types
        self.assertIsInstance(self.trades.buy_trades[0], BuyTrade)
        self.assertIsInstance(self.trades.buy_trades[2], BuyTrade)
        self.assertIsInstance(
            self.trades.sells_by_account["C"][0],
            SellTrade,
            f"Expected SellTrade, got {type(self.trades.sells_by_account['C'][0])}",
        )
        self.assertIsInstance(
            self.trades.sells_by_account["X"][0],
            SellTrade,
            f"Expected SellTrade, got {type(self.trades.sells_by_account['C'][0])}",
        )

    def test_sort_trades(self):
        """Test trade sorting functionality"""
        # Add trades in reverse date order
        self.trades.buy_trades = []
        self.trades.sells_by_account = {}

        self.trades.add_trade(self.trade3)  # May 17
        # trade2 == SellTrade
        self.trades.add_trade(self.trade2)  # May 16
        self.trades.add_trade(self.trade1)  # May 15

        # Sort trades
        self.trades.sort_trades()

        # Verify date order
        self.assertEqual(
            self.trades.buy_trades[0].trade_id,
            "T1",
            f"Expected T1, got {self.trades.buy_trades[0].trade_id} ",
        )
        self.assertEqual(
            self.trades.sells_by_account["C"][0].trade_id,
            "S1",
            f"Expected S1, got {self.trades.sells_by_account['C'][0].trade_id}",
        )
        self.assertEqual(
            self.trades.buy_trades[1].trade_id,
            "B1",
            f"Expected B1, got {self.trades.buy_trades[1].trade_id}",
        )

    def test_json_serialization(self):
        """Test trades collection serialization to JSON"""
        trade_dict = self.trades.to_dict()

        # Verify top-level structure
        self.assertEqual(trade_dict["security_type"], "stock")
        self.assertEqual(
            len(trade_dict["buy_trades"]),
            3,
            f"Expected 3 buy trades, got {len(trade_dict['buy_trades'])}",
        )
        self.assertEqual(len(trade_dict["sells_by_account"]["C"]), 1)
        self.assertEqual(len(trade_dict["sells_by_account"]["X"]), 1)

        # Verify trade content
        self.assertEqual(trade_dict["buy_trades"][0]["trade_id"], "T1")
        self.assertEqual(trade_dict["buy_trades"][1]["trade_id"], "B1")
        # sell_trade = trade_dict["sells_by_account"]["C"][0].to_dict()
        sell_trade = trade_dict["sells_by_account"]["C"][0]
        self.assertEqual(sell_trade["trade_id"], "S1")

        # Test full JSON serialization
        import json

        json_str = json.dumps(trade_dict)
        self.assertIsInstance(json_str, str)
        reconstructed = json.loads(json_str)
        self.assertEqual(
            len(reconstructed["buy_trades"]),
            3,
            f"Expected 3 buy trades, got {len(reconstructed['buy_trades'])}",
        )


class TestBuyTradesClass(unittest.TestCase):
    def setUp(self):
        # Create sample buy trades with different dates and accounts
        self.buy1 = BuyTrade(
            {
                "trade_id": "B1",
                "symbol": "TEST",
                "action": "B",
                "trade_date": datetime(2023, 5, 10),
                "quantity": 100,
                "price": 50.0,
                "account": "IRA-123",  # Add account
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
                "account": "TAXABLE-456",  # Add account
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
                "account": "IRA-123",  # Add account
            }  # type: ignore
        )

        # Create buy trades collection with date filter
        self.buy_trades = BuyTrades(security_type="stock", after_date_str="2023-05-15")

        # Add trades
        self.buy_trades.add_trade(self.buy1)  # Before filter date
        self.buy_trades.add_trade(self.buy2)  # On filter date
        self.buy_trades.add_trade(self.buy3)  # After filter date

    def test_account_filtering(self):
        """Test account-based filtering of buy trades"""
        # Create new collection with account filter
        ira_trades = BuyTrades(
            security_type="stock",
            after_date_str="2023-05-01",
            account="IRA-123",  # Filter for IRA-123 account
        )

        # Add all trades
        ira_trades.add_trade(self.buy1)
        ira_trades.add_trade(self.buy2)
        ira_trades.add_trade(self.buy3)

        # Apply filters
        ira_trades.filter_buy_trades()

        # Should only keep IRA-123 trades after 2023-05-01
        self.assertEqual(
            len(ira_trades.buy_trades),
            2,
            f"Expected 2 IRA trades, got {len(ira_trades.buy_trades)}",
        )

        # Verify correct trades
        trade_ids = [t.trade_id for t in ira_trades.buy_trades]
        self.assertIn("B1", trade_ids, "B1 should be included")
        self.assertIn("B3", trade_ids, "B3 should be included")
        self.assertNotIn("B2", trade_ids, "B2 should be filtered out")

        # Test no account filter (should return all)
        all_trades = BuyTrades(security_type="stock", after_date_str="2023-05-01")
        all_trades.add_trade(self.buy1)
        all_trades.add_trade(self.buy2)
        all_trades.add_trade(self.buy3)
        all_trades.filter_buy_trades()
        self.assertEqual(
            len(all_trades.buy_trades),
            3,
            f"Expected 3 trades when no account filter, got {len(all_trades.buy_trades)}",
        )

        # Test account filter with no matches
        empty_trades = BuyTrades(security_type="stock", account="NONEXISTENT")
        empty_trades.add_trade(self.buy1)
        empty_trades.add_trade(self.buy2)
        empty_trades.add_trade(self.buy3)
        empty_trades.filter_buy_trades()
        self.assertEqual(
            len(empty_trades.buy_trades),
            0,
            f"Expected 0 trades for non-existent account, got {len(empty_trades.buy_trades)}",
        )

    def test_combined_filters(self):
        """Test combination of account, date, and status filters"""
        # Create trade with status
        closed_trade = BuyTrade(
            {
                "trade_id": "B4",
                "symbol": "TEST",
                "action": "B",
                "trade_date": datetime(2023, 5, 25),
                "quantity": 300,
                "price": 54.0,
                "account": "IRA-123",
                "is_done": True,  # Mark as closed
            }  # type: ignore
        )

        # Create collection with multiple filters
        filtered_trades = BuyTrades(
            security_type="stock",
            after_date_str="2023-05-15",
            account="IRA-123",
            status="open",  # Only open trades
        )

        # Add trades
        filtered_trades.add_trade(self.buy1)  # Wrong date
        filtered_trades.add_trade(self.buy2)  # Wrong account
        filtered_trades.add_trade(
            self.buy3
        )  # Should match (open, correct account/date)
        filtered_trades.add_trade(closed_trade)  # Wrong status

        # Apply filters
        filtered_trades.filter_buy_trades()

        # Should only keep B3
        self.assertEqual(
            len(filtered_trades.buy_trades),
            1,
            f"Expected 1 trade, got {len(filtered_trades.buy_trades)}",
        )
        self.assertEqual(
            filtered_trades.buy_trades[0].trade_id,
            "B3",
            f"Expected B3, got {filtered_trades.buy_trades[0].trade_id}",
        )

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
