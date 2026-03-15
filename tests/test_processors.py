import csv
import unittest
import os
from datetime import datetime

from lib.csv_processing_utils import CSVProcessor
from lib.db_utils import DatabaseInserter
#TODO This needs to test the DatabaseInserter class

class TestCSVProcessing(unittest.TestCase):

    def setUp(self):
        self.test_dir = "test_data"
        self.test_input_dir = "test_data/input"
        self.test_output_dir = "test_data/output"
        self.test_processed_dir = "test_data/processed"
        self.test_db_path = "test_data/test_stock_trades.db"
        self.test_db_path_two = "test_data/test_trades.db"

        # Create test directories if they don't exist
        os.makedirs(self.test_input_dir, exist_ok=True)
        os.makedirs(self.test_output_dir, exist_ok=True)
        os.makedirs(self.test_processed_dir, exist_ok=True)

        self.csv_processor = CSVProcessor(
            self.test_input_dir, self.test_output_dir, self.test_processed_dir)

        self.db_inserter = DatabaseInserter(self.test_db_path)
        with DatabaseInserter(db_path=self.test_db_path_two) as db:
            transaction = {
                #TODO Create a sample trade_transaction for testing
            }
            # if not db.transaction_exists(transaction):
                # db.insert_transaction(transaction)



    def tearDown(self):
        # Clean up test database and output files
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        if os.path.exists(self.test_db_path_two):
            os.remove(self.test_db_path_two)
        for file in os.listdir(self.test_output_dir):
            os.remove(os.path.join(self.test_output_dir, file))
        for file in os.listdir(self.test_input_dir):
            os.remove(os.path.join(self.test_input_dir, file))
        for file in os.listdir(self.test_processed_dir):
            os.remove(os.path.join(self.test_processed_dir, file))
        # Remove test directories
        os.rmdir(self.test_input_dir)
        os.rmdir(self.test_output_dir)
        os.rmdir(self.test_processed_dir)
        # Remove test directory
        os.rmdir(self.test_dir)

    # --- Already-covered methods ---

    def test_convert_to_float(self):
        self.assertEqual(self.csv_processor.convert_to_float("  $500.10  "), 500.10)
        self.assertEqual(self.csv_processor.convert_to_float(500), 500.00)
        self.assertEqual(self.csv_processor.convert_to_float(" 5,00.10  "), 500.10)
        self.assertEqual(self.csv_processor.convert_to_float("1 5,00.10  "), 1500.10)

    def test_extract_quantity(self):
        self.assertEqual(self.csv_processor.extract_quantity(
            "50 Shares (All or None)"), 50)
        self.assertEqual(self.csv_processor.extract_quantity("100.093"), 100.093)

    def test_convert_trade_date(self):
        self.assertEqual(self.csv_processor.convert_trade_date(
            "08/31/2024", "%m/%d/%Y"), "2024-08-31")

    def test_validate_price(self):
        self.assertTrue(self.csv_processor.validate_price("100.50"))
        self.assertTrue(self.csv_processor.validate_price("$50"))
        self.assertFalse(self.csv_processor.validate_price("invalid"))

    def test_is_option_trade_expired(self):
        """Expired options should be recognized as option trades."""
        row = {"Action": "Expired", "Symbol": "MSTX 12/19/2025 45.00 C"}
        self.assertTrue(self.csv_processor.is_option_trade(row))

    def test_is_option_trade_open_close(self):
        """Buy/Sell to Open/Close should be recognized as option trades."""
        self.assertTrue(self.csv_processor.is_option_trade(
            {"Action": "Buy to Open", "Symbol": "MSTX"}))
        self.assertTrue(self.csv_processor.is_option_trade(
            {"Action": "Sell to Close", "Symbol": "MSTX"}))

    def test_is_option_trade_regular(self):
        """Regular Buy/Sell should not be option trades."""
        self.assertFalse(self.csv_processor.is_option_trade(
            {"Action": "Buy", "Symbol": "MSTX"}))
        self.assertFalse(self.csv_processor.is_option_trade(
            {"Action": "Sell", "Symbol": "MSTX"}))

    def test_calculate_amount_expired(self):
        """Expired options should have amount of 0."""
        row = {"Action": "Expired", "Symbol": "MSTX", "Price": "", "Quantity": "-1"}
        self.assertEqual(self.csv_processor.calculate_amount(row), 0)

    def test_extract_option_label_expired(self):
        """Expired options should extract C/P trade type from label."""
        row = {"Action": "Expired", "Symbol": "MSTX 12/19/2025 45.00 C"}
        result = self.csv_processor.extract_option_label(row)
        self.assertIsNotNone(result)
        self.assertEqual(result["Symbol"], "MSTX")
        self.assertEqual(result["Trade Type"], "C")
        self.assertEqual(result["Target Price"], 45.0)
        self.assertEqual(result["Expiration Date"], "12/19/2025")

    def test_extract_option_label_expired_put(self):
        """Expired put options should extract P trade type."""
        row = {"Action": "Expired", "Symbol": "TSLA 01/17/2025 200.00 P"}
        result = self.csv_processor.extract_option_label(row)
        self.assertIsNotNone(result)
        self.assertEqual(result["Symbol"], "TSLA")
        self.assertEqual(result["Trade Type"], "P")

    def test_determine_trade_type_expired_call(self):
        """Expired call should preserve C trade type from option label."""
        row = {"Action": "Expired", "Trade Type": "C"}
        self.assertEqual(self.csv_processor.determine_trade_type(row), "C")

    def test_determine_trade_type_expired_put(self):
        """Expired put should preserve P trade type from option label."""
        row = {"Action": "Expired", "Trade Type": "P"}
        self.assertEqual(self.csv_processor.determine_trade_type(row), "P")

    def test_convert_trade_date_as_of(self):
        """'as of' date format should use the second date."""
        result = self.csv_processor.convert_trade_date(
            "12/22/2025 as of 12/19/2025", "%m/%d/%Y")
        self.assertEqual(result, "2025-12-19")

    # --- extract_symbol_from_description ---

    def test_extract_symbol_from_row(self):
        """Symbol from row['Symbol'] takes priority."""
        row = {"Symbol": "AAPL", "Description": "Something else"}
        self.assertEqual(self.csv_processor.extract_symbol_from_description(row), "AAPL")

    def test_extract_symbol_from_description(self):
        """Symbol extracted from parentheses in Description when Symbol is empty."""
        row = {"Symbol": "", "Description": "TDA TRAN - QUALIFIED DIVIDEND (FFIC)"}
        self.assertEqual(self.csv_processor.extract_symbol_from_description(row), "FFIC")

    def test_extract_symbol_no_match_in_description(self):
        """Returns default symbol when Description has no parenthesised symbol."""
        row = {"Symbol": "", "Description": "TDA TRAN - NO PARENTHESES"}
        self.assertEqual(self.csv_processor.extract_symbol_from_description(row), "NONE")

    def test_extract_symbol_empty_description(self):
        """Returns default symbol when both Symbol and Description are empty."""
        row = {"Symbol": "", "Description": ""}
        self.assertEqual(self.csv_processor.extract_symbol_from_description(row), "NONE")

    # --- is_option_label_pattern ---

    def test_is_option_label_pattern_call(self):
        self.assertTrue(self.csv_processor.is_option_label_pattern("MSTX 12/19/2025 45.00 C"))

    def test_is_option_label_pattern_put(self):
        self.assertTrue(self.csv_processor.is_option_label_pattern("TSLA 1/17/2025 200.00 P"))

    def test_is_option_label_pattern_plain_symbol(self):
        self.assertFalse(self.csv_processor.is_option_label_pattern("AAPL"))

    # --- calculate_amount ---

    def test_calculate_amount_stock_buy(self):
        """Stock buy amount is negative (cash out)."""
        row = {"Action": "Buy", "Symbol": "AAPL", "Price": "150.00", "Quantity": "10"}
        self.assertEqual(self.csv_processor.calculate_amount(row), -1500.00)

    def test_calculate_amount_stock_sell(self):
        """Stock sell amount is positive (cash in)."""
        row = {"Action": "Sell", "Symbol": "AAPL", "Price": "160.00", "Quantity": "10"}
        self.assertEqual(self.csv_processor.calculate_amount(row), 1600.00)

    def test_calculate_amount_option_buy_to_open(self):
        """Option buy multiplies by 100."""
        row = {"Action": "Buy to Open", "Symbol": "MSTX", "Price": "2.50", "Quantity": "5"}
        self.assertEqual(self.csv_processor.calculate_amount(row), -1250.00)

    def test_calculate_amount_option_sell_to_close(self):
        """Option sell multiplies by 100."""
        row = {"Action": "Sell to Close", "Symbol": "MSTX", "Price": "3.00", "Quantity": "5"}
        self.assertEqual(self.csv_processor.calculate_amount(row), 1500.00)

    def test_calculate_amount_non_trade_action(self):
        """Non-buy/sell actions (e.g. Bank Interest) return None."""
        row = {"Action": "Bank Interest", "Symbol": "NONE", "Price": "0", "Quantity": "0"}
        self.assertIsNone(self.csv_processor.calculate_amount(row))

    def test_calculate_amount_invalid_price(self):
        """Invalid price returns 0."""
        row = {"Action": "Buy", "Symbol": "AAPL", "Price": "N/A", "Quantity": "10"}
        self.assertEqual(self.csv_processor.calculate_amount(row), 0)

    # --- calculate_stop / calculate_sell ---

    def test_calculate_stop_buy(self):
        """Stop price is 5% below buy price."""
        row = {"Action": "Buy", "Price": "100.00"}
        self.assertAlmostEqual(self.csv_processor.calculate_stop(row), 95.00)

    def test_calculate_stop_non_buy(self):
        """Non-buy rows return None for stop price."""
        self.assertIsNone(self.csv_processor.calculate_stop({"Action": "Sell", "Price": "100.00"}))

    def test_calculate_sell_buy(self):
        """Projected sell price is 15% above buy price."""
        row = {"Action": "Buy", "Price": "100.00"}
        self.assertAlmostEqual(self.csv_processor.calculate_sell(row), 115.00)

    def test_calculate_sell_non_buy(self):
        """Non-buy rows return 0.0 for projected sell price."""
        self.assertEqual(self.csv_processor.calculate_sell({"Action": "Sell", "Price": "100.00"}), 0.0)

    # --- determine_trade_type ---

    def test_determine_trade_type_buy(self):
        self.assertEqual(self.csv_processor.determine_trade_type({"Action": "Buy"}), "L")

    def test_determine_trade_type_sell(self):
        self.assertEqual(self.csv_processor.determine_trade_type({"Action": "Sell"}), "L")

    def test_determine_trade_type_option_call(self):
        """Buy to Open with Trade Type C returns C."""
        row = {"Action": "Buy to Open", "Trade Type": "C"}
        self.assertEqual(self.csv_processor.determine_trade_type(row), "C")

    def test_determine_trade_type_option_put(self):
        """Sell to Close with Trade Type P returns P."""
        row = {"Action": "Sell to Close", "Trade Type": "P"}
        self.assertEqual(self.csv_processor.determine_trade_type(row), "P")

    def test_determine_trade_type_unknown(self):
        """Unrecognized action with no Trade Type returns UK."""
        row = {"Action": "Unrecognized Action"}
        self.assertEqual(self.csv_processor.determine_trade_type(row), "UK")

    # --- determine_account_type ---

    def test_determine_account_type_c(self):
        self.assertEqual(self.csv_processor.determine_account_type("C_schwab.csv"), "C")

    def test_determine_account_type_r(self):
        self.assertEqual(self.csv_processor.determine_account_type("r_schwab.csv"), "R")

    def test_determine_account_type_d(self):
        """Files starting with D map to Individual account 'I'."""
        self.assertEqual(self.csv_processor.determine_account_type("D_schwab.csv"), "I")

    def test_determine_account_type_unknown(self):
        self.assertEqual(self.csv_processor.determine_account_type("schwab.csv"), "X")

    # --- is_duplicate_row ---

    def test_is_duplicate_row_first_occurrence(self):
        seen = set()
        row = {"Action": "Buy", "Symbol": "AAPL", "Price": "150.00"}
        self.assertFalse(self.csv_processor.is_duplicate_row(row, seen, "C"))

    def test_is_duplicate_row_second_occurrence(self):
        seen = set()
        row = {"Action": "Buy", "Symbol": "AAPL", "Price": "150.00"}
        self.csv_processor.is_duplicate_row(row, seen, "C")
        self.assertTrue(self.csv_processor.is_duplicate_row(row, seen, "C"))

    def test_is_duplicate_row_different_account_not_duplicate(self):
        """Same row data but different account should not be a duplicate."""
        seen = set()
        row = {"Action": "Buy", "Symbol": "AAPL", "Price": "150.00"}
        self.csv_processor.is_duplicate_row(row, seen, "C")
        self.assertFalse(self.csv_processor.is_duplicate_row(row, seen, "R"))

    # --- format_trade_transaction ---

    def test_format_trade_transaction(self):
        tt = {
            "symbol": "AAPL", "name": "Apple Inc.", "action": "B",
            "label": "", "trade_type": "L", "quantity": 10, "price": 150.0,
            "trade_date": "2024-01-15", "expiration_date": None,
            "amount": -1500.0, "target_price": 172.5,
            "initial_stop_price": 142.5, "projected_sell_price": 172.5,
            "account": "C",
        }
        result = self.csv_processor.format_trade_transaction(tt)
        self.assertEqual(result[0], "AAPL")
        self.assertEqual(result[1], "Apple Inc.")
        self.assertEqual(result[2], "B")
        self.assertEqual(result[3], "")       # label
        self.assertEqual(result[4], "L")      # trade_type
        self.assertEqual(result[5], 10)       # quantity
        self.assertEqual(result[6], 150.0)    # price
        self.assertEqual(result[7], "")       # fees placeholder
        self.assertEqual(result[8], "2024-01-15")
        self.assertEqual(result[9], None)     # expiration_date
        self.assertEqual(result[10], -1500.0) # amount
        self.assertEqual(result[14], "")      # P/L placeholder
        self.assertEqual(result[15], "C")     # account

    # --- File I/O: output_file_has_data ---

    def _write_csv(self, filename, rows):
        path = os.path.join(self.test_output_dir, filename)
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            for row in rows:
                writer.writerow(row)
        return path

    def test_output_file_has_data_header_only(self):
        path = self._write_csv("header_only.csv", [["Symbol", "Action", "Price"]])
        self.assertFalse(self.csv_processor.output_file_has_data(path))

    def test_output_file_has_data_with_rows(self):
        path = self._write_csv("with_data.csv", [
            ["Symbol", "Action", "Price"],
            ["AAPL", "Buy", "150.00"],
        ])
        self.assertTrue(self.csv_processor.output_file_has_data(path))

    # --- File I/O: sort_output_file ---

    def test_sort_output_file(self):
        path = self._write_csv("unsorted.csv", [
            ["Symbol", "Trade Date", "Action"],
            ["TSLA", "2024-03-01", "Buy"],
            ["AAPL", "2024-01-15", "Sell"],
            ["AAPL", "2024-01-10", "Buy"],
        ])
        self.csv_processor.sort_output_file(path)
        with open(path, "r") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual([r["Symbol"] for r in rows], ["AAPL", "AAPL", "TSLA"])
        self.assertEqual(rows[0]["Trade Date"], "2024-01-10")
        self.assertEqual(rows[1]["Trade Date"], "2024-01-15")

    # --- File I/O: redo_output_file ---

    def test_redo_output_file_with_data_keeps_file(self):
        path = self._write_csv("keep.csv", [
            ["Symbol", "Trade Date", "Action"],
            ["AAPL", "2024-01-10", "Buy"],
        ])
        self.csv_processor.redo_output_file(path, line_count=2)
        self.assertTrue(os.path.exists(path))

    def test_redo_output_file_empty_removes_file(self):
        path = self._write_csv("empty.csv", [["Symbol", "Trade Date", "Action"]])
        self.csv_processor.redo_output_file(path, line_count=0)
        self.assertFalse(os.path.exists(path))

    # --- File I/O: get_input_files ---

    def _write_input_file(self, filename):
        path = os.path.join(self.test_input_dir, filename)
        open(path, "w").close()
        return path

    def test_get_input_files_returns_matching(self):
        self._write_input_file("C_schwab.csv")
        self._write_input_file("R_schwab.csv")
        files = self.csv_processor.get_input_files("schwab")
        self.assertEqual(len(files), 2)

    def test_get_input_files_filters_by_keyword(self):
        self._write_input_file("C_schwab.csv")
        self._write_input_file("C_other.csv")
        files = self.csv_processor.get_input_files("schwab")
        self.assertEqual(len(files), 1)
        self.assertIn("C_schwab.csv", files[0])

    def test_get_input_files_excludes_non_csv(self):
        self._write_input_file("C_schwab.csv")
        self._write_input_file("C_schwab.txt")
        files = self.csv_processor.get_input_files("schwab")
        self.assertEqual(len(files), 1)

    def test_get_input_files_nonexistent_dir(self):
        processor = CSVProcessor("/nonexistent/dir", self.test_output_dir, self.test_processed_dir)
        self.assertEqual(processor.get_input_files("schwab"), [])

    # --- process_files end-to-end ---

    OUTPUT_HEADER = [
        "Symbol", "Name", "Action", "Label", "Trade Type",
        "Quantity", "Price", "Fees", "Trade Date", "Expiration Date",
        "Amount", "Target Price", "Initial Stop Price", "Projected Sell Price",
        "P/L", "Account",
    ]

    @staticmethod
    def _stub_row_processor(csv_proc, row, db_inserter=None, account="C"):
        """Minimal row processor: returns a trade transaction dict for Buy/Sell rows."""
        if row["Action"] not in ("Buy", "Sell"):
            return None
        price = csv_proc.convert_to_float(row["Price"])
        qty = csv_proc.convert_to_float(row["Quantity"])
        return {
            "symbol": row["Symbol"],
            "name": row.get("Name", ""),
            "action": "B" if row["Action"] == "Buy" else "S",
            "label": "",
            "trade_type": "L",
            "quantity": qty,
            "price": price,
            "trade_date": row["Trade Date"],
            "expiration_date": None,
            "amount": -(qty * price) if row["Action"] == "Buy" else (qty * price),
            "target_price": None,
            "initial_stop_price": None,
            "projected_sell_price": None,
            "account": account,
        }

    def _write_input_csv(self, filename, header, rows):
        path = os.path.join(self.test_input_dir, filename)
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            for row in rows:
                writer.writerow(row)
        return path

    def test_process_files_creates_output(self):
        """process_files writes matching rows to the output CSV."""
        self._write_input_csv("C_test.csv",
            ["Action", "Symbol", "Name", "Quantity", "Price", "Trade Date"],
            [
                ["Buy", "AAPL", "Apple", "10", "150.00", "2024-01-15"],
                ["Buy", "TSLA", "Tesla", "5", "200.00", "2024-01-16"],
            ],
        )
        input_files = self.csv_processor.get_input_files("C_test")
        self.csv_processor.process_files(
            input_files, "output.csv", self.OUTPUT_HEADER, self._stub_row_processor
        )
        output_path = os.path.join(self.test_output_dir, "output.csv")
        self.assertTrue(os.path.exists(output_path))
        with open(output_path, "r") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["Symbol"], "AAPL")

    def test_process_files_moves_input_to_processed(self):
        """process_files moves the input file to processed_dir after processing."""
        self._write_input_csv("C_move.csv",
            ["Action", "Symbol", "Name", "Quantity", "Price", "Trade Date"],
            [["Buy", "TSLA", "Tesla", "5", "200.00", "2024-02-01"]],
        )
        input_files = self.csv_processor.get_input_files("C_move")
        self.csv_processor.process_files(
            input_files, "output2.csv", self.OUTPUT_HEADER, self._stub_row_processor
        )
        self.assertFalse(os.path.exists(os.path.join(self.test_input_dir, "C_move.csv")))
        self.assertTrue(os.path.exists(os.path.join(self.test_processed_dir, "C_move.csv")))

    def test_process_files_skips_duplicates(self):
        """Duplicate rows in the input file are written only once."""
        self._write_input_csv("C_dupe.csv",
            ["Action", "Symbol", "Name", "Quantity", "Price", "Trade Date"],
            [
                ["Buy", "AAPL", "Apple", "10", "150.00", "2024-01-15"],
                ["Buy", "AAPL", "Apple", "10", "150.00", "2024-01-15"],  # duplicate
                ["Buy", "TSLA", "Tesla", "5", "200.00", "2024-01-16"],
            ],
        )
        input_files = self.csv_processor.get_input_files("C_dupe")
        self.csv_processor.process_files(
            input_files, "output3.csv", self.OUTPUT_HEADER, self._stub_row_processor
        )
        output_path = os.path.join(self.test_output_dir, "output3.csv")
        with open(output_path, "r") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 2)  # duplicate dropped, 2 unique rows remain

    def test_process_files_empty_output_deleted(self):
        """If no rows match, the output file is deleted."""
        self._write_input_csv("C_empty.csv",
            ["Action", "Symbol", "Name", "Quantity", "Price", "Trade Date"],
            [["Bank Interest", "NONE", "", "0", "0", "2024-01-15"]],
        )
        input_files = self.csv_processor.get_input_files("C_empty")
        self.csv_processor.process_files(
            input_files, "output4.csv", self.OUTPUT_HEADER, self._stub_row_processor
        )
        self.assertFalse(os.path.exists(os.path.join(self.test_output_dir, "output4.csv")))


if __name__ == '__main__':
    unittest.main()
