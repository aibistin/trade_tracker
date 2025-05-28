from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Tuple
from lib.dataclasses.Trade import BuyTrade, SellTrade, Trade

@dataclass
class Trades:
    security_type: str
    trades: list[Trade] = field(default_factory=list)
    buy_trades: list[BuyTrade] = field(default_factory=list)
    sell_trades: list[SellTrade] = field(default_factory=list)

    def _sort_trades(self, trades: list[Trade]) -> list[Trade]:
        """Sort trades by trade date, type, and action."""
        trades.sort(
            key=lambda x: (
                x.trade_date,
                x.action,
                x.account,
                x.is_option,
                x.trade_type,
            )
        )
        return trades

    def sort_trades(self) -> None:
        """Sort Trades by trade date, type, and action."""
        self._sort_trades(self.buy_trades)
        self._sort_trades(self.sell_trades)

    def add_trade(self, trade: Trade) -> None:
        """Add a trade to the Trades, BuyTrades and SellTtrades collections."""
        if not isinstance(trade, Trade):
            raise TypeError("trade must be an instance of Trade")

        self.trades.append(trade)
        if isinstance(trade, BuyTrade):
            self.buy_trades.append(trade)
        elif isinstance(trade, SellTrade):
            self.sell_trades.append(trade)


@dataclass
class BuyTrades(Trades):
    buy_trades: list[BuyTrade] = field(default_factory=list)
    trades: Tuple[SellTrade, ...] = field(default_factory=tuple, init=False, repr=False)
    sell_trades: Tuple[SellTrade, ...] = field(
        default_factory=tuple, init=False, repr=False
    )
    after_date_str: Optional[str] = None
    after_date: Optional[datetime] = field(default=None, init=False)

    def __post_init__(self):
        """
        Populate after_date with datetime -> after_date_str.
        """
        if self.after_date_str is not None:
            try:
                self.after_date = datetime.strptime(self.after_date_str, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"after_date must be in 'yyyy-mm-dd' format, got: {self.after_date_str}"
                )


    def add_trade(self, trade: BuyTrade) -> Trade | None:
        if not isinstance(trade, BuyTrade):
            raise TypeError(f"trade must be an instance of BuyTrade: {trade}")

        if self.after_date:
            if trade.trade_date >= self.after_date:
                self.buy_trades.append(trade)
                return trade
        else:
            self.buy_trades.append(trade)
            return trade

        return None


    def filter_buy_trades(self) -> None:
        """
        Filter Buy trades on or after self.after_date.
        If after_date is None, it does not filter the trades.
        self.buy_trades is modified in place.
        If after_date is None, it does not filter the trades.

        Returns:
            None

        """
        if self.after_date is not None:
            self.buy_trades = [
                buy_trade
                for buy_trade in self.buy_trades
                if buy_trade.trade_date >= self.after_date
            ]
