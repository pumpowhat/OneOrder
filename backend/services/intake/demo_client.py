import hashlib
import json
import re
from pathlib import Path

# Words (lower-case) that identify a spreadsheet column, in Danish, Swedish, Norwegian and English.
COLUMN_WORDS = {
    "description": {"beskrivelse", "beskrivning", "benævnelse", "benämning", "varebeskrivelse", "vare", "artikel",
                    "produkt", "product", "item", "description", "materiale", "material", "navn", "namn", "name"},
    "quantity": {"antal", "antall", "mængde", "mengde", "kvantitet", "qty", "quantity", "stk"},
    "unit": {"enhed", "enhet", "unit", "uom", "mål"},
}

UNITS = r"stk|st|pcs|m2|m²|m|lm|pk|pkt|pakke|pack|rl|rulle|rull|sæk|sack|pall|palle|kg|l|ltr"
NUM = r"\d+(?:[.,]\d+)?"
QTY_FIRST = re.compile(rf"^({NUM})\s*(?:x\s*)?({UNITS})?\.?\s+(.+)$", re.IGNORECASE)
QTY_LAST = re.compile(rf"^(.+?)\s*(?:[:\-–]|\s)\s*({NUM})\s*({UNITS})\.?$", re.IGNORECASE)
KEYED = re.compile(r"^([^\W\d_]+(?: [^\W\d_]+)?)\s*:\s*(.+)$")
DATE = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}[./-]\d{1,2}[./-]\d{4})\b")
CUSTOMER_KEYS = {"kunde", "kund", "kunder", "customer", "firma", "company"}
SITE_KEYS = {"leveringsadresse", "levering", "leveransadress", "leveransadresse", "adresse", "adress", "delivery",
             "site", "byggeplads", "byggeplass", "byggarbetsplats", "leveringssted"}

# Rule-based reading is a fallback, so it never claims enough certainty to skip review.
RULE_CONFIDENCE = 0.75


class DemoFixtureMissing(ValueError):
    pass


def fixture_key(content: bytes | str) -> str:
    data = content.encode() if isinstance(content, str) else content
    return hashlib.sha256(data).hexdigest()


class DemoClient:
    """AIClient that needs no API key: recorded fixtures for known inputs, rules for the rest."""

    def __init__(self, fixture_dir: Path):
        self.fixture_dir = Path(fixture_dir)

    def extract_from_image(self, data: bytes, media_type: str) -> dict:
        fixture = self._load(data)
        if fixture is None:
            raise DemoFixtureMissing(
                "Demo mode has no recorded result for this photo. Use a sample from samples/, "
                "record one with scripts/record_fixture.py, or set AI_MODE=live."
            )
        return fixture

    def extract_from_text(self, text: str) -> dict:
        return self._load(text) or parse_email(text)

    def map_excel_columns(self, headers: list[str], sample_rows: list[list]) -> dict:
        mapping = {"customer": None, "delivery_site": None, "requested_date": None}
        for field, words in COLUMN_WORDS.items():
            mapping[field] = next((h for h in headers if words & set(re.findall(r"\w+", h.lower()))), None)
        return mapping

    def _load(self, content: bytes | str) -> dict | None:
        path = self.fixture_dir / f"{fixture_key(content)}.json"
        return json.loads(path.read_text("utf-8"))["payload"] if path.exists() else None


def parse_email(text: str) -> dict:
    customer = site = requested = None
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"^[-*•]\s+", "", raw.strip())
        if not line:
            continue
        if (date := DATE.search(line)) and requested is None:
            requested = _iso(date.group(1))
            continue
        if keyed := KEYED.match(line):
            key, value = keyed.group(1).lower(), keyed.group(2).strip()
            if key in CUSTOMER_KEYS:
                customer = value
                continue
            if key in SITE_KEYS:
                site = value
                continue
        for pattern, qty_i, unit_i, desc_i in ((QTY_FIRST, 1, 2, 3), (QTY_LAST, 2, 3, 1)):
            if match := pattern.match(line):
                lines.append({
                    "description": match.group(desc_i).strip(" :-–"),
                    "quantity": float(match.group(qty_i).replace(",", ".")),
                    "unit": match.group(unit_i),
                    "confidence": RULE_CONFIDENCE,
                    "source_text": line,
                })
                break
    return {"customer": customer, "delivery_site": site, "requested_date": requested, "lines": lines}


def _iso(value: str) -> str | None:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value
    day, month, year = re.split(r"[./-]", value)
    return f"{year}-{int(month):02d}-{int(day):02d}"
