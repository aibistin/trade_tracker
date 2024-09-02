from lib.csv_processing_utils import CSVProcessor
from lib.db_utils import DatabaseInserter
import os
from datetime import datetime

def process_schwab_transactions_row(self, row, **kwargs):
    """Processes a row from the Schwab Transactions CSV file and inserts into the database."""

    db_inserter =  kwargs['db_inserter'] if 'db_inserter' in kwargs else None
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
        "",  # P/L
    ]

    # Insert/update security if needed
    db_inserter.insert_security(processed_row[0], processed_row[1])

    # Insert transaction if it doesn't exist
    if not db_inserter.transaction_exists(
            processed_row[0], processed_row[2], processed_row[6], 
            processed_row[3], processed_row[4], processed_row[7]
        ):

        db_inserter.insert_transaction(
            processed_row[0],  # symbol
            processed_row[2],  # action (assuming it's already converted to acronym)
            processed_row[6],  # trade_date
            None,              # reason (not provided in CSV, set to None)
            processed_row[3],  # quantity
            processed_row[4],  # price
            processed_row[7],  # amount
            processed_row[8],  # initial_stop_price
            processed_row[9],  # projected_sell_price
        )

    return processed_row


def main():
    processor = CSVProcessor("data/input", "data/output", "data/processed")
    db_inserter = DatabaseInserter(db_path="data/stock_trades.db")

    input_files = processor.get_input_files("transaction")

    if input_files:
        timestamp = datetime.now().strftime("%m%d%y%H%M%S")
        output_filename = f"transaction_record_{timestamp}.csv"
        output_header = ["Symbol", "Name", "Action", "Quantity", "Price",
                         "Fees", "Trade Date", "Amount", "Stop@", "Sell@", "P/L"]

        processor.process_files(
             input_files, output_filename, output_header, process_schwab_transactions_row,
        db_inserter=db_inserter)

        db_inserter.close()

    else:
        print(f"Warning: No Transaction files to process!")

if __name__ == "__main__":
    main()
