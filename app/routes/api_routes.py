# app/routes/api_routes.py
import json, os
from flask import Blueprint, request
from app.utils import filter_symbols
import logging

from flask import Blueprint, jsonify
from flask_limiter import Limiter
from lib.trading_analyzer import TradingAnalyzer
from lib.yfinance import YahooFinance
from flask_limiter.util import get_remote_address

api_bp = Blueprint("api", __name__)
log = logging.getLogger(__name__)

# limiter = Limiter(
#     api_bp,
#     key_func=get_remote_address,  # Uses client IP address #type: ignore
#     default_limits=["200 per day", "50 per hour"],
# )

from ..models.models import (
    get_all_securities,
    get_current_holdings,
    get_current_holdings_symbols,
    get_trade_data_for_analysis_new,
)


# TODO Add proper authentication
def valid_api_key(request):
    # Implement your API key validation logic
    log.debug(f"[valid_api_key] FLASK_ENV: {os.environ.get('FLASK_ENV')}")
    if os.environ.get("FLASK_ENV") == "dev":
        log.debug(f"[valid_api_key] Dev Environment- No API key check")
        return True
    return request.headers.get("X-API-KEY") == os.environ.get("API_SECRET_KEY")


@api_bp.before_request
def require_api_key():
    log.info(f"[require_api_key] Before request: {request.method} {request.url}")
    # if request.endpoint != "api.get_stock_data":  # Exclude public endpoints
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
    log.debug(f"[get_current_holdings_json] Current Holdings[:3]: {current_holdings[:3]}")
    # Convert the tuple data into a list of dictionaries with named fields
    holdings_list = [
        {
            "symbol": symbol,
            "shares": shares,
            "average_price": price,
            "profit_loss": pl,
            "name": name,
        }
        for symbol, shares, price, pl, name in current_holdings
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
    Valid values for scope are 'all', 'open' or 'closed'."""

    if scope not in ["all", "open", "closed"]:
        return (
            jsonify(
                {"error": 'Invalid scope. Must be either "all", "open" or "closed"'}
            ),
            400,
        )

    # log.debug(f"[{stock_symbol}] Getting {scope.capitalize()} Positions JSON")

    trade_record = {
        "stock_symbol": stock_symbol,
        "transaction_stats": {},
        "requested": f"{scope}_trades",
    }

    trade_transactions = get_trade_data_for_analysis_new(stock_symbol)
    # log.debug(f"[Routes][get_positions_json] raw_data: {trade_transactions}")

    analyzer = TradingAnalyzer(stock_symbol, trade_transactions)

    # getter_methods = {
    #     "all": analyzer.get_profit_loss_data_json,
    #     # "open": analyzer.get_open_trades,
    #     # TODO add new method to trading_analyzer.py
    #     "open": analyzer.get_profit_loss_data_json,
    #     # "closed": analyzer.get_closed_trades,
    #     # TODO add new method to trading_analyzer.py
    #     "closed": analyzer.get_profit_loss_data_json,
    # }

    # Get the appropriate method based on the scope
    # getter_method = getter_methods.get(scope, analyzer.get_profit_loss_data_json)

    analyzer.analyze_trades(status=scope)
    trade_record["transaction_stats"] = analyzer.get_profit_loss_data_json()

    # log.debug(
    #     f"[Routes] {scope.capitalize()} positions for {stock_symbol}: {json.dumps(trade_record, sort_keys=True, indent=2)}"
    # )
    return jsonify(trade_record)
