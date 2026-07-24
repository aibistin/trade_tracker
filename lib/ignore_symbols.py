import os

IGNORE_SYMBOLS_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'config', 'ignore_symbols.txt')
)


def get_ignored_symbols(path=IGNORE_SYMBOLS_PATH):
    """
    Symbols to exclude from every trade data query, one per line in
    config/ignore_symbols.txt. Blank lines and lines starting with '#' are
    skipped. Read fresh on every call (the file is tiny and rarely changes)
    so edits take effect without an app restart. Returns an empty set if the
    file doesn't exist.
    """
    if not os.path.exists(path):
        return set()
    with open(path) as f:
        return {
            line.strip().upper() for line in f
            if line.strip() and not line.strip().startswith('#')
        }
