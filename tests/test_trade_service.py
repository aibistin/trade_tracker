import unittest
from app.services.trade_service import validate_trade_update, REASON_MAX_LEN


class TestValidateTradeUpdate(unittest.TestCase):

    def test_empty_data_returns_no_errors(self):
        self.assertEqual(validate_trade_update({}), {})

    def test_valid_reason(self):
        self.assertEqual(validate_trade_update({"reason": "Good entry"}), {})

    def test_reason_none_is_allowed(self):
        self.assertEqual(validate_trade_update({"reason": None}), {})

    def test_reason_too_long(self):
        errors = validate_trade_update({"reason": "x" * (REASON_MAX_LEN + 1)})
        self.assertIn("reason", errors)

    def test_reason_exact_max_length_is_valid(self):
        self.assertEqual(validate_trade_update({"reason": "x" * REASON_MAX_LEN}), {})

    def test_reason_not_a_string(self):
        errors = validate_trade_update({"reason": 42})
        self.assertIn("reason", errors)

    def test_valid_stop_price(self):
        self.assertEqual(validate_trade_update({"initial_stop_price": 10.5}), {})

    def test_valid_sell_price(self):
        self.assertEqual(validate_trade_update({"projected_sell_price": "25.00"}), {})

    def test_zero_stop_price_is_invalid(self):
        errors = validate_trade_update({"initial_stop_price": 0})
        self.assertIn("initial_stop_price", errors)

    def test_negative_sell_price_is_invalid(self):
        errors = validate_trade_update({"projected_sell_price": -5.0})
        self.assertIn("projected_sell_price", errors)

    def test_non_numeric_price_is_invalid(self):
        errors = validate_trade_update({"initial_stop_price": "abc"})
        self.assertIn("initial_stop_price", errors)

    def test_price_none_is_allowed(self):
        self.assertEqual(validate_trade_update({"initial_stop_price": None}), {})

    def test_multiple_errors_returned(self):
        errors = validate_trade_update({
            "reason": "x" * (REASON_MAX_LEN + 1),
            "initial_stop_price": -1,
        })
        self.assertIn("reason", errors)
        self.assertIn("initial_stop_price", errors)

    def test_unknown_fields_ignored(self):
        self.assertEqual(validate_trade_update({"quantity": 100}), {})


if __name__ == "__main__":
    unittest.main()
