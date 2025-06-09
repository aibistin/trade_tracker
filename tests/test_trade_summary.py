import unittest
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import cast, List
from lib.models.TradeSummary import TradeSummary, OPTIONS_MULTIPLIER, STOCK_MULTIPLIER
from lib.models.Trade import BuyTrade, SellTrade, TradeData


# Mock BuyTrades collection class
@dataclass
class BuyTrades:
    security_type: str
    buy_trades: List[BuyTrade]


class TestTradeSummary(unittest.TestCase):
    def setUp(self):
        self.symbol = "TEST"
        self.buy_date = datetime.now() - timedelta(days=10)
        self.sell_date = datetime.now() - timedelta(days=5)

        # Create sample trades

        # return BuyTrade(cast(TradeData, trade))
        self.stock_buy = BuyTrade(
            cast(
                TradeData,
                {
                    "trade_id": 1,
                    "symbol": self.symbol,
                    "action": "B",
                    "trade_date": self.buy_date,
                    "trade_type": "L",
                    "quantity": 100,
                    "price": 10.0,
                    "amount": -1000.0,  # Negative for buy
                    "is_option": False,
                    "sells": [],
                },
            )
        )

        self.option_buy = BuyTrade(
            cast(
                TradeData,
                {
                    "trade_id": 2,
                    "symbol": self.symbol,
                    "action": "BO",
                    "trade_date": self.buy_date,
                    "trade_type": "C",
                    "quantity": 5,  # Contracts
                    "price": 1.0,
                    "amount": -500.0,  # Negative for buy
                    "is_option": True,
                    "sells": [],
                },
            )
        )

        self.stock_sell = SellTrade(
            cast(
                TradeData,
                {
                    "trade_id": "101",
                    "symbol": self.symbol,
                    "action": "S",
                    "trade_date": self.sell_date,
                    "trade_type": "L",
                    "quantity": 50,
                    "price": 12.0,
                    "amount": 600.0,  # Positive for sell
                    "is_option": False,
                },
            )
        )

        self.option_sell = SellTrade(
            cast(
                TradeData,
                {
                    "trade_id": 102,
                    "symbol": self.symbol,
                    "action": "SC",
                    "trade_date": self.sell_date,
                    "trade_type": "C",
                    "quantity": 3,  # Contracts
                    "price": 1.5,
                    "amount": 450.0,  # Positive for sell
                    "is_option": True,
                },
            )
        )

        # Add sells to buys
        self.stock_buy.sells.append(self.stock_sell)
        self.option_buy.sells.append(self.option_sell)

        # Create collections # One BuyTrade with one SellTrade
        self.stock_trades = BuyTrades(
            security_type="stock", buy_trades=[self.stock_buy]
        )

        self.option_trades = BuyTrades(
            security_type="option", buy_trades=[self.option_buy]
        )

    def test_create_stock_summary(self):
        """Test creating stock summary from trades"""
        summary = TradeSummary.create_from_buy_trades_collection(
            symbol=self.symbol, buy_trades_collection=self.stock_trades
        )

        # Test basic properties
        self.assertEqual(
            summary.symbol,
            self.symbol,
            f"[{self.symbol}] Expected symbol: {self.symbol} Got: {summary.symbol}",
        )
        self.assertFalse(
            summary.is_option,
            f"[{self.symbol}] Expected is_option: False Got: {summary.is_option}",
        )
        self.assertEqual(
            summary.multiplier,
            STOCK_MULTIPLIER,
            f"[{self.symbol}] Expected multiplier: {STOCK_MULTIPLIER} Got: {summary.multiplier}",
        )

        # Test quantities and amounts
        self.assertEqual(
            summary.bought_quantity,
            100,
            f"[{self.symbol}] Expected bought_quantity: 100 Got: {summary.bought_quantity}",
        )

        # BuyTrade  { "trade_id": 1, "symbol": self.symbol, "action": "B", "trade_date": self.buy_date, "trade_type": "L", "quantity": 100, "price": 10.0, "amount": 1000.0,  # Negative for buy "is_option": False, "sells": [], },
        # SellTrade { "trade_id": "101", "symbol": self.symbol, "action": "S", "trade_date": self.sell_date, "trade_type": "L", "quantity": 50, "price": 12.0, "amount": 600.0,  # Positive for sell "is_option": False, },

        self.assertEqual(
            summary.bought_amount,
            -1000,
            f"[{self.symbol}] Expected bought_amount: -1000 Got: {summary.bought_amount}",
        )

        self.assertEqual(
            summary.sold_quantity,
            50,
            f"[{self.symbol}] Expected sold_quantity: 50 Got: {summary.sold_quantity}",
        )
        self.assertEqual(
            summary.sold_amount,
            600,
            f"[{self.symbol}] Expected sold_amount: 600 Got: {summary.sold_amount}",
        )

        # Test averages
        self.assertEqual(
            summary.get_average_bought_price(),
            -10.0,
            f"[{self.symbol}] Expected avg bought price: -10.0 Got: {summary.average_bought_price}",
        )
        self.assertEqual(
            summary.get_average_sold_price(),
            12.0,
            f"[{self.symbol}] Expected avg sold: 12.0 Got: {summary.average_sold_price}",
        )

        # Test trade lists
        self.assertEqual(
            len(summary.buy_trades),
            1,
            f"[{self.symbol}] Expected 1 buy trade Got: {len(summary.buy_trades)}",
        )
        self.assertEqual(
            len(summary.sell_trades),
            1,
            f"[{self.symbol}] Expected 1 sell trade Got: {len(summary.sell_trades)}",
        )

    def test_create_option_summary(self):
        """Test creating option summary from trades"""
        summary = TradeSummary.create_from_buy_trades_collection(
            symbol=self.symbol, buy_trades_collection=self.option_trades
        )

        # Test basic properties
        self.assertEqual(
            summary.symbol,
            self.symbol,
            f"[{self.symbol}] Expected symbol: {self.symbol} Got: {summary.symbol}",
        )
        self.assertTrue(
            summary.is_option,
            f"[{self.symbol}] Expected is_option: True Got: {summary.is_option}",
        )
        self.assertEqual(
            summary.multiplier,
            OPTIONS_MULTIPLIER,
            f"[{self.symbol}] Expected multiplier: {OPTIONS_MULTIPLIER} Got: {summary.multiplier}",
        )

        # Test quantities and amounts
        self.assertEqual(
            summary.bought_quantity,
            5,
            f"[{self.symbol}] Expected bought_quantity: 5 Got: {summary.bought_quantity}",
        )
        self.assertEqual(
            summary.bought_amount,
            -500,
            f"[{self.symbol}] Expected bought_amount: -500 Got: {summary.bought_amount}",
        )
        self.assertEqual(
            summary.sold_quantity,
            3,
            f"[{self.symbol}] Expected sold_quantity: 3 Got: {summary.sold_quantity}",
        )
        self.assertEqual(
            summary.sold_amount,
            450,
            f"[{self.symbol}] Expected sold_amount: 450 Got: {summary.sold_amount}",
        )

        # Test averages
        self.assertEqual(
            summary.get_average_bought_price(),
            -1.0,
            f"[{self.symbol}] Expected avg bought price: -1.0 Got: {summary.average_bought_price}",
        )
        self.assertEqual(
            summary.get_average_sold_price(),
            1.5,
            f"[{self.symbol}] Expected avg sold: 1.5 Got: {summary.average_sold_price}",
        )

    def test_multiple_trades(self):
        """Test summary with multiple buy and sell trades"""
        # Add another stock buy with sells
        stock_buy2 = BuyTrade(
            {
                "trade_id": 3,
                "symbol": self.symbol,
                "action": "B",
                "trade_date": self.buy_date,
                "trade_type": "L",
                "quantity": 200,
                "price": 15.0,
                "amount": -3000.0,
                "is_option": False,
                "sells": [],
            },
        )

        stock_sell2 = SellTrade(
            {
                "trade_id": 103,
                "symbol": self.symbol,
                "action": "S",
                "trade_date": self.sell_date,
                "trade_type": "L",
                "quantity": 200,
                "price": 18.0,
                "amount": 3600.0,
                "is_option": False,
            }
        )

        stock_buy2.sells.append(stock_sell2)
        self.stock_trades.buy_trades.append(stock_buy2)

        summary = TradeSummary.create_from_buy_trades_collection(
            symbol=self.symbol, buy_trades_collection=self.stock_trades
        )

        # Test totals
        self.assertEqual(
            summary.bought_quantity,
            300,
            f"[{self.symbol}] Expected bought_quantity: 300 Got: {summary.bought_quantity}",
        )
        self.assertEqual(
            summary.bought_amount,
            -4000,
            f"[{self.symbol}] Expected bought_amount: -4000 Got: {summary.bought_amount}",
        )
        self.assertEqual(
            summary.sold_quantity,
            250,
            f"[{self.symbol}] Expected sold_quantity: 250 Got: {summary.sold_quantity}",
        )
        self.assertEqual(
            summary.sold_amount,
            4200,
            f"[{self.symbol}] Expected sold_amount: 4200 Got: {summary.sold_amount}",
        )

        # Test averages
        self.assertEqual(
            summary.get_average_bought_price(),
            -13.333,
            f"[{self.symbol}] Expected avg bought price: -13.333 Got: {summary.average_bought_price}",
        )
        self.assertEqual(
            summary.get_average_sold_price(),
            16.8,
            f"[{self.symbol}] Expected avg sold: 16.8 Got: {summary.average_sold_price}",
        )

    def test_validation_errors(self):
        """Test validation checks in summary creation"""
        bad_symbol = "WRONG"
        # Test symbol mismatch
        bad_symbol_trade = BuyTrade(
            {
                "trade_id": 4,
                "symbol": bad_symbol,
                "action": "B",
                "trade_date": self.buy_date,
                "trade_type": "L",
                "quantity": 100,
                "price": 10.0,
                "amount": -1000.0,
                "is_option": False,
                "sells": [],
            },
        )

        bad_trades = BuyTrades(security_type="stock", buy_trades=[bad_symbol_trade])

        with self.assertRaises(ValueError) as context:
            TradeSummary.create_from_buy_trades_collection(
                symbol=self.symbol, buy_trades_collection=bad_trades
            )

        self.assertIn(
            f"Trade symbol {bad_symbol} != summary symbol {self.symbol}",
            str(context.exception),
        )

        # Test security type mismatch
        bad_type_trade = BuyTrade(
            {
                "trade_id": 5,
                "symbol": self.symbol,
                "action": "BO",
                "trade_date": self.buy_date,
                "trade_type": "C",
                "quantity": 100,
                "price": 10.0,
                "amount": -1000.0,
                "is_option": True,  # Should be stock
                "sells": [],
            },
        )

        bad_trades = BuyTrades(security_type="stock", buy_trades=[bad_type_trade])

        with self.assertRaises(ValueError) as context:
            TradeSummary.create_from_buy_trades_collection(
                symbol=self.symbol, buy_trades_collection=bad_trades
            )

        # Test sell date before buy date
        early_sell = SellTrade(
            {
                "trade_id": 104,
                "symbol": self.symbol,
                "action": "S",
                "trade_date": self.buy_date - timedelta(days=2),
                "trade_type": "L",
                "quantity": 100,
                "price": 10.0,
                "amount": 1000.0,
                "is_option": False,
            }
        )

        bad_buy_early_sell = BuyTrade(
            {
                "trade_id": 6,
                "symbol": self.symbol,
                "action": "B",
                "trade_date": self.buy_date,
                "trade_type": "L",
                "quantity": 100,
                "price": 10.0,
                "amount": -1000.0,
                "is_option": False,
            }
        )
        bad_buy_early_sell.apply_sell_trade(early_sell)

        bad_trades = BuyTrades(security_type="stock", buy_trades=[bad_buy_early_sell])

        with self.assertRaises(ValueError) as context:
            TradeSummary.create_from_buy_trades_collection(
                symbol=bad_buy_early_sell.symbol, buy_trades_collection=bad_trades
            )

        self.assertIn("Sell date", str(context.exception))
        self.assertIn("before buy date", str(context.exception))

    def test_calculated_fields(self):
        """Test calculated fields after final totals"""
        summary = TradeSummary.create_from_buy_trades_collection(
            symbol=self.symbol, buy_trades_collection=self.stock_trades
        )

        # Set closed quantities (normally done by process_all_trades)
        summary.process_all_trades(self.symbol)
        # summary.calculate_final_totals(final_sold_quantity=50, final_sold_amount=600)

        # Test open quantities
        self.assertEqual(
            summary.get_open_bought_quantity(),
            50,
            f"[{self.symbol}] Expected open qty: 50 Got: {summary.open_bought_quantity}",
        )
        self.assertEqual(
            summary.get_open_bought_amount(),
            -500,
            f"[{self.symbol}] Expected open bought amount: -500 Got: {summary.open_bought_amount}",
        )

        # Test profit/loss
        # BuyTrade  { "trade_id": 1, "symbol": self.symbol, "action": "B", "trade_date": self.buy_date, "trade_type": "L", "quantity": 100, "price": 10.0, "amount": 1000.0,  # Negative for buy "is_option": False, "sells": [], },
        # SellTrade { "trade_id": "101", "symbol": self.symbol, "action": "S", "trade_date": self.sell_date, "trade_type": "L", "quantity": 50, "price": 12.0, "amount": 600.0,  # Positive for sell "is_option": False, },

        # Buy 50 @ 10 = -500
        # Sell 50 @ 12 = 600  => P/L = +100
        self.assertEqual(
            summary.get_profit_loss(),
            100,
            f"[{self.symbol}] Expected P/L: $ 100 Got: {summary.profit_loss}",
        )

        self.assertEqual(
            summary.get_percent_profit_loss(),
            20.0,
            f"[{self.symbol}] Expected % P/L: 20.0 Got: {summary.percent_profit_loss}",
        )

        # Test basis prices
        self.assertEqual(
            summary.get_average_basis_sold_price(),
            10.0,
            f"[{self.symbol}] Expected basis sold price: 10.0 Got: {summary.average_basis_sold_price}",
        )
        self.assertEqual(
            summary.get_average_basis_open_price(),
            10.0,
            f"[{self.symbol}] Expected basis open price: 10.0 Got: {summary.average_basis_open_price}",
        )

    def test_zero_quantity_handling(self):
        """Test handling of zero quantities in calculations"""
        # Create trade with no sells
        buy_only = BuyTrade(
            {
                "trade_id": 7,
                "symbol": self.symbol,
                "action": "B",
                "trade_date": self.buy_date,
                "trade_type": "L",
                "quantity": 100,
                "price": 10.0,
                "amount": -1000.0,
                "is_option": False,
                "sells": [],
            },
        )

        trades = BuyTrades(security_type="stock", buy_trades=[buy_only])

        summary = TradeSummary.create_from_buy_trades_collection(
            symbol=self.symbol, buy_trades_collection=trades
        )

        # Test averages with zero sold quantity
        self.assertEqual(
            summary.get_average_sold_price(),
            0.0,
            f"[{self.symbol}] Expected avg sold: 0.0 Got: {summary.average_sold_price}",
        )

        # Test calculated fields
        summary.calculate_final_totals(0, 0)
        self.assertEqual(
            summary.get_open_bought_quantity(),
            100,
            f"[{self.symbol}] Expected open qty: 100 Got: {summary.open_bought_quantity}",
        )
        self.assertEqual(
            summary.get_profit_loss(),
            0.0,
            f"[{self.symbol}] Expected P/L: 0.0 Got: {summary.profit_loss}",
        )
        self.assertEqual(
            summary.get_percent_profit_loss(),
            0.0,
            f"[{self.symbol}] Expected % P/L: 0.0 Got: {summary.percent_profit_loss}",
        )
        self.assertEqual(
            summary.get_average_basis_sold_price(),
            0.0,
            f"[{self.symbol}] Expected basis sold: 0.0 Got: {summary.average_basis_sold_price}",
        )

    def test_date_conversion(self):
        """Test after_date conversion to ISO format"""
        # Test with datetime object
        dt_obj = datetime(2023, 1, 15, 10, 30, 0)
        summary = TradeSummary(symbol=self.symbol, is_option=False, after_date=dt_obj)
        self.assertEqual(
            summary.after_date,
            "2023-01-15T10:30:00",
            f"[{self.symbol}] Expected ISO date: 2023-01-15T10:30:00 Got: {summary.after_date}",
        )

        # Test with string in ISO format
        summary = TradeSummary(
            symbol=self.symbol, is_option=False, after_date="2023-01-15T10:30:00"
        )
        self.assertEqual(
            summary.after_date,
            "2023-01-15T10:30:00",
            f"[{self.symbol}] Expected ISO date: 2023-01-15T10:30:00 Got: {summary.after_date}",
        )

        # Test with date string
        summary = TradeSummary(
            symbol=self.symbol, is_option=False, after_date="2023-01-15"
        )
        self.assertEqual(
            summary.after_date,
            "2023-01-15T00:00:00",
            f"[{self.symbol}] Expected ISO date: 2023-01-15T00:00:00 Got: {summary.after_date}",
        )

        # Test invalid format
        with self.assertRaises(ValueError):
            TradeSummary(symbol=self.symbol, is_option=False, after_date="15-01-2023")


if __name__ == "__main__":
    unittest.main()
