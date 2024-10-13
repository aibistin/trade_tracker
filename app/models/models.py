# app/models/models.py
# from sqlalchemy import func, select, case
from sqlalchemy import func, case, cast, Numeric, select
# from app import db
from ..extensions import db

class Security(db.Model):
    symbol = db.Column(db.String(30), primary_key=True)
    name = db.Column(db.String(80), nullable=False)


class TradeTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(30), db.ForeignKey('security.symbol'), nullable=False)
    action = db.Column(db.String(3), nullable=False)
    trade_date = db.Column(db.DateTime, nullable=False)
    reason = db.Column(db.String(80), default='')
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    initial_stop_price = db.Column(db.Float)
    projected_sell_price = db.Column(db.Float)

    security = db.relationship('Security', backref=db.backref('transactions', lazy=True))
    from sqlalchemy import func, case, cast, Numeric

    @staticmethod
    def get_trade_stats_summary():
        """Fetches trade statistics summary from the database."""
        trade_summary = db.session.query(
            TradeTransaction.symbol,
            func.sum(case((TradeTransaction.action == 'S', TradeTransaction.quantity), else_=0)).label('sell_quantity'),
            func.sum(case((TradeTransaction.action == 'S', TradeTransaction.amount), else_=0)).label('sell_amount'),
            func.avg(case((TradeTransaction.action == 'S', TradeTransaction.price), else_=0)).label('average_sell_price'),
            func.sum(case((TradeTransaction.action == 'B', TradeTransaction.quantity), else_=0)).label('buy_quantity'),
            func.sum(case((TradeTransaction.action == 'B', TradeTransaction.amount), else_=0)).label('buy_amount'),
            func.avg(case((TradeTransaction.action == 'B', TradeTransaction.price), else_=0)).label('average_buy_price'),
            (func.sum(case((TradeTransaction.action == 'B', TradeTransaction.amount), else_=0)) + 
             func.sum(case((TradeTransaction.action == 'S', TradeTransaction.amount), else_=0))).label('profit_loss')
        ).filter(
            TradeTransaction.action.in_(["B", "S", "RS"])
        ).group_by(
            TradeTransaction.symbol
        ).subquery()

        result = db.session.query(
            trade_summary.c.symbol,
            func.round(func.coalesce(trade_summary.c.buy_amount, 0), 2).label('buy_amount'),
            func.round(func.coalesce(trade_summary.c.average_buy_price, 0), 2).label('average_buy_price'),
            func.coalesce(trade_summary.c.buy_quantity, 0).label('buy_quantity'),
            func.coalesce(trade_summary.c.sell_quantity, 0).label('sell_quantity'),
            func.round(func.coalesce(trade_summary.c.sell_amount, 0), 2).label('sell_amount'),
            func.round(func.coalesce(trade_summary.c.average_sell_price, 0), 2).label('average_sell_price'),
            func.round(func.coalesce(trade_summary.c.profit_loss, 0), 2).label('profit_loss'),
            case(
                (func.round(func.coalesce(trade_summary.c.profit_loss, 0), 2) < 0, 'L'),
                else_= case(
                    (func.round(func.coalesce(trade_summary.c.profit_loss, 0), 2) > 0, 'P'),
                    else_= 'E'
                )
            ).label('win_lose')
        ).filter(
            trade_summary.c.buy_quantity == trade_summary.c.sell_quantity
        ).all()

        return result


    def get_open_positions():
        """Fetches open positions (where bought quantity exceeds sold quantity)."""
    
        buy_sum = (
            select(
                TradeTransaction.symbol,
                TradeTransaction.action,
                func.sum(TradeTransaction.quantity).label("bsum"),
                func.abs(func.sum(TradeTransaction.amount)).label("bamount"),
            )
            .where(TradeTransaction.action.in_(["B", "RS"]))
            .group_by(TradeTransaction.symbol)
            .order_by(TradeTransaction.symbol)
            .cte("buy_sum")
        )
    
        sell_sum = (
            select(
                TradeTransaction.symbol,
                TradeTransaction.action,
                func.sum(TradeTransaction.quantity).label("ssum"),
                func.sum(TradeTransaction.amount).label("samount"),
            )
            .where(TradeTransaction.action.in_(["S"]))
            .group_by(TradeTransaction.symbol)
            .order_by(TradeTransaction.symbol)
            .cte("sell_sum")
        )
    
        result = (
            select(buy_sum)
            .outerjoin(sell_sum, buy_sum.c.symbol == sell_sum.c.symbol)
            .where((buy_sum.c.bsum > sell_sum.c.ssum) | (sell_sum.c.ssum == None)) 
        )

        open_positions = db.session.execute(result).all()
        return open_positions


def get_current_holdings(symbol=None):
    """
    Fetches current holdings (stocks where bought quantity exceeds sold quantity), sorted by symbol.
    Args:
        symbol (str, optional): If provided, fetches holdings only for this symbol. Otherwise, fetches all holdings.
    """

    buy_sum = (
        select(
            TradeTransaction.symbol,
            TradeTransaction.action,
            func.sum(TradeTransaction.quantity).label("bsum"),
            func.avg(TradeTransaction.price).label("bprice"),  # Added average buy price
            func.abs(func.sum(TradeTransaction.amount)).label("bamount"),
        )
        .where(TradeTransaction.action.in_(["B", "RS"]))
        .group_by(TradeTransaction.symbol)
        .order_by(TradeTransaction.symbol)
        .cte("buy_sum")
    )

    sell_sum = (
        select(
            TradeTransaction.symbol,
            TradeTransaction.action,
            func.sum(TradeTransaction.quantity).label("ssum"),
            func.sum(TradeTransaction.amount).label("samount"),
        )
        .where(TradeTransaction.action.in_(["S"]))
        .group_by(TradeTransaction.symbol)
        .order_by(TradeTransaction.symbol)
        .cte("sell_sum")
    )

    result = (
        select(
            buy_sum.c.symbol,
            (buy_sum.c.bsum - func.coalesce(sell_sum.c.ssum, 0)).label("quantity"),
            buy_sum.c.bprice.label("avg_price"),
            (buy_sum.c.bamount - func.coalesce(sell_sum.c.samount, 0)).label("cost_basis"),
        )
        .select_from(buy_sum)
        .outerjoin(sell_sum, buy_sum.c.symbol == sell_sum.c.symbol)
        .where((buy_sum.c.bsum > sell_sum.c.ssum) | (sell_sum.c.ssum == None))
        # .order_by(buy_sum.c.symbol)  # Add sorting here
    )

    # current_holdings = db.session.execute(result).all()
    # return current_holdings
    # Apply filter if symbol is provided
    if symbol:
        result = result.where(buy_sum.c.symbol == symbol)
    else:
        result = result.order_by(buy_sum.c.symbol)

    current_holdings = db.session.execute(result).all()
    return current_holdings
