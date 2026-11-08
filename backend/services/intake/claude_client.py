import base64
import json
import os

import anthropic

from .image import prepare_image
from .prompts import (  # noqa: F401  (re-exported for callers that import them from here)
    COLUMN_RULES,
    COLUMN_SCHEMA,
    MATCH_RULES,
    MATCH_SCHEMA,
    ORDER_RULES,
    ORDER_SCHEMA,
    PDF_ORDER_PROMPT,
)

DEFAULT_MODEL = "claude-opus-5-5"
MAX_TOKENS = 16000


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

    def extract_from_pdf(self, data: bytes) -> dict:
        content = [
            {
                "type": "document",
                "source": {
                    "type": "base64", "media_type": "application/pdf",
                    "data": base64.standard_b64encode(data).decode(),
                },
            },
            {"type": "text", "text": PDF_ORDER_PROMPT},
        ]
        return self._ask(ORDER_RULES, content, ORDER_SCHEMA)

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
