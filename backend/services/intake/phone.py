"""Shared, deterministic extraction of phone metadata from spreadsheet columns."""

from backend.services.orders.phone import normalize_phone

PHONE_KEYS = {"phone", "telephone", "tel", "telefon", "mobil", "mobile", "tlf", "customer phone", "phone number", "telefonnummer"}


def phone_from_columns(headers: list[str], rows: list[list]) -> tuple[bool, str | None]:
    """Read a phone metadata column, rejecting conflicting values instead of picking a row."""
    indexes = [i for i, h in enumerate(headers) if h.strip().lower() in PHONE_KEYS]
    values = set()
    for row in rows:
        for i in indexes:
            if i < len(row) and row[i] is not None and str(row[i]).strip():
                raw = str(row[i]).strip()
                try:
                    values.add(normalize_phone(raw))
                except ValueError:
                    values.add(raw)
    return bool(indexes), next(iter(values)) if len(values) == 1 else None

