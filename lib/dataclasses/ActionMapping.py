from dataclasses import dataclass
from typing import Dict


@dataclass
class ActionMapping:
    """Dataclass for storing and managing trade action mappings"""

    action_map: Dict[str, str] = None

    def __init__(self):
        self.action_map = {
            "Bank Interest": "BI",
            "Bond Interest": "BOI",
            "Buy": "B",
            "Buy to Close": "BC",
            "Buy to Open": "BO",
            "Cash Dividend": "CD",
            "Cash Merger": "CM",
            "Cash Merger Adj": "CMJ",
            "Exchange or Exercise": "EE",
            "Expired": "EXP",
            "Funds Received": "FR",
            "Internal Transfer": "IT",
            "Journal": "J",
            "Journaled Shares": "JS",
            "Mandatory Reorg Exc": "MRE",
            "MoneyLink Transfer": "MT",
            "Pr Yr Div Reinvest": "PYDR",
            "Qual Div Reinvest": "QDR",
            "Qualified Dividend": "QD",
            "Reinvest Shares": "RS",
            "Reinvest Dividend": "RD",
            "Reverse Split": "RSP",
            "Sell": "S",
            "Sell to Close": "SC",
            "Sell to Open": "SO",
            "Stock Split": "SSP",
            "Tax Withholding": "TXW",
        }
        # Create reverse mapping for potential future use
        self.reverse_map = {v: k for k, v in self.action_map.items()}

    def get_acronym(self, full_name: str) -> str:
        """Get action acronym from full name"""
        return self.action_map.get(full_name, None)


    def is_buy_type_action(self, acronym: str) -> str:
        """Check if the acronym is a buy type action (Buy, Buy to Open, Sell to Open)"""
        return acronym in {"B", "BO", "RS", "RD", "PYDR", "QDR", "SO"}


    def is_sell_type_action(self, acronym: str) -> str:
        """Check if the acronym is a sell type action (Sell, Buy to Close , Sell to Close)"""
        return acronym in {"S", "BC", "SC"}


    def get_full_name(self, acronym: str) -> str:
        """Get full action name from acronym or None"""
        return self.reverse_map.get(acronym, None)
