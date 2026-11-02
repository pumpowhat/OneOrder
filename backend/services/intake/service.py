import io
import re
from datetime import date, datetime
from pathlib import Path

from openpyxl import load_workbook

from .ai import AIClient
from .schemas import DraftLine, DraftOrder, SourceType

IMAGE_TYPES = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
EXCEL_SUFFIXES = {".xlsx"}
TEXT_SUFFIXES = {".txt", ".eml"}

# A line we could map and parse cleanly from a spreadsheet; below any review threshold.
EXCEL_CONFIDENCE = 0.95
UNPARSEABLE_CONFIDENCE = 0.4
SAMPLE_ROWS = 5


class UnsupportedInput(ValueError):
    pass


class IntakeService:
    def __init__(self, ai: AIClient):
        self.ai = ai

    def process(self, filename: str, content: bytes) -> DraftOrder:
        suffix = Path(filename).suffix.lower()
        if suffix in IMAGE_TYPES:
            return self.from_image(content, IMAGE_TYPES[suffix], filename)
        if suffix in EXCEL_SUFFIXES:
            return self.from_excel(content, filename)
        if suffix in TEXT_SUFFIXES:
            return self.from_email(content.decode("utf-8", errors="replace"), filename)
        raise UnsupportedInput(f"Unsupported file type: {suffix or filename}")

    def from_image(self, data: bytes, media_type: str, name: str | None = None) -> DraftOrder:
        return self._build(SourceType.IMAGE, name, self.ai.extract_from_image(data, media_type))

    def from_email(self, text: str, name: str | None = None) -> DraftOrder:
        if not text.strip():
            raise UnsupportedInput("Email text is empty")
        return self._build(SourceType.EMAIL, name, self.ai.extract_from_text(text))

    def from_excel(self, data: bytes, name: str | None = None) -> DraftOrder:
        sheet = load_workbook(io.BytesIO(data), read_only=True, data_only=True).active
        rows = [list(row) for row in sheet.iter_rows(values_only=True) if any(c is not None for c in row)]
        if len(rows) < 2:
            raise UnsupportedInput("Spreadsheet has no data rows")

        headers = [str(c).strip() if c is not None else "" for c in rows[0]]
        body = rows[1:]
        mapping = self.ai.map_excel_columns(headers, body[:SAMPLE_ROWS])

        index = {h: i for i, h in enumerate(headers) if h}
        col = {key: index.get(mapping.get(key) or "") for key in ("description", "quantity", "unit")}
        if col["description"] is None or col["quantity"] is None:
            raise UnsupportedInput("Could not find description and quantity columns")

        lines, warnings = [], []
        for n, row in enumerate(body, start=2):
            description = _cell(row, col["description"])
            if not description:
                continue
            quantity = _to_number(_cell(row, col["quantity"]))
            if quantity is None:
                warnings.append(f"Row {n}: quantity is missing or not a number")
            lines.append(
                DraftLine(
                    description=description,
                    quantity=quantity or 0,
                    unit=_cell(row, col["unit"]),
                    confidence=EXCEL_CONFIDENCE if quantity else UNPARSEABLE_CONFIDENCE,
                    source_text=" | ".join(str(c) for c in row if c is not None),
                )
            )

        order = DraftOrder(
            source_type=SourceType.EXCEL,
            source_name=name,
            customer=mapping.get("customer"),
            delivery_site=mapping.get("delivery_site"),
            requested_date=_to_date(mapping.get("requested_date")),
            lines=lines,
            warnings=warnings,
        )
        if not lines:
            order.warnings.append("No order lines found")
        return order

    def _build(self, source: SourceType, name: str | None, payload: dict) -> DraftOrder:
        """Turn a raw AI payload into a validated draft, dropping and flagging bad lines."""
        lines, warnings = [], []
        for n, raw in enumerate(payload.get("lines") or [], start=1):
            description = str(raw.get("description") or "").strip()
            quantity = _to_number(raw.get("quantity"))
            if not description or quantity is None or quantity <= 0:
                warnings.append(f"Line {n} dropped: missing description or valid quantity")
                continue
            lines.append(
                DraftLine(
                    description=description,
                    quantity=quantity,
                    unit=(str(raw["unit"]).strip() or None) if raw.get("unit") else None,
                    confidence=min(max(_to_number(raw.get("confidence")) or 0.0, 0.0), 1.0),
                    source_text=raw.get("source_text"),
                )
            )
        if not lines:
            warnings.append("No order lines found")
        return DraftOrder(
            source_type=source,
            source_name=name,
            customer=payload.get("customer"),
            delivery_site=payload.get("delivery_site"),
            requested_date=_to_date(payload.get("requested_date")),
            lines=lines,
            warnings=warnings,
        )


def _cell(row: list, index: int | None) -> str | None:
    if index is None or index >= len(row) or row[index] is None:
        return None
    return str(row[index]).strip() or None


def _to_number(value) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"-?\d+(?:[.,]\d+)?", str(value))
    return float(match.group().replace(",", ".")) if match else None


def _to_date(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)) if value else None
    except ValueError:
        return None
