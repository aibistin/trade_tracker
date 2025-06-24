# app/models/models.py
from sqlalchemy import func, case, cast, Numeric, select

# from app import db
from ..extensions import db

#TODO Not handling "BC" (Buy to Close) and "SO" (Sell to Open)
# RS = Reinvest Shares
common_actions = ["B", "BO", "EE","RS", "S","SC"]


class Security(db.Model):
    symbol = db.Column(db.String(30), primary_key=True)
    name = db.Column(db.String(80), nullable=False)


class TradeTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(30), db.ForeignKey("security.symbol"), nullable=False)
    action = db.Column(db.String(3), nullable=False)
    trade_type = db.Column(db.String(1), nullable=False)  # 'L', 'S', 'C', 'P', 'O'
    label = db.Column(db.String(40), default="")  # Option Label
    trade_date = db.Column(db.DateTime, nullable=False)
    expiration_date = db.Column(db.DateTime)  # Expiration date for options
    reason = db.Column(db.String(80), default="")
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    target_price = db.Column(db.Float)
    amount = db.Column(db.Float, nullable=False)
    initial_stop_price = db.Column(db.Float)
    projected_sell_price = db.Column(db.Float)
    account = db.Column(db.String(1), nullable=False)  # 'C', 'R', 'I'

    security = db.relationship(
        "Security", backref=db.backref("transactions", lazy=True)
    )

    @staticmethod
    def get_trade_stats_summary():
        """Fetches trade statistics summary from the database."""
        trade_summary = (
            db.session.query(
                TradeTransaction.symbol,
                func.sum(
                    case(
                        (TradeTransaction.action == "S", TradeTransaction.quantity),
                        else_=0,
                    )
                ).label("sell_quantity"),
                func.sum(
                    case(
                        (TradeTransaction.action == "S", TradeTransaction.amount),
                        else_=0,
                    )
                ).label("sell_amount"),
                func.avg(
                    case(
                        (TradeTransaction.action == "S", TradeTransaction.price),
                        else_=0,
                    )
                ).label("average_sell_price"),
                func.sum(
                    case(
                        (TradeTransaction.action == "B", TradeTransaction.quantity),
                        else_=0,
                    )
                ).label("buy_quantity"),
                func.sum(
                    case(
                        (TradeTransaction.action == "B", TradeTransaction.amount),
                        else_=0,
                    )
                ).label("buy_amount"),
                func.avg(
                    case(
                        (TradeTransaction.action == "B", TradeTransaction.price),
                        else_=0,
                    )
                ).label("average_buy_price"),
                (
                    func.sum(
                        case(
                            (TradeTransaction.action == "B", TradeTransaction.amount),
                            else_=0,
                        )
                    )
                    + func.sum(
                        case(
                            (TradeTransaction.action == "S", TradeTransaction.amount),
                            else_=0,
                        )
                    )
                ).label("profit_loss"),
            )
            .filter(TradeTransaction.action.in_(common_actions))
            .group_by(TradeTransaction.symbol)
            .subquery()
        )

        result = (
            db.session.query(
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
            .filter(trade_summary.c.buy_quantity == trade_summary.c.sell_quantity)
            .all()
        )

        return result

    # TODO Not being called. Remove
    def get_open_positions():
        """Fetches open positions (where bought quantity exceeds sold quantity)."""

        buy_sum = (
            select(
                TradeTransaction.symbol,
                TradeTransaction.action,
                TradeTransaction.trade_type,
                TradeTransaction.label,
                TradeTransaction.expiration_date,
                TradeTransaction.target_price,
                func.sum(TradeTransaction.quantity).label("bsum"),
                func.abs(func.sum(TradeTransaction.amount)).label("bamount"),
            )
            .where(TradeTransaction.action.in_(["B", "RS", "BO"]))
            .group_by(TradeTransaction.symbol, TradeTransaction.trade_type)
            .order_by(TradeTransaction.symbol, TradeTransaction.trade_type)
            .cte("buy_sum")
        )

        sell_sum = (
            select(
                TradeTransaction.symbol,
                TradeTransaction.action,
                func.sum(TradeTransaction.quantity).label("ssum"),
                func.sum(TradeTransaction.amount).label("samount"),
            )
            .where(TradeTransaction.action.in_(["S", "SC"]))
            .group_by(TradeTransaction.symbol, TradeTransaction.trade_type)
            .order_by(TradeTransaction.symbol, TradeTransaction.trade_type)
            .cte("sell_sum")
        )

        result = (
            select(buy_sum)
            .outerjoin(sell_sum, buy_sum.c.symbol == sell_sum.c.symbol)
            .where((buy_sum.c.bsum > sell_sum.c.ssum) | (sell_sum.c.ssum == None))
        )

        open_positions = db.session.execute(result).all()
        return open_positions


# trade_type
# label
# expiration_date
# target_price
# TradeTransaction.symbol,
# TradeTransaction.action,
# TradeTransaction.trade_type,
# TradeTransaction.label,
# TradeTransaction.expiration_date,
# TradeTransaction.target_price,


# def get_current_holdings(symbol=None):
#     """
#     Fetches current holdings (stocks where bought quantity exceeds sold quantity), sorted by symbol.
#     Args:
#         symbol (str, optional): If provided, fetches holdings only for this symbol. Otherwise, fetches all holdings.
#     """
#     symbol_names = (
#         db.session.query(Security.symbol, Security.name)
#         .order_by(Security.symbol)
#         .cte("symbol_names")
#     )

#     buy_sum = (
#         select(
#             TradeTransaction.symbol,
#             TradeTransaction.action,
#             TradeTransaction.trade_type,
#             TradeTransaction.label,
#             func.sum(TradeTransaction.quantity).label("bsum"),
#             func.avg(TradeTransaction.price).label("bprice"),  # Added average buy price
#             func.abs(func.sum(TradeTransaction.amount)).label("bamount"),
#         )
#         .where(TradeTransaction.action.in_(["B", "RS", "BO"]))
#         .group_by(TradeTransaction.symbol, TradeTransaction.trade_type)
#         .order_by(TradeTransaction.symbol, TradeTransaction.trade_type)
#         .cte("buy_sum")
#     )

#     sell_sum = (
#         select(
#             TradeTransaction.symbol,
#             TradeTransaction.action,
#             TradeTransaction.trade_type,
#             TradeTransaction.label,
#             func.sum(TradeTransaction.quantity).label("ssum"),
#             func.sum(TradeTransaction.amount).label("samount"),
#         )
#         .where(TradeTransaction.action.in_(["S", "SC"]))
#         .group_by(TradeTransaction.symbol, TradeTransaction.trade_type)
#         .order_by(TradeTransaction.symbol, TradeTransaction.trade_type)
#         .cte("sell_sum")
#     )

#     result = (
#         select(
#             buy_sum.c.symbol,
#             (buy_sum.c.bsum - func.coalesce(sell_sum.c.ssum, 0)).label("quantity"),
#             buy_sum.c.bprice.label("avg_price"),
#             (func.coalesce(sell_sum.c.samount, 0) - buy_sum.c.bamount).label(
#                 "cost_basis"
#             ),
#         )
#         .select_from(buy_sum)
#         .outerjoin(sell_sum, buy_sum.c.symbol == sell_sum.c.symbol)
#         .where((buy_sum.c.bsum > sell_sum.c.ssum) | (sell_sum.c.ssum == None))
#         # .order_by(buy_sum.c.symbol)  # Add sorting here
#         .join(symbol_names, buy_sum.c.symbol == symbol_names.c.symbol)
#         .add_columns(symbol_names.c.name.label("security_name"))
#     )

#     # current_holdings = db.session.execute(result).all()
#     # return current_holdings
#     # Apply filter if symbol is provided
#     if symbol:
#         result = result.where(buy_sum.c.symbol == symbol)
#     else:
#         result = result.order_by(buy_sum.c.symbol)

#     current_holdings = db.session.execute(result).all()
#     return current_holdings

def get_current_holdings(symbol=None):
    """
    Fetches current holdings (stocks where bought quantity exceeds sold quantity), sorted by symbol.
    Args:
        symbol (str, optional): If provided, fetches holdings only for this symbol. Otherwise, fetches all holdings.
    """
    symbol_names = (
        db.session.query(Security.symbol, Security.name)
        .order_by(Security.symbol)
        .cte("symbol_names")
    )

            # func.avg(TradeTransaction.price).label("bprice"),  # Added average buy price
        
    buy_sum = (
        select(
            TradeTransaction.symbol,
            TradeTransaction.action,
            TradeTransaction.trade_type,
            TradeTransaction.label,
            func.sum(TradeTransaction.quantity).label("bsum"),
            # Replace func.avg with weighted average calculation
            func.abs(func.sum(TradeTransaction.amount)).label("bamount"),

        )
        .where(TradeTransaction.action.in_(["B", "RS", "BO"]))
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
        .where(TradeTransaction.action.in_(["S", "SC"]))
        .group_by(TradeTransaction.symbol, TradeTransaction.trade_type)
        .order_by(TradeTransaction.symbol, TradeTransaction.trade_type)
        .cte("sell_sum")
    )

    result = (
        select(
            buy_sum.c.symbol,
            (buy_sum.c.bsum - func.coalesce(sell_sum.c.ssum, 0)).label("quantity"),
            # Calculate weighted average: total amount / total quantity
            case(
                (buy_sum.c.bsum > 0, func.round(buy_sum.c.bamount / buy_sum.c.bsum, 2)),
                else_=0
            ).label("avg_price"),
            (func.coalesce(sell_sum.c.samount, 0) - buy_sum.c.bamount).label("cost_basis"),
        )
        .select_from(buy_sum)
        .outerjoin(sell_sum, buy_sum.c.symbol == sell_sum.c.symbol)
        .where((buy_sum.c.bsum > sell_sum.c.ssum) | (sell_sum.c.ssum == None))
        .join(symbol_names, buy_sum.c.symbol == symbol_names.c.symbol)
        .add_columns(symbol_names.c.name.label("security_name"))
    )

    if symbol:
        result = result.where(buy_sum.c.symbol == symbol)
    else:
        result = result.order_by(buy_sum.c.symbol)

    current_holdings = db.session.execute(result).all()
    return current_holdings




def get_current_holdings_symbols():
    """Returns a list of symbols from current holdings."""
    current_holdings = get_current_holdings()
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
    # return [{"symbol": holding["symbol"], "name": holding["name"]} for holding in holdings_list]
    return [[holding["symbol"], holding["name"]] for holding in holdings_list]


def get_raw_trade_data(symbol):

    return (
        db.session.query(
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
        )
        .filter(
            TradeTransaction.symbol == symbol,
            TradeTransaction.action.in_(common_actions),
            # TradeTransaction.symbol != "ET",
        )
        .order_by(
            TradeTransaction.trade_date,
            TradeTransaction.action,
            TradeTransaction.trade_type,
            TradeTransaction.account,
        )
        .all()
    )


def get_trade_data_for_analysis_new(stock_symbol):
    """Returns all trade transactions for a given stock symbol."""

    trade_transactions = []
    raw_trade_data = get_raw_trade_data(stock_symbol)
    for (
        id,
        symbol,
        action,
        trade_type,
        label,
        trade_date,
        expiration_date,
        quantity,
        price,
        target_price,
        amount,
        account,
    ) in raw_trade_data:

        trade_transactions.append(
            {
                "id": id,
                "symbol": symbol,
                "action": action,
                "trade_type": trade_type,
                "label": label,
                "trade_date": trade_date,
                "expiration_date": expiration_date,
                "quantity": quantity,
                "price": price,
                "target_price": target_price,
                "amount": amount,
                "account": account,
            }
        )
    return trade_transactions


def get_trade_data_for_analysis(stock_symbol):
    """Returns all trade transactions for a given stock symbol."""

    trade_transactions = []
    raw_trade_data = get_raw_trade_data(stock_symbol)
    for (
        id,
        symbol,
        action,
        trade_type,
        label,
        trade_date,
        expiration_date,
        quantity,
        price,
        target_price,
        amount,
        account,
    ) in raw_trade_data:

        trade_transactions.append(
            {
                "Id": id,
                "Symbol": symbol,
                "Action": action,
                "Trade Type": trade_type,
                "Label": label,
                "Trade Date": trade_date,
                "Expiration Date": expiration_date,
                "Quantity": quantity,
                "Price": price,
                "Target Price": target_price,
                "Amount": amount,
                "Account": account,
            }
        )
    return trade_transactions


def get_all_securities():
    """Fetches all securities from the database."""
    return (
        db.session.query(Security.symbol, Security.name).order_by(Security.symbol).all()
    )
