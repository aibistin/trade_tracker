import re

from lib.ignore_symbols import get_ignored_symbols

SYMBOLS_TO_EXCLUDE = [
    "",
    "14067D508",
    "14067D607",
    "873379101",
    "BMY/R",
    "G06242104",
    "MMDA1",
]

# Matches the option-contract part of a symbol, e.g. "CORZ 09/20/2024 9.00 C"
OPTION_LABEL_RE = re.compile(r"\s+\d{2}/\d{2}/\d{4}\s+\d+\.\d+\s+[A-Z]")


def is_option_symbol(symbol):
    """True if the symbol string is an option label rather than a plain ticker."""
    return bool(OPTION_LABEL_RE.search(symbol))


def filter_symbols(all_symbol_names):
    ignored = get_ignored_symbols()
    return [
        (symbol, name)
        for symbol, name in all_symbol_names
        if symbol
        and len(symbol) < 6
        and not is_option_symbol(symbol)
        and symbol not in SYMBOLS_TO_EXCLUDE
        and symbol.upper() not in ignored
    ]
