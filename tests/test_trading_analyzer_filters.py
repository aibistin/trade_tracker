import unittest
from datetime import datetime
from lib.trading_analyzer import TradingAnalyzer

class TestTradingAnalyzerFilters(unittest.TestCase):
    def setUp(self):
        # Sample trade data with open and closed positions
        self.trades = [
            # Closed trade (fully sold)
            {
                "id": "0001", "symbol": "FILT", "action": "B", 
                "trade_date": "2023-05-15", "quantity": 100, 
                "price": 50.0, "amount": -5000.0
            },
            {
                "id": "0002", "symbol": "FILT", "action": "S", 
                "trade_date": "2023-05-16", "quantity": 100, 
                "price": 55.0, "amount": 5500.0
            },
            # Open trade (partially sold)
            {
                "id": "0003", "symbol": "FILT", "action": "B", 
                "trade_date": "2023-05-17", "quantity": 200, 
                "price": 52.0, "amount": -10400.0
            },
            {
                "id": "0004", "symbol": "FILT", "action": "S", 
                "trade_date": "2023-05-18", "quantity": 100, 
                "price": 53.0, "amount": 5300.0
            },
            # Open trade (not sold)
            {
                "id": "0005", "symbol": "FILT", "action": "B", 
                "trade_date": "2023-05-19", "quantity": 150, 
                "price": 54.0, "amount": -8100.0
            }
        ]
        self.analyzer = TradingAnalyzer("FILT", self.trades)

    def test_status_filter_closed(self):
        """Test closed trades filter"""
        self.analyzer.analyze_trades(status='closed')
        pl_data = self.analyzer.get_profit_loss_data()
        # print(f"Profit/Loss Data: {pl_data}") 
        # Should only have one closed trade
        self.assertEqual(len(pl_data["stock"]["all_trades"]), 1, f"Expected 1 closed trade, got {len(pl_data['stock']['all_trades'])}")
        self.assertEqual(pl_data["stock"]["all_trades"][0].trade_id, "0001", f"Expected trade ID '0001', got {pl_data['stock']['all_trades'][0].trade_id}")
        self.assertTrue(pl_data["stock"]["all_trades"][0].is_done, "Trade should be marked as done")

    def test_status_filter_open(self):
        """Test open trades filter"""
        self.analyzer.analyze_trades(status='open')
        pl_data = self.analyzer.get_profit_loss_data()
        
        # Should have two open trades
        self.assertEqual(len(pl_data["stock"]["all_trades"]), 2, f"Expected 2 open trades, got {len(pl_data['stock']['all_trades'])}")
        trade_ids = {t.trade_id for t in pl_data["stock"]["all_trades"]}
        self.assertEqual(trade_ids, {"0003", "0005"}, f"Expected open trades with IDs '0003' and '0005', got {trade_ids}")
        self.assertTrue(all(not t.is_done for t in pl_data["stock"]["all_trades"]), "All open trades should not be done")

    def test_combined_filters(self):
        """Test date and status filters together"""
        self.analyzer.analyze_trades(after_date="2023-05-17", status='open')
        pl_data = self.analyzer.get_profit_loss_data()
        
        # Should have two open trades after 2023-05-17
        self.assertEqual(len(pl_data["stock"]["all_trades"]), 2)
        trade_ids = {t.trade_id for t in pl_data["stock"]["all_trades"]}
        self.assertEqual(trade_ids, {"0003", "0005"})

    def test_no_filter(self):
        """Test no status filter (all trades)"""
        self.analyzer.analyze_trades()
        pl_data = self.analyzer.get_profit_loss_data()
        self.assertEqual(len(pl_data["stock"]["all_trades"]), 3)

    def test_invalid_status(self):
        """Test invalid status filter"""
        with self.assertRaises(ValueError):
            self.analyzer.analyze_trades(status='invalid')

if __name__ == '__main__':
    unittest.main()