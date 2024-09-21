# lib/trading_analyzer.py
import warnings


class TradingAnalyzer:
    def __init__(self, data_dict):
        self.data_dict = data_dict
        self.results = {}

    def _is_last_trade_open(self, all_trades):
        if len(all_trades) > 0 and self._is_trade_open(all_trades[-1]):
            return True
        return False

    def _is_trade_open(self, trade):
        if (trade['quantity'] > trade['current_sold_qty'] and (trade['current_sold_qty'] > 0)):
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
            sell_rec_for_trade = {
                'trade_date': sell['Trade Date'],
                'quantity': 0,
                'price':  sell['Price'],
                'amount': 0,
                'profit_loss': 0,
                'percent_profit_loss': 0,
            }

            print(f"################## Start _add_sells_to_trade #####################")
            print(f"[] Sell Quantity = {sell['Quantity']}")
            # start
            qty_to_close_the_trade = bought_qty - buy_trade['current_sold_qty']
            amt_to_close_the_trade = (
                sell['Amount'] / sell['Quantity']) * qty_to_close_the_trade

            if sell['Quantity'] - qty_to_close_the_trade == 0:
                # The buy trade WILL be closed with this sell
                sell_rec_for_trade['quantity'] = qty_to_close_the_trade
                sell_rec_for_trade['amount'] = amt_to_close_the_trade
                buy_trade['current_sold_qty'] += qty_to_close_the_trade
                sell_trades.pop(0)  # Done with this sell record
            elif (sell['Quantity'] - qty_to_close_the_trade) > 0:
                # The buy trade will be closed with a part of this sell.
                # --- Modify in place
                sell_rec_for_trade['quantity'] = qty_to_close_the_trade
                sell_rec_for_trade['amount'] = amt_to_close_the_trade
                buy_trade['current_sold_qty'] += qty_to_close_the_trade
                sell['Quantity'] -= qty_to_close_the_trade
                sell['Amount'] -= amt_to_close_the_trade
            else:
                # The buy trade will remain open after this sell.
                sell_rec_for_trade['quantity'] = sell['Quantity']
                sell_rec_for_trade['amount'] = sell['Amount']
                buy_trade['current_sold_qty'] += sell['Quantity']
                sell_trades.pop(0)  # Done with this sell record

            print(f"[] bought_quantity = {bought_qty}")
            print(f"[] Qty to close trade = {qty_to_close_the_trade}")
            print(f"[] sell_quantity = {sell['Quantity']}")
            print(f"[] Sell Trade = {sell}")

            # Calculate profit & loss for this Sell trade.
            price_difference = sell['Price'] - buy_trade['price']
            profit_loss = round(price_difference * sell_rec_for_trade['quantity'], 2)
 
            sell_rec_for_trade['percent_profit_loss'] = round((price_difference / buy_trade['price']) * 100, 2)

            sell_rec_for_trade['profit_loss'] = profit_loss

            print(f"Sell record for this Buy trade: {sell_rec_for_trade}")
            print(f"################## END #####################")

            buy_trade['sells'].append(sell_rec_for_trade)

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
                'bought_quantity': round(total_bought_quantity, 2),
                'bought_amount': round(total_bought_amount, 2),
                'sold_quantity': round(total_sold_quantity, 2),
                'sold_amount': round(total_sold_amount, 2),
                'closed_bought_quantity': 0,
                'closed_bought_amount': 0,
                'open_bought_quantity': 0,
                'open_bought_amount': 0,
                'profit_loss': 0,
                'percent_profit_loss': 0,
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

            # Match sell trades with buy trades
            while buy_trades:
                current_buy_trade = {}
                buy = buy_trades[0]
                bought_quantity += buy['Quantity']
                print(f"[{symbol}] Buy Trade: {buy}")

                if self._is_last_trade_open(self.results[symbol]['all_trades']):
                    # Complete an open trade
                    current_buy_trade = self.results[symbol]['all_trades'][-1]
                else:
                    # A new open trade
                    current_buy_trade = {
                        'trade_date': buy['Trade Date'],
                        'quantity': buy['Quantity'],
                        'price':  buy['Price'],
                        'amount': buy['Amount'],
                        'current_sold_qty': 0,
                        'sells': []
                    }


                not_sold_quantity = bought_quantity - total_sold_quantity

                if bought_quantity > total_sold_quantity:
                    # We have some unsold shares. Partially match the buy trade
                    # Or we have a buy trade with no sells.
                    closed_bought_quantity = buy['Quantity'] - \
                        not_sold_quantity
                    closed_bought_amount = (
                        buy['Amount'] / buy['Quantity']) * closed_bought_quantity

                    print(f"[{symbol}] Bought Qty: {buy['Quantity']}")
                    print(
                        f"[{symbol}] Partial Closed B Qty: {closed_bought_quantity}")
                    print(
                        f"[{symbol}] Partial Closed B Amt: {closed_bought_amount}")
                    self.results[symbol]['closed_bought_quantity'] += closed_bought_quantity
                    self.results[symbol]['closed_bought_amount'] += closed_bought_amount

                    if len(sell_trades) > 0:
                        current_buy_trade['quantity'] = closed_bought_quantity
                        current_buy_trade['amount'] = closed_bought_amount
                        self._add_sells_to_this_trade(
                            current_buy_trade, sell_trades)

                    # print(f"Adding this to results: {current_buy_trade}")
                    self.results[symbol]['all_trades'].append(
                        current_buy_trade)
                    if total_sold_quantity > 0:
                        buy_trades.pop(0)
                        break
                else:
                    # Fully match the buy trade
                    print(f"[{symbol}] FullMatch buy Qty: {buy['Quantity']}")
                    self.results[symbol]['closed_bought_quantity'] += buy['Quantity']

                    self.results[symbol]['closed_bought_amount'] += buy['Amount']
                    current_buy_trade['quantity'] = buy['Quantity']
                    current_buy_trade['amount'] = buy['Amount']
                    if len(sell_trades) > 0:
                        self._add_sells_to_this_trade(
                            current_buy_trade, sell_trades)

                    self.results[symbol]['all_trades'].append(
                        current_buy_trade)
                    buy_trades.pop(0)  # Remove the matched buy trade

            # Calculate open shares for this symbol
            self.results[symbol]['open_bought_quantity'] = round(self.results[symbol]['bought_quantity'] -
                                                                 self.results[symbol]['closed_bought_quantity'], 2)
            self.results[symbol]['open_bought_amount'] = round(self.results[symbol]['bought_amount'] -
                                                               self.results[symbol]['closed_bought_amount'], 2)

            # Calculate Profit/Loss
            if abs(self.results[symbol]['closed_bought_amount']) > 0:
                self.results[symbol]['profit_loss'] = self.results[symbol]['sold_amount'] + \
                    self.results[symbol]['closed_bought_amount']
                self.results[symbol]['percent_profit_loss'] =  \
                    (self.results[symbol]['profit_loss'] /
                     abs(self.results[symbol]['closed_bought_amount'])) * 100

    def get_results(self):
        return self.results
