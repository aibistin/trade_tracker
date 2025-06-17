SYMBOLS_TO_EXCLUDE = [
    "",
    "14067D508",
    "14067D607",
    "873379101",
    "BMY/R",
    "CGRN",
    "G06242104",
    "MMDA1",
]

def filter_symbols(all_symbol_names):
    import re
    return [
        (symbol, name)
        for symbol, name in all_symbol_names
        if symbol
        and len(symbol) < 6
        and not re.search(r"\s+\d{2}/\d{2}/\d{4}\s+\d+\.\d+\s+[A-Z]", symbol)
        and symbol not in SYMBOLS_TO_EXCLUDE
    ]
