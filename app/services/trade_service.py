# app/services/trade_service.py
from datetime import datetime

REASON_MAX_LEN = 500

VALID_SCOPES = ["all", "open", "closed"]
VALID_ACCOUNTS = ["C", "R", "I", "O"]
VALID_ASSET_TYPES = ["stock", "option", "all"]


def validate_positions_params(scope, after_date=None, account=None, asset_type="all"):
    """
    Validates the common request parameters for position/trade endpoints.
    Returns an error message string for the first invalid parameter, or None.
    """
    if scope not in VALID_SCOPES:
        return 'Invalid scope. Must be either "all", "open" or "closed"'

    if asset_type not in VALID_ASSET_TYPES:
        return f"asset_type must be one of {VALID_ASSET_TYPES}"

    if after_date is not None:
        try:
            datetime.strptime(after_date, "%Y-%m-%d")
        except (ValueError, TypeError):
            return "after_date must be in 'YYYY-MM-DD' format"

    if account is not None and account not in VALID_ACCOUNTS:
        return f"account must be one of {VALID_ACCOUNTS}"

    return None


def validate_trade_update(data: dict) -> dict:
    """
    Validates user-editable trade fields.
    Args:
        data: dict with any subset of {reason, initial_stop_price, projected_sell_price}
    Returns:
        dict of field -> error message (empty if all valid)
    """
    errors = {}

    if "reason" in data:
        reason = data["reason"]
        if reason is not None:
            if not isinstance(reason, str):
                errors["reason"] = "Must be a string"
            elif len(reason) > REASON_MAX_LEN:
                errors["reason"] = f"Must be {REASON_MAX_LEN} characters or fewer"

    for price_field in ("initial_stop_price", "projected_sell_price"):
        if price_field in data:
            val = data[price_field]
            if val is not None:
                try:
                    if float(val) <= 0:
                        errors[price_field] = "Must be a positive number"
                except (TypeError, ValueError):
                    errors[price_field] = "Must be a positive number"

    return errors
