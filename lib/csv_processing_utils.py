import csv
import os
import re
from datetime import datetime
from lib.models.ActionMapping import ActionMapping

option_label_pattern = r"\s*\S+\s+\d{1,2}/\d{1,2}/\d{2,4}\s+\d+\.\d+\s+[CP]"
default_symbol = "NONE"  # Ex: Moneylink transfer transactions.


class CSVProcessor:
    def __init__(self, input_dir, output_dir, processed_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.processed_dir = processed_dir
        print("CSVProcessor: Input Dir: " + self.input_dir)

        self.action_mapping = ActionMapping()  # Initialize action mapping

    def extract_quantity(self, quantity_str):
        """Extract numeric quantity (int or float) from string."""

        quantity = self.convert_to_float(quantity_str)
        if quantity is None:
            print(f"Warning: Unexpected quantity format: {quantity_str}")

        return quantity

    def convert_trade_date(self, trade_date_str, date_format="%m/%d/%Y"):
        """Convert trade date string to YYYY-MM-DD format."""
        # Handle cases where date might have multiple formats

        if " as of " in trade_date_str:
            # 'Bank Interest' and Options Expirations.
            # Get Second date for this type: '11/04/2024 as of 11/01/2024'
            trade_date_str = trade_date_str.split(" as of ")[1].strip()

        try:
            trade_datetime = datetime.strptime(trade_date_str, date_format)
            return trade_datetime.strftime("%Y-%m-%d")
        except ValueError:
            print(f"Warning: Invalid date format: {trade_date_str}")
            return None

    def convert_to_float(self, some_input):

        if isinstance(some_input, str):
            new_input = re.sub(r"[^\d\.]", "", some_input)
        else:
            new_input = some_input

        try:
            result = float(new_input)
        except ValueError:
            print(
                f"Warning: Unable to convert '{some_input}' to float. Please check the input format."
            )
            result = None
        return result

    def validate_price(self, price_str):
        """Validate price format (number or number with '$')."""
        if not price_str:
            return False

        price = self.convert_to_float(price_str)
        if price is None:
            print(f"Warning: Invalid price format: {price_str}")
            return False

        return price

    def extract_symbol_from_description(self, row):
        """Extracts the Symbol from the row["Description"].
        If row["Symbol"] is empty, it will try to extract it from the row["Description"].
        Example Description: "TDA TRAN - QUALIFIED DIVIDEND (FFIC)"
        Example Symbol: "FFIC"
        Returns: The row["Symbol"] if it exists, otherwise the extracted symbol from Description.
        If both are empty, it returns a default symbol.
        Example:
        "Date","Action","Symbol","Description","Quantity","Price","Fees","Amount":w
        "03/26/2021","Qual Div Reinvest","","TDA TRAN - QUALIFIED DIVIDEND (FFIC)","","","","$171.31"
        """
        if "Symbol" in row and row["Symbol"] != "":
            return row["Symbol"]

        if "Description" in row and row["Description"]:
            match = re.search(r"\((.*?)\)", row["Description"])
            if match:
                symbol = match.group(1).strip()
                print(
                    f"Extracted Symbol, {symbol} from Description {row['Description']}"
                )
                return symbol
            else:
                print(
                    f"Warning: No 'symbol' in Description, {row['Description']} use '{default_symbol}'"
                )
        else:
            print(
                f"Warning: Symbol and Description field are empty, use '{default_symbol}'"
            )

        return default_symbol

    def is_option_label_pattern(self, string):
        """Checks if the string matches the option label pattern."""
        return bool(re.search(option_label_pattern, string))

    def is_option_trade(self, row):
        """Checks if the row is an option trade."""
        if any(x in row["Action"] for x in ["Open", "Close"]):
            return True
        else:
            return False

    def determine_trade_type(self, row):
        """Determines the trade type based on the action.
        Possible trade types: 'L', 'S', 'C', 'P', 'O'
        Long, Short, Call, Put, Other.
        TODO: Add logic to determine if it's a Call or Put based on the symbol.
        TODO: Add logic to determine if it's a short sell.
        Return 'UK' (Unknown) if the action is not recognized.
        """

        if row["Action"] in ("Buy", "Sell"):
            return "L"
        elif "Trade Type" in row and row["Trade Type"] in ["C", "P"]:
            return row["Trade Type"]

        return self.action_mapping.get_acronym(row["Action"]) or "UK"

    def calculate_amount(self, row):
        """Calculates the amount based on quantity and price. For Buy Sell & Re-Invest Orders"""

        if not row["Action"].startswith(("Buy", "Sell", "Reinvest")):
            return None

        price = self.convert_to_float(row["Price"])
        if price is None:
            print(f"Warning: Invalid format for security: {row['Symbol']}")
            print(f"Price: {row['Price']},  Action: {row['Action']}")
            return 0

        quantity = self.convert_to_float(row["Quantity"])
        if quantity is None:
            print(f"Warning: Invalid Quantity for security: {row['Symbol']}")
            print(f"Price: {row['Quantity']},  Action: {row['Action']}")
            print(f"Quantity: {quantity}, Price: {str(price)}")
            return 0.0

        amount = 0
        try:
            if self.is_option_trade(row):
                # Convert an Option Open/Close to standard 100*price
                amount = round((quantity * price) * 100, 2)
            else:
                amount = round((quantity * price), 2)

            return -amount if row["Action"].startswith("Buy") else amount

        except ValueError:
            print("Warning: Invalid quantity or price format.")
            print(f"Quantity: {quantity}, Price: {str(price)}")
            return 0.0

    def extract_option_label(self, row):
        """Extracts the option label from the Symbol.
        When "Symbol" has text in the format of: "CORZ 09/20/2024 9.00 C",
        The method extracts the following into a dictionary:
        Symbol: CORZ
        Label: CORZ 09/20/2024 9.00 C
        Expiration Date: 09/20/2024
        Target Price: 9.00
        Trade Type: C
        Note: This can also be used to extract "Exchange or Exercise" label data.
        """
        # First check if the symbol contains "\s*\S+\s+\d{1,2}/\d{1,2}/\d{2,4}\s+\d+\.\d+\s+[CP]"
        match = re.search(option_label_pattern, row["Symbol"])

        if match:
            option_fields = {}
            label = match.group(0).strip()
            option_fields["Label"] = label
            option_fields["Symbol"] = label.split()[0]

            if self.is_option_trade(row):
                option_fields["Trade Type"] = label.split()[-1]
            else:
                # "Exchange or Exercise" trades also have an option label
                option_fields["Trade Type"] = "O"

            option_fields["Expiration Date"] = label.split()[1]
            option_fields["Target Price"] = self.convert_to_float(label.split()[2])
            return option_fields
        else:
            print(f"Info: Is not an Option trade: {row['Symbol']}")
            return None

    def calculate_stop(self, row):
        """Calculates the stop price for a buy order."""
        if not row["Action"].startswith("Buy"):
            return None

        price = self.convert_to_float(row["Price"])

        try:
            return round(price * 0.95)
        except ValueError:
            print("Warning(calculate_stop): Invalid price format: " + str(price))
            return 0.0

    def calculate_sell(self, row):
        """Calculates the sell price."""
        if not row["Action"].startswith("Buy"):
            return 0.0

        price = self.convert_to_float(row["Price"])

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
        """Sorts a CSV file by Symbol (ascending) and Trade Date (ascending),
        excluding the header row.
        """
        with open(file_path, "r") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames  # Store the header row
            data = list(reader)  # Read the rest of the data into a list

        # Sort the data (excluding the header)
        sorted_data = sorted(data, key=lambda row: (row["Symbol"], row["Trade Date"]))

        # Write the sorted data back to the file (including the header)
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for row in sorted_data:
                writer.writerow(row.values())

    def redo_output_file(self, output_file, line_count=0):
        """Remove the output file if it's empty. Sort it if it's full."""
        if line_count > 1:
            self.sort_output_file(output_file)
            print(f"Info: Created output file {output_file}")
        else:
            os.remove(output_file)
            print(f"Warning: Output file {output_file} was empty and has been deleted.")

    def get_input_files(self, keyword, file_extension=".csv"):
        """Get input files matching the keyword and extension."""
        if not os.path.exists(self.input_dir):
            print(f"Error: Input directory '{self.input_dir}' does not exist.")
            return []
        return [
            os.path.join(self.input_dir, f)
            for f in os.listdir(self.input_dir)
            if f.lower().endswith(file_extension) and keyword.lower() in f.lower()
        ]

    def determine_account_type(self, file_name):
        """Determine account type based on the file name."""
        if file_name.lower().startswith("c"):
            print(f"Info: Account: 'C', File name: '{file_name}'")
            return "C"
        elif file_name.lower().startswith("r"):
            print(f"Info: Account: 'R', File name: '{file_name}'")
            return "R"
        elif file_name.lower().startswith("d"):
            # Designated Individual Account File
            print(f"Info: Account: 'I', File name: '{file_name}'")
            return "I"

        print(
            f"Warning: Expected file name starting with 'C','R','D'. File: '{file_name}'"
        )
        return "X"

    def is_duplicate_row(self, row, seen_rows, account):
        """Check for duplicate rows."""
        row_tuple = tuple([row.values(), account])
        if row_tuple in seen_rows:
            return True
        seen_rows.add(row_tuple)
        return False

    def format_trade_transaction(self, trade_transaction):
        """Format the trade transaction for output."""
        return [
            trade_transaction["symbol"],
            trade_transaction["name"],
            trade_transaction["action"],
            trade_transaction["label"],
            trade_transaction["trade_type"],
            trade_transaction["quantity"],
            trade_transaction["price"],
            "",  # Fees
            trade_transaction["trade_date"],
            trade_transaction["expiration_date"],
            trade_transaction["amount"],
            trade_transaction["target_price"],
            trade_transaction["initial_stop_price"],
            trade_transaction["projected_sell_price"],
            "",  # P/L
            trade_transaction["account"],
        ]

    def process_files(
        self, input_files, output_filename, output_header, row_processor, **kwargs
    ):
        """Main file processing logic."""
        output_file = os.path.join(self.output_dir, output_filename)
        field_names = kwargs["field_names"] if "field_names" in kwargs else None
        db_inserter = kwargs["db_inserter"] if "db_inserter" in kwargs else None
        seen_rows = set()
        out_count = 0

        with open(output_file, "w", newline="") as out_csv:
            writer = csv.writer(out_csv)
            writer.writerow(output_header)

            for input_file in input_files:

                print(f"Info: Reading file path: {input_file}")
                file_name = os.path.basename(input_file)
                print(f"Info: File Name: '{file_name}'")
                account = self.determine_account_type(file_name)

                with open(input_file, "r") as in_csv:
                    reader = csv.DictReader(in_csv, fieldnames=field_names)
                    for row in reader:
                        if self.is_duplicate_row(row, seen_rows, account):
                            continue

                        # Custom row processing
                        trade_transaction = row_processor(
                            self, row, db_inserter=db_inserter, account=account
                        )
                        if trade_transaction:
                            writer.writerow(
                                self.format_trade_transaction(trade_transaction)
                            )
                            out_count += 1
                    # Move to processed
                    os.rename(
                        input_file,
                        os.path.join(self.processed_dir, os.path.basename(input_file)),
                    )

        # Ensure output file is handled properly
        self.redo_output_file(output_file, out_count)
