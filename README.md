# trade_tracker

## Track Trades Made on the Schwab Platform

- A web application that allows users to track their stock trades and view their portfolio performance.
- Uses Python, Flask, and SQLAlchemy.
- The front end uses Bootstrap, Jinja2 and jQuery

### Features

- **Track trades:** Add, update, and delete trades.
- **View portfolio summary:** See a high-level overview of your portfolio's performance, including total value, profit/loss, and top holdings.
- **View individual transaction details:** Get detailed information about each trade, including price, quantity, and profit/loss.

### How to Use

1. Clone the repository:

```bash
    git clone https://github.com/aibistin/trade_tracker.git
```

2.Install dependencies:

```bash
    pip install requirements.txt
```

3.Create an SQLite3 database in the ./data directory:

```bash
    python create_db.py
    echo ./util/create_stock_trades.sql | sqlite3 ./data/stock_trades.db
```

4.You can setup your environment with pyenv-virtualenv:
Modify the paths in ./python_setup.sh

 ```bash
 ./python_setup.sh
 ```

1. Run the application:

```bash
    python app.py
    # or Modify the PYTHONPATH in  run_flask.sh 
    ./run_flask.sh
```

2.Open a web browser and navigate to <http://localhost:5000> to use the application.

### Contributing

Contributions are welcome! Please submit a pull request if you have any improvements or new features to add.

### License

This application is licensed under the MIT License.

### Acknowledgements

### Additional Notes

- This application is still under development.
- Please report any bugs or issues you encounter.
- I would love to hear your feedback on how to improve this application!-

Thank you for using Trade Tracker!
