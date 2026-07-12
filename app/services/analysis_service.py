# app/services/analysis_service.py
"""Shared trade-analysis pipeline used by both API and web routes."""
import logging
import threading
import time

from sqlalchemy import func, select

from lib.trading_analyzer import TradingAnalyzer
from app.extensions import db
from app.models.models import TradeTransaction
from app.repositories.trade_repository import get_trade_data_for_analysis

log = logging.getLogger(__name__)

# In-process cache for analyze_symbol_safe. Entries are validated against a
# data-version token (MAX(id), COUNT(*)) so any insert — including from the
# external Schwab sync process — invalidates the whole cache on the next
# request. Trade-field edits don't change the token, so the update routes call
# clear_analysis_cache() explicitly. The TTL is a backstop for edits made
# directly in SQLite outside the app.
CACHE_TTL_SECONDS = 30 * 60

_cache_lock = threading.Lock()
_cache = {}            # (symbol, status) -> (result, cached_at)
_cache_version = None  # data-version token the current entries were built from


def _data_version():
    """Cheap token that changes whenever trade rows are inserted or deleted."""
    return db.session.execute(
        select(func.max(TradeTransaction.id), func.count(TradeTransaction.id))
    ).one()


def clear_analysis_cache():
    """Drop all cached analysis results (call after mutating trade rows)."""
    global _cache_version
    with _cache_lock:
        _cache.clear()
        _cache_version = None


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
    """analyze_symbol variant for cross-symbol loops, with caching.

    Returns None (instead of raising) for symbols with no transactions or
    with data problems, so one bad symbol can't break an aggregate endpoint.
    Results are cached per (symbol, status); callers must treat the returned
    dict as read-only.
    """
    global _cache_version
    key = (symbol, status)
    now = time.monotonic()
    version = _data_version()

    with _cache_lock:
        if version != _cache_version:
            _cache.clear()
            _cache_version = version
        entry = _cache.get(key)
        if entry is not None and now - entry[1] < CACHE_TTL_SECONDS:
            return entry[0]

    try:
        transactions = get_trade_data_for_analysis(symbol)
        if not transactions:
            result = None  # cached too — no point re-querying empty symbols
        else:
            analyzer = TradingAnalyzer(symbol, transactions)
            analyzer.analyze_trades(status=status)
            result = analyzer.get_profit_loss_data_json()
    except Exception as e:
        # Transient failures are not cached
        log.warning(f"[analyze_symbol_safe] Skipping {symbol}: {e}")
        return None

    with _cache_lock:
        # Only store if the data hasn't shifted underneath us mid-computation
        if version == _cache_version:
            _cache[key] = (result, now)
    return result


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
