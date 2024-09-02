from app import app
from flask import Flask, render_template, request
from datetime import datetime, timedelta
import os
import pytz
from flask_sqlalchemy import SQLAlchemy
from .extensions import db

print("[routes.py] Flask Env  = " + os.environ.get('FLASK_ENV') )
from .models.models import Security, TradeTransaction

# app = Flask(__name__)
print("Inside Routes name: " + __name__)




# Create the database tables (only needed once)
with app.app_context():
    db.create_all()

@app.before_request
def before_request():
    print("Before request")

@app.route('/')
@app.route('/index')
def index():
    # Example: Fetch all transactions and display them
    print("Inside Home route '/'")
    transactions = TradeTransaction.query.all()
    return render_template('index.html', transactions=transactions)


@app.route('/transaction/<int:transaction_id>')
def view_transaction(transaction_id):
    transaction = db.session.get(TradeTransaction, transaction_id)  # Use db.session.get()
    if not transaction:
        return "Transaction not found", 404
    return render_template('update_transaction.html', transaction_id=transaction_id, transaction=transaction)
########################


@app.route('/recent_trades/<int:days>')
def recent_trades(days):
    """Fetches buy and sell transactions from the specified number of days,
    ordered by symbol and trade date, including the security name."""

    print("Inside Recent Trades route '/recent_trades'")
    days_ago = datetime.now(pytz.timezone('America/New_York')) - timedelta(days=days)

    transactions = (
        db.session.query(TradeTransaction, Security.name)  # Query both tables
        .join(Security, TradeTransaction.symbol == Security.symbol)  # Join on symbol
        .filter(
            TradeTransaction.action.in_(["B", "S"]),
            TradeTransaction.trade_date > days_ago
        )
        .order_by(
            TradeTransaction.symbol,
            TradeTransaction.trade_date.desc()
        )
        .all()
    )
    return render_template('recent_trades.html', transactions=transactions, days=days)


@app.route('/trades/<string:symbol>')
def trades_by_symbol(symbol):
    """Fetches all buy and sell transactions for the given symbol, ordered by trade date."""

    transactions = TradeTransaction.query.filter(
        TradeTransaction.action.in_(["B", "S"]),
        TradeTransaction.symbol == symbol
    ).order_by(
        TradeTransaction.trade_date
    ).all()

    return render_template('trades_by_symbol.html', transactions=transactions, symbol=symbol)


@app.route('/update_transaction/<int:transaction_id>', methods=['POST'])
def update_transaction(transaction_id):
    """Updates the reason, initial_stop_price, and projected_sell_price fields of a transaction."""

    transaction = db.session.get(TradeTransaction, transaction_id)  # Use db.session.get()
    if not transaction:
        return "Transaction not found", 404

    # Get updated values from the request (allowing for optional updates)
    reason = request.form.get('reason')
    initial_stop_price = request.form.get('initial_stop_price')
    projected_sell_price = request.form.get('projected_sell_price')

    # Update fields only if values are provided
    if reason:
        transaction.reason = reason
    if initial_stop_price:
        try:
            transaction.initial_stop_price = float(initial_stop_price)
        except ValueError:
            return "Error: Invalid initial_stop_price format", 400  # Bad Request
    if projected_sell_price:
        try:
            transaction.projected_sell_price = float(projected_sell_price)
        except ValueError:
            return "Error: Invalid projected_sell_price format", 400

    db.session.commit()

    return "Transaction updated successfully", 200  # OK


if __name__ == '__main__':
    app.run(debug=True)  # Run the Flask app in debug mode
