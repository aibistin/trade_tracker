# lib/trading_analyzer.py
from dotenv import load_dotenv
import os

load_dotenv()

import warnings
import logging
import os
import time
from datetime import datetime
from typing import Any, cast, Dict, List, Optional
from lib.models.Trade import BuyTrade, SellTrade, TradeData
from lib.models.Trades import Trades, BuyTrades
from lib.models.TradeSummary import TradeSummary
from lib.models.ActionMapping import ActionMapping


OPTIONS_MULTIPLIER = 100
STOCK_MULTIPLIER = 1

timestr = time.strftime("%Y%m%d")
log_level = os.getenv("LOG_LEVEL", "INFO").upper()


# Set up logging to flush immediately (no buffering)
class FlushStreamHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()


logging.getLogger().handlers.clear()
# logging.getLogger().addHandler(FlushStreamHandler())
logging.basicConfig(
    filename=f"./logs/trading_analyzer_{timestr}.log",
    # level=logging.DEBUG,
    level=log_level,
    format="%(asctime)s - %(levelname)s - %(lineno)d> %(message)s",
)


class TradingAnalyzer:

    def __init__(
        self, stock_symbol: str, trade_transactions: List[Dict[str, Any]]
    ) -> None:
        if not isinstance(stock_symbol, str):
            raise TypeError("stock_symbol must be a string")
        if not isinstance(trade_transactions, list):
            raise TypeError("trade_transactions must be a list")

        logging.warning(f"Log level set to: {log_level}")
        logging.warning(f"Log level env: {os.getenv('LOG_LEVEL')}")
        self.stock_symbol = stock_symbol
        self.trade_transactions = trade_transactions

        self.required_trade_fields = [
            "id",
            "symbol",
            "action",
            "quantity",
            "price",
            "trade_date",
        ]
        # TODO This could be a datatype
        self.profit_loss_data = {
            "stock": {
                "has_trades": False,
                "summary": {},
                "all_trades": [],
            },
            "option": {
                "has_trades": False,
                "summary": {},
                "all_trades": [],
            },
        }

        self.buy_sell_actions = ["B", "Buy", "BO", "RS", "S", "SC"]
        self.action_mapping = ActionMapping()

    def _convert_to_trade(self, trade: Dict[str, Any]) -> BuyTrade | SellTrade:
        """Validate a trade to ensure it has the required fields and valid data.

        Args:
            trade (Dict[str, Any]): A trade transaction.

        Raises:
            ValueError: If the trade is missing required fields or contains invalid data.

        Returns: A Trade Object
        """

        for field in self.required_trade_fields:
            if field not in trade:
                logging.error(f"[{self.stock_symbol}] missing field: {trade}")
                raise ValueError(
                    f"{self.stock_symbol} - is missing required field: {field}"
                )

        if trade["action"] in (self.buy_sell_actions):
            if not isinstance(trade["price"], (int, float)) or trade["price"] <= 0:
                raise ValueError(
                    f"{trade['symbol']} ID: {trade['id']} - Invalid price: {trade['price']}"
                )

        # Check that Trade Date is either a string or datetime
        if not isinstance(trade["trade_date"], (str, datetime)):
            raise ValueError(
                f"{trade['symbol']} ID: {trade['id']} -Invalid trade date: {trade['Trade Date']}, must be a string or datetime"
            )

        if self.action_mapping.is_buy_type_action(trade["action"]):
            return BuyTrade(cast(TradeData, trade))
        elif self.action_mapping.is_sell_type_action(trade["action"]):
            return SellTrade(cast(TradeData, trade))
        else:
            logging.error(f"[{self.stock_symbol}] Unknown action: {trade['action']}")
            raise ValueError(
                f"[{self.stock_symbol}] Unknown action: {trade['action']} - ID {trade['id']}"
            )

    def _analyze_trades(
        # self, after_date: Optional[str] = None, status: Optional[str] = "all"
        self,
        after_date: Optional[str] = None,
        status: str = "all",
    ) -> None:
        symbol = self.stock_symbol
        stock_trades = Trades(security_type="stock")
        option_trades = Trades(security_type="option")
        try:
            for trade_dict in self.trade_transactions:
                trade = self._convert_to_trade(trade_dict)
                (
                    stock_trades.add_trade(trade)
                    if not trade.is_option
                    else option_trades.add_trade(trade)
                )
        except Exception as e:
            logging.error(f"[{symbol}] Error converting trades to Trade: {e}")
            raise

        logging.info(
            f"[{symbol}] {len(self.trade_transactions)} trades converted to Trade"
        )

        try:
            stock_trades.sort_trades()
            option_trades.sort_trades()
        except Exception as e:
            logging.error(f"[{symbol}] Error sorting trades: {e}")
            raise

        logging.debug(f"[{symbol}] All sell trades are sorted")
        # logging.debug(f"[{symbol}] Sorted Stock Trades: {stock_trades}")

        for trades in [stock_trades, option_trades]:
            security_type = trades.security_type
            if len(trades.buy_trades) == 0:
                logging.info(f"[{symbol}] No {security_type} trades")
                continue

            try:
                buy_trades = self._create_buy_trades_collection(
                    trades, symbol, status=status, after_date=after_date
                )
            except Exception as e:
                logging.error(
                    f"[{symbol}] Error creating BuyTrades collection for {security_type}: {e}"
                )
                raise

            if buy_trades is None:
                logging.warning(f"[{symbol}] Has no {security_type} BuyTrades")
                continue

            # Filter BuyTrades collection
            buy_trades.filter_buy_trades()
            logging.debug(
                f"[{symbol}] Filtered {security_type} BuyTrades: \n{buy_trades}"  
            )

            logging.debug(
                f"[{symbol}] Filtered {security_type} BuyTrades: {buy_trades}"
            )

            try:
                trade_summary = TradeSummary.create_from_buy_trades_collection(
                    symbol=self.stock_symbol,
                    buy_trades_collection=buy_trades,
                    after_date=after_date,
                )
            except Exception as e:
                logging.error(
                    f"[{symbol}] Error creating {buy_trades.security_type} summary record: {e}"
                )
                raise

            logging.debug(f"[{symbol}] {security_type} Summary: {trade_summary}")

            # Update profit/loss data
            self.profit_loss_data[security_type]["has_trades"] = (
                len(trade_summary.buy_trades) > 0
            )
            self.profit_loss_data[security_type]["summary"] = trade_summary

            try:
                trade_summary.security_summary_sanity_check(symbol)
            except Exception as e:
                logging.error(
                    f"[{symbol}] Error in {security_type} summary sanity check: {e}"
                )
                raise

            # TODO - Check if we need ["all_trades"]
            self.profit_loss_data[security_type]["all_trades"] = (
                trade_summary.process_all_trades(symbol)
            )

    def _create_buy_trades_collection(
        self,
        trades: Trades,
        symbol: str,
        status: str = "all",
        after_date: Optional[str] = None,
    ) -> Optional[BuyTrades]:
        """Group sell trades with their corresponding buy trades (stock or option)."""

        if not trades.buy_trades:
            logging.info(f"[{symbol}] No {trades.security_type} buy trades")
            return None

        FilteredBuyTrades = BuyTrades(
            security_type=trades.security_type, after_date_str=after_date, status=status
        )

        for current_buy_record in trades.buy_trades:
            # if sell_trades_sorted:
            if current_buy_record.account in trades.sells_by_account and len(
                trades.sells_by_account[current_buy_record.account]
            ):
                current_buy_record.apply_sell_trades(
                    trades.sells_by_account[current_buy_record.account]
                )

            try:
                FilteredBuyTrades.add_trade(current_buy_record)
            except Exception as e:
                logging.error(
                    f"[{symbol}] Error adding buy trade to BuyTrades collection: {e}"
                )
                raise

        return FilteredBuyTrades

    def _initialize_profit_loss_data_structure(
        self, stock_summary: TradeSummary, option_summary: TradeSummary
    ) -> Dict[str, Any]:
        """Initialize the profit/loss data structure."""

        for i, security_type in enumerate(["stock", "option"]):
            self.profit_loss_data[security_type]["has_trades"] = False
            self.profit_loss_data[security_type]["summary"] = (
                stock_summary if i == 0 else option_summary
            )
            self.profit_loss_data[security_type]["all_trades"] = []

        return self.profit_loss_data

    def analyze_trades(
        self, after_date: Optional[str] = None, status: Optional[str] = None
    ) -> None:
        """
        Analyze trades and calculate profit/loss for each trade.

        Args:
            after_date (str, optional): Date in 'yyyy-mm-dd' format. Only include
                buy trades on or after this date.
            status (str, optional): Filter by trade status. Valid values:
                'open' - Only trades with unsold shares
                'closed' - Only fully closed trades
                None - All trades (default)
        """

        # Validate status parameter
        valid_statuses = ["all", "open", "closed", None]
        if status not in valid_statuses:
            logging.error(f"[{self.stock_symbol}] Invalid status: {status}")
            raise ValueError(
                f"Invalid status: '{status}'. Must be one of {valid_statuses}"
            )

        if after_date is not None:
            try:
                datetime.strptime(after_date, "%Y-%m-%d")
            except ValueError:
                logging.error(
                    f"[{self.stock_symbol}] Invalid after_date format: {after_date}"
                )
                raise ValueError(
                    f"after_date must be in 'yyyy-mm-dd' format, got: {after_date}"
                )

        logging.info(
            f"[{self.stock_symbol}] Analyzing trades after: {after_date}, status: {status}"
        )

        self._analyze_trades(after_date, status)

    def get_profit_loss_data(self) -> Dict[str, Any]:
        """
        Returns:
            Dict[str, Any]: Filtered profit_loss_data.
            profit_loss_data = {
                "stock": {
                     # Type Summary dataclass
                    "summary": {},
                    # Type: Trades
                    "all_trades": [],
                },
                "option": {
                     # Type Summary dataclass
                    "summary": {},
                    # Type: Trades
                    "all_trades": [],
                },
            }

        """

        return self.profit_loss_data

    def _convert_summary_to_dict(self, summary: Any) -> Dict[str, Any]:
        """Convert TradeSummary to dictionary with proper serialization"""
        if not hasattr(summary, "__dict__"):
            return {}

        result = {}
        for key, value in summary.__dict__.items():
            # Skip special attributes
            if key.startswith("__") and key.endswith("__"):
                continue

            if key == "buy_trades" or key == "sell_trades":
                result[key] = [t.to_dict() for t in value] if value else []
            elif key == "sells_by_account":
                result[key] = {
                    k: [t.to_dict() for t in v] for k, v in value.items()   
                }
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif hasattr(value, "to_dict"):
                result[key] = value.to_dict()
            else:
                result[key] = value
        return result

    def get_profit_loss_data_json(self) -> Dict[str, Any]:
        """
        Returns profit/loss data in fully JSON-serializable format.

        Returns:
            Dict[str, Any]: JSON-serializable profit_loss_data
        """
        profit_loss_data = self.get_profit_loss_data()
        json_data = {}

        for security_type in ["stock", "option"]:
            sec_data = profit_loss_data[security_type]

            # Convert all_trades to dictionaries
            all_trades_dicts = []
            for buy_trade in sec_data["all_trades"]:
                if hasattr(buy_trade, "to_dict"):
                    sell_trades = [t.to_dict() for t in buy_trade.sells]
                    # del buy_trade.sells
                    all_trades_dicts.append(buy_trade.to_dict())
                    for sell_trade in sell_trades:
                        all_trades_dicts.append(sell_trade)
                else:
                    # Fallback for unexpected types
                    # TODO: Check if this is used and Flatten out the sell trades
                    all_trades_dicts.append(str(buy_trade))

            json_sec = {
                "has_trades": sec_data["has_trades"],
                "summary": self._convert_summary_to_dict(sec_data["summary"]),
                "all_trades": all_trades_dicts,
            }
            json_data[security_type] = json_sec

        return json_data
