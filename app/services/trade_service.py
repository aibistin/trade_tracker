# app/services/trade_service.py

REASON_MAX_LEN = 500


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
