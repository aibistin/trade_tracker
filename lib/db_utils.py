import logging
import sqlite3
from sqlite3 import Connection, Cursor
from typing import Dict, Optional, Any, Union
from contextlib import contextmanager
from lib.dataclasses.ActionMapping import ActionMapping

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Base class for database connection handling."""

    def __init__(self, db_path: Optional[str] = None, db: Optional[Any] = None):
        # self.conn = sqlite3.connect(db_path, timeout=10)
        # self.cursor = self.conn.cursor()
        self._conn: Optional[Connection] = None
        self._cursor: Optional[Cursor] = None

        if db:
            self._conn = db.engine.raw_connection()  # Use the provided db connection
            self._cursor = self._conn.cursor()
        else:
            self._conn = sqlite3.connect(db_path, timeout=10)
            self._cursor = self._conn.cursor()

        self.action_mapping = ActionMapping()  # Initialize action mapping

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logging.error(f"DB connection exc_type: {exc_type}")
        if exc_val:
            logging.error(f"DB connection exc_val: {exc_val}")
        if exc_tb:
            logging.error(f"DB connection TraceBack: {exc_tb}")
        self.close()

    @property
    def connection(self) -> Connection:
        if not self._conn:
            raise ConnectionError("Database connection not established")
        return self._conn

    @property
    def cursor(self) -> Cursor:
        if not self._cursor:
            raise ConnectionError("Database cursor not available")
        return self._cursor

    def close(self) -> None:
        """Close database connection gracefully."""
        if self._conn:
            self._conn.close()
            self._conn = None
            self._cursor = None


class DatabaseInserter(DatabaseConnection):
    """Handles database insert operations with transaction support."""

    def __init__(self, db_path: Optional[str] = None, db: Optional[Any] = None):
        super().__init__(db_path, db)
        self.action_mapping = ActionMapping()

    @contextmanager
    def transaction(self):
        """Context manager for transaction handling."""
        try:
            yield self.cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error("Transaction rolled back: %s", e)
            raise

    def insert_security(self, security: Dict[str, str]) -> None:
        """
        Insert security into 'security' table.

        Args:
            security: Dictionary with 'symbol' and 'name' keys

        Raises:
            sqlite3.Error: On database operation failure
        """
        query = """
            INSERT INTO security (symbol, name)
            VALUES (:symbol, :name)
        """
        try:
            with self.transaction():
                self.cursor.execute(query, security)
        except sqlite3.IntegrityError:
            logger.info("Security %s already exists", security.get("symbol"))
        except sqlite3.Error as e:
            logger.error("Error inserting security: %s", e)
            raise

    def transaction_exists(self, trade_transaction: Dict[str, Any]) -> bool:
        """
        Check if transaction exists in database.

        Args:
            trade_transaction: Dictionary with transaction details

        Returns:
            bool: True if transaction exists
        """
        query = """
            SELECT 1 FROM trade_transaction
            WHERE 
                symbol = :symbol AND
                action = :action AND
                trade_type = :trade_type AND
                trade_date = :trade_date AND
                quantity = :quantity AND
                price = :price AND
                amount = :amount AND
                account = :account
            LIMIT 1
        """

        params = {
            "symbol": trade_transaction["symbol"],
            "action": self.convert_action(trade_transaction["action"]),
            "trade_type": trade_transaction.get("trade_type", ""),
            "trade_date": trade_transaction["trade_date"],
            "quantity": trade_transaction["quantity"],
            "price": self._parse_price(trade_transaction.get("price")),
            "amount": trade_transaction["amount"],
            "account": trade_transaction.get("account", "U"),
        }

        try:
            with self.transaction():
                self.cursor.execute(query, params)
                return bool(self.cursor.fetchone())
        except sqlite3.Error as e:
            logger.error("Error checking transaction existence: %s", e)
            return False

    def insert_transaction(self, trade_transaction: Dict[str, Any]) -> None:
        """
        Insert transaction into 'trade_transaction' table.

        Args:
            trade_transaction: Dictionary with transaction details

        Raises:
            ValueError: For invalid price formats
            sqlite3.Error: On database operation failure
        """
        query = """
            INSERT INTO trade_transaction (
                symbol, action, label, trade_type, trade_date, expiration_date,
                reason, quantity, price, amount, target_price,
                initial_stop_price, projected_sell_price, account
            ) VALUES (
                :symbol, :action, :label, :trade_type, :trade_date, :expiration_date,
                :reason, :quantity, :price, :amount, :target_price,
                :initial_stop_price, :projected_sell_price, :account
            )
        """
        params = self._prepare_transaction_params(trade_transaction)
        logger.debug(f"Inserting Params: {params}")

        try:
            with self.transaction():
                self.cursor.execute(query, params)
        except sqlite3.Error as e:
            logger.error("Error inserting transaction: %s", e)
            logger.error(f"Params: {params}")
            raise

        # action_acronym = self.convert_action(trade_transaction["action"])
        # stock_symbol = trade_transaction["symbol"];

        # # Call the new method
        # price_float = self._get_price(trade_transaction["price"], action_acronym, stock_symbol)

        # target_price_float = self._get_price(trade_transaction["target_price"], action_acronym, stock_symbol)

        # self.cursor.execute(
        #     """
        #     INSERT INTO trade_transaction (
        #         symbol, action, label, trade_type, trade_date, expiration_date,
        #         reason, quantity, price, amount, target_price,
        #         initial_stop_price, projected_sell_price, account
        #     )
        #     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        #     """,
        #     (
        #         stock_symbol,
        #         action_acronym,
        #         trade_transaction["label"] or None,
        #         trade_transaction["trade_type"],
        #         trade_transaction["trade_date"],
        #         trade_transaction["expiration_date"] or None,
        #         trade_transaction["reason"] or None,
        #         trade_transaction["quantity"],
        #         price_float,
        #         trade_transaction["amount"],
        #         target_price_float or None,
        #         trade_transaction["initial_stop_price"] or None,
        #         trade_transaction["projected_sell_price"] or None,
        #         trade_transaction["account"] or None,
        #     ),
        # )
        # self.conn.commit()

    def _prepare_transaction_params(
        self, trade_transaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare parameters for transaction insertion."""
        action_acronym = self.convert_action(trade_transaction["action"])

        return {
            "symbol": trade_transaction["symbol"],
            "action": action_acronym,
            "label": trade_transaction.get("label"),
            "trade_type": trade_transaction.get("trade_type", ""),
            "trade_date": trade_transaction["trade_date"],
            "expiration_date": trade_transaction.get("expiration_date"),
            "reason": trade_transaction.get("reason"),
            "quantity": trade_transaction["quantity"],
            "price": self._parse_price(trade_transaction.get("price"), action_acronym),
            "amount": trade_transaction["amount"],
            "target_price": self._parse_price(trade_transaction.get("target_price")),
            "initial_stop_price": trade_transaction.get("initial_stop_price"),
            "projected_sell_price": trade_transaction.get("projected_sell_price"),
            "account": trade_transaction.get("account", "U"),
        }


    def convert_action(self, action: str) -> str:
        """Convert action name to standardized acronym."""
        if self.action_mapping.acronym_exists(action):
            return action
        return self.action_mapping.get_acronym(action) or "UK"

    def _parse_price(
        self, price: Union[str, float, None], action: Optional[str] = None
    ) -> Optional[float]:
        """Parse and validate price values."""
        if price in (None, ""):
            if action in ("EE", "EXP"):
                logger.info("Defaulting price to 0.0 for action %s", action)
                return 0.0
            return None

        try:
            return float(str(price).replace("$", "").strip())
        except ValueError:
            logger.warning("Invalid price format: %s", price)
            raise ValueError(f"Invalid price value: {price}")

            # For Option Exercise/Expiration, we allow price to be None
            # print(f"INFO[db_utils][{symbol}]: Entering 0.0 for price when Action = {action_acronym}")
            # price_float =  0.0
        # else:
        # print(f"Warning[db_utils][{symbol}]: Price is None for Action = {action_acronym}.")

        # price_float = self._get_price(trade_transaction["price"], action_acronym, stock_symbol)
        # target_price_float = self._get_price(trade_transaction["target_price"], action_acronym, stock_symbol)

    # def convert_action(self, action):
    #     """Converts the full action name to its corresponding acronym.
    #     Any updates to this should also be added to the database, "validate_action_trigger" function.
    #     """
    #     # Return acronym if found, else 'UK' for 'Unknown'
    #     return self.action_mapping.get_acronym(action)

    # def insert_security(self, security):
    #     """Inserts security into the 'security' table using a dictionary.
    #     Args:
    #         security (dict):  {"symbol": row["Symbol"], "name": row["Description"]}
    #     """
    #     try:
    #         self.cursor.execute(
    #             "INSERT INTO security (symbol, name) VALUES (?, ?)",
    #             (security["symbol"], security["name"]),
    #         )
    #         self.conn.commit()
    #     except sqlite3.IntegrityError:
    #         print(f"INFO: Security symbol {security['symbol']} already exists.")

    # def transaction_exists(self, trade_transaction):
    #     """Checks if a transaction with the given details already exists in the database."""

    #     action_acronym = self.convert_action(trade_transaction["action"])
    #     stock_symbol = trade_transaction["symbol"];

    #     price_float = self._get_price(trade_transaction["price"], action_acronym, stock_symbol)

    #     print('[db_utils]: Checking if transaction exists in the database...')
    #     print(f'[db_utils]: Symbol: {stock_symbol} Action: {action_acronym} Date: {trade_transaction["trade_date"]}')
    #     print(f'[db_utils]: TradeType: {trade_transaction["trade_type"]}')

    #     self.cursor.execute(
    #         """
    #         SELECT * FROM trade_transaction
    #         WHERE symbol = ?  AND action = ?  AND trade_type = ?
    #         AND trade_date = ? AND  quantity = ?
    #         AND price = ?  AND amount = ? AND account = ?
    #         """,
    #         (
    #             stock_symbol,
    #             action_acronym,
    #             trade_transaction["trade_type"],
    #             trade_transaction["trade_date"],
    #             trade_transaction["quantity"],
    #             price_float,
    #             trade_transaction["amount"],
    #             trade_transaction["account"] or 'U',
    #         ),
    #     )
    #     return self.cursor.fetchone() is not None

    # def insert_transaction(self, trade_transaction):
    #     """Inserts a transaction into the 'trade_transaction' table using a dictionary."""

    #     action_acronym = self.convert_action(trade_transaction["action"])
    #     stock_symbol = trade_transaction["symbol"];

    #     # Call the new method
    #     price_float = self._get_price(trade_transaction["price"], action_acronym, stock_symbol)

    #     target_price_float = self._get_price(trade_transaction["target_price"], action_acronym, stock_symbol)

    #     self.cursor.execute(
    #         """
    #         INSERT INTO trade_transaction (
    #             symbol, action, label, trade_type, trade_date, expiration_date,
    #             reason, quantity, price, amount, target_price,
    #             initial_stop_price, projected_sell_price, account
    #         )
    #         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    #         """,
    #         (
    #             stock_symbol,
    #             action_acronym,
    #             trade_transaction["label"] or None,
    #             trade_transaction["trade_type"],
    #             trade_transaction["trade_date"],
    #             trade_transaction["expiration_date"] or None,
    #             trade_transaction["reason"] or None,
    #             trade_transaction["quantity"],
    #             price_float,
    #             trade_transaction["amount"],
    #             target_price_float or None,
    #             trade_transaction["initial_stop_price"] or None,
    #             trade_transaction["projected_sell_price"] or None,
    #             trade_transaction["account"] or None,
    #         ),
    #     )
    #     self.conn.commit()

    # def _get_price(self, price, action_acronym, symbol):
    #     """
    #     Converts price to float based on various conditions.

    #     Args:
    #         price: The price value to convert
    #         action_acronym: The action type acronym
    #         symbol: The stock symbol for logging

    #     Returns:
    #         float: Converted price or None
    #     """
    #     price_float = None
    #     if price not in ["", None]:
    #         price_float = self.validate_and_convert_to_float(price)
    #     elif action_acronym in ('EE', 'EXP'):
    #         # For Option Exercise/Expiration, we allow price to be None
    #         print(f"INFO[db_utils][{symbol}]: Entering 0.0 for price when Action = {action_acronym}")
    #         price_float =  0.0
    #     else:
    #         print(f"Warning[db_utils][{symbol}]: Price is None for Action = {action_acronym}.")

    #     return price_float

    # def validate_and_convert_to_float(self, price_in):
    #     """Validate price format (number or number with '$')."""
    #     if not price_in:
    #         return False

    #     try:
    #         return (
    #             float(price_in.replace("$", ""))
    #             if isinstance(price_in, str)
    #             else price_in
    #         )
    #     except ValueError:
    #         print(f"Warning[db_utils]: Invalid price format: {price_in}")
    #         return False

    # # def close(self):
    # #     """Closes the database connection."""
    # #     self.conn.close()
