# app/models/models.py
from ..extensions import db
from lib.constants import Action

# Actions that represent trade entries (buys) or exits (sells)
common_actions = [
    Action.BUY, Action.BUY_TO_OPEN, Action.EXERCISED,
    Action.EXPIRED, Action.REINVEST_SHARES, Action.SELL, Action.SELL_TO_CLOSE,
]


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
    reason = db.Column(db.String(500), default="")
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
