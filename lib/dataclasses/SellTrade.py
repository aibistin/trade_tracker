from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class SellTrade:
    trade_id: str
    trade_date: datetime
    trade_date_iso: str
    quantity: float
    price: float
    amount: float
    profit_loss: float
    percent_profit_loss: float
    account: Optional[str] = None