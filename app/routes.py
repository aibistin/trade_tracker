from .models.models import Security, TradeTransaction
from lib.trading_analyzer import TradingAnalyzer
from app import app
from flask import Flask, render_template, request
from datetime import datetime, timedelta
import os
import pytz
import dumper
from flask_sqlalchemy import SQLAlchemy
from .extensions import db

print("[routes.py] Flask Env  = " + os.environ.get('FLASK_ENV'))

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
    print("Inside Home route '/'")
    transactions = TradeTransaction.query.all()
    return render_template('index.html', transactions=transactions)


@app.route('/transaction/<int:transaction_id>')
def view_transaction(transaction_id):
    transaction = db.session.get(
        TradeTransaction, transaction_id)
    if not transaction:
        return "Transaction not found", 404
    return render_template('update_transaction.html', transaction_id=transaction_id, transaction=transaction)


@app.route('/recent_trades/<int:days>')
def recent_trades(days):
    """Fetches buy and sell transactions from the specified number of days,
    ordered by symbol and trade date, including the security name."""

    print("Inside Recent Trades route '/recent_trades'")
    days_ago = datetime.now(pytz.timezone(
        'America/New_York')) - timedelta(days=days)

    transactions = (
        db.session.query(TradeTransaction, Security.name)  # Query both tables
        # Join on symbol
        .join(Security, TradeTransaction.symbol == Security.symbol)
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

    for trans,sec in transactions:
        # print(dumper.dump(trans))
        print("++++++++++++")
        print( sec )
        print( trans.initial_stop_price ) if  trans.initial_stop_price != 'None' else  print("Feck")
        print( trans.projected_sell_price)
        print("=======")
        
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


@app.route('/trade_stats_summary')
def trade_stats_summary():
    """Fetches trade statistics summary and renders the template."""
    # The SQLAlchemy query will be added here (see next section)
    trade_stats = TradeTransaction.get_trade_stats_summary()
    return render_template('trade_stats_summary.html', trade_stats=trade_stats)


@app.route('/trade_stats_pl')
def trade_stats_pl():
    """Fetches trade statistics summary and renders the template."""

    # Fetch raw data from the database (adjust the query if needed)
    raw_trade_data = db.session.query(
        TradeTransaction.symbol,
        TradeTransaction.action,
        TradeTransaction.trade_date,
        TradeTransaction.quantity,
        TradeTransaction.price,
        TradeTransaction.amount
    ).filter(
        TradeTransaction.action.in_(["B", "RS", "S"]),
    ).all()

    # Group data by symbol
    data_dict = {}
    for symbol, action, trade_date, quantity, price, amount in raw_trade_data:
        if symbol not in data_dict:
            data_dict[symbol] = []
        data_dict[symbol].append({'Action': action, 'Trade Date': trade_date, 'Quantity': quantity, 'Price': price, 'Amount': amount})

    # Analyze trades for each symbol
    all_trade_stats = {}
    for symbol, trades in data_dict.items():
        analyzer = TradingAnalyzer({symbol: trades})  # Analyze for each symbol separately
        analyzer.analyze_trades()
        all_trade_stats[symbol] = analyzer.get_results()[symbol]  # Store results with symbol as key
    

    return render_template('trade_stats_pl.html', trade_stats=all_trade_stats)

if __name__ == '__main__':
    app.run(debug=True)  # Run the Flask app in debug mode
