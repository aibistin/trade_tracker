import unittest
import json
from lib.trading_analyzer import TradingAnalyzer

class TestTradingAnalyzerJSON(unittest.TestCase):
    def setUp(self):
        # Sample trade data
        self.trades = [
            {
                "id": "0001",
                "symbol": "TEST",
                "action": "B",
                "trade_type": "L",
                "quantity": 100,
                "price": 50.0,
                "trade_date": "2023-05-15",
                "amount": -5000.0
            },
            {
                "id": "0002",
                "symbol": "TEST",
                "action": "S",
                "trade_type": "L",
                "quantity": 50,
                "price": 55.0,
                "trade_date": "2023-05-16",
                "amount": 2750.0
            }
        ]
        self.analyzer = TradingAnalyzer("TEST", self.trades)
        self.analyzer.analyze_trades()

    def test_json_output_structure(self):
        """Test JSON output has correct structure"""
        json_data = self.analyzer.get_profit_loss_data_json()
        
        # Verify top-level structure
        self.assertIn("stock", json_data)
        self.assertIn("option", json_data)
        
        # Verify security type structure
        stock_data = json_data["stock"]
        self.assertIn("has_trades", stock_data)
        self.assertIn("summary", stock_data)
        self.assertIn("all_trades", stock_data)
        
        # Verify summary contains expected fields
        summary = stock_data["summary"]
        self.assertIn("symbol", summary)
        self.assertIn("bought_quantity", summary)
        self.assertIn("sold_quantity", summary)
        
        # Verify trades are properly converted
        self.assertIsInstance(stock_data["all_trades"], list)
        if stock_data["all_trades"]:
            trade = stock_data["all_trades"][0]
            self.assertIn("trade_id", trade)
            self.assertIn("quantity", trade)

    # @unittest.skip("Skipping test_full_json_serialization round trip deserialization. May not be needed.")
    def test_full_json_serialization(self):
        """Test the entire structure can be serialized to JSON"""
        json_data = self.analyzer.get_profit_loss_data_json()
        
        # Test serialization
        try:
            json_str = json.dumps(json_data)
            self.assertIsInstance(json_str, str)
            
            # Test round-trip deserialization
            reconstructed = json.loads(json_str)
            self.assertEqual(reconstructed["stock"]["summary"]["symbol"], "TEST")
            if reconstructed["stock"]["all_trades"]:
                trade = reconstructed["stock"]["all_trades"][0]
                self.assertEqual(trade["trade_id"], "0001")
        except Exception as e:
            self.fail(f"JSON serialization failed: {str(e)}")

    def test_empty_data_handling(self):
        """Test JSON output with no trades"""
        empty_analyzer = TradingAnalyzer("EMPTY", [])
        empty_analyzer.analyze_trades()
        json_data = empty_analyzer.get_profit_loss_data_json()
        
        stock_data = json_data["stock"]
        self.assertFalse(stock_data["has_trades"])
        self.assertEqual(stock_data["summary"], {})
        self.assertEqual(stock_data["all_trades"], [])

if __name__ == '__main__':
    unittest.main()