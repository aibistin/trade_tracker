# tests/test_yfinance.py
import unittest
from unittest.mock import patch
from lib.yfinance import YahooFinance

test_symbol = "AAPL"
mock_test_symbol = "FAKE1"


class TestYahooFinance(unittest.TestCase):

    def test_get_stock_data(self):
        """Tests the get_stock_data method for valid and invalid symbols."""

        # Test with a valid symbol
        yf_instance = YahooFinance(test_symbol)
        yf_instance.get_stock_data()
        got_data = yf_instance.get_results()

        self.assertTrue(got_data, msg=f"Got no data for {test_symbol}")
        self.assertIsInstance(
            got_data, dict, msg=f"Got data is not a dictionary: {got_data}"
        )

        # Assert the presence of specific keys (values may change)
        expected_keys = [
            "priceHint",
            "previousClose",
            "open",
            "dayLow",
            "dayHigh",
            "regularMarketPreviousClose",
            "regularMarketOpen",
            "regularMarketDayLow",
            "regularMarketDayHigh",
            "exDividendDate",
            "trailingPE",
            "forwardPE",
            "volume",
            "regularMarketVolume",
            "averageVolume",
            "averageVolume10days",
            "averageDailyVolume10Day",
            "bid",
            "ask",
            "bidSize",
            "askSize",
            "marketCap",
            "fiftyTwoWeekLow",
            "fiftyTwoWeekHigh",
            "priceToSalesTrailing12Months",
            "fiftyDayAverage",
            "twoHundredDayAverage",
            "currency",
            "enterpriseValue",
            "profitMargins",
            "floatShares",
            "sharesOutstanding",
            "sharesShort",
            "sharesShortPriorMonth",
            "sharesShortPreviousMonthDate",
            "dateShortInterest",
            "sharesPercentSharesOut",
            "heldPercentInsiders",
            "heldPercentInstitutions",
            "shortRatio",
            "shortPercentOfFloat",
            "impliedSharesOutstanding",
            "bookValue",
            "priceToBook",
        ]
        for key in expected_keys:
            self.assertIn(
                key, got_data, msg=f"Key {key} not found in got_data: {got_data}"
            )

        # Invalid ticker test
        yf_instance_invalid = YahooFinance("INVALID_SYMBOL")
        yf_instance_invalid.get_stock_data()
        data_invalid = yf_instance_invalid.get_results()
        # Expect an empty dictionary or handle the error case
        self.assertEqual(
            data_invalid, {}, msg=f"Got data for invalid symbol: {data_invalid}"
        )

    # @unittest.skip("Skipping test_get_mock_stock_data")
    @patch("yfinance.Ticker")  # Mock the yfinance.Ticker class
    def test_get_mock_stock_data(self, mock_ticker):
        """Tests the get_stock_data method with mock data."""
    
        mock_data = {
            "priceHint": 2,
            "previousClose": 108.71,
            "open": 109.0,
            "dayLow": 107.5,
            "dayHigh": 110.0,
            "regularMarketPreviousClose": 108.71,
            "regularMarketOpen": 109.0,
            "regularMarketDayLow": 107.5,
            "regularMarketDayHigh": 110.0,
            "exDividendDate": None,
            "trailingPE": 15.2,
            "forwardPE": 14.8,
            "volume": 5000000,
            "regularMarketVolume": 5000000,
            "averageVolume": 4500000,
            "averageVolume10days": 4700000,
            "averageDailyVolume10Day": 4700000,
            "bid": 108.5,
            "ask": 109.5,
            "bidSize": 1000,
            "askSize": 1200,
            "marketCap": 2000000000,
            "fiftyTwoWeekLow": 90.0,
            "fiftyTwoWeekHigh": 120.0,
            "priceToSalesTrailing12Months": 5.5,
            "fiftyDayAverage": 105.0,
            "twoHundredDayAverage": 100.0,
            "currency": "USD",
            "enterpriseValue": 2100000000,
            "profitMargins": 0.25,
            "floatShares": 8000000,
            "sharesOutstanding": 10000000,
            "sharesShort": 500000,
            "sharesShortPriorMonth": 450000,
            "sharesShortPreviousMonthDate": "2023-09-30",
            "dateShortInterest": "2023-10-15",
            "sharesPercentSharesOut": 0.05,
            "heldPercentInsiders": 0.1,
            "heldPercentInstitutions": 0.7,
            "shortRatio": 1.2,
            "shortPercentOfFloat": 0.0625,
            "impliedSharesOutstanding": 10000000,
            "bookValue": 12.0,
            "priceToBook": 9.176231,
            "quoteType": "EQUITY"  # Ensure this key is included if needed
        }
    
        # Configure the mock object to return the mock data
        mock_ticker.return_value.info = mock_data
    
        yf_instance = YahooFinance(mock_test_symbol, ticker_class=mock_ticker)
        yf_instance.get_stock_data()
        got_data = yf_instance.get_results()
    
        self.assertIsInstance(
            got_data, dict, msg=f"Got data isn't a dictionary: {got_data}"
        )
    
        for key, value in mock_data.items():
            self.assertIn(key, got_data, msg=f"Key {key} not found in got_data")
            self.assertEqual(
                got_data[key],
                value,
                msg=f"Value for key {key} does not match: {got_data[key]} != {value}",
            )


if __name__ == "__main__":
    unittest.main()
