# lib/trading_analyzer.py

import warnings
import logging
import time
from datetime import datetime

timestr = time.strftime("%Y%m%d")

logging.basicConfig(
    filename=f"./logs/trading_analyzer_{timestr}.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(lineno)d> %(message)s",
)


class TradingAnalyzer:

    def __init__(self, stock_symbol: str, trade_transactions: list) -> None:
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

    def _sell_adder(self, buy_trade: dict, sell_trade: dict, symbol: str) -> dict:
        bought_qty = buy_trade["quantity"]
        sell_rec_for_trade = self._initialize_sell_record(sell_trade)
        multiplier = 100 if buy_trade["is_option"] else 1

        logging.debug(f"[{symbol}] Current trade bought_quantity: {bought_qty}")
        logging.debug(f"[{symbol}] Sell record quantity: {sell_trade['Quantity']}")

        qty_to_close_the_trade = bought_qty - buy_trade["current_sold_qty"]
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
        return sell_rec_for_trade

    def _get_average_bought_price(self, trade, multiplier):
        return (
            round(
                trade["bought_amount"] / (trade["bought_quantity"] * multiplier),
                2,
            )
            if trade["bought_quantity"] != 0
            else 0
        )

    def _get_average_sold_price(self, trade, multiplier):
        return (
            round(
                trade["sold_amount"] / (trade["sold_quantity"] * multiplier),
                2,
            )
            if trade["sold_quantity"] != 0
            else 0
        )

    def _get_percent_profit_loss(self, trade):
        if trade["closed_bought_amount"] != 0:
            return round(
                (trade["profit_loss"] / abs(trade["closed_bought_amount"])) * 100, 2
            )
        return 0

    def _convert_to_iso_format(self, date_obj: datetime | str) -> str:
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d")
                # date_obj = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
            except ValueError:
                logging.error(f"Could not parse date string: {date_obj}")
                raise
        return date_obj.isoformat()

    def _initialize_sell_record(self, sell_trade: dict) -> dict:
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
        buy_trade: dict,
        sell_trade: dict,
        sell_rec_for_trade: dict,
        qty_to_close: float,
        amt_to_close: float,
    ) -> None:
        """
        Close the trade by updating the quantities and amounts for both buy and sell trades.

        Args:
            buy_trade (dict): The buy trade record.
            sell_trade (dict): The sell trade record.
            sell_rec_for_trade (dict): The sell record for the trade.
            qty_to_close (float): The quantity to close the trade.
            amt_to_close (float): The amount to close the trade.
        """
        sell_rec_for_trade["quantity"] = qty_to_close
        sell_rec_for_trade["amount"] = amt_to_close
        buy_trade["current_sold_qty"] += qty_to_close
        buy_trade["is_done"] = True
        sell_trade["is_done"] = True

        logging.debug(
            f"Closed trade: {buy_trade['trade_id']} with quantity: {qty_to_close} and amount: {amt_to_close}"
        )

    def _partially_close_trade(
        self,
        buy_trade: dict,
        sell_trade: dict,
        sell_rec_for_trade: dict,
        qty_to_close: float,
        amt_to_close: float,
    ) -> None:
        sell_rec_for_trade["quantity"] = qty_to_close
        sell_rec_for_trade["amount"] = amt_to_close
        buy_trade["current_sold_qty"] += qty_to_close
        sell_trade["Quantity"] -= qty_to_close
        sell_trade["Amount"] -= amt_to_close
        buy_trade["is_done"] = True
        sell_trade["is_done"] = False

    def _keep_trade_open(
        self, buy_trade: dict, sell_trade: dict, sell_rec_for_trade: dict
    ) -> None:
        sell_rec_for_trade["quantity"] = sell_trade["Quantity"]
        sell_rec_for_trade["amount"] = sell_trade["Amount"]
        buy_trade["current_sold_qty"] += sell_trade["Quantity"]
        buy_trade["is_done"] = False
        sell_trade["is_done"] = True

    def _calculate_profit_loss(
        self, buy_trade: dict, sell_trade: dict, sell_rec_for_trade: dict
    ) -> None:

        multiplier = 100 if buy_trade["is_option"] else 1

        price_difference = sell_trade["Price"] - buy_trade["price"]

        profit_loss = round(
            price_difference * sell_rec_for_trade["quantity"] * multiplier, 2
        )

        sell_rec_for_trade["percent_profit_loss"] = round(
            (price_difference / buy_trade["price"]) * 100, 2
        )

        sell_rec_for_trade["profit_loss"] = profit_loss

    def _add_sells_to_this_trade(self, buy_trade, sell_trades, symbol):

        bought_qty = buy_trade["quantity"]

        while sell_trades and (buy_trade["current_sold_qty"] < bought_qty):

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

            buy_trade["sells"].append(sell_rec_for_trade)

    def _create_current_buy_trade_record(self, buy_record):

        expiration_date_iso = (
            self._convert_to_iso_format(buy_record["Expiration Date"])
            if "Expiration Date" in buy_record and buy_record["Expiration Date"]
            else None
        )

        current_buy_trade = {
            "trade_id": buy_record["Id"],
            "symbol": buy_record["Symbol"],
            "trade_date_iso": self._convert_to_iso_format(buy_record["Trade Date"]),
            "trade_date": buy_record["Trade Date"],
            "trade_type": buy_record["Trade Type"],
            "trade_label": buy_record["Label"],
            "quantity": buy_record["Quantity"],
            "expiration_date_iso": expiration_date_iso,
            "price": buy_record["Price"],
            "target_price": buy_record["Target Price"],
            "amount": buy_record["Amount"],
            "account": buy_record.get("Account", None),
            "current_sold_qty": 0,
            "is_option": buy_record["is_option"],
            "is_done": False,
            "sells": [],
        }

        return current_buy_trade

    def _stock_option_summary_sanity_check(self, stock_summary, option_summary):

        symbol = self.stock_symbol

        for i, summary in enumerate([stock_summary, option_summary]):
            type = "stock" if i == 0 else "option"

            # adjusted_bought_quantity = summary["bought_quantity"] * multiplier
            # adjusted_sold_quantity = summary["sold_quantity"] * multiplier
            log_msg =  f'''
                [{symbol}] Total {type} buy quantity: {summary["bought_quantity"]}
                [{symbol}] Total {type} buy amount: {summary["bought_amount"]}
                '''
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

            log_msg =  f'''
                [{symbol}] Total {type} Bought Q: {summary["bought_quantity"]}
                [{symbol}] Total {type} Sold Q: {summary["sold_quantity"]}
                '''
            logging.info(log_msg)


    def _get_summary_dict(self):
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

    def _create_stock_and_option_summary(self, sorted_trades):

        stock_summary = self._get_summary_dict()
        option_summary = stock_summary.copy()
        option_summary["is_option"] = True

        # Separate buy and sell trades
        for trade in sorted_trades:

            if trade["Symbol"] != self.stock_symbol:
                raise ValueError(
                    f"Trade symbol {trade['Symbol']} does not match stock symbol {self.stock_symbol}"
                )

            # Check if the trade has a valid amount
            amount = trade.get("Amount")
            if isinstance(amount, str):
                # TODO Check for and remove these silly python "None"s
                logging.info(f"[{self.stock_symbol}] - Amount: <{amount}>")
                continue
            # Sum the Buy and 'Reinvest Shares'
            action = trade.get("Action")
            trade["is_option"] = True if trade["Trade Type"] in ("C", "P") else False

            summary = option_summary if trade["is_option"] else stock_summary

            if action in ("B", "RS", "BO"):
                summary["bought_quantity"] += trade.get("Quantity", 0)
                summary["bought_amount"] += trade.get("Amount", 0)
                summary["buy_trades"].append(trade)
            elif action in ("S", "SC"):
                summary["sold_quantity"] += trade.get("Quantity", 0)
                summary["sold_amount"] += trade.get("Amount", 0)
                summary["sell_trades"].append(trade)

        stock_summary["average_bought_price"] = ( self._get_average_bought_price(stock_summary, multiplier = 1))
        option_summary["average_bought_price"] = ( self._get_average_bought_price(option_summary, multiplier = 100))

        stock_summary["average_sold_price"] = ( self._get_average_sold_price(stock_summary, multiplier = 1))
        option_summary["average_sold_price"] = ( self._get_average_sold_price(option_summary, multiplier = 100))

        return stock_summary, option_summary

    def _add_buy_trade_to_summary(self, summary_dict, buy_trade, multiplier):
        "In place update of summary_dict"

        summary_dict["bought_amount"] += buy_trade["amount"]
        summary_dict["bought_quantity"] += buy_trade["quantity"]
        summary_dict["sold_quantity"] += buy_trade["current_sold_qty"]
        summary_dict["closed_bought_amount"] += (
            buy_trade["current_sold_qty"] * buy_trade["price"] * multiplier
        )
        summary_dict["sold_amount"] += sum(
            [sell["amount"] for sell in buy_trade["sells"]]
        )
        summary_dict["profit_loss"] += sum(
            [sell["profit_loss"] for sell in buy_trade["sells"]]
        )

    def analyze_trades(self) -> None:
        """_summary_
        Analyze trades and calculate profit/loss for each trade.
        Args:
            trade_transactions (list): Trade data from the database.
        Returns:
            None

        populates:
            self.profit_loss_data = {
                "stock": {
                    "summary": {},
                    "all_trades": [],
                },
                "option": {
                    "summary": {},
                    "all_trades": [],
                },
            }

        Raises:
            ValueError: If trade_transactions is not provided.
        Example:
            analyzer = TradingAnalyzer(trade_transactions)
            analyzer.analyze_trades()
        """

        symbol = self.stock_symbol
        logging.info(f"Working on symbol: {symbol}")

        sorted_trades = sorted(
            self.trade_transactions,
            key=lambda x: (x["Trade Date"], x["Trade Type"], x["Action"]),
        )

        stock_summary, option_summary = self._create_stock_and_option_summary(
            sorted_trades
        )

        self.profit_loss_data = profit_loss_data = {
            "stock": {
                "summary": stock_summary,
                "all_trades": [],
            },
            "option": {
                "summary": option_summary,
                "all_trades": [],
            },
        }

        self._stock_option_summary_sanity_check(stock_summary, option_summary)

        # Match sell trades with buy trades
        for i, trade_type_summary in enumerate([stock_summary, option_summary]):
            type = "stock" if i == 0 else "option"
            multiplier = 100 if type == "option" else 1
            running_bought_quantity = 0
            running_sold_quantity = 0
            running_sold_amount = 0
            sell_trades = trade_type_summary.pop("sell_trades")
            buy_trades = trade_type_summary.pop("buy_trades")

            while running_bought_quantity < trade_type_summary["bought_quantity"]:
                buy_record = buy_trades.pop(0)
                running_bought_quantity += buy_record["Quantity"]

                logging.debug(
                    f"[{symbol}] Running {type} bought qty: {running_bought_quantity}"
                )
                logging.debug(f"[{symbol}] Buy Trade: {buy_record}")

                current_buy_trade = self._create_current_buy_trade_record(buy_record)

                # The sold Quantity that can be matched with this buy record
                unmatched_sold_quantity = (
                    trade_type_summary["sold_quantity"] - running_sold_quantity
                )
                logging.info(f"[{symbol}] Sell {type} trade count: {len(sell_trades)}")
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
                    f"[{symbol}] Unmatched {type} sold quantity: {unmatched_sold_quantity}"
                )
                logging.debug(
                    f"[{symbol}] Current closed_{type} bought_quantity: {sold_quantity_this_trade}"
                )
                logging.debug(
                    f"[{symbol}] Running {type} sold quantity: {running_sold_quantity}"
                )

                # The 'bought' amount with matching sells
                # Note: All bought amounts are negative
                closed_bought_amount = (
                    -buy_record["Price"] * sold_quantity_this_trade * multiplier
                )

                running_sold_amount += closed_bought_amount

                if sold_quantity_this_trade > 0:
                    self._add_sells_to_this_trade(
                        current_buy_trade, sell_trades, symbol
                    )

                profit_loss_data[type]["all_trades"].append(current_buy_trade)

            trade_type_summary["closed_bought_quantity"] = running_sold_quantity
            trade_type_summary["closed_bought_amount"] = running_sold_amount

            # Calculate open shares for this symbol
            trade_type_summary["open_bought_quantity"] = round(
                trade_type_summary["bought_quantity"]
                - trade_type_summary["closed_bought_quantity"],
                2,
            )

            trade_type_summary["open_bought_amount"] = - round(
                abs(trade_type_summary["bought_amount"]) - abs(trade_type_summary["closed_bought_amount"]),
                2,
            )

            # Calculate Profit/Loss
            if abs(trade_type_summary["closed_bought_amount"]) != 0:
                trade_type_summary["profit_loss"] = trade_type_summary["sold_amount"] - abs(
                    trade_type_summary["closed_bought_amount"]
                )

            trade_type_summary["percent_profit_loss"] = self._get_percent_profit_loss(trade_type_summary)

            # Calculate Average Basis Sold Price
            if abs(trade_type_summary["sold_quantity"]) != 0:
                trade_type_summary["average_basis_sold_price"] = abs(
                    trade_type_summary["closed_bought_amount"]
                ) / (abs(trade_type_summary["sold_quantity"] * multiplier))

            # Calculate Average Basis Un-Sold Price
            if abs(trade_type_summary["open_bought_quantity"]) != 0:
                trade_type_summary["average_basis_open_price"] = abs(
                    trade_type_summary["open_bought_amount"]
                ) / (abs(trade_type_summary["open_bought_quantity"] * multiplier))

            self.profit_loss_data[type]["summary"] = trade_type_summary


    def get_results(self):
        # TODO: Replace this with 'get_profit_loss_data' method
        return self.profit_loss_data

    def get_profit_loss_data(self):
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

    # def get_symbols_with_open_trades(self):
    #     open_trade_symbols = []

    #     for symbol, trades in self.profit_loss_data.items():
    #         for buy_trade in trades["all_trades"]:
    #             if buy_trade["is_done"] == False:
    #                 open_trade_symbols.append(symbol)
    #                 break
    #     return open_trade_symbols
    # Calculate Average Sold Price

    def _filter_trades_by_status(self, trade_status="open", trade_transactions=None):
        """
        Get "open" or "closed" trades
        Args:
            trade_status (str): "open" or "closed"
            trade_transactions (list): Trade data from the database
        Uses self.profit_loss_data:
              {
                "stock": {
                    "summary": {},
                    "all_trades": [],
                },
                "option": {
                    "summary": {},
                    "all_trades": [],
                },
            }
        Returns:
            dict: A dictionary containing trade information
            {
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
        Raises:
            ValueError: If trade_status is not "open" or "closed"
        Example:
            analyzer = TradingAnalyzer(trade_transactions)
            open_trades = analyzer.get_open_trades(trade_status="open")
            closed_trades = analyzer.get_open_trades(trade_status="closed")
        """

        if trade_status not in ["open", "closed"]:
            raise ValueError("Invalid trade_status. Use 'open' or 'closed'.")

        logging.info(
            f'[filter_by_{trade_status}_trades] Getting all "{trade_status}" trades'
        )
        if trade_status == "open":
            is_correct_status = lambda x: x["is_done"] == False
        else:
            is_correct_status = lambda x: x["is_done"] == True

        symbol = self.stock_symbol

        # If we are using a new set of trade transactions
        if trade_transactions:
            self.trade_transactions = trade_transactions
            self.analyze_trades()

        logging.debug(f"[filter_by_{trade_status}_trades] Symbol: [{symbol}]")

        stock_summary = self._get_summary_dict()
        option_summary = stock_summary.copy()
        option_summary["is_option"] = True

        filtered_pl = {
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

        for i, type_info in enumerate(
            [self.profit_loss_data["stock"], self.profit_loss_data["option"]]
        ):
            type = "stock" if i == 0 else "option"
            multiplier = 100 if type == "option" else 1
            all_trades = type_info["all_trades"]

            for buy_trade in all_trades:

                if buy_trade["symbol"] != self.stock_symbol:
                    raise ValueError(
                        f"Trade symbol {buy_trade['symbol']} != {self.stock_symbol}"
                    )

                if is_correct_status(buy_trade):
                    self._add_buy_trade_to_summary( filtered_pl[type]["summary"], buy_trade, multiplier )
                    filtered_pl[type]["all_trades"].append(buy_trade)

            filtered_pl[type]["summary"]["average_bought_price"] = (
                self._get_average_bought_price(filtered_pl[type]["summary"], multiplier)
            )

            filtered_pl[type]["summary"]["open_bought_quantity"] = (
                filtered_pl[type]["summary"]["bought_quantity"]
                - filtered_pl[type]["summary"]["sold_quantity"]
            )

            filtered_pl[type]["summary"]["open_bought_amount"] = round(
                abs(filtered_pl[type]["summary"]["bought_amount"])
                - abs(filtered_pl[type]["summary"]["closed_bought_amount"]),
                2,
            )

            filtered_pl[type]["summary"]["percent_profit_loss"] = (
                self._get_percent_profit_loss(filtered_pl[type]["summary"])
            )

            # NEW - Calculate Average Basis Sold Price
            if abs(filtered_pl[type]["summary"]["sold_quantity"]) != 0:
                filtered_pl[type]["summary"]["average_basis_sold_price"] = abs(
                    filtered_pl[type]["summary"]["closed_bought_amount"]
                ) / (abs(filtered_pl[type]["summary"]["sold_quantity"] * multiplier))

            # Calculate Average Basis Un-Sold Price
            if abs(filtered_pl[type]["summary"]["open_bought_quantity"]) != 0:
                filtered_pl[type]["summary"]["average_basis_open_price"] = abs(
                    filtered_pl[type]["summary"]["open_bought_amount"]
                ) / (
                    abs(
                        filtered_pl[type]["summary"]["open_bought_quantity"]
                        * multiplier
                    )
                )

            filtered_pl[type]["summary"]["average_sold_price"] = (
                self._get_average_sold_price(filtered_pl[type]["summary"], multiplier)
            )

            logging.debug(
                f"[filter_by_{trade_status}_trades] Appending: [{symbol}] Trade Info: [{filtered_pl}]"
            )

        logging.debug(
            f"[filter_by_{trade_status}_trades] Returning: All {trade_status} Trades: [{filtered_pl}]"
        )
        return filtered_pl

    def get_open_trades(self, trade_transactions=None):
        return self._filter_trades_by_status("open", trade_transactions)

    def get_closed_trades(self, trade_transactions=None):
        return self._filter_trades_by_status("closed", trade_transactions)
