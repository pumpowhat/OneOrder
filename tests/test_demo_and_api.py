import io
import json

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook
from PIL import Image

from backend.ai import get_ai_client
from backend.main import app
from backend.services.intake.demo_client import DemoClient, DemoFixtureMissing, fixture_key, parse_email

EMAIL = """Hej,

Kunde: Byg ApS
Leveringsadresse: Vesterbrogade 1, København
Leveres 20.11.2026

- 40 stk gipsplade 13mm
12,5 m2 isolering 100mm
Skruer 4x40 - 8 pk
Tak for hjælpen
"""


def test_parse_email_reads_header_and_both_line_styles():
    out = parse_email(EMAIL)
    assert out["customer"] == "Byg ApS"
    assert out["delivery_site"] == "Vesterbrogade 1, København"
    assert out["requested_date"] == "2026-11-20"
    assert [(l["description"], l["quantity"], l["unit"]) for l in out["lines"]] == [
        ("gipsplade 13mm", 40, "stk"),
        ("isolering 100mm", 12.5, "m2"),
        ("Skruer 4x40", 8, "pk"),
    ]
    assert all(l["confidence"] < 0.85 for l in out["lines"])  # rule-based lines always need review


def test_demo_maps_excel_columns_in_any_nordic_language():
    mapping = DemoClient("x").map_excel_columns(["Varenr", "Beskrivning", "Antal", "Enhet"], [])
    assert (mapping["description"], mapping["quantity"], mapping["unit"]) == ("Beskrivning", "Antal", "Enhet")


def test_demo_replays_recorded_fixture(tmp_path):
    payload = {"customer": "X", "lines": []}
    (tmp_path / f"{fixture_key(b'photo')}.json").write_text(json.dumps({"source": "a.jpg", "payload": payload}))
    client = DemoClient(tmp_path)
    assert client.extract_from_image(b"photo", "image/jpeg") == payload
    with pytest.raises(DemoFixtureMissing):
        client.extract_from_image(b"other", "image/jpeg")


@pytest.fixture
def api(tmp_path, monkeypatch):
    # The health endpoint reads AI_MODE directly, independently of the client override.
    monkeypatch.setenv("AI_MODE", "demo")
    app.dependency_overrides[get_ai_client] = lambda: DemoClient(tmp_path)
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_intake_text(api):
    res = api.post("/api/intake", data={"text": EMAIL})
    assert res.status_code == 200
    body = res.json()
    assert body["source_type"] == "email" and len(body["lines"]) == 3


def test_intake_excel_upload(api):
    wb = Workbook()
    wb.active.append(["Beskrivelse", "Antal", "Enhed"])
    wb.active.append(["Gips", 4, "stk"])
    buf = io.BytesIO()
    wb.save(buf)
    res = api.post("/api/intake", files={"file": ("o.xlsx", buf.getvalue())})
    assert res.status_code == 200 and res.json()["lines"][0]["quantity"] == 4


def test_intake_photo_without_fixture_is_422(api):
    buf = io.BytesIO()
    Image.new("RGB", (10, 10)).save(buf, format="PNG")
    res = api.post("/api/intake", files={"file": ("a.png", buf.getvalue())})
    assert res.status_code == 422 and "no recorded result" in res.json()["detail"]


def test_intake_validation(api):
    assert api.post("/api/intake").status_code == 422
    assert api.post("/api/intake", data={"text": "x"}, files={"file": ("a.txt", b"x")}).status_code == 422
    assert api.post("/api/intake", files={"file": ("a.doc", b"x")}).status_code == 422


def test_health_reports_ai_mode(api):
    assert api.get("/api/health").json() == {"status": "ok", "ai_mode": "demo"}
