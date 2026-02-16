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
        os.remove(self.test_db_path)
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


    def test_convert_to_float(self):
        # Test cases for convert_to_float
        self.assertEqual(self.csv_processor.convert_to_float("  $500.10  "), 500.10)
        self.assertEqual(self.csv_processor.convert_to_float(500), 500.00)
        self.assertEqual(self.csv_processor.convert_to_float(" 5,00.10  "), 500.10)
        self.assertEqual(self.csv_processor.convert_to_float("1 5,00.10  "), 1500.10)

    def test_extract_quantity(self):
        # Test cases for extract_quantity
        self.assertEqual(self.csv_processor.extract_quantity(
            "50 Shares (All or None)"), 50)
        self.assertEqual(self.csv_processor.extract_quantity("100.093"), 100.093)
        # Add more test cases as needed

    def test_convert_trade_date(self):
        # Test cases for convert_trade_date
        self.assertEqual(self.csv_processor.convert_trade_date(
            "08/31/2024", "%m/%d/%Y"), "2024-08-31")
        # Add more test cases

    def test_validate_price(self):
        # Test cases for validate_price
        self.assertTrue(self.csv_processor.validate_price("100.50"))
        self.assertTrue(self.csv_processor.validate_price("$50"))
        self.assertFalse(self.csv_processor.validate_price("invalid"))
        # Add more test cases

    # def test_process_files(self):
        # Create a test CSV file in the input directory
        # ...

        # Call process_files with appropriate arguments
        # ...

        # Check if the output file exists and has the correct data
        # ...

        # Check if the data was inserted into the database correctly
        # ...

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


if __name__ == '__main__':
    unittest.main()
