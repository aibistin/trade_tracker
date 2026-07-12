# app/services/analysis_service.py
"""Shared trade-analysis pipeline used by both API and web routes."""
import logging

from lib.trading_analyzer import TradingAnalyzer
from app.repositories.trade_repository import get_trade_data_for_analysis

log = logging.getLogger(__name__)


def analyze_symbol(symbol, status="all", account=None, after_date=None, asset_type="all"):
    """Run the full analysis pipeline for one symbol.

    Returns the JSON-serializable profit/loss dict from TradingAnalyzer.
    Raises on invalid input or malformed trade data — use analyze_symbol_safe
    when looping across many symbols.
    """
    transactions = get_trade_data_for_analysis(symbol)
    analyzer = TradingAnalyzer(symbol, transactions)
    analyzer.analyze_trades(status=status, account=account, after_date=after_date)
    return analyzer.get_profit_loss_data_json(asset_type=asset_type)


def analyze_symbol_safe(symbol, status="all"):
    """analyze_symbol variant for cross-symbol loops.

    Returns None (instead of raising) for symbols with no transactions or
    with data problems, so one bad symbol can't break an aggregate endpoint.
    """
    try:
        transactions = get_trade_data_for_analysis(symbol)
        if not transactions:
            return None
        analyzer = TradingAnalyzer(symbol, transactions)
        analyzer.analyze_trades(status=status)
        return analyzer.get_profit_loss_data_json()
    except Exception as e:
        log.warning(f"[analyze_symbol_safe] Skipping {symbol}: {e}")
        return None


def iter_open_buy_trades(analysis_data):
    """Yield (asset_type, trade_dict, remaining_qty) for each open buy trade.

    Walks the stock and option sections of an analyze_symbol result and skips
    sell rows and fully-closed buys.
    """
    for asset_type in ("stock", "option"):
        section = analysis_data.get(asset_type, {})
        if not section.get("has_trades"):
            continue
        for trade in section.get("all_trades", []):
            if not trade.get("is_buy_trade"):
                continue
            remaining_qty = trade["quantity"] - trade.get("current_sold_qty", 0)
            if remaining_qty > 0:
                yield asset_type, trade, remaining_qty
