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
        """Converts the full action name to its corresponding acronym."""
        action_map = {
            "Bank Interest": "BI",
            "Bond Interest": "BOI",
            "Buy": "B",
            "Buy to Open": "BO",
            "Cash Merger": "CM",
            "Cash Merger Adj": "CMJ",
            "Funds Received": "FR",
            "Internal Transfer": "IT",
            "Journal": "J",
            "Journaled Shares": "JS",
            "Qual Div Reinvest": "QDR",
            "Qualified Dividend": "QD",
            "Reinvest Shares": "RS",
            "Reinvest Dividend": "RD",
            "Sell": "S",
            "Sell to Close": "SC",
            "Stock Split": "SS"
        }
#        return action_map.get(action, action)  # Return acronym if found, else original action
        # Return acronym if found, else 'UK' for 'Unknown'
        return action_map.get(action, action) if action in action_map else 'UK'

    def insert_security(self, symbol, name):
        """Inserts a security into the 'security' table."""
        try:
            self.cursor.execute(
                "INSERT INTO security (symbol, name) VALUES (?, ?)", (symbol, name))
            self.conn.commit()
        except sqlite3.IntegrityError:
            # Handle duplicate symbol (if needed, you can update the existing record instead)
            print(f"Warning: Security with symbol '{symbol}' already exists.")

    def transaction_exists(self, symbol, action, trade_date, quantity, price, amount, account):
        """Checks if a transaction with the given details already exists in the database."""

        action_acronym = self.convert_action(action)  # Convert action
        price_float = self.validate_price(price)

        self.cursor.execute("""
            SELECT * FROM trade_transaction
            WHERE symbol = ? AND action = ? AND trade_date = ?
                  AND quantity = ? AND price = ? AND amount = ? AND account = ?
        """, (symbol, action_acronym, trade_date, quantity, price_float, amount, account))
        return self.cursor.fetchone() is not None  # True if a row is found, False otherwise

    def insert_transaction(self, symbol, action, trade_date, reason, quantity, price, amount, initial_stop_price, projected_sell_price, account):
        """Inserts a transaction into the 'transaction' table, converting the action first."""
        action_acronym = self.convert_action(action)  # Convert action
        price_float = self.validate_price(price)

        self.cursor.execute("""
            INSERT INTO trade_transaction (symbol, action, trade_date, reason, quantity, price, amount, initial_stop_price, projected_sell_price, account)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (symbol, action_acronym, trade_date, reason, quantity, price_float, amount, initial_stop_price, projected_sell_price, account))
        self.conn.commit()

    def close(self):
        """Closes the database connection."""
        self.conn.close()

    def validate_price(self, price_in):
        """Validate price format (number or number with '$')."""
        if not price_in:
            return False

        try:
            return float(price_in.replace("$", "")) if isinstance(price_in, str) else price_in
        except ValueError:
            print(f"Warning[db_utils]: Invalid price format: {price_in}")
            return False
