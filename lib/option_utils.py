"""Utilities for converting between option ticker formats."""
from datetime import datetime


def label_to_occ(label: str) -> str:
    """Convert a Schwab option label string to OCC format.

    Args:
        label: Schwab format, e.g. "UUUU 04/17/2026 23.00 C"

    Returns:
        OCC format, e.g. "UUUU260417C00023000"

    Raises:
        ValueError: If the label cannot be parsed.
    """
    parts = label.strip().split()
    if len(parts) != 4:
        raise ValueError(
            f"Expected 4 parts in option label, got {len(parts)}: {label!r}"
        )

    ticker, date_str, strike_str, option_type = parts

    if option_type not in ("C", "P"):
        raise ValueError(f"Invalid option type {option_type!r} in label: {label!r}")

    try:
        date = datetime.strptime(date_str, "%m/%d/%Y")
    except ValueError:
        raise ValueError(f"Cannot parse date {date_str!r} in label: {label!r}")

    try:
        strike = int(round(float(strike_str) * 1000))
    except ValueError:
        raise ValueError(f"Cannot parse strike {strike_str!r} in label: {label!r}")

    return f"{ticker}{date.strftime('%y%m%d')}{option_type}{strike:08d}"
