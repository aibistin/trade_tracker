from .models.models import (
    Security,
    TradeTransaction,
    get_current_holdings,
    get_raw_trade_data,
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
    )


# @app.route('/update_transaction/<int:transaction_id>', methods=['GET'])
# def update_transaction(transaction_id):
#     transaction = db.session.get(
#         TradeTransaction, transaction_id)
#     if not transaction:
#         return "Transaction not found", 404
#     return render_template('update_transaction.html', transaction_id=transaction_id, transaction=transaction)


@app.route("/update_transaction/<int:transaction_id>", methods=["POST"])
def update_transaction(transaction_id):
    """Updates the reason, initial_stop_price, and projected_sell_price fields of a transaction."""

    transaction = TradeTransaction.query.get_or_404(transaction_id)

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
    """Detailed buy, sell, profit and lost  transactions for the given symbol."""

    raw_trade_data = get_raw_trade_data(symbol)
    # Group data by symbol
    data_dict = {}
    for id, symbol, action, trade_date, quantity, price, amount in raw_trade_data:
        if symbol not in data_dict:
            data_dict[symbol] = []
        data_dict[symbol].append(
            {
                "Id": id,
                "Action": action,
                "Trade Date": trade_date,
                "Quantity": quantity,
                "Price": price,
                "Amount": amount,
            }
        )

    # Analyze trades for each symbol
    all_trade_stats = {}
    for symbol, trades in data_dict.items():
        # Analyze for each symbol separately
        analyzer = TradingAnalyzer({symbol: trades})
        analyzer.analyze_trades()
        # Store results with symbol as key
        all_trade_stats[symbol] = analyzer.get_results()[symbol]

    print(f"[Routes] Trade Detail for {symbol}: {all_trade_stats}")
    return render_template(
        "trade_detail_by_symbol.html", trade_stats=all_trade_stats, symbol=symbol
    )


@app.route("/trade_stats_summary")
def trade_stats_summary():
    """Fetches trade statistics summary and renders the template."""
    trade_stats = TradeTransaction.get_trade_stats_summary()
    return render_template("trade_stats_summary.html", trade_stats=trade_stats)


@app.route("/trade_stats_pl")
def trade_stats_pl():
    """Fetches trade statistics summary and renders the template."""

    # Fetch raw data from the database
    raw_trade_data = get_raw_trade_data(symbol)

    # Group data by symbol
    data_dict = {}
    for id, symbol, action, trade_date, quantity, price, amount in raw_trade_data:
        if symbol not in data_dict:
            data_dict[symbol] = []
        data_dict[symbol].append(
            {
                "Id": id,
                "Action": action,
                "Trade Date": trade_date,
                "Quantity": quantity,
                "Price": price,
                "Amount": amount,
            }
        )

    # Analyze trades for each symbol
    all_trade_stats = {}
    for symbol, trades in data_dict.items():
        # Analyze for each symbol separately
        analyzer = TradingAnalyzer({symbol: trades})
        analyzer.analyze_trades()
        # Store results with symbol as key
        all_trade_stats[symbol] = analyzer.get_results()[symbol]

    print(f"[Routes] Trade Stats: {all_trade_stats}")
    return render_template("trade_stats_pl.html", trade_stats=all_trade_stats)


@app.route("/current_holdings")
@app.route("/open_positions")
@app.route("/open_trades")
def open_positions():
    """Fetches all open trades."""
    current_holdings = get_current_holdings()
    print(f"Open Trades: {current_holdings}")
    return render_template("current_holdings.html", current_holdings=current_holdings)


@app.route("/open_positions/<string:symbol>")
@app.route("/open_trades/<string:symbol>")
def open_positions_symbol(symbol):
    """Fetches all open trades for a given Stock ticker."""
    current_holdings = get_current_holdings(symbol)
    print(f"Open Trades: {current_holdings}")
    return render_template(
        "current_holdings.html", symbol=symbol, current_holdings=current_holdings
    )


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


@app.route("/open_positions_json/<string:stock_symbol>")
def get_open_positions_json(stock_symbol):
    """Fetches open positions for a given stock symbol and returns it as JSON."""
    print(f"[{stock_symbol}] Getting Open Positions JSON")

    raw_trade_data = get_raw_trade_data(stock_symbol)

    # Group data by symbol
    data_dict = {stock_symbol: []}
    for id, symbol, action, trade_date, quantity, price, amount in raw_trade_data:
        data_dict[symbol].append(
            {
                "Id": id,
                "Action": action,
                "Trade Date": trade_date,
                "Quantity": quantity,
                "Price": price,
                "Amount": amount,
            }
        )

    open_positions = {}
    analyzer = TradingAnalyzer(data_dict)
    analyzer.analyze_trades()
    open_positions = analyzer.get_open_trades()[stock_symbol]

    print(f"[{stock_symbol}] Open positions: {open_positions}")
    return jsonify({stock_symbol: open_positions})


if __name__ == "__main__":
    app.run(debug=True)  # Run the Flask app in debug mode
