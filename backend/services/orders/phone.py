"""Conservative phone formatting, without guessing a country or verifying ownership."""

import re


def normalize_phone(value: str | None) -> str:
    """Accept 7–15 ASCII digits, an optional +/00 prefix and common visual separators.

    National numbers remain national: the delivery site's country is not evidence of
    the customer's dialling code. This checks syntax only, not reachability.
    """
    raw = (value or "").strip()
    if not raw or len(raw) > 64 or not re.fullmatch(r"\+?[0-9\s().-]+", raw):
        raise ValueError("Enter a customer phone number with 7–15 digits and an optional country code")
    compact = re.sub(r"[\s().-]", "", raw)
    if compact.startswith("00"):
        compact = "+" + compact[2:]
    digits = compact.removeprefix("+")
    if not re.fullmatch(r"[0-9]{7,15}", digits) or (compact.startswith("+") and digits.startswith("0")):
        raise ValueError("Enter a customer phone number with 7–15 digits and an optional country code")
    return compact
