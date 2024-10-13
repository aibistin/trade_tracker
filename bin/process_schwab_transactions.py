from lib.csv_processing_utils import CSVProcessor
from lib.db_utils import DatabaseInserter
import os
from datetime import datetime


def process_schwab_transactions_row(self, row, **kwargs):
    """Processes a row from the Schwab Transactions CSV file and inserts into the database."""

    db_inserter = kwargs['db_inserter'] if 'db_inserter' in kwargs else None
    account = kwargs['account'] if 'account' in kwargs else None
    quantity = CSVProcessor.extract_quantity(row["Quantity"])

    if not CSVProcessor.validate_price(row["Price"]):
        if row['Action'].startswith(('B', 'S')) and len(row['Action']) <= 3:
            print(f"Skipping row due to invalid price: {row}")
            return None

    # Calculate the transaction amount.
    row['Amount'] = str(self.calculate_amount(row))
    row['Stop@'] = str(self.calculate_stop(row))
    row['Sell@'] = str(self.calculate_sell(row))

    # Convert and validate trade date
    trade_date_str = CSVProcessor.convert_trade_date(row["Date"], "%m/%d/%Y")
    if not trade_date_str:
        print(f"Skipping row due to invalid or missing trade date: {row}")
        return None

    # Create processed row if all validations pass
    processed_row = [
        row["Symbol"],
        row["Description"],
        row["Action"],
        quantity,
        row["Price"],
        row["Fees & Comm"],
        trade_date_str,
        row["Amount"],
        row['Stop@'],
        row['Sell@'],
        "",  # P/L,
        account
    ]

    # Insert/update security if needed
    db_inserter.insert_security(processed_row[0], processed_row[1])

    # Insert transaction if it doesn't exist
    if not db_inserter.transaction_exists(
        processed_row[0], processed_row[2], processed_row[6],
        processed_row[3], processed_row[4], processed_row[7], account
    ):

        db_inserter.insert_transaction(
            processed_row[0],  # symbol
            # action (assuming it's already converted to acronym)
            processed_row[2],
            processed_row[6],  # trade_date
            "",                # reason (not provided in CSV, set to '')
            processed_row[3],  # quantity
            processed_row[4],  # price
            processed_row[7],  # amount
            processed_row[8],  # initial_stop_price
            processed_row[9],  # projected_sell_price
            account,          # 'C', 'R', 'I'
        )
        print(f"[{processed_row[0]} Inserted transaction for:")
    else:
        print(f"[{processed_row[0]} Transaction already exists for:")

    print(f"[{processed_row[0]} Date:{processed_row[6]}, Action:{processed_row[2]}, Qty:{processed_row[3]}, Price:{processed_row[4]}")

    return processed_row


def main():
    processor = CSVProcessor("data/input", "data/output", "data/processed")
    # db_path= "data/test.db"
    db_path = "data/stock_trades.db"

    db_inserter = DatabaseInserter(db_path=db_path)
    print(f"Connected to: {db_path}")

    input_files = processor.get_input_files("transaction")

    if input_files:
        timestamp = datetime.now().strftime("%m%d%y%H%M%S")
        output_filename = f"transaction_record_{timestamp}.csv"
        output_header = ["Symbol", "Name", "Action", "Quantity", "Price",
                         "Fees", "Trade Date", "Amount", "Stop@", "Sell@", "P/L", "Act."]

        processor.process_files(
            input_files, output_filename, output_header, process_schwab_transactions_row,
            db_inserter=db_inserter)

        print("Completed writing to: " + output_filename)

    else:
        print(f"Warning: No Transaction files to process!")

    db_inserter.close()
    print(f"Closed connection to: {db_path}")


if __name__ == "__main__":
    main()
