# from app import db
from sqlalchemy import func, case, cast, Numeric
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
