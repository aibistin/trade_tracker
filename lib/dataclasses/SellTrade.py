from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class SellTrade:
    trade_id: str
    trade_date: datetime
    trade_date_iso: str
    trade_label: str
    trade_type: str
    quantity: float
    price: float
    amount: float
    profit_loss: float
    percent_profit_loss: float
    is_option: bool = False
    # Optional fields
    expiration_date_iso: Optional[str] = None
    target_price: Optional[float] = None
    account: Optional[str] = None
    reason: Optional[str] = None
