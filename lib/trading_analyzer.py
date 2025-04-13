# lib/trading_analyzer.py
from dotenv import load_dotenv
import os

load_dotenv()

import warnings
import logging
import os
import time
from dataclasses import replace
from datetime import datetime
from typing import Any, List, Dict, Optional, Tuple, Union
from lib.dataclasses.Trade import BuyTrade, SellTrade
from lib.dataclasses.TradeSummary import TradeSummary
from lib.dataclasses.ActionMapping import ActionMapping


OPTIONS_MULTIPLIER = 100
STOCK_MULTIPLIER = 1

timestr = time.strftime("%Y%m%d")
log_level = os.getenv("LOG_LEVEL", "INFO").upper()


logging.basicConfig(
    filename=f"./logs/trading_analyzer_{timestr}.log",
    # level=logging.DEBUG,
    level=log_level,
    format="%(asctime)s - %(levelname)s - %(lineno)d> %(message)s",
)


class TradingAnalyzer:

    def __init__(
        self, stock_symbol: str, trade_transactions: List[Dict[str, Any]]
    ) -> None:
        if not isinstance(stock_symbol, str):
            raise TypeError("stock_symbol must be a string")
        if not isinstance(trade_transactions, list):
            raise TypeError("trade_transactions must be a list")

        self.stock_symbol = stock_symbol
        self.trade_transactions = trade_transactions
        self.profit_loss_data = {}

        self.buy_sell_actions = ["B", "Buy", "BO", "S", "SC"]
        self.action_mapping = ActionMapping()

    def _is_option(self, trade: Dict[str, Any]) -> bool:
        return trade["trade_type"] in ("C", "P") or trade["action"] in ("EXP", "EE")

    def _validate_trade(self, trade: Dict[str, Any]) -> None:
        """Validate a trade to ensure it has the required fields and valid data.

        Args:
            trade (Dict[str, Any]): A trade transaction.

        Raises:
            ValueError: If the trade is missing required fields or contains invalid data.
        """
        required_fields = ["id", "symbol", "action", "quantity", "price", "trade_date"]
        for field in required_fields:
            if field not in trade:
                raise ValueError(f"Trade is missing required field: {field}")

        if not isinstance(trade["quantity"], (int, float)) or trade["quantity"] <= 0:
            raise ValueError(f"Invalid quantity in trade: {trade["quantity"]}")

        if self.action_mapping.get_full_name(trade["action"]) is None:
            raise ValueError(f"Invalid action acronym in trade: {trade['Action']}")

        trade["is_option"] = self._is_option(trade)

        if trade["action"] == "EXP":
            # Expired Option. Convert it to a Sell trade for price=0, amount=0
            trade["action"] = "SC"
            trade["amount"] = 0
            trade["Reason"] = "Expired Option"
        elif trade["action"] == "EE":
            # The Option is Exercised. Convert it to a Sell trade for price=0, amount=0
            # TODO Find subsequent Buy Trade and
            trade["action"] = "SC"
            trade["price"] = trade["target_price"]
            trade["amount"] = trade["target_price"] * trade["quantity"] * 100
            trade["Reason"] = "Exercised Option"

        if trade["action"] in (self.buy_sell_actions):
            if not isinstance(trade["price"], (int, float)) or trade["price"] <= 0:
                raise ValueError(f"Invalid price in trade: {trade['price']}")

        # Check that Trade Date is either a string or datetime
        if not isinstance(trade["trade_date"], (str, datetime)):
            raise ValueError(
                f"Invalid trade date in trade: {trade['Trade Date']}, must be a string or datetime object"
            )

    def _sell_adder(
        self,
        buy_trade: BuyTrade,
        sell_trade_unapplied: SellTrade,
        symbol: str,
    ) -> SellTrade:
        """Create a SellTrade object from a sell trade dictionary.

        Args:
            buy_trade (BuyTrade): The buy trade object.
            sell_trade_unapplied (SellTrade): The SellTrade not applied to this BuyTrade.
            symbol (str): The stock symbol.

        Returns:
            SellTrade: A SellTrade object to apply to the BuyTrade.
        """

        multiplier = OPTIONS_MULTIPLIER if buy_trade.is_option else STOCK_MULTIPLIER

        # The sell trade that IS applied to the buy trade
        sell_trade_applied = replace(sell_trade_unapplied)

        # Quantity and amount needed to close this buy trade
        qty_to_close_the_trade = buy_trade.quantity - buy_trade.current_sold_qty
        amt_to_close_the_trade = round(
            sell_trade_applied.price * qty_to_close_the_trade * multiplier, 2
        )

        if sell_trade_applied.quantity == qty_to_close_the_trade:
            sell_trade_applied.close_buy_and_sell_trade(
                buy_trade,
                sell_trade_unapplied,
                qty_to_close_the_trade,
                amt_to_close_the_trade,
            )
            sell_trade_unapplied = None
            logging.debug(
                f"Closed BuyTrade: {buy_trade.trade_id} with qty: {qty_to_close_the_trade} and amount: {amt_to_close_the_trade}"
            )

        elif sell_trade_applied.quantity > qty_to_close_the_trade:
            # The BuyTrade is closed. The remaining SellTrade can be applied to the next BuyTrade
            sell_trade_unapplied = sell_trade_applied.close_buy_trade_update_sell_trade(
                buy_trade,
                sell_trade_unapplied,
                qty_to_close_the_trade,
                amt_to_close_the_trade,
            )
            logging.debug(
                f"Closed BuyTrade: {buy_trade.trade_id} with quantity: {qty_to_close_the_trade} and amount: {amt_to_close_the_trade}"
            )
        else:
            # sell_trade_applied .quantity < qty_to_close_the_trade:
            sell_trade_applied.update_buy_trade_close_sell_trade(
                buy_trade, sell_trade_unapplied
            )
            sell_trade_unapplied = None
            logging.debug(
                f"Update buy/sell trade: {buy_trade.trade_id} with quantity: {sell_trade_applied .quantity} and amount: {sell_trade_applied .amount}"
            )

        logging.debug(f"[{symbol}] Applied SellTrade: {sell_trade_applied }")
        logging.debug(f"[{symbol}] Unapplied SellTrade: {sell_trade_unapplied}")
        return replace(sell_trade_applied)

    def _initialize_buy_trade(self, buy_record: Dict[str, Any]) -> BuyTrade:
        """Create a BuyTrade object from a buy record dictionary.

        Args:
            buy_record (dict): A dictionary containing trade data.

        Returns:
            BuyTrade: A Trade object representing the buy trade.
        """

        return BuyTrade(
            trade_id=buy_record["id"],
            symbol=buy_record["symbol"],
            action=buy_record["action"],
            trade_date=buy_record["trade_date"],
            trade_type=buy_record["trade_type"],
            trade_label=buy_record["label"],
            quantity=buy_record["quantity"],
            price=buy_record["price"],
            target_price=buy_record["target_price"],
            amount=buy_record["amount"],
            current_sold_qty=0,
            is_option=buy_record.get("is_option", False),
            is_done=buy_record.get("is_done", False),
            account=buy_record.get("account", None),
            expiration_date_iso=buy_record.get("expiration_date", None),
        )

    def _initialize_sell_trade(
        self,
        sell_trade: Dict[str, Any],
    ) -> SellTrade:

        return SellTrade(
            trade_id=sell_trade["id"],
            symbol=sell_trade["symbol"],
            action=sell_trade["action"],
            trade_date=sell_trade["trade_date"],
            trade_type=sell_trade.get("trade_type", None),
            trade_label=sell_trade.get("label", None),
            quantity=sell_trade.get("quantity", 0.0),
            price=sell_trade.get("price", 0.0),
            amount=sell_trade.get("amount", 0.0),  # Ensure amount is set, default to 0
            reason=sell_trade.get("reason", None),
            initial_stop_price=sell_trade.get("initial_stop_price", None),
            projected_sell_price=sell_trade.get("projected_sell_price", None),
            account=sell_trade.get("account", None),
            is_option=sell_trade.get("is_option", False),
            is_done=sell_trade.get("is_done", False),
            target_price=sell_trade.get("target_price", None),
            expiration_date_iso=sell_trade.get("expiration_date", None),
            profit_loss=0,
            percent_profit_loss=0,
        )

    def _add_sells_to_this_trade(
        self, buy_trade: BuyTrade, sell_trades: List[SellTrade], symbol: str
    ) -> None:
        """Add sell trades to a buy trade and update quantities and amounts.

        Args:
            buy_trade (BuyTrade): The buy trade object.
            sell_trades (List[SellTrade]): A list of sell trade dictionaries.
            symbol (str): The stock symbol.
        """

        while sell_trades and (buy_trade.current_sold_qty < buy_trade.quantity):
            sell_trade = sell_trades[0]
            sell_rec_for_trade = self._sell_adder(buy_trade, sell_trade, symbol)

            # if sell_trade["is_done"]:
            if sell_trade is None or sell_trade.is_done:
                sell_trades.pop(0)

            buy_trade.sells.append(sell_rec_for_trade)

    def _stock_option_summary_sanity_check(
        self, stock_summary: TradeSummary, option_summary: TradeSummary
    ) -> None:

        symbol = self.stock_symbol

        for i, summary in enumerate([stock_summary, option_summary]):
            type = "stock" if i == 0 else "option"

            log_msg = f"""
                [{symbol}] Total {type} buy quantity: {summary.bought_quantity}
                [{symbol}] Total {type} buy amount: {summary.bought_amount}
                """
            logging.info(log_msg)

            # Validate that we are not selling more than we bought
            if summary.sold_quantity > summary.bought_quantity:
                warnings.warn(
                    f"[{symbol}] Total {type} quantity sold ({summary.sold_quantity}) exceeds total {type} quantity bought ({summary.bought_quantity})"
                )

            if summary.bought_quantity > summary.sold_quantity:
                logging.info(f"[{symbol}] has some open {type} trades")
            else:
                logging.info(f"[{symbol}] All {type} trades have been closed")

            log_msg = f"""
                [{symbol}] Total {type} Bought Q: {summary.bought_quantity}
                [{symbol}] Total {type} Sold Q: {summary.sold_quantity}
                """
            logging.info(log_msg)

    def _create_stock_and_option_summary(
        self, sorted_trades: List[Dict[str, Any]]
    ) -> Tuple[TradeSummary, TradeSummary]:
        """Create summaries for stock and option trades.

        Args:
            sorted_trades (list): A list of sorted trade transactions.

        Returns
            tuple: A tuple containing stock_summary and option_summary.
        """
        # Initialize summaries
        stock_summary = TradeSummary(
            symbol=self.stock_symbol,
            is_option=False,
        )
        option_summary = TradeSummary(
            symbol=self.stock_symbol,
            is_option=True,
        )

        for trade in sorted_trades:
            if trade["symbol"] != self.stock_symbol:
                raise ValueError(
                    f"Trade symbol {trade['Symbol']} does not match stock symbol {self.stock_symbol}"
                )

            trade["is_option"] = self._is_option(trade)

            action_name = self.action_mapping.get_full_name(trade["action"])
            summary = option_summary if trade["is_option"] else stock_summary

            logging.debug(
                f'[{self.stock_symbol}] ID: {trade["id"]} Action: {trade["action"]} Action Name: {action_name}'
            )
            logging.debug(
                f'[{self.stock_symbol}] Type: {trade["trade_type"]} IsOption: {trade["is_option"]}'
            )

            if self.action_mapping.is_buy_type_action(trade["action"]):
                summary.bought_quantity += trade.get("quantity", 0)
                summary.bought_amount += trade.get("amount", 0)
                summary.buy_trades.append(self._initialize_buy_trade(trade))
            elif self.action_mapping.is_sell_type_action(trade["action"]):
                summary.sold_quantity += trade.get("quantity", 0)
                summary.sold_amount += trade.get("amount", 0)
                summary.sell_trades.append(self._initialize_sell_trade(trade))

        stock_summary.get_average_bought_price()
        option_summary.get_average_bought_price()
        stock_summary.get_average_sold_price()
        option_summary.get_average_sold_price()

        logging.debug(f"[{self.stock_symbol}] Stock Summary: {stock_summary}")
        return stock_summary, option_summary

    def _add_buy_trade_to_summary(
        self, summmary: TradeSummary, buy_trade: BuyTrade, multiplier: int
    ) -> None:
        "In place update of summmary"

        summmary.bought_amount += buy_trade.amount
        summmary.bought_quantity += buy_trade.quantity
        summmary.sold_quantity += buy_trade.current_sold_qty
        summmary.closed_bought_amount += (
            buy_trade.current_sold_qty * buy_trade.price * multiplier
        )
        summmary.sold_amount += sum([sell.amount for sell in buy_trade.sells])

        summmary.profit_loss += sum([sell.profit_loss for sell in buy_trade.sells])

    def analyze_trades(self) -> None:
        """Analyze trades and calculate profit/loss for each trade."""
        symbol = self.stock_symbol
        logging.info(f"Working on symbol: {symbol}")

        try:
            # Validate all trades before processing. Flag Options trades
            for trade in self.trade_transactions:
                self._validate_trade(trade)
                # self._initialize_sell_trade(sell_trade, buy_trade)

            sorted_trades = self._sort_trades()

            stock_summary, option_summary = self._create_stock_and_option_summary(
                sorted_trades
            )
            logging.debug(f"[{symbol}] Option Summary: {option_summary}")
            self._initialize_profit_loss_data(
                stock_summary=stock_summary, option_summary=option_summary
            )

            self._stock_option_summary_sanity_check(stock_summary, option_summary)

            self._process_trades_by_type("stock", stock_summary, symbol)
            self._process_trades_by_type("option", option_summary, symbol)

        except ValueError as e:
            logging.error(f"[{symbol} Error analyzing trades: {e}")
            raise
        except Exception as e:
            logging.error(f"[{symbol} Unexpected error analyzing trades: {e}")
            raise

    def _sort_trades(self) -> List[Dict[str, Any]]:
        """Sort trades by trade date, type, and action."""
        return sorted(
            self.trade_transactions,
            # TODO Put "account" first
            key=lambda x: (
                x["trade_date"],
                x["action"],
                x["account"],
                x["is_option"],
                x["trade_type"],
            ),
        )

    def _initialize_profit_loss_data(
        self, stock_summary: TradeSummary, option_summary: TradeSummary
    ) -> Dict[str, Any]:
        """Initialize the profit/loss data structure."""
        self.profit_loss_data = {
            "stock": {
                "summary": stock_summary,
                "all_trades": [],
            },
            "option": {
                "summary": option_summary,
                "all_trades": [],
            },
        }
        return self.profit_loss_data

    def _process_trades_by_type(
        self, security_type: str, trade_summary: TradeSummary, symbol: str
    ) -> None:
        """Process trades for a specific type (stock or option)."""
        multiplier = 100 if security_type == "option" else 1
        running_bought_quantity = 0
        running_sold_quantity = 0
        running_sold_amount = 0
        # TODO If there is no reason to have buy_trades and sell_trades as lists in the TradeSummary
        # Put them separately

        sell_trades = trade_summary.sell_trades[:]
        # trade_summary.sell_trades.clear()
        sell_trades = trade_summary.sell_trades[:]
        buy_trades = trade_summary.buy_trades[:]
        # trade_summary.buy_trades.clear()

        while running_bought_quantity < trade_summary.bought_quantity:
            if not buy_trades:
                missing = trade_summary.bought_quantity - running_bought_quantity
                logging.error(f"[{symbol}] You are missing {missing} buy trades")
                break

            current_buy_record = buy_trades.pop(0)
            running_bought_quantity += current_buy_record.quantity

            logging.debug(
                f"[{symbol}] Running {security_type} bought qty: {running_bought_quantity}"
            )
            logging.debug(f"[{symbol}] Buy Trade: {current_buy_record}")

            # The sold Quantity that can be matched with this buy record
            unmatched_sold_quantity = (
                trade_summary.sold_quantity - running_sold_quantity
            )
            logging.info(
                f"[{symbol}] Sell {security_type} trade count: {len(sell_trades)}"
            )
            sold_quantity_this_trade = 0
            closed_bought_amount = 0

            if current_buy_record.quantity <= unmatched_sold_quantity:
                # This Buy record has matching sells
                sold_quantity_this_trade = current_buy_record.quantity
            else:
                # Buy record will have some open trades after this
                sold_quantity_this_trade = unmatched_sold_quantity

            running_sold_quantity += sold_quantity_this_trade

            logging.debug(
                f"[{symbol}] Unmatched {security_type} sold quantity: {unmatched_sold_quantity}"
            )
            logging.debug(
                f"[{symbol}] Current closed_{security_type} bought_quantity: {sold_quantity_this_trade}"
            )
            logging.debug(
                f"[{symbol}] Running {security_type} sold quantity: {running_sold_quantity}"
            )

            # The 'bought' amount with matching sells
            # Note: All bought amounts are negative
            closed_bought_amount = (
                -current_buy_record.price * sold_quantity_this_trade * multiplier
            )

            running_sold_amount += closed_bought_amount

            if sold_quantity_this_trade > 0:
                self._add_sells_to_this_trade(current_buy_record, sell_trades, symbol)

            self.profit_loss_data[security_type]["all_trades"].append(
                current_buy_record
            )

        # Calculate trade summary
        trade_summary.calculate_final_totals(running_sold_quantity, running_sold_amount)

    def get_results(self) -> Dict[str, Any]:
        # TODO: Replace this with 'get_profit_loss_data' method
        return self.profit_loss_data

    def get_profit_loss_data(self) -> Dict[str, Any]:
        """
        Returns:
             profit_loss_data = {
                "stock": {
                    "summary": {},
                    "all_trades": [],
                },
                "option": {
                    "summary": {},
                    "all_trades": [],
                },
            }

        """

        return self.profit_loss_data

    def _filter_trades_by_status(
        self,
        trade_status: str = "open",
        trade_transactions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Filter trades by status (open or closed)."""
        if trade_status not in ["open", "closed"]:
            raise ValueError("Invalid trade_status. Use 'open' or 'closed'.")

        logging.info(
            f'[filter_by_{trade_status}_trades] Getting all "{trade_status}" trades'
        )

        filtered_pl = {
            "stock_symbol": self.stock_symbol,
            "stock": {
                "summary": TradeSummary(symbol=self.stock_symbol, is_option=False),
                "all_trades": [],
            },
            "option": {
                "summary": TradeSummary(symbol=self.stock_symbol, is_option=True),
                "all_trades": [],
            },
        }
        self._process_filtered_trades(filtered_pl, trade_status, trade_transactions)
        return filtered_pl

    def _process_filtered_trades(
        self,
        filtered_pl: Dict[str, Any],
        trade_status: str,
        trade_transactions: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Process trades for a specific status (open or closed)."""
        if trade_transactions:
            self.trade_transactions = trade_transactions
            self.analyze_trades()

        symbol = self.stock_symbol

        logging.debug(f"[{symbol}] [filter_by_{trade_status}_trades]")

        for i, type_info in enumerate(
            [self.profit_loss_data["stock"], self.profit_loss_data["option"]]
        ):
            type = "stock" if i == 0 else "option"
            multiplier = 100 if type == "option" else 1
            all_trades = type_info["all_trades"]

            for buy_trade in all_trades:
                if buy_trade.symbol != self.stock_symbol:
                    raise ValueError(
                        f"Trade symbol {buy_trade.symbol} != {self.stock_symbol}"
                    )

                if (trade_status == "open" and not buy_trade.is_done) or (
                    trade_status == "closed" and buy_trade.is_done
                ):

                    self._add_buy_trade_to_summary(
                        filtered_pl[type]["summary"], buy_trade, multiplier
                    )

                    filtered_pl[type]["all_trades"].append(buy_trade)

            filtered_pl[type]["summary"].calculate_final_totals(
                filtered_pl[type]["summary"].sold_quantity,
                filtered_pl[type]["summary"].sold_amount,
            )

    def get_open_trades(
        self, trade_transactions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        return self._filter_trades_by_status("open", trade_transactions)

    def get_closed_trades(
        self, trade_transactions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        return self._filter_trades_by_status("closed", trade_transactions)
