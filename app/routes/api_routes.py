# app/routes/api_routes.py
import os
import logging

from flask import Blueprint, request, jsonify
from app.utils import filter_symbols
from lib.trading_analyzer import TradingAnalyzer
from lib.yfinance import YahooFinance

api_bp = Blueprint("api", __name__)
log = logging.getLogger(__name__)

from ..models.models import (
    get_all_securities,
    get_current_holdings,
    get_current_holdings_symbols,
    get_trade_data_for_analysis_new,
)


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

    trade_transactions = get_trade_data_for_analysis_new(stock_symbol)

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

    trade_transactions = get_trade_data_for_analysis_new(stock_symbol)
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
