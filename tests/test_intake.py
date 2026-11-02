import io

import pytest
from openpyxl import Workbook

from backend.services.intake import IntakeService, SourceType, UnsupportedInput


class FakeAI:
    def __init__(self, payload=None, mapping=None):
        self.payload = payload or {}
        self.mapping = mapping or {}
        self.calls = []

    def extract_from_image(self, data, media_type):
        self.calls.append(("image", media_type))
        return self.payload

    def extract_from_text(self, text):
        self.calls.append(("text", text))
        return self.payload

    def map_excel_columns(self, headers, sample_rows):
        self.calls.append(("excel", headers))
        return self.mapping


PAYLOAD = {
    "customer": "Byg ApS",
    "delivery_site": "Vesterbrogade 1, Copenhagen",
    "requested_date": "2026-11-20",
    "lines": [
        {"description": "Gipsplade 13mm", "quantity": "40", "unit": "stk", "confidence": 0.97, "source_text": "40 stk gips"},
        {"description": "Skruer 4x40", "quantity": 12.5, "unit": "", "confidence": 0.6},
        {"description": "", "quantity": 3, "confidence": 0.9},
        {"description": "Spær", "quantity": "many", "confidence": 0.9},
    ],
}


def xlsx(rows):
    wb = Workbook()
    for row in rows:
        wb.active.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def test_email_builds_validated_draft():
    ai = FakeAI(PAYLOAD)
    order = IntakeService(ai).from_email("Hej, vi skal bruge ...")
    assert order.source_type is SourceType.EMAIL
    assert order.customer == "Byg ApS"
    assert str(order.requested_date) == "2026-11-20"
    assert [l.description for l in order.lines] == ["Gipsplade 13mm", "Skruer 4x40"]
    assert order.lines[0].quantity == 40
    assert order.lines[1].unit is None
    assert len(order.warnings) == 2  # empty description and non-numeric quantity dropped


def test_low_confidence_lines_need_review():
    order = IntakeService(FakeAI(PAYLOAD)).from_email("x")
    assert [l.needs_review for l in order.lines] == [False, True]
    assert order.needs_review


def test_confidence_is_clamped_and_bad_date_ignored():
    payload = {"requested_date": "tomorrow", "lines": [{"description": "a", "quantity": 1, "confidence": 3}]}
    order = IntakeService(FakeAI(payload)).from_email("x")
    assert order.lines[0].confidence == 1.0
    assert order.requested_date is None


def test_empty_email_rejected():
    with pytest.raises(UnsupportedInput):
        IntakeService(FakeAI()).from_email("   ")


def test_image_dispatch_by_extension():
    ai = FakeAI(PAYLOAD)
    order = IntakeService(ai).process("list.JPG", b"\xff\xd8")
    assert order.source_type is SourceType.IMAGE
    assert ai.calls == [("image", "image/jpeg")]


def test_unknown_extension_rejected():
    with pytest.raises(UnsupportedInput):
        IntakeService(FakeAI()).process("order.doc", b"")


def test_excel_uses_ai_column_mapping():
    data = xlsx([
        ["Varenr", "Beskrivning", "Antal", "Enhet"],
        ["1", "Gipsskiva 13mm", 40, "st"],
        ["2", "Skruv 4x40", "12,5", "pkt"],
        [None, None, None, None],
        ["3", "Reglar", "ca", "st"],
    ])
    mapping = {"description": "Beskrivning", "quantity": "Antal", "unit": "Enhet", "customer": "Bygg AB"}
    order = IntakeService(FakeAI(mapping=mapping)).process("order.xlsx", data)
    assert order.source_type is SourceType.EXCEL
    assert order.customer == "Bygg AB"
    assert [(l.description, l.quantity, l.unit) for l in order.lines] == [
        ("Gipsskiva 13mm", 40, "st"),
        ("Skruv 4x40", 12.5, "pkt"),
        ("Reglar", 0, "st"),
    ]
    assert [l.needs_review for l in order.lines] == [False, False, True]
    assert len(order.warnings) == 1


def test_excel_without_mappable_columns_rejected():
    data = xlsx([["a", "b"], [1, 2]])
    with pytest.raises(UnsupportedInput):
        IntakeService(FakeAI(mapping={"description": "nope"})).process("o.xlsx", data)
