import yfinance as yf
from yfinance import Ticker
import json
import logging
import os
import time

log = logging.getLogger(__name__)


class YahooFinance:
    """
    Retrieves and stores stock data from Yahoo Finance.

    Attributes:
        stock_symbol (str): The symbol of the stock to retrieve data for.
        results (dict): A dictionary to store the retrieved stock data.
    """

    def __init__(self, stock_symbol, ticker_class=Ticker):
        """
        Initializes YahooFinance with a stock symbol and a ticker class.
        Args:
            stock_symbol (str): The stock symbol.
            ticker_class: The class used to fetch stock data (default is yf.Ticker).
        """
        self.stock_symbol = stock_symbol
        self.ticker_class = ticker_class  # Store the ticker class
        self.results = {}

    @staticmethod
    def _sanitize_cache_filename(symbol):
        """Convert a symbol to a safe filename for caching (handles option tickers with slashes/spaces)."""
        return symbol.replace("/", "_").replace(" ", "_")

    def get_stock_data(self, max_age_minutes=60):
        """
        Fetches stock data from Yahoo Finance and caches it in a JSON file.
        Args:
            max_age_minutes (int, optional): The maximum age of the cached file in minutes.
                                             Defaults to 60 minutes.

        """
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(project_dir, "data", "yfinance")
        safe_name = self._sanitize_cache_filename(self.stock_symbol)
        file_path = os.path.join(data_dir, f"{safe_name}.json")

        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"The directory '{data_dir}' does not exist.")

        # Check if local cached file exists and is recent
        if self.is_cache_valid(file_path, max_age_minutes):
            log.debug(f"Using cached data for {self.stock_symbol}")
            self.load_cached_data(file_path)
            return  # Return cached data

        # Fetch fresh data from Yahoo Finance
        log.info(f"Fetching fresh data for {self.stock_symbol}")
        self.fetch_fresh_data(file_path)

    def is_cache_valid(self, file_path, max_age_minutes):
        """Check if the cached file is valid based on its age."""
        return (
            os.path.exists(file_path)
            and (time.time() - os.path.getmtime(file_path)) / 60 < max_age_minutes
        )

    def load_cached_data(self, file_path):
        """Load data from the cached JSON file."""
        try:
            with open(file_path, "r") as f:
                self.results = json.load(f)
                log.debug(f"Loaded cached for {self.stock_symbol}: {self.results}")
        except Exception as e:
            log.error(f"Error reading cached data for {self.stock_symbol}: {e}")
            self.results = {}

    def fetch_fresh_data(self, file_path):
        """Fetch fresh stock data and cache it."""
        try:
            stock_results = self.ticker_class(
                self.stock_symbol
            )  # Use the injected ticker class
            stock_results.actions  # This is a dummy call to trigger the cache
            log.debug(f"Got results for {self.stock_symbol}: {stock_results.info}")

            if all(value is None for value in stock_results.info.values()):
                self.results = {}
            else:
                self.results = stock_results.info
                if (
                    self.results["quoteType"] == "ETF"
                    and "currentPrice" not in stock_results.info
                ):
                    stock_results.history(
                        period="1d"
                    )  # history needs to be called first
                    self.results["currentPrice"] = stock_results.history_metadata[
                        "regularMarketPrice"
                    ]

            # Cache the data to a JSON file
            with open(file_path, "w") as f:
                json.dump(self.results, f, indent=4)

        except Exception as e:
            log.error(f"Error fetching data for {self.stock_symbol}: {e}")
            self.results = {}

    def get_results(self):
        """Returns the retrieved stock data."""
        return self.results


def get_quote(ticker):
    """Fetch the cached Yahoo Finance info dict for a ticker.

    Returns {} on any fetch error so callers can degrade gracefully.
    """
    try:
        yf_client = YahooFinance(ticker)
        yf_client.get_stock_data()
        return yf_client.get_results() or {}
    except Exception as e:
        log.warning(f"Failed to fetch quote for {ticker}: {e}")
        return {}


def extract_price(info, is_option=False):
    """Pick the best available price field from a Yahoo info dict.

    Options report lastPrice; stocks report currentPrice. Each falls back to
    regularMarketPrice (and options to currentPrice) when missing.
    """
    if not info:
        return None
    if is_option:
        return (
            info.get("lastPrice")
            or info.get("regularMarketPrice")
            or info.get("currentPrice")
        )
    return info.get("currentPrice") or info.get("regularMarketPrice")


def get_market_price(ticker, is_option=False):
    """Fetch the current market price for a ticker, or None if unavailable."""
    return extract_price(get_quote(ticker), is_option=is_option)
