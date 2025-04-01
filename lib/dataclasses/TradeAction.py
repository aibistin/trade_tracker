from enum import Enum
#TODO Merge this dataclass with ActionType.py

class TradeAction(Enum):
    """Enum representing different trade actions."""
    BUY = "B"
    SELL = "S"
    REINVEST_SHARES = "RS"
    SELL_CLOSE = "SC"
    BUY_OPEN = "BO"

from enum import Enum

class TradeAction(Enum):
    """Enum representing different trade actions."""
    BANK_INTEREST = "BI"
    BOND_INTEREST = "BOI"
    BUY = "B"
    BUY_TO_CLOSE = "BC"
    BUY_TO_OPEN = "BO"
    CASH_DIVIDEND = "CD"
    CASH_MERGER = "CM"
    CASH_MERGER_ADJ = "CMJ"
    EXCHANGE_OR_EXERCISE = "EE"
    EXPIRED = "EXP"
    FUNDS_RECEIVED = "FR"
    INTERNAL_TRANSFER = "IT"
    JOURNAL = "J"
    JOURNALED_SHARES = "JS"
    MANDATORY_REORG_EXC = "MRE",
    MONEYLINK_TRANSFER = "MT"
    PR_YR_DIV_REINVEST = "PYDR"
    QUAL_DIV_REINVEST = "QDR"
    QUALIFIED_DIVIDEND = "QD"
    REINVEST_SHARES = "RS"
    REINVEST_DIVIDEND = "RD"
    REVERSE_SPLIT = "RSP"
    SELL = "S"
    SELL_TO_CLOSE = "SC"
    SELL_TO_OPEN = "SO"
    STOCK_SPLIT = "SSP"
    TAX_WITHHOLDING = "TXW"
    UNKNOWN = "UK"  # For any action not in the list

