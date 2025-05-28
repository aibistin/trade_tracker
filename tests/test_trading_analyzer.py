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
                        "id": "0001",
                        "symbol": "SN",
                        "action": "B",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 100.0,
                        "price": 91.39,
                        "target_price": 0.0,
                        "trade_date": "2024-08-22",
                        "amount": -9139.0,
                        "account": "C",
                    },
                    {
                        "id": "0002",
                        "symbol": "SN",
                        "action": "S",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 100.0,
                        "price": 88.9427,
                        "target_price": 0.0,
                        "trade_date": "2024-08-23",
                        "amount": 8894.27,
                        "account": "C",
                    },
                    # Sold 100
                    {
                        "id": "0003",
                        "symbol": "SN",
                        "action": "B",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 50.0,
                        "price": 89.4964,
                        "target_price": 0.0,
                        "trade_date": "2024-08-26",
                        "amount": -4474.82,
                        "account": "C",
                    },
                    # Sold 50
                    {
                        "id": "0004",
                        "symbol": "SN",
                        "action": "B",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 50.0,
                        "price": 91.7,
                        "target_price": 0.0,
                        "trade_date": "2024-08-27",
                        "amount": -4585.0,
                        "account": "C",
                    },
                    # Sold 50
                    {
                        "id": "0005",
                        "symbol": "SN",
                        "action": "S",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 100.0,
                        "price": 94.92,
                        "target_price": 0.0,
                        "trade_date": "2024-09-06",
                        "amount": 9492.0,
                        "account": "C",
                    },
                    # Sold for previous two trades
                    {
                        "id": "0006",
                        "symbol": "SN",
                        "action": "B",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 50.0,
                        "price": 94.85,
                        "target_price": 0.0,
                        "trade_date": "2024-08-30",
                        "amount": -4742.5,
                        "account": "C",
                    },
                    {
                        "id": "0007",
                        "symbol": "SN",
                        "action": "S",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 25.0,
                        "price": 94.94,
                        "target_price": 0.0,
                        "trade_date": "2024-09-06",
                        "amount": 2373.5,
                        "account": "C",
                    },
                    {
                        "id": "0008",
                        "symbol": "SN",
                        "action": "S",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 10.0,
                        "price": 96.99,
                        "target_price": 0.0,
                        "trade_date": "2024-09-07",
                        "amount": 969.9,
                        "account": "C",
                    },
                    {
                        "id": "0009",
                        "symbol": "SN",
                        "action": "B",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 25.0,
                        "price": 98.99,
                        "target_price": 0.0,
                        "trade_date": "2024-09-10",
                        "amount": -2474.75,
                        "account": "C",
                    },
                ]
            },
            {
                "NVDA": [
                    {
                        "id": "0011",
                        "symbol": "NVDA",
                        "action": "B",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 200.0,
                        "price": 300.0,
                        "target_price": 0.0,
                        "trade_date": "2024-08-22",
                        "amount": -60000.0,
                        "account": "C",
                    },
                    {
                        "id": "0012",
                        "symbol": "NVDA",
                        "action": "S",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 150.0,
                        "price": 310.0,
                        "target_price": 0.0,
                        "trade_date": "2024-09-01",
                        "amount": 46500.0,
                        "account": "C",
                    },
                    {
                        "id": "0013",
                        "symbol": "NVDA",
                        "action": "S",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 50.0,
                        "price": 315.0,
                        "target_price": 0.0,
                        "trade_date": "2024-09-02",
                        "amount": 15750.0,
                        "account": "C",
                    },
                ]
            },
            {
                "TNA": [
                    {
                        "id": "0111",
                        "symbol": "TNA",
                        "action": "B",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 150.0,
                        "price": 50.25,
                        "target_price": 0.0,
                        "trade_date": "2024-07-31",
                        "amount": -7537.5,
                        "account": "C",
                    },
                    {
                        "id": "0112",
                        "symbol": "TNA",
                        "action": "S",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 100.0,
                        "price": 47.2,
                        "target_price": 0.0,
                        "trade_date": "2024-08-01",
                        "amount": 4720.0,
                        "account": "C",
                    },
                    {
                        "id": "0113",
                        "symbol": "TNA",
                        "action": "S",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 50.0,
                        "price": 43.2601,
                        "target_price": 0.0,
                        "trade_date": "2024-08-27",
                        "amount": 2163.01,
                        "account": "C",
                    },
                ]
            },
            {
                "NAIL": [
                    {
                        "id": "0222",
                        "symbol": "NAIL",
                        "action": "B",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 40.0,
                        "price": 130.4599,
                        "target_price": 0.0,
                        "trade_date": "2024-07-25",
                        "amount": -5218.4,
                        "account": "C",
                    },
                    {
                        "id": "0223",
                        "symbol": "NAIL",
                        "action": "B",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 40.0,
                        "price": 145.0,
                        "target_price": 0.0,
                        "trade_date": "2024-07-26",
                        "amount": -5800.0,
                        "account": "C",
                    },
                    {
                        "id": "0224",
                        "symbol": "NAIL",
                        "action": "B",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 50.0,
                        "price": 127.1,
                        "target_price": 0.0,
                        "trade_date": "2024-08-05",
                        "amount": -6355.0,
                        "account": "C",
                    },
                    {
                        "id": "0225",
                        "symbol": "NAIL",
                        "action": "S",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 50.0,
                        "price": 145.4,
                        "target_price": 0.0,
                        "trade_date": "2024-08-27",
                        "amount": 7270.0,
                        "account": "C",
                    },
                    {
                        "id": "0226",
                        "symbol": "NAIL",
                        "action": "S",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 80.0,
                        "price": 147.5,
                        "target_price": 0.0,
                        "trade_date": "2024-08-27",
                        "amount": 11800.0,
                        "account": "C",
                    },
                    {
                        "id": "0227",
                        "symbol": "NAIL",
                        "action": "B",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 50.0,
                        "price": 145.7,
                        "target_price": 0.0,
                        "trade_date": "2024-08-30",
                        "amount": -7285.0,
                        "account": "C",
                    },
                    {
                        "id": "0228",
                        "symbol": "NAIL",
                        "action": "S",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 50.0,
                        "price": 140.6,
                        "target_price": 0.0,
                        "trade_date": "2024-09-03",
                        "amount": 7030.0,
                        "account": "C",
                    },
                    {
                        "id": "0229",
                        "symbol": "NAIL",
                        "action": "B",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 50.0,
                        "price": 140.87,
                        "target_price": 0.0,
                        "trade_date": "2024-09-12",
                        "amount": -7043.5,
                        "account": "C",
                    },
                    {
                        "id": "0231",
                        "symbol": "NAIL",
                        "action": "S",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 50.0,
                        "price": 156.38,
                        "target_price": 0.0,
                        "trade_date": "2024-09-13",
                        "amount": 7819.0,
                        "account": "C",
                    },
                    {
                        "id": "0232",
                        "symbol": "NAIL",
                        "action": "B",
                        "trade_type": "L",
                        "label": "",
                        "quantity": 40.0,
                        "price": 159.6201,
                        "target_price": 0.0,
                        "trade_date": "2024-09-16",
                        "amount": -6384.8,
                        "account": "C",
                    },
                ]
            },
            {
                "NIO": [
                    {
                        "id": "500",
                        "symbol": "NIO",
                        "action": "B",
                        "trade_type": "L",
                        "trade_date": "2024-09-24",
                        "label": "",
                        "quantity": 1000.0,
                        "price": 5.865,
                        "target_price": 0.0,
                        "amount": -5865.0,
                        "account": "R",
                    },
                    {
                        "id": "504",
                        "symbol": "NIO",
                        "action": "B",
                        "trade_type": "L",
                        "trade_date": "2024-09-26",
                        "label": "",
                        "quantity": 200.0,
                        "price": 5.8199,
                        "target_price": 0.0,
                        "amount": -1163.98,
                        "account": "R",
                    },
                    {
                        "id": "507",
                        "symbol": "NIO",
                        "action": "B",
                        "trade_type": "L",
                        "trade_date": "2024-09-25",
                        "label": "",
                        "quantity": 800.0,
                        "price": 5.73,
                        "target_price": 0.0,
                        "amount": -4584.0,
                        "account": "R",
                    },
                    {
                        "id": "509",
                        "symbol": "NIO",
                        "action": "S",
                        "trade_type": "L",
                        "trade_date": "2024-09-25",
                        "label": "",
                        "quantity": 1000.0,
                        "price": 5.5905,
                        "target_price": 0.0,
                        "amount": 5590.5,
                        "account": "R",
                    },
                    {
                        "id": "518",
                        "symbol": "NIO",
                        "action": "S",
                        "trade_type": "L",
                        "trade_date": "2024-09-30",
                        "label": "",
                        "quantity": 400.0,
                        "price": 7.38,
                        "target_price": 0.0,
                        "amount": 2952.0,
                        "account": "R",
                    },
                    {
                        "id": "530",
                        "symbol": "NIO",
                        "action": "B",
                        "trade_type": "L",
                        "trade_date": "2024-10-03",
                        "label": "",
                        "quantity": 100.0,
                        "price": 6.759,
                        "target_price": 0.0,
                        "amount": -675.9,
                        "account": "R",
                    },
                    {
                        "id": "536",
                        "symbol": "NIO",
                        "action": "B",
                        "trade_type": "L",
                        "trade_date": "2024-10-04",
                        "label": "",
                        "quantity": 100.0,
                        "price": 6.5399,
                        "target_price": 0.0,
                        "amount": -653.99,
                        "account": "C",
                    },
                ]
            },
            {
                "SOUN": [
                    # 1 - One Buy and Two Sells
                    # 542|SOUN|BO|SOUN 09/20/2024 4.00 C|C|2024-07-16|2024-09-20||3.0|1.8|-540.0|4.0|||C
                    {
                        "id": "542",
                        "symbol": "SOUN",
                        "action": "BO",
                        "trade_type": "C",
                        "trade_date": "2024-07-16",
                        "expiration_date": "2024-09-20",
                        "label": "SOUN 09/20/2024 4.00 C",
                        "quantity": 3.0,
                        "price": 1.8,
                        "target_price": 4.0,
                        "amount": -540.0,
                        "account": "C",
                    },
                    # 520|SOUN|SC|SOUN 09/20/2024 4.00 C|C|2024-09-18|2024-09-20||2.0|0.87|174.0|4.0|||C
                    {
                        "id": "520",
                        "symbol": "SOUN",
                        "action": "SC",
                        "trade_type": "C",
                        "trade_date": "2024-09-18",
                        "expiration_date": "2024-09-20",
                        "label": "SOUN 09/20/2024 4.00 C",
                        "quantity": 2.00,
                        "price": 0.87,
                        "target_price": 4.0,
                        "amount": 174.0,
                        "account": "C",
                    },
                    # 529|SOUN|EE|SOUN 09/20/2024 4.00 C|O|2024-09-19|2024-09-20||1.0|0.0|None|4.0|||C
                    {
                        # Exchanged for 100 SOUN @ 4.0/shr
                        "id": "529",
                        "symbol": "SOUN",
                        "action": "EE",
                        "trade_type": "C",
                        "trade_date": "2024-09-19",
                        "expiration_date": "2024-09-20",
                        "label": "SOUN 09/20/2024 4.00 C",
                        "quantity": 1.00,
                        "price": 0.0,
                        "target_price": 4.0,
                        "amount": None,
                        "account": "C",
                    },
                    # 2 - One Buy and One Sell
                    # 526|SOUN|BO|SOUN 04/17/2025 5.00 C|C|2024-10-09|2025-04-17||1.0|0.92|-92.0|5.0|||I
                    {
                        "id": "526",
                        "symbol": "SOUN",
                        "action": "BO",
                        "trade_type": "C",
                        "trade_date": "2024-10-09",
                        "expiration_date": "2025-04-17",
                        "label": "SOUN 04/17/2025 5.00 C",
                        "quantity": 1.00,
                        "price": 0.92,
                        "target_price": 5.0,
                        "amount": -92.0,
                        "account": "I",
                    },
                    # 521|SOUN|SC|SOUN 04/17/2025 5.00 C|C|2025-02-21|2025-04-17||1.0|5.5|550.0|5.0|||I
                    {
                        "id": "521",
                        "symbol": "SOUN",
                        "action": "SC",
                        "trade_type": "C",
                        "trade_date": "2025-02-21",
                        "expiration_date": "2025-04-17",
                        "label": "SOUN 04/17/2025 5.00 C",
                        "quantity": 1.0,
                        "price": 5.5,
                        "target_price": 5.0,
                        "amount": 550.0,
                        "account": "I",
                    },
                    # 2 - One Buy and No Sell
                    # 462|SOUN|BO|SOUN 07/18/2025 8.00 C|C|2025-02-24|2025-07-18||1.0|3.05|-305.0|8.0|||C
                    {
                        "id": "462",
                        "symbol": "SOUN",
                        "action": "BO",
                        "trade_type": "C",
                        "trade_date": "2025-02-24",
                        "expiration_date": "2025-07-18",
                        "label": "SOUN 07/18/2025 8.00 C",
                        "quantity": 1.0,
                        "price": 3.05,
                        "target_price": 8.0,
                        "amount": -305.0,
                        "account": "C",
                    },
                ],
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
                    "account": "C",
                    "current_sold_qty": 100,
                    "sells": [
                        {
                            "trade_date": "2024-08-23",
                            "trade_date_iso": "2024-08-23T00:00:00",
                            "quantity": 100,
                            "price": 88.9427,
                            "amount": 8894.27,
                            "account": "C",
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
                    "account": "C",
                    "current_sold_qty": 50,
                    # Half of one sell
                    "sells": [
                        {
                            "trade_date": "2024-09-06",
                            "trade_date_iso": "2024-09-06T00:00:00",
                            "quantity": 50,
                            "price": 94.92,
                            "amount": 9492.00 / 2,
                            "account": "C",
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
                    "account": "C",
                    "current_sold_qty": 50,
                    # Half of one sell
                    "sells": [
                        {
                            "trade_date": "2024-09-06",
                            "trade_date_iso": "2024-09-06T00:00:00",
                            "quantity": 50,
                            "price": 94.92,
                            "amount": 9492.27 / 2,
                            "account": "C",
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
                    "account": "C",
                    "current_sold_qty": 35,
                    "sells": [
                        {
                            "trade_date": "2024-09-06",
                            "trade_date_iso": "2024-09-06T00:00:00",
                            "quantity": 25,
                            "price": 94.94,
                            "amount": 2373.5,
                            "account": "C",
                            "profit_loss": 2373.5 - (4742.5 / 2),
                            "percent_profit_loss": ((94.94 - 94.85) / 94.85) * 100,
                        },
                        {
                            "trade_date": "2024-09-07",
                            "trade_date_iso": "2024-09-07T00:00:00",
                            "quantity": 10,
                            "price": 96.99,
                            "amount": 969.9,
                            "account": "C",
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
                    "account": "C",
                    "current_sold_qty": 200,
                    "sells": [
                        {
                            "trade_date": "2024-09-01",
                            "trade_date_iso": "2024-09-01T00:00:00",
                            "quantity": 150,
                            "price": 310.0,
                            "amount": 46500.0,
                            "account": "C",
                            "profit_loss": 46500.0 - (60000.0 * 0.75),
                            "percent_profit_loss": ((310.0 - 300.0) / 300) * 100,
                        },
                        {
                            "trade_date": "2024-09-02",
                            "trade_date_iso": "2024-09-02T00:00:00",
                            "quantity": 50,
                            "price": 315.0,
                            "amount": 15750.0,
                            "account": "C",
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
                    "account": "C",
                    "current_sold_qty": 150,
                    "sells": [
                        {
                            "trade_date": "2024-08-01",
                            "trade_date_iso": "2024-08-01T00:00:00",
                            "quantity": 100,
                            "price": 47.2,
                            "amount": 4720.0,
                            "account": "C",
                            "profit_loss": (47.20 - 50.25) * 100,
                            "percent_profit_loss": ((47.2 - 50.25) / 50.25) * 100,
                        },
                        {
                            "trade_date": "2024-08-27",
                            "trade_date_iso": "2024-08-27T00:00:00",
                            "quantity": 50,
                            "price": 43.2601,
                            "amount": 2163.01,
                            "account": "C",
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
                    "account": "C",
                    "current_sold_qty": 40,
                    "sells": [
                        {  # NAIL|S|2024-08-27|50.0|145.4|7270.0  -> 40 of 50
                            "trade_date": "2024-08-27",
                            "trade_date_iso": "2024-08-27T00:00:00",
                            "quantity": 40,
                            "price": 145.4,
                            "amount": (145.4 * 40),
                            "account": "C",
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
                    "account": "C",
                    "current_sold_qty": 40,
                    # Half of one sell
                    "sells": [
                        {
                            "trade_date": "2024-08-27",
                            "trade_date_iso": "2024-08-27T00:00:00",
                            "quantity": 10,
                            "price": 145.4,
                            "amount": (145.4 * 10),
                            "account": "C",
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
                            "account": "C",
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
                    "account": "C",
                    "current_sold_qty": 50,
                    "sells": [
                        {  # NAIL|S|2024-08-27|80.0|147.5|11800.0 -> 30 + 50 of 80
                            "trade_date": "2024-08-27",
                            "trade_date_iso": "2024-08-27T00:00:00",
                            "quantity": 50,
                            "price": 147.50,
                            "amount": 7375.0,  # (11800.0/80) * 50
                            "account": "C",
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
                    "account": "C",
                    "current_sold_qty": 50,
                    "sells": [
                        {  # NAIL|S|2024-09-03|50.0|140.6|7030.0
                            "trade_date": "2024-09-03",
                            "trade_date_iso": "2024-09-03T00:00:00",
                            "quantity": 50,
                            "price": 140.6,
                            "amount": 7030.0,
                            "account": "C",
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
                    "account": "C",
                    "current_sold_qty": 50,
                    "sells": [
                        {  # NAIL|S|2024-09-13|50.0|156.38|7819.0
                            "trade_date": "2024-09-13",
                            "trade_date_iso": "2024-09-13T00:00:00",
                            "quantity": 50,
                            "price": 156.38,
                            "amount": 7819.0,
                            "account": "C",
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
                    "account": "C",
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
                    "account": "C",
                    "current_sold_qty": 1000,
                    "sells": [
                        {
                            "trade_date": "2024-09-25",
                            "trade_date_iso": "2024-09-25T00:00:00",
                            "quantity": 1000,
                            "price": 5.5905,
                            "amount": 5590.5,
                            "account": "C",
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
            # SOUN
            # expect_soun
            # 542|SOUN|BO|SOUN 09/20/2024 4.00 C|C|2024-07-16|2024-09-20||3.0|1.8|-540.0|4.0|||C
            # 520|SOUN|SC|SOUN 09/20/2024 4.00 C|C|2024-09-18|2024-09-20||2.0|0.87|174.0|4.0|||C
            # 529|SOUN|EE|SOUN 09/20/2024 4.00 C|O|2024-09-19|2024-09-20||1.0|0.0|None|4.0|||C
            "SOUN": [
                {
                    "trade_id": "542",
                    "trade_date": "2024-07-16",
                    "trade_date_iso": "2024-07-16T00:00:00",
                    "quantity": 3,
                    "trade_label": "SOUN 09/20/2024 4.00 C",
                    "trade_type": "C",
                    "price": 1.8,
                    "amount": -540.0,
                    "account": "C",
                    "current_sold_qty": 3,
                    "is_option": True,
                    "is_done": True,
                    "target_price": 4.0,
                    "expiration_date_iso": "2024-09-20T00:00:00",
                    "sells": [
                        {
                            "trade_id": "520",
                            "trade_date": "2024-09-18",
                            "trade_date_iso": "2024-09-18T00:00:00",
                            "trade_label": "SOUN 09/20/2024 4.00 C",
                            "is_option": True,
                            "quantity": 2,
                            "price": 0.87,
                            "amount": 174.0,
                            "target_price": 4.0,
                            "account": "C",
                            "profit_loss": 174.0 - 360.0,
                            "percent_profit_loss": round(
                                ((174.0 - 360.0) / 360.0) * 100, 2
                            ),
                            "expiration_date_iso": "2024-09-20T00:00:00",
                        },
                        {
                            # Exercised option
                            "trade_id": "529",
                            "trade_date": "2024-09-19",
                            "trade_date_iso": "2024-09-19T00:00:00",
                            "trade_label": "SOUN 09/20/2024 4.00 C",
                            "is_option": True,
                            "quantity": 1,
                            "price": 0.0,
                            # Amount will eventually be 4.0 * 100
                            "amount": None,
                            "target_price": 4.0,
                            "account": "C",
                            "profit_loss": 0.0,
                            "percent_profit_loss": 0.0,
                            "expiration_date_iso": "2024-09-20T00:00:00",
                        },
                    ],
                },
                # 526|SOUN|BO|SOUN 04/17/2025 5.00 C|C|2024-10-09|2025-04-17||1.0|0.92|-92.0|5.0|||I
                # 521|SOUN|SC|SOUN 04/17/2025 5.00 C|C|2025-02-21|2025-04-17||1.0|5.5|550.0|5.0|||I
                {
                    "trade_id": "526",
                    "trade_date": "2024-10-09",
                    "trade_date_iso": "2024-10-09T00:00:00",
                    "quantity": 1,
                    "trade_label": "SOUN 04/17/2025 5.00 C",
                    "trade_type": "C",
                    "price": 0.92,
                    "amount": -92.0,
                    "account": "I",
                    "current_sold_qty": 1,
                    "is_option": True,
                    "is_done": True,
                    "target_price": 5.0,
                    "expiration_date_iso": "2025-04-17T00:00:00",
                    "sells": [
                        {
                            "trade_id": "521",
                            "trade_date": "2025-02-21",
                            "trade_date_iso": "2025-02-21T00:00:00",
                            "trade_label": "SOUN 04/17/2025 5.00 C",
                            "is_option": True,
                            "quantity": 1,
                            "price": 5.5,
                            "amount": 550.0,
                            "target_price": 5.0,
                            "account": "I",
                            "profit_loss": 550.0 - 92.0,
                            "percent_profit_loss": round(
                                ((550.0 - 92.0) / 92.0) * 100, 2
                            ),
                            "expiration_date_iso": "2025-04-17T00:00:00",
                        },
                    ],
                },
                # 462|SOUN|BO|SOUN 07/18/2025 8.00 C|C|2025-02-24|2025-07-18||1.0|3.05|-305.0|8.0|||C
                {
                    "trade_id": "462",
                    "trade_date": "2025-02-24",
                    "trade_date_iso": "2025-02-24T00:00:00",
                    "quantity": 1,
                    "trade_label": "SOUN 07/18/2025 8.00 C",
                    "trade_type": "C",
                    "price": 3.05,
                    "amount": -305.0,
                    "account": "C",
                    "current_sold_qty": 0,
                    "is_option": True,
                    "is_done": False,
                    "target_price": 8.0,
                    "expiration_date_iso": "2025-07-18T00:00:00",
                    "sells": [],
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

        self.check_option_fields = [
            "trade_type",
            "is_option",
            "trade_label",
            "target_price",
            "expiration_date_iso",
        ]

    # @unittest.skip("Skip SOUN")
    def test_analyze_trades_soun(self):
        # Expected:
        symbol = next(iter(self.data_list[5]))
        transactions = self.data_list[5][symbol]
        self.assertEqual(symbol, "SOUN")
        analyzer = TradingAnalyzer(symbol, transactions)
        analyzer.analyze_trades()
        profit_loss_data = analyzer.get_profit_loss_data()
        stock_summary = profit_loss_data["stock"]["summary"]
        has_stock_trades = profit_loss_data["stock"]["has_trades"]
        all_stock_trades = profit_loss_data["stock"]["all_trades"]
        option_summary = profit_loss_data["option"]["summary"]
        all_option_trades = profit_loss_data["option"]["all_trades"]
        has_option_trades = profit_loss_data["option"]["has_trades"]

        # Check stock results for symbol 'SOUN'

        expected_stock_has_trades = False
        # expected_bought_qty = 0
        # expected_bought_amount = 0
        # expected_sold_qty = 0
        # expected_sold_amount = 0
        # expected_closed_bought_amount = 0
        # expected_open_bought_amount = 0

        # expected_profit_loss = expected_sold_amount + expected_closed_bought_amount
        # expected_profit_loss_percent = (
        #     (abs(expected_profit_loss / expected_closed_bought_amount) * 100)
        #     if expected_closed_bought_amount != 0
        #     else 0
        # )

        # Check option results for symbol 'SOUN'
        expected_option_has_trades = True
        expected_option_bought_qty = 5
        expected_option_bought_amount = -540.0 - 92.0 - 305.0

        expected_option_sold_qty = 4
        # $1124.00
        expected_option_sold_amount = 174.0 + 550.0 + 400

        expected_option_closed_bought_amount = -540.0 - 92.0
        expected_option_open_bought_amount = -305.0
        expected_option_open_bought_qty = 1
        expect_option_trade_count = len(self.expect_trades["SOUN"])
        # Bought :
        #  3.0 * 1.08
        #  1.00 * 0.92
        #  1.00 * 3.05  # Not sold
        # Sold :
        # 2.00 * 0.87
        # 1.00 * 0
        # 1.0  * 5.5
        # (1.8 * 3) + 0.92 + 3.05   =  9.47

        # 5.4 + 0.92 + 3.05 = 9.37/5 = 1.894
        expected_option_average_bought_price = -1.874
        # (1.8 * 3) + 0.92  = 6.32/4 = 1.58
        expected_option_average_basis_closed_price = 1.58
        expected_option_average_basis_open_price = 3.05
        # Sold
        # (2 * .87) + 4.0(Strike Price) + 5.5 = 7.24/4 = 1.81
        expected_option_average_sold_price = 2.81

        expected_option_profit_loss = (
            expected_option_sold_amount + expected_option_closed_bought_amount
        )

        expected_option_profit_loss_percent = (
            abs(expected_option_profit_loss / expected_option_closed_bought_amount)
            * 100
        )

        # Stock Checks
        self.assertEqual(
            has_stock_trades,
            expected_stock_has_trades,
            "SOUN should have no stock trades",
        )
        self.assertEqual(stock_summary, {}, "SOUN stock_summary should be empty")

        # self.assertEqual(stock_summary.bought_quantity, expected_bought_qty)
        # self.assertEqual(stock_summary.bought_quantity, expected_bought_qty)

        # self.assertAlmostEqual(
        #     stock_summary.bought_amount, expected_bought_amount, places=2
        # )
        # self.assertEqual(stock_summary.sold_quantity, expected_sold_qty)
        # self.assertAlmostEqual(
        #     stock_summary.sold_amount, expected_sold_amount, places=2
        # )
        # self.assertEqual(
        #     stock_summary.closed_bought_quantity,
        #     expected_sold_qty,
        #     "SOUN closed_bought_quantity",
        # )

        # self.assertAlmostEqual(
        #     stock_summary.closed_bought_amount,
        #     expected_closed_bought_amount,
        #     places=2,
        #     msg="SOUN closed_bought_amount",
        # )

        # self.assertEqual(stock_summary.open_bought_quantity, 0)

        # self.assertAlmostEqual(
        #     stock_summary.open_bought_amount, expected_open_bought_amount, places=2
        # )

        # self.assertAlmostEqual(
        #     stock_summary.profit_loss, expected_profit_loss, places=2
        # )

        # self.assertAlmostEqual(
        #     stock_summary.percent_profit_loss,
        #     expected_profit_loss_percent,
        #     places=2,
        # )

        # Complete Trades
        self.assertEqual(len(all_stock_trades), 0)

        # Option Checks
        self.assertEqual(
            has_option_trades,
            expected_option_has_trades,
            "SOUN should have option trades",
        )

        self.assertEqual(
            option_summary.is_option,
            True,
            msg=f"{symbol} - Option is_option mismatch. Got {option_summary.is_option}, expected True",
        )

        self.assertEqual(
            option_summary.symbol,
            "SOUN",
            msg=f"{symbol} - Option symbol mismatch. Got {option_summary.symbol}, expected 'SOUN'",
        )

        self.assertEqual(
            option_summary.bought_quantity,
            expected_option_bought_qty,
            msg=f"{symbol} - Option bought_quantity mismatch. Got {option_summary.bought_quantity}, expected {expected_option_bought_qty}",
        )

        self.assertAlmostEqual(
            option_summary.bought_amount,
            expected_option_bought_amount,
            places=2,
            msg=f"{symbol} - Option bought amount mismatch. Got {option_summary.bought_amount}, expected {expected_option_bought_amount}",
        )
        self.assertEqual(
            option_summary.sold_quantity,
            expected_option_sold_qty,
            f"{symbol} - Option sold quantity mismatch",
        )
        self.assertAlmostEqual(
            option_summary.sold_amount,
            expected_option_sold_amount,
            places=2,
            msg=f"{symbol} - Option sold amount mismatch. Got {option_summary.sold_amount}, expected {expected_option_sold_amount}",
        )

        # self.assertEqual(
        #     option_summary.closed_bought_quantity,
        #     expected_option_sold_qty,
        #     "SOUN option closed_bought_quantity mismatch",
        # )
        # self.assertEqual(option_summary.sold_quantity, expected_option_sold_qty)

        self.assertEqual(
            option_summary.closed_bought_quantity,
            expected_option_sold_qty,
            "SOUN closed_bought_quantity",
        )

        self.assertAlmostEqual(
            option_summary.closed_bought_amount,
            expected_option_closed_bought_amount,
            places=2,
            msg=f"{symbol} closed_bought_amount expected {expected_option_closed_bought_amount}",
        )

        self.assertEqual(
            option_summary.open_bought_quantity,
            expected_option_open_bought_qty,
            f"{symbol} - Option open_bought_quantity mismatch",
        )

        self.assertAlmostEqual(
            option_summary.open_bought_amount,
            expected_option_open_bought_amount,
            places=2,
            msg=f"{symbol} - Option open_bought_amount mismatch. Got {option_summary.open_bought_amount}, expected {expected_option_open_bought_amount}",
        )

        self.assertAlmostEqual(
            option_summary.profit_loss,
            expected_option_profit_loss,
            places=2,
            msg=f"{symbol} - Option profit_loss mismatch. Got {option_summary.profit_loss}, expected {expected_option_profit_loss}",
        )

        self.assertAlmostEqual(
            option_summary.percent_profit_loss,
            expected_option_profit_loss_percent,
            places=2,
            msg=f"{symbol} - Option percent_profit_loss mismatch. Got {option_summary.percent_profit_loss}, expected {expected_option_profit_loss_percent}",
        )

        # Option price checks
        self.assertAlmostEqual(
            option_summary.average_bought_price,
            expected_option_average_bought_price,
            places=3,
            msg=f"{symbol} - Option average_bought_price mismatch. Got {option_summary.average_bought_price}, expected {expected_option_average_bought_price}",
        )

        self.assertAlmostEqual(
            option_summary.average_basis_sold_price,
            expected_option_average_basis_closed_price,
            places=2,
            msg=f"{symbol} - Option average_basis_sold_price mismatch. Got {option_summary.average_basis_sold_price}, expected {expected_option_average_basis_closed_price}",
        )

        self.assertAlmostEqual(
            option_summary.average_basis_open_price,
            expected_option_average_basis_open_price,
            places=2,
        )

        # Sold
        self.assertAlmostEqual(
            option_summary.average_sold_price,
            expected_option_average_sold_price,
            places=2,
            msg=f"{symbol} - Option average_sold_price mismatch. Got {option_summary.average_sold_price}, expected {expected_option_average_sold_price}",
        )

        # Complete Option Trades for SOUN
        self.assertEqual(
            len(all_option_trades),
            expect_option_trade_count,
            f"{symbol} - Expect {expect_option_trade_count} option trdes for SOUN",
        )

        for i, expected_trade in enumerate(self.expect_trades["SOUN"]):

            got_trade = all_option_trades[i]

            for field in self.check_option_fields:
                self.assertEqual(
                    getattr(got_trade, field),
                    expected_trade[field],
                    f"[{symbol}] {field} - Got {getattr(got_trade,field)} - expected {expected_trade[field]}",
                )

            self.assertEqual(
                got_trade.is_done,
                expected_trade["is_done"],
                f"[{symbol}] - Got {got_trade.is_done} - expected {expected_trade['is_done']}",
            )

            # self.assertEqual(got_trade.is_option, expected_trade["is_option"])
            # self.assertEqual(got_trade.trade_label, expected_trade["trade_label"])
            # self.assertEqual(got_trade.expiration_date_iso, expected_trade["expiration_date_iso"])
            # self.assertEqual(got_trade.target_price, expected_trade["target_price"])
            self.assertEqual(
                got_trade.trade_date,
                expected_trade["trade_date"],
                f"[{symbol}] - trade_date",
            )
            self.assertEqual(
                got_trade.quantity, expected_trade["quantity"], f"[{symbol}] - quantity"
            )
            self.assertEqual(
                got_trade.quantity, expected_trade["quantity"], f"[{symbol}] - quantity"
            )
            self.assertEqual(
                got_trade.current_sold_qty,
                expected_trade["current_sold_qty"],
                f"[{symbol}] - current_sold_qty",
            )

            self.assertEqual(
                len(got_trade.sells),
                len(expected_trade["sells"]),
                f"[{symbol}] - Got {len(got_trade.sells)} sells, expected {len(expected_trade['sells'])} sells",
            )
            # Compare all fields from the Trade dataclass

            # [ "trade_id", "amount", "trade_date", "price", "quantity", "profit_loss", "percent_profit_loss", "account"]
            # [ "trade_type", "is_option", "trade_label","target_price", "expiration_date_iso", "profit_loss", "percent_profit_loss", "account", ]
            for j, expected_sell in enumerate(expected_trade["sells"]):
                got_sell = got_trade.sells[j]
                if got_sell.trade_id != "529":
                    for field in self.check_fields:
                        self.assertEqual(
                            getattr(got_sell, field),
                            expected_sell[field],
                            f"[SOUN] Got field {field} doesnt match: {expected_sell[field]}",
                        )
                else:
                    # This trade was modified because it was exercised
                    self.assertEqual(got_sell.trade_id, "529", f"{symbol} - trade_id")
                    self.assertEqual(
                        got_sell.trade_date_iso,
                        "2024-09-19T00:00:00",
                        f"{symbol} - trade_date_iso",
                    )
                    self.assertEqual(
                        got_sell.trade_date, "2024-09-19", f"{symbol} - trade_date"
                    )
                    self.assertEqual(got_sell.price, 4.0, f"{symbol} - price")
                    self.assertEqual(
                        got_sell.expiration_date_iso,
                        "2024-09-20T00:00:00",
                        f"[SOUN] Got expiration_date_iso, {got_sell.expiration_date_iso}, doesnt match: 2024-09-20T00:00:00",
                    )

                if got_sell.trade_id != "529":
                    self.assertAlmostEqual(
                        got_sell.profit_loss,
                        expected_sell["profit_loss"],
                        places=2,
                        msg=f'SOUN - Got profit/loss: {got_sell.profit_loss}, expected profit/loss={expected_sell["profit_loss"]}',
                    )
                    self.assertAlmostEqual(
                        got_sell.percent_profit_loss,
                        expected_sell["percent_profit_loss"],
                        places=2,
                        msg=f'SOUN - Got % profit/loss: {got_sell.percent_profit_loss}, expected % profit/loss={expected_sell["percent_profit_loss"]}',
                    )
                else:
                    # This trade was modified because it was exercised
                    self.assertAlmostEqual(
                        got_sell.profit_loss,
                        400 - 180.00,
                        msg=f"SOUN EXE trade - Got profit/loss: {got_sell.profit_loss}, expected profit/loss={400 -180.00}",
                    )
                    self.assertAlmostEqual(
                        got_sell.percent_profit_loss,
                        ((400.0 - 180.0) / 180.0) * 100,
                        places=2,
                        msg=f"SOUN - Got % profit/loss: {got_sell.percent_profit_loss}, expected % profit/loss={((400.0 - 180.0) /180360.0) * 100}",
                    )

    # end_soun

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

        self.assertEqual(stock_summary.bought_quantity, 275.0, f"{symbol} - bought_quantity")

        self.assertAlmostEqual(stock_summary.bought_amount, -25416.07, places=2, msg=f"{symbol} - bought_amount")

        self.assertEqual(stock_summary.sold_quantity, 235.0, f"{symbol} - sold_quantity")

        self.assertAlmostEqual(stock_summary.sold_amount, 20759.77 + 969.9, places=2, msg=f"{symbol} - sold_amount")
        self.assertEqual(
            stock_summary.closed_bought_quantity, 235.0, f"{symbol} closed_bought_quantity"
        )
        self.assertAlmostEqual(
            stock_summary.closed_bought_amount,
            expected_closed_bought_amount,
            places=2,
            msg=f"{symbol} closed_bought_amount expected {expected_closed_bought_amount}",
        )

        self.assertEqual(stock_summary.open_bought_quantity, 40.0)

        self.assertAlmostEqual(
            stock_summary.open_bought_amount, expected_open_bought_amount, places=2
        )
        self.assertAlmostEqual(
            stock_summary.profit_loss, expected_profit_loss, places=2
        )
        self.assertAlmostEqual(
            stock_summary.percent_profit_loss, expected_profit_loss_percent, places=2
        )

        # Complete Trades
        self.assertEqual(len(all_trades), 5, f"{symbol} - all_trades count - expected 5")

        for i, expected_trade in enumerate(self.expect_trades["SN"]):
            got_trade = all_trades[i]
            # Compare all fields from the Trade dataclass
            self.assertEqual(got_trade.trade_date, expected_trade["trade_date"])
            self.assertEqual(
                got_trade.quantity, expected_trade["quantity"], "SN - quantity"
            )
            self.assertEqual(got_trade.price, expected_trade["price"])
            self.assertEqual(got_trade.amount, expected_trade["amount"])
            self.assertEqual(
                got_trade.current_sold_qty, expected_trade["current_sold_qty"]
            )

            self.assertEqual(len(got_trade.sells), len(expected_trade["sells"]))

            # Verify all fields in sells match
            for j, expected_sell in enumerate(expected_trade["sells"]):
                got_sell = got_trade.sells[j]
                # Compare all fields from the Sell dataclass
                self.assertEqual(got_sell.trade_date, expected_sell["trade_date"], f"{symbol} - Sell trade_date expected {expected_sell['trade_date']}")
                self.assertEqual(got_sell.quantity, expected_sell["quantity"], f"{symbol} -Sell  quantity expected {expected_sell['quantity']}")
                self.assertEqual(got_sell.trade_date_iso, expected_sell["trade_date_iso"], f"{symbol} - Sell trade_date_iso expected {expected_sell['trade_date_iso']}")
                self.assertEqual(got_sell.price, expected_sell["price"], f"{symbol} - Sell price expected {expected_sell['price']}")
                # self.assertEqual(got_sell.trade_id, expected_sell["trade_id"], f"{symbol} - Sell trade_id expected {expected_sell['trade_id']}")
                # self.assertEqual(got_sell.trade_label, expected_sell["trade_label"], f"{symbol} - Sell trade_label expected {expected_sell['trade_label']}")
                # self.assertEqual(got_sell.amount, expected_sell["amount"])
                # self.assertEqual(got_sell.current_sold_qty, expected_sell["current_sold_qty"])
                self.assertAlmostEqual(
                    got_sell.profit_loss, expected_sell["profit_loss"], places=2
                )
                self.assertAlmostEqual(
                    got_sell.percent_profit_loss,
                    expected_sell["percent_profit_loss"],
                    places=2,
                )
                self.assertEqual(got_sell.account, expected_sell["account"])

    # @unittest.skip("Skip NVDA")
    def test_analyze_trades_nvda(self):

        symbol = next(iter(self.data_list[1]))
        transactions = self.data_list[1][symbol]
        self.assertEqual(symbol, "NVDA")
        analyzer = TradingAnalyzer(symbol, transactions)
        analyzer.analyze_trades()
        profit_loss_data = analyzer.get_profit_loss_data()
        stock_summary = profit_loss_data["stock"]["summary"]
        print(f"NVDA profit_loss_data: {profit_loss_data}")
        all_trades = profit_loss_data["stock"]["all_trades"]

        # Check results for symbol 'NVDA'
        self.assertEqual(stock_summary.bought_quantity, 200.0)
        self.assertAlmostEqual(stock_summary.bought_amount, -60000.0, places=2)
        self.assertEqual(
            stock_summary.sold_quantity, 200.0, f"{symbol} - sold_quantity"
        )
        self.assertAlmostEqual(stock_summary.sold_amount, 62250.0, places=2)
        self.assertEqual(
            stock_summary.closed_bought_quantity,
            200.0,
            f"{symbol} - closed_bought_quantity",
        )
        self.assertAlmostEqual(
            stock_summary.closed_bought_amount,
            -60000.0,
            places=2,
            msg=f"{symbol} closed_bought_amount expected {-60000.0}",
        )
        self.assertEqual(
            stock_summary.open_bought_quantity, 0, f"{symbol} - open_bought_quantity"
        )
        self.assertAlmostEqual(
            stock_summary.open_bought_amount,
            0,
            places=2,
            msg=f"{symbol} - open_bought_amount",
        )

        self.assertAlmostEqual(
            stock_summary.profit_loss, 2250.0, places=2, msg=f"{symbol} - profit_loss"
        )
        self.assertAlmostEqual(
            stock_summary.percent_profit_loss,
            3.75,
            places=2,
            msg=f"{symbol} - percent_profit_loss",
        )
        # Check if the stock summary is correct
        # Complete Trades
        self.assertEqual(len(all_trades), 1, f"{symbol} - all_trades count")

        for i, expected_trade in enumerate(self.expect_trades["NVDA"]):
            got_trade = all_trades[i]
            # Verify each field in the got_trade matches the expected_trade
            self.assertEqual(
                got_trade.trade_date,
                expected_trade["trade_date"],
                f"{symbol} - trade_date",
            )
            self.assertEqual(got_trade.quantity, expected_trade["quantity"])
            self.assertEqual(got_trade.amount, expected_trade["amount"])
            self.assertEqual(
                got_trade.current_sold_qty,
                expected_trade["current_sold_qty"],
                msg=f"NVDA - current_sold_qty mismatch: got {got_trade.current_sold_qty}, expected {expected_trade['current_sold_qty']}",
            )
            self.assertEqual(len(got_trade.sells), len(expected_trade["sells"]))
            for j, expected_sell in enumerate(expected_trade["sells"]):
                got_sell = got_trade.sells[j]
                self.assertEqual(got_sell.trade_date, expected_sell["trade_date"])
                self.assertEqual(got_sell.quantity, expected_sell["quantity"])
                self.assertEqual(got_sell.amount, expected_sell["amount"])
                self.assertEqual(got_sell.price, expected_sell["price"])
                self.assertAlmostEqual(
                    got_sell.profit_loss, expected_sell["profit_loss"], places=2
                )
                self.assertAlmostEqual(
                    got_sell.percent_profit_loss,
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
        self.assertEqual(stock_summary.bought_quantity, 150.0)
        self.assertAlmostEqual(stock_summary.bought_amount, -7537.5, places=2)
        self.assertEqual(
            stock_summary.sold_quantity, 150.0, f"{symbol} - sold_quantity"
        )
        self.assertAlmostEqual(
            stock_summary.sold_amount,
            4720.0 + 2163.01,
            places=2,
            msg=f"{symbol} - sold_amount",
        )

        self.assertEqual(
            stock_summary.closed_bought_quantity,
            150.0,
            f"{symbol} - closed_bought_quantity",
        )

        self.assertEqual(
            stock_summary.open_bought_quantity, 0.0, f"{symbol} open_bought_quantity"
        )
        self.assertAlmostEqual(
            stock_summary.open_bought_amount,
            0,
            places=2,
            msg=f"{symbol} open_bought_amount expected 0",
        )

        self.assertAlmostEqual(
            stock_summary.profit_loss, -7537.5 + 4720.0 + 2163.01, places=2
        )
        self.assertAlmostEqual(stock_summary.percent_profit_loss, -8.68, places=2)
        # Complete Trades
        self.assertEqual(len(all_trades), 1, f"{symbol} - all_trades count - expected 1")

        for i, expected_trade in enumerate(self.expect_trades["TNA"]):
            got_trade = all_trades[i]

            self.assertEqual(
                got_trade.trade_date,
                expected_trade["trade_date"],
                msg=f"[{symbol}] - trade_date mismatch: got {got_trade.trade_date}, expected {expected_trade['trade_date']}",
            )
            self.assertEqual(
                got_trade.quantity,
                expected_trade["quantity"],
                msg=f"[{symbol}] - quantity mismatch: got {got_trade.quantity}, expected {expected_trade['quantity']}",
            )
            self.assertEqual(
                got_trade.amount,
                expected_trade["amount"],
                msg=f"[{symbol}] - amount mismatch: got {got_trade.amount}, expected {expected_trade['amount']}",
            )
            self.assertEqual(
                got_trade.current_sold_qty,
                expected_trade["current_sold_qty"],
                msg=f"[{symbol}] - current_sold_qty mismatch: got {got_trade.current_sold_qty}, expected {expected_trade['current_sold_qty']}",
            )
            self.assertEqual(
                len(got_trade.sells),
                len(expected_trade["sells"]),
                msg=f"[{symbol}] - sells count mismatch: got {len(got_trade.sells)}, expected {len(expected_trade['sells'])}",
            )

            for j, expected_sell in enumerate(expected_trade["sells"]):
                got_sell = got_trade.sells[j]
                self.assertEqual(
                    got_sell.trade_date,
                    expected_sell["trade_date"],
                    msg=f"[{symbol}] - Got sell trade_date {got_sell.trade_date} doesn't match expected {expected_sell['trade_date']}",
                )
                self.assertEqual(
                    got_sell.quantity,
                    expected_sell["quantity"],
                    msg=f"[{symbol}] - Got sell quantity {got_sell.quantity} doesn't match expected {expected_sell['quantity']}",
                )
                self.assertEqual(
                    got_sell.price,
                    expected_sell["price"],
                    msg=f"[{symbol}] - Got sell price {got_sell.price} doesn't match expected {expected_sell['price']}",
                )

                self.assertAlmostEqual(
                    got_sell.amount,
                    expected_sell["amount"],
                    places=2,
                    msg=f"TNA - Got amount: {got_sell.amount}, expected {expected_sell['amount']}",
                )

                self.assertAlmostEqual(
                    got_sell.profit_loss,
                    expected_sell["profit_loss"],
                    places=1,
                    msg=f"TNA - Got profit_loss: {got_sell.profit_loss}, expected {expected_sell['profit_loss']}",
                )
                self.assertAlmostEqual(
                    got_sell.percent_profit_loss,
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

        self.assertEqual(
            stock_summary.bought_quantity,
            expected_bought_qty,
            f"{symbol} - bought_quantity",
        )

        self.assertAlmostEqual(
            stock_summary.bought_amount,
            expected_bought_amount,
            places=2,
            msg=f"{symbol} - bought_amount",
        )

        self.assertEqual(
            stock_summary.sold_quantity, expected_sold_qty, f"{symbol} - sold_quantity expected {expected_sold_qty}"
        )

        self.assertAlmostEqual(
            stock_summary.sold_amount,
            expected_sold_amount,
            places=2,
            msg=f"{symbol} - sold_amount",
        )
        self.assertEqual(
            stock_summary.closed_bought_quantity,
            expected_sold_qty,
            f"{symbol} closed_bought_quantity",
        )

        self.assertAlmostEqual(
            stock_summary.closed_bought_amount,
            expected_closed_bought_amount,
            places=2,
            msg=f"{symbol} closed_bought_amount expected {expected_closed_bought_amount}",
        )

        self.assertEqual(stock_summary.open_bought_quantity, 40.0)

        self.assertAlmostEqual(
            stock_summary.open_bought_amount, expected_open_bought_amount, places=2
        )
        self.assertAlmostEqual(
            stock_summary.profit_loss, expected_profit_loss, places=2
        )
        self.assertAlmostEqual(
            stock_summary.percent_profit_loss,
            expected_profit_loss_percent,
            places=2,
        )

        # Complete Trades
        self.assertEqual(len(all_trades), 6, f"{symbol} - all_trades count expected 6")

        for i, expected_trade in enumerate(self.expect_trades["NAIL"]):
            got_trade = all_trades[i]
            self.assertEqual(got_trade.trade_date, expected_trade["trade_date"])
            self.assertEqual(got_trade.quantity, expected_trade["quantity"], f"{symbol} - expected {expected_trade['quantity']}")
            self.assertEqual(
                got_trade.amount,
                expected_trade["amount"],
                msg=f"{symbol} - Got amount {got_trade.amount}, expected {expected_trade['amount']}",
            )
            self.assertEqual(
                got_trade.current_sold_qty,
                expected_trade["current_sold_qty"],
                msg=f"{symbol} - Got current_sold_qty {got_trade.current_sold_qty}, expected {expected_trade['current_sold_qty']}",
            )
            self.assertEqual(
                len(got_trade.sells),
                len(expected_trade["sells"]),
                msg=f"{symbol} - Got sells count {len(got_trade.sells)} doesn't match expected {len(expected_trade['sells'])}",
            )

            for j, expected_sell in enumerate(expected_trade["sells"]):
                got_sell = got_trade.sells[j]
                self.assertEqual(got_sell.trade_date, expected_sell["trade_date"])
                self.assertEqual(got_sell.quantity, expected_sell["quantity"])
                self.assertEqual(got_sell.amount, expected_sell["amount"])
                self.assertEqual(got_sell.price, expected_sell["price"])

                self.assertAlmostEqual(
                    got_sell.profit_loss, expected_sell["profit_loss"], places=2
                )
                self.assertAlmostEqual(
                    got_sell.percent_profit_loss,
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

        self.assertEqual(
            stock_summary.bought_quantity,
            expected_bought_qty,
            f"{symbol} - bought_quantity",
        )

        self.assertAlmostEqual(
            stock_summary.bought_amount,
            expected_bought_amount,
            places=2,
            msg=f"{symbol} - bought_amount",
        )

        self.assertEqual(
            stock_summary.sold_quantity, expected_sold_qty, f"{symbol} - sold_quantity - expected {expected_sold_qty}"
        )
        # 5590.5 + 2952.0

        self.assertAlmostEqual(
            stock_summary.sold_amount,
            expected_sold_amount,
            places=2,
            msg=f"{symbol} - sold_amount expected {expected_sold_amount}",
        )
        self.assertEqual(
            stock_summary.closed_bought_quantity,
            expected_sold_qty,
            f"{symbol} closed_bought_quantity expected {expected_sold_qty} expected {expected_sold_qty}",
        )

        self.assertAlmostEqual(
            stock_summary.closed_bought_amount,
            expected_closed_bought_amount,
            places=2,
            msg=f"{symbol} closed_bought_amount {expected_closed_bought_amount} expected {expected_closed_bought_amount}",
        )

        self.assertEqual(
            stock_summary.open_bought_quantity,
            800.0,
            f"{symbol} - open_bought_quantity expected 800.0",
        )

        self.assertAlmostEqual(
            stock_summary.open_bought_amount,
            expected_open_bought_amount,
            places=2,
            msg=f"{symbol} - open_bought_amount expected {expected_open_bought_amount}",
        )
        self.assertAlmostEqual(
            stock_summary.profit_loss,
            expected_profit_loss,
            places=2,
            msg=f"{symbol} - profit_loss expected {expected_profit_loss}",
        )
        self.assertAlmostEqual(
            stock_summary.percent_profit_loss,
            expected_profit_loss_percent,
            places=2,
            msg=f"{symbol} - percent_profit_loss expected {expected_profit_loss_percent}",
        )

        # Complete Trades
        self.assertEqual(len(all_trades), 5, f"{symbol} - all_trades count expected 5")

        for i, expected_trade in enumerate(self.expect_trades["NIO"]):
            got_trade = all_trades[i]
            self.assertEqual(got_trade.trade_date, expected_trade["trade_date"], f"{symbol} - ID {got_trade.trade_id} - Got trade_date {got_trade.trade_date} doesn't match expected {expected_trade['trade_date']}")
            self.assertEqual(got_trade.quantity, expected_trade["quantity"], f"{symbol} - ID {got_trade.trade_id} - Got quantity {got_trade.quantity} doesn't match expected {expected_trade['quantity']}")
            self.assertEqual(got_trade.amount, expected_trade["amount"], f"{symbol} - ID {got_trade.trade_id} - Got amount {got_trade.amount} doesn't match expected {expected_trade['amount']}")
            self.assertEqual(
                got_trade.current_sold_qty,
                expected_trade["current_sold_qty"],
                msg=f"NIO -  ID {got_trade.trade_id} - Got current_sold_qty {got_trade.current_sold_qty} doesn't match expected {expected_trade['current_sold_qty']}",
            )
            self.assertEqual(len(got_trade.sells), len(expected_trade["sells"]))

            for j, expected_sell in enumerate(expected_trade["sells"]):
                got_sell = got_trade.sells[j]
                self.assertEqual(got_sell.trade_date, expected_sell["trade_date"], f"{symbol} - ID {got_sell.trade_id} - Got sell.trade_date {got_sell.trade_date} != expected {expected_sell['trade_date']}")
                self.assertEqual(got_sell.quantity, expected_sell["quantity"], f"{symbol} - ID {got_sell.trade_id} - Got sell.quantity {got_sell.quantity} != expected {expected_sell['quantity']}")
                self.assertEqual(got_sell.amount, expected_sell["amount"], f"{symbol} - ID {got_sell.trade_id} - Got sell.amount {got_sell.amount} != expected {expected_sell['amount']}")
                self.assertEqual(got_sell.price, expected_sell["price"], f"{symbol} - ID {got_sell.trade_id} - Got sell.price {got_sell.price} != expected {expected_sell['price']}")

                self.assertAlmostEqual(
                    got_sell.profit_loss,
                    expected_sell["profit_loss"],
                    places=2,
                    msg=f"{symbol} - ID {got_sell.trade_id} - profit_loss expected {expected_sell['profit_loss']}",  
                )

                self.assertAlmostEqual(
                    got_sell.percent_profit_loss,
                    expected_sell["percent_profit_loss"],
                    places=2,
                    msg=f"{symbol} - percent_profit_loss expected {expected_sell['percent_profit_loss']}",
                )

    @unittest.skip(
        "Skip testing get_open_trades SN until we integrate with the new code"
    )
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

        # self.assertEqual(len(open_trades), len(expected_open_trades))
        self.assertEqual(
            len(open_trades),
            len(expected_open_trades),
            msg=f"[{symbol}] Got {len(open_trades)} open trades. Expected {len(expected_open_trades)} open trades",
        )
        for i, expected_trade in enumerate(expected_open_trades):
            got_trade = open_trades[i]
            self.assertEqual(got_trade.trade_date, expected_trade["trade_date"])
            self.assertEqual(got_trade.quantity, expected_trade["quantity"])
            self.assertEqual(got_trade.price, expected_trade["price"])
            self.assertEqual(got_trade.amount, expected_trade["amount"])
            self.assertEqual(
                got_trade.current_sold_qty, expected_trade["current_sold_qty"]
            )

            self.assertEqual(len(got_trade.sells), len(expected_trade["sells"]))
            for j, expected_sell in enumerate(expected_trade["sells"]):
                got_sell = got_trade.sells[j]
                for field in self.check_fields:
                    self.assertEqual(
                        getattr(got_sell, field),
                        expected_sell[field],
                        f"[SN] Field {field} does not match",
                    )
            self.assertEqual(got_trade.is_done, expected_trade["is_done"])

    @unittest.skip(
        "Skip testing get_open_trades NVDA until we integrate with the new code"
    )
    def test_get_open_trades_nvda(self):
        analyzer = TradingAnalyzer("NVDA", self.data_list[1]["NVDA"])
        analyzer.analyze_trades()
        profit_loss_data = analyzer.get_open_trades()
        open_trades = profit_loss_data["stock"]["all_trades"]
        expected_open_trades = []
        self.assertEqual(len(open_trades), len(expected_open_trades))

    @unittest.skip(
        "Skip testing get_open_trades TNA until we integrate with the new code"
    )
    def test_get_open_trades_tna(self):
        analyzer = TradingAnalyzer("TNA", self.data_list[2]["TNA"])
        analyzer.analyze_trades()
        profit_loss_data = analyzer.get_open_trades()
        open_trades = profit_loss_data["stock"]["all_trades"]
        expected_open_trades = []
        self.assertEqual(len(open_trades), len(expected_open_trades))

    @unittest.skip(
        "Skip testing get_open_trades NAIL until we integrate with the new code"
    )
    def test_get_open_trades_nail(self):
        symbol = "NAIL"
        analyzer = TradingAnalyzer(symbol, self.data_list[3][symbol])
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

        self.assertEqual(
            len(open_trades),
            len(expected_open_trades),
            msg=f"[{symbol}] Got {len(open_trades)} open trades. Expected {len(expected_open_trades)} open trades",
        )

        for i, expected_trade in enumerate(expected_open_trades):
            got_trade = open_trades[i]
            self.assertEqual(got_trade.trade_date, expected_trade["trade_date"])
            self.assertEqual(got_trade.quantity, expected_trade["quantity"])
            self.assertEqual(got_trade.price, expected_trade["price"])
            self.assertEqual(got_trade.amount, expected_trade["amount"])
            self.assertEqual(
                got_trade.current_sold_qty, expected_trade["current_sold_qty"]
            )

            # self.assertEqual(got_trade.sells, expected_trade["sells"])

            # Avoid duplicate loop
            for j, expected_sell in enumerate(expected_trade["sells"]):
                got_sell = got_trade.sells[j]
                for field in self.check_fields:
                    self.assertEqual(
                        getattr(got_sell, field),
                        expected_sell[field],
                        f"[{symbol}] Field {field} does not match {expected_sell[field]}",
                    )

    @unittest.skip(
        "Skip testing get_open_trades NIO until we integrate with the new code"
    )
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
                # "id": "507",
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
                # "id": "504",
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

        # self.assertEqual(len(open_trades), len(expected_open_trades))
        self.assertEqual(
            len(open_trades),
            len(expected_open_trades),
            msg=f"[{symbol}] Got {len(open_trades)} open trades. Expected {len(expected_open_trades)} open trades",
        )

        for i, expected_trade in enumerate(expected_open_trades):
            got_trade = open_trades[i]

            self.assertEqual(got_trade.trade_date, expected_trade["trade_date"])
            self.assertEqual(got_trade.quantity, expected_trade["quantity"])
            self.assertEqual(got_trade.price, expected_trade["price"])
            self.assertEqual(got_trade.amount, expected_trade["amount"])
            self.assertEqual(
                got_trade.current_sold_qty, expected_trade["current_sold_qty"]
            )

            # self.assertEqual(got_trade["sells"], expected_trade["sells"])
            for j, expected_sell in enumerate(expected_trade["sells"]):
                got_sell = got_trade.sells[j]
                for field in self.check_fields:
                    self.assertEqual(
                        getattr(got_sell, field),
                        expected_sell[field],
                        f"[NIO] Field {field} does not match",
                    )
            self.assertEqual(got_trade.is_done, expected_trade["is_done"])

    def test_invalid_trade_data(self):
        """Test that invalid trade data raises an error."""
        invalid_trade = {
            "id": "0001",
            "symbol": "ERR",
            "action": "B",
            "quantity": -100,
            "price": 50.0,
            "trade_date": "2024-01-01",
        }
        with self.assertRaises(ValueError):
            analyzer = TradingAnalyzer("ERR", [invalid_trade])
            analyzer.analyze_trades()


if __name__ == "__main__":
    unittest.main()
