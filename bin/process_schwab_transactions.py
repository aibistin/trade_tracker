from lib.csv_processing_utils import CSVProcessor
from lib.db_utils import DatabaseInserter
import os
from datetime import datetime


def add_option_fields(row, new_fields, csv_processor):
    """Adds new fields to the row dictionary."""
    row["Symbol"] = new_fields["Symbol"]
    row["Label"] = new_fields["Label"]
    row["Trade Type"] = new_fields["Trade Type"]
    row["Expiration Date"] = csv_processor.convert_trade_date(
        new_fields["Expiration Date"], "%m/%d/%Y"
    )
    row["Target Price"] = new_fields["Target Price"]


def process_schwab_transactions_row(csv_processor, row, **kwargs):
    """Processes a row from the Schwab Transactions CSV file and inserts into the database."""

    # Populate missing Symbol field if necessary
    print(
        f"Before Extract Symbol: {row['Symbol']}, Description row: {row['Description']}"
    )
    if not len(row["Symbol"]) > 0:
        row["Symbol"] = csv_processor.extract_symbol_from_description(row)
    print(
        f"After Extract Symbol: {row['Symbol']}, Description row: {row['Description']}"
    )

    db_inserter = kwargs["db_inserter"] if "db_inserter" in kwargs else None
    account = kwargs["account"] if "account" in kwargs else None

    if not csv_processor.validate_price(row["Price"]):
        if row["Action"].startswith(("B", "S")) and len(row["Action"]) <= 3:
            print(f"Skipping row due to invalid price: {row}")
            return None

    symbol = row["Symbol"]
    # Some "Symbol" fields have an option pattern but are not option trades.
    # Example: "Exchange or Exercise","EE", "SOUN 09/20/2024 4.00 C".
    if csv_processor.is_option_label_pattern(row["Symbol"]):
        new_fields = csv_processor.extract_option_label(row)
        if new_fields:
            print(f"[{symbol}] Extracted option fields: {new_fields}")
            symbol = new_fields["Symbol"]
            add_option_fields(row, new_fields, csv_processor)

    if csv_processor.is_option_trade(row):
        if not new_fields:
            print(
                f"[{symbol}] ERROR: Skipping Option Trade. Invalid option trade row: {row}"
            )
            return None

    row["Trade Type"] = row.get("Trade Type", csv_processor.determine_trade_type(row))
    row["Amount"] = str(csv_processor.calculate_amount(row))
    row["Stop@"] = str(csv_processor.calculate_stop(row))
    row["Sell@"] = str(csv_processor.calculate_sell(row))

    trade_date_str = csv_processor.convert_trade_date(row["Date"], "%m/%d/%Y")
    if not trade_date_str:
        if row["Trade Type"] == "O":
            print(
                f"[{symbol}] Skipping row due to invalid or missing trade date: {row}"
            )
        else:
            print(f"[{symbol}] ERROR: Trade has invalid or missing trade date: {row}")
        return None

    trade_transaction = {
        "symbol": row["Symbol"],
        "name": row["Description"],
        "action": row["Action"],
        "label": row.get("Label", None),
        "trade_type": row.get("Trade Type", "O"),
        "trade_date": trade_date_str,
        "expiration_date": row.get("Expiration Date", None),
        "reason": "",
        "quantity": csv_processor.extract_quantity(row["Quantity"]),
        "price": row["Price"],
        "amount": row["Amount"],
        "target_price": row.get("Target Price", None),
        "initial_stop_price": "",
        "projected_sell_price": "",
        "account": account,  # 'C', 'R', 'I'
    }

    try:
        db_inserter.insert_security(trade_transaction)
    except Exception as e:
        if "Security symbol" in str(e) and "already exists" in str(e):
            print(f"[{symbol}] INFO: Security {symbol} already exists")
        else:
            print(f"[{symbol}] ERROR: Failed to insert security: {e}")
            return None

    if not db_inserter.transaction_exists(trade_transaction):
        print(f"[{symbol}] Inserting Transaction: {trade_transaction}")
        try:
            db_inserter.insert_transaction(trade_transaction)
        except Exception as e:
            if "Duplicate" in str(e):
                print(f"[{symbol}] INFO: {e}")
            else:
                print(f"[{symbol}] ERROR: Failed to insert transaction: {e}")
            return None
        print(f'[{symbol}] Inserted transaction for: {trade_transaction["trade_date"]}')
    else:
        print(f'[{symbol}] Transaction exists: {trade_transaction["trade_date"]}')


    return trade_transaction


def main():
    processor = CSVProcessor("data/input", "data/output", "data/processed")
    db_path = "data/stock_trades.db"

    db_inserter = DatabaseInserter(db_path=db_path)
    print(f"Connected to: {db_path}")

    input_files = processor.get_input_files("transaction")

    if input_files:
        timestamp = datetime.now().strftime("%m%d%y%H%M%S")
        output_filename = f"transaction_record_{timestamp}.csv"

        output_header = [
            "Symbol",
            "Name",
            "Action",
            "Label",
            "Trade Type",
            "Quantity",
            "Price",
            "Fees",
            "Trade Date",
            "Expiration Date",
            "Amount",
            "Target Price",
            "Stop@",
            "Sell@",
            "P/L",
            "Act.",
        ]

        processor.process_files(
            input_files,
            output_filename,
            output_header,
            process_schwab_transactions_row,
            db_inserter=db_inserter,
        )

        print("Completed writing to: " + output_filename)

    else:
        print(f"Warning: No Transaction files to process!")

    db_inserter.close()
    print(f"Closed connection to: {db_path}")


if __name__ == "__main__":
    main()
