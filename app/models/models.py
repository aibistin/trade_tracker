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
    reason = db.Column(db.String(80))
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    initial_stop_price = db.Column(db.Float)
    projected_sell_price = db.Column(db.Float)

    security = db.relationship('Security', backref=db.backref('transactions', lazy=True))