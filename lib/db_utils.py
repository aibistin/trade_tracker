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
            print(f"Warning: Security symbol {security['symbol']} already exists.")

    def transaction_exists(self, trade_transaction):
        """Checks if a transaction with the given details already exists in the database."""

        action_acronym = self.convert_action(trade_transaction["action"])
        price_float = self.validate_price(trade_transaction["price"])
        target_price_float = self.validate_price(trade_transaction["target_price"])

        self.cursor.execute(
            """
            SELECT * FROM trade_transaction
            WHERE symbol = ?   AND action = ? AND label = ? AND trade_type = ? 
            AND trade_date = ? AND expiration_date = ?      AND quantity = ? 
            AND price = ?      AND amount = ? AND target_price = ? AND account = ?
            """,
            (
                trade_transaction["symbol"],
                action_acronym,
                trade_transaction["label"],
                trade_transaction["trade_type"],
                trade_transaction["trade_date"],
                trade_transaction["expiration_date"],
                trade_transaction["quantity"],
                price_float,
                trade_transaction["amount"],
                target_price_float,
                trade_transaction["account"],
            ),
        )
        return self.cursor.fetchone() is not None

    def insert_transaction(self, trade_transaction):
        """Inserts a transaction into the 'trade_transaction' table using a dictionary."""
        action_acronym = self.convert_action(trade_transaction["action"])
        price_float = self.validate_price(trade_transaction["price"])
        target_price_float = self.validate_price(trade_transaction["target_price"])

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
                trade_transaction["symbol"],
                action_acronym,
                trade_transaction["label"],
                trade_transaction["trade_type"],
                trade_transaction["trade_date"],
                trade_transaction["expiration_date"],
                trade_transaction["reason"],
                trade_transaction["quantity"],
                price_float,
                trade_transaction["amount"],
                target_price_float,
                trade_transaction["initial_stop_price"],
                trade_transaction["projected_sell_price"],
                trade_transaction["account"],
            ),
        )
        self.conn.commit()

    def validate_price(self, price_in):
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
