import unittest

from lib.trading_analyzer import TradingAnalyzer


def valid_trade(**overrides):
    trade = {
        "id": "1",
        "symbol": "FAKE",
        "action": "B",
        "trade_type": "L",
        "trade_date": "2026-01-05",
        "quantity": 10.0,
        "price": 100.0,
        "amount": -1000.0,
        "account": "C",
    }
    trade.update(overrides)
    return trade


class TestAnalyzerInputValidation(unittest.TestCase):
    """Error-path tests for TradingAnalyzer input validation."""

    def test_non_string_symbol_raises_type_error(self):
        with self.assertRaises(TypeError):
            TradingAnalyzer(123, [])

    def test_non_list_transactions_raises_type_error(self):
        with self.assertRaises(TypeError):
            TradingAnalyzer("FAKE", {"not": "a list"})

    def test_invalid_status_raises_value_error(self):
        analyzer = TradingAnalyzer("FAKE", [])
        with self.assertRaises(ValueError) as ctx:
            analyzer.analyze_trades(status="bogus")
        self.assertIn("Invalid status", str(ctx.exception))

    def test_invalid_after_date_raises_value_error(self):
        analyzer = TradingAnalyzer("FAKE", [])
        with self.assertRaises(ValueError) as ctx:
            analyzer.analyze_trades(after_date="01/05/2026")
        self.assertIn("after_date", str(ctx.exception))

    def test_missing_required_field_raises(self):
        trade = valid_trade()
        del trade["price"]
        analyzer = TradingAnalyzer("FAKE", [trade])
        with self.assertRaises(ValueError) as ctx:
            analyzer.analyze_trades()
        self.assertIn("missing required field", str(ctx.exception))

    def test_negative_price_raises(self):
        analyzer = TradingAnalyzer("FAKE", [valid_trade(price=-5.0)])
        with self.assertRaises(ValueError) as ctx:
            analyzer.analyze_trades()
        self.assertIn("Invalid price", str(ctx.exception))

    def test_invalid_trade_date_type_raises(self):
        analyzer = TradingAnalyzer("FAKE", [valid_trade(trade_date=20260105)])
        with self.assertRaises(ValueError) as ctx:
            analyzer.analyze_trades()
        self.assertIn("Invalid trade date", str(ctx.exception))

    def test_unknown_action_raises(self):
        analyzer = TradingAnalyzer("FAKE", [valid_trade(action="ZZ")])
        with self.assertRaises(ValueError) as ctx:
            analyzer.analyze_trades()
        self.assertIn("Unknown action", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
