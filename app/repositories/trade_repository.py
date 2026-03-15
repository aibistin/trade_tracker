# app/repositories/trade_repository.py
from sqlalchemy import func, case, select

from ..extensions import db
from ..models.models import Security, TradeTransaction, common_actions
from lib.constants import Action


def get_trade_stats_summary():
    """Fetches trade statistics summary from the database."""
    trade_summary = (
        select(
            TradeTransaction.symbol,
            func.sum(
                case(
                    (TradeTransaction.action == Action.SELL, TradeTransaction.quantity),
                    else_=0,
                )
            ).label("sell_quantity"),
            func.sum(
                case(
                    (TradeTransaction.action == Action.SELL, TradeTransaction.amount),
                    else_=0,
                )
            ).label("sell_amount"),
            func.avg(
                case(
                    (TradeTransaction.action == Action.SELL, TradeTransaction.price),
                    else_=0,
                )
            ).label("average_sell_price"),
            func.sum(
                case(
                    (TradeTransaction.action == Action.BUY, TradeTransaction.quantity),
                    else_=0,
                )
            ).label("buy_quantity"),
            func.sum(
                case(
                    (TradeTransaction.action == Action.BUY, TradeTransaction.amount),
                    else_=0,
                )
            ).label("buy_amount"),
            func.avg(
                case(
                    (TradeTransaction.action == Action.BUY, TradeTransaction.price),
                    else_=0,
                )
            ).label("average_buy_price"),
            (
                func.sum(
                    case(
                        (TradeTransaction.action == Action.BUY, TradeTransaction.amount),
                        else_=0,
                    )
                )
                + func.sum(
                    case(
                        (TradeTransaction.action == Action.SELL, TradeTransaction.amount),
                        else_=0,
                    )
                )
            ).label("profit_loss"),
        )
        .where(TradeTransaction.action.in_(common_actions))
        .group_by(TradeTransaction.symbol)
        .subquery()
    )

    stmt = (
        select(
            trade_summary.c.symbol,
            func.round(func.coalesce(trade_summary.c.buy_amount, 0), 2).label(
                "buy_amount"
            ),
            func.round(
                func.coalesce(trade_summary.c.average_buy_price, 0), 2
            ).label("average_buy_price"),
            func.coalesce(trade_summary.c.buy_quantity, 0).label("buy_quantity"),
            func.coalesce(trade_summary.c.sell_quantity, 0).label("sell_quantity"),
            func.round(func.coalesce(trade_summary.c.sell_amount, 0), 2).label(
                "sell_amount"
            ),
            func.round(
                func.coalesce(trade_summary.c.average_sell_price, 0), 2
            ).label("average_sell_price"),
            func.round(func.coalesce(trade_summary.c.profit_loss, 0), 2).label(
                "profit_loss"
            ),
            case(
                (
                    func.round(func.coalesce(trade_summary.c.profit_loss, 0), 2)
                    < 0,
                    "L",
                ),
                else_=case(
                    (
                        func.round(func.coalesce(trade_summary.c.profit_loss, 0), 2)
                        > 0,
                        "P",
                    ),
                    else_="E",
                ),
            ).label("win_lose"),
        )
        .where(trade_summary.c.buy_quantity == trade_summary.c.sell_quantity)
    )

    return db.session.execute(stmt).mappings().all()


def get_current_holdings(symbol=None):
    """
    Fetches current holdings (stocks where bought quantity exceeds sold quantity), sorted by symbol.
    Args:
        symbol (str, optional): If provided, fetches holdings only for this symbol. Otherwise, fetches all holdings.
    """
    symbol_names = (
        select(Security.symbol, Security.name)
        .order_by(Security.symbol)
        .cte("symbol_names")
    )

    buy_sum = (
        select(
            TradeTransaction.symbol,
            TradeTransaction.action,
            TradeTransaction.trade_type,
            TradeTransaction.label,
            func.sum(TradeTransaction.quantity).label("bsum"),
            func.abs(func.sum(TradeTransaction.amount)).label("bamount"),
        )
        .where(TradeTransaction.action.in_([Action.BUY, Action.REINVEST_SHARES, Action.BUY_TO_OPEN]))
        .group_by(TradeTransaction.symbol, TradeTransaction.trade_type)
        .order_by(TradeTransaction.symbol, TradeTransaction.trade_type)
        .cte("buy_sum")
    )

    sell_sum = (
        select(
            TradeTransaction.symbol,
            TradeTransaction.action,
            TradeTransaction.trade_type,
            TradeTransaction.label,
            func.sum(TradeTransaction.quantity).label("ssum"),
            func.sum(TradeTransaction.amount).label("samount"),
        )
        .where(TradeTransaction.action.in_([Action.SELL, Action.SELL_TO_CLOSE, Action.EXPIRED, Action.EXERCISED]))
        .group_by(TradeTransaction.symbol, TradeTransaction.trade_type)
        .order_by(TradeTransaction.symbol, TradeTransaction.trade_type)
        .cte("sell_sum")
    )

    result = (
        select(
            buy_sum.c.symbol,
            buy_sum.c.trade_type,
            (buy_sum.c.bsum - func.coalesce(sell_sum.c.ssum, 0)).label("quantity"),
            case(
                (buy_sum.c.bsum > 0, func.round(buy_sum.c.bamount / buy_sum.c.bsum, 2)),
                else_=0
            ).label("avg_price"),
            (func.coalesce(sell_sum.c.samount, 0) - buy_sum.c.bamount).label("cost_basis"),
        )
        .select_from(buy_sum)
        .outerjoin(sell_sum, (buy_sum.c.symbol == sell_sum.c.symbol) & (buy_sum.c.trade_type == sell_sum.c.trade_type))
        .where((buy_sum.c.bsum > sell_sum.c.ssum) | (sell_sum.c.ssum == None))
        .join(symbol_names, buy_sum.c.symbol == symbol_names.c.symbol)
        .add_columns(symbol_names.c.name.label("security_name"))
    )

    if symbol:
        result = result.where(buy_sum.c.symbol == symbol)
    else:
        result = result.order_by(buy_sum.c.symbol)

    return db.session.execute(result).all()


def get_current_holdings_symbols():
    """Returns a list of unique [symbol, name] pairs from current holdings."""
    current_holdings = get_current_holdings()
    seen = set()
    result = []
    for symbol, trade_type, shares, price, pl, name in current_holdings:
        if symbol not in seen:
            seen.add(symbol)
            result.append([symbol, name])
    return result


def get_raw_trade_data(symbol):
    stmt = (
        select(
            TradeTransaction.id,
            TradeTransaction.symbol,
            TradeTransaction.action,
            TradeTransaction.trade_type,
            TradeTransaction.label,
            TradeTransaction.trade_date,
            TradeTransaction.expiration_date,
            TradeTransaction.quantity,
            TradeTransaction.price,
            TradeTransaction.target_price,
            TradeTransaction.amount,
            TradeTransaction.account,
            TradeTransaction.reason,
            TradeTransaction.initial_stop_price,
            TradeTransaction.projected_sell_price,
        )
        .where(
            TradeTransaction.symbol == symbol,
            TradeTransaction.action.in_(common_actions),
        )
        .order_by(
            TradeTransaction.trade_date,
            TradeTransaction.action,
            TradeTransaction.trade_type,
            TradeTransaction.account,
        )
    )
    return db.session.execute(stmt).mappings().all()


def get_trade_data_for_analysis(stock_symbol):
    """Returns all trade transactions for a given stock symbol."""
    return [dict(row) for row in get_raw_trade_data(stock_symbol)]


def get_all_securities():
    """Fetches all securities from the database."""
    stmt = select(Security.symbol, Security.name).order_by(Security.symbol)
    return db.session.execute(stmt).all()
