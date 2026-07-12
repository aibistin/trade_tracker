# tests/test_yfinance.py
import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from lib.yfinance import YahooFinance, extract_price, get_market_price, get_quote

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

    def test_sanitize_cache_filename(self):
        self.assertEqual(
            YahooFinance._sanitize_cache_filename("BRK/A 01/17/2025"),
            "BRK_A_01_17_2025",
        )

    def test_load_cached_data_valid_file(self):
        yf_instance = YahooFinance("CACHED")
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump({"currentPrice": 42.0}, f)
        try:
            yf_instance.load_cached_data(f.name)
            self.assertEqual(yf_instance.get_results(), {"currentPrice": 42.0})
        finally:
            os.unlink(f.name)

    def test_load_cached_data_corrupt_file_returns_empty(self):
        yf_instance = YahooFinance("CORRUPT")
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write("{not valid json")
        try:
            yf_instance.load_cached_data(f.name)
            self.assertEqual(yf_instance.get_results(), {})
        finally:
            os.unlink(f.name)

    def test_is_cache_valid(self):
        yf_instance = YahooFinance("ANY")
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write("{}")
        try:
            self.assertTrue(yf_instance.is_cache_valid(f.name, max_age_minutes=60))
            self.assertFalse(yf_instance.is_cache_valid(f.name, max_age_minutes=0))
            self.assertFalse(yf_instance.is_cache_valid("/nonexistent.json", 60))
        finally:
            os.unlink(f.name)

    @patch("yfinance.Ticker")
    def test_fetch_error_returns_empty_results(self, mock_ticker):
        mock_ticker.side_effect = Exception("network down")
        yf_instance = YahooFinance("BROKEN", ticker_class=mock_ticker)
        yf_instance.get_stock_data(max_age_minutes=0)
        self.assertEqual(yf_instance.get_results(), {})


class TestPriceHelpers(unittest.TestCase):
    """Tests for the module-level quote/price helper functions."""

    def test_extract_price_stock_prefers_current_price(self):
        info = {"currentPrice": 10.0, "regularMarketPrice": 9.0, "lastPrice": 8.0}
        self.assertEqual(extract_price(info), 10.0)

    def test_extract_price_stock_falls_back_to_regular_market(self):
        self.assertEqual(extract_price({"regularMarketPrice": 9.0}), 9.0)

    def test_extract_price_option_prefers_last_price(self):
        info = {"currentPrice": 10.0, "regularMarketPrice": 9.0, "lastPrice": 8.0}
        self.assertEqual(extract_price(info, is_option=True), 8.0)

    def test_extract_price_empty_info(self):
        self.assertIsNone(extract_price({}))
        self.assertIsNone(extract_price(None))

    @patch("lib.yfinance.YahooFinance")
    def test_get_quote_returns_info(self, MockYF):
        MockYF.return_value.get_results.return_value = {"currentPrice": 5.0}
        self.assertEqual(get_quote("FAKE"), {"currentPrice": 5.0})

    @patch("lib.yfinance.YahooFinance")
    def test_get_quote_swallows_errors(self, MockYF):
        MockYF.return_value.get_stock_data.side_effect = Exception("API down")
        self.assertEqual(get_quote("FAKE"), {})

    @patch("lib.yfinance.YahooFinance")
    def test_get_market_price(self, MockYF):
        MockYF.return_value.get_results.return_value = {"lastPrice": 3.5}
        self.assertEqual(get_market_price("FAKE250117C00150000", is_option=True), 3.5)
        MockYF.return_value.get_results.return_value = {}
        self.assertIsNone(get_market_price("FAKE"))


if __name__ == "__main__":
    unittest.main()
