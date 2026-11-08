"""Prompts and JSON schemas shared by every live AI provider (Claude, Gemini)."""

_NULLABLE_STR = {"type": ["string", "null"]}

ORDER_SCHEMA = {
    "type": "object",
    "properties": {
        "customer": _NULLABLE_STR,
        "customer_phone": _NULLABLE_STR,
        "delivery_site": _NULLABLE_STR,
        "requested_date": {"type": ["string", "null"], "description": "ISO date YYYY-MM-DD"},
        "lines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "quantity": {"type": "number"},
                    "unit": _NULLABLE_STR,
                    "confidence": {"type": "number", "description": "0 to 1"},
                    "source_text": {"type": "string", "description": "The text exactly as written"},
                },
                "required": ["description", "quantity", "unit", "confidence", "source_text"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["customer", "customer_phone", "delivery_site", "requested_date", "lines"],
    "additionalProperties": False,
}

COLUMN_SCHEMA = {
    "type": "object",
    "properties": {
        "description": _NULLABLE_STR,
        "quantity": _NULLABLE_STR,
        "unit": _NULLABLE_STR,
        "customer": _NULLABLE_STR,
        "customer_phone": _NULLABLE_STR,
        "delivery_site": _NULLABLE_STR,
        "requested_date": _NULLABLE_STR,
    },
    "required": ["description", "quantity", "unit", "customer", "customer_phone", "delivery_site", "requested_date"],
    "additionalProperties": False,
}

ORDER_RULES = """\
You read building-material orders sent by contractors to a Nordic builders' merchant.
Text may be Danish, Swedish, Norwegian or English, and may be handwritten.

Rules:
- One entry in `lines` per material line, in the order written. Keep the description in the
  original language; do not translate or normalise it.
- `source_text` is the line exactly as written, so a person can compare it with your reading.
- `quantity` is the number ordered (decimal comma means decimal point). If a line has no readable
  quantity, give your best reading with a low confidence rather than inventing a confident one.
- `confidence` is how sure you are of description AND quantity together: 0.95+ for clear print,
  0.5-0.8 for doubtful handwriting, below 0.5 for guesses. Never give high confidence to a guess.
- Read customer_phone only when a customer contact phone is explicitly stated. Preserve its
  country code and leading zeros; never invent digits, infer a country code from the site,
  or use a supplier phone. If several conflicting customer phones cannot be resolved, use null.
- Use null for customer, customer_phone, delivery_site, requested_date or unit when they are not stated.
  `requested_date` must be YYYY-MM-DD; resolve it only if the year is clear."""

COLUMN_RULES = """\
You map the columns of a contractor's order spreadsheet. Given the header row and a few sample
rows, return the exact header text of the column holding each field, or null if there is none.
`description` is the material name, `quantity` the amount ordered, `unit` its unit of measure.
Also return customer, customer_phone, delivery_site and requested_date (YYYY-MM-DD) as actual
metadata VALUES (not column headers) only if they appear in the sample rows; otherwise null.
customer_phone must preserve leading zeros and the written country code. Never invent a phone
or infer its country from the delivery site. If customer phone values conflict, return null.
For description, quantity and unit use header text exactly as given."""

MATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "sku": {"type": ["string", "null"]},
    },
    "required": ["sku"],
    "additionalProperties": False,
}

MATCH_RULES = """\
You are an expert in Nordic building materials. A customer wrote an order line description in Danish,
Swedish, Norwegian or English. Given the description and top candidate products from the catalogue,
choose the best matching SKU. If none match the material, return null."""
