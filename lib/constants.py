from enum import Enum


class Action(str, Enum):
    """Action codes for trade transactions.

    Using str mixin so members compare equal to their string values,
    allowing them to be used anywhere a plain string action code is expected.
    """
    BUY = "B"
    BUY_TO_OPEN = "BO"
    BUY_TO_CLOSE = "BC"
    SELL = "S"
    SELL_TO_CLOSE = "SC"
    SELL_TO_OPEN = "SO"
    EXPIRED = "EXP"
    EXERCISED = "EE"
    REINVEST_SHARES = "RS"
    REINVEST_DIVIDEND = "RD"
    PRIOR_YR_DIV_REINVEST = "PYDR"
    QUAL_DIV_REINVEST = "QDR"


# Quantity multipliers
OPTIONS_MULTIPLIER = 100
STOCK_MULTIPLIER = 1
