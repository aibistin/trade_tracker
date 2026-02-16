import logging
import os
from datetime import datetime

from lib.csv_processing_utils import CSVProcessor
from lib.db_utils import DatabaseInserter

log = logging.getLogger(__name__)

SKIPPED_ROWS = []

def write_skipped_rows(file_path, skipped_rows):
    """Writes skipped rows to a CSV file."""
    if skipped_rows:
        with open(file_path, "w") as f:
            for row in skipped_rows:
                f.write(",".join(str(value) for value in row.values()) + "\n")
        log.info(f"Skipped rows written to: {file_path}")
        log.info(f"Skipped rows: {len(skipped_rows)}")
    else:
        log.info("No skipped rows to write.")


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
    log.debug(f"Before Extract Symbol: {row['Symbol']}, Description row: {row['Description']}")
    if not len(row["Symbol"]) > 0:
        row["Symbol"] = csv_processor.extract_symbol_from_description(row)
    log.debug(f"After Extract Symbol: {row['Symbol']}, Description row: {row['Description']}")

    db_inserter = kwargs["db_inserter"] if "db_inserter" in kwargs else None
    account = kwargs["account"] if "account" in kwargs else None

    if not csv_processor.validate_price(row["Price"]):
        if row["Action"].startswith(("B", "S")) and len(row["Action"]) <= 3:
            log.warning(f"Skipping row due to invalid price: {row}")
            SKIPPED_ROWS.append(row)
            return None
        else:
            row["Price"] = 0


    symbol = row["Symbol"]
    # Some "Symbol" fields have an option pattern but are not option trades.
    # Example: "Exchange or Exercise","EE", "SOUN 09/20/2024 4.00 C".
    if csv_processor.is_option_label_pattern(row["Symbol"]):
        new_fields = csv_processor.extract_option_label(row)
        if new_fields:
            log.info(f"[{symbol}] Extracted option fields: {new_fields}")
            symbol = new_fields["Symbol"]
            add_option_fields(row, new_fields, csv_processor)

    if csv_processor.is_option_trade(row):
        if not new_fields:
            log.error(f"[{symbol}] Skipping Option Trade. Invalid option trade row: {row}")
            SKIPPED_ROWS.append(row)
            return None

    # row["Trade Type"] = row.get("Trade Type", csv_processor.determine_trade_type(row))
    row["Trade Type"] = csv_processor.determine_trade_type(row)
    row["Amount"] = csv_processor.calculate_amount(row)
    row["Stop@"] = csv_processor.calculate_stop(row)
    row["Sell@"] = csv_processor.calculate_sell(row)
    trade_date_str = csv_processor.convert_trade_date(row["Date"], "%m/%d/%Y")
    quantity = csv_processor.extract_quantity(row["Quantity"])
    if quantity is None:
        if row["Action"].startswith(("B", "S")):
            log.warning(f"[{symbol}] Skipping row due to zero quantity: {row}")
            SKIPPED_ROWS.append(row)
            return None
        else:
            quantity = 0

    if not trade_date_str:
        if row["Trade Type"] == "UK":
            log.warning(f"[{symbol}] Skipping row due to invalid or missing trade date: {row}")
        else:
            log.error(f"[{symbol}] Trade has invalid or missing trade date: {row}")

        SKIPPED_ROWS.append(row)
        return None

    trade_transaction = {
        "symbol": row["Symbol"],
        "name": row["Description"],
        "action": row["Action"],
        "label": row.get("Label", None),
        "trade_type": row["Trade Type"],
        "trade_date": trade_date_str,
        "expiration_date": row.get("Expiration Date", None),
        "reason": row.get( "Reason", ""),  # For internal use, 
        "quantity": quantity,
        "price": row["Price"],
        "amount": row["Amount"],
        "target_price": row.get("Target Price", None),
        "initial_stop_price": row.get("Initial Stop Price") or None,
        "projected_sell_price": row.get("Projected Sell Price") or None,
        "account": account,  # 'C', 'R', 'I'
    }

    try:
        db_inserter.insert_security(trade_transaction)
    except Exception as e:
        if "Security symbol" in str(e) and "already exists" in str(e):
            log.info(f"[{symbol}] Security {symbol} already exists")
        else:
            log.error(f"[{symbol}] Failed to insert security: {e}")
            SKIPPED_ROWS.append(row)
            return None

    if not db_inserter.transaction_exists(trade_transaction):
        log.info(f"[{symbol}] Inserting Transaction: {trade_transaction}")
        try:
            db_inserter.insert_transaction(trade_transaction)
        except Exception as e:
            if "Duplicate" in str(e):
                log.info(f"[{symbol}] {e}")
            else:
                log.error(f"[{symbol}] Failed to insert transaction: {e}")
                SKIPPED_ROWS.append(row)
            return None
        log.info(f"[{symbol}] Inserted transaction for: {trade_transaction}")
    else:
        log.debug(f"[{symbol}] Transaction exists: {trade_transaction}")

    return trade_transaction


def main():
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    processor = CSVProcessor("data/input", "data/output", "data/processed")
    db_path = "data/stock_trades.db"
    # Generate a timestamp string for filenames
    timestamp = datetime.now().strftime("%m%d%y%H%M%S")
    skipped_rows_file = f"data/error/skipped_rows_{timestamp}.csv"

    db_inserter = DatabaseInserter(db_path=db_path)
    log.info(f"Connected to: {db_path}")

    input_files = processor.get_input_files("transaction")

    if input_files:
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
        log.info(f"Completed writing to: {output_filename}")
    else:
        log.warning("No Transaction files to process!")

    db_inserter.close()
    log.info(f"Closed connection to: {db_path}")

    write_skipped_rows(skipped_rows_file, SKIPPED_ROWS)



if __name__ == "__main__":
    main()
