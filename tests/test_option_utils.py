import unittest

from lib.option_utils import label_to_occ


class TestLabelToOcc(unittest.TestCase):
    """Tests for Schwab option label → OCC ticker conversion."""

    def test_call_label(self):
        self.assertEqual(label_to_occ("UUUU 04/17/2026 23.00 C"), "UUUU260417C00023000")

    def test_put_label(self):
        self.assertEqual(label_to_occ("QBTS 07/17/2026 25.00 P"), "QBTS260717P00025000")

    def test_fractional_strike(self):
        self.assertEqual(label_to_occ("F 01/16/2026 12.50 C"), "F260116C00012500")

    def test_strips_surrounding_whitespace(self):
        self.assertEqual(label_to_occ("  SPY 12/19/2025 500.00 C  "), "SPY251219C00500000")

    def test_wrong_part_count_raises(self):
        with self.assertRaises(ValueError) as ctx:
            label_to_occ("UUUU 04/17/2026 23.00")
        self.assertIn("Expected 4 parts", str(ctx.exception))

    def test_invalid_option_type_raises(self):
        with self.assertRaises(ValueError) as ctx:
            label_to_occ("UUUU 04/17/2026 23.00 X")
        self.assertIn("Invalid option type", str(ctx.exception))

    def test_invalid_date_raises(self):
        with self.assertRaises(ValueError) as ctx:
            label_to_occ("UUUU 2026-04-17 23.00 C")
        self.assertIn("Cannot parse date", str(ctx.exception))

    def test_invalid_strike_raises(self):
        with self.assertRaises(ValueError) as ctx:
            label_to_occ("UUUU 04/17/2026 abc C")
        self.assertIn("Cannot parse strike", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
