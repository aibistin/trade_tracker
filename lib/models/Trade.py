from __future__ import annotations
import copy
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, TypedDict
from lib.models.ActionMapping import ActionMapping

ACTION_MAP = ActionMapping()
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
        "account": "X",
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
        self.symbol = trade_data["symbol"]
        self.action = trade_data["action"]
        self.trade_date = trade_data["trade_date"]
        # The Database trade_transaction table uses "id"
        setattr(self, "trade_id", trade_data.get("trade_id", trade_data.get("id")))
        if not self.trade_id:
            raise KeyError("Trade ID is required")

        # Set optional attributes with defaults
        # TODO: Test that this works
        for field, default in self._DEFAULTS.items():
            setattr(self, field, trade_data.get(field, default))
        # The Database trade_transaction table uses "label"
        setattr(
            self,
            "trade_label",
            trade_data.get("trade_label", trade_data.get("label", "")),
        )

        self.expiration_date_iso = trade_data.get("expiration_date", None)

        self.is_option = self._determine_if_option()

        # Validation
        if ACTION_MAP.get_full_name(self.action) is None:
            raise ValueError(
                f"{self.symbol} ID: {self.trade_id} - Invalid action acronym: {self.action}"
            )

        if self.quantity <= 0:
            raise ValueError(
                f"Invalid quantity: {self.quantity} for trade {self.trade_id}"
            )

        # Handle date conversions
        if isinstance(self.trade_date, str):
            self.trade_date = self._convert_to_datetime(self.trade_date)

        self.trade_date_iso = self._convert_to_iso_format(self.trade_date)

        if self.expiration_date_iso:
            self.expiration_date_iso = self._convert_to_iso_format(
                self.expiration_date_iso
            )

        self._normalize_special_trade_types()

    def __repr__(self) -> str:
        """Human-readable representation showing all attributes with detailed list items"""
        attrs = []
        for key, value in self.__dict__.items():
            # Skip internal attributes
            if key.startswith("_"):
                continue

            # Format datetime objects
            if isinstance(value, datetime):
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            # Format lists with full details
            elif isinstance(value, list):
                # Handle empty lists
                if not value:
                    value = "[]"
                else:
                    # Format each item in the list
                    items = []
                    for i, item in enumerate(value):
                        # For Trade objects, show their full representation
                        if isinstance(item, Trade):
                            # Create a compact representation
                            trade_repr = (
                                f"\n{item.__class__.__name__}("
                                f"id={item.trade_id}, "
                                f"qty={item.quantity}, "
                                f"price={item.price}, "
                                f"trade_date={item.trade_date.strftime('%Y-%m-%d')}, "
                                f"account={item.account}, "
                            )
                            # Add profit/loss for SellTrades
                            if isinstance(item, SellTrade):
                                trade_repr += f", basis_price={item.basis_price}"
                                trade_repr += f", basis_amt={item.basis_amt}"
                                trade_repr += f", profit_loss={item.profit_loss}"
                            elif isinstance(item, BuyTrade):
                                trade_repr += (
                                    f", current_sold_amt={item.current_sold_amt}"
                                )
                                trade_repr += (
                                    f", current_profit_loss={item.current_profit_loss}"
                                )
                                trade_repr += f", current_percent_profit_loss={item.current_percent_profit_loss}"
                            trade_repr += ")\n"
                            items.append(trade_repr)
                        # For other objects, use their repr but limit length
                        else:
                            item_repr = repr(item)
                            if len(item_repr) > 50:
                                item_repr = item_repr[:47] + "..."
                            items.append(item_repr)

                        # Limit to 5 items for readability
                        if i >= 2 and len(value) > 5:
                            items.append(f"...+{len(value)-3} more")
                            break

                    value = "[" + ", ".join(items) + "]"

            attrs.append(f"{key}={value}")

        return f"{self.__class__.__name__}({', '.join(attrs)})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a JSON-serializable dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            # Skip private attributes
            if key.startswith("_"):
                continue

            # Convert datetimes to ISO strings
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif key == "sells" and isinstance(value, list):
                result[key] = [sell.to_dict() for sell in value]
            else:
                result[key] = value
        return result

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

    @staticmethod
    def _convert_to_datetime(trade_date_str: str) -> datetime:

        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                trade_date = datetime.strptime(trade_date_str, fmt)
                return trade_date
            except ValueError:
                continue

        raise ValueError(
            f"trade.trade_date_str format must be: '%Y-%m-%d' or '%Y-%m-%dT%H:%M:%S', got: {trade_date_str}"
        )

    @property
    def multiplier(self) -> int:
        """Return multiplier based on security type"""
        return OPTIONS_MULTIPLIER if self.is_option else STOCK_MULTIPLIER

    def _determine_if_option(self) -> bool:
        """Determine if this trade is for an option based on trade type or action"""
        if not hasattr(self, "trade_type"):
            raise AttributeError(
                f"Trade {self.trade_id} is missing trade_type attribute"
            )

        # Option if trade type is Call/Put or action is expiration/exercise
        return self.trade_type in ("C", "P") or self.action in ("EXP", "EE")

    def _normalize_special_trade_types(self):
        """Convert special trade types (EXP/EE) to standard sell trades"""
        if self.action == "EXP":
            self._convert_expired_option()
        elif self.action == "EE":
            self._convert_exercised_option()

    def _convert_expired_option(self):
        """Convert expired option to sell trade with zero value"""
        if not self.is_option:
            logging.warning(f"Trade {self.trade_id} marked as EXP but is not option")

        self.action = "SC"
        self.price = 0.0
        self.amount = 0.0
        self.reason = "Expired Option"
        logging.debug(f"Converted EXP trade {self.trade_id} to SC with price=0")

    def _convert_exercised_option(self):
        """Convert exercised option to sell trade with target price"""
        if not self.is_option:
            logging.warning(f"Trade {self.trade_id} marked as EE but is not option")

        if self.target_price is None:
            raise ValueError(f"Exercised option {self.trade_id} missing target_price")

        self.action = "SC"
        self.price = self.target_price
        self.amount = self.price * self.quantity * OPTIONS_MULTIPLIER
        self.reason = "Exercised Option"
        logging.debug(
            f"Converted EE trade {self.trade_id} to SC at {self.target_price}"
        )


class BuyTrade(Trade):
    """Class representing a buy trade with position management"""

    def __init__(self, trade_data: TradeData):
        super().__init__(trade_data)
        self.is_buy_trade: bool = True
        self.current_sold_qty: float = 0.0
        # TODO: Add to test_trade.py
        self.current_basis_sold_amt: float = 0.0
        self.current_sold_amt: float = 0.0
        self.current_profit_loss: float = 0.0
        self.current_percent_profit_loss: float = 0.0
        self.sells: List[SellTrade] = []

    def __repr__(self) -> str:
        """Enhanced representation for buy trades"""
        base_repr = super().__repr__()
        # buy-specific fields
        return base_repr.replace(
            ")\n",
            f", current_sold_qty={self.current_sold_qty}, current_sold_amt={self.current_sold_amt})\n"
            + f", current_basis_sold_amt={self.current_basis_sold_amt}\n"
            + f", current_current_profit_loss={self.current_profit_loss}, current_percent_profit_loss={self.current_percent_profit_loss})\n"
            + f", sells_count={len(self.sells)}"
            + f")\n",
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        return super().to_dict()

    def apply_sell_trade(self, sell_trade: "SellTrade") -> "SellTrade":
        """Apply a sell trade to this position and return applied portion"""
        applied_sell = copy.deepcopy(sell_trade)
        qty_to_close = self.quantity - self.current_sold_qty
        applied_qty = min(sell_trade.quantity, qty_to_close)
        logging.debug(
            f"[{self.symbol}] Apply sell {sell_trade.trade_id} to buy {self.trade_id} - applied_qty: {applied_qty}"
        )

        applied_sell.quantity = round(applied_qty, 4)
        applied_sell.amount = round(
            applied_qty * applied_sell.price * self.multiplier, 2
        )

        self.current_sold_qty += applied_qty
        sell_trade.quantity -= applied_qty
        sell_trade.amount -= applied_sell.amount
        # TODO test in test_trade.py
        self.current_sold_amt += applied_sell.amount
        self.current_basis_sold_amt += applied_qty * self.price * self.multiplier
        applied_sell.basis_price = self.price
        applied_sell.basis_amt = applied_qty * self.price * self.multiplier

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

        # applied_sell.calculate_profit_loss()
        price_diff = abs(applied_sell.price) - applied_sell.basis_price
        amount_diff = price_diff * applied_sell.quantity * applied_sell.multiplier
        applied_sell.profit_loss = round(amount_diff, 2)
        applied_sell.percent_profit_loss = (
            round((amount_diff / applied_sell.basis_amt) * 100, 2)
            if amount_diff != 0
            else 0
        )

        self.sells.append(applied_sell)  # This portion of sell is included with buy

        # TODO test in trade_test.py
        self.current_profit_loss += applied_sell.profit_loss
        self.current_percent_profit_loss = (
            self.current_profit_loss / self.current_basis_sold_amt
        ) * 100

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
        # TODO: Add basis price  and basis_amt to test_trade.py
        self.basis_price: float = 0.0
        self.basis_amt: float = 0.0
        self.profit_loss: float = 0.0
        self.percent_profit_loss: float = 0.0

    def __repr__(self) -> str:
        """Enhanced representation for sell trades"""
        base_repr = super().__repr__()
        # Add sell-specific fields
        return base_repr.replace(
            ")",
            f", basis_price={self.basis_price}, basis_amt={self.basis_amt}\n"
            + f", profit_loss={self.profit_loss}, percent_profit_loss={self.percent_profit_loss}\n"
            + f")\n",
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        return super().to_dict()

    def calculate_profit_loss(self) -> None:
        """Calculate profit/loss against a buy trade"""
        price_diff = abs(self.price) - self.basis_price
        amount_diff = price_diff * self.quantity * self.multiplier
        self.profit_loss = round(amount_diff, 2)
        self.percent_profit_loss = round((amount_diff / self.basis_amt) * 100, 2)
