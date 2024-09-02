# from ..lib.csv_processing_utils import CSVProcessor
# from csv_processing_utils import CSVProcessor
from lib.csv_processing_utils import CSVProcessor
import os


from datetime import datetime


def check_directories(output_dir, input_dir, processed_dir):
    """Checks the existence and writability of specified directories.

    Args:
        output_dir: The path to the output directory.
        input_dir: The path to the input directory.
        processed_dir: The path to the processed directory.

    Returns:
        True if all directories exist and are writable, False otherwise.
    """

    for dir_path in (output_dir, input_dir, processed_dir):
        if not os.path.isdir(dir_path):
            print(f"Error: '{dir_path}' does not exist or is not a directory.")
            return False

        if not os.access(dir_path, os.W_OK):
            print(f"Error: '{dir_path}' is not writable.")
            return False

    return True  # All checks passed


# **kwards not used in this script but must be pssed anyway
def process_schwab_orders(self, row, **kwargs):
    """Processes a row from the Schwab Transactions CSV file."""

    # Extract and validate quantity
    row["Quantity"] = CSVProcessor.extract_quantity(row["Quantity"])

    # Validate price
    if not CSVProcessor.validate_price(row["Price"]):
        if row['Action'].startswith(('B', 'S')) and not row['Status'].startswith('Canc'):
            print(f"Skipping row due to invalid price: {row}")
        return None

    # Convert and validate trade date
    trade_date_str = CSVProcessor.convert_trade_date(
        row["Time and Date(ET)"], "%I:%M %p %m/%d/%Y")

    if not trade_date_str:
        print(f"Skipping row due to invalid or missing trade date: {row}")
        return None

    # Calculate the transaction amount.
    row['Amount'] = str(self.calculate_amount(row))
    row['Stop@'] = str(self.calculate_stop(row))
    row['Sell@'] = str(self.calculate_sell(row))

    # Create processed row if all validations pass
    processed_row = [
        row["Symbol"],
        row["Name"],  # "Name of security"
        row["Action"],
        "",  # Reason
        row["Quantity"],
        row["Price"],  # 'Fill Price'
        trade_date_str,
        row["Order Number"],
        row["Amount"],
        row['Stop@'],
        row['Sell@'],
        "",  # P/L
    ]

    return processed_row


if __name__ == "__main__":
    processor = CSVProcessor("data/input", "data/output", "data/processed")
    input_files = processor.get_input_files("order")
    # Symbol,Strategy Name,Name of security,Status,Action,Quantity|Face Value,Price,Timing,Fill Price,Time and Date(ET),Last Activity Date(ET),Reinvest Capital Gains,Order Number
    input_fieldnames = ['Symbol', 'Strategy Name', 'Name', 'Status', 'Action', 'Quantity', 'Request Price',
                        'Timing', 'Price', 'Time and Date(ET)', 'Last Activity Date(ET)', 'Reinvest Capital Gains', 'Order Number']

    if input_files:
        timestamp = datetime.now().strftime("%m%d%y%H%M%S")
        output_filename = f"order_record_{timestamp}.csv"
        output_header = ["Symbol", "Name", "Action", "Reason", "Quantity", "Price",
                         "Trade Date", "Order#", "Amount", "Stop@", "Sell@", "P/L"]

        processor.process_files(
            input_files, output_filename, output_header, process_schwab_orders,
            field_names=input_fieldnames)
    else:
        print(f"Warning: No Order files to process!")
