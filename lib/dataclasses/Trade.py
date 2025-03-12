from dataclasses import dataclass
from datetime import datetime

from typing import List, Optional
from lib.dataclasses.SellTrade import SellTrade

@dataclass
class Trade:
    trade_id: str
    symbol: str
    action: str
    trade_date: datetime
    trade_date_iso: str
    trade_type: str
    trade_label: str
    quantity: float
    price: float
    amount: float
    expiration_date_iso: str
    account: Optional[str] = None
    current_sold_qty: float = 0
    is_option: bool = False
    is_done: bool = False
    sells: List[SellTrade] = None
    # Optional fields
    target_price: Optional[float] = None
    reason: Optional[str] = None
    initial_stop_price: Optional[float] = None
    projected_sell_price: Optional[float] = None

    def __post_init__(self):
        """Initialize the `sells` list if it's None."""
        if self.sells is None:
            self.sells = []

