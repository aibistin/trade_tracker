# app/routes/web_routes.py
import logging
from datetime import datetime, timedelta
import pytz
from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import select
from ..extensions import db
from app.utils import SYMBOLS_TO_EXCLUDE, is_option_symbol
from lib.trading_analyzer import TradingAnalyzer

web_bp = Blueprint("web", __name__)
log = logging.getLogger(__name__)

from ..models.models import Security, TradeTransaction
from ..repositories.trade_repository import get_trade_data_for_analysis, get_trade_stats_summary
from ..services.trade_service import validate_trade_update
from ..services.analysis_service import clear_analysis_cache
from lib.constants import Action


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

    # Filter out option symbols
    securities = [sec for sec in all_securities if not is_option_symbol(sec.symbol)]
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

    data = {
        k: request.form.get(k)
        for k in ("reason", "initial_stop_price", "projected_sell_price")
        if request.form.get(k) is not None
    }

    errors = validate_trade_update(data)
    if errors:
        for field, msg in errors.items():
            flash(f"{field}: {msg}", "error")
            log.error(f"[update_transaction] Validation error — {field}: {msg}")
        return redirect(url_for("web.view_transaction", transaction_id=transaction_id))

    if "reason" in data:
        transaction.reason = data["reason"]
    if "initial_stop_price" in data:
        transaction.initial_stop_price = float(data["initial_stop_price"])
    if "projected_sell_price" in data:
        transaction.projected_sell_price = float(data["projected_sell_price"])

    log.info(f"Committing the update for transaction id: {transaction_id}")
    db.session.commit()
    # Field edits don't change the cache's data-version token — clear explicitly
    clear_analysis_cache()
    flash("Transaction updated successfully!", "success")
    return redirect(url_for("web.view_transaction", transaction_id=transaction_id))

@web_bp.route("/recent_trades/<int:days>")
def recent_trades(days):
    """Fetches buy and sell transactions from the specified number of days,
    ordered by symbol and trade date, including the security name."""

    log.info("Inside Recent Trades route '/recent_trades'")
    days_ago = datetime.now(pytz.timezone("America/New_York")) - timedelta(days=days)

    stmt = (
        select(TradeTransaction, Security.name)
        .join(Security, TradeTransaction.symbol == Security.symbol)
        .where(
            TradeTransaction.action.in_([Action.BUY, Action.REINVEST_SHARES, Action.SELL]),
            TradeTransaction.trade_date > days_ago,
        )
        .order_by(
            TradeTransaction.symbol,
            TradeTransaction.trade_date,
            TradeTransaction.action,
        )
    )
    transactions = db.session.execute(stmt).all()
    return render_template("recent_trades.html", transactions=transactions, days=days)


@web_bp.route("/trades/<string:symbol>")
def trades_by_symbol(symbol):
    """Fetches all buy and sell transactions for the given symbol, ordered by trade date."""

    log.info(f"Inside Trades By Symbol route '/trades/{symbol}'")
    stmt = (
        select(TradeTransaction)
        .where(
            TradeTransaction.action.in_([Action.BUY, Action.REINVEST_SHARES, Action.SELL]),
            TradeTransaction.symbol == symbol,
        )
        .order_by(TradeTransaction.trade_date)
    )
    transactions = db.session.execute(stmt).scalars().all()
    log.debug(f"/trades/symbol Transactions: {transactions}")
    return render_template(
        "trades_by_symbol.html", transactions=transactions, symbol=symbol
    )


@web_bp.route("/trade/detail/<string:symbol>")
def trade_detail_by_symbol(symbol):
    """Detailed buy, sell, profit and loss stock transactions for the given symbol."""

    trade_transactions = get_trade_data_for_analysis(symbol)
    analyzer = TradingAnalyzer(symbol, trade_transactions)
    analyzer.analyze_trades()
    stock_data = analyzer.get_profit_loss_data()["stock"]

    if not stock_data["has_trades"]:
        return f"No stock trades found for {symbol}", 404

    log.info(f"[Routes] Trade Detail for {symbol}")
    return render_template(
        "trade_detail_by_symbol.html",
        trade_stats={
            "summary": stock_data["summary"],
            "all_trades": stock_data["all_buy_trades"],
        },
        symbol=symbol,
    )


@web_bp.route("/trade_stats_summary")
def trade_stats_summary():
    """Fetches trade statistics summary and renders the template."""
    trade_stats = get_trade_stats_summary()
    return render_template("trade_stats_summary.html", trade_stats=trade_stats)


