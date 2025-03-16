import sqlite3


class DatabaseInserter:
    def __init__(self, db_path=None, db=None):
        # self.conn = sqlite3.connect(db_path, timeout=10)
        # self.cursor = self.conn.cursor()
        if db:
            self.conn = db.engine.raw_connection()  # Use the provided db connection
            self.cursor = self.conn.cursor()
        else:
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()

    def convert_action(self, action):
        """Converts the full action name to its corresponding acronym.
        Any updates to this should also be added to the database, "validate_action_trigger" function.
        """

        action_map = {
            "Bank Interest": "BI",
            "Bond Interest": "BOI",
            "Buy": "B",
            "Buy to Close": "BC",
            "Buy to Open": "BO",
            "Cash Dividend": "CD",
            "Cash Merger": "CM",
            "Cash Merger Adj": "CMJ",
            "Exchange or Exercise": "EE",
            "Expired": "EXP",
            "Funds Received": "FR",
            "Internal Transfer": "IT",
            "Journal": "J",
            "Journaled Shares": "JS",
            "MoneyLink Transfer": "MT",
            "Pr Yr Div Reinvest": "PYDR",
            "Qual Div Reinvest": "QDR",
            "Qualified Dividend": "QD",
            "Reinvest Shares": "RS",
            "Reinvest Dividend": "RD",
            "Reverse Split": "RSP",
            "Sell": "S",
            "Sell to Close": "SC",
            "Sell to Open": "SO",
            "Stock Split": "SSP",
            "Tax Withholding": "TXW",
        }

        # Return acronym if found, else 'UK' for 'Unknown'
        return action_map.get(action, "UK")

    def insert_security(self, security):
        """Inserts security into the 'security' table using a dictionary.
        Args:
            security (dict):  {"symbol": row["Symbol"], "name": row["Description"]}
        """
        try:
            self.cursor.execute(
                "INSERT INTO security (symbol, name) VALUES (?, ?)",
                (security["symbol"], security["name"]),
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            print(f"INFO: Security symbol {security['symbol']} already exists.")

    def transaction_exists(self, trade_transaction):
        """Checks if a transaction with the given details already exists in the database."""

        action_acronym = self.convert_action(trade_transaction["action"])
        stock_symbol = trade_transaction["symbol"];

        price_float = self._get_price(trade_transaction["price"], action_acronym, stock_symbol)

        print('[db_utils]: Checking if transaction exists in the database...')
        print(f'[db_utils]: Symbol: {stock_symbol} Action: {action_acronym} Date: {trade_transaction["trade_date"]}')

        self.cursor.execute(
            """
            SELECT * FROM trade_transaction
            WHERE symbol = ?  AND action = ?  AND trade_type = ? 
            AND trade_date = ? AND  quantity = ? 
            AND price = ?  AND amount = ? AND account = ?
            """,
            (
                stock_symbol,
                action_acronym,
                trade_transaction["trade_type"],
                trade_transaction["trade_date"],
                trade_transaction["quantity"],
                price_float,
                trade_transaction["amount"],
                trade_transaction["account"] or 'U',
            ),
        )
        return self.cursor.fetchone() is not None

    def insert_transaction(self, trade_transaction):
        """Inserts a transaction into the 'trade_transaction' table using a dictionary."""

        action_acronym = self.convert_action(trade_transaction["action"])
        stock_symbol = trade_transaction["symbol"];

        # Call the new method
        price_float = self._get_price(trade_transaction["price"], action_acronym, stock_symbol)

        target_price_float = self._get_price(trade_transaction["target_price"], action_acronym, stock_symbol)

        self.cursor.execute(
            """
            INSERT INTO trade_transaction (
                symbol, action, label, trade_type, trade_date, expiration_date,
                reason, quantity, price, amount, target_price,
                initial_stop_price, projected_sell_price, account
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stock_symbol,
                action_acronym,
                trade_transaction["label"] or None,
                trade_transaction["trade_type"],
                trade_transaction["trade_date"],
                trade_transaction["expiration_date"] or None,
                trade_transaction["reason"] or None,
                trade_transaction["quantity"],
                price_float,
                trade_transaction["amount"],
                target_price_float or None,
                trade_transaction["initial_stop_price"] or None,
                trade_transaction["projected_sell_price"] or None,
                trade_transaction["account"] or None,
            ),
        )
        self.conn.commit()

    def _get_price(self, price, action_acronym, symbol):
        """
        Converts price to float based on various conditions.
            
        Args:
            price: The price value to convert
            action_acronym: The action type acronym
            symbol: The stock symbol for logging
            
        Returns:
            float: Converted price or None
        """
        price_float = None
        if price not in ["", None]:
            price_float = self.validate_and_convert_to_float(price)
        elif action_acronym in ('EE', 'EXP'):
            # For Option Exercise/Expiration, we allow price to be None
            print(f"INFO[db_utils][{symbol}]: Entering 0.0 for price when Action = {action_acronym}")
            price_float =  0.0
        else:
            print(f"Warning[db_utils][{symbol}]: Price is None for Action = {action_acronym}.")

        return price_float


    def validate_and_convert_to_float(self, price_in):
        """Validate price format (number or number with '$')."""
        if not price_in:
            return False

        try:
            return (
                float(price_in.replace("$", ""))
                if isinstance(price_in, str)
                else price_in
            )
        except ValueError:
            print(f"Warning[db_utils]: Invalid price format: {price_in}")
            return False

    def close(self):
        """Closes the database connection."""
        self.conn.close()
