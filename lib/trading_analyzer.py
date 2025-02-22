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

    def __init__(self, data_dict):
        self.data_dict = data_dict
        self.results = {}

    # buy_trade = {
    #     'trade_id': buy_record['Id'],
    #     'trade_date': buy_record['Trade Date'],
    #     'quantity': 0,
    #     'price':  buy_record['Price'],
    #     'amount': 0,
    #     'current_sold_qty': 0,
    #     'sells': []
    # }

    def _sell_adder(self, buy_trade: dict, sell_trade: dict, symbol: str) -> dict:
        bought_qty = buy_trade["quantity"]
        sell_rec_for_trade = self._initialize_sell_record(sell_trade)

        logging.debug(f"[{symbol}] Current trade bought_quantity: {bought_qty}")
        logging.debug(f"[{symbol}] Sell record quantity: {sell_trade['Quantity']}")

        qty_to_close_the_trade = bought_qty - buy_trade["current_sold_qty"]
        amt_to_close_the_trade = sell_trade["Price"] * qty_to_close_the_trade

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

    def _convert_to_iso_format(self, date_obj: datetime) -> str:
        # date_obj = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
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
        price_difference = sell_trade["Price"] - buy_trade["price"]
        profit_loss = round(price_difference * sell_rec_for_trade["quantity"], 2)
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

    def analyze_trades(self) -> None:
        for symbol, trades in self.data_dict.items():
            sorted_trades = sorted(trades, key=lambda x: (x["Trade Date"], x["Action"]))
            buy_trades = []
            sell_trades = []
            total_bought_quantity = 0.0
            total_bought_amount = 0.0
            # Accumulate sold quantity
            total_sold_quantity = 0.0
            total_sold_amount = 0.0

            logging.info(f"Working on symbol: {symbol}")
            # Separate buy and sell trades
            for trade in sorted_trades:
                amount = trade.get("Amount")
                if isinstance(amount, str):
                    # TODO Remove these silly "None"s
                    logging.info(f"[{symbol}] - Amount: <{amount}>")
                    continue
                # Sum the Buy and 'Reinvest Shares'
                action = trade.get("Action")
                if action in ("B", "RS"):
                    buy_trades.append(trade)
                    total_bought_quantity += trade.get("Quantity", 0)
                    total_bought_amount += trade.get("Amount", 0)
                elif action == "S":
                    sell_trades.append(trade)
                    total_sold_quantity += trade.get("Quantity", 0)
                    total_sold_amount += trade.get("Amount", 0)

            logging.info(f"[{symbol}] Total buy trades: {len(buy_trades)}")
            logging.info(f"[{symbol}] Total sell trades: {len(sell_trades)}")
            # Initialize results for the current trade symbol
            self.results[symbol] = {"summary": {}, "all_trades": []}

            self.results[symbol]["summary"] = {
                "bought_quantity": round(total_bought_quantity, 2),
                "bought_amount": round(total_bought_amount, 2),
                "average_bought_price": round(
                    total_bought_amount / total_bought_quantity, 2
                ),
                "sold_quantity": round(total_sold_quantity, 2),
                "sold_amount": round(total_sold_amount, 2),
                "average_basis_sold_price": 0,
                "average_basis_open_price": 0,
                "average_sold_price": (
                    round(total_sold_amount / total_sold_quantity, 2)
                    if (total_sold_quantity > 0)
                    else 0
                ),
                "closed_bought_quantity": 0,
                "closed_bought_amount": 0,
                "open_bought_quantity": 0,
                "open_bought_amount": 0,
                "profit_loss": 0,
                "percent_profit_loss": 0,
            }

            # Validate that we are not selling more than we bought
            if total_sold_quantity > total_bought_quantity:
                warnings.warn(
                    f"[{symbol}] Total quantity sold ({total_sold_quantity}) exceeds total quantity bought ({total_bought_quantity})"
                )

            if total_bought_quantity > total_sold_quantity:
                logging.info(f"[{symbol}] has some open trades")
            else:
                logging.info(f"[{symbol}] All trades have been closed")

            logging.info(f"[{symbol}] Total Bought Q: {total_bought_quantity}")
            logging.info(f"[{symbol}] Total Sold Q: {total_sold_quantity}")

            # Accumulate matching bought quantity for this symbol
            running_bought_quantity = 0
            running_sold_quantity = 0
            running_sold_amount = 0

            # Match sell trades with buy trades
            while running_bought_quantity < total_bought_quantity:
                current_buy_trade = {}
                buy_record = buy_trades.pop(0)
                running_bought_quantity += buy_record["Quantity"]

                logging.debug(
                    f"[{symbol}] Running bought qty: {running_bought_quantity}"
                )
                logging.debug(f"[{symbol}] Buy Trade: {buy_record}")

                current_buy_trade = {
                    "trade_id": buy_record["Id"],
                    "trade_date_iso": self._convert_to_iso_format(
                        buy_record["Trade Date"]
                    ),
                    "trade_date": buy_record["Trade Date"],
                    "quantity": buy_record["Quantity"],
                    "price": buy_record["Price"],
                    "amount": buy_record["Amount"],
                    "account": buy_record.get("Account", None),
                    "current_sold_qty": 0,
                    "is_done": False,
                    "sells": [],
                }

                unmatched_sold_quantity = total_sold_quantity - running_sold_quantity
                logging.info(f"[{symbol}] Sell trade count: {len(sell_trades)}")

                sold_quantity_this_trade = 0
                closed_bought_amount = 0

                if buy_record["Quantity"] <= unmatched_sold_quantity:
                    # This Buy record has matching sells
                    sold_quantity_this_trade = buy_record["Quantity"]
                    running_sold_quantity += sold_quantity_this_trade
                else:
                    # Buy record will have open trades
                    sold_quantity_this_trade = unmatched_sold_quantity
                    running_sold_quantity += sold_quantity_this_trade

                logging.debug(
                    f"[{symbol}] Unmatched sold quantity: {unmatched_sold_quantity}"
                )
                logging.debug(
                    f"[{symbol}] Current closed_bought_quantity: {sold_quantity_this_trade}"
                )
                logging.debug(
                    f"[{symbol}] Running sold quantity: {running_sold_quantity}"
                )

                # All bought amounts are negative
                closed_bought_amount = -buy_record["Price"] * sold_quantity_this_trade
                running_sold_amount += closed_bought_amount
                if sold_quantity_this_trade > 0:
                    self._add_sells_to_this_trade(
                        current_buy_trade, sell_trades, symbol
                    )

                self.results[symbol]["all_trades"].append(current_buy_trade)

            self.results[symbol]["summary"][
                "closed_bought_quantity"
            ] = running_sold_quantity
            self.results[symbol]["summary"][
                "closed_bought_amount"
            ] = running_sold_amount

            # Calculate open shares for this symbol
            self.results[symbol]["summary"]["open_bought_quantity"] = round(
                self.results[symbol]["summary"]["bought_quantity"]
                - self.results[symbol]["summary"]["closed_bought_quantity"],
                2,
            )
            self.results[symbol]["summary"]["open_bought_amount"] = round(
                abs(self.results[symbol]["summary"]["bought_amount"])
                - abs(self.results[symbol]["summary"]["closed_bought_amount"]),
                2,
            )

            # # Calculate Profit/Loss
            if abs(self.results[symbol]["summary"]["closed_bought_amount"]) > 0:
                self.results[symbol]["summary"]["profit_loss"] = self.results[symbol][
                    "summary"
                ]["sold_amount"] - abs(
                    self.results[symbol]["summary"]["closed_bought_amount"]
                )
                self.results[symbol]["summary"]["percent_profit_loss"] = (
                    self.results[symbol]["summary"]["profit_loss"]
                    / abs(self.results[symbol]["summary"]["closed_bought_amount"])
                ) * 100

            # Calculate Average Basis Sold Price
            if abs(self.results[symbol]["summary"]["sold_quantity"]) > 0:
                self.results[symbol]["summary"]["average_basis_sold_price"] = abs(
                    self.results[symbol]["summary"]["closed_bought_amount"]
                ) / abs(self.results[symbol]["summary"]["sold_quantity"])

            # Calculate Average Basis Un-Sold Price
            if abs(self.results[symbol]["summary"]["open_bought_quantity"]) > 0:
                self.results[symbol]["summary"]["average_basis_open_price"] = abs(
                    self.results[symbol]["summary"]["open_bought_amount"]
                ) / abs(self.results[symbol]["summary"]["open_bought_quantity"])

    def get_results(self):
        return self.results

    def get_open_trades(self):
        trade_info = {}

        for symbol, trades in self.results.items():
            logging.debug(f"[analyze_trades] Symbol: [{symbol}] Trades: [{trades}]")

            if symbol not in trade_info:

                trade_info[symbol] = {"summary": {}, "all_trades": []}
                trade_info[symbol]["summary"] = {
                    "symbol": symbol,
                    "bought_quantity": 0,
                    "bought_amount": 0,
                    "sold_quantity": 0,
                    "sold_amount": 0,
                    "closed_bought_quantity": 0,
                    "closed_bought_amount": 0,
                    "open_bought_quantity": 0,
                    "open_bought_amount": 0,
                    "profit_loss": 0,
                    "percent_profit_loss": 0,
                    "average_bought_price": 0,
                    "average_basis_sold_price": 0,
                    "average_basis_open_price": 0,
                    "average_sold_price": 0,
                }

            for buy_trade in trades["all_trades"]:
                if buy_trade["is_done"] == False:
                    trade_info[symbol]["summary"]["bought_amount"] += buy_trade[
                        "amount"
                    ]
                    trade_info[symbol]["summary"]["bought_quantity"] += buy_trade[
                        "quantity"
                    ]
                    # trade_info[symbol]["summary"]["open_bought_quantity"] += buy_trade[
                    # "quantity"
                    # ]
                    trade_info[symbol]["summary"]["sold_quantity"] += buy_trade[
                        "current_sold_qty"
                    ]

                    trade_info[symbol]["summary"]["closed_bought_amount"] += (
                        buy_trade["current_sold_qty"] * buy_trade["price"]
                    )

                    trade_info[symbol]["summary"]["sold_amount"] += sum(
                        [sell["amount"] for sell in buy_trade["sells"]]
                    )

                    trade_info[symbol]["summary"]["profit_loss"] += sum(
                        [sell["profit_loss"] for sell in buy_trade["sells"]]
                    )
                    trade_info[symbol]["all_trades"].append(buy_trade)

            if trade_info[symbol]["summary"]["bought_quantity"] != 0:
                trade_info[symbol]["summary"]["average_bought_price"] = (
                    trade_info[symbol]["summary"]["bought_amount"]
                    / trade_info[symbol]["summary"]["bought_quantity"]
                )

            trade_info[symbol]["summary"]["open_bought_quantity"] = (
                trade_info[symbol]["summary"]["bought_quantity"]
                - trade_info[symbol]["summary"]["sold_quantity"]
            )

            trade_info[symbol]["summary"]["open_bought_amount"] = round(
                abs(trade_info[symbol]["summary"]["bought_amount"])
                - abs(trade_info[symbol]["summary"]["closed_bought_amount"]),
                2,
            )

            if trade_info[symbol]["summary"]["closed_bought_amount"] != 0:
                trade_info[symbol]["summary"]["percent_profit_loss"] = round(
                    (
                        trade_info[symbol]["summary"]["profit_loss"]
                        / trade_info[symbol]["summary"]["closed_bought_amount"]
                    )
                    * 100,
                    2,
                )
            else:
                trade_info[symbol]["summary"]["percent_profit_loss"] = 0

            # NEW - Calculate Average Basis Sold Price
            if abs(trade_info[symbol]["summary"]["sold_quantity"]) > 0:
                trade_info[symbol]["summary"]["average_basis_sold_price"] = abs(
                    trade_info[symbol]["summary"]["closed_bought_amount"]
                ) / abs(trade_info[symbol]["summary"]["sold_quantity"])

            # Calculate Average Basis Un-Sold Price
            if abs(trade_info[symbol]["summary"]["open_bought_quantity"]) > 0:
                trade_info[symbol]["summary"]["average_basis_open_price"] = abs(
                    trade_info[symbol]["summary"]["open_bought_amount"]
                ) / abs(trade_info[symbol]["summary"]["open_bought_quantity"])

            # Calculate Average Sold Price
            if trade_info[symbol]["summary"]["sold_quantity"] > 0:
                trade_info[symbol]["summary"]["average_sold_price"] = round(
                    trade_info[symbol]["summary"]["sold_amount"]
                    / trade_info[symbol]["summary"]["sold_quantity"],
                    2,
                )

            logging.debug(
                f"[analyze_trades] Appending : [{symbol}] Trade Info: [{trade_info[symbol]}]"
            )

        logging.debug(f"[analyze_trades] Returning: All Open Trades: [{trade_info}]")
        return trade_info
