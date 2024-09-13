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
                {'Action': 'B', 'Quantity': 50.0, 'Price': 89.4964,
                 'Trade Date': '2024-08-26', 'Amount': -4474.82},
                {'Action': 'B', 'Quantity': 50.0, 'Price': 91.7,
                 'Trade Date': '2024-08-27', 'Amount': -4585.0},
                {'Action': 'B', 'Quantity': 50.0, 'Price': 94.85,
                 'Trade Date': '2024-08-30', 'Amount': -4742.5},
                {'Action': 'S', 'Quantity': 100.0, 'Price': 94.92,
                 'Trade Date': '2024-09-06', 'Amount': 9492.0},
                {'Action': 'S', 'Quantity': 25.0, 'Price': 94.94,
                 'Trade Date': '2024-09-06', 'Amount': 2373.5},
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

    def test_analyze_trades_sn(self):
        analyzer = TradingAnalyzer(self.data_dict[0])
        analyzer.analyze_trades()
        results = analyzer.get_results()

        # Check results for symbol 'SN'
        self.assertEqual(results['SN']['bought_quantity'], 275.0)
        self.assertAlmostEqual(
            results['SN']['bought_amount'], -25416.07, places=2)
        self.assertEqual(results['SN']['sold_quantity'], 225.0)
        self.assertAlmostEqual(
            results['SN']['sold_amount'], 20759.77, places=2)
        self.assertEqual(results['SN']['closed_bought_quantity'], 225.0)
        self.assertAlmostEqual(
            results['SN']['closed_bought_amount'], -20570.07, places=2)

        self.assertEqual(results['SN']['open_bought_quantity'], 50.0)
        self.assertAlmostEqual(
            results['SN']['open_bought_amount'], -25416.07 + 20570.07, places=2)

        self.assertAlmostEqual(results['SN']['Profit/Loss'], 189.7, places=2)
        self.assertAlmostEqual(
            results['SN']['PercentProfit/Loss'], 0.92, places=2)

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


if __name__ == '__main__':
    unittest.main()
