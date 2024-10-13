# tests/test_yfinance.py
import unittest
from unittest.mock import patch
from lib.yfinance import YahooFinance

test_symbol = 'AAPL'

class TestYahooFinance(unittest.TestCase):

    def test_get_stock_data(self):
        """Tests the get_stock_data method for valid and invalid symbols."""

        # Test with a valid symbol
        yf_instance = YahooFinance(test_symbol) 
        yf_instance.get_stock_data()
        data = yf_instance.get_results()
        # print(f"[{test_symbol}] Results: {data}")

        self.assertIsInstance(data, dict)
        self.assertTrue(data) 

        # Assert the presence of specific keys (values may change)
        expected_keys = [
            'priceHint', 'previousClose', 'open', 'dayLow', 'dayHigh', 
            'regularMarketPreviousClose', 'regularMarketOpen', 'regularMarketDayLow', 
            'regularMarketDayHigh', 'exDividendDate', 'trailingPE', 'forwardPE', 
            'volume', 'regularMarketVolume', 'averageVolume', 'averageVolume10days', 
            'averageDailyVolume10Day', 'bid', 'ask', 'bidSize', 'askSize', 
            'marketCap', 'fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'priceToSalesTrailing12Months', 
            'fiftyDayAverage', 'twoHundredDayAverage', 'currency', 'enterpriseValue', 
            'profitMargins', 'floatShares', 'sharesOutstanding', 'sharesShort', 
            'sharesShortPriorMonth', 'sharesShortPreviousMonthDate', 'dateShortInterest', 
            'sharesPercentSharesOut', 'heldPercentInsiders', 'heldPercentInstitutions', 
            'shortRatio', 'shortPercentOfFloat', 'impliedSharesOutstanding', 'bookValue', 
            'priceToBook'
        ]
        for key in expected_keys:
            self.assertIn(key, data)

        # Invalid ticker test
        yf_instance_invalid = YahooFinance('INVALID_SYMBOL')
        yf_instance_invalid.get_stock_data()
        data_invalid = yf_instance_invalid.get_results()
        self.assertEqual(data_invalid, {})  # Expect an empty dictionary or handle the error case

    @patch('yfinance.Ticker')  # Mock the yfinance.Ticker class
    def test_get_mock_stock_data(self, mock_ticker):
        """Tests the get_stock_data method with mock data."""

        mock_data = {
            'priceHint': 2,
            'previousClose': 108.71,
            'open': 109.0,
            # ... (include all the keys you want to test)
            'priceToBook': 9.176231,
        }

        # Configure the mock object to return the mock data
        mock_ticker.return_value.info = mock_data  

        # Test with a valid symbol
        yf_instance = YahooFinance(test_symbol) 
        yf_instance.get_stock_data()
        data = yf_instance.get_results()

        self.assertIsInstance(data, dict)
        self.assertEqual(data, mock_data) 

        #TODO Assert the presence of specific keys


if __name__ == '__main__':
    unittest.main()