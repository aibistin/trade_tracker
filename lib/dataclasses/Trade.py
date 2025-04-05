from dataclasses import dataclass, field    
from datetime import datetime
from typing import List, Optional, Union
# from typing import Any,  Dict, Tuple


@dataclass
class Trade:
    trade_id: str
    symbol: str
    action: str
    trade_date: datetime
    # trade_date_iso: str
    trade_type: str
    trade_label: str
    quantity: float
    price: float
    amount: float
    account: Optional[str] = None
    current_sold_qty: float = 0
    is_option: bool = False
    # Optional fields
    expiration_date_iso: Optional[str] = None
    target_price: Optional[float] = None
    account: Optional[str] = None
    reason: Optional[str] = None
    target_price: Optional[float] = None
    reason: Optional[str] = None
    initial_stop_price: Optional[float] = None
    projected_sell_price: Optional[float] = None

    def __post_init__(self):
        """Populate trade_date_iso with ISO format of trade_date."""
        if self.trade_date:
            self.trade_date_iso = self._convert_to_iso_format(self.trade_date)
        if self.expiration_date_iso:
            self.expiration_date_iso = self._convert_to_iso_format(self.expiration_date_iso)



    def _convert_to_iso_format(self, date_obj: Union[datetime, str]) -> str:
        if isinstance(date_obj, str):
            try:
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d")
            except ValueError as e:
                #TODO logging instead of print
                print (f"Date string must match format, Y-m-d: {date_obj}: {e}")
                raise 
            except Exception as e:
                print (f"Failed parsing date string: {date_obj}: {e}")
        return date_obj.isoformat()




@dataclass
class SellTrade(Trade):
    """Dataclass for Sell Trade, inheriting from Trade."""

    profit_loss: float = 0.0
    percent_profit_loss: float = 0.0


@dataclass
class BuyTrade(Trade):
    """Dataclass for Buy Trade, inheriting from Trade."""

    is_done: bool = False
    sells: List[SellTrade] = field(default_factory=list)

