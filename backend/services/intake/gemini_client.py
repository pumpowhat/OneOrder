import json
import os

from google import genai
from google.genai import errors, types

from .image import prepare_image
from .prompts import (
    COLUMN_RULES,
    COLUMN_SCHEMA,
    MATCH_RULES,
    MATCH_SCHEMA,
    ORDER_RULES,
    ORDER_SCHEMA,
    PDF_ORDER_PROMPT,
)

DEFAULT_MODEL = "gemini-3.5-flash"
# Gemini answers 503 ("high demand") in bursts, so retry those with backoff. 429 is NOT retried:
# on the free tier it usually means the daily quota is used up, which waiting seconds will not fix.
RETRY_ATTEMPTS = 4
RETRY_STATUS_CODES = [500, 503, 504]
# One call must not hang for minutes when Gemini is overloaded: give up after this long, then retry.
REQUEST_TIMEOUT_MS = 60_000


class GeminiClient:
    """Live AIClient backed by the Gemini API (vision for photos, structured JSON output).

    The key is read from GEMINI_API_KEY (or GOOGLE_API_KEY); the model from AI_MODEL.
    """

    def __init__(self, client: genai.Client | None = None, model: str | None = None):
        self.client = client or genai.Client(
            api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            http_options=types.HttpOptions(
                timeout=REQUEST_TIMEOUT_MS,
                retry_options=types.HttpRetryOptions(
                    attempts=RETRY_ATTEMPTS, http_status_codes=RETRY_STATUS_CODES
                )
            ),
        )
        self.model = model or os.getenv("AI_MODEL") or DEFAULT_MODEL

    def extract_from_image(self, data: bytes, media_type: str) -> dict:
        jpeg, media_type = prepare_image(data)
        contents = [
            types.Part.from_bytes(data=jpeg, mime_type=media_type),
            "Extract the order from this photo.",
        ]
        return self._ask(ORDER_RULES, contents, ORDER_SCHEMA)

    def extract_from_text(self, text: str) -> dict:
        return self._ask(ORDER_RULES, f"Extract the order from this email:\n\n{text}", ORDER_SCHEMA)

    def extract_from_pdf(self, data: bytes) -> dict:
        contents = [types.Part.from_bytes(data=data, mime_type="application/pdf"), PDF_ORDER_PROMPT]
        return self._ask(ORDER_RULES, contents, ORDER_SCHEMA)

    def map_excel_columns(self, headers: list[str], sample_rows: list[list]) -> dict:
        payload = json.dumps({"headers": headers, "sample_rows": sample_rows}, default=str, ensure_ascii=False)
        return self._ask(COLUMN_RULES, payload, COLUMN_SCHEMA)

    def match_product(self, description: str, candidates: list[dict]) -> str | None:
        payload = json.dumps({"description": description, "candidates": candidates}, default=str, ensure_ascii=False)
        return self._ask(MATCH_RULES, payload, MATCH_SCHEMA).get("sku")

    def _ask(self, system: str, contents, schema: dict) -> dict:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    response_mime_type="application/json",
                    response_json_schema=schema,
                ),
            )
        except errors.APIError as exc:
            raise RuntimeError(_describe(exc, self.model)) from exc
        reason = response.candidates[0].finish_reason if response.candidates else None
        if not response.text or (reason is not None and getattr(reason, "name", str(reason)) != "STOP"):
            raise RuntimeError(f"AI extraction failed: finish_reason={getattr(reason, 'name', reason)}")
        return json.loads(response.text)


def _describe(exc: errors.APIError, model: str) -> str:
    """One readable line for the API caller (the router turns RuntimeError into HTTP 502)."""
    if exc.code == 429:
        return (
            f"Gemini quota exceeded for model '{model}' (the free tier allows few requests per day). "
            "Wait for the quota to reset, use another AI_MODEL, enable billing, or run with AI_MODE=demo."
        )
    if exc.code == 404:
        return f"Gemini model '{model}' is not available to this key; set AI_MODEL to another model."
    if exc.code in (401, 403):
        return "Gemini rejected the API key; check GEMINI_API_KEY."
    return f"Gemini API error {exc.code} {exc.status}: {(exc.message or '')[:200]}"
