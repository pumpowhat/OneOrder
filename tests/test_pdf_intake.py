import io
import json

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.ai import get_ai_client
from backend.db import Base, get_db
from backend.main import app
from backend.services.intake import IntakeService, UnsupportedInput
from backend.services.intake.demo_client import DemoClient, fixture_key


PAYLOAD = {
    "customer": "Byg ApS",
    "customer_phone": "+4500000001",
    "delivery_site": "Sundkaj 7, 2150 Nordhavn",
    "requested_date": "2026-11-20",
    "lines": [
        {"description": "Gipsplade standard 13mm 1200x2400", "quantity": 20, "unit": "stk",
         "confidence": 0.96, "source_text": "20 stk Gipsplade standard 13mm 1200x2400"},
        {"description": "Gipsskruer 3.9x40mm", "quantity": 8, "unit": "pk",
         "confidence": 0.7, "source_text": "8 pk Gipsskruer 3.9x40mm"},
    ],
}


def pdf_bytes(pages=2, *, scanned=False, encrypted=False):
    out = io.BytesIO()
    if scanned:
        images = []
        for line in PAYLOAD["lines"][:pages]:
            image = Image.new("RGB", (600, 800), "white")
            ImageDraw.Draw(image).text((30, 50), line["source_text"], fill="black")
            images.append(image)
        images[0].save(out, format="PDF", save_all=True, append_images=images[1:])
    else:
        writer = PdfWriter()
        font = writer._add_object(DictionaryObject({
            NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }))
        for n in range(pages):
            page = writer.add_blank_page(width=600, height=800)
            page[NameObject("/Resources")] = DictionaryObject({
                NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
            })
            stream = DecodedStreamObject()
            text = PAYLOAD["lines"][n % 2]["source_text"]
            stream.set_data(f"BT /F1 12 Tf 30 750 Td ({text}) Tj ET".encode())
            page[NameObject("/Contents")] = writer._add_object(stream)
        if encrypted:
            writer.encrypt("test-password")
        writer.write(out)
    return out.getvalue()


class PdfAI:
    def __init__(self):
        self.documents = []

    def extract_from_pdf(self, data):
        self.documents.append(data)
        return PAYLOAD

    def match_product(self, description, candidates):
        return candidates[0]["sku"] if candidates else None


@pytest.mark.parametrize("scanned", [False, True], ids=["text-pdf", "scanned-pdf"])
def test_pdf_passes_all_pages_to_ai_and_builds_reviewable_order(scanned):
    ai = PdfAI()
    data = pdf_bytes(scanned=scanned)
    order = IntakeService(ai).process("order.PDF", data)
    assert ai.documents == [data]  # keep the entire document, including image-only pages
    assert order.source_type.value == "pdf"
    assert order.source_name == "order.PDF"
    assert order.customer == PAYLOAD["customer"]
    assert order.customer_phone == PAYLOAD["customer_phone"]
    assert [line.quantity for line in order.lines] == [20, 8]
    assert [line.needs_review for line in order.lines] == [False, True]


@pytest.mark.parametrize("data, message", [
    (b"", "readable PDF"),
    (b"not a pdf", "readable PDF"),
    (b"%PDF-1.7\nbroken", "readable PDF"),
    (pdf_bytes(pages=0), "no pages"),
    (pdf_bytes(pages=21), "20 pages"),
    (pdf_bytes(encrypted=True), "encrypted"),
])
def test_invalid_pdf_rejected_before_ai(data, message):
    ai = PdfAI()
    with pytest.raises(UnsupportedInput, match=message):
        IntakeService(ai).process("order.pdf", data)
    assert ai.documents == []


def test_twenty_page_pdf_is_accepted():
    data = pdf_bytes(pages=20)
    ai = PdfAI()
    assert IntakeService(ai).process("order.pdf", data).lines
    assert ai.documents == [data]


def test_pdf_demo_replays_fixture_and_describes_missing_ocr(tmp_path):
    data = pdf_bytes()
    demo = DemoClient(tmp_path)
    with pytest.raises(ValueError, match="PDF.*AI_MODE=live"):
        IntakeService(demo).process("order.pdf", data)
    (tmp_path / f"{fixture_key(data)}.json").write_text(json.dumps({"payload": PAYLOAD}))
    order = IntakeService(demo).process("order.pdf", data)
    assert order.customer == "Byg ApS" and len(order.lines) == 2


@pytest.fixture
def client(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'pdf.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine)

    def database():
        with sessions() as db:
            yield db

    app.dependency_overrides[get_db] = database
    app.dependency_overrides[get_ai_client] = PdfAI
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


@pytest.mark.parametrize("mime", ["application/pdf", "application/octet-stream", "text/html"])
def test_pdf_upload_matches_skus_and_preserves_original_with_pdf_mime(client, mime):
    data = pdf_bytes(scanned=True)
    response = client.post("/api/intake", files={"file": ("scan.pdf", data, mime)})
    assert response.status_code == 200, response.text
    order = response.json()
    assert order["source_type"] == "pdf"
    assert order["lines"][0]["matched_sku"] == "GYP-13-2400"
    source = client.get(f"/api/orders/{order['id']}/source").json()
    assert source == {"name": "scan.pdf", "mime": "application/pdf", "source_type": "pdf", "kind": "pdf"}
    raw = client.get(f"/api/orders/{order['id']}/source/file")
    assert raw.content == data and raw.headers["content-type"] == "application/pdf"
    stored = client.get(f"/api/orders/{order['id']}").json()
    assert stored["source_type"] == "pdf" and stored["has_source"]
    assert stored["audit_logs"][0]["action"] == "create_draft"
    assert client.get("/api/orders").json()[0]["source_type"] == "pdf"


@pytest.mark.parametrize("data, status", [(b"%PDF-broken", 422), (b"x" * (10 * 1024 * 1024 + 1), 413)])
def test_bad_pdf_upload_creates_no_draft(client, data, status):
    response = client.post("/api/intake", files={"file": ("order.pdf", data, "application/pdf")})
    assert response.status_code == status
    assert client.get("/api/orders").json() == []


def test_pdf_provider_failure_creates_no_draft(client):
    class FailingAI(PdfAI):
        def extract_from_pdf(self, data):
            raise RuntimeError("PDF OCR service unavailable")

    app.dependency_overrides[get_ai_client] = FailingAI
    response = client.post("/api/intake", files={"file": ("order.pdf", pdf_bytes(), "application/pdf")})
    assert response.status_code == 502
    assert client.get("/api/orders").json() == []
