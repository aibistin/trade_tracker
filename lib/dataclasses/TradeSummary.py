from dataclasses import dataclass, field
from typing import List, Optional, Union
from lib.dataclasses.Trade import BuyTrade, SellTrade

OPTIONS_MULTIPLIER = 100
STOCK_MULTIPLIER = 1


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
    average_basis_open_price: float = 0.0
    average_basis_sold_price: float = 0.0
    buy_trades: List["BuyTrade"] = field(default_factory=list)
    sell_trades: List["SellTrade"] = field(default_factory=list)
    multiplier: Optional[int] = 1

    def __post_init__(self):
        self.multiplier = (
            OPTIONS_MULTIPLIER if self.is_option == True else STOCK_MULTIPLIER
        )

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

        self.closed_bought_quantity = round(final_sold_quantity,2)
        self.closed_bought_amount = round(final_sold_amount,2)

        self.get_open_bought_quantity()
        self.get_open_bought_amount()
        self.get_profit_loss()
        self.get_percent_profit_loss()
        # Calculate Average Basis Sold Price
        self.get_average_basis_sold_price()
        # Calculate Average Basis Un-Sold Price
        self.get_average_basis_open_price()
