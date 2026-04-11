# app/routes/api_routes.py
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Blueprint, request, jsonify
from app.utils import filter_symbols
from lib.trading_analyzer import TradingAnalyzer
from lib.yfinance import YahooFinance
from lib.option_utils import label_to_occ
import yfinance as yf_lib

api_bp = Blueprint("api", __name__)
log = logging.getLogger(__name__)

from ..models.models import TradeTransaction
from ..repositories.trade_repository import (
    get_all_securities,
    get_all_traded_symbols,
    get_current_holdings,
    get_current_holdings_symbols,
    get_trade_data_for_analysis,
)
from ..extensions import db
from ..services.trade_service import validate_trade_update


# TODO Add proper authentication
def valid_api_key(request):
    log.debug(f"[valid_api_key] FLASK_ENV: {os.environ.get('FLASK_ENV')}")
    if os.environ.get("FLASK_ENV") == "dev":
        log.debug(f"[valid_api_key] Dev Environment- No API key check")
        return True
    return request.headers.get("X-API-KEY") == os.environ.get("API_SECRET_KEY")


@api_bp.before_request
def require_api_key():
    log.debug(f"[require_api_key] {request.method} {request.url} from {request.remote_addr}")

    if not valid_api_key(request):
        log.debug(f"[require_api_key] Invalid API Key")
        return jsonify(error="Unauthorized"), 401


# Ajax
@api_bp.route("/get_stock_data/<string:stock_symbol>")
def get_stock_data(stock_symbol):
    """Fetches stock data from Yahoo Finance and returns it as JSON."""
    log.debug(f"[{stock_symbol}] Getting Yahoo Data")
    yf = YahooFinance(stock_symbol)
    yf.get_stock_data()
    stock_data = yf.get_results()
    log.debug(f"[{stock_symbol}] Yahoo Data: {stock_data}")
    return jsonify(stock_data)


@api_bp.route("/trade/symbols_json")
def get_symbols():
    all_symbol_names = get_all_securities()
    symbols_names = filter_symbols(all_symbol_names)
    log.debug(f"[trade/symbols_json] symbols_names[:3]: {symbols_names[:3]}")
    return jsonify(symbols_names)


@api_bp.route("/trade/current_holdings_json")
def get_current_holdings_json():
    """Get current holdings from the database and return as JSON."""

    # Specific logging for this route
    logging.getLogger("app.routes.api_routes").setLevel(logging.DEBUG)

    current_holdings = get_current_holdings()
    log.debug(
        f"[get_current_holdings_json] Current Holdings[:3]: {current_holdings[:3]}"
    )
    # Convert the tuple data into a list of dictionaries with named fields
    holdings_list = [
        {
            "symbol": symbol,
            "trade_type": trade_type,
            "shares": shares,
            "average_price": price,
            "profit_loss": pl,
            "name": name,
        }
        for symbol, trade_type, shares, price, pl, name in current_holdings
    ]

    log.debug(f"[get_current_holdings_json] Holdings list: {holdings_list}")

    return jsonify(holdings_list)


@api_bp.route("/trade/current_holdings_symbols_json")
def get_current_holdings_symbols_json():
    """Get current holdings, symbols only from the database and return as JSON."""
    current_symbols = get_current_holdings_symbols()
    log.debug(
        f"[get_current_holdings_symbols_json] Current Symbols[:3]: {current_symbols[:3]}"
    )
    return jsonify(current_symbols)


@api_bp.route("/options/prices", methods=["POST"])
def get_options_prices():
    """Get current prices for a list of option tickers.

    Request body: {"tickers": ["AAPL250117C00150000", ...]}
    Returns: {"prices": {"AAPL250117C00150000": {"bid": ..., "ask": ..., "last": ..., "symbol": ...}, ...}}
    """
    data = request.get_json(silent=True)
    if data is None or "tickers" not in data:
        return jsonify({"error": "Request body must contain a 'tickers' list"}), 400

    tickers = data["tickers"]
    if not isinstance(tickers, list):
        return jsonify({"error": "'tickers' must be a list"}), 400

    prices = {}
    for ticker in tickers:
        if not isinstance(ticker, str) or not ticker.strip():
            continue
        try:
            yf = YahooFinance(ticker)
            yf.get_stock_data()
            info = yf.get_results()
            if info:
                prices[ticker] = {
                    "bid": info.get("bid"),
                    "ask": info.get("ask"),
                    "last": info.get("lastPrice") or info.get("regularMarketPrice") or info.get("currentPrice"),
                    "symbol": info.get("symbol", ticker),
                }
            else:
                prices[ticker] = {"bid": None, "ask": None, "last": None, "symbol": ticker}
        except Exception as e:
            log.warning(f"[options/prices] Failed to fetch price for {ticker}: {e}")
            prices[ticker] = {"bid": None, "ask": None, "last": None, "symbol": ticker}

    log.info(f"[options/prices] Fetched prices for {len(prices)}/{len(tickers)} tickers")
    return jsonify({"prices": prices})


@api_bp.route("/trades/<string:scope>/json/<string:stock_symbol>")
def get_positions_json(scope, stock_symbol):
    """Get either open or closed positions for a given stock symbol in JSON format.
    Valid values for scope are 'all', 'open' or 'closed'.

    Optional query parameters:
        after_date: Filter trades on or after this date (YYYY-MM-DD format)
        account: Filter by account code (C, R, I, or O)
        asset_type: Filter by asset type — 'stock', 'option', or 'all' (default: 'all').
                    When set to 'stock' or 'option', only that section is included in the
                    response. The frontend exposes this via a green toggle button group
                    in the navbar, passed as a query parameter (e.g. ?asset_type=stock).
    """

    if scope not in ["all", "open", "closed"]:
        return (
            jsonify(
                {"error": 'Invalid scope. Must be either "all", "open" or "closed"'}
            ),
            400,
        )

    after_date = request.args.get("after_date")
    account = request.args.get("account")
    asset_type = request.args.get("asset_type", "all")

    # Validate asset_type
    valid_asset_types = ["stock", "option", "all"]
    if asset_type not in valid_asset_types:
        return jsonify({"error": f"asset_type must be one of {valid_asset_types}"}), 400

    # Validate after_date format if provided
    if after_date is not None:
        from datetime import datetime
        try:
            datetime.strptime(after_date, "%Y-%m-%d")
        except (ValueError, TypeError):
            return jsonify({"error": "after_date must be in 'YYYY-MM-DD' format"}), 400

    # Validate account if provided
    valid_accounts = ["C", "R", "I", "O"]
    if account is not None and account not in valid_accounts:
        return jsonify({"error": f"account must be one of {valid_accounts}"}), 400

    log.info(f"[{stock_symbol}] Getting {scope.capitalize()} Positions JSON"
             + (f" after_date={after_date}" if after_date else "")
             + (f" account={account}" if account else "")
             + (f" asset_type={asset_type}" if asset_type != "all" else ""))

    trade_record = {
        "stock_symbol": stock_symbol,
        "transaction_stats": {},
        "requested": f"{scope}_trades",
    }

    if after_date or account or asset_type != "all":
        trade_record["filters"] = {}
        if after_date:
            trade_record["filters"]["after_date"] = after_date
        if account:
            trade_record["filters"]["account"] = account
        if asset_type != "all":
            trade_record["filters"]["asset_type"] = asset_type

    trade_transactions = get_trade_data_for_analysis(stock_symbol)

    analyzer = TradingAnalyzer(stock_symbol, trade_transactions)

    analyzer.analyze_trades(status=scope, after_date=after_date, account=account)
    trade_record["transaction_stats"] = analyzer.get_profit_loss_data_json(asset_type=asset_type)
    log.debug(
        f"[Routes] {scope.capitalize()} all_trades for {stock_symbol}: {trade_record['transaction_stats']}"
    )

    return jsonify(trade_record)

@api_bp.route("/trades/<string:scope>/json/<string:stock_symbol>/filtered", methods=['POST'])
def get_filtered_positions_json(scope, stock_symbol):
    """Get positions with additional filters (after_date, account) for a stock symbol in JSON format.
    Valid values for scope are 'all', 'open' or 'closed'."""

    
    if scope not in ["all", "open", "closed"]:
        return (
            jsonify(
                {"error": 'Invalid scope. Must be either "all", "open" or "closed"'}
            ),
            400,
        )

    # Get filter parameters from request body
    request_data = request.get_json(silent=True)
    if request_data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    after_date = request_data.get('after_date')
    account = request_data.get('account')

    # Validate after_date format if provided
    if after_date is not None:
        from datetime import datetime
        try:
            datetime.strptime(after_date, "%Y-%m-%d")
        except (ValueError, TypeError):
            return jsonify({"error": "after_date must be in 'YYYY-MM-DD' format"}), 400

    # Validate account if provided
    valid_accounts = ["C", "R", "I", "O"]
    if account is not None and account not in valid_accounts:
        return jsonify({"error": f"account must be one of {valid_accounts}"}), 400
    
    log.info(f"[{stock_symbol}] Getting {scope.capitalize()} Positions with filters: "
             f"after_date={after_date}, account={account}")

    trade_record = {
        "stock_symbol": stock_symbol,
        "transaction_stats": {},
        "requested": f"{scope}_trades",
        "filters": {
            "after_date": after_date,
            "account": account
        }
    }

    trade_transactions = get_trade_data_for_analysis(stock_symbol)
    log.debug(f"[Routes][get_filtered_positions_json] raw_data: {trade_transactions}")
    analyzer = TradingAnalyzer(stock_symbol, trade_transactions)

    # Apply filters
    analyzer.analyze_trades(
        status=scope,
        after_date=after_date,
        account=account
    )
    
    trade_record["transaction_stats"] = analyzer.get_profit_loss_data_json()
    
    log.debug(
        f"[Routes] Filtered {scope} positions for {stock_symbol}: "
        f"Found {len(trade_record['transaction_stats']['stock']['all_trades'])} trades"
    )

    return jsonify(trade_record)


@api_bp.route("/trade/update/<int:transaction_id>", methods=["PATCH"])
def update_trade(transaction_id):
    """Update user-editable fields on a trade transaction (reason, initial_stop_price, projected_sell_price)."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    trade = db.session.get(TradeTransaction, transaction_id)
    if trade is None:
        return jsonify({"error": f"Trade {transaction_id} not found"}), 404

    errors = validate_trade_update(data)

    if errors:
        return jsonify({"error": "Validation failed", "fields": errors}), 422

    allowed_fields = {"reason", "initial_stop_price", "projected_sell_price"}
    updated = {}
    for field in allowed_fields:
        if field in data:
            setattr(trade, field, data[field])
            updated[field] = data[field]

    if not updated:
        return jsonify({"error": "No valid fields to update"}), 400

    db.session.commit()
    log.info(f"[update_trade] Updated trade {transaction_id}: {updated}")
    return jsonify({"success": True, "updated": updated}), 200


@api_bp.route("/holdings")
def get_holdings():
    """Get genuinely open positions using TradingAnalyzer to match buys against sells.

    Stock positions are aggregated by symbol (one row per ticker, no duplicates).
    Option positions are aggregated by contract label (one row per unique option contract).
    Option prices are fetched using OCC-format tickers converted from Schwab labels.

    Returns separate stock and option sections, each with per-position details.
    """
    symbols = get_all_traded_symbols()
    name_map = {symbol: name for symbol, name in get_all_securities()}

    # symbol -> { name, trade_type, total_qty, total_cost }
    stock_agg = {}
    # label -> { occ_ticker, symbol, name, trade_type, total_qty, total_cost }
    option_agg = {}

    for symbol in symbols:
        try:
            transactions = get_trade_data_for_analysis(symbol)
            if not transactions:
                continue
            analyzer = TradingAnalyzer(symbol, transactions)
            analyzer.analyze_trades(status="open")
            data = analyzer.get_profit_loss_data_json()
        except Exception as e:
            log.warning(f"[holdings] Skipping {symbol}: {e}")
            continue

        # Aggregate stock positions by symbol
        sec = data.get("stock", {})
        if sec.get("has_trades"):
            for trade in sec.get("all_trades", []):
                if not trade.get("is_buy_trade"):
                    continue
                remaining_qty = trade["quantity"] - trade.get("current_sold_qty", 0)
                if remaining_qty <= 0:
                    continue
                if symbol not in stock_agg:
                    stock_agg[symbol] = {
                        "name": name_map.get(symbol, ""),
                        "trade_type": trade.get("trade_type", "L"),
                        "total_qty": 0.0,
                        "total_cost": 0.0,
                    }
                stock_agg[symbol]["total_qty"] += remaining_qty
                stock_agg[symbol]["total_cost"] += trade["price"] * remaining_qty

        # Aggregate option positions by contract label
        sec = data.get("option", {})
        if sec.get("has_trades"):
            for trade in sec.get("all_trades", []):
                if not trade.get("is_buy_trade"):
                    continue
                remaining_qty = trade["quantity"] - trade.get("current_sold_qty", 0)
                if remaining_qty <= 0:
                    continue
                label = trade.get("trade_label", "")
                if not label:
                    continue
                try:
                    occ_ticker = label_to_occ(label)
                except ValueError as e:
                    log.warning(f"[holdings] Cannot convert option label {label!r}: {e}")
                    continue
                if label not in option_agg:
                    option_agg[label] = {
                        "occ_ticker": occ_ticker,
                        "symbol": symbol,
                        "name": name_map.get(symbol, ""),
                        "trade_type": trade.get("trade_type", ""),
                        "total_qty": 0.0,
                        "total_cost": 0.0,
                    }
                option_agg[label]["total_qty"] += remaining_qty
                option_agg[label]["total_cost"] += trade["price"] * remaining_qty * 100

    # Build flat position lists
    stock_positions = []
    for symbol, agg in stock_agg.items():
        qty = round(agg["total_qty"], 4)
        cost_basis = round(agg["total_cost"], 2)
        avg_cost = round(cost_basis / qty, 4) if qty > 0 else 0.0
        stock_positions.append({
            "symbol": symbol,
            "name": agg["name"],
            "trade_type": agg["trade_type"],
            "label": "",
            "quantity": qty,
            "avg_cost": avg_cost,
            "cost_basis": cost_basis,
            "current_price": None,
            "market_value": None,
            "unrealized_pnl": None,
            "pnl_pct": None,
        })

    option_positions = []
    for label, agg in option_agg.items():
        qty = round(agg["total_qty"], 4)
        cost_basis = round(agg["total_cost"], 2)
        # avg_cost is per-contract price (cost_basis already includes ×100 multiplier)
        avg_cost = round(cost_basis / (qty * 100), 4) if qty > 0 else 0.0
        option_positions.append({
            "symbol": agg["symbol"],
            "name": agg["name"],
            "trade_type": agg["trade_type"],
            "label": label,
            "occ_ticker": agg["occ_ticker"],
            "quantity": qty,
            "avg_cost": avg_cost,
            "cost_basis": cost_basis,
            "current_price": None,
            "market_value": None,
            "unrealized_pnl": None,
            "pnl_pct": None,
        })

    # Fetch current prices in parallel — stocks by symbol, options by OCC ticker
    def _fetch_yf_price(ticker_key, is_option):
        try:
            yf = YahooFinance(ticker_key)
            yf.get_stock_data()
            info = yf.get_results()
            if not info:
                return ticker_key, None
            if is_option:
                price = info.get("lastPrice") or info.get("regularMarketPrice") or info.get("currentPrice")
            else:
                price = info.get("currentPrice") or info.get("regularMarketPrice")
            return ticker_key, price
        except Exception as e:
            log.warning(f"[holdings] Failed to fetch price for {ticker_key}: {e}")
            return ticker_key, None

    fetch_tasks = {}
    for pos in stock_positions:
        fetch_tasks[pos["symbol"]] = False  # stock
    for pos in option_positions:
        fetch_tasks[pos["occ_ticker"]] = True  # option (OCC format)

    price_map = {}
    if fetch_tasks:
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = {pool.submit(_fetch_yf_price, k, v): k for k, v in fetch_tasks.items()}
            for fut in as_completed(futures):
                key, price = fut.result()
                price_map[key] = price

    for pos in stock_positions:
        price = price_map.get(pos["symbol"])
        if price is not None:
            pos["current_price"] = price
            pos["market_value"] = round(price * pos["quantity"], 2)
            pos["unrealized_pnl"] = round(pos["market_value"] - pos["cost_basis"], 2)
            pos["pnl_pct"] = (
                round((pos["unrealized_pnl"] / pos["cost_basis"]) * 100, 2)
                if pos["cost_basis"] != 0 else 0.0
            )

    for pos in option_positions:
        price = price_map.get(pos["occ_ticker"])
        if price is not None:
            pos["current_price"] = price
            pos["market_value"] = round(price * pos["quantity"] * 100, 2)
            pos["unrealized_pnl"] = round(pos["market_value"] - pos["cost_basis"], 2)
            pos["pnl_pct"] = (
                round((pos["unrealized_pnl"] / pos["cost_basis"]) * 100, 2)
                if pos["cost_basis"] != 0 else 0.0
            )

    stock_total_cost = sum(p["cost_basis"] for p in stock_positions)
    stock_total_value = sum(p["market_value"] for p in stock_positions if p["market_value"] is not None)
    option_total_cost = sum(p["cost_basis"] for p in option_positions)
    option_total_value = sum(p["market_value"] for p in option_positions if p["market_value"] is not None)

    log.info(f"[holdings] {len(stock_positions)} stock positions, {len(option_positions)} option positions")
    return jsonify({
        "stock": {
            "positions": stock_positions,
            "total_cost_basis": round(stock_total_cost, 2),
            "total_market_value": round(stock_total_value, 2),
            "total_unrealized_pnl": round(stock_total_value - stock_total_cost, 2),
        },
        "option": {
            "positions": option_positions,
            "total_cost_basis": round(option_total_cost, 2),
            "total_market_value": round(option_total_value, 2),
            "total_unrealized_pnl": round(option_total_value - option_total_cost, 2),
        },
    })


@api_bp.route("/option/price")
def get_option_price():
    """Fetch current price for a single option by its Schwab label string.

    Query params:
        label: Schwab option label, e.g. "UUUU 04/17/2026 23.00 C"

    Returns:
        { "price": float|null, "bid": float|null, "ask": float|null, "occ_ticker": str }
    """
    label = request.args.get("label", "").strip()
    if not label:
        return jsonify({"error": "label query parameter is required"}), 400

    try:
        occ_ticker = label_to_occ(label)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    price = bid = ask = None
    try:
        yf = YahooFinance(occ_ticker)
        yf.get_stock_data()
        info = yf.get_results()
        if info:
            price = info.get("lastPrice") or info.get("regularMarketPrice") or info.get("currentPrice")
            bid = info.get("bid")
            ask = info.get("ask")
    except Exception as e:
        log.warning(f"[option/price] Failed to fetch price for {occ_ticker}: {e}")

    return jsonify({"price": price, "bid": bid, "ask": ask, "occ_ticker": occ_ticker})


@api_bp.route("/ticker/history/<string:symbol>")
def get_ticker_history(symbol):
    """Return OHLCV price history and trade annotations for sparkline charts.

    Query params:
        period: yfinance period string (default '3mo'). Valid: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
        interval: yfinance interval string (default '1d'). Valid: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
    """
    period = request.args.get("period", "3mo")
    interval = request.args.get("interval", "1d")

    valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
    valid_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]

    if period not in valid_periods:
        return jsonify({"error": f"period must be one of {valid_periods}"}), 400
    if interval not in valid_intervals:
        return jsonify({"error": f"interval must be one of {valid_intervals}"}), 400

    # Fetch price history from yfinance
    prices = []
    try:
        ticker = yf_lib.Ticker(symbol)
        hist = ticker.history(period=period, interval=interval)
        for date, row in hist.iterrows():
            prices.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(row["Open"], 2),
                "high": round(row["High"], 2),
                "low": round(row["Low"], 2),
                "close": round(row["Close"], 2),
                "volume": int(row["Volume"]),
            })
    except Exception as e:
        log.warning(f"[ticker/history] Failed to fetch history for {symbol}: {e}")

    # Fetch trade annotations from DB
    trades = []
    try:
        transactions = get_trade_data_for_analysis(symbol)
        for t in transactions:
            trade_date = t.get("trade_date")
            if hasattr(trade_date, "strftime"):
                trade_date = trade_date.strftime("%Y-%m-%d")
            elif isinstance(trade_date, str) and "T" in trade_date:
                trade_date = trade_date.split("T")[0]
            trades.append({
                "date": trade_date,
                "action": t.get("action"),
                "price": t.get("price"),
                "quantity": t.get("quantity"),
                "trade_type": t.get("trade_type", ""),
                "label": t.get("label", ""),
            })
    except Exception as e:
        log.warning(f"[ticker/history] Failed to fetch trades for {symbol}: {e}")

    log.info(f"[ticker/history] {symbol}: {len(prices)} price points, {len(trades)} trades")
    return jsonify({"symbol": symbol, "prices": prices, "trades": trades})


@api_bp.route("/portfolio/heatmap")
def get_portfolio_heatmap():
    """Return open positions formatted for a treemap visualization.

    Each position includes market_value, cost_basis, unrealized_pnl, pnl_pct,
    and weight (fraction of total portfolio market value).
    """
    symbols = get_all_traded_symbols()
    name_map = {symbol: name for symbol, name in get_all_securities()}

    positions = []

    for symbol in symbols:
        try:
            transactions = get_trade_data_for_analysis(symbol)
            if not transactions:
                continue
            analyzer = TradingAnalyzer(symbol, transactions)
            analyzer.analyze_trades(status="open")
            data = analyzer.get_profit_loss_data_json()
        except Exception as e:
            log.warning(f"[heatmap] Skipping {symbol}: {e}")
            continue

        for asset_type in ("stock", "option"):
            sec = data.get(asset_type, {})
            if not sec.get("has_trades"):
                continue
            for trade in sec.get("all_trades", []):
                if not trade.get("is_buy_trade"):
                    continue
                remaining_qty = trade["quantity"] - trade.get("current_sold_qty", 0)
                if remaining_qty <= 0:
                    continue

                avg_cost = trade["price"]
                multiplier = 100 if asset_type == "option" else 1
                cost_basis = round(avg_cost * remaining_qty * multiplier, 2)

                position = {
                    "symbol": symbol,
                    "name": name_map.get(symbol, ""),
                    "trade_type": asset_type,
                    "label": trade.get("trade_label", ""),
                    "quantity": remaining_qty,
                    "cost_basis": cost_basis,
                    "market_value": None,
                    "unrealized_pnl": None,
                    "pnl_pct": None,
                    "weight": 0.0,
                }
                positions.append(position)

    # Fetch current prices — options use OCC-format tickers
    price_cache = {}
    for pos in positions:
        if pos["trade_type"] == "option" and pos["label"]:
            try:
                cache_key = label_to_occ(pos["label"])
            except ValueError:
                log.warning(f"[heatmap] Cannot convert label: {pos['label']!r}")
                continue
        else:
            cache_key = pos["symbol"]

        if cache_key in price_cache:
            price = price_cache[cache_key]
        else:
            price = None
            try:
                yf = YahooFinance(cache_key)
                yf.get_stock_data()
                info = yf.get_results()
                if info:
                    price = (
                        info.get("lastPrice")
                        or info.get("regularMarketPrice")
                        or info.get("currentPrice")
                    )
            except Exception as e:
                log.warning(f"[heatmap] Failed to fetch price for {cache_key}: {e}")
            price_cache[cache_key] = price

        if price is not None:
            multiplier = 100 if pos["trade_type"] == "option" else 1
            pos["market_value"] = round(price * pos["quantity"] * multiplier, 2)
            pos["unrealized_pnl"] = round(pos["market_value"] - pos["cost_basis"], 2)
            pos["pnl_pct"] = (
                round((pos["unrealized_pnl"] / pos["cost_basis"]) * 100, 2)
                if pos["cost_basis"] != 0 else 0.0
            )

    # Compute weights based on market value (or cost_basis as fallback)
    total_value = sum(
        p["market_value"] if p["market_value"] is not None else p["cost_basis"]
        for p in positions
    )
    if total_value > 0:
        for pos in positions:
            val = pos["market_value"] if pos["market_value"] is not None else pos["cost_basis"]
            pos["weight"] = round(val / total_value, 4)

    log.info(f"[portfolio/heatmap] {len(positions)} positions, total_value={total_value}")
    return jsonify({"positions": positions, "total_market_value": round(total_value, 2)})


def _build_symbol_stats(symbol, scope="closed"):
    """Run TradingAnalyzer for a symbol and return serializable stats for stock and option."""
    try:
        transactions = get_trade_data_for_analysis(symbol)
        if not transactions:
            return None
        analyzer = TradingAnalyzer(symbol, transactions)
        analyzer.analyze_trades(status=scope)
        data = analyzer.get_profit_loss_data_json()
    except Exception as e:
        log.warning(f"[dashboard] Skipping {symbol}: {e}")
        return None

    result = {}
    for asset_type in ("stock", "option"):
        sec = data.get(asset_type, {})
        if not sec.get("has_trades"):
            continue
        summary = sec.get("summary", {})
        result[asset_type] = {
            "winning_trades_count": summary.get("winning_trades_count", 0) or 0,
            "losing_trades_count": summary.get("losing_trades_count", 0) or 0,
            "batting_average": summary.get("batting_average", 0.0) or 0.0,
            "profit_loss": summary.get("profit_loss", 0.0) or 0.0,
            "percent_profit_loss": summary.get("percent_profit_loss", 0.0) or 0.0,
        }
    return result if result else None


@api_bp.route("/dashboard/summary")
def get_dashboard_summary():
    """Aggregate win/loss and P&L stats across all symbols (closed trades only)."""
    # Build a name lookup from the security table
    name_map = {symbol: name for symbol, name in get_all_securities()}
    symbols = get_all_traded_symbols()

    total_wins = 0
    total_losses = 0
    total_pnl = 0.0
    by_symbol = []

    for symbol in symbols:
        stats = _build_symbol_stats(symbol, scope="closed")
        if stats is None:
            continue

        symbol_wins = sum(s["winning_trades_count"] for s in stats.values())
        symbol_losses = sum(s["losing_trades_count"] for s in stats.values())
        symbol_pnl = sum(s["profit_loss"] for s in stats.values())

        total_wins += symbol_wins
        total_losses += symbol_losses
        total_pnl += symbol_pnl

        total_decided = symbol_wins + symbol_losses
        by_symbol.append({
            "symbol": symbol,
            "name": name_map.get(symbol, ""),
            "stock": stats.get("stock"),
            "option": stats.get("option"),
            "combined": {
                "winning_trades_count": symbol_wins,
                "losing_trades_count": symbol_losses,
                "batting_average": round(symbol_wins / total_decided, 3) if total_decided else 0.0,
                "profit_loss": round(symbol_pnl, 2),
            },
        })

    total_decided = total_wins + total_losses
    overall = {
        "total_realized_pnl": round(total_pnl, 2),
        "total_winning_trades": total_wins,
        "total_losing_trades": total_losses,
        "batting_average": round(total_wins / total_decided, 3) if total_decided else 0.0,
        "symbols_traded": len(by_symbol),
    }

    log.info(f"[dashboard/summary] {len(by_symbol)} symbols, overall: {overall}")
    return jsonify({"overall": overall, "by_symbol": by_symbol})


@api_bp.route("/dashboard/pnl_over_time")
def get_pnl_over_time():
    """Monthly and quarterly P&L aggregates across all closed trades.

    Optional query param:
        asset_type: 'all' (default), 'stock', or 'option'
    """
    asset_type = request.args.get("asset_type", "all")
    valid_asset_types = ["all", "stock", "option"]
    if asset_type not in valid_asset_types:
        return jsonify({"error": f"asset_type must be one of {valid_asset_types}"}), 400

    symbols = get_all_traded_symbols()
    security_types = ["stock", "option"] if asset_type == "all" else [asset_type]

    # Collect all closed buy trades across all symbols
    monthly = {}   # key: "YYYY-MM"
    quarterly = {} # key: "YYYY-QN"

    for symbol in symbols:
        try:
            transactions = get_trade_data_for_analysis(symbol)
            if not transactions:
                continue
            analyzer = TradingAnalyzer(symbol, transactions)
            analyzer.analyze_trades(status="closed")
            data = analyzer.get_profit_loss_data_json()
        except Exception as e:
            log.warning(f"[dashboard/pnl_over_time] Skipping {symbol}: {e}")
            continue

        for sec_type in security_types:
            sec = data.get(sec_type, {})
            if not sec.get("has_trades"):
                continue
            for trade in sec.get("all_trades", []):
                if not trade.get("is_buy_trade") or not trade.get("is_done"):
                    continue
                closed_date = trade.get("closed_date")
                if not closed_date:
                    continue

                from datetime import datetime as dt
                try:
                    close_dt = dt.fromisoformat(closed_date)
                except (ValueError, TypeError):
                    continue

                pnl = trade.get("current_profit_loss", 0.0) or 0.0
                pnl_pct = trade.get("current_percent_profit_loss", 0.0) or 0.0
                is_win = pnl > 0

                month_key = close_dt.strftime("%Y-%m")
                q_num = (close_dt.month - 1) // 3 + 1
                quarter_key = f"{close_dt.year}-Q{q_num}"

                for bucket_key, buckets in ((month_key, monthly), (quarter_key, quarterly)):
                    if bucket_key not in buckets:
                        buckets[bucket_key] = {
                            "winning_trades": 0,
                            "losing_trades": 0,
                            "pnl_dollars": 0.0,
                            "pnl_pct_sum": 0.0,
                            "trade_count": 0,
                        }
                    b = buckets[bucket_key]
                    b["winning_trades"] += 1 if is_win else 0
                    b["losing_trades"] += 0 if is_win else 1
                    b["pnl_dollars"] += pnl
                    b["pnl_pct_sum"] += pnl_pct
                    b["trade_count"] += 1

    def _format_bucket(key, b, is_quarterly):
        decided = b["winning_trades"] + b["losing_trades"]
        avg_pct = round(b["pnl_pct_sum"] / b["trade_count"], 2) if b["trade_count"] else 0.0
        if is_quarterly:
            year, q = key.split("-")
            label = f"{q} {year}"
        else:
            from datetime import datetime as dt
            label = dt.strptime(key, "%Y-%m").strftime("%b %Y")
        return {
            "period": key,
            "label": label,
            "winning_trades": b["winning_trades"],
            "losing_trades": b["losing_trades"],
            "batting_average": round(b["winning_trades"] / decided, 3) if decided else 0.0,
            "pnl_dollars": round(b["pnl_dollars"], 2),
            "pnl_pct_avg": avg_pct,
        }

    monthly_list = [_format_bucket(k, v, False) for k, v in sorted(monthly.items())]
    quarterly_list = [_format_bucket(k, v, True) for k, v in sorted(quarterly.items())]

    log.info(f"[dashboard/pnl_over_time] {len(monthly_list)} months, {len(quarterly_list)} quarters")
    return jsonify({"monthly": monthly_list, "quarterly": quarterly_list})
