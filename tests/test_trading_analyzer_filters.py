import unittest
from datetime import datetime
from lib.trading_analyzer import TradingAnalyzer


import unittest
from datetime import datetime
from lib.trading_analyzer import TradingAnalyzer


class TestTradingAnalyzerFilters(unittest.TestCase):
    def setUp(self):
        # Sample trade data with accounts
        self.trades = [
            # Closed trade in account XYZ
            {
                "id": "0001",
                "symbol": "FILT",
                "action": "B",
                "trade_date": "2023-05-15",
                "quantity": 100,
                "price": 50.0,
                "amount": -5000.0,
                "account": "XYZ",
            },
            {
                "id": "0002",
                "symbol": "FILT",
                "action": "S",
                "trade_date": "2023-05-16",
                "quantity": 100,
                "price": 55.0,
                "amount": 5500.0,
                "account": "XYZ",
            },
            # Open trade in account XYZ
            {
                "id": "0003",
                "symbol": "FILT",
                "action": "B",
                "trade_date": "2023-05-17",
                "quantity": 200,
                "price": 52.0,
                "amount": -10400.0,
                "account": "XYZ",
            },
            {
                "id": "0004",
                "symbol": "FILT",
                "action": "S",
                "trade_date": "2023-05-18",
                "quantity": 100,
                "price": 53.0,
                "amount": 5300.0,
                "account": "XYZ",
            },
            # Open trade in account ABC
            {
                "id": "0005",
                "symbol": "FILT",
                "action": "B",
                "trade_date": "2023-05-19",
                "quantity": 150,
                "price": 54.0,
                "amount": -8100.0,
                "account": "ABC",
            },
            # Closed trade in account ABC
            {
                "id": "0006",
                "symbol": "FILT",
                "action": "B",
                "trade_date": "2023-05-10",
                "quantity": 50,
                "price": 40.0,
                "amount": -2000.0,
                "account": "ABC",
            },
            {
                "id": "0007",
                "symbol": "FILT",
                "action": "S",
                "trade_date": "2023-05-12",
                "quantity": 50,
                "price": 45.0,
                "amount": 2250.0,
                "account": "ABC",
            },
        ]
        self.analyzer = TradingAnalyzer("FILT", self.trades)

    def test_status_filter_closed(self):
        """Test closed trades filter"""
        self.analyzer.analyze_trades(status="closed")
        pl_data = self.analyzer.get_profit_loss_data()
        # Should have two closed trade "id": "0001" account XYZ, "id": "0006" account ABC
        self.assertEqual(
            len(pl_data["stock"]["all_buy_trades"]),
            2,
            f"Expected two closed trades, got {len(pl_data['stock']['all_buy_trades'])}",
        )

        self.assertEqual(
            pl_data["stock"]["all_buy_trades"][0].trade_id,
            "0006",
            f"Expected trade ID '0006', got {pl_data['stock']['all_buy_trades'][0].trade_id}",
        )
        self.assertTrue(
            pl_data["stock"]["all_buy_trades"][0].is_done,
            "Trade should be marked as done",
        )

        self.assertEqual(
            pl_data["stock"]["all_buy_trades"][1].trade_id,
            "0001",
            f"Expected trade ID '0001', got {pl_data['stock']['all_buy_trades'][1].trade_id}",
        )
        self.assertTrue(
            pl_data["stock"]["all_buy_trades"][1].is_done,
            "Trade should be marked as done",
        )

    def test_status_filter_open(self):
        """Test open trades filter"""
        self.analyzer.analyze_trades(status="open")
        pl_data = self.analyzer.get_profit_loss_data()

        # Should have two open trades
        self.assertEqual(
            len(pl_data["stock"]["all_buy_trades"]),
            2,
            f"Expected 2 open trades, got {len(pl_data['stock']['all_buy_trades'])}",
        )
        trade_ids = {t.trade_id for t in pl_data["stock"]["all_buy_trades"]}
        self.assertEqual(
            trade_ids,
            {"0003", "0005"},
            f"Expected open trades with IDs '0003' and '0005', got {trade_ids}",
        )
        self.assertTrue(
            all(not t.is_done for t in pl_data["stock"]["all_buy_trades"]),
            "All open trades should not be done",
        )

    def test_combined_filters(self):
        """Test date and status filters together"""
        self.analyzer.analyze_trades(after_date="2023-05-17", status="open")
        pl_data = self.analyzer.get_profit_loss_data()

        # Should have two open trades after 2023-05-17
        self.assertEqual(len(pl_data["stock"]["all_buy_trades"]), 2)
        trade_ids = {t.trade_id for t in pl_data["stock"]["all_buy_trades"]}
        self.assertEqual(trade_ids, {"0003", "0005"})

    def test_no_filter(self):
        """Test no status filter (all trades)"""
        self.analyzer.analyze_trades()
        pl_data = self.analyzer.get_profit_loss_data()
        self.assertEqual(
            len(pl_data["stock"]["all_buy_trades"]),
            4,
            f"Expected 4 trades, got {len(pl_data['stock']['all_buy_trades'])} ",
        )

    def test_invalid_status(self):
        """Test invalid status filter"""
        with self.assertRaises(ValueError):
            self.analyzer.analyze_trades(status="invalid")

    def test_account_filter_xyz(self):
        """Test filtering trades for account XYZ"""
        self.analyzer.analyze_trades(account="XYZ")
        pl_data = self.analyzer.get_profit_loss_data()

        # Should have 2 buys and 1 sell in XYZ
        self.assertEqual(
            len(pl_data["stock"]["all_buy_trades"]),
            2,
            f"Expected 2 buy trades for XYZ, got {len(pl_data['stock']['all_buy_trades'])}",
        )
        self.assertEqual(
            len(pl_data["stock"]["all_buy_trades"][0].sells),
            1,
            f"Expected 1 sell trades for XYZ, got {len(pl_data['stock']['all_buy_trades'][0].sells)}",
        )

        trade_ids = {t.trade_id for t in pl_data["stock"]["all_buy_trades"]}
        self.assertEqual(
            trade_ids,
            # {"0001", "0002", "0003"},
            {"0001", "0003"},
            f"Expected XYZ trades 0001-0003, got {trade_ids}",
        )

    def test_account_filter_abc(self):
        """Test filtering trades for account ABC"""
        self.analyzer.analyze_trades(account="ABC")
        pl_data = self.analyzer.get_profit_loss_data()

        # Should have 2 buys and 1 sell in ABC
        self.assertEqual(
            len(pl_data["stock"]["all_buy_trades"]),
            2,
            f"Expected 3 trades for ABC, got {len(pl_data['stock']['all_buy_trades'])}",
        )

        trade_ids = {t.trade_id for t in pl_data["stock"]["all_buy_trades"]}
        self.assertEqual(
            trade_ids,
            {"0005", "0006"},
            f"Expected ABC trades 0005, 0006, got {trade_ids}",
        )

    def test_account_date_status_filters(self):
        """Test combination of account, date, and status filters"""
        # Filter for open trades in XYZ after 2023-05-16
        self.analyzer.analyze_trades(
            account="XYZ", after_date="2023-05-16", status="open"
        )
        pl_data = self.analyzer.get_profit_loss_data()

        # Should have 1 open trade in XYZ after 2023-05-16 (trade 0003)
        self.assertEqual(
            len(pl_data["stock"]["all_buy_trades"]),
            1,
            f"Expected 1 open trade in XYZ after 2023-05-16, got {len(pl_data['stock']['all_buy_trades'])}",
        )
        self.assertEqual(
            pl_data["stock"]["all_buy_trades"][0].trade_id,
            "0003",
            f"Expected trade 0003, got {pl_data['stock']['all_buy_trades'][0].trade_id}",
        )
        self.assertFalse(
            pl_data["stock"]["all_buy_trades"][0].is_done, "Trade should be open"
        )

    def test_account_filter_no_matches(self):
        """Test account filter with no matching trades"""
        self.analyzer.analyze_trades(account="NONEXISTENT")
        pl_data = self.analyzer.get_profit_loss_data()

        self.assertEqual(
            len(pl_data["stock"]["all_buy_trades"]),
            0,
            f"Expected 0 trades for non-existent account, got {len(pl_data['stock']['all_buy_trades'])}",
        )

    def test_account_filter_with_closed_status(self):
        """Test account filter combined with closed status"""
        self.analyzer.analyze_trades(account="ABC", status="closed")
        pl_data = self.analyzer.get_profit_loss_data()

        # Should have 1 closed trade in ABC (trade 0006)
        self.assertEqual(
            len(pl_data["stock"]["all_buy_trades"]),
            1,
            f"Expected 1 closed trade in ABC, got {len(pl_data['stock']['all_buy_trades'])}",
        )
        self.assertEqual(
            pl_data["stock"]["all_buy_trades"][0].trade_id,
            "0006",
            f"Expected trade 0006, got {pl_data['stock']['all_buy_trades'][0].trade_id}",
        )
        self.assertTrue(
            pl_data["stock"]["all_buy_trades"][0].is_done, "Trade should be closed"
        )


if __name__ == "__main__":
    unittest.main()
