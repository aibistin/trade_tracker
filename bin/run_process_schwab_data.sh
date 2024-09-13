#!/bin/bash
# Script Name: process_schwab_data.sh
# Define directories
SOURCE_DIR="/home/austin/Documents/Finance/Stocks/tradefiles"
INPUT_DIR="/home/austin/Apps/python/Trading/data/input"
TODAY=`date +%Y%m%d`
LOG_FILE_TRANS="/home/austin/Apps/python/Trading/logs/process_schwab_transactions_$TODAY.log"
LOG_FILE_ORDER="/home/austin/Apps/python/Trading/logs/process_schwab_orders_$TODAY.log" 
DATE_TIME=`date +"%Y-%m-%d %H:%M:%S"`


# Move CSV files to input directory
echo "Moving CSV files to input directory..."
find "$SOURCE_DIR" -type f -name "*.csv" -exec mv -t "$INPUT_DIR" {} +
echo "Done moving files."

# Run Python scripts
echo "Running Python scripts..."
echo "         ====== START $DATE_TIME ======" >>  $LOG_FILE_TRANS
python3 -m bin.process_schwab_transactions >> $LOG_FILE_TRANS 2>&1
echo "          END" >>  $LOG_FILE_TRANS
echo "             " >>  $LOG_FILE_TRANS

echo "         ====== START $DATE_TIME ======" >>  $LOG_FILE_ORDER
python3 -m bin.process_schwab_orders >> $LOG_FILE_ORDER 2>&1
echo "          END" >>  $LOG_FILE_ORDER
echo "             " >>  $LOG_FILE_ORDER

# python3 -m bin.new_process_schwab_transactions >> logs/run_tests_log_$TODAY.log 2>&1
echo "Finished processing."
