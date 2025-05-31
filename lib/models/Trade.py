from __future__ import annotations
import copy
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, TypedDict

OPTIONS_MULTIPLIER = 100
STOCK_MULTIPLIER = 1


# Required fields
class RequiredTradeData(TypedDict):
    trade_id: str
    symbol: str
    action: str
    trade_date: datetime
    trade_type: str
    trade_label: str
    quantity: float
    price: float
    amount: float
    is_option: bool
    is_done: bool


# Optional fields with defaults
class OptionalTradeData(TypedDict, total=False):
    account: Optional[str]
    expiration_date: Optional[str]
    target_price: Optional[float]
    reason: Optional[str]
    initial_stop_price: Optional[float]
    projected_sell_price: Optional[float]
    # Optional fields to rename
    id: Optional[str]  # Can use "id" or "trade_id"
    label: Optional[str]  # Can use "label" or "trade_label"


# Combined type
class TradeData(RequiredTradeData, OptionalTradeData):
    pass


class Trade:
    """Base class for all trade types with type-safe initialization"""

    # Explicitly declare attributes for type checking
    trade_id: str
    symbol: str
    action: str
    trade_date: datetime
    trade_type: str
    trade_label: str
    quantity: float
    price: float
    amount: float
    is_option: bool
    is_done: bool
    trade_date_iso: Optional[str]
    account: Optional[str]
    expiration_date_iso: Optional[str]
    target_price: Optional[float]
    reason: Optional[str]
    initial_stop_price: Optional[float]
    projected_sell_price: Optional[float]
    # Optional fields to rename
    id: Optional[str]  # Can use "id" or "trade_id"
    label: Optional[str]  # Can use "label" or "trade_label"

    _DEFAULTS = {
        "trade_type": "",
        "account": "",
        "quantity": 0.0,
        "price": 0.0,
        "amount": 0.0,
        "is_option": False,
        "is_done": False,
        "expiration_date_iso": "",
        "target_price": None,
        "reason": None,
        "initial_stop_price": None,
        "projected_sell_price": None,
    }

    def __init__(self, trade_data: TradeData):
        """
        Initialize trade from dictionary with validation and defaults
        """

        # Set required attributes
        # The Database trade_transaction table uses "id" 
        setattr(self, "trade_id", trade_data.get("trade_id", trade_data.get("id")))
        if not self.trade_id:
            raise KeyError("Trade ID is required")
        self.symbol = trade_data["symbol"]
        self.action = trade_data["action"]
        self.trade_date = trade_data["trade_date"]

        # Set optional attributes with defaults
        for field, default in self._DEFAULTS.items():
            setattr(self, field, trade_data.get(field, default))
        # The Database trade_transaction table uses "label" 
        setattr(
            self,
            "trade_label",
            trade_data.get("trade_label", trade_data.get("label", "")),
        )

        self.expiration_date_iso = trade_data.get("expiration_date", None)

        # Handle date conversions
        self.trade_date_iso = self._convert_to_iso_format(self.trade_date)
        if self.expiration_date_iso:
            self.expiration_date_iso = self._convert_to_iso_format(
                self.expiration_date_iso
            )

        # Validation
        if self.quantity <= 0:
            raise ValueError(
                f"Invalid quantity: {self.quantity} for trade {self.trade_id}"
            )

    def __repr__(self) -> str:
        """Human-readable representation showing all attributes"""
        attrs = []
        for key, value in self.__dict__.items():
            # No internal attributes
            if key.startswith("_"):
                continue

            if isinstance(value, datetime):
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, list):
                value = f"[{len(value)} items]"

            attrs.append(f"{key}={value}")

        return f"{self.__class__.__name__}({', '.join(attrs)})"

    @staticmethod
    def _convert_to_iso_format(dt_obj: Any) -> Optional[str]:
        """Convert various date formats to ISO string"""
        if not dt_obj:
            return None
        if isinstance(dt_obj, datetime):
            return dt_obj.strftime("%Y-%m-%dT%H:%M:%S")
        if isinstance(dt_obj, str):
            # Handle different string formats
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(dt_obj, fmt).strftime("%Y-%m-%dT%H:%M:%S")
                except ValueError:
                    continue
        return str(dt_obj)  # Fallback to string representation

    @property
    def multiplier(self) -> int:
        """Return multiplier based on security type"""
        return OPTIONS_MULTIPLIER if self.is_option else STOCK_MULTIPLIER


# BuyTrade and SellTrade classes remain the same as before
class BuyTrade(Trade):
    """Class representing a buy trade with position management"""

    def __init__(self, trade_data: TradeData):
        super().__init__(trade_data)
        self.is_buy_trade: bool = True
        self.current_sold_qty: float = 0.0
        self.sells: List[SellTrade] = []

    def __repr__(self) -> str:
        """Enhanced representation for buy trades"""
        base_repr = super().__repr__()
        # buy-specific fields
        return base_repr.replace(
            ")",
            f", current_sold_qty={self.current_sold_qty}, sells_count={len(self.sells)})",
        )

    def apply_sell_trade(self, sell_trade: "SellTrade") -> "SellTrade":
        """Apply a sell trade to this position and return applied portion"""
        applied_sell = copy.deepcopy(sell_trade)
        qty_to_close = self.quantity - self.current_sold_qty
        applied_qty = min(sell_trade.quantity, qty_to_close)
        logging.debug(
            f"[{self.symbol}] Apply sell {sell_trade.trade_id} to buy {self.trade_id} - applied_qty: {applied_qty}"
        )

        applied_sell.quantity = applied_qty
        applied_sell.amount = round(
            applied_qty * applied_sell.price * self.multiplier, 2
        )

        self.current_sold_qty += applied_qty
        sell_trade.quantity -= applied_qty
        sell_trade.amount -= applied_sell.amount

        logging.debug(
            f"[{self.symbol}] Buy current_sold_qty: {self.current_sold_qty} buy original quantity: {self.quantity}"
        )
        # Update the position status
        self.is_done = self.current_sold_qty >= self.quantity
        logging.debug(f"[{self.symbol}] Sell trade_quantity: {sell_trade.quantity}")
        # Sell trade is removed if it's done
        sell_trade.is_done = sell_trade.quantity == 0
        # Applied sell will track the sell trades status.
        applied_sell.is_done = sell_trade.quantity == 0

        applied_sell.calculate_profit_loss(self)
        # This portion of sell trade will be included with the buy trade
        self.sells.append(applied_sell)

        logging.debug(
            f"[{self.symbol}] Applied {applied_qty} from sell {sell_trade.trade_id}"
        )
        return applied_sell

    def apply_sell_trades(self, sell_trades: List["SellTrade"]) -> None:
        """Apply multiple sell trades until position closed or sells exhausted"""
        while sell_trades and not self.is_done:
            sell_trade = sell_trades[0]
            self.apply_sell_trade(sell_trade)
            if sell_trade.is_done:
                sell_trades.pop(0)


class SellTrade(Trade):
    """Class representing a sell trade with P&L calculation"""

    def __init__(self, trade_data: TradeData):
        super().__init__(trade_data)
        self.profit_loss: float = 0.0
        self.percent_profit_loss: float = 0.0

    def __repr__(self) -> str:
        """Enhanced representation for sell trades"""
        base_repr = super().__repr__()
        # Add sell-specific fields
        return base_repr.replace(
            ")",
            f", profit_loss={self.profit_loss}, percent_profit_loss={self.percent_profit_loss})",
        )

    def calculate_profit_loss(self, buy_trade: BuyTrade) -> None:
        """Calculate profit/loss against a buy trade"""
        price_diff = self.price - buy_trade.price
        self.profit_loss = round(price_diff * self.quantity * self.multiplier, 2)
        self.percent_profit_loss = round((price_diff / buy_trade.price) * 100, 2)
