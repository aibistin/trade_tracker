# app/routes/web_routes.py
import re
from flask import Blueprint, flash, redirect, url_for
from datetime import datetime, timedelta
import pytz
import logging
from flask import render_template, redirect, request, url_for, flash
from sqlalchemy import select
from ..extensions import db
from app.utils import SYMBOLS_TO_EXCLUDE
from lib.trading_analyzer import TradingAnalyzer
web_bp = Blueprint("web", __name__)
log = logging.getLogger(__name__)
# web_logger = logging.getLogger('web_routes')


from ..models.models import (
    Security,
    TradeTransaction,
    get_trade_data_for_analysis_new,
)


@web_bp.route("/")
@web_bp.route("/index")
def index():
    log.info(f"[index] Home Page")
    stmt = (
        select(Security)
        .where(Security.symbol.notin_(SYMBOLS_TO_EXCLUDE))
        .order_by(Security.symbol)
    )
    all_securities = db.session.execute(stmt).scalars().all()

    # Filter out option symbols using regular expressions
    securities = [
        sec
        for sec in all_securities
        if not re.search(r"\s+\d{2}/\d{2}/\d{4}\s+\d+\.\d+\s+[A-Z]", sec.symbol)
    ]
    log.debug(f"[index] Securities[:3]: {securities[:3]}")
    return render_template("index.html", securities=securities)


@web_bp.route("/transaction/<int:transaction_id>")
@web_bp.route("/view_transaction/<int:transaction_id>")
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


@web_bp.route("/update_transaction/<int:transaction_id>", methods=["POST"])
def update_transaction(transaction_id):
    """Updates the reason, initial_stop_price, and projected_sell_price fields of a transaction."""

    log.info(f"[update_transaction] Updating transaction ID: {transaction_id}")

    transaction = db.session.get(TradeTransaction, transaction_id)
    if not transaction:
        log.error(f"[update_transaction] Transaction not found: {transaction_id}")
        return "Transaction not found", 404

    reason = request.form.get("reason")
    if reason is not None:
        transaction.reason = reason

    initial_stop_price = request.form.get("initial_stop_price")
    if initial_stop_price is not None:
        try:
            transaction.initial_stop_price = float(initial_stop_price)
        except (ValueError, TypeError):
            flash("Invalid Initial Stop Price. Please enter a number.", "error")
            log.error(f"Invalid Initial Stop Price: {initial_stop_price}")
            return redirect(url_for("web.view_transaction", transaction_id=transaction_id))

    projected_sell_price = request.form.get("projected_sell_price")
    if projected_sell_price is not None:
        try:
            transaction.projected_sell_price = float(projected_sell_price)
        except (ValueError, TypeError):
            flash("Invalid Projected Sell Price. Please enter a number.", "error")
            log.error(f"Invalid Projected Sell Price: {projected_sell_price}") 
            return redirect(url_for("web.view_transaction", transaction_id=transaction_id))

    log.info(f"Committing the update for transaction id: {transaction_id}")
    db.session.commit()
    flash("Transaction updated successfully!", "success")
    return redirect(url_for("web.view_transaction", transaction_id=transaction_id))

@web_bp.route("/recent_trades/<int:days>")
def recent_trades(days):
    """Fetches buy and sell transactions from the specified number of days,
    ordered by symbol and trade date, including the security name."""

    log.info("Inside Recent Trades route '/recent_trades'")
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


@web_bp.route("/trades/<string:symbol>")
def trades_by_symbol(symbol):
    """Fetches all buy and sell transactions for the given symbol, ordered by trade date."""

    log.info(f"Inside Trades By Symbol route '/trades/{symbol}'")
    transactions = (
        TradeTransaction.query.filter(
            TradeTransaction.action.in_(["B", "RS", "S"]),
            TradeTransaction.symbol == symbol,
        )
        .order_by(TradeTransaction.trade_date)
        .all()
    )
    log.debug(f"/trades/symbol Transactions: {transactions}")
    return render_template(
        "trades_by_symbol.html", transactions=transactions, symbol=symbol
    )


@web_bp.route("/trade/detail/<string:symbol>")
def trade_detail_by_symbol(symbol):
    """Detailed buy, sell, profit and loss transactions for the given symbol."""

    trade_transactions = get_trade_data_for_analysis_new(symbol)
    all_trade_stats = {}
    analyzer = TradingAnalyzer(symbol, trade_transactions)
    analyzer.analyze_trades()
    # Store results with symbol as key
    all_trade_stats = analyzer.get_profit_loss_data()[symbol]

    log.info(f"[Routes] Trade Detail for {symbol}: {all_trade_stats}")
    return render_template(
        "trade_detail_by_symbol.html",
        trade_stats=all_trade_stats,
        symbol=symbol,
    )


@web_bp.route("/trade_stats_summary")
def trade_stats_summary():
    """Fetches trade statistics summary and renders the template."""
    trade_stats = TradeTransaction.get_trade_stats_summary()
    return render_template("trade_stats_summary.html", trade_stats=trade_stats)


@web_bp.route("/open_positions/<string:stock_symbol>")
@web_bp.route("/open_trades/<string:stock_symbol>")
def open_positions(stock_symbol):
    """Fetches open positions for a given stock symbol."""
    log.info(f"[{stock_symbol}] Getting Open Positions")

    # Fetch trade data from the database
    trade_transactions = get_trade_data_for_analysis_new(stock_symbol)
    open_position_data = {}
    analyzer = TradingAnalyzer(stock_symbol, trade_transactions)
    analyzer.analyze_trades()
    try:
        open_position_data = analyzer.get_open_trades()
        log.info(f"[Routes][{stock_symbol}] Open position Data: {open_position_data}")
    except Exception as e:
        log.info(f"[Routes - open_trades] Error: [{stock_symbol}] {e}")
        open_position_data[stock_symbol] = {}

    return render_template(
        "open_trade_detail_by_symbol.html",
        open_position_data=open_position_data,
        stock_symbol=stock_symbol,
    )
