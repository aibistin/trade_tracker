from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Union

OPTIONS_MULTIPLIER = 100
STOCK_MULTIPLIER = 1


@dataclass
class Trade:
    trade_id: str
    symbol: str
    action: str
    trade_date: datetime
    trade_type: str
    trade_label: str
    quantity: float = 0.0
    price: float = 0.0
    amount: float = 0.0
    is_option: bool = False
    is_done: bool = False
    # Optional fields
    trade_date_iso: Optional[str] = None
    account: Optional[str] = None
    expiration_date_iso: Optional[str] = None
    target_price: Optional[float] = None
    reason: Optional[str] = None
    initial_stop_price: Optional[float] = None
    projected_sell_price: Optional[float] = None

    def __post_init__(self):
        """Populate trade_date_iso with ISO format of trade_date."""
        if self.trade_date and self.trade_date_iso is None:
            self.trade_date_iso = self._convert_to_iso_format(self.trade_date)

        if self.expiration_date_iso:
            self.expiration_date_iso = self._convert_to_iso_format(
                self.expiration_date_iso
            )

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
                    continue  # Try the next format if the current one fails

            # If none of the formats worked, raise an error
            raise ValueError(f"Invalid date string format: {dt_obj_or_str}")

        # If the input is neither a string nor a datetime object, raise an error
        raise TypeError("Input must be a string or a datetime object.")


@dataclass
class SellTrade(Trade):
    """Dataclass for Sell Trade, inheriting from Trade."""

    profit_loss: float = 0.0
    percent_profit_loss: float = 0.0

    def close_buy_and_sell_trade(
        self,
        buy_trade: "BuyTrade",
        sell_trade_unapplied: "SellTrade",
        qty_to_close: float,
        amt_to_close: float,
    ) -> None:
        """Close the trade by updating the quantities and amounts.
        Args:
            buy_trade (BuyTrade): The BuyTrade trade dataclass.
            sell_trade_unapplied (SellTrade): The SellTrade not applied to this BuyTrade.
            qty_to_close (float): The quantity to close the trade.
            amt_to_close (float): The amount to close the trade.
        """
        # print(
            # f"{self.symbol} - ID {self.trade_id} - Qty: {self.quantity} - Quantity to close: {qty_to_close}"
        # )
        # self.quantity = qty_to_close
        # self.amount = amt_to_close
        buy_trade.current_sold_qty += qty_to_close
        buy_trade.is_done = True
        sell_trade_unapplied.is_done = True
        self.calculate_profit_loss(buy_trade)

    def close_buy_trade_update_sell_trade(
        self,
        buy_trade: "BuyTrade",
        sell_trade_unapplied: "SellTrade",
        qty_to_close: float,
        amt_to_close: float,
    ) -> None:
        """This SellTrade closes the BuyTrade
        and has more to apply to the next BuyTrade.

        Args:
            buy_trade (BuyTrade): The BuyTrade trade dataclass.
            sell_trade_unapplied (SellTrade): The SellTrade not applied to this BuyTrade.
            qty_to_close (float): The quantity to close the trade.
            amt_to_close (float): The amount to close the trade.
        """
        self.quantity = qty_to_close
        self.amount = amt_to_close
        buy_trade.current_sold_qty += qty_to_close
        sell_trade_unapplied.quantity -= qty_to_close
        sell_trade_unapplied.amount -= amt_to_close
        buy_trade.is_done = True
        sell_trade_unapplied.is_done = False
        self.calculate_profit_loss(buy_trade)

    def update_buy_trade_close_sell_trade(
        self,
        buy_trade: "BuyTrade",
        sell_trade_unapplied: "SellTrade",
    ) -> None:
        """They BuyTrade is updated but not closed.

        Args:
            buy_trade (BuyTrade): The BuyTrade trade dataclass.
            sell_trade_unapplied (SellTrade): The SellTrade not applied to this BuyTrade.
        """
        self.quantity = sell_trade_unapplied.quantity
        self.amount = sell_trade_unapplied.amount
        buy_trade.current_sold_qty += sell_trade_unapplied.quantity
        buy_trade.is_done = False
        sell_trade_unapplied.is_done = True
        self.calculate_profit_loss(buy_trade)

    def calculate_profit_loss(self, buy_trade: Trade) -> None:
        """Calculate profit/loss."""
        multiplier = OPTIONS_MULTIPLIER if buy_trade.is_option else STOCK_MULTIPLIER
        price_difference = self.price - buy_trade.price

        self.profit_loss = round(
            float(price_difference * self.quantity) * multiplier,
            2,
        )

        self.percent_profit_loss = round(
            float(price_difference / buy_trade.price) * 100,
            2,
        )


@dataclass
class BuyTrade(Trade):
    """Dataclass for Buy Trade, inheriting from Trade."""

    current_sold_qty: float = 0.0
    sells: List[SellTrade] = field(default_factory=list)
