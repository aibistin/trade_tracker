#!/bin/bash
# Script Name: process_schwab_data.sh
TODAY=`date +%Y%m%d`
#TODO Use Environment Variables
WORK_DIR="${HOME}/Apps/python/Trading/"
JAIL_DIR="${HOME}/Documents/Finance/Stocks/tradefiles"
INPUT_DIR="${HOME}/Apps/python/Trading/data/input"
LOG_DIR="${HOME}/Apps/python/Trading/logs"
LOG_FILE_RUNNER="${LOG_DIR}/run_file_processors_$TODAY.log"
LOG_FILE_TRANS="${LOG_DIR}/process_schwab_transactions_$TODAY.log"
LOG_FILE_ORDER="${LOG_DIR}/process_schwab_orders_$TODAY.log" 

# Move out all logs older than 12 hours
find "${LOG_DIR}" -maxdepth 1 -type f -name ".log" -mmin +720 -exec mv {} "${LOG_DIR}"/old \;

# WFH
pushd $WORK_DIR

function get_dtime(){
    echo "$(date +"%Y-%m-%d %H:%M:%S")"
}

echo "         ====== START 'run_process_schwab_data' - $(get_dtime) ======" >>  $LOG_FILE_RUNNER

echo "$(get_dtime):Checking for Transaction files to move from:" | tee -a $LOG_FILE_RUNNER
echo "$(get_dtime):$JAIL_DIR to $INPUT_DIR..." | tee -a $LOG_FILE_RUNNER
find "$JAIL_DIR" -type f -name "*Trans*.csv" -exec mv -t "$INPUT_DIR" {} + 2>> $LOG_FILE_RUNNER
if [ $? -ne 0 ]; then
    echo "$(get_dtime):Error: Failed to move Transaction files from $JAIL_DIR to $INPUT_DIR" | tee -a $LOG_FILE_RUNNER
fi

echo "$(get_dtime):Checking for Order files to move from:" | tee -a $LOG_FILE_RUNNER
echo "$(get_dtime):$JAIL_DIR to $INPUT_DIR..." | tee -a $LOG_FILE_RUNNER
find "$JAIL_DIR" -type f -name "*Order*.csv" -exec mv -t "$INPUT_DIR" {} + 2>> $LOG_FILE_RUNNER
if [ $? -ne 0 ]; then
    echo "$(get_dtime):Error: Failed to move Order files from $JAIL_DIR to $INPUT_DIR" | tee -a $LOG_FILE_RUNNER
fi

# Is there any transaction files in the $INPUT_DIR 
TCSV_FILES=$(find "$INPUT_DIR" -type f -name "*Trans*.csv" -newerct "$(date -r "$INPUT_DIR" '+%Y-%m-%dT%H:%M:%S')")

if [ -n "$TCSV_FILES" ]; then
    echo "$(get_dtime):Transaction files $TCSV_FILES" | tee -a $LOG_FILE_RUNNER
    echo "$(get_dtime):Running 'process_schwab_transactions'..." | tee -a $LOG_FILE_RUNNER
    echo "         ====== START - $(get_dtime) ======" >>  $LOG_FILE_TRANS
    LOG_LEVEL=INFO python3 -m bin.process_schwab_transactions >> $LOG_FILE_TRANS 2>&1
    if [ $? -ne 0 ]; then
        echo "$(get_dtime):Error: The 'process_schwab_transactions' failed! Exit code:$?" | tee -a $LOG_FILE_RUNNER
    fi
    echo "          END - $(get_dtime)" >>  $LOG_FILE_TRANS
    echo "             " >>  $LOG_FILE_TRANS
else
    echo "$(get_dtime):No Transaction files in $JAIL_DIR..." | tee -a $LOG_FILE_RUNNER
fi
        
# Is there any order files in the $INPUT_DIR 
OCSV_FILES=$(find "$INPUT_DIR" -type f -name "*Order*.csv" -newerct "$(date -r "$INPUT_DIR" '+%Y-%m-%dT%H:%M:%S')")
if [ -n "$OCSV_FILES" ]; then
    echo "$(get_dtime):Order files $OCSV_FILES" | tee -a $LOG_FILE_RUNNER

    echo "         ====== START - $(get_dtime) ======" >>  $LOG_FILE_ORDER
    python3 -m bin.process_schwab_orders >> $LOG_FILE_ORDER 2>&1
    echo "$(get_dtime):Running 'process_schwab_orders'..." | tee -a $LOG_FILE_RUNNER
    if [ $? -ne 0 ]; then
        echo "$(get_dtime))Error: The Python script 'process_schwab_orders' failed with exit code $?" | tee -a $LOG_FILE_RUNNER
    fi
    echo "          END" >>  $LOG_FILE_ORDER
    echo "             " >>  $LOG_FILE_ORDER
else
    echo "$(get_dtime):No Order files in $JAIL_DIR..." | tee -a $LOG_FILE_RUNNER
fi

# Return to where we came from.
popd 
echo "         ====== END 'run_process_schwab_data' - $(get_dtime) ======" >>  $LOG_FILE_RUNNER
