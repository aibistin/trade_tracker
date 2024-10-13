import unittest
import os
from datetime import datetime

from lib.csv_processing_utils import CSVProcessor
from lib.db_utils import DatabaseInserter


class TestCSVProcessing(unittest.TestCase):

    def setUp(self):
        self.test_input_dir = "test_data/input"
        self.test_output_dir = "test_data/output"
        self.test_processed_dir = "test_data/processed"
        self.test_db_path = "test_stock_trades.db"

        # Create test directories if they don't exist
        os.makedirs(self.test_input_dir, exist_ok=True)
        os.makedirs(self.test_output_dir, exist_ok=True)
        os.makedirs(self.test_processed_dir, exist_ok=True)

        self.processor = CSVProcessor(
            self.test_input_dir, self.test_output_dir, self.test_processed_dir)
        self.db_inserter = DatabaseInserter(self.test_db_path)

    def tearDown(self):
        # Clean up test database and output files
        os.remove(self.test_db_path)
        for file in os.listdir(self.test_output_dir):
            os.remove(os.path.join(self.test_output_dir, file))

    def test_convert_to_float(self):
        # Test cases for convert_to_float
        self.assertEqual(CSVProcessor.convert_to_float("  $500.10  "), 500.10)
        self.assertEqual(CSVProcessor.convert_to_float(500), 500.00)
        self.assertEqual(CSVProcessor.convert_to_float(" 5,00.10  "), 500.10)
        self.assertEqual(CSVProcessor.convert_to_float("1 5,00.10  "), 1500.10)

    def test_extract_quantity(self):
        # Test cases for extract_quantity
        self.assertEqual(CSVProcessor.extract_quantity(
            "50 Shares (All or None)"), 50)
        self.assertEqual(CSVProcessor.extract_quantity("100.093"), 100.093)
        # Add more test cases as needed

    def test_convert_trade_date(self):
        # Test cases for convert_trade_date
        self.assertEqual(CSVProcessor.convert_trade_date(
            "08/31/2024", "%m/%d/%Y"), "2024-08-31")
        # Add more test cases

    def test_validate_price(self):
        # Test cases for validate_price
        self.assertTrue(CSVProcessor.validate_price("100.50"))
        self.assertTrue(CSVProcessor.validate_price("$50"))
        self.assertFalse(CSVProcessor.validate_price("invalid"))
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

    # Add more test methods as needed (e.g., for database insertion, sorting, etc.)


if __name__ == '__main__':
    unittest.main()
