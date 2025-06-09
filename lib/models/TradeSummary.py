from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from datetime import datetime
import logging
from typing import List, Optional, Union
from lib.models.Trade import BuyTrade, SellTrade
from lib.models.Trades import BuyTrades

# TODO - Create test script for TradeSummary
OPTIONS_MULTIPLIER = 100
STOCK_MULTIPLIER = 1


@dataclass_json
@dataclass
class TradeSummary:
    """A dataclass for storing totals for all trades for a given stock symbol."""

    symbol: str
    is_option: bool
    bought_quantity: float = 0.0
    bought_amount: float = 0.0
    sold_quantity: float = 0.0
    sold_amount: float = 0.0
    closed_bought_quantity: float = 0.0
    closed_bought_amount: float = 0.0
    open_bought_quantity: float = 0.0
    open_bought_amount: float = 0.0
    profit_loss: float = 0.0
    percent_profit_loss: float = 0.0
    average_bought_price: float = 0.0
    average_sold_price: float = 0.0  # Added missing field
    average_basis_open_price: float = 0.0
    average_basis_sold_price: float = 0.0
    buy_trades: List[BuyTrade] = field(default_factory=list)
    sell_trades: List[SellTrade] = field(default_factory=list)
    multiplier: int = 1
    after_date: Optional[str] = None

    def __post_init__(self):
        """
        Create a multiplier based on the type of trade.
        Populate after_date with ISO format of after_date.
        """
        self.multiplier = (
            OPTIONS_MULTIPLIER if self.is_option == True else STOCK_MULTIPLIER
        )

        if self.after_date:
            self.after_date = self._convert_to_iso_format(self.after_date)

    @classmethod
    def create_from_buy_trades_collection(
        cls,
        symbol: str,
        buy_trades_collection: BuyTrades,
        after_date: Optional[str] = None,
    ) -> "TradeSummary":
        """Factory method to create TradeSummary from a BuyTrades collection.

        Args:
            symbol: Stock symbol
            buy_trades_collection: BuyTrades collection object
            after_date: Optional date filter in ISO format

        Returns:
            TradeSummary: Populated summary object
        """
        if buy_trades_collection.security_type not in ("stock", "option"):
            raise ValueError(
                f"Invalid security_type: {buy_trades_collection.security_type}"
            )

        is_option = buy_trades_collection.security_type == "option"
        trade_summary = cls(symbol=symbol, is_option=is_option, after_date=after_date)

        for trade in buy_trades_collection.buy_trades:
            # Validate trade matches summary
            if trade.symbol != symbol:
                raise ValueError(
                    f"Trade symbol {trade.symbol} != summary symbol {symbol}"
                )

            if trade.is_option != is_option:
                raise ValueError(
                    f"Trade {trade.trade_id}, is_option={trade.is_option} but Collection security_type={buy_trades_collection.security_type}"
                )

            # Process buy trade
            trade_summary.bought_quantity += trade.quantity
            trade_summary.bought_amount += trade.amount
            trade_summary.buy_trades.append(trade)

            # Process associated sell trades
            for sell in trade.sells:
                # Validate sell date occurs after buy date
                if sell.trade_date < trade.trade_date:
                    raise ValueError(
                        f"Sell date {sell.trade_date} before buy date {trade.trade_date}"
                    )

                trade_summary.sold_quantity += sell.quantity
                trade_summary.sold_amount += sell.amount
                trade_summary.sell_trades.append(sell)

        # Calculate averages
        trade_summary.get_average_bought_price()
        trade_summary.get_average_sold_price()

        return trade_summary

    def get_average_bought_price(self) -> float:
        """Calculate the average bought price."""
        if self.bought_quantity == 0:
            return 0.0
        self.average_bought_price = round(
            float(self.bought_amount / (self.bought_quantity * self.multiplier)),
            3,
        )
        return self.average_bought_price

    def get_average_sold_price(self) -> float:
        """Calculate the average sold price."""
        if self.sold_quantity == 0:
            return 0.0
        self.average_sold_price = round(
            float(self.sold_amount / (self.sold_quantity * self.multiplier)), 3
        )
        return self.average_sold_price

    def get_open_bought_quantity(self) -> float:
        self.open_bought_quantity = round(
            float(self.bought_quantity - self.closed_bought_quantity),
            2,
        )
        return self.open_bought_quantity

    def get_open_bought_amount(self) -> float:
        self.open_bought_amount = -round(
            float(abs(self.bought_amount) - abs(self.closed_bought_amount)),
            2,
        )
        return self.open_bought_amount

    def get_average_basis_sold_price(self) -> float:
        """Calculate the average basis sold price."""
        if self.sold_quantity != 0:
            self.average_basis_sold_price = float(
                abs(self.closed_bought_amount) / (self.sold_quantity * self.multiplier)
            )
        return self.average_basis_sold_price

    def get_average_basis_open_price(self) -> float:
        """Calculate Average Basis Un-Sold Price"""
        if self.open_bought_quantity != 0:
            self.average_basis_open_price = float(
                abs(self.open_bought_amount)
                / (self.open_bought_quantity * self.multiplier)
            )
        return self.average_basis_open_price

    def get_profit_loss(self) -> float:
        if abs(self.closed_bought_amount) != 0:
            self.profit_loss = float(self.sold_amount - abs(self.closed_bought_amount))
        return self.profit_loss

    def get_percent_profit_loss(self) -> float:
        if self.closed_bought_amount != 0 and self.profit_loss != 0:
            self.percent_profit_loss = round(
                (self.profit_loss / abs(self.closed_bought_amount)) * 100, 2
            )
        return self.percent_profit_loss

    def calculate_final_totals(
        self,
        final_sold_quantity: float,
        final_sold_amount: float,
    ) -> None:
        """Calculate summary metrics."""

        self.closed_bought_quantity = round(final_sold_quantity, 2)
        self.closed_bought_amount = round(final_sold_amount, 2)

        self.get_open_bought_quantity()
        self.get_open_bought_amount()
        self.get_profit_loss()
        self.get_percent_profit_loss()
        # Calculate Average Basis Sold Price
        self.get_average_basis_sold_price()
        # Calculate Average Basis Un-Sold Price
        self.get_average_basis_open_price()

    def _convert_to_iso_format(self, dt_obj_or_str: Union[datetime, str]) -> str:
        if isinstance(dt_obj_or_str, datetime):
            # If it's already a datetime object, format it directly
            return dt_obj_or_str.strftime("%Y-%m-%dT%H:%M:%S")

        if isinstance(dt_obj_or_str, str):
            # Try to parse the string in the expected formats
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    date_obj = datetime.strptime(dt_obj_or_str, fmt)
                    return date_obj.strftime("%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    continue

            raise ValueError(
                f"Invalid date string format for 'after_date': {dt_obj_or_str}"
            )

        raise TypeError("Input must be a string or a datetime object.")

    def process_all_trades(self, symbol: str) -> List[BuyTrade]:
        """
        Compute final totals for a given symbol.

        This method takes a symbol and a list of BuyTrade objects, and computes
        the final totals for that symbol. It adds the totals to the summary,
        and returns the list of BuyTrade objects.

        Args:
            symbol (str): The symbol to compute the final totals for.

        Returns:
            List[BuyTrade]: The list of BuyTrade objects with the final totals.
        """

        security_type = "option" if self.is_option else "stock"
        logging.info(f"[{symbol}] Adding final totals to {security_type} summary")

        multiplier = (
            OPTIONS_MULTIPLIER if security_type == "option" else STOCK_MULTIPLIER
        )
        running_bought_quantity = 0
        running_sold_quantity = 0
        running_sold_amount = 0

        sell_trades = self.sell_trades[:]
        buy_trades = self.buy_trades[:]
        all_trades = []

        if not buy_trades:
            logging.info(f"[{symbol}] {security_type} has no buy trades")
            if self.bought_quantity > 0:
                missing = self.bought_quantity - running_bought_quantity
                raise Exception(
                    f"[{symbol}] Is missing {missing} {security_type} buy trades"
                )

        for current_buy_record in buy_trades:

            running_bought_quantity += current_buy_record.quantity

            logging.debug(
                f"[{symbol}] Buy Trade: {current_buy_record.trade_id}"
                + f"[{symbol}] Running {security_type} bought qty: {running_bought_quantity}"
            )

            # The sold Quantity that can be matched with this buy record
            unmatched_sold_quantity = self.sold_quantity - running_sold_quantity
            logging.info(
                f"[{symbol}] Sell {security_type} trade count: {len(sell_trades)}"
            )
            sold_quantity_this_trade = 0

            if current_buy_record.quantity <= unmatched_sold_quantity:
                # This Buy record has matching sells
                sold_quantity_this_trade = current_buy_record.quantity
            else:
                # Buy record will have some open trades after this
                sold_quantity_this_trade = unmatched_sold_quantity

            running_sold_quantity += sold_quantity_this_trade

            logging.debug(
                f"[{symbol}] Unmatched {security_type} sold quantity: {unmatched_sold_quantity}"
                + f"[{symbol}] Current closed_{security_type} bought_quantity: {sold_quantity_this_trade}"
                + f"[{symbol}] Running {security_type} sold quantity: {running_sold_quantity}"
            )

            # The 'bought' amount for these matching sells. Bought amount is negative.
            running_sold_amount += (
                -current_buy_record.price * sold_quantity_this_trade * multiplier
            )
            all_trades.append(current_buy_record)

        self.calculate_final_totals(running_sold_quantity, running_sold_amount)

        return all_trades

    def security_summary_sanity_check(self, symbol: str) -> None:

        if self.symbol != symbol:
            raise ValueError(f"Trade symbol {self.symbol} != summary symbol {symbol}")

        security_type = "option" if self.is_option else "stock"

        log_msg = f"""
            Sanity check for {security_type} trades for {symbol}
            [{symbol}] Total {security_type} buy quantity: {self.bought_quantity}
            [{symbol}] Total {security_type} buy amount: {self.bought_amount}
                """
        logging.info(log_msg)

        # Validate that we are not selling more than we bought
        if self.sold_quantity > self.bought_quantity:
            logging.warning(
                f"[{symbol}] Total {security_type} quantity sold ({self.sold_quantity}) exceeds total {security_type} quantity bought ({self.bought_quantity})"
            )

        if self.bought_quantity > self.sold_quantity:
            logging.info(f"[{symbol}] has some open {security_type} trades")
        else:
            logging.info(f"[{symbol}] All {security_type} trades have been closed")

        log_msg = f"""
            [{symbol}] Total {security_type} Bought Q: {self.bought_quantity}
            [{symbol}] Total {security_type} Sold Q: {self.sold_quantity}
            """
        logging.info(log_msg)
