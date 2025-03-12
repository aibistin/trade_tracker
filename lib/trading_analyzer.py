# lib/trading_analyzer.py

import warnings
import logging
import os
import time
from datetime import datetime
from typing import Any, List, Dict, Optional, Tuple, Union
from lib.dataclasses.Trade import Trade
from lib.dataclasses.SellTrade import SellTrade
from lib.dataclasses.TradeAction import TradeAction


timestr = time.strftime("%Y%m%d")

logging.basicConfig(
    filename=f"./logs/trading_analyzer_{timestr}.log",
    level=logging.DEBUG,
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
        self.profit_loss_data = {
            "stock_symbol": self.stock_symbol,
            "stock": {
                "summary": {},
                "all_trades": [],
            },
            "option": {
                "summary": {},
                "all_trades": [],
            },
        }


    def _validate_trade_data(self, trade: Dict) -> None:
        """Validate trade data to ensure required fields are present.
    
        Args:
            trade (Dict): A trade transaction.
    
        Raises:
            ValueError: If required fields are missing or invalid.
        """
        required_fields = ["Id", "Symbol", "Action", "Quantity", "Price", "Trade Date"]
        for field in required_fields:
            if field not in trade:
                raise ValueError(f"Missing required field in trade: {field}")
    
        if not isinstance(trade["Quantity"], (int, float)) or trade["Quantity"] <= 0:
            raise ValueError(f"Invalid quantity in trade: {trade['Quantity']}")
    
        if not isinstance(trade["Price"], (int, float)) or trade["Price"] <= 0:
            raise ValueError(f"Invalid price in trade: {trade['Price']}")
    
    

    def _sell_adder( self, buy_trade: Trade, sell_trade: Dict[str, Any], symbol: str) -> SellTrade:
        """Create a SellTrade object from a sell trade dictionary.
    
        Args:
            buy_trade (Trade): The buy trade object.
            sell_trade (dict): A dictionary containing sell trade data.
            symbol (str): The stock symbol.

        Returns:
            SellTrade: A SellTrade object representing the sell trade.
        """
        sell_rec_for_trade = self._initialize_sell_record(sell_trade)

        multiplier = 100 if buy_trade.is_option else 1

        logging.debug(f"[{symbol}] Current trade bought_quantity: {buy_trade.quantity}")
        logging.debug(f"[{symbol}] Sell record quantity: {sell_trade['Quantity']}")

        qty_to_close_the_trade = buy_trade.quantity - buy_trade.current_sold_qty
        amt_to_close_the_trade = (
            sell_trade["Price"] * qty_to_close_the_trade * multiplier
        )
        if sell_trade["Quantity"] == qty_to_close_the_trade:
            self._close_trade(
                buy_trade,
                sell_trade,
                sell_rec_for_trade,
                qty_to_close_the_trade,
                amt_to_close_the_trade,
            )
        elif sell_trade["Quantity"] > qty_to_close_the_trade:
            self._partially_close_trade(
                buy_trade,
                sell_trade,
                sell_rec_for_trade,
                qty_to_close_the_trade,
                amt_to_close_the_trade,
            )
        else:
            self._keep_trade_open(buy_trade, sell_trade, sell_rec_for_trade)

        self._calculate_profit_loss(buy_trade, sell_trade, sell_rec_for_trade)
        logging.debug(f"[{symbol}] Append this to the buy trade: {sell_rec_for_trade}")

        # TODO Keep this?
        return SellTrade(
            trade_id=sell_trade["Id"],
            trade_date=sell_trade["Trade Date"],
            trade_date_iso=self._convert_to_iso_format(sell_trade["Trade Date"]),
            quantity=sell_rec_for_trade["quantity"],
            price=sell_trade["Price"],
            amount=round(sell_rec_for_trade["amount"], 2),
            profit_loss=sell_rec_for_trade["profit_loss"],
            percent_profit_loss=sell_rec_for_trade["percent_profit_loss"],
            account=sell_trade.get("Account", None),
        )


    def _get_average_bought_price(
        self, trade: Dict[str, Any], multiplier: int
    ) -> float:
        return (
            round(
                trade["bought_amount"] / (trade["bought_quantity"] * multiplier),
                2,
            )
            if trade["bought_quantity"] != 0
            else 0
        )

    def _get_average_sold_price(self, trade: Dict[str, Any], multiplier: int) -> float:
        return (
            round(
                trade["sold_amount"] / (trade["sold_quantity"] * multiplier),
                2,
            )
            if trade["sold_quantity"] != 0
            else 0
        )

    def _get_percent_profit_loss(self, trade: Dict[str, Any]) -> float:
        if trade["closed_bought_amount"] != 0:
            return round(
                (trade["profit_loss"] / abs(trade["closed_bought_amount"])) * 100, 2
            )
        return 0

    def _convert_to_iso_format(self, date_obj: Union[datetime, str]) -> str:
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d")
                # date_obj = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
            except ValueError:
                logging.error(f"Could not parse date string: {date_obj}")
                raise
        return date_obj.isoformat()

    def _initialize_sell_record(self, sell_trade: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "trade_id": sell_trade["Id"],
            "trade_date_iso": self._convert_to_iso_format(sell_trade["Trade Date"]),
            "trade_date": sell_trade["Trade Date"],
            "quantity": 0,
            "price": sell_trade["Price"],
            "amount": 0,
            "profit_loss": 0,
            "percent_profit_loss": 0,
            "account": sell_trade.get("Account", None),
        }

    def _close_trade(
        self,
        buy_trade: Trade,
        sell_trade: Dict[str, Any],
        sell_rec_for_trade: Dict[str, Any],
        qty_to_close: float,
        amt_to_close: float,
    ) -> None:
        """Close the trade by updating the quantities and amounts.
        Args:
            buy_trade (Trade): The buy trade object.
            sell_trade (dict): The sell trade dictionary.
            sell_rec_for_trade (dict): The sell record for the trade.
            qty_to_close (float): The quantity to close the trade.
            amt_to_close (float): The amount to close the trade.
        """
        sell_rec_for_trade["quantity"] = qty_to_close
        sell_rec_for_trade["amount"] = amt_to_close
        buy_trade.current_sold_qty += qty_to_close
        buy_trade.is_done = True
        sell_trade["is_done"] = True

        logging.debug(
            f"Closed trade: {buy_trade.trade_id} with quantity: {qty_to_close} and amount: {amt_to_close}"
        )


    def _partially_close_trade(
        self,
        buy_trade: Trade,
        sell_trade: Dict[str, Any],
        sell_rec_for_trade: Dict[str, Any],
        qty_to_close: float,
        amt_to_close: float,
    ) -> None:
        """Partially close the trade by updating the quantities and amounts.

        Args:
            buy_trade (Trade): The buy trade object.
            sell_trade (dict): The sell trade dictionary.
            sell_rec_for_trade (dict): The sell record for the trade.
            qty_to_close (float): The quantity to close the trade.
            amt_to_close (float): The amount to close the trade.
        """
        sell_rec_for_trade["quantity"] = qty_to_close
        sell_rec_for_trade["amount"] = amt_to_close
        buy_trade.current_sold_qty += qty_to_close
        sell_trade["Quantity"] -= qty_to_close
        sell_trade["Amount"] -= amt_to_close
        buy_trade.is_done = True
        sell_trade["is_done"] = False

        logging.debug(
            f"Partially closed trade: {buy_trade.trade_id} with quantity: {qty_to_close} and amount: {amt_to_close}"
        )


    def _keep_trade_open(
        self,
        buy_trade: Trade,
        sell_trade: Dict[str, Any],
        sell_rec_for_trade: Dict[str, Any],
    ) -> None:
        """Keep the trade open by updating the quantities and amounts.

        Args:
            buy_trade (Trade): The buy trade object.
            sell_trade (dict): The sell trade dictionary.
            sell_rec_for_trade (dict): The sell record for the trade.
        """
        sell_rec_for_trade["quantity"] = sell_trade["Quantity"]
        sell_rec_for_trade["amount"] = sell_trade["Amount"]
        buy_trade.current_sold_qty += sell_trade["Quantity"]
        buy_trade.is_done = False
        sell_trade["is_done"] = True

        logging.debug(
            f"Kept trade open: {buy_trade.trade_id} with quantity: {sell_trade['Quantity']} and amount: {sell_trade['Amount']}"
        )


    def _calculate_profit_loss(
        self,
        buy_trade: Trade,
        sell_trade: Dict[str, Any],
        sell_rec_for_trade: Dict[str, Any],
    ) -> None:
        """Calculate profit/loss for a sell trade and update the sell record.

        Args:
            buy_trade (Trade): The buy trade object.
            sell_trade (dict): The sell trade dictionary.
            sell_rec_for_trade (dict): The sell record for the trade.
        """

        multiplier = 100 if buy_trade.is_option else 1
        # Calculate the price difference between the sell and buy trades
        price_difference = sell_trade["Price"] - buy_trade.price

        # Calculate the profit/loss for the sell trade
        sell_rec_for_trade["profit_loss"] = round(
            price_difference * sell_rec_for_trade["quantity"] * multiplier, 2
        )
        # Calculate the percentage profit/loss
        sell_rec_for_trade["percent_profit_loss"] = round(
            (price_difference / buy_trade.price) * 100, 2
        )

    def _add_sells_to_this_trade(
        self, buy_trade: Trade, sell_trades: List[dict], symbol: str
    ) -> None:
        """Add sell trades to a buy trade and update quantities and amounts.

        Args:
            buy_trade (Trade): The buy trade object.
            sell_trades (List[dict]): A list of sell trade dictionaries.
            symbol (str): The stock symbol.
        """
        bought_qty = buy_trade.quantity

        while sell_trades and (buy_trade.current_sold_qty < bought_qty):
            sell = sell_trades[0]
            logging.debug(
                f"################## Start _add_sells_to_trade #####################"
            )
            sell_rec_for_trade = self._sell_adder(buy_trade, sell, symbol)
            logging.debug(
                f"################## End _add_sells_to_trade #####################"
            )

            if sell["is_done"]:
                sell_trades.pop(0)

            buy_trade.sells.append(sell_rec_for_trade)


    def _create_current_buy_trade_record(self, buy_record: Dict[str, Any]) -> Trade:
        """Create a Trade object from a buy record dictionary.

        Args:
            buy_record (dict): A dictionary containing trade data.

        Returns:
            Trade: A Trade object representing the buy trade.
        """
        expiration_date_iso = (
            self._convert_to_iso_format(buy_record["Expiration Date"])
            if "Expiration Date" in buy_record and buy_record["Expiration Date"]
            else None
        )

        return Trade(
            trade_id=buy_record["Id"],
            symbol=buy_record["Symbol"],
            action=buy_record["Action"],
            trade_date=buy_record["Trade Date"],
            trade_date_iso=self._convert_to_iso_format(buy_record["Trade Date"]),
            trade_type=buy_record["Trade Type"],
            trade_label=buy_record["Label"],
            quantity=buy_record["Quantity"],
            price=buy_record["Price"],
            target_price=buy_record["Target Price"],
            amount=buy_record["Amount"],
            current_sold_qty=0,
            is_done=False,
            account=buy_record.get("Account", None),
            is_option=buy_record["is_option"],
            expiration_date_iso=expiration_date_iso,
        )


    def _stock_option_summary_sanity_check(
        self, stock_summary: Dict[str, Any], option_summary: Dict[str, Any]
    ) -> None:

        symbol = self.stock_symbol

        for i, summary in enumerate([stock_summary, option_summary]):
            type = "stock" if i == 0 else "option"

            log_msg = f"""
                [{symbol}] Total {type} buy quantity: {summary["bought_quantity"]}
                [{symbol}] Total {type} buy amount: {summary["bought_amount"]}
                """
            logging.info(log_msg)

            # Validate that we are not selling more than we bought
            if summary["sold_quantity"] > summary["bought_quantity"]:
                warnings.warn(
                    f'[{symbol}] Total {type} quantity sold ({summary["sold_quantity"]}) exceeds total {type} quantity bought ({summary["bought_quantity"]})'
                )

            if summary["bought_quantity"] > summary["sold_quantity"]:
                logging.info(f"[{symbol}] has some open {type} trades")
            else:
                logging.info(f"[{symbol}] All {type} trades have been closed")

            log_msg = f"""
                [{symbol}] Total {type} Bought Q: {summary["bought_quantity"]}
                [{symbol}] Total {type} Sold Q: {summary["sold_quantity"]}
                """
            logging.info(log_msg)

    def _get_summary_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.stock_symbol,
            "bought_quantity": 0.0,
            "bought_amount": 0.0,
            "average_bought_price": 0.0,
            "sold_quantity": 0.0,
            "sold_amount": 0.0,
            "average_basis_sold_price": 0,
            "average_basis_open_price": 0,
            "average_sold_price": 0.0,
            "closed_bought_quantity": 0,
            "closed_bought_amount": 0,
            "open_bought_quantity": 0,
            "open_bought_amount": 0,
            "profit_loss": 0,
            "percent_profit_loss": 0,
            "is_option": False,
            "buy_trades": [],
            "sell_trades": [],
        }

    def _create_stock_and_option_summary(
        self, sorted_trades: List[Dict[str, Any]]
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Create summaries for stock and option trades.

        Args:
            sorted_trades (list): A list of sorted trade transactions.

        Returns
            tuple: A tuple containing stock_summary and option_summary.
        """
        # Initialize summaries
        stock_summary = self._get_summary_dict()
        option_summary = stock_summary.copy()
        option_summary["is_option"] = True

        for trade in sorted_trades:
            if trade["Symbol"] != self.stock_symbol:
                raise ValueError(
                    f"Trade symbol {trade['Symbol']} does not match stock symbol {self.stock_symbol}"
                )

            # Check if the trade has a valid amount
            amount = trade.get("Amount")
            if isinstance(amount, str):
                logging.info(f"[{self.stock_symbol}] - Amount: <{amount}>")
                continue

            # Determine if the trade is an option
            trade["is_option"] = trade["Trade Type"] in ("C", "P")

            # Use the TradeAction enum
            action = TradeAction(trade["Action"])  # Convert string to TradeAction enum
            summary = option_summary if trade["is_option"] else stock_summary

            # Handle buy actions
            if action in (
                TradeAction.BUY,
                TradeAction.REINVEST_SHARES,
                TradeAction.BUY_TO_OPEN,
            ):
                summary["bought_quantity"] += trade.get("Quantity", 0)
                summary["bought_amount"] += trade.get("Amount", 0)
                summary["buy_trades"].append(trade)

            # Handle sell actions
            elif action in (
                TradeAction.SELL,
                TradeAction.SELL_TO_CLOSE,
            ):
                summary["sold_quantity"] += trade.get("Quantity", 0)
                summary["sold_amount"] += trade.get("Amount", 0)
                summary["sell_trades"].append(trade)

        # Calculate average prices
        stock_summary["average_bought_price"] = self._get_average_bought_price(
            stock_summary, multiplier=1
        )
        option_summary["average_bought_price"] = self._get_average_bought_price(
            option_summary, multiplier=100
        )

        stock_summary["average_sold_price"] = self._get_average_sold_price(
            stock_summary, multiplier=1
        )
        option_summary["average_sold_price"] = self._get_average_sold_price(
            option_summary, multiplier=100
        )

        return stock_summary, option_summary


    def _add_buy_trade_to_summary(
        self, summary_dict: Dict[str, Any], buy_trade: Trade, multiplier: int
    ) -> None:
        "In place update of summary_dict"

        summary_dict["bought_amount"] += buy_trade.amount
        summary_dict["bought_quantity"] += buy_trade.quantity
        summary_dict["sold_quantity"] += buy_trade.current_sold_qty
        summary_dict["closed_bought_amount"] += (
            buy_trade.current_sold_qty * buy_trade.price * multiplier
        )
        summary_dict["sold_amount"] += sum([sell.amount for sell in buy_trade.sells])

        summary_dict["profit_loss"] += sum(
            [sell.profit_loss for sell in buy_trade.sells]
        )

    def analyze_trades(self) -> None:
        """Analyze trades and calculate profit/loss for each trade."""
        symbol = self.stock_symbol
        logging.info(f"Working on symbol: {symbol}")

        # Sort trades
        sorted_trades = self._sort_trades()

        # Create stock and option summaries
        stock_summary, option_summary = self._create_stock_and_option_summary(
            sorted_trades
        )

        # Initialize profit/loss data
        self.profit_loss_data = self._initialize_profit_loss_data(
            stock_summary, option_summary
        )

        # Sanity check summaries
        self._stock_option_summary_sanity_check(stock_summary, option_summary)

        # Process stock and option trades
        self._process_trades_by_type("stock", stock_summary, symbol)
        self._process_trades_by_type("option", option_summary, symbol)

    def _sort_trades(self) -> List[Dict[str, Any]]:
        """Sort trades by trade date, type, and action."""
        return sorted(
            self.trade_transactions,
            key=lambda x: (x["Trade Date"], x["Trade Type"], x["Action"]),
        )

    def _initialize_profit_loss_data(
        self, stock_summary: Dict[str, Any], option_summary: Dict[str, Any] 
    ) -> Dict[str, Any]:    
        """Initialize the profit/loss data structure."""
        return {
            "stock": {
                "summary": stock_summary,
                "all_trades": [],
            },
            "option": {
                "summary": option_summary,
                "all_trades": [],
            },
        }


    def _process_trades_by_type(
        self, trade_type: str, trade_summary: Dict[str, Any], symbol: str
    ) -> None:
        # self, trade_type: str, trade_summary: dict, symbol: str
        """Process trades for a specific type (stock or option)."""
        multiplier = 100 if trade_type == "option" else 1
        running_bought_quantity = 0
        running_sold_quantity = 0
        running_sold_amount = 0
        sell_trades = trade_summary.pop("sell_trades")
        buy_trades = trade_summary.pop("buy_trades")

        while running_bought_quantity < trade_summary["bought_quantity"]:
            buy_record = buy_trades.pop(0)
            running_bought_quantity += buy_record["Quantity"]

            logging.debug(
                f"[{symbol}] Running {trade_type} bought qty: {running_bought_quantity}"
            )
            logging.debug(f"[{symbol}] Buy Trade: {buy_record}")

            current_buy_trade = self._create_current_buy_trade_record(buy_record)

            # The sold Quantity that can be matched with this buy record
            unmatched_sold_quantity = (
                trade_summary["sold_quantity"] - running_sold_quantity
            )
            logging.info(
                f"[{symbol}] Sell {trade_type} trade count: {len(sell_trades)}"
            )
            sold_quantity_this_trade = 0
            closed_bought_amount = 0

            if buy_record["Quantity"] <= unmatched_sold_quantity:
                # This Buy record has matching sells
                sold_quantity_this_trade = buy_record["Quantity"]
            else:
                # Buy record will have some open trades after this
                sold_quantity_this_trade = unmatched_sold_quantity

            running_sold_quantity += sold_quantity_this_trade

            logging.debug(
                f"[{symbol}] Unmatched {trade_type} sold quantity: {unmatched_sold_quantity}"
            )
            logging.debug(
                f"[{symbol}] Current closed_{trade_type} bought_quantity: {sold_quantity_this_trade}"
            )
            logging.debug(
                f"[{symbol}] Running {trade_type} sold quantity: {running_sold_quantity}"
            )

            # The 'bought' amount with matching sells
            # Note: All bought amounts are negative
            closed_bought_amount = (
                -buy_record["Price"] * sold_quantity_this_trade * multiplier
            )

            running_sold_amount += closed_bought_amount

            if sold_quantity_this_trade > 0:
                self._add_sells_to_this_trade(current_buy_trade, sell_trades, symbol)

            self.profit_loss_data[trade_type]["all_trades"].append(current_buy_trade)

        # Calculate trade summary
        self._calculate_trade_summary(
            trade_summary, running_sold_quantity, running_sold_amount, multiplier
        )

    def _calculate_trade_summary(
        self,
        trade_summary: Dict[str, Any],
        running_sold_quantity: float,
        running_sold_amount: float,
        multiplier: int,
    ) -> None:
        """Calculate summary metrics for a trade type."""
        trade_summary["closed_bought_quantity"] = running_sold_quantity
        trade_summary["closed_bought_amount"] = running_sold_amount

        # Calculate open shares for this symbol
        trade_summary["open_bought_quantity"] = round(
            trade_summary["bought_quantity"] - trade_summary["closed_bought_quantity"],
            2,
        )

        trade_summary["open_bought_amount"] = -round(
            abs(trade_summary["bought_amount"])
            - abs(trade_summary["closed_bought_amount"]),
            2,
        )

        # Calculate Profit/Loss
        if abs(trade_summary["closed_bought_amount"]) != 0:
            trade_summary["profit_loss"] = trade_summary["sold_amount"] - abs(
                trade_summary["closed_bought_amount"]
            )

        trade_summary["percent_profit_loss"] = self._get_percent_profit_loss(
            trade_summary
        )

        # Calculate Average Basis Sold Price
        if abs(trade_summary["sold_quantity"]) != 0:
            trade_summary["average_basis_sold_price"] = abs(
                trade_summary["closed_bought_amount"]
            ) / (abs(trade_summary["sold_quantity"] * multiplier))

        # Calculate Average Basis Un-Sold Price
        if abs(trade_summary["open_bought_quantity"]) != 0:
            trade_summary["average_basis_open_price"] = abs(
                trade_summary["open_bought_amount"]
            ) / (abs(trade_summary["open_bought_quantity"] * multiplier))


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

        # Initialize filtered profit/loss data
        filtered_pl = self._initialize_filtered_pl()

        # Process stock and option trades
        self._process_filtered_trades(filtered_pl, trade_status, trade_transactions)

        return filtered_pl

    def _initialize_filtered_pl(self) -> dict:
        """Initialize the filtered profit/loss data structure."""
        stock_summary = self._get_summary_dict()
        option_summary = stock_summary.copy()
        option_summary["is_option"] = True

        return {
            "stock_symbol": self.stock_symbol,
            "stock": {
                "summary": stock_summary,
                "all_trades": [],
            },
            "option": {
                "summary": option_summary,
                "all_trades": [],
            },
        }

    # def _process_filtered_trades(
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
        logging.debug(f"[filter_by_{trade_status}_trades] Symbol: [{symbol}]")

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

            self._calculate_filtered_summary(filtered_pl[type]["summary"], multiplier)

    def _calculate_filtered_summary(
        self, summary: Dict[str, Any], multiplier: int
    ) -> None:
        """Calculate summary metrics for filtered trades."""
        summary["average_bought_price"] = self._get_average_bought_price(
            summary, multiplier
        )
        summary["average_sold_price"] = self._get_average_sold_price(
            summary, multiplier
        )

        summary["open_bought_quantity"] = (
            summary["bought_quantity"] - summary["sold_quantity"]
        )

        summary["open_bought_amount"] = round(
            abs(summary["bought_amount"]) - abs(summary["closed_bought_amount"]),
            2,
        )

        summary["percent_profit_loss"] = self._get_percent_profit_loss(summary)

        # Calculate Average Basis Sold Price
        if abs(summary["sold_quantity"]) != 0:
            summary["average_basis_sold_price"] = abs(
                summary["closed_bought_amount"]
            ) / (abs(summary["sold_quantity"] * multiplier))

        # Calculate Average Basis Un-Sold Price
        if abs(summary["open_bought_quantity"]) != 0:
            summary["average_basis_open_price"] = abs(summary["open_bought_amount"]) / (
                abs(summary["open_bought_quantity"] * multiplier)
            )


    def get_open_trades(
        self, trade_transactions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        return self._filter_trades_by_status("open", trade_transactions)

    def get_closed_trades(
        self, trade_transactions: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        return self._filter_trades_by_status("closed", trade_transactions)
