# tests/test_yfinance.py
import unittest
from unittest.mock import patch, MagicMock
from lib.yfinance import YahooFinance

test_symbol = "AAPL"
mock_test_symbol = "FAKE1"

MOCK_STOCK_DATA = {
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
    "quoteType": "EQUITY",
}


class TestYahooFinance(unittest.TestCase):

    @patch("yfinance.Ticker")
    def test_get_stock_data(self, mock_ticker):
        """Tests the get_stock_data method for valid and invalid symbols."""

        # --- Valid symbol ---
        mock_ticker.return_value.info = MOCK_STOCK_DATA
        mock_ticker.return_value.actions = MagicMock()

        yf_instance = YahooFinance(test_symbol, ticker_class=mock_ticker)
        yf_instance.get_stock_data(max_age_minutes=0)  # bypass file cache
        got_data = yf_instance.get_results()

        self.assertTrue(got_data, msg=f"Got no data for {test_symbol}")
        self.assertIsInstance(got_data, dict, msg=f"Got data is not a dictionary: {got_data}")

        for key in MOCK_STOCK_DATA:
            self.assertIn(key, got_data, msg=f"Key {key} not found in got_data")

        # --- Invalid symbol: all-None info → should return {} ---
        mock_ticker.return_value.info = {k: None for k in MOCK_STOCK_DATA}
        mock_ticker.return_value.actions = MagicMock()

        yf_instance_invalid = YahooFinance("INVALID_SYMBOL", ticker_class=mock_ticker)
        yf_instance_invalid.get_stock_data(max_age_minutes=0)
        data_invalid = yf_instance_invalid.get_results()

        self.assertEqual(data_invalid, {}, msg=f"Got data for invalid symbol: {data_invalid}")

    @patch("yfinance.Ticker")
    def test_get_mock_stock_data(self, mock_ticker):
        """Tests the get_stock_data method with mock data."""

        mock_ticker.return_value.info = MOCK_STOCK_DATA
        mock_ticker.return_value.actions = MagicMock()

        yf_instance = YahooFinance(mock_test_symbol, ticker_class=mock_ticker)
        yf_instance.get_stock_data(max_age_minutes=0)
        got_data = yf_instance.get_results()

        self.assertIsInstance(got_data, dict, msg=f"Got data isn't a dictionary: {got_data}")

        for key, value in MOCK_STOCK_DATA.items():
            self.assertIn(key, got_data, msg=f"Key {key} not found in got_data")
            self.assertEqual(
                got_data[key],
                value,
                msg=f"Value for key {key} does not match: {got_data[key]} != {value}",
            )


if __name__ == "__main__":
    unittest.main()
