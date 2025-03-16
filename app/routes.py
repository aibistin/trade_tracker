from .models.models import (
    Security,
    TradeTransaction,
    get_all_securities,
    get_current_holdings,
    get_current_holdings_symbols,
    get_trade_data_for_analysis,
)

from lib.trading_analyzer import TradingAnalyzer
from lib.yfinance import YahooFinance
from sqlalchemy import select
from app import app
from flask import Flask, render_template, request
from flask import jsonify, flash, redirect, url_for
from datetime import datetime, timedelta
import dumper
import os
import pytz
import re
from flask_sqlalchemy import SQLAlchemy
from .extensions import db
from sqlalchemy.orm import aliased

# List of unwanted Stock symbols
symbols_to_exclude = [
    "",
    "14067D508",
    "14067D607",
    "873379101",
    "BMY/R",
    "CGRN",
    "G06242104",
    "MMDA1",
    "FAKE1",
    "FAKE2",
    "FAKE3",
]


def _filtered_symbols(all_symbol_names):
    """Returns a list of symbols that are not in the exclusion list and do not match the unwanted patterns."""
    filtered_symbols = [
        (symbol, name)
        for (symbol, name) in all_symbol_names
        if symbol
        and len(symbol) < 6
        and not re.search(r"\s+\d{2}/\d{2}/\d{4}\s+\d+\.\d+\s+[A-Z]", symbol)
        and not symbol in symbols_to_exclude
    ]
    return filtered_symbols


print("[routes.py] Flask Env  = " + os.environ.get("FLASK_ENV"))

# app = Flask(__name__)
print("Inside Routes name: " + __name__)


# Create the database tables (only needed once)
with app.app_context():
    db.create_all()


@app.before_request
def before_request():
    print(f"Before request: {request.method} {request.url}")


@app.route("/")
@app.route("/index")
def index():
    stmt = (
        select(Security)
        .where(Security.symbol.notin_(symbols_to_exclude))
        .order_by(Security.symbol)
    )
    all_securities = db.session.execute(stmt).scalars().all()

    # Filter out option symbols using regular expressions
    securities = [
        sec
        for sec in all_securities
        if not re.search(r"\s+\d{2}/\d{2}/\d{4}\s+\d+\.\d+\s+[A-Z]", sec.symbol)
    ]
    print(f"[index] Securities: {securities}")
    return render_template("index.html", securities=securities)


@app.route("/transaction/<int:transaction_id>")
@app.route("/view_transaction/<int:transaction_id>")
def view_transaction(transaction_id):
    transaction = db.session.get(TradeTransaction, transaction_id)
    if not transaction:
        return "Transaction not found", 404
    return render_template(
        "transaction_detail.html",
        transaction_id=transaction_id,
        transaction=transaction,
        stock_symbol=transaction.symbol,
    )


@app.route("/update_transaction/<int:transaction_id>", methods=["POST"])
def update_transaction(transaction_id):
    """Updates the reason, initial_stop_price, and projected_sell_price fields of a transaction."""

    print(f"[update_transaction] Updating transaction ID: {transaction_id}")

    try:
        transaction = db.session.execute( select(TradeTransaction).where(TradeTransaction.id == transaction_id))
    except Exception as e:
        print(f"[update_transaction] Select Error: {e}")
        return "Transaction not found", 404


    transaction.reason = request.form.get("reason")
    try:
        transaction.initial_stop_price = float(request.form.get("initial_stop_price"))
    except (ValueError, TypeError):
        flash("Invalid Initial Stop Price. Please enter a number.", "error")
        return redirect(url_for("view_transaction", transaction_id=transaction_id))

    try:
        transaction.projected_sell_price = float(
            request.form.get("projected_sell_price")
        )
    except (ValueError, TypeError):
        flash("Invalid Projected Sell Price. Please enter a number.", "error")
        return redirect(url_for("view_transaction", transaction_id=transaction_id))

    print(f"Committing the update for transaction id: {transaction_id}")
    db.session.commit()
    flash("Transaction updated successfully!", "success")
    return redirect(url_for("view_transaction", transaction_id=transaction_id))


@app.route("/recent_trades/<int:days>")
def recent_trades(days):
    """Fetches buy and sell transactions from the specified number of days,
    ordered by symbol and trade date, including the security name."""

    print("Inside Recent Trades route '/recent_trades'")
    days_ago = datetime.now(pytz.timezone("America/New_York")) - timedelta(days=days)

    transactions = (
        db.session.query(TradeTransaction, Security.name)  # Query both tables
        # Join on symbol
        .join(Security, TradeTransaction.symbol == Security.symbol)
        .filter(
            TradeTransaction.action.in_(["B", "RS", "S"]),
            TradeTransaction.trade_date > days_ago,
        )
        .order_by(
            TradeTransaction.symbol,
            # TradeTransaction.trade_date.desc(),
            TradeTransaction.trade_date,
            TradeTransaction.action,
        )
        .all()
    )
    return render_template("recent_trades.html", transactions=transactions, days=days)


@app.route("/trades/<string:symbol>")
def trades_by_symbol(symbol):
    """Fetches all buy and sell transactions for the given symbol, ordered by trade date."""

    transactions = (
        TradeTransaction.query.filter(
            TradeTransaction.action.in_(["B", "RS", "S"]),
            TradeTransaction.symbol == symbol,
        )
        .order_by(TradeTransaction.trade_date)
        .all()
    )
    return render_template(
        "trades_by_symbol.html", transactions=transactions, symbol=symbol
    )


@app.route("/trade/detail/<string:symbol>")
def trade_detail_by_symbol(symbol):
    """Detailed buy, sell, profit and loss transactions for the given symbol."""

    trade_transactions = get_trade_data_for_analysis(symbol)
    all_trade_stats = {}
    analyzer = TradingAnalyzer(symbol, trade_transactions)
    analyzer.analyze_trades()
    # Store results with symbol as key
    all_trade_stats = analyzer.get_profit_loss_data()[symbol]

    print(f"[Routes] Trade Detail for {symbol}: {all_trade_stats}")
    return render_template(
        "trade_detail_by_symbol.html",
        trade_stats=all_trade_stats, symbol=symbol,
    )


@app.route("/trade_stats_summary")
def trade_stats_summary():
    """Fetches trade statistics summary and renders the template."""
    trade_stats = TradeTransaction.get_trade_stats_summary()
    return render_template("trade_stats_summary.html", trade_stats=trade_stats)


# @app.route("/trade_stats_pl")
# def trade_stats_pl(symbol):
#     """Fetches trade statistics summary and renders the template."""

#     # Fetch trade data from the database
#     trade_transactions = get_trade_data_for_analysis(symbol)

#     # Analyze trades for each symbol
#     all_trade_stats = {}
#     # Analyze for each symbol separately
#     analyzer = TradingAnalyzer({symbol: trade_transactions})
#     analyzer.analyze_trades()
#     # Store results with symbol as key
#     all_trade_stats = analyzer.get_profit_loss_data()

#     print(f"[Routes] Trade Stats: {all_trade_stats}")
#     return render_template("trade_stats_pl.html", trade_stats=all_trade_stats)


# Ajax
@app.route("/get_stock_data/<string:stock_symbol>")
def get_stock_data(stock_symbol):
    """Fetches stock data from Yahoo Finance and returns it as JSON."""
    print(f"[{stock_symbol}] Getting Yahoo Data")
    yf = YahooFinance(stock_symbol)
    yf.get_stock_data()
    stock_data = yf.get_results()
    print(f"[{stock_symbol}] Yahoo Data: {stock_data}")
    return jsonify(stock_data)


@app.route("/open_positions/<string:stock_symbol>")
@app.route("/open_trades/<string:stock_symbol>")
def open_positions(stock_symbol):
    """Fetches open positions for a given stock symbol."""
    print(f"[{stock_symbol}] Getting Open Positions")

    # Fetch trade data from the database
    trade_transactions = get_trade_data_for_analysis(stock_symbol)
    open_position_data = {}
    analyzer = TradingAnalyzer(stock_symbol, trade_transactions)
    analyzer.analyze_trades()
    try:
        open_position_data = analyzer.get_open_trades()
        print(f"[Routes][{stock_symbol}] Open position Data: {open_position_data}")
    except Exception as e:
        print(f"[Routes - open_trades] Error: [{stock_symbol}] {e}")
        open_position_data[stock_symbol] = {}

    return render_template(
        "open_trade_detail_by_symbol.html",
        open_position_data=open_position_data,
        stock_symbol=stock_symbol,
    )

# API
@app.route("/trade/symbols_json")
def get_symbols():

    all_symbol_names = get_all_securities()

    # print(f"[get_symbols] All Symbols: {all_symbol_names}")
    symbols_names = _filtered_symbols(all_symbol_names)
    print(f"[get_symbols] symbols_names: {symbols_names}")
    return jsonify(symbols_names)


@app.route("/trade/current_holdings_json")
def get_current_holdings_json():
    """Get current holdings from the database and return as JSON."""
    current_holdings = get_current_holdings()
    print(f"[get_current_holdings_json] Current Holdings: {current_holdings}")
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

    print(f"[get_current_holdings_json] Holdings list: {holdings_list}")

    return jsonify(holdings_list)


@app.route("/trade/current_holdings_symbols_json")
def get_current_holdings_symbols_json():
    """Get current holdings, symbols only from the database and return as JSON."""
    current_symbols = get_current_holdings_symbols()
    print(f"[get_current_holdings_symbols_json] Current Symbols: {current_symbols}")

    return jsonify(current_symbols)


@app.route("/trades/<string:scope>/json/<string:stock_symbol>")
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

    print(f"[{stock_symbol}] Getting {scope.capitalize()} Positions JSON")

    trade_record = {
        "stock_symbol": stock_symbol,
        "transaction_stats": {},
        "requested": f"{scope}_trades",
    }
   
    trade_transactions = get_trade_data_for_analysis(stock_symbol)
    analyzer = TradingAnalyzer(stock_symbol, trade_transactions)

    getter_methods = {
        "all": analyzer.get_profit_loss_data,
        "open": analyzer.get_open_trades,
        "closed": analyzer.get_closed_trades,
    }

    # Get the appropriate method based on the scope
    getter_method = getter_methods.get(scope, analyzer.get_profit_loss_data)

    analyzer.analyze_trades()
    trade_record["transaction_stats"] = getter_method()

    print(f"[Routes] {scope.capitalize()} positions for {stock_symbol}: {trade_record}")
    return jsonify(trade_record)


if __name__ == "__main__":
    app.run(debug=True)  # Run the Flask app in debug mode
