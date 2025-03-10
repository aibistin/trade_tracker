import unittest
from lib.trading_analyzer import TradingAnalyzer

""""
    Test TradingAnalyzer
    - Test the TradingAnalyzer class with various stock transactions.
    - Verify the accuracy of profit/loss calculations.

To run all tests in the test directory:
python -m unittest discover -v
To run this test file:
python -m unittest tests.test_trading_analyzer

"""


class TestTradingAnalyzer(unittest.TestCase):
    def setUp(self):
        self.data_list = [
            {
                "SN": [
                    {
                        "Id": "0001",
                        "Symbol": "SN",
                        "Action": "B",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 100.0,
                        "Price": 91.39,
                        "Target Price": 0.0,
                        "Trade Date": "2024-08-22",
                        "Amount": -9139.0,
                        "Account": "C",
                    },
                    {
                        "Id": "0002",
                        "Symbol": "SN",
                        "Action": "S",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 100.0,
                        "Price": 88.9427,
                        "Target Price": 0.0,
                        "Trade Date": "2024-08-23",
                        "Amount": 8894.27,
                        "Account": "C",
                    },
                    # Sold 100
                    {
                        "Id": "0003",
                        "Symbol": "SN",
                        "Action": "B",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 50.0,
                        "Price": 89.4964,
                        "Target Price": 0.0,
                        "Trade Date": "2024-08-26",
                        "Amount": -4474.82,
                        "Account": "C",
                    },
                    # Sold 50
                    {
                        "Id": "0004",
                        "Symbol": "SN",
                        "Action": "B",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 50.0,
                        "Price": 91.7,
                        "Target Price": 0.0,
                        "Trade Date": "2024-08-27",
                        "Amount": -4585.0,
                        "Account": "C",
                    },
                    # Sold 50
                    {
                        "Id": "0005",
                        "Symbol": "SN",
                        "Action": "S",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 100.0,
                        "Price": 94.92,
                        "Target Price": 0.0,
                        "Trade Date": "2024-09-06",
                        "Amount": 9492.0,
                        "Account": "C",
                    },
                    # Sold for previous two trades
                    {
                        "Id": "0006",
                        "Symbol": "SN",
                        "Action": "B",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 50.0,
                        "Price": 94.85,
                        "Target Price": 0.0,
                        "Trade Date": "2024-08-30",
                        "Amount": -4742.5,
                        "Account": "C",
                    },
                    {
                        "Id": "0007",
                        "Symbol": "SN",
                        "Action": "S",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 25.0,
                        "Price": 94.94,
                        "Target Price": 0.0,
                        "Trade Date": "2024-09-06",
                        "Amount": 2373.5,
                        "Account": "C",
                    },
                    {
                        "Id": "0008",
                        "Symbol": "SN",
                        "Action": "S",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 10.0,
                        "Price": 96.99,
                        "Target Price": 0.0,
                        "Trade Date": "2024-09-07",
                        "Amount": 969.9,
                        "Account": "C",
                    },
                    {
                        "Id": "0009",
                        "Symbol": "SN",
                        "Action": "B",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 25.0,
                        "Price": 98.99,
                        "Target Price": 0.0,
                        "Trade Date": "2024-09-10",
                        "Amount": -2474.75,
                        "Account": "C",
                    },
                ]
            },
            {
                "NVDA": [
                    {
                        "Id": "0011",
                        "Symbol": "NVDA",
                        "Action": "B",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 200.0,
                        "Price": 300.0,
                        "Target Price": 0.0,
                        "Trade Date": "2024-08-22",
                        "Amount": -60000.0,
                    },
                    {
                        "Id": "0012",
                        "Symbol": "NVDA",
                        "Action": "S",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 150.0,
                        "Price": 310.0,
                        "Target Price": 0.0,
                        "Trade Date": "2024-09-01",
                        "Amount": 46500.0,
                    },
                    {
                        "Id": "0013",
                        "Symbol": "NVDA",
                        "Action": "S",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 50.0,
                        "Price": 315.0,
                        "Target Price": 0.0,
                        "Trade Date": "2024-09-02",
                        "Amount": 15750.0,
                    },
                ]
            },
            {
                "TNA": [
                    {
                        "Id": "0111",
                        "Symbol": "TNA",
                        "Action": "B",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 150.0,
                        "Price": 50.25,
                        "Target Price": 0.0,
                        "Trade Date": "2024-07-31",
                        "Amount": -7537.5,
                    },
                    {
                        "Id": "0112",
                        "Symbol": "TNA",
                        "Action": "S",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 100.0,
                        "Price": 47.2,
                        "Target Price": 0.0,
                        "Trade Date": "2024-08-01",
                        "Amount": 4720.0,
                    },
                    {
                        "Id": "0113",
                        "Symbol": "TNA",
                        "Action": "S",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 50.0,
                        "Price": 43.2601,
                        "Target Price": 0.0,
                        "Trade Date": "2024-08-27",
                        "Amount": 2163.01,
                    },
                ]
            },
            {
                "NAIL": [
                    {
                        "Id": "0222",
                        "Symbol": "NAIL",
                        "Action": "B",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 40.0,
                        "Price": 130.4599,
                        "Target Price": 0.0,
                        "Trade Date": "2024-07-25",
                        "Amount": -5218.4,
                    },
                    {
                        "Id": "0223",
                        "Symbol": "NAIL",
                        "Action": "B",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 40.0,
                        "Price": 145.0,
                        "Target Price": 0.0,
                        "Trade Date": "2024-07-26",
                        "Amount": -5800.0,
                    },
                    {
                        "Id": "0224",
                        "Symbol": "NAIL",
                        "Action": "B",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 50.0,
                        "Price": 127.1,
                        "Target Price": 0.0,
                        "Trade Date": "2024-08-05",
                        "Amount": -6355.0,
                    },
                    {
                        "Id": "0225",
                        "Symbol": "NAIL",
                        "Action": "S",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 50.0,
                        "Price": 145.4,
                        "Target Price": 0.0,
                        "Trade Date": "2024-08-27",
                        "Amount": 7270.0,
                    },
                    {
                        "Id": "0226",
                        "Symbol": "NAIL",
                        "Action": "S",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 80.0,
                        "Price": 147.5,
                        "Target Price": 0.0,
                        "Trade Date": "2024-08-27",
                        "Amount": 11800.0,
                    },
                    {
                        "Id": "0227",
                        "Symbol": "NAIL",
                        "Action": "B",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 50.0,
                        "Price": 145.7,
                        "Target Price": 0.0,
                        "Trade Date": "2024-08-30",
                        "Amount": -7285.0,
                    },
                    {
                        "Id": "0228",
                        "Symbol": "NAIL",
                        "Action": "S",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 50.0,
                        "Price": 140.6,
                        "Target Price": 0.0,
                        "Trade Date": "2024-09-03",
                        "Amount": 7030.0,
                    },
                    {
                        "Id": "0229",
                        "Symbol": "NAIL",
                        "Action": "B",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 50.0,
                        "Price": 140.87,
                        "Target Price": 0.0,
                        "Trade Date": "2024-09-12",
                        "Amount": -7043.5,
                    },
                    {
                        "Id": "0231",
                        "Symbol": "NAIL",
                        "Action": "S",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 50.0,
                        "Price": 156.38,
                        "Target Price": 0.0,
                        "Trade Date": "2024-09-13",
                        "Amount": 7819.0,
                    },
                    {
                        "Id": "0232",
                        "Symbol": "NAIL",
                        "Action": "B",
                        "Trade Type": "L",
                        "Label": "",
                        "Quantity": 40.0,
                        "Price": 159.6201,
                        "Target Price": 0.0,
                        "Trade Date": "2024-09-16",
                        "Amount": -6384.8,
                    },
                ]
            },
            {
                "NIO": [
                    {
                        "Id": "500",
                        "Symbol": "NIO",
                        "Action": "B",
                        "Trade Type": "L",
                        "Trade Date": "2024-09-24",
                        "Label": "",
                        "Quantity": 1000.0,
                        "Price": 5.865,
                        "Target Price": 0.0,
                        "Amount": -5865.0,
                        "Account": "R",
                    },
                    {
                        "Id": "504",
                        "Symbol": "NIO",
                        "Action": "B",
                        "Trade Type": "L",
                        "Trade Date": "2024-09-26",
                        "Label": "",
                        "Quantity": 200.0,
                        "Price": 5.8199,
                        "Target Price": 0.0,
                        "Amount": -1163.98,
                        "Account": "R",
                    },
                    {
                        "Id": "507",
                        "Symbol": "NIO",
                        "Action": "B",
                        "Trade Type": "L",
                        "Trade Date": "2024-09-25",
                        "Label": "",
                        "Quantity": 800.0,
                        "Price": 5.73,
                        "Target Price": 0.0,
                        "Amount": -4584.0,
                        "Account": "R",
                    },
                    {
                        "Id": "509",
                        "Symbol": "NIO",
                        "Action": "S",
                        "Trade Type": "L",
                        "Trade Date": "2024-09-25",
                        "Label": "",
                        "Quantity": 1000.0,
                        "Price": 5.5905,
                        "Target Price": 0.0,
                        "Amount": 5590.5,
                        "Account": "R",
                    },
                    {
                        "Id": "518",
                        "Symbol": "NIO",
                        "Action": "S",
                        "Trade Type": "L",
                        "Trade Date": "2024-09-30",
                        "Label": "",
                        "Quantity": 400.0,
                        "Price": 7.38,
                        "Target Price": 0.0,
                        "Amount": 2952.0,
                        "Account": "R",
                    },
                    {
                        "Id": "530",
                        "Symbol": "NIO",
                        "Action": "B",
                        "Trade Type": "L",
                        "Trade Date": "2024-10-03",
                        "Label": "",
                        "Quantity": 100.0,
                        "Price": 6.759,
                        "Target Price": 0.0,
                        "Amount": -675.9,
                        "Account": "R",
                    },
                    {
                        "Id": "536",
                        "Symbol": "NIO",
                        "Action": "B",
                        "Trade Type": "L",
                        "Trade Date": "2024-10-04",
                        "Label": "",
                        "Quantity": 100.0,
                        "Price": 6.5399,
                        "Target Price": 0.0,
                        "Amount": -653.99,
                        "Account": "C",
                    },
                ]
            },
        ]

        self.expect_trades = {
            "SN": [
                {
                    "trade_date": "2024-08-22",
                    "trade_date_iso": "2024-08-22T00:00:00",
                    "quantity": 100,
                    "price": 91.39,
                    "amount": -9139.0,
                    "current_sold_qty": 100,
                    "sells": [
                        {
                            "trade_date": "2024-08-23",
                            "trade_date_iso": "2024-08-23T00:00:00",
                            "quantity": 100,
                            "price": 88.9427,
                            "amount": 8894.27,
                            "profit_loss": -244.73,
                            "percent_profit_loss": -(244.73 / 9139) * 100,
                        }
                    ],
                },
                {
                    "trade_date": "2024-08-26",
                    "trade_date_iso": "2024-08-26T00:00:00",
                    "quantity": 50,
                    "price": 89.4964,
                    "amount": -4474.82,
                    "current_sold_qty": 50,
                    # Half of one sell
                    "sells": [
                        {
                            "trade_date": "2024-09-06",
                            "trade_date_iso": "2024-09-06T00:00:00",
                            "quantity": 50,
                            "price": 94.92,
                            "amount": 9492.00 / 2,
                            "profit_loss": (9492.00 / 2) - 4474.82,
                            "percent_profit_loss": ((94.92 - 89.4964) / 89.4964) * 100,
                        }
                    ],
                },
                {
                    "trade_date": "2024-08-27",
                    "trade_date_iso": "2024-08-27T00:00:00",
                    "quantity": 50,
                    "price": 91.70,
                    "amount": -4585.00,
                    "current_sold_qty": 50,
                    # Half of one sell
                    "sells": [
                        {
                            "trade_date": "2024-09-06",
                            "trade_date_iso": "2024-09-06T00:00:00",
                            "quantity": 50,
                            "price": 94.92,
                            "amount": 9492.27 / 2,
                            "profit_loss": round((9492.27 / 2)) - 4585.00,
                            "percent_profit_loss": ((94.92 - 91.70) / 91.70) * 100,
                        }
                    ],
                },
                {
                    "trade_date": "2024-08-30",
                    "trade_date_iso": "2024-08-30T00:00:00",
                    "quantity": 50,
                    "price": 94.85,
                    "amount": -4742.50,
                    "current_sold_qty": 35,
                    "sells": [
                        {
                            "trade_date": "2024-09-06",
                            "trade_date_iso": "2024-09-06T00:00:00",
                            "quantity": 25,
                            "price": 94.94,
                            "amount": 2373.5,
                            "profit_loss": 2373.5 - (4742.5 / 2),
                            "percent_profit_loss": ((94.94 - 94.85) / 94.85) * 100,
                        },
                        {
                            "trade_date": "2024-09-07",
                            "trade_date_iso": "2024-09-07T00:00:00",
                            "quantity": 10,
                            "price": 96.99,
                            "amount": 969.9,
                            "profit_loss": 969.9 - (4742.5 / 5),
                            "percent_profit_loss": ((96.99 - 94.85) / 94.85) * 100,
                        },
                    ],
                },
            ],
            "NVDA": [
                {
                    "trade_date": "2024-08-22",
                    "trade_date_iso": "2024-08-22T00:00:00",
                    "quantity": 200,
                    "price": 300,
                    "amount": -60000.0,
                    "current_sold_qty": 200,
                    "sells": [
                        {
                            "trade_date": "2024-09-01",
                            "trade_date_iso": "2024-09-01T00:00:00",
                            "quantity": 150,
                            "price": 310.0,
                            "amount": 46500.0,
                            "profit_loss": 46500.0 - (60000.0 * 0.75),
                            "percent_profit_loss": ((310.0 - 300.0) / 300) * 100,
                        },
                        {
                            "trade_date": "2024-09-02",
                            "trade_date_iso": "2024-09-02T00:00:00",
                            "quantity": 50,
                            "price": 315.0,
                            "amount": 15750.0,
                            "profit_loss": 15750.0 - (60000.0 * 0.25),
                            "percent_profit_loss": ((315.0 - 300.0) / 300) * 100,
                        },
                    ],
                }
            ],
            "TNA": [
                {
                    "trade_date": "2024-07-31",
                    "trade_date_iso": "2024-07-31T00:00:00",
                    "quantity": 150,
                    "price": 50.25,
                    "amount": -7537.5,
                    "current_sold_qty": 150,
                    "sells": [
                        {
                            "trade_date": "2024-08-01",
                            "trade_date_iso": "2024-08-01T00:00:00",
                            "quantity": 100,
                            "price": 47.2,
                            "amount": 4720.0,
                            "profit_loss": (47.20 - 50.25) * 100,
                            "percent_profit_loss": ((47.2 - 50.25) / 50.25) * 100,
                        },
                        {
                            "trade_date": "2024-08-27",
                            "trade_date_iso": "2024-08-27T00:00:00",
                            "quantity": 50,
                            "price": 43.2601,
                            "amount": 2163.01,
                            "profit_loss": (43.2601 - 50.25) * 50,
                            "percent_profit_loss": ((43.2601 - 50.25) / 50.25) * 100,
                        },
                    ],
                }
            ],
            "NAIL": [
                {
                    "trade_date": "2024-07-25",
                    "trade_date_iso": "2024-07-25T00:00:00",
                    "quantity": 40,
                    "price": 130.4599,
                    "amount": -5218.4,
                    "current_sold_qty": 40,
                    "sells": [
                        {  # NAIL|S|2024-08-27|50.0|145.4|7270.0  -> 40 of 50
                            "trade_date": "2024-08-27",
                            "trade_date_iso": "2024-08-27T00:00:00",
                            "quantity": 40,
                            "price": 145.4,
                            "amount": (145.4 * 40),
                            "profit_loss": (145.4 * 40) - (130.4599 * 40),
                            "percent_profit_loss": (
                                ((145.4 * 40) - (130.4599 * 40)) / (130.4599 * 40)
                            )
                            * 100,
                        }
                    ],
                },
                {
                    "trade_date": "2024-07-26",
                    "trade_date_iso": "2024-07-26T00:00:00",
                    "quantity": 40,
                    "price": 145.00,
                    "amount": -5800.0,
                    "current_sold_qty": 40,
                    # Half of one sell
                    "sells": [
                        {
                            "trade_date": "2024-08-27",
                            "trade_date_iso": "2024-08-27T00:00:00",
                            "quantity": 10,
                            "price": 145.4,
                            "amount": (145.4 * 10),
                            "profit_loss": (145.4 * 10) - (145.00 * 10),
                            "percent_profit_loss": (
                                ((145.4 * 10) - (145.00 * 10)) / (145.00 * 10)
                            )
                            * 100,
                        },
                        {  # NAIL|S|2024-08-27|80.0|147.5|11800.0 -> 30 of 80
                            "trade_date": "2024-08-27",
                            "trade_date_iso": "2024-08-27T00:00:00",
                            "quantity": 30,
                            "price": 147.5,
                            "amount": (147.5 * 30),
                            "profit_loss": (147.5 * 30) - (145.00 * 30),
                            "percent_profit_loss": (
                                ((147.5 * 30) - (145.00 * 30)) / (145.00 * 30)
                            )
                            * 100,
                        },
                    ],
                },
                {  # NAIL|B|2024-08-05|50.0|127.1|-6355.0
                    "trade_date": "2024-08-05",
                    "trade_date_iso": "2024-08-05T00:00:00",
                    "quantity": 50,
                    "price": 127.10,
                    "amount": -6355.0,
                    "current_sold_qty": 50,
                    "sells": [
                        {  # NAIL|S|2024-08-27|80.0|147.5|11800.0 -> 30 + 50 of 80
                            "trade_date": "2024-08-27",
                            "trade_date_iso": "2024-08-27T00:00:00",
                            "quantity": 50,
                            "price": 147.50,
                            "amount": 7375.0,  # (11800.0/80) * 50
                            "profit_loss": (147.5 * 50) - (127.10 * 50),
                            "percent_profit_loss": (
                                ((147.5 * 50) - (127.1 * 50)) / (127.1 * 50)
                            )
                            * 100,
                        },
                    ],
                },
                {  # NAIL|B|2024-08-30|50.0|145.7|-7285.0
                    "trade_date": "2024-08-30",
                    "trade_date_iso": "2024-08-30T00:00:00",
                    "quantity": 50,
                    "price": 145.7,
                    "amount": -7285.0,
                    "current_sold_qty": 50,
                    "sells": [
                        {  # NAIL|S|2024-09-03|50.0|140.6|7030.0
                            "trade_date": "2024-09-03",
                            "trade_date_iso": "2024-09-03T00:00:00",
                            "quantity": 50,
                            "price": 140.6,
                            "amount": 7030.0,
                            "profit_loss": (140.6 * 50) - (145.7 * 50),
                            "percent_profit_loss": ((140.6 - 145.7) / 145.7) * 100,
                        }
                    ],
                },
                {  # NAIL|B|2024-09-12|50.0|140.87|-7043.5
                    "trade_date": "2024-09-12",
                    "trade_date_iso": "2024-09-12T00:00:00",
                    "quantity": 50,
                    "price": 140.87,
                    "amount": -7043.5,
                    "current_sold_qty": 50,
                    "sells": [
                        {  # NAIL|S|2024-09-13|50.0|156.38|7819.0
                            "trade_date": "2024-09-13",
                            "trade_date_iso": "2024-09-13T00:00:00",
                            "quantity": 50,
                            "price": 156.38,
                            "amount": 7819.0,
                            "profit_loss": (156.38 * 50) - (140.87 * 50),
                            "percent_profit_loss": ((156.38 - 140.87) / 140.87) * 100,
                        }
                    ],
                },
                {  # NAIL|B|2024-09-16|40.0|159.6201|-6384.8
                    "trade_date": "2024-09-16",
                    "trade_date_iso": "2024-09-16T00:00:00",
                    "quantity": 40,
                    "price": 159.6201,
                    "amount": -6384.8,
                    "current_sold_qty": 0,
                    "sells": [],
                },
            ],
            "NIO": [
                {
                    "trade_date": "2024-09-24",
                    "trade_date_iso": "2024-09-24T00:00:00",
                    "quantity": 1000,
                    "price": 5.865,
                    "amount": -5865.0,
                    "current_sold_qty": 1000,
                    "sells": [
                        {
                            "trade_date": "2024-09-25",
                            "trade_date_iso": "2024-09-25T00:00:00",
                            "quantity": 1000,
                            "price": 5.5905,
                            "amount": 5590.5,
                            "profit_loss": 5590.5 - 5865.0,
                            "percent_profit_loss": ((5590.5 - 5865.0) / 5865.0) * 100,
                        }
                    ],
                    "account": "R",
                },
                {
                    "trade_date": "2024-09-25",
                    "trade_date_iso": "2024-09-25T00:00:00",
                    "quantity": 800,
                    "price": 5.73,
                    "amount": -4584.0,
                    "current_sold_qty": 400,
                    "sells": [
                        {
                            "trade_date": "2024-09-30",
                            "trade_date_iso": "2024-09-30T00:00:00",
                            "quantity": 400,
                            "price": 7.38,
                            "amount": 2952.0,
                            "profit_loss": 2952.0 - (4584.0 / 2),
                            "percent_profit_loss": (
                                (2952.0 - (4584.0 / 2)) / (4584.0 / 2)
                            )
                            * 100,
                        }
                    ],
                    "account": "R",
                },
                {
                    "trade_date": "2024-09-26",
                    "trade_date_iso": "2024-09-26T00:00:00",
                    "quantity": 200,
                    "price": 5.8199,
                    "amount": -1163.98,
                    "current_sold_qty": 0,
                    "sells": [],
                    "account": "R",
                },
                {
                    "trade_date": "2024-10-03",
                    "trade_date_iso": "2024-10-03T00:00:00",
                    "quantity": 100,
                    "price": 6.759,
                    "amount": -675.9,
                    "current_sold_qty": 0,
                    "sells": [],
                    "account": "R",
                },
                {
                    "trade_date": "2024-10-04",
                    "trade_date_iso": "2024-10-04T00:00:00",
                    "quantity": 100,
                    "price": 6.5399,
                    "amount": -653.99,
                    "current_sold_qty": 0,
                    "sells": [],
                    "account": "C",
                },
            ],
        }


        self.check_fields = [
                "trade_id",
                "amount",
                "trade_date",
                "price",
                "quantity",
                "profit_loss",
                "percent_profit_loss",
                "account",
            ]

    # @unittest.skip("Skip SN")
    def test_analyze_trades_sn(self):
        symbol = next(iter(self.data_list[0]))
        transactions = self.data_list[0][symbol]
        self.assertEqual(symbol, "SN")
        analyzer = TradingAnalyzer(symbol, transactions)
        analyzer.analyze_trades()
        profit_loss_data = analyzer.get_profit_loss_data()
        stock_summary = profit_loss_data["stock"]["summary"]
        all_trades = profit_loss_data["stock"]["all_trades"]

        # Check results for symbol 'SN'
        expected_bought_amount = -9139.0 - 4474.82 - 4585.0 - 4742.5 - 2474.75
        expected_sold_amount = 8894.27 + 9492.0 + 2373.5 + 969.9
        expected_closed_bought_amount = (
            -9139.0 - 4474.82 - 4585.0 - round((4742.5 / 50) * 35, 2)
        )
        expected_open_bought_amount = (
            expected_bought_amount - expected_closed_bought_amount
        )
        expected_profit_loss = expected_sold_amount + expected_closed_bought_amount
        expected_profit_loss_percent = (
            abs(expected_profit_loss / expected_closed_bought_amount) * 100
        )

        self.assertEqual(stock_summary["bought_quantity"], 275.0)

        self.assertAlmostEqual(stock_summary["bought_amount"], -25416.07, places=2)

        self.assertEqual(stock_summary["sold_quantity"], 235.0)

        self.assertAlmostEqual(stock_summary["sold_amount"], 20759.77 + 969.9, places=2)
        self.assertEqual(
            stock_summary["closed_bought_quantity"], 235.0, "SN closed_bought_quantity"
        )
        self.assertAlmostEqual(
            stock_summary["closed_bought_amount"],
            expected_closed_bought_amount,
            places=2,
            msg="SN closed_bought_amount",
        )

        self.assertEqual(stock_summary["open_bought_quantity"], 40.0)

        self.assertAlmostEqual(
            stock_summary["open_bought_amount"], expected_open_bought_amount, places=2
        )
        self.assertAlmostEqual(
            stock_summary["profit_loss"], expected_profit_loss, places=2
        )
        self.assertAlmostEqual(
            stock_summary["percent_profit_loss"], expected_profit_loss_percent, places=2
        )

        # Complete Trades
        self.assertEqual(len(all_trades), 5, "SN - all_trades count")

        for i, expected_trade in enumerate(self.expect_trades["SN"]):
            got_trade = all_trades[i]
            self.assertEqual(got_trade["trade_date"], expected_trade["trade_date"])
            self.assertEqual(
                got_trade["quantity"], expected_trade["quantity"], "SN - quantity"
            )
            self.assertEqual(got_trade["amount"], expected_trade["amount"])
            self.assertEqual(
                got_trade["current_sold_qty"], expected_trade["current_sold_qty"]
            )

            self.assertEqual(len(got_trade["sells"]), len(expected_trade["sells"]))
            for j, expected_sell in enumerate(expected_trade["sells"]):
                got_sell = got_trade["sells"][j]
                self.assertEqual(got_sell["trade_date"], expected_sell["trade_date"])
                self.assertEqual(got_sell["quantity"], expected_sell["quantity"])
                self.assertEqual(got_sell["price"], expected_sell["price"])
                self.assertAlmostEqual(
                    got_sell["profit_loss"], expected_sell["profit_loss"], places=2
                )
                self.assertAlmostEqual(
                    got_sell["percent_profit_loss"],
                    expected_sell["percent_profit_loss"],
                    places=2,
                )

    # @unittest.skip("Skip NVDA")
    def test_analyze_trades_nvda(self):

        symbol = next(iter(self.data_list[1]))
        transactions = self.data_list[1][symbol]
        self.assertEqual(symbol, "NVDA")
        analyzer = TradingAnalyzer(symbol, transactions)
        analyzer.analyze_trades()
        profit_loss_data = analyzer.get_profit_loss_data()
        stock_summary = profit_loss_data["stock"]["summary"]
        all_trades = profit_loss_data["stock"]["all_trades"]

        # Check results for symbol 'NVDA'
        self.assertEqual(stock_summary["bought_quantity"], 200.0)
        self.assertAlmostEqual(stock_summary["bought_amount"], -60000.0, places=2)
        self.assertEqual(stock_summary["sold_quantity"], 200.0)
        self.assertAlmostEqual(stock_summary["sold_amount"], 62250.0, places=2)
        self.assertEqual(stock_summary["closed_bought_quantity"], 200.0)
        self.assertAlmostEqual(
            stock_summary["closed_bought_amount"], -60000.0, places=2
        )

        self.assertEqual(stock_summary["open_bought_quantity"], 0)
        self.assertAlmostEqual(stock_summary["open_bought_amount"], 0, places=2)

        self.assertAlmostEqual(stock_summary["profit_loss"], 2250.0, places=2)
        self.assertAlmostEqual(stock_summary["percent_profit_loss"], 3.75, places=2)
        # Complete Trades
        self.assertEqual(len(all_trades), 1)

        for i, expected_trade in enumerate(self.expect_trades["NVDA"]):
            got_trade = all_trades[i]
            self.assertEqual(got_trade["trade_date"], expected_trade["trade_date"])
            self.assertEqual(got_trade["quantity"], expected_trade["quantity"])
            self.assertEqual(got_trade["amount"], expected_trade["amount"])
            self.assertEqual(
                got_trade["current_sold_qty"], expected_trade["current_sold_qty"]
            )
            self.assertEqual(len(got_trade["sells"]), len(expected_trade["sells"]))
            for j, expected_sell in enumerate(expected_trade["sells"]):
                got_sell = got_trade["sells"][j]
                self.assertEqual(got_sell["trade_date"], expected_sell["trade_date"])
                self.assertEqual(got_sell["quantity"], expected_sell["quantity"])
                self.assertEqual(got_sell["price"], expected_sell["price"])
                self.assertAlmostEqual(
                    got_sell["profit_loss"], expected_sell["profit_loss"], places=2
                )
                self.assertAlmostEqual(
                    got_sell["percent_profit_loss"],
                    expected_sell["percent_profit_loss"],
                    places=2,
                )

    # @unittest.skip("Skip TNA")
    def test_analyze_trades_tna(self):

        symbol = next(iter(self.data_list[2]))
        transactions = self.data_list[2][symbol]
        self.assertEqual(symbol, "TNA")
        analyzer = TradingAnalyzer(symbol, transactions)
        analyzer.analyze_trades()
        profit_loss_data = analyzer.get_profit_loss_data()
        stock_summary = profit_loss_data["stock"]["summary"]
        all_trades = profit_loss_data["stock"]["all_trades"]

        # Check results for symbol 'TNA'
        self.assertEqual(stock_summary["bought_quantity"], 150.0)
        self.assertAlmostEqual(stock_summary["bought_amount"], -7537.5, places=2)
        self.assertEqual(stock_summary["sold_quantity"], 150.0)
        self.assertAlmostEqual(stock_summary["sold_amount"], 4720.0 + 2163.01, places=2)

        self.assertEqual(stock_summary["closed_bought_quantity"], 150.0)
        self.assertAlmostEqual(stock_summary["closed_bought_amount"], -7537.5, places=2)

        self.assertEqual(stock_summary["open_bought_quantity"], 0.0)
        self.assertAlmostEqual(stock_summary["open_bought_amount"], 0, places=2)

        self.assertAlmostEqual(
            stock_summary["profit_loss"], -7537.5 + 4720.0 + 2163.01, places=2
        )
        self.assertAlmostEqual(stock_summary["percent_profit_loss"], -8.68, places=2)
        # Complete Trades
        self.assertEqual(len(all_trades), 1)

        for i, expected_trade in enumerate(self.expect_trades["TNA"]):
            got_trade = all_trades[i]
            self.assertEqual(got_trade["trade_date"], expected_trade["trade_date"])
            self.assertEqual(got_trade["quantity"], expected_trade["quantity"])
            self.assertEqual(got_trade["amount"], expected_trade["amount"])
            self.assertEqual(
                got_trade["current_sold_qty"], expected_trade["current_sold_qty"]
            )
            self.assertEqual(len(got_trade["sells"]), len(expected_trade["sells"]))
            for j, expected_sell in enumerate(expected_trade["sells"]):
                got_sell = got_trade["sells"][j]
                self.assertEqual(got_sell["trade_date"], expected_sell["trade_date"])
                self.assertEqual(got_sell["quantity"], expected_sell["quantity"])
                self.assertEqual(got_sell["price"], expected_sell["price"])

                self.assertAlmostEqual(
                    got_sell["profit_loss"], expected_sell["profit_loss"], places=1
                )
                self.assertAlmostEqual(
                    got_sell["percent_profit_loss"],
                    expected_sell["percent_profit_loss"],
                    places=2,
                )

    # @unittest.skip("Skip NAIL")
    def test_analyze_trades_nail(self):
        # Expected:
        symbol = next(iter(self.data_list[3]))
        transactions = self.data_list[3][symbol]
        self.assertEqual(symbol, "NAIL")
        analyzer = TradingAnalyzer(symbol, transactions)
        analyzer.analyze_trades()
        profit_loss_data = analyzer.get_profit_loss_data()
        stock_summary = profit_loss_data["stock"]["summary"]
        all_trades = profit_loss_data["stock"]["all_trades"]

        # Check results for symbol 'NAIL'
        expected_bought_qty = 270
        expected_bought_amount = -38086.7
        expected_sold_qty = 230
        expected_sold_amount = 33919.0

        # -38086.7 + 6384.8 = −31701.9
        expected_closed_bought_amount = round(-38086.7 + 6384.8, 2)
        expected_open_bought_amount = -6384.8

        # bought amounts are negative numbers
        expected_profit_loss = expected_sold_amount + expected_closed_bought_amount
        expected_profit_loss_percent = (
            abs(expected_profit_loss / expected_closed_bought_amount) * 100
        )

        self.assertEqual(stock_summary["bought_quantity"], expected_bought_qty)

        self.assertAlmostEqual(
            stock_summary["bought_amount"], expected_bought_amount, places=2
        )

        self.assertEqual(stock_summary["sold_quantity"], expected_sold_qty)

        self.assertAlmostEqual(
            stock_summary["sold_amount"], expected_sold_amount, places=2
        )
        self.assertEqual(
            stock_summary["closed_bought_quantity"],
            expected_sold_qty,
            "NAIL closed_bought_quantity",
        )

        self.assertAlmostEqual(
            stock_summary["closed_bought_amount"],
            expected_closed_bought_amount,
            places=2,
        )

        self.assertEqual(stock_summary["open_bought_quantity"], 40.0)

        self.assertAlmostEqual(
            stock_summary["open_bought_amount"], expected_open_bought_amount, places=2
        )
        self.assertAlmostEqual(
            stock_summary["profit_loss"], expected_profit_loss, places=2
        )
        self.assertAlmostEqual(
            stock_summary["percent_profit_loss"],
            expected_profit_loss_percent,
            places=2,
        )

        # Complete Trades
        self.assertEqual(len(all_trades), 6)

        for i, expected_trade in enumerate(self.expect_trades["NAIL"]):
            got_trade = all_trades[i]
            self.assertEqual(got_trade["trade_date"], expected_trade["trade_date"])
            self.assertEqual(got_trade["quantity"], expected_trade["quantity"])
            self.assertEqual(got_trade["amount"], expected_trade["amount"])
            self.assertEqual(
                got_trade["current_sold_qty"], expected_trade["current_sold_qty"]
            )
            self.assertEqual(len(got_trade["sells"]), len(expected_trade["sells"]))
            for j, expected_sell in enumerate(expected_trade["sells"]):
                got_sell = got_trade["sells"][j]
                self.assertEqual(got_sell["trade_date"], expected_sell["trade_date"])
                self.assertEqual(got_sell["quantity"], expected_sell["quantity"])
                self.assertEqual(got_sell["amount"], expected_sell["amount"])
                self.assertEqual(got_sell["price"], expected_sell["price"])

                self.assertAlmostEqual(
                    got_sell["profit_loss"], expected_sell["profit_loss"], places=2
                )
                self.assertAlmostEqual(
                    got_sell["percent_profit_loss"],
                    expected_sell["percent_profit_loss"],
                    places=2,
                )

    def test_analyze_trades_nio(self):
        # Expected:
        symbol = next(iter(self.data_list[4]))
        transactions = self.data_list[4][symbol]
        self.assertEqual(symbol, "NIO")
        analyzer = TradingAnalyzer(symbol, transactions)
        analyzer.analyze_trades()
        profit_loss_data = analyzer.get_profit_loss_data()
        stock_summary = profit_loss_data["stock"]["summary"]
        all_trades = profit_loss_data["stock"]["all_trades"]

        # Check results for symbol 'NIO'
        expected_bought_qty = 2200
        # -5865.0 -4584.0 -1163.98 -675.9 -653.99
        expected_bought_amount = -12942.87
        expected_sold_qty = 1400
        # 5590.5 + 2952.0
        expected_sold_amount = 8542.5
        # -5865.0 - (4584.0/2)
        expected_closed_bought_amount = -8157.0
        # (-4584.0/2) -1163.98 -675.9 -653.99
        expected_open_bought_amount = -4785.87

        expected_profit_loss = expected_sold_amount + expected_closed_bought_amount
        expected_profit_loss_percent = (
            abs(expected_profit_loss / expected_closed_bought_amount) * 100
        )

        self.assertEqual(stock_summary["bought_quantity"], expected_bought_qty)

        self.assertAlmostEqual(
            stock_summary["bought_amount"], expected_bought_amount, places=2
        )

        self.assertEqual(stock_summary["sold_quantity"], expected_sold_qty)

        self.assertAlmostEqual(
            stock_summary["sold_amount"], expected_sold_amount, places=2
        )
        self.assertEqual(
            stock_summary["closed_bought_quantity"],
            expected_sold_qty,
            "NIO closed_bought_quantity",
        )

        self.assertAlmostEqual(
            stock_summary["closed_bought_amount"],
            expected_closed_bought_amount,
            places=2,
            msg="NIO closed_bought_amount",
        )

        self.assertEqual(stock_summary["open_bought_quantity"], 800.0)

        self.assertAlmostEqual(
            stock_summary["open_bought_amount"], expected_open_bought_amount, places=2
        )
        self.assertAlmostEqual(
            stock_summary["profit_loss"], expected_profit_loss, places=2
        )
        self.assertAlmostEqual(
            stock_summary["percent_profit_loss"],
            expected_profit_loss_percent,
            places=2,
        )

        # Complete Trades
        self.assertEqual(len(all_trades), 5)

        for i, expected_trade in enumerate(self.expect_trades["NIO"]):
            got_trade = all_trades[i]
            self.assertEqual(got_trade["trade_date"], expected_trade["trade_date"])
            self.assertEqual(got_trade["quantity"], expected_trade["quantity"])
            self.assertEqual(got_trade["amount"], expected_trade["amount"])
            self.assertEqual(
                got_trade["current_sold_qty"], expected_trade["current_sold_qty"]
            )
            self.assertEqual(len(got_trade["sells"]), len(expected_trade["sells"]))
            for j, expected_sell in enumerate(expected_trade["sells"]):
                got_sell = got_trade["sells"][j]
                self.assertEqual(got_sell["trade_date"], expected_sell["trade_date"])
                self.assertEqual(got_sell["quantity"], expected_sell["quantity"])
                self.assertEqual(got_sell["amount"], expected_sell["amount"])
                self.assertEqual(got_sell["price"], expected_sell["price"])

                self.assertAlmostEqual(
                    got_sell["profit_loss"],
                    expected_sell["profit_loss"],
                    places=2,
                    msg="NIO - profit_loss",
                )
                self.assertAlmostEqual(
                    got_sell["percent_profit_loss"],
                    expected_sell["percent_profit_loss"],
                    places=2,
                    msg="NIO - percent_profit_loss",
                )

                # Add the following test cases to the `tests/test_trading_analyzer.py` file

    def test_get_open_trades_sn(self):

        symbol = next(iter(self.data_list[0]))
        transactions = self.data_list[0][symbol]
        self.assertEqual(symbol, "SN")
        analyzer = TradingAnalyzer(symbol, transactions)
        analyzer.analyze_trades()
        profit_loss_data = analyzer.get_open_trades()
        # stock_summary = profit_loss_data["stock"]["summary"]
        open_trades = profit_loss_data["stock"]["all_trades"]

        expected_open_trades = [
            {
                "trade_date": "2024-08-30",
                "quantity": 50,
                "price": 94.85,
                "amount": -4742.5,
                "current_sold_qty": 35,
                "sells": [
                    {
                        "amount": 2373.5,
                        "percent_profit_loss": 0.09,
                        "price": 94.94,
                        "profit_loss": 2.25,
                        "quantity": 25.0,
                        "trade_date": "2024-09-06",
                        "trade_id": "0007",
                        "account": "C",
                    },
                    {
                        "amount": 969.9,
                        "percent_profit_loss": 2.26,
                        "price": 96.99,
                        "profit_loss": 21.4,
                        "quantity": 10.0,
                        "trade_date": "2024-09-07",
                        "trade_id": "0008",
                        "account": "C",
                    },
                ],
                "is_done": False,
            },
            {
                "trade_date": "2024-09-10",
                "quantity": 25,
                "price": 98.99,
                "amount": -2474.75,
                "current_sold_qty": 0,
                "sells": [],
                "is_done": False,
            },
        ]

        self.assertEqual(len(open_trades), len(expected_open_trades))
        for i, expected_trade in enumerate(expected_open_trades):
            got_trade = open_trades[i]
            self.assertEqual(got_trade["trade_date"], expected_trade["trade_date"])
            self.assertEqual(got_trade["quantity"], expected_trade["quantity"])
            self.assertEqual(got_trade["price"], expected_trade["price"])
            self.assertEqual(got_trade["amount"], expected_trade["amount"])
            self.assertEqual(
                got_trade["current_sold_qty"], expected_trade["current_sold_qty"]
            )

            self.assertEqual(len(got_trade["sells"]), len(expected_trade["sells"]))
            for j, expected_sell in enumerate(expected_trade["sells"]):
                got_sell = got_trade["sells"][j]
                for field in self.check_fields:
                    self.assertEqual(got_sell[field], expected_sell[field], f"[SN] Field {field} does not match")
            self.assertEqual(got_trade["is_done"], expected_trade["is_done"])

    def test_get_open_trades_nvda(self):
        analyzer = TradingAnalyzer("NVDA", self.data_list[1]["NVDA"])
        analyzer.analyze_trades()
        profit_loss_data = analyzer.get_open_trades()
        open_trades = profit_loss_data["stock"]["all_trades"]
        expected_open_trades = []
        self.assertEqual(len(open_trades), len(expected_open_trades))

    def test_get_open_trades_tna(self):
        analyzer = TradingAnalyzer("TNA", self.data_list[2]["TNA"])
        analyzer.analyze_trades()
        profit_loss_data = analyzer.get_open_trades()
        open_trades = profit_loss_data["stock"]["all_trades"]
        expected_open_trades = []
        self.assertEqual(len(open_trades), len(expected_open_trades))

    def test_get_open_trades_nail(self):
        analyzer = TradingAnalyzer("NAIL", self.data_list[3]["NAIL"])
        analyzer.analyze_trades()
        profit_loss_data = analyzer.get_open_trades()
        open_trades = profit_loss_data["stock"]["all_trades"]

        expected_open_trades = [
            {
                "trade_date": "2024-09-16",
                "quantity": 40,
                "price": 159.6201,
                "amount": -6384.8,
                "current_sold_qty": 0,
                "sells": [],
                "is_done": False,
            }
        ]

        self.assertEqual(len(open_trades), len(expected_open_trades))
        for i, expected_trade in enumerate(expected_open_trades):
            got_trade = open_trades[i]
            self.assertEqual(got_trade["trade_date"], expected_trade["trade_date"])
            self.assertEqual(got_trade["quantity"], expected_trade["quantity"])
            self.assertEqual(got_trade["price"], expected_trade["price"])
            self.assertEqual(got_trade["amount"], expected_trade["amount"])
            self.assertEqual(
                got_trade["current_sold_qty"], expected_trade["current_sold_qty"]
            )

            # self.assertEqual(got_trade["sells"], expected_trade["sells"])

            for j, expected_sell in enumerate(expected_trade["sells"]):
                got_sell = got_trade["sells"][j]
                for field in self.check_fields:
                    self.assertEqual(got_sell[field], expected_sell[field], f"[NAIL] Field {field} does not match")
            self.assertEqual(got_trade["is_done"], expected_trade["is_done"])

    def test_get_open_trades_nio(self):
        symbol = next(iter(self.data_list[4]))
        transactions = self.data_list[4][symbol]
        self.assertEqual(symbol, "NIO")
        analyzer = TradingAnalyzer(symbol, transactions)
        analyzer.analyze_trades()
        profit_loss_data = analyzer.get_open_trades()
        # stock_summary = profit_loss_data["stock"]["summary"]
        open_trades = profit_loss_data["stock"]["all_trades"]

        expected_open_trades = [
            {
                # "Id": "507",
                "trade_date": "2024-09-25",
                "quantity": 800,
                "price": 5.73,
                "amount": -4584.0,
                "current_sold_qty": 400,
                "is_done": False,
                "account": "R",
                "sells": [
                    {
                        "trade_id": "518",
                        "trade_date": "2024-09-30",
                        "quantity": 400.0,
                        "price": 7.38,
                        "amount": 2952.0,
                        "profit_loss": 660.0,
                        "percent_profit_loss": 28.8,
                        "account": "R",
                    }
                ],
            },
            {
                # "Id": "504",
                "trade_date": "2024-09-26",
                "quantity": 200,
                "price": 5.8199,
                "amount": -1163.98,
                "current_sold_qty": 0,
                "sells": [],
                "is_done": False,
                "account": "R",
            },
            {
                "trade_date": "2024-10-03",
                "quantity": 100,
                "price": 6.759,
                "amount": -675.9,
                "current_sold_qty": 0,
                "sells": [],
                "is_done": False,
                "account": "R",
            },
            {
                "trade_date": "2024-10-04",
                "quantity": 100,
                "price": 6.5399,
                "amount": -653.99,
                "current_sold_qty": 0,
                "sells": [],
                "is_done": False,
                "account": "C",
            },
        ]

        self.assertEqual(len(open_trades), len(expected_open_trades))

        for i, expected_trade in enumerate(expected_open_trades):
            got_trade = open_trades[i]
            self.assertEqual(got_trade["trade_date"], expected_trade["trade_date"])
            self.assertEqual(got_trade["quantity"], expected_trade["quantity"])
            self.assertEqual(got_trade["price"], expected_trade["price"])
            self.assertEqual(got_trade["amount"], expected_trade["amount"])
            self.assertEqual(
                got_trade["current_sold_qty"], expected_trade["current_sold_qty"]
            )
            # self.assertEqual(got_trade["sells"], expected_trade["sells"])
            for j, expected_sell in enumerate(expected_trade["sells"]):
                got_sell = got_trade["sells"][j]
                for field in self.check_fields:
                    self.assertEqual(got_sell[field], expected_sell[field], f"[NIO] Field {field} does not match")

            self.assertEqual(got_trade["is_done"], expected_trade["is_done"])


if __name__ == "__main__":
    unittest.main()
