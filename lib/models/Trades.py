from __future__ import annotations
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, MutableSequence
from lib.models.Trade import Trade, BuyTrade, SellTrade


# Type variable for covariant trade types
TradeType = TypeVar("TradeType", bound=Trade)




# Type variable for covariant trade types
TradeType = TypeVar("TradeType", bound=Trade)


@dataclass
class TradeCollection:
    """Base class for trade collections with serialization support"""

    security_type: str
    buy_trades: List[BuyTrade] = field(default_factory=list)
    sells_by_account: Dict[str, List[SellTrade]] = field(default_factory=dict)  # type: ignore

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            # Skip private attributes
            if key.startswith("_"):
                continue

            # Handle datetime objects
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, list) and value and isinstance(value[0], Trade):
                result[key] = [item.to_dict() for item in value]
            # convert sells_by_account
            elif key == "sells_by_account":
                result[key] = {
                    k: [t.to_dict() for t in v]
                    for k, v in self.sells_by_account.items()
                }

            # Handle other objects with to_dict method
            elif hasattr(value, "to_dict"):
                result[key] = value.to_dict()  # type: ignore
            else:
                result[key] = value
        return result

    def add_trade(self, trade: Trade) -> None:
        """Add a trade to the appropriate collections"""
        if not isinstance(trade, Trade):
            raise TypeError(f"'trade' ID {trade.trade_id} must be an instance of Trade")
        if not trade.account:
            raise ValueError(f"'trade' ID {trade.trade_id} must be an 'account'")

        if isinstance(trade, BuyTrade):
            self.buy_trades.append(trade)
        elif isinstance(trade, SellTrade):
            if not trade.account in self.sells_by_account:
                self.sells_by_account[trade.account] = []  # type: ignore
            self.sells_by_account[trade.account].append(trade)  # type: ignore


@dataclass
class Trades(TradeCollection):
    """Container for mixed trade types (both buy and sell)"""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        return super().to_dict()

    def _sort_trades(self, trades: MutableSequence[TradeType]) -> None:
        """Sort trades by trade date, type, and action in-place."""
        trades.sort(
            key=lambda x: (
                x.account,
                x.trade_date,
                x.action,
                x.is_option,
                x.trade_type,
            )
        )

    def sort_trades(self) -> None:
        """Sort all trades by trade date, type, and action."""
        self._sort_trades(self.buy_trades)
        for account in self.sells_by_account:
            logging.debug(
                f"Sorting {len(self.sells_by_account[account])} trades for account: {account}"
            )
            self._sort_trades(self.sells_by_account[account])


@dataclass
class BuyTrades(TradeCollection):
    """Container for buy trades with filtering capabilities"""

    status: str = field(default="all")  # 'all', 'open', or 'closed'
    account: Optional[str] = None  # New: account filter
    after_date_str: Optional[str] = None
    after_date: Optional[datetime] = field(default=None, init=False)
    sells_by_account: Dict[str, List[SellTrade]] = field(default_factory=dict)  # type: ignore

    


    def __post_init__(self):
        """Parse after_date_str into datetime and validate status"""
        if self.after_date_str:
            try:
                self.after_date = datetime.strptime(self.after_date_str, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"after_date must be in 'yyyy-mm-dd' format, got: {self.after_date_str}"
                )

        # Validate status
        self.status = self.status.lower() if self.status else "all"
        if self.status not in {"all", "open", "closed"}:
            raise ValueError("Status must be one of 'all', 'open', or 'closed'")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary"""
        return super().to_dict()

    def add_trade(self, trade: BuyTrade) -> Optional[BuyTrade]:
        """Add buy trade without filtering (filtering happens later)"""
        if not isinstance(trade, BuyTrade):
            raise TypeError(f"trade must be an instance of BuyTrade: {type(trade)}")
        if not trade.account:
            raise ValueError(f"'trade' ID {trade.trade_id} must have an 'account'")

        self.buy_trades.append(trade)
        return trade

    def filter_buy_trades(self) -> None:
        """Apply all filters in a single pass for efficiency"""
        if not self.buy_trades:
            return

        # Single-pass filtering
        filtered = []
        for trade in self.buy_trades:

            # Account filter - skip if account doesn't match
            if self.account and trade.account != self.account:
                continue

            # Date filter
            if self.after_date and trade.trade_date < self.after_date:
                continue

            # Status filter
            if self.status == "open" and trade.is_done:
                continue
            if self.status == "closed" and not trade.is_done:
                continue


            filtered.append(trade)

        self.buy_trades = filtered
