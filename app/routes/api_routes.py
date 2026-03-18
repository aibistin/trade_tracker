# app/routes/api_routes.py
import os
import logging

from flask import Blueprint, request, jsonify
from app.utils import filter_symbols
from lib.trading_analyzer import TradingAnalyzer
from lib.yfinance import YahooFinance

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
