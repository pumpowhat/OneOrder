import base64
import json
import os

import anthropic

from .image import prepare_image

DEFAULT_MODEL = "claude-opus-5-5"
MAX_TOKENS = 16000

_NULLABLE_STR = {"type": ["string", "null"]}

ORDER_SCHEMA = {
    "type": "object",
    "properties": {
        "customer": _NULLABLE_STR,
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
    "required": ["customer", "delivery_site", "requested_date", "lines"],
    "additionalProperties": False,
}

COLUMN_SCHEMA = {
    "type": "object",
    "properties": {
        "description": _NULLABLE_STR,
        "quantity": _NULLABLE_STR,
        "unit": _NULLABLE_STR,
        "customer": _NULLABLE_STR,
        "delivery_site": _NULLABLE_STR,
        "requested_date": _NULLABLE_STR,
    },
    "required": ["description", "quantity", "unit", "customer", "delivery_site", "requested_date"],
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
- Use null for customer, delivery_site, requested_date or unit when they are not stated.
  `requested_date` must be YYYY-MM-DD; resolve it only if the year is clear."""

COLUMN_RULES = """\
You map the columns of a contractor's order spreadsheet. Given the header row and a few sample
rows, return the exact header text of the column holding each field, or null if there is none.
`description` is the material name, `quantity` the amount ordered, `unit` its unit of measure.
Also return customer, delivery_site and requested_date (YYYY-MM-DD) only if they appear as values
in the sample rows; otherwise null. Use header text exactly as given."""

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


class ClaudeClient:
    """Live AIClient backed by the Claude API (vision for photos, structured JSON output)."""

    def __init__(self, client: anthropic.Anthropic | None = None, model: str | None = None):
        self.client = client or anthropic.Anthropic()
        self.model = model or os.getenv("AI_MODEL") or DEFAULT_MODEL

    def extract_from_image(self, data: bytes, media_type: str) -> dict:
        jpeg, media_type = prepare_image(data)
        content = [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": base64.standard_b64encode(jpeg).decode()},
            },
            {"type": "text", "text": "Extract the order from this photo."},
        ]
        return self._ask(ORDER_RULES, content, ORDER_SCHEMA)

    def extract_from_text(self, text: str) -> dict:
        return self._ask(ORDER_RULES, f"Extract the order from this email:\n\n{text}", ORDER_SCHEMA)

    def map_excel_columns(self, headers: list[str], sample_rows: list[list]) -> dict:
        payload = json.dumps({"headers": headers, "sample_rows": sample_rows}, default=str, ensure_ascii=False)
        return self._ask(COLUMN_RULES, payload, COLUMN_SCHEMA)

    def match_product(self, description: str, candidates: list[dict]) -> str | None:
        payload = json.dumps({"description": description, "candidates": candidates}, default=str, ensure_ascii=False)
        return self._ask(MATCH_RULES, payload, MATCH_SCHEMA).get("sku")

    def _ask(self, system: str, content, schema: dict) -> dict:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=system,
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": schema}},
            messages=[{"role": "user", "content": content}],
        )
        if response.stop_reason in ("refusal", "max_tokens"):
            raise RuntimeError(f"AI extraction failed: stop_reason={response.stop_reason}")
        return json.loads(next(b.text for b in response.content if b.type == "text"))
