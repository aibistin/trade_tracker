from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, MutableSequence
from lib.models.Trade import Trade, BuyTrade, SellTrade

# Type variable for covariant trade types
TradeType = TypeVar("TradeType", bound=Trade)

@dataclass
class TradeCollection:
    """Base class for trade collections with serialization support"""

    security_type: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            # Skip private attributes
            if key.startswith('_'):
                continue

            # Handle datetime objects
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, list) and value and isinstance(value[0], Trade):
                result[key] = [item.to_dict() for item in value]
            # Handle other objects with to_dict method
            elif hasattr(value, 'to_dict'):
                result[key] = value.to_dict() # type: ignore
            else:
                result[key] = value
        return result


@dataclass
class Trades(TradeCollection):
    """Container for mixed trade types (both buy and sell)"""

    trades: List[Trade] = field(default_factory=list)
    buy_trades: List[BuyTrade] = field(default_factory=list)
    sell_trades: List[SellTrade] = field(default_factory=list)

    def _sort_trades(self, trades: MutableSequence[TradeType]) -> None:
        """Sort trades by trade date, type, and action in-place."""
        trades.sort(
            key=lambda x: (
                x.trade_date,
                x.action,
                x.account,
                x.is_option,
                x.trade_type,
            )
        )

    def sort_trades(self) -> None:
        """Sort all trades by trade date, type, and action."""
        self._sort_trades(self.trades)
        self._sort_trades(self.buy_trades)
        self._sort_trades(self.sell_trades)

    def add_trade(self, trade: Trade) -> None:
        """Add a trade to the appropriate collections"""
        if not isinstance(trade, Trade):
            raise TypeError("trade must be an instance of Trade")

        self.trades.append(trade)

        if isinstance(trade, BuyTrade):
            self.buy_trades.append(trade)
        elif isinstance(trade, SellTrade):
            self.sell_trades.append(trade)


@dataclass
class BuyTrades(TradeCollection):
    """Container specifically for buy trades with date filtering"""

    buy_trades: List[BuyTrade] = field(default_factory=list)
    after_date_str: Optional[str] = None
    after_date: Optional[datetime] = field(default=None, init=False)

    def __post_init__(self):
        """Parse after_date_str into datetime"""
        if self.after_date_str:
            try:
                self.after_date = datetime.strptime(self.after_date_str, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"after_date must be in 'yyyy-mm-dd' format, got: {self.after_date_str}"
                )

    def add_trade(self, trade: BuyTrade) -> Optional[BuyTrade]:
        """Add buy trade if it meets date criteria"""
        if not isinstance(trade, BuyTrade):
            raise TypeError(f"trade must be an instance of BuyTrade: {type(trade)}")

        if self.after_date and trade.trade_date < self.after_date:
            return None

        self.buy_trades.append(trade)
        return trade

    def filter_buy_trades(self) -> None:
        """Filter buy trades to only those on or after after_date"""
        if self.after_date:
            self.buy_trades = [
                trade
                for trade in self.buy_trades
                if trade.trade_date >= self.after_date
            ]
