import unittest
from lib.trading_analyzer import TradingAnalyzer


class TestTradingAnalyzer(unittest.TestCase):
    def setUp(self):
        self.data_list = [
            {'SN': [
                {'Id': '0001',
                 'Action': 'B', 'Quantity': 100.0, 'Price': 91.39,
                 'Trade Date': '2024-08-22', 'Amount': -9139.0},
                {'Id': '0002', 'Action': 'S', 'Quantity': 100.0, 'Price': 88.9427,
                 'Trade Date': '2024-08-23', 'Amount': 8894.27},
                # Sold 100

                {'Id': '0003', 'Action': 'B', 'Quantity': 50.0, 'Price': 89.4964,
                 'Trade Date': '2024-08-26', 'Amount': -4474.82},
                # Sold 50

                {'Id': '0004', 'Action': 'B', 'Quantity': 50.0, 'Price': 91.7,
                 'Trade Date': '2024-08-27', 'Amount': -4585.0},
                # Sold 50

                {'Id': '0005', 'Action': 'S', 'Quantity': 100.0, 'Price': 94.92,
                 'Trade Date': '2024-09-06', 'Amount': 9492.0},
                # Sold for previous two trades

                {'Id': '0006', 'Action': 'B', 'Quantity': 50.0, 'Price': 94.85,
                 'Trade Date': '2024-08-30', 'Amount': -4742.5},


                {'Id': '0007', 'Action': 'S', 'Quantity': 25.0, 'Price': 94.94,
                 'Trade Date': '2024-09-06', 'Amount': 2373.5},
                {'Id': '0008', 'Action': 'S', 'Quantity': 10.0, 'Price': 96.99,
                 'Trade Date': '2024-09-07', 'Amount': 969.9},

                {'Id': '0009', 'Action': 'B', 'Quantity': 25.0, 'Price': 98.99,
                 'Trade Date': '2024-09-10', 'Amount': -2474.75}

            ]},
            {'NVDA': [
                {'Id': '0011', 'Action': 'B', 'Quantity': 200.0, 'Price': 300.0,
                 'Trade Date': '2024-08-22', 'Amount': -60000.0},
                {'Id': '0012', 'Action': 'S', 'Quantity': 150.0, 'Price': 310.0,
                 'Trade Date': '2024-09-01', 'Amount': 46500.0},
                {'Id': '0013', 'Action': 'S', 'Quantity': 50.0, 'Price': 315.0,
                 'Trade Date': '2024-09-02', 'Amount': 15750.0}
            ]},
            {'TNA': [
                {'Id': '0111', 'Action': 'B', 'Quantity': 150.0, 'Price': 50.25,
                 'Trade Date': '2024-07-31', 'Amount': -7537.5},
                {'Id': '0112', 'Action': 'S', 'Quantity': 100.0, 'Price': 47.2,
                 'Trade Date': '2024-08-01', 'Amount': 4720.0},
                {'Id': '0113', 'Action': 'S', 'Quantity': 50.0, 'Price': 43.2601,
                 'Trade Date': '2024-08-27', 'Amount': 2163.01},
            ]},
            {'NAIL': [
                {'Id': '0222', 'Action':  'B', 'Quantity':  40.0, 'Price':  130.4599,
                    'Trade Date':  '2024-07-25', 'Amount': -5218.4},
                {'Id': '0223', 'Action':  'B', 'Quantity':  40.0, 'Price':  145.0,
                    'Trade Date':  '2024-07-26', 'Amount': -5800.0},
                {'Id': '0224', 'Action':  'B', 'Quantity':  50.0, 'Price':  127.1,
                    'Trade Date':  '2024-08-05', 'Amount': -6355.0},
                {'Id': '0225', 'Action':  'S', 'Quantity':  50.0, 'Price':  145.4,
                    'Trade Date':  '2024-08-27', 'Amount':  7270.0},
                {'Id': '0226', 'Action':  'S', 'Quantity':  80.0, 'Price':  147.5,
                    'Trade Date':  '2024-08-27', 'Amount':  11800.0},
                {'Id': '0227', 'Action':  'B', 'Quantity':  50.0, 'Price':  145.7,
                    'Trade Date':  '2024-08-30', 'Amount': -7285.0},
                {'Id': '0228', 'Action':  'S', 'Quantity':  50.0, 'Price':  140.6,
                    'Trade Date':  '2024-09-03', 'Amount':  7030.0},
                {'Id': '0229', 'Action':  'B', 'Quantity':  50.0, 'Price':  140.87,
                    'Trade Date':  '2024-09-12', 'Amount': -7043.5},
                {'Id': '0231', 'Action':  'S', 'Quantity':  50.0, 'Price':  156.38,
                    'Trade Date':  '2024-09-13', 'Amount':  7819.0},
                {'Id': '0232', 'Action':  'B', 'Quantity':  40.0, 'Price':  159.6201,
                    'Trade Date':  '2024-09-16', 'Amount': -6384.8}
            ]
            },
            {'NIO': [
                {'Id': '500',  'Action': 'B', 'Trade Date': '2024-09-24',
                    'Quantity': 1000.0, 'Price': 5.865, 'Amount': -5865.0, 'Account': 'R'},
                {'Id': '504',  'Action': 'B', 'Trade Date': '2024-09-26',
                    'Quantity': 200.0, 'Price': 5.8199, 'Amount': -1163.98, 'Account': 'R'},
                {'Id': '507',  'Action': 'B', 'Trade Date': '2024-09-25',
                    'Quantity': 800.0, 'Price': 5.73, 'Amount': -4584.0, 'Account': 'R'},
                {'Id': '509',  'Action': 'S', 'Trade Date': '2024-09-25',
                    'Quantity': 1000.0, 'Price': 5.5905, 'Amount': 5590.5, 'Account': 'R'},
                {'Id': '518',  'Action': 'S', 'Trade Date': '2024-09-30',
                    'Quantity': 400.0, 'Price': 7.38, 'Amount': 2952.0, 'Account': 'R'},
                {'Id': '530',  'Action': 'B', 'Trade Date': '2024-10-03',
                    'Quantity': 100.0, 'Price': 6.759, 'Amount': -675.9, 'Account': 'R'},
                {'Id': '536',  'Action': 'B', 'Trade Date': '2024-10-04',
                    'Quantity': 100.0, 'Price': 6.5399, 'Amount': -653.99, 'Account': 'C'}
            ]
            }
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
                    'quantity': 50,
                    'price':  94.85,
                    'amount': -4742.50,
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
            ],
            'NAIL': [
                {
                    'trade_date': '2024-07-25',
                    'quantity': 40,
                    'price':  130.4599,
                    'amount': -5218.4,
                    'current_sold_qty': 40,
                    'sells': [
                        {     # NAIL|S|2024-08-27|50.0|145.4|7270.0  -> 40 of 50
                            'trade_date': '2024-08-27',
                            'quantity': 40,
                            'price':  145.4,
                            'amount': (145.4 * 40),
                            'profit_loss': (145.4 * 40) - (130.4599 * 40),
                            'percent_profit_loss': (((145.4 * 40) - (130.4599 * 40)) / (130.4599 * 40)) * 100,
                        }
                    ]
                },
                {
                    'trade_date': '2024-07-26',
                    'quantity': 40,
                    'price':  145.00,
                    'amount': -5800.0,
                    'current_sold_qty': 40,
                    # Half of one sell
                    'sells': [
                        {
                            'trade_date': '2024-08-27',
                            'quantity': 10,
                            'price':  145.4,
                            'amount': (145.4 * 10),
                            'profit_loss': (145.4 * 10) - (145.00 * 10),
                            'percent_profit_loss': (((145.4 * 10) - (145.00 * 10)) / (145.00 * 10)) * 100,
                        },
                        {  # NAIL|S|2024-08-27|80.0|147.5|11800.0 -> 30 of 80
                            'trade_date': '2024-08-27',
                            'quantity': 30,
                            'price':  147.5,
                            'amount': (147.5 * 30),
                            'profit_loss': (147.5 * 30) - (145.00 * 30),
                            'percent_profit_loss': (((147.5 * 30) - (145.00 * 30)) / (145.00 * 30)) * 100,
                        }
                    ]
                },
                {  # NAIL|B|2024-08-05|50.0|127.1|-6355.0
                    'trade_date': '2024-08-05',
                    'quantity': 50,
                    'price':  127.10,
                    'amount': -6355.0,
                    'current_sold_qty': 50,
                    'sells': [
                        {   # NAIL|S|2024-08-27|80.0|147.5|11800.0 -> 30 + 50 of 80
                            'trade_date': '2024-08-27',
                            'quantity': 50,
                            'price':  147.50,
                            'amount': 7375.0,  # (11800.0/80) * 50
                            'profit_loss': (147.5 * 50) - (127.10 * 50),
                            'percent_profit_loss': (((147.5 * 50) - (127.1 * 50)) / (127.1 * 50)) * 100,
                        },
                    ]
                },
                {  # NAIL|B|2024-08-30|50.0|145.7|-7285.0
                    'trade_date': '2024-08-30',
                    'quantity': 50,
                    'price':  145.7,
                    'amount': -7285.0,
                    'current_sold_qty': 50,
                    'sells': [
                        {  # NAIL|S|2024-09-03|50.0|140.6|7030.0
                            'trade_date': '2024-09-03',
                            'quantity': 50,
                            'price':  140.6,
                            'amount': 7030.0,
                            'profit_loss': (140.6 * 50) - (145.7 * 50),
                            'percent_profit_loss': ((140.6 - 145.7)/145.7) * 100,
                        }
                    ]
                },
                {  # NAIL|B|2024-09-12|50.0|140.87|-7043.5
                    'trade_date': '2024-09-12',
                    'quantity': 50,
                    'price':  140.87,
                    'amount': -7043.5,
                    'current_sold_qty': 50,
                    'sells': [
                        {  # NAIL|S|2024-09-13|50.0|156.38|7819.0
                            'trade_date': '2024-09-13',
                            'quantity': 50,
                            'price':  156.38,
                            'amount': 7819.0,
                            'profit_loss': (156.38 * 50) - (140.87 * 50),
                            'percent_profit_loss': ((156.38 - 140.87)/140.87) * 100,
                        }
                    ]
                },
                {  # NAIL|B|2024-09-16|40.0|159.6201|-6384.8
                    'trade_date': '2024-09-16',
                    'quantity': 40,
                    'price':  159.6201,
                    'amount': -6384.8,
                    'current_sold_qty': 0,
                    'sells': []
                },
            ],
            'NIO': [
                {
                    'trade_date': '2024-09-24',
                    'quantity': 1000,
                    'price':  5.865,
                    'amount': -5865.0,
                    'current_sold_qty': 1000,
                    'sells': [
                        {
                            'trade_date': '2024-09-25',
                            'quantity': 1000,
                            'price':  5.5905,
                            'amount': 5590.5,
                            'profit_loss': 5590.5 - 5865.0,
                            'percent_profit_loss': ((5590.5 - 5865.0)/5865.0) * 100,
                        }
                    ],
                    'acccount': 'R',
                },
                {
                    'trade_date': '2024-09-25',
                    'quantity': 800,
                    'price':  5.73,
                    'amount': -4584.0,
                    'current_sold_qty': 400,
                    'sells': [
                        {
                            'trade_date': '2024-09-30',
                            'quantity': 400,
                            'price':  7.38,
                            'amount': 2952.0,
                            'profit_loss': 2952.0 - (4584.0/2),
                            'percent_profit_loss': ((2952.0 - (4584.0/2)) / (4584.0/2)) * 100,
                        }
                    ],
                    'acccount': 'R',
                },
                {
                    'trade_date': '2024-09-26',
                    'quantity': 200,
                    'price':  5.8199,
                    'amount': -1163.98,
                    'current_sold_qty': 0,
                    'sells': [],
                    'acccount': 'R',
                },
                {
                    'trade_date': '2024-10-03',
                    'quantity': 100,
                    'price':  6.759,
                    'amount': -675.9,
                    'current_sold_qty': 0,
                    'sells': [],
                    'acccount': 'R',
                },
                {
                    'trade_date': '2024-10-04',
                    'quantity': 100,
                    'price':  6.5399,
                    'amount': -653.99,
                    'current_sold_qty': 0,
                    'sells': [],
                    'acccount': 'C',
                },
            ]
        }

    # @unittest.skip("Skip SN")
    def test_analyze_trades_sn(self):
        analyzer = TradingAnalyzer(self.data_list[0])
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
        self.assertEqual(
            results['SN']['closed_bought_quantity'], 235.0, "SN closed_bought_quantity")
        self.assertAlmostEqual(
            results['SN']['closed_bought_amount'], expected_closed_bought_amount, places=2, msg="SN closed_bought_amount")

        self.assertEqual(results['SN']['open_bought_quantity'], 40.0)

        self.assertAlmostEqual(
            results['SN']['open_bought_amount'], expected_open_bought_amount, places=2)
        self.assertAlmostEqual(
            results['SN']['profit_loss'], expected_profit_loss, places=2)
        self.assertAlmostEqual(
            results['SN']['percent_profit_loss'], expected_profit_loss_percent, places=2)

        # Complete Trades
        self.assertEqual(
            len(results['SN']['all_trades']), 5, "SN - all_trades count")

        for i, expected_trade in enumerate(self.expect_trades['SN']):
            got_trade = results['SN']['all_trades'][i]
            self.assertEqual(got_trade['trade_date'],
                             expected_trade['trade_date'])
            self.assertEqual(
                got_trade['quantity'], expected_trade['quantity'], "SN - quantity")
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

    # @unittest.skip("Skip NVDA")
    def test_analyze_trades_nvda(self):
        analyzer = TradingAnalyzer(self.data_list[1])
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
            results['NVDA']['profit_loss'], 2250.0, places=2)
        self.assertAlmostEqual(
            results['NVDA']['percent_profit_loss'], 3.75, places=2)
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

    # @unittest.skip("Skip TNA")
    def test_analyze_trades_tna(self):
        analyzer = TradingAnalyzer(self.data_list[2])
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
            results['TNA']['profit_loss'], -7537.5 + 4720.0 + 2163.01, places=2)
        self.assertAlmostEqual(
            results['TNA']['percent_profit_loss'], -8.68, places=2)
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

    # @unittest.skip("Skip NAIL")
    def test_analyze_trades_nail(self):
        # Expected:
        analyzer = TradingAnalyzer(self.data_list[3])
        analyzer.analyze_trades()
        results = analyzer.get_results()

        # Check results for symbol 'NAIL'
        expected_bought_qty = 270
        expected_bought_amount = -38086.7
        expected_sold_qty = 230
        expected_sold_amount = 33919.0

        # -38086.7 + 6384.8 = −31701.9
        expected_closed_bought_amount = round(-38086.7 + 6384.8, 2)
        expected_open_bought_amount = -6384.8

        # bought amounts are negative numbers
        expected_profit_loss = expected_sold_amount + expected_closed_bought_amount
        expected_profit_loss_percent = abs(
            expected_profit_loss / expected_closed_bought_amount) * 100

        self.assertEqual(
            results['NAIL']['bought_quantity'], expected_bought_qty)

        self.assertAlmostEqual(
            results['NAIL']['bought_amount'], expected_bought_amount, places=2)

        self.assertEqual(results['NAIL']['sold_quantity'], expected_sold_qty)

        self.assertAlmostEqual(
            results['NAIL']['sold_amount'], expected_sold_amount, places=2)
        self.assertEqual(
            results['NAIL']['closed_bought_quantity'], expected_sold_qty, "NAIL closed_bought_quantity")

        self.assertAlmostEqual(
            results['NAIL']['closed_bought_amount'], expected_closed_bought_amount, places=2)

        self.assertEqual(results['NAIL']['open_bought_quantity'], 40.0)

        self.assertAlmostEqual(
            results['NAIL']['open_bought_amount'], expected_open_bought_amount, places=2)
        self.assertAlmostEqual(
            results['NAIL']['profit_loss'], expected_profit_loss, places=2)
        self.assertAlmostEqual(
            results['NAIL']['percent_profit_loss'], expected_profit_loss_percent, places=2)

        # Complete Trades
        self.assertEqual(len(results['NAIL']['all_trades']), 6)

        for i, expected_trade in enumerate(self.expect_trades['NAIL']):
            got_trade = results['NAIL']['all_trades'][i]
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
                self.assertEqual(got_sell['amount'], expected_sell['amount'])
                self.assertEqual(got_sell['price'], expected_sell['price'])

                self.assertAlmostEqual(
                    got_sell['profit_loss'], expected_sell['profit_loss'], places=2)
                self.assertAlmostEqual(
                    got_sell['percent_profit_loss'], expected_sell['percent_profit_loss'], places=2)

    def test_analyze_trades_nio(self):
        # Expected:
        analyzer = TradingAnalyzer(self.data_list[4])
        analyzer.analyze_trades()
        results = analyzer.get_results()

        # Check results for symbol 'NIO'
        expected_bought_qty = 2200
        # -5865.0 -4584.0 -1163.98 -675.9 -653.99
        expected_bought_amount = -12942.87
        expected_sold_qty = 1400
        # 5590.5 + 2952.0
        expected_sold_amount = 8542.5
        # -5865.0 - (4584.0/2)
        expected_closed_bought_amount = -8157.0
        # (-4584.0/2) -1163.98 -675.9 -653.99
        expected_open_bought_amount = -4785.87

        expected_profit_loss = expected_sold_amount + expected_closed_bought_amount
        expected_profit_loss_percent = abs(
            expected_profit_loss / expected_closed_bought_amount) * 100

        self.assertEqual(
            results['NIO']['bought_quantity'], expected_bought_qty)

        self.assertAlmostEqual(
            results['NIO']['bought_amount'], expected_bought_amount, places=2)

        self.assertEqual(results['NIO']['sold_quantity'], expected_sold_qty)

        self.assertAlmostEqual(
            results['NIO']['sold_amount'], expected_sold_amount, places=2)
        self.assertEqual(
            results['NIO']['closed_bought_quantity'], expected_sold_qty, "NIO closed_bought_quantity")

        self.assertAlmostEqual(
            results['NIO']['closed_bought_amount'], expected_closed_bought_amount, places=2, msg="NIO closed_bought_amount")

        self.assertEqual(results['NIO']['open_bought_quantity'], 800.0)

        self.assertAlmostEqual(
            results['NIO']['open_bought_amount'], expected_open_bought_amount, places=2)
        self.assertAlmostEqual(
            results['NIO']['profit_loss'], expected_profit_loss, places=2)
        self.assertAlmostEqual(
            results['NIO']['percent_profit_loss'], expected_profit_loss_percent, places=2)

        # Complete Trades
        self.assertEqual(len(results['NIO']['all_trades']), 5)

        for i, expected_trade in enumerate(self.expect_trades['NIO']):
            got_trade = results['NIO']['all_trades'][i]
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
                self.assertEqual(got_sell['amount'], expected_sell['amount'])
                self.assertEqual(got_sell['price'], expected_sell['price'])

                self.assertAlmostEqual(
                    got_sell['profit_loss'], expected_sell['profit_loss'], places=2, msg="NIO - profit_loss")
                self.assertAlmostEqual(
                    got_sell['percent_profit_loss'], expected_sell['percent_profit_loss'], places=2, msg="NIO - percent_profit_loss")


if __name__ == '__main__':
    unittest.main()
