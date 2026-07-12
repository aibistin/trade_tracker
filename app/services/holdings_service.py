# app/services/holdings_service.py
"""Builds the aggregated open-holdings view served by GET /api/holdings."""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from lib.option_utils import label_to_occ
from lib.yfinance import get_market_price
from lib.constants import OPTIONS_MULTIPLIER
from app.repositories.trade_repository import (
    get_all_securities,
    get_all_traded_symbols,
)
from .analysis_service import analyze_symbol_safe, iter_open_buy_trades

log = logging.getLogger(__name__)

PRICE_FETCH_WORKERS = 8


def build_holdings():
    """Aggregate genuinely open positions across all traded symbols.

    Stocks are aggregated by symbol (one row per ticker); options by contract
    label (one row per unique contract, priced via its OCC-format ticker).
    Returns the full response dict with stock and option sections.
    """
    stock_agg, option_agg = _aggregate_open_positions()

    stock_positions = [_stock_position(symbol, agg) for symbol, agg in stock_agg.items()]
    option_positions = [_option_position(label, agg) for label, agg in option_agg.items()]

    _apply_live_prices(stock_positions, option_positions)

    log.info(
        f"[holdings] {len(stock_positions)} stock positions, "
        f"{len(option_positions)} option positions"
    )
    return {
        "stock": _section_with_totals(stock_positions),
        "option": _section_with_totals(option_positions),
    }


def _aggregate_open_positions():
    """Sum open quantity and cost per stock symbol and per option label."""
    name_map = {symbol: name for symbol, name in get_all_securities()}

    stock_agg = {}   # symbol -> { name, trade_type, total_qty, total_cost }
    option_agg = {}  # label  -> { occ_ticker, symbol, name, trade_type, total_qty, total_cost }

    for symbol in get_all_traded_symbols():
        data = analyze_symbol_safe(symbol, status="open")
        if data is None:
            continue

        for asset_type, trade, remaining_qty in iter_open_buy_trades(data):
            if asset_type == "stock":
                agg = stock_agg.setdefault(symbol, {
                    "name": name_map.get(symbol, ""),
                    "trade_type": trade.get("trade_type", "L"),
                    "total_qty": 0.0,
                    "total_cost": 0.0,
                })
                agg["total_qty"] += remaining_qty
                agg["total_cost"] += trade["price"] * remaining_qty
            else:
                label = trade.get("trade_label", "")
                if not label:
                    continue
                try:
                    occ_ticker = label_to_occ(label)
                except ValueError as e:
                    log.warning(f"[holdings] Cannot convert option label {label!r}: {e}")
                    continue
                agg = option_agg.setdefault(label, {
                    "occ_ticker": occ_ticker,
                    "symbol": symbol,
                    "name": name_map.get(symbol, ""),
                    "trade_type": trade.get("trade_type", ""),
                    "total_qty": 0.0,
                    "total_cost": 0.0,
                })
                agg["total_qty"] += remaining_qty
                agg["total_cost"] += trade["price"] * remaining_qty * OPTIONS_MULTIPLIER

    return stock_agg, option_agg


def _base_position(agg):
    """Fields common to stock and option position rows."""
    return {
        "name": agg["name"],
        "trade_type": agg["trade_type"],
        "quantity": round(agg["total_qty"], 4),
        "cost_basis": round(agg["total_cost"], 2),
        "current_price": None,
        "market_value": None,
        "unrealized_pnl": None,
        "pnl_pct": None,
    }


def _stock_position(symbol, agg):
    pos = _base_position(agg)
    qty = pos["quantity"]
    pos["symbol"] = symbol
    pos["label"] = ""
    pos["avg_cost"] = round(pos["cost_basis"] / qty, 4) if qty > 0 else 0.0
    return pos


def _option_position(label, agg):
    pos = _base_position(agg)
    qty = pos["quantity"]
    pos["symbol"] = agg["symbol"]
    pos["label"] = label
    pos["occ_ticker"] = agg["occ_ticker"]
    # avg_cost is per-contract price (cost_basis already includes the x100 multiplier)
    pos["avg_cost"] = (
        round(pos["cost_basis"] / (qty * OPTIONS_MULTIPLIER), 4) if qty > 0 else 0.0
    )
    return pos


def _apply_live_prices(stock_positions, option_positions):
    """Fetch current prices in parallel and fill in market value / P&L fields."""
    fetch_tasks = {pos["symbol"]: False for pos in stock_positions}
    fetch_tasks.update({pos["occ_ticker"]: True for pos in option_positions})
    if not fetch_tasks:
        return

    price_map = {}
    with ThreadPoolExecutor(max_workers=PRICE_FETCH_WORKERS) as pool:
        futures = {
            pool.submit(get_market_price, ticker, is_option): ticker
            for ticker, is_option in fetch_tasks.items()
        }
        for future in as_completed(futures):
            price_map[futures[future]] = future.result()

    for pos in stock_positions:
        _price_position(pos, price_map.get(pos["symbol"]), multiplier=1)
    for pos in option_positions:
        _price_position(pos, price_map.get(pos["occ_ticker"]), multiplier=OPTIONS_MULTIPLIER)


def _price_position(pos, price, multiplier):
    if price is None:
        return
    pos["current_price"] = price
    pos["market_value"] = round(price * pos["quantity"] * multiplier, 2)
    pos["unrealized_pnl"] = round(pos["market_value"] - pos["cost_basis"], 2)
    pos["pnl_pct"] = (
        round((pos["unrealized_pnl"] / pos["cost_basis"]) * 100, 2)
        if pos["cost_basis"] != 0 else 0.0
    )


def _section_with_totals(positions):
    total_cost = sum(p["cost_basis"] for p in positions)
    total_value = sum(p["market_value"] for p in positions if p["market_value"] is not None)
    return {
        "positions": positions,
        "total_cost_basis": round(total_cost, 2),
        "total_market_value": round(total_value, 2),
        "total_unrealized_pnl": round(total_value - total_cost, 2),
    }
