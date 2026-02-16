import logging
import sqlite3
from sqlite3 import Connection, Cursor
from typing import Dict, Optional, Any, Union
from contextlib import contextmanager
from lib.models.ActionMapping import ActionMapping

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
            raise RuntimeError(f"Failed to insert security {security['symbol']}: {e}")

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
                label = :label AND
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
            "label": trade_transaction.get("label"),
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
        except sqlite3.IntegrityError:
            logger.warning(
                "Transaction for %s already exists", trade_transaction.get("symbol")
            )
        except sqlite3.Error as e:
            logger.error("Error inserting transaction: %s", e)
            logger.error(f"Params: {params}")
            raise RuntimeError(
                f"Failed to insert transaction for {trade_transaction['symbol']}: {e}"
            )

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
