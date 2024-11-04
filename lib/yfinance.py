import yfinance as yf
import json, logging, os, time
from requests import Session
from requests_cache import CacheMixin, SQLiteCache
from requests_ratelimiter import LimiterMixin, MemoryQueueBucket
from pyrate_limiter import Duration, RequestRate, Limiter


# Combine requests_cache with rate-limiting
# to avoid triggering Yahoo's rate-limiter/blocker that can corrupt data.
class CachedLimiterSession(CacheMixin, LimiterMixin, Session):
    pass


timestr = time.strftime("%Y%m%d")
logging.basicConfig(
    filename=f"./logs/yfinance_{timestr}.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(lineno)d> %(message)s",
)


class YahooFinance:
    """
    Retrieves and stores stock data from Yahoo Finance.

    Attributes:
        stock_symbol (str): The symbol of the stock to retrieve data for.
        results (dict): A dictionary to store the retrieved stock data.
    """

    def __init__(self, stock_symbol):
        """
        Initializes YahooFinance with a stock symbol.
        Args:
            stock_symbol (str): The stock symbol.
        """
        self.stock_symbol = stock_symbol
        self.results = {}

        self.session = CachedLimiterSession(
            limiter=Limiter(
                RequestRate(2, Duration.SECOND * 5)
            ),  # max 2 requests per 5 seconds
            bucket_class=MemoryQueueBucket,
            backend=SQLiteCache("./data/yfinance/yfinance.cache"),
        )
        self.session.headers["User-agent"] = "trade-analyzer/1.0"


    def get_stock_data(self, max_age_minutes=60):  # Add max_age_minutes parameter
        """
        Fetches stock data from Yahoo Finance and caches it in a JSON file.
        Args:
            max_age_minutes (int, optional): The maximum age of the cached file in minutes.
                                             Defaults to 15 minutes.
        """
        project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_dir = os.path.join(project_dir, "data", "yfinance")
        file_path = os.path.join(data_dir, f"{self.stock_symbol}.json")

        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"The directory '{data_dir}' does not exist.")

        # Check if local cached file exists and is recent
        if (
            os.path.exists(file_path)
            and (time.time() - os.path.getmtime(file_path)) / 60 < max_age_minutes
        ):
            logging.debug(f"Using cached data for {self.stock_symbol}")
            try:
                with open(file_path, "r") as f:
                    self.results = json.load(f)
                return  # Return cached data
            except Exception as e:
                logging.error(f"Error reading cached data for {self.stock_symbol}: {e}")

        # Fetch fresh data from Yahoo Finance
        logging.info(f"Fetching fresh data for {self.stock_symbol}")
        try:
            # Using the inbuilt yFinance cache
            stock_results = yf.Ticker(self.stock_symbol, session=self.session)
            stock_results.actions # This is a dummy call to trigger the cache   

            if all(value is None for value in stock_results.info.values()):
                self.results = {}
            else:
                self.results = stock_results.info
                # ETFs don't have a currentPrice attribute
                # EQUITY, ETF, INDEX, CRYPTOCURRENCY, FUTURE, CURRENCY, OPTION
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
            logging.error(f"Error fetching data for {self.stock_symbol}: {e}")
            self.results = {}

    def get_results(self):
        """Returns the retrieved stock data."""
        return self.results


"""
## Some More Examples
stock_results = yf.Ticker(self.stock_symbol)
# get all stock info
self.results = stock_results.info
print(f"[{self.stock_symbol}] Info - {stock_results}")

# get historical market data
hist = stock_results.history(period="1mo")
# Date  Open  High  Low  Close  Volume  Dividends  Stock Splits
print(f"[{self.stock_symbol}] History - {hist}")

# show meta information about the history (requires history() to be called first)
stock_results.history_metadata
print(f"[{self.stock_symbol}] History Metadata - {stock_results.history_metadata}")

# show actions (dividends, splits, capital gains)
stock_results.actions
stock_results.dividends
stock_results.splits
stock_results.capital_gains  # only for mutual funds & etfs

# show share count
stock_results.get_shares_full(start="2022-01-01", end=None)

# show financials:
stock_results.calendar
stock_results.sec_filings
# - income statement
stock_results.income_stmt
stock_results.quarterly_income_stmt
# - balance sheet
stock_results.balance_sheet
stock_results.quarterly_balance_sheet
# - cash flow statement
stock_results.cashflow
stock_results.quarterly_cashflow
# see `Ticker.get_income_stmt()` for more options

# show holders
stock_results.major_holders
stock_results.institutional_holders
stock_results.mutualfund_holders
stock_results.insider_transactions
stock_results.insider_purchases
stock_results.insider_roster_holders

stock_results.sustainability

# show recommendations
stock_results.recommendations
stock_results.recommendations_summary
stock_results.upgrades_downgrades

# show analysts data
stock_results.analyst_price_targets
stock_results.earnings_estimate
stock_results.revenue_estimate
stock_results.earnings_history
print(f"[{self.stock_symbol}] Earnings History - {stock_results.earnings_history}")
stock_results.eps_trend

print(f"[{self.stock_symbol}] EPS Trend - {stock_results.eps_trend}")
stock_results.eps_revisions
stock_results.growth_estimates

# Show future and historic earnings dates, returns at most next 4 quarters and last 8 quarters by default.
# Note: If more are needed use stock_results.get_earnings_dates(limit=XX) with increased limit argument.
stock_results.earnings_dates

# show ISIN code - *experimental*
ISIN = International Securities Identification Number
stock_results.isin

# show options expirations
stock_results.options

# show news
stock_results.news

# get option chain for specific expiration
opt = stock_results.option_chain('YYYY-MM-DD')
data available via: opt.calls, opt.puts
"""
