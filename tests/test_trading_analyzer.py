import unittest
from lib.trading_analyzer import TradingAnalyzer


class TestTradingAnalyzer(unittest.TestCase):
    def setUp(self):
        self.data_dict = [
            {'SN': [
                {'Action': 'B', 'Quantity': 100.0, 'Price': 91.39,
                 'Trade Date': '2024-08-22', 'Amount': -9139.0},
                {'Action': 'S', 'Quantity': 100.0, 'Price': 88.9427,
                 'Trade Date': '2024-08-23', 'Amount': 8894.27},
                # Sold 100

                {'Action': 'B', 'Quantity': 50.0, 'Price': 89.4964,
                 'Trade Date': '2024-08-26', 'Amount': -4474.82},
                # Sold 50

                {'Action': 'B', 'Quantity': 50.0, 'Price': 91.7,
                 'Trade Date': '2024-08-27', 'Amount': -4585.0},
                # Sold 50

                {'Action': 'S', 'Quantity': 100.0, 'Price': 94.92,
                 'Trade Date': '2024-09-06', 'Amount': 9492.0},
                # Sold for previous two trades

                {'Action': 'B', 'Quantity': 50.0, 'Price': 94.85,
                 'Trade Date': '2024-08-30', 'Amount': -4742.5},


                {'Action': 'S', 'Quantity': 25.0, 'Price': 94.94,
                 'Trade Date': '2024-09-06', 'Amount': 2373.5},
                {'Action': 'S', 'Quantity': 10.0, 'Price': 96.99,
                 'Trade Date': '2024-09-07', 'Amount': 969.9},

                {'Action': 'B', 'Quantity': 25.0, 'Price': 98.99,
                 'Trade Date': '2024-09-10', 'Amount': -2474.75}

            ]},
            {'NVDA': [
                {'Action': 'B', 'Quantity': 200.0, 'Price': 300.0,
                 'Trade Date': '2024-08-22', 'Amount': -60000.0},
                {'Action': 'S', 'Quantity': 150.0, 'Price': 310.0,
                 'Trade Date': '2024-09-01', 'Amount': 46500.0},
                {'Action': 'S', 'Quantity': 50.0, 'Price': 315.0,
                 'Trade Date': '2024-09-02', 'Amount': 15750.0}
            ]},
            {'TNA': [
                {'Action': 'B', 'Quantity': 150.0, 'Price': 50.25,
                 'Trade Date': '2024-07-31', 'Amount': -7537.5},
                {'Action': 'S', 'Quantity': 100.0, 'Price': 47.2,
                 'Trade Date': '2024-08-01', 'Amount': 4720.0},
                {'Action': 'S', 'Quantity': 50.0, 'Price': 43.2601,
                 'Trade Date': '2024-08-27', 'Amount': 2163.01},
            ]}
        ]

        self.expect_trades = {
            'SN': [
                {
                    'trade_date': '2024-08-22',
                    'quantity': 100,
                    'price':  91.39,
                    'amount': -9139.0,
                    'current_sold_qty': 100,
                    'sells': [
                        {
                            'trade_date': '2024-08-23',
                            'quantity': 100,
                            'price':  88.9427,
                            'amount': 8894.27,
                            'profit_loss': -244.73,
                            'percent_profit_loss': -(244.73/9139) * 100,
                        }
                    ]
                },
                {
                    'trade_date': '2024-08-26',
                    'quantity': 50,
                    'price':  89.4964,
                    'amount': -4474.82,
                    'current_sold_qty': 50,
                    # Half of one sell
                    'sells': [
                        {
                            'trade_date': '2024-09-06',
                            'quantity': 50,
                            'price':  94.92,
                            'amount': 9492.00/2,
                            'profit_loss': (9492.00/2) - 4474.82,
                            'percent_profit_loss': ((94.92 - 89.4964)/89.4964) * 100,
                        }
                    ]
                },
                {
                    'trade_date': '2024-08-27',
                    'quantity': 50,
                    'price':  91.70,
                    'amount': -4585.00,
                    'current_sold_qty': 50,
                    # Half of one sell
                    'sells': [
                        {
                            'trade_date': '2024-09-06',
                            'quantity': 50,
                            'price':  94.92,
                            'amount': 9492.27/2,
                            'profit_loss': round((9492.27/2)) - 4585.00,
                            'percent_profit_loss': ((94.92 - 91.70)/91.70) * 100,
                        }
                    ]
                },

                {
                    'trade_date': '2024-08-30',
                    'quantity': 35,
                    'price':  94.85,
                    'amount': (-4742.50/2) - (4742.5/5),
                    'current_sold_qty': 35,
                    'sells': [
                        {
                            'trade_date': '2024-09-06',
                            'quantity': 25,
                            'price':  94.94,
                            'amount': 2373.5,
                            'profit_loss': 2373.5 - (4742.5/2),
                            'percent_profit_loss': ((94.94 - 94.85)/94.85) * 100,
                        },
                        {
                            'trade_date': '2024-09-07',
                            'quantity': 10,
                            'price':  96.99,
                            'amount': 969.9,
                            'profit_loss': 969.9 - (4742.5/5),
                            'percent_profit_loss': ((96.99 - 94.85)/94.85) * 100,
                        }
                    ]
                }
            ],
            'NVDA': [
                {
                    'trade_date': '2024-08-22',
                    'quantity': 200,
                    'price':  300,
                    'amount': -60000.0,
                    'current_sold_qty': 200,
                    'sells': [
                        {
                            'trade_date': '2024-09-01',
                            'quantity': 150,
                            'price':  310.0,
                            'amount': 46500.0,
                            'profit_loss': 46500.0 - (60000.0 * .75),
                            'percent_profit_loss': ((310.0 - 300.0)/300) * 100,
                        },
                        {
                            'trade_date': '2024-09-02',
                            'quantity': 50,
                            'price':  315.0,
                            'amount': 15750.0,
                            'profit_loss': 15750.0 - (60000.0 * .25),
                            'percent_profit_loss': ((315.0 - 300.0)/300) * 100,
                        }
                    ]
                }
            ],
            'TNA': [
                {
                    'trade_date': '2024-07-31',
                    'quantity': 150,
                    'price':  50.25,
                    'amount': -7537.5,
                    'current_sold_qty': 150,
                    'sells': [
                        {
                            'trade_date': '2024-08-01',
                            'quantity': 100,
                            'price':  47.2,
                            'amount': 4720.0,
                            'profit_loss': (47.20 - 50.25) * 100,
                            'percent_profit_loss': ((47.2 - 50.25)/50.25) * 100,
                        },
                        {
                            'trade_date': '2024-08-27',
                            'quantity': 50,
                            'price':  43.2601,
                            'amount': 2163.01,
                            'profit_loss': (43.2601 - 50.25) * 50,
                            'percent_profit_loss': ((43.2601 - 50.25)/50.25) * 100,
                        }
                    ]
                }
            ]
        }

    def test_analyze_trades_sn(self):
        analyzer = TradingAnalyzer(self.data_dict[0])
        analyzer.analyze_trades()
        results = analyzer.get_results()

        # Check results for symbol 'SN'
        expected_bought_amount = -9139.0 - 4474.82 - 4585.0 - 4742.5 - 2474.75
        expected_sold_amount = 8894.27 + 9492.0 + 2373.5 + 969.9
        expected_closed_bought_amount = -9139.0 - \
            4474.82 - 4585.0 - round((4742.5/50) * 35, 2)
        expected_open_bought_amount = expected_bought_amount - expected_closed_bought_amount
        expected_profit_loss = expected_sold_amount + expected_closed_bought_amount
        expected_profit_loss_percent = abs(
            expected_profit_loss / expected_closed_bought_amount) * 100

        self.assertEqual(results['SN']['bought_quantity'], 275.0)

        self.assertAlmostEqual(
            results['SN']['bought_amount'], -25416.07, places=2)

        self.assertEqual(results['SN']['sold_quantity'], 235.0)

        self.assertAlmostEqual(
            results['SN']['sold_amount'], 20759.77 + 969.9, places=2)
        self.assertEqual(results['SN']['closed_bought_quantity'], 235.0)
        self.assertAlmostEqual(
            results['SN']['closed_bought_amount'], expected_closed_bought_amount, places=2)

        self.assertEqual(results['SN']['open_bought_quantity'], 40.0)

        self.assertAlmostEqual(
            results['SN']['open_bought_amount'], expected_open_bought_amount, places=2)
        self.assertAlmostEqual(
            results['SN']['Profit/Loss'], expected_profit_loss, places=2)
        self.assertAlmostEqual(
            results['SN']['PercentProfit/Loss'], expected_profit_loss_percent, places=2)

        # Complete Trades
        self.assertEqual(len(results['SN']['all_trades']), 4)

        for i, expected_trade in enumerate(self.expect_trades['SN']):
            got_trade = results['SN']['all_trades'][i]
            self.assertEqual(got_trade['trade_date'],
                             expected_trade['trade_date'])
            self.assertEqual(got_trade['quantity'], expected_trade['quantity'])
            self.assertEqual(got_trade['amount'], expected_trade['amount'])
            self.assertEqual(
                got_trade['current_sold_qty'], expected_trade['current_sold_qty'])
            self.assertEqual(len(got_trade['sells']), len(
                expected_trade['sells']))
            for j, expected_sell in enumerate(expected_trade['sells']):
                got_sell = got_trade['sells'][j]
                self.assertEqual(got_sell['trade_date'],
                                 expected_sell['trade_date'])
                self.assertEqual(got_sell['quantity'],
                                 expected_sell['quantity'])
                self.assertEqual(got_sell['price'], expected_sell['price'])
                self.assertAlmostEqual(
                    got_sell['profit_loss'], expected_sell['profit_loss'], places=2)
                self.assertAlmostEqual(
                    got_sell['percent_profit_loss'], expected_sell['percent_profit_loss'], places=2)

    def test_analyze_trades_nvda(self):
        analyzer = TradingAnalyzer(self.data_dict[1])
        analyzer.analyze_trades()
        results = analyzer.get_results()

        # Check results for symbol 'NVDA'
        self.assertEqual(results['NVDA']['bought_quantity'], 200.0)
        self.assertAlmostEqual(
            results['NVDA']['bought_amount'], -60000.0, places=2)
        self.assertEqual(results['NVDA']['sold_quantity'], 200.0)
        self.assertAlmostEqual(
            results['NVDA']['sold_amount'], 62250.0, places=2)
        self.assertEqual(results['NVDA']['closed_bought_quantity'], 200.0)
        self.assertAlmostEqual(
            results['NVDA']['closed_bought_amount'], -60000.0, places=2)

        self.assertEqual(results['NVDA']['open_bought_quantity'], 0)
        self.assertAlmostEqual(
            results['NVDA']['open_bought_amount'], 0, places=2)

        self.assertAlmostEqual(
            results['NVDA']['Profit/Loss'], 2250.0, places=2)
        self.assertAlmostEqual(
            results['NVDA']['PercentProfit/Loss'], 3.75, places=2)
        # Complete Trades
        self.assertEqual(len(results['NVDA']['all_trades']), 1)

        for i, expected_trade in enumerate(self.expect_trades['NVDA']):
            got_trade = results['NVDA']['all_trades'][i]
            self.assertEqual(got_trade['trade_date'],
                             expected_trade['trade_date'])
            self.assertEqual(got_trade['quantity'], expected_trade['quantity'])
            self.assertEqual(got_trade['amount'], expected_trade['amount'])
            self.assertEqual(
                got_trade['current_sold_qty'], expected_trade['current_sold_qty'])
            self.assertEqual(len(got_trade['sells']), len(
                expected_trade['sells']))
            for j, expected_sell in enumerate(expected_trade['sells']):
                got_sell = got_trade['sells'][j]
                self.assertEqual(got_sell['trade_date'],
                                 expected_sell['trade_date'])
                self.assertEqual(got_sell['quantity'],
                                 expected_sell['quantity'])
                self.assertEqual(got_sell['price'], expected_sell['price'])
                self.assertAlmostEqual(
                    got_sell['profit_loss'], expected_sell['profit_loss'], places=2)
                self.assertAlmostEqual(
                    got_sell['percent_profit_loss'], expected_sell['percent_profit_loss'], places=2)


    def test_analyze_trades_tna(self):
        analyzer = TradingAnalyzer(self.data_dict[2])
        analyzer.analyze_trades()
        results = analyzer.get_results()

        # Check results for symbol 'TNA'
        self.assertEqual(results['TNA']['bought_quantity'], 150.0)
        self.assertAlmostEqual(
            results['TNA']['bought_amount'], -7537.5, places=2)
        self.assertEqual(results['TNA']['sold_quantity'], 150.0)
        self.assertAlmostEqual(
            results['TNA']['sold_amount'], 4720.0 + 2163.01, places=2)

        self.assertEqual(results['TNA']['closed_bought_quantity'], 150.0)
        self.assertAlmostEqual(
            results['TNA']['closed_bought_amount'], -7537.5, places=2)

        self.assertEqual(results['TNA']['open_bought_quantity'], 0.0)
        self.assertAlmostEqual(
            results['TNA']['open_bought_amount'], 0, places=2)

        self.assertAlmostEqual(
            results['TNA']['Profit/Loss'], -7537.5 + 4720.0 + 2163.01, places=2)
        self.assertAlmostEqual(
            results['TNA']['PercentProfit/Loss'], -8.68, places=2)
        # Complete Trades
        self.assertEqual(len(results['TNA']['all_trades']), 1)

        for i, expected_trade in enumerate(self.expect_trades['TNA']):
            got_trade = results['TNA']['all_trades'][i]
            self.assertEqual(got_trade['trade_date'],
                             expected_trade['trade_date'])
            self.assertEqual(got_trade['quantity'], expected_trade['quantity'])
            self.assertEqual(got_trade['amount'], expected_trade['amount'])
            self.assertEqual(
                got_trade['current_sold_qty'], expected_trade['current_sold_qty'])
            self.assertEqual(len(got_trade['sells']), len(
                expected_trade['sells']))
            for j, expected_sell in enumerate(expected_trade['sells']):
                got_sell = got_trade['sells'][j]
                self.assertEqual(got_sell['trade_date'],
                                 expected_sell['trade_date'])
                self.assertEqual(got_sell['quantity'],
                                 expected_sell['quantity'])
                self.assertEqual(got_sell['price'], expected_sell['price'])

                self.assertAlmostEqual(
                    got_sell['profit_loss'], expected_sell['profit_loss'], places=1)
                self.assertAlmostEqual(
                    got_sell['percent_profit_loss'], expected_sell['percent_profit_loss'], places=2)


if __name__ == '__main__':
    unittest.main()
