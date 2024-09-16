# lib/trading_analyzer.py
import warnings


class TradingAnalyzer:
    def __init__(self, data_dict):
        self.data_dict = data_dict
        self.results = {}

    def _is_last_trade_open(self, all_trades):
        if len(all_trades) > 0 and self._is_trade_open(all_trades[-1]):
            # and (all_trades[-1]['quantity'] >  all_trades[-1]['current_sold_qty']):
            return True
        return False

    def _is_trade_open(self, trade):
        if (trade['quantity'] > trade['current_sold_qty']):
            return True
        return False

    # buy_trade = {
    #     'trade_date': buy['Trade Date'],
    #     'quantity': 0,
    #     'price':  buy['Price'],
    #     'amount': 0,
    #     'current_sold_qty': 0,
    #     'sells': []
    # }

    def _add_sells_to_this_trade(self, buy_trade, sell_trades):

        bought_qty = buy_trade['quantity']

        while sell_trades and (buy_trade['current_sold_qty'] < bought_qty):
            sell = sell_trades[0]
            # print(f"Current Sell: {sell}")
            new_sell_record = {}
            sell_qty = 0
            sell_amt = 0

            gross_sell_qty = sell['Quantity'] + buy_trade['current_sold_qty']
            if gross_sell_qty > bought_qty:
                # Not all of this sell trade belong to buy_trade
                sell_qty = bought_qty - buy_trade['current_sold_qty']
                sell_amt = (sell['Amount'] / sell['Quantity']) * sell_qty
                # Modify 'sell' in place.
                sell['Quantity'] -= bought_qty
                sell['Amount'] -= sell_amt
            else:
                # All of this sell trade belong to buy_trade
                sell_qty = sell['Quantity']
                sell_amt = sell['Amount']
                sell_trades.pop(0)  # Done with this sell record

            buy_trade['current_sold_qty'] += sell_qty

            # print(f"Changed Sell Trade: {sell}")

            price_difference = sell['Price'] - buy_trade['price']
            profit_loss = round(price_difference * sell_qty, 2)
            pct_profit_loss = round(
                (price_difference / buy_trade['price']) * 100, 2)

            new_sell_record = {
                'trade_date': sell['Trade Date'],
                'quantity': sell_qty,
                'price':  sell['Price'],
                'amount': sell_amt,
                'profit_loss': profit_loss,
                'percent_profit_loss': pct_profit_loss,
            }
            # print(f"New Sell Record: {new_sell_record}")
            buy_trade['sells'].append(new_sell_record)

    def analyze_trades(self):

        for symbol, trades in self.data_dict.items():
            sorted_trades = sorted(trades, key=lambda x: (
                x['Trade Date'], x['Action']))
            buy_trades = []
            sell_trades = []
            total_bought_quantity = 0
            total_bought_amount = 0
            # Accumulate sold quantity
            total_sold_quantity = 0
            total_sold_amount = 0

            print(f"Working on symbol {symbol}")
            # Separate buy and sell trades
            for trade in sorted_trades:
                if isinstance(trade['Amount'], str):
                    # TODO Remove these silly "None"s
                    print(f'[{symbol}] - Amount: <{trade["Amount"]}>')
                    continue
                # Sum the Buy and 'Reinvest Shares'
                if trade['Action'] in ('B', 'RS'):
                    buy_trades.append(trade)
                    total_bought_quantity += trade['Quantity']
                    total_bought_amount += trade['Amount']
                elif trade['Action'] == 'S':
                    sell_trades.append(trade)
                    total_sold_quantity += trade['Quantity']
                    total_sold_amount += trade['Amount']

            print(f"Total sell trades @ start: {len(sell_trades)}")
            # Initialize results for the symbol
            self.results[symbol] = {
                'bought_quantity': round(total_bought_quantity,2),
                'bought_amount': round(total_bought_amount,2),
                'sold_quantity': round(total_sold_quantity,2),
                'sold_amount': round(total_sold_amount,2),
                'closed_bought_quantity': 0,
                'closed_bought_amount': 0,
                'open_bought_quantity': 0,
                'open_bought_amount': 0,
                'Profit/Loss': 0,
                'PercentProfit/Loss': 0,
                'all_trades': []
            }

            # Validate that we are not selling more than we bought
            if total_sold_quantity > total_bought_quantity:
                warnings.warn(
                    f"[{symbol}] Total quantity sold ({total_sold_quantity}) exceeds total quantity bought ({total_bought_quantity})")

            # Accumulate matching bought quantity for this symbol
            bought_quantity = 0

            print(f"[{symbol}] Total Sold Q: {total_sold_quantity}")
            print(f"[{symbol}] Total Bought Q: {total_bought_quantity}")

            # Match with buy trades
            if total_sold_quantity > 0:
                while buy_trades:
                    buy = buy_trades[0]
                    bought_quantity += buy['Quantity']

                    current_trade = {}

                    if self._is_last_trade_open(self.results[symbol]['all_trades']):
                        # Complete the open trade
                        current_buy_trade = self.results[symbol]['all_trades'][-1]
                    else:
                        # A new open trade
                        current_buy_trade = {
                            'trade_date': buy['Trade Date'],
                            'quantity': 0,
                            'price':  buy['Price'],
                            'amount': 0,
                            'current_sold_qty': 0,
                            'sells': []
                        }

                    if bought_quantity > total_sold_quantity:
                        # We have some unsold shares. Partially match the buy trade
                        not_sold_quantity = bought_quantity - total_sold_quantity
                        closed_bought_quantity = buy['Quantity'] - \
                            not_sold_quantity
                        closed_bought_amount = (
                            buy['Amount'] / buy['Quantity']) * closed_bought_quantity
                        print(
                            f"[{symbol}] Partial Closed B Qty: {closed_bought_quantity}")
                        self.results[symbol]['closed_bought_quantity'] += closed_bought_quantity
                        self.results[symbol]['closed_bought_amount'] += closed_bought_amount
                        current_buy_trade['quantity'] = closed_bought_quantity
                        current_buy_trade['amount'] = closed_bought_amount

                        self._add_sells_to_this_trade(
                            current_buy_trade, sell_trades)
                        self.results[symbol]['all_trades']. append(
                            current_buy_trade)
                        break
                    else:
                        # Fully match the buy trade
                        # print(f"[{symbol}] FullMatch buy Qty: {buy['Quantity']}")
                        self.results[symbol]['closed_bought_quantity'] += buy['Quantity']

                        self.results[symbol]['closed_bought_amount'] += buy['Amount']
                        current_buy_trade['quantity'] = buy['Quantity']
                        current_buy_trade['amount'] = buy['Amount']
                        self._add_sells_to_this_trade(
                            current_buy_trade, sell_trades)
                        buy_trades.pop(0)  # Remove the matched buy trade
                        self.results[symbol]['all_trades']. append(
                            current_buy_trade)

                # Get Open Trades
                self.results[symbol]['open_bought_quantity'] = round(self.results[symbol]['bought_quantity'] -
                                                                     self.results[symbol]['closed_bought_quantity'], 2)
                self.results[symbol]['open_bought_amount'] = round(self.results[symbol]['bought_amount'] -
                                                                   self.results[symbol]['closed_bought_amount'], 2)

                # Calculate Profit/Loss
                if abs(self.results[symbol]['closed_bought_amount']) > 0:
                    self.results[symbol]['Profit/Loss'] = self.results[symbol]['sold_amount'] + \
                        self.results[symbol]['closed_bought_amount']
                    self.results[symbol]['PercentProfit/Loss'] =  \
                        (self.results[symbol]['Profit/Loss'] /
                         abs(self.results[symbol]['closed_bought_amount'])) * 100

    def get_results(self):
        return self.results
