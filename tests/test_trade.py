import unittest
import logging, time, os
from datetime import datetime
from lib.models.Trade import Trade, BuyTrade, SellTrade, TradeData
from typing import List, cast


timestr = time.strftime("%Y%m%d")
log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
logging.basicConfig(
    filename=f"./logs/trading_analyzer_{timestr}.log",
    # level=logging.DEBUG,
    level=log_level,
    format="%(asctime)s - %(levelname)s - %(lineno)d> %(message)s",
)


class TestTradeClasses(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Convert sample data to TradeData format
        cls.sample_trades: List[TradeData] = [
            {
                "trade_id": "0001",
                "symbol": "SN",
                "action": "B",
                "trade_date": datetime(2024, 8, 22),
                "trade_type": "L",
                "trade_label": "",
                "quantity": 100.0,
                "price": 91.39,
                "amount": -9139.0,
                "account": "C",
                "is_option": False,
                "is_done": False,
            },
            {
                "trade_id": "0002",
                "symbol": "SN",
                "action": "S",
                "trade_date": datetime(2024, 8, 23),
                "trade_type": "L",
                "trade_label": "",
                "quantity": 100.0,
                "price": 88.9427,
                "amount": 8894.27,
                "account": "C",
                "is_option": False,
                "is_done": False,
            },
            {
                "trade_id": "0003",
                "symbol": "SN",
                "action": "B",
                "trade_date": datetime(2024, 8, 26),
                "trade_type": "L",
                "trade_label": "",
                "quantity": 50.0,
                "price": 89.4964,
                "amount": -4474.82,
                "account": "C",
                "is_option": False,
                "is_done": False,
            },
            {
                "trade_id": "0004",
                "symbol": "SN",
                "action": "B",
                "trade_date": datetime(2024, 8, 27),
                "trade_type": "L",
                "trade_label": "",
                "quantity": 50.0,
                "price": 91.7,
                "amount": -4585.0,
                "account": "C",
                "is_option": False,
                "is_done": False,
            },
            # 04
            {
                "trade_id": "0005",
                "symbol": "SN",
                "action": "S",
                "trade_date": datetime(2024, 9, 6),
                "trade_type": "L",
                "trade_label": "",
                "quantity": 100.0,
                "price": 94.92,
                "amount": 9492.0,
                "account": "C",
                "is_option": False,
                "is_done": False,
            },
            # 05
            {
                "trade_id": "0006",
                "symbol": "SN",
                "action": "B",
                "trade_date": datetime(2024, 8, 30),
                "trade_type": "L",
                "trade_label": "",
                "quantity": 50.0,
                "price": 94.85,
                "amount": -4742.5,
                "account": "C",
                "is_option": False,
                "is_done": False,
            },
            # 06
            {
                "trade_id": "0007",
                "symbol": "SN",
                "action": "S",
                "trade_date": datetime(2024, 9, 6),
                "trade_type": "L",
                "trade_label": "",
                "quantity": 25.0,
                "price": 94.94,
                "amount": 2373.5,
                "account": "C",
                "is_option": False,
                "is_done": False,
            },
            {
                "trade_id": "0008",
                "symbol": "SN",
                "action": "S",
                "trade_date": datetime(2024, 9, 7),
                "trade_type": "L",
                "trade_label": "",
                "quantity": 10.0,
                "price": 96.99,
                "amount": 969.9,
                "account": "C",
                "is_option": False,
                "is_done": False,
            },
            {
                "trade_id": "0009",
                "symbol": "SN",
                "action": "B",
                "trade_date": datetime(2024, 9, 10),
                "trade_type": "L",
                "trade_label": "",
                "quantity": 25.0,
                "price": 98.99,
                "amount": -2474.75,
                "account": "C",
                "is_option": False,
                "is_done": False,
            },
        ]

    def test_buy_trade_creation(self):
        """Test creation of BuyTrade with all attributes"""
        data = self.sample_trades[0]
        trade = BuyTrade(data)
        symbol = trade.symbol

        self.assertEqual(
            trade.trade_id, "0001", f"[{symbol}] Got: {trade.trade_id},expected: 0001"
        )
        self.assertEqual(
            trade.symbol, "SN", f"[{symbol}] Got: {trade.symbol},expected: SN"
        )
        self.assertEqual(
            trade.action, "B", f"[{symbol}] Got: {trade.action},expected: B"
        )
        self.assertEqual(
            trade.trade_type, "L", f"[{symbol}] Got: {trade.trade_type},expected: L"
        )
        self.assertEqual(
            trade.trade_label, "", f"[{symbol}] Got: {trade.trade_label},expected: ''"
        )
        self.assertEqual(
            trade.trade_date_iso,
            "2024-08-22T00:00:00",
            f"[{symbol}] Got: {trade.trade_date_iso},expected: 2024-08-22T00:00:00",
        )
        self.assertEqual(
            trade.trade_date,
            datetime(2024, 8, 22),
            f"[{symbol}] Got: {trade.trade_date},expected: 2024-08-22",
        )
        self.assertEqual(
            trade.quantity, 100.0, f"[{symbol}] Got: {trade.quantity},expected: 100.0"
        )
        self.assertEqual(
            trade.price, 91.39, f"[{symbol}] Got: {trade.price},expected: 91.39"
        )

        self.assertEqual(
            trade.amount, -9139.0, f"[{symbol}] Got: {trade.amount},expected: -9139.0"
        )
        self.assertEqual(
            trade.account, "C", f"[{symbol}] Got: {trade.account},expected: C"
        )
        self.assertFalse(
            trade.is_option, f"[{symbol}] Got: {trade.is_option},expected: False"
        )
        self.assertFalse(
            trade.is_done, f"[{symbol}] Got: {trade.is_done},expected: False"
        )
        self.assertEqual(
            trade.current_sold_qty,
            0.0,
            f"[{symbol}] Got: {trade.current_sold_qty},expected: 0.0",
        )
        self.assertEqual(
            len(trade.sells), 0, f"[{symbol}] Got: {len(trade.sells)},expected: 0"
        )

    def test_sell_trade_creation(self):
        """Test creation of SellTrade with all attributes"""
        data = self.sample_trades[1]
        trade = SellTrade(data)
        symbol = trade.symbol

        self.assertEqual(
            trade.trade_id, "0002", f"[{symbol}] Got: {trade.trade_id},expected: 0002"
        )
        self.assertEqual(
            trade.symbol, "SN", f"[{symbol}] Got: {trade.symbol},expected: SN"
        )
        self.assertEqual(
            trade.action, "S", f"[{symbol}] Got: {trade.action},expected: S"
        )
        self.assertEqual(
            trade.trade_type, "L", f"[{symbol}] Got: {trade.trade_type},expected: L"
        )
        self.assertEqual(
            trade.trade_label, "", f"[{symbol}] Got: {trade.trade_label},expected: ''"
        )
        self.assertEqual(
            trade.trade_date,
            datetime(2024, 8, 23),
            f"[{symbol}] Got: {trade.trade_date},expected: 2024-08-23",
        )
        self.assertEqual(
            trade.trade_date_iso,
            "2024-08-23T00:00:00",
            f"[{symbol}] Got: {trade.trade_date_iso},expected: 2024-08-23T00:00:00",
        )
        self.assertEqual(
            trade.quantity, 100.0, f"[{symbol}] Got: {trade.quantity},expected: 100.0"
        )
        self.assertEqual(
            trade.price, 88.9427, f"[{symbol}] Got: {trade.price},expected: 88.9427"
        )
        self.assertEqual(
            trade.amount, 8894.27, f"[{symbol}] Got: {trade.amount},expected: 8894.27"
        )
        self.assertEqual(
            trade.account, "C", f"[{symbol}] Got: {trade.account},expected: C"
        )
        self.assertFalse(
            trade.is_option, f"[{symbol}] Got: {trade.is_option},expected: False"
        )
        self.assertFalse(
            trade.is_done, f"[{symbol}] Got: {trade.is_done},expected: False"
        )
        self.assertEqual(
            trade.profit_loss, 0.0, f"[{symbol}] Got: {trade.profit_loss},expected: 0.0"
        )
        self.assertEqual(
            trade.percent_profit_loss,
            0.0,
            f"[{symbol}] Got: {trade.percent_profit_loss},expected: 0.0",
        )

    def test_full_trade_match(self):
        """Test matching a full buy with a sell"""
        buy = BuyTrade(self.sample_trades[0])  # 100 shares @91.39
        sell = SellTrade(self.sample_trades[1])  # 100 shares @88.9427

        applied = buy.apply_sell_trade(sell)

        # Buy trade should be closed
        self.assertTrue(buy.is_done, f"[{buy.symbol}] Buy trade should be done")
        self.assertEqual(
            buy.quantity, 100.0, f"[{buy.symbol}] Got: {buy.quantity},expected: 100.0"
        )
        self.assertEqual(
            buy.current_sold_qty,
            100.0,
            f"[{buy.symbol}] Got: {buy.current_sold_qty},expected: 100.0",
        )
        self.assertEqual(
            len(buy.sells), 1, f"[{buy.symbol}] Got: {len(buy.sells)},expected: 1"
        )

        # Sell trade should be fully consumed
        self.assertTrue(sell.is_done, f"[{sell.symbol}] Sell trade should be done")
        self.assertEqual(
            sell.quantity, 0, f"[{sell.symbol}] Got: {sell.quantity},expected: 0"
        )
        self.assertEqual(
            sell.amount, 0, f"[{sell.symbol}] Got: {sell.amount},expected: 0"
        )

        # Applied portion should have correct P&L
        self.assertEqual(
            applied.quantity,
            100.0,
            f"[{applied.symbol}] Got: {applied.quantity},expected: 100.0",
        )
        self.assertEqual(
            applied.amount,
            8894.27,
            f"[{applied.symbol}] Got: {applied.amount},expected: 8894.27",
        )
        self.assertAlmostEqual(
            applied.profit_loss,
            (88.9427 - 91.39) * 100,
            2,
            f"[{applied.symbol}] Got: {applied.profit_loss},expected: {(88.9427 - 91.39) * 100}",
        )
        self.assertAlmostEqual(
            applied.percent_profit_loss,
            ((88.9427 - 91.39) / 91.39) * 100,
            2,
            f"[{applied.symbol}] Got: {applied.percent_profit_loss},expected: {((88.9427 - 91.39) / 91.39) * 100}",
        )

    def test_partial_trade_match(self):
        """Test partial matching of trades"""
        buy = BuyTrade(self.sample_trades[5])  # 50 shares @94.85
        sell1 = SellTrade(self.sample_trades[6])  # 25 shares @94.94
        sell2 = SellTrade(self.sample_trades[7])  # 10 shares @96.99

        # Apply first sell (25 shares)
        applied1 = buy.apply_sell_trade(sell1)
        self.assertFalse(buy.is_done, f"[{buy.symbol}] Buy trade should not be done")
        self.assertEqual(
            buy.quantity, 50.0, f"[{buy.symbol}] Got: {buy.quantity},expected: 50.0"
        )
        self.assertEqual(
            buy.current_sold_qty,
            25.0,
            f"[{buy.symbol}] Got: {buy.current_sold_qty},expected: 25.0",
        )
        self.assertEqual(
            len(buy.sells), 1, f"[{buy.symbol}] Got: {len(buy.sells)},expected: 1"
        )
        # self.assertAlmostEqual(applied1.profit_loss, (94.94 - 94.85) * 25, 2)
        self.assertAlmostEqual(
            applied1.percent_profit_loss,
            ((94.94 - 94.85) / 94.85) * 100,
            2,
            f"[{applied1.symbol}] Got: {applied1.percent_profit_loss},expected: {((94.94 - 94.85) / 94.85) * 100}",
        )
        # Sell trades should be partially consumed

        # Apply second sell (10 shares)
        applied2 = buy.apply_sell_trade(sell2)
        # TODO check if this is correct
        self.assertFalse(buy.is_done, f"[{buy.symbol}] Buy trade should not be done")
        self.assertEqual(
            buy.quantity, 50.0, f"[{buy.symbol}] Got: {buy.quantity},expected: 50.0"
        )
        self.assertEqual(
            buy.current_sold_qty,
            35.0,
            f"[{buy.symbol}] Got: {buy.current_sold_qty},expected: 35.0",
        )
        self.assertEqual(
            len(buy.sells), 2, f"[{buy.symbol}] Got: {len(buy.sells)},expected: 2"
        )
        self.assertAlmostEqual(
            applied2.percent_profit_loss,
            ((96.99 - 94.85) / 94.85) * 100,
            2,
            f"[{applied2.symbol}] Got: {applied2.percent_profit_loss},expected: {((96.99 - 94.85) / 94.85) * 100}",
        )
        # Sell trades should be partially consumed
        self.assertTrue(sell1.is_done, f"[{sell1.symbol}] Sell trade should be done")
        self.assertEqual(
            sell1.quantity, 0, f"[{sell1.symbol}] Got: {sell1.quantity},expected: 0"
        )
        self.assertTrue(sell2.is_done, f"[{sell2.symbol}] Sell trade should be done")
        self.assertEqual(
            sell2.quantity, 0, f"[{sell2.symbol}] Got: {sell2.quantity},expected: 0"
        )

    def test_multiple_buys_one_sell(self):
        """Test applying one sell across multiple buys"""
        buy1 = BuyTrade(self.sample_trades[2])  # 50 shares @89.4964
        buy2 = BuyTrade(self.sample_trades[3])  # 50 shares @91.7
        sell = SellTrade(self.sample_trades[4])  # 100 shares @94.92

        # Apply sell to first buy (should consume entire buy)
        applied1 = buy1.apply_sell_trade(sell)
        self.assertTrue(buy1.is_done)
        self.assertEqual(buy1.current_sold_qty, 50.0)
        self.assertAlmostEqual(applied1.profit_loss, (94.92 - 89.4964) * 50, 2)

        # Sell should have remaining 50 shares
        self.assertFalse(sell.is_done)
        self.assertEqual(sell.quantity, 50.0)

        # Apply remaining sell to second buy
        applied2 = buy2.apply_sell_trade(sell)
        self.assertTrue(buy2.is_done)
        self.assertEqual(buy2.current_sold_qty, 50.0)
        self.assertAlmostEqual(applied2.profit_loss, (94.92 - 91.7) * 50, 2)

        # Sell should be fully consumed
        self.assertTrue(sell.is_done)
        self.assertEqual(sell.quantity, 0)

    def test_apply_sell_trades_method(self):
        """Test applying multiple sells to a buy position"""
        buy = BuyTrade(self.sample_trades[5])  # ID: "0006", 50 shares @94.85
        # Sells quantity = 135 - Apply 50 shares
        sells = [
            # sells[0] -> "0007" ->  done
            SellTrade(self.sample_trades[6]),  # Using 25 of 25  shares
            # sells[1] ->  "0008" -> done
            SellTrade(self.sample_trades[7]),  # Using 10 of 10 shares
            # sells[2] ->  "0005" -> NOT done
            SellTrade(self.sample_trades[4]),  # Using 15 of 100 shares
        ]

        buy.apply_sell_trades(sells)

        # Buy should be closed (25 + 10 + 15 from last sell)
        self.assertTrue(buy.is_done, f"[{buy.symbol}] Buy trade should be done")
        self.assertEqual(
            buy.quantity, 50.0, f"[{buy.symbol}] Got: {buy.quantity},expected: 50.0"
        )
        self.assertEqual(
            buy.current_sold_qty,
            50.0,
            f"[{buy.symbol}] Got: {buy.current_sold_qty},expected: 50.0",
        )

        self.assertEqual(
            len(buy.sells), 3, f"[{buy.symbol}] Got: {len(buy.sells)},expected: 3"
        )

        # The first two "done" sells are popped from the list a
        self.assertEqual(len(sells), 1, f"[{buy.symbol}] Got: {len(sells)},expected: 1")

        # BuyTrade - Sell trades status
        self.assertTrue(
            buy.sells[0].is_done,
            f"[{sells[0].symbol}] {buy.sells[0].trade_id} Fully applied Sell trade should be done",
        )

        self.assertTrue(
            buy.sells[1].is_done,
            f"[{buy.sells[1].symbol}] {buy.sells[1].trade_id} Fully applied Sell trade should be done",
        )
        self.assertFalse(
            buy.sells[2].is_done,
            f"[{buy.sells[2].symbol}] {buy.sells[2].trade_id} Partially applied Sell trade should not be done",
        )  # Still has remaining shares

        self.assertEqual(
            buy.sells[2].quantity,
            15.0,
            f"[{buy.sells[2].symbol}] Got {buy.sells[2].quantity}, expected: {15.0}",
        )  # 15 taken from the last sell id "0005"

        # Original SellTrade - Only one remaining
        self.assertEqual(
            sells[0].trade_id,
            "0005",
            f"[{sells[0].symbol}] Got {buy.sells[0].quantity}, expected: {85.0}",
        )  # Trade id "0005" is the only one remaining

        self.assertFalse(
            sells[0].is_done,
            f"[{sells[0].symbol}] {sells[0].trade_id} Partially applied Sell trade should not be done",
        )  # Still has remaining shares

        self.assertEqual(
            sells[0].quantity,
            85.0,
            f"[{sells[0].symbol}] Got {buy.sells[0].quantity}, expected: {85.0}",
        )  # 100 - 15 = 85

        self.assertEqual(
            sells[0].amount,
            9492.0 - (94.92 * 15),
            f"[{sells[0].symbol}] Got amount {sells[0].amount}, expected: {9492.0 - (94.92 * 15)}",
        )  # remaining amount = original amount - (price * quantity)

        # Verify P&L calculations
        profit_loss = sum(sell.profit_loss for sell in buy.sells)
        expected = (94.94 - 94.85) * 25 + (96.99 - 94.85) * 10 + (94.92 - 94.85) * 15
        self.assertAlmostEqual(profit_loss, expected, 2)

    def test_repr_output(self):
        """Test string representation of trades"""
        buy = BuyTrade(self.sample_trades[0])  # type: ignore
        sell = SellTrade(self.sample_trades[1])  # type: ignore

        buy_repr = repr(buy)
        self.assertIn("BuyTrade(", buy_repr)
        self.assertIn("trade_id=0001", buy_repr)
        self.assertIn("symbol=SN", buy_repr)
        self.assertIn("quantity=100.0", buy_repr)
        self.assertIn("current_sold_qty=0.0", buy_repr)

        sell_repr = repr(sell)
        self.assertIn("SellTrade(", sell_repr)
        self.assertIn("trade_id=0002", sell_repr)
        self.assertIn("symbol=SN", sell_repr)
        self.assertIn("quantity=100.0", sell_repr)
        self.assertIn("profit_loss=0.0", sell_repr)

    def test_date_conversion(self):
        """Test various date formats are converted correctly"""
        # Test datetime input
        trade1 = BuyTrade(
            {
                "trade_id": "1001",
                "symbol": "TEST",
                "action": "B",
                "trade_date": datetime(2023, 5, 15),
                "quantity": 10,
                "price": 100.0,
            }  # type: ignore
        )
        self.assertEqual(trade1.trade_date_iso, "2023-05-15T00:00:00")

        # Test string input (ISO format)
        trade2 = SellTrade(
            {
                "trade_id": "1002",
                "symbol": "TEST",
                "action": "S",
                "trade_date": "2023-05-16T14:30:00",  # type: ignore
                "quantity": 10,
                "price": 105.0,
            }
        )
        self.assertEqual(trade2.trade_date_iso, "2023-05-16T14:30:00")

        # Test string input (date only)
        trade3 = BuyTrade(
            {
                "trade_id": "1003",
                "symbol": "TEST",
                "action": "B",
                "trade_date": "2023-05-17",  # type: ignore
                "quantity": 10,
                "price": 102.0,
            }
        )
        self.assertEqual(trade3.trade_date_iso, "2023-05-17T00:00:00")

    def test_validation(self):
        """Test trade validation rules"""
        # Missing required field
        with self.assertRaises(KeyError):
            BuyTrade(
                {
                    "symbol": "TEST",
                    "action": "B",
                    "trade_date": datetime.now(),
                    "quantity": 10,
                    "price": 100.0,
                }  # type: ignore
            )

        # Invalid quantity
        with self.assertRaises(ValueError):
            BuyTrade(
                {
                    "trade_id": "1001",
                    "symbol": "TEST",
                    "action": "B",
                    "trade_date": datetime.now(),
                    "quantity": 0,
                    "price": 100.0,
                }  # type: ignore
            )


if __name__ == "__main__":
    unittest.main()
