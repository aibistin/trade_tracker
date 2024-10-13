import csv
import os
import re
from datetime import datetime


class CSVProcessor:
    def __init__(self, input_dir, output_dir, processed_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.processed_dir = processed_dir
        print("CSVProcessor: Input Dir: " + self.input_dir)

        # Ensure directories exist
        # os.makedirs(self.input_dir, exist_ok=True)
        # os.makedirs(self.output_dir, exist_ok=True)
        # os.makedirs(self.processed_dir, exist_ok=True)

    @staticmethod
    def extract_quantity(quantity_str):
        """Extract numeric quantity (int or float) from string."""

        quantity = CSVProcessor.convert_to_float(quantity_str)
        if quantity is not None:
            return quantity
        else:
            print(f"Warning: Unexpected quantity format: {quantity_str}")
            return 0


    @staticmethod
    def convert_trade_date(trade_date_str, date_format="%m/%d/%Y"):
        """Convert trade date string to YYYY-MM-DD format."""
        try:
            trade_datetime = datetime.strptime(trade_date_str, date_format)
            return trade_datetime.strftime("%Y-%m-%d")
        except ValueError:
            print(f"Warning: Invalid date format: {trade_date_str}")
            return None

    @staticmethod
    def convert_to_float(some_input):

        if isinstance(some_input, str):
            new_input = re.sub(r"[^\d\.]", "", some_input)
        else:
            new_input = some_input

        try:
            result = float(new_input)
        except ValueError:
            print(f"Warning: Invalid float format: {some_input}")
            result = None
        return result

    @staticmethod
    def validate_price(price_str):
        """Validate price format (number or number with '$')."""
        if not price_str:
            return False

        price = CSVProcessor.convert_to_float(price_str)
        if price is None:
            print(f"Warning: Invalid price format: {price_str}")
            return False

        return price

    def calculate_amount(self, row):
        """Calculates the amount based on quantity and price. For Buy Sell & Re-Invest Orders"""

        if not row['Action'].startswith(('Buy', 'Sell', 'Reinvest')):
            return None

        price = CSVProcessor.convert_to_float(row['Price'])
        if price is None:
            print(f"Warning: Invalid format for security: {row['Symbol']}")
            print(f"Price: {row['Price']},  Action: {row['Action']}")
            return 0

        quantity = CSVProcessor.convert_to_float(row['Quantity'])
        if quantity is None:
            print(f"Warning: Invalid Quantity for security: {row['Symbol']}")
            print(f"Price: {row['Quantity']},  Action: {row['Action']}")
            print(f"Quantity: {quantity}, Price: {str(price)}")
            return 0.0

        amount = 0
        try:
            if any(x in row['Action'] for x in ['Open', 'Close']):
                # Convert an Option Open/Close to standard 100*price 
                amount = round((quantity * price) * 100, 2)
            else:
                amount = round((quantity * price), 2)

            return - amount if row['Action'].startswith('Buy') else amount

        except ValueError:
            print("Warning: Invalid quantity or price format.")
            print(f"Quantity: {quantity}, Price: {str(price)}")
            return 0.0

    def calculate_stop(self, row):
        """Calculates the stop price for a buy order."""
        if not row['Action'].startswith('Buy'):
            return None

        # price = float(re.sub("[^\d\.]", "", row['Price']))
        price = CSVProcessor.convert_to_float(row['Price'])

        try:
            return round(price * 0.95)
        except ValueError:
            print("Warning(calculate_stop): Invalid price format: " + str(price))
            return 0.0

    def calculate_sell(self, row):
        """Calculates the sell price."""
        if not row['Action'].startswith('Buy'):
            return 0.0

        # price = float(re.sub("[^\d\.]", "", row['Price']))
        price = CSVProcessor.convert_to_float(row['Price'])

        try:
            return round(price * 1.15)
        except ValueError:
            print("Warning(calculate_sell): Invalid price format: " + str(price))
            return None

    def output_file_has_data(self, file_path):
        """Checks if a CSV file has data rows beyond the header."""
        with open(file_path, "r") as f:
            line_count = len(f.readlines())
            return line_count > 1

    def sort_output_file(self, file_path):
        """Sorts a CSV file by Symbol (ascending) and Trade Date (ascending)."""
        data = []
        with open(file_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)

        # Sort the data using a lambda function for multiple keys
        sorted_data = sorted(data, key=lambda row: (
            row["Symbol"], row["Trade Date"], row["Action"]))

        # Write the sorted data back to the file
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(reader.fieldnames)  # Write header
            for row in sorted_data:
                writer.writerow(row.values())

    def sort_output_file(self, file_path):
        """Sorts a CSV file by Symbol (ascending) and Trade Date (ascending),
           excluding the header row.
        """
        with open(file_path, "r") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames  # Store the header row
            data = list(reader)  # Read the rest of the data into a list

        # Sort the data (excluding the header)
        sorted_data = sorted(data, key=lambda row: (
            row["Symbol"], row["Trade Date"]))

        # Write the sorted data back to the file (including the header)
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for row in sorted_data:
                writer.writerow(row.values())

    def redo_output_file(self, output_file, line_count=0):
        """ Remove the output file if it's empty. Sort it if it's full."""
        if line_count > 1:
            self.sort_output_file(output_file)
            print(f"Info: Created output file {output_file}")
        else:
            os.remove(output_file)
            print(
                f"Warning: Output file {output_file} was empty and has been deleted.")

    def get_input_files(self, keyword, file_extension=".csv"):
        """Get input files matching the keyword and extension."""
        if not os.path.exists(self.input_dir):
            print(f"Error: Input directory '{self.input_dir}' does not exist.")
            return []
        return [os.path.join(self.input_dir, f) for f in os.listdir(self.input_dir)
                if f.lower().endswith(file_extension) and keyword.lower() in f.lower()]

    # def process_files(self, input_files, output_filename, output_header, row_processor, field_names = None):
    def process_files(self, input_files, output_filename, output_header, row_processor,
                      **kwargs):
        """Main file processing logic."""
        output_file = os.path.join(self.output_dir, output_filename)
        field_names = kwargs['field_names'] if 'field_names' in kwargs else None
        db_inserter = kwargs['db_inserter'] if 'db_inserter' in kwargs else None
        seen_rows = set()
        out_count = 0

        with open(output_file, "w", newline="") as out_csv:
            writer = csv.writer(out_csv)
            writer.writerow(output_header)

            for input_file in input_files:
                account = 'I'  # C = Contributory, R = Roth Contributory, I = Individual
                print(f"Info: Reading file path: {input_file}")
                file_name = os.path.basename(input_file)
                print(f"Info: File Name: {file_name}")

                if file_name.lower().startswith('c'):
                    account = 'C'
                elif file_name.lower().startswith('r'):
                    account = 'R'

                with open(input_file, "r") as in_csv:
                    reader = csv.DictReader(in_csv, fieldnames=field_names)
                    for row in reader:
                        # Deduplication
                        row_tuple = tuple([row.values(), account])
                        if row_tuple in seen_rows:
                            continue
                        seen_rows.add(row_tuple)

                        # Custom row processing
                        processed_row = row_processor(
                            self, row, db_inserter=db_inserter, account=account)
                        if processed_row:
                            writer.writerow(processed_row)
                            out_count += 1
                    # Move to processed
                    os.rename(input_file, os.path.join(
                        self.processed_dir, os.path.basename(input_file)))

        # Ensure output file is handled properly
        self.redo_output_file(output_file, out_count)
