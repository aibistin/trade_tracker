import json
import os
import tempfile
import unittest

from bin.seed_transfer_adjustments import build_record, load_adjustments


class TestLoadAdjustments(unittest.TestCase):
    def _write(self, records):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(records, f)
        self.addCleanup(os.remove, path)
        return path

    def test_loads_valid_records(self):
        path = self._write([{
            "symbol": "BE", "quantity": 100, "account": "C", "price": 18.0,
            "trade_date": "2017-01-01", "activity_id": "0000000",
            "action": "B", "trade_type": "L",
        }])
        records = load_adjustments(path)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["symbol"], "BE")

    def test_missing_quantity_raises(self):
        path = self._write([{
            "symbol": "MDB", "quantity": None, "account": "C", "price": 47.0,
            "trade_date": "2018-06-01", "activity_id": "1010000",
            "action": "B", "trade_type": "L",
        }])
        with self.assertRaises(ValueError) as ctx:
            load_adjustments(path)
        self.assertIn("MDB", str(ctx.exception))
        self.assertIn("quantity", str(ctx.exception))


class TestBuildRecord(unittest.TestCase):
    def test_computes_negative_amount_for_a_buy(self):
        record = build_record({
            "symbol": "be", "quantity": 100, "account": "C", "price": 18.0,
            "trade_date": "2017-01-01", "activity_id": "0000000",
            "action": "B", "trade_type": "L",
        })
        self.assertEqual(record["symbol"], "BE")
        self.assertEqual(record["amount"], -1800.0)
        self.assertIsNone(record["label"])
        self.assertEqual(record["activity_id"], 0)
        self.assertEqual(record["leg_index"], 0)

    def test_fractional_quantity_amount_rounded(self):
        record = build_record({
            "symbol": "DE", "quantity": 133.914, "account": "R", "price": 104.0,
            "trade_date": "2017-01-01", "activity_id": "1000010",
            "action": "B", "trade_type": "L",
        })
        self.assertEqual(record["amount"], -round(133.914 * 104.0, 2))
        self.assertEqual(record["activity_id"], 1000010)


if __name__ == "__main__":
    unittest.main()
