"""Phone intake, approval transactions and old-DB migration without external AI calls.

Approval functions are exercised against real SQLite sessions, independently of HTTP/TestClient.
"""
import json
from pathlib import Path

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from backend.db import Base, OrderModel, init_db, order_model_to_dict, save_draft_order
from backend.routers.orders import ApproveOrderRequest, approve_order, _order_summary
from backend.services.intake import IntakeService
from backend.services.intake.demo_client import DemoClient
from backend.services.intake.prompts import ORDER_SCHEMA, COLUMN_SCHEMA
from backend.services.intake.schemas import DraftLine, DraftOrder, SourceType
from backend.services.orders.phone import normalize_phone
from tests.test_intake import FakeAI, xlsx


@pytest.mark.parametrize(("raw", "expected"), [
    (" +45 00 00 00 01 ", "+4500000001"),
    ("0046 (00) 00-00.02", "+4600000002"),
    ("090 000 0001", "0900000001"),
    ("1234567", "1234567"),
    ("+123456789012345", "+123456789012345"),
])
def test_phone_formatting_preserves_digits_and_does_not_guess_country(raw, expected):
    assert normalize_phone(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "   ", "123", "+", "phone", "+45 123ABC456",
                                     "1234567890123456", "+0123456789", "+45/12345678", "++4512345678"])
def test_invalid_phone_is_rejected(raw):
    with pytest.raises(ValueError, match="customer phone"):
        normalize_phone(raw)


@pytest.mark.parametrize("source", ["image", "email"])
def test_live_intake_contract_carries_phone_without_inventing_one(source):
    payload = {"customer": "Example Co", "customer_phone": "0045 00 00 00 01", "lines": []}
    service = IntakeService(FakeAI(payload))
    order = service.from_image(b"x", "image/jpeg") if source == "image" else service.from_email("order")
    assert order.customer_phone == "+4500000001"
    payload.pop("customer_phone")
    assert service.from_email("order").customer_phone is None
    for schema in [ORDER_SCHEMA, COLUMN_SCHEMA]:
        assert "customer_phone" in schema["required"]


@pytest.mark.parametrize("label", ["Telefon", "Telefonnummer", "Tlf", "Tel.", "Phone", "Customer phone"])
def test_demo_email_reads_phone_labels(label):
    # A date-like sequence in a phone must not be mistaken for the requested date.
    email = f"Kunde: Example Co\n{label}: +45 2026-11-20\nDato: 2026-11-30\n1 stk gips"
    order = IntakeService(DemoClient("unused")).from_email(email)
    assert order.customer_phone == "+4520261120"
    assert str(order.requested_date) == "2026-11-30"
    assert len(order.lines) == 1


@pytest.mark.parametrize("label", ["Delivery", "Levering", "Leveringsadresse"])
def test_dated_delivery_line_is_requested_date_not_site(label):
    email = f"Kunde: Example Co\n{label}: 2025-03-12\nTlf: 12345678\n1 stk gips"
    order = IntakeService(DemoClient("unused")).from_email(email)
    assert str(order.requested_date) == "2025-03-12"
    assert order.delivery_site is None
    assert order.customer_phone == "12345678"


def test_doubtful_ocr_is_kept_for_manual_correction():
    order = IntakeService(FakeAI({"customer_phone": "+45 OO 0000 01"})).from_email("order")
    assert order.customer_phone == "+45 OO 0000 01"
    with pytest.raises(ValueError):
        normalize_phone(order.customer_phone)


def test_conflicting_phone_values_are_not_silently_chosen():
    service = IntakeService(DemoClient("unused"))
    assert service.from_email("Phone: +4500000001\nPhone: +4600000002").customer_phone is None
    rows = [["Product", "Qty", "Phone"]] + [["gips", 1, "+4500000001"] for _ in range(5)]
    rows.append(["gips", 1, "+4600000002"])
    order = service.process("order.xlsx", xlsx(rows))
    assert order.customer_phone is None  # conflict beyond AI's five sample rows also counts
    assert any("conflicting" in w for w in order.warnings)


def test_excel_phone_keeps_national_leading_zero():
    service = IntakeService(DemoClient("unused"))
    order = service.process("order.xlsx", xlsx([
        ["Product", "Qty", "Telefon"], ["gips", 1, "090 000 0001"],
    ]))
    assert order.customer_phone == "0900000001"


@pytest.fixture
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'phones.db'}")
    Base.metadata.create_all(engine)
    with Session(engine, autoflush=False) as session:
        yield session
    engine.dispose()


def draft(db, phone=None):
    order = DraftOrder(source_type=SourceType.EMAIL, customer="Example Co", customer_phone=phone,
                       lines=[DraftLine(description="Gips", quantity=1, confidence=0.95,
                                        matched_sku="GYP-13-2400", match_score=1, confirmed=True)])
    save_draft_order(db, order)
    return order.id


@pytest.mark.parametrize("phone", [None, "", "   ", "abc", "123"])
def test_approval_blocks_missing_or_invalid_phone_and_rolls_back(db, phone):
    oid = draft(db)
    original = order_model_to_dict(db.get(OrderModel, oid))
    request = ApproveOrderRequest(customer_phone=phone, corrections=[{"line_index": 0, "quantity": 12}])
    with pytest.raises(HTTPException) as error:
        approve_order(oid, request, db)
    assert error.value.status_code == 409
    assert "customer phone" in error.value.detail
    db.rollback()  # session dependency close rolls back failed requests in the HTTP path
    current = order_model_to_dict(db.get(OrderModel, oid))
    assert current["status"] == "draft"
    assert current["lines"][0]["quantity"] == original["lines"][0]["quantity"]
    assert current["audit_logs"] == original["audit_logs"]


def test_manual_correction_is_persisted_and_audited(db):
    oid = draft(db, "+45 OO 0000 01")
    result = approve_order(oid, ApproveOrderRequest(customer_phone="0045 00 00 00 01"), db)
    assert result["status"] == "approved"
    assert result["customer_phone"] == "+4500000001"
    event = next(l for l in result["audit_logs"] if l["action"] == "set_customer_phone")
    assert event["payload_before"] == {"customer_phone": "+45 OO 0000 01"}
    assert event["payload_after"] == {"customer_phone": "+4500000001"}
    db.expire_all()
    assert _order_summary(db.get(OrderModel, oid))["customer_phone"] == "+4500000001"


def test_extracted_phone_can_be_reused_and_is_not_unique_across_orders(db):
    for _ in range(2):
        oid = draft(db, "+45 00 00 00 01")
        result = approve_order(oid, ApproveOrderRequest(), db)
        assert result["status"] == "approved" and result["customer_phone"] == "+4500000001"


def test_explicit_blank_cannot_fall_back_to_extracted_phone(db):
    oid = draft(db, "+4500000001")
    with pytest.raises(HTTPException):
        approve_order(oid, ApproveOrderRequest(customer_phone=" "), db)
    db.rollback()
    assert db.get(OrderModel, oid).customer_phone == "+4500000001"


def test_old_database_upgrade_keeps_existing_confirmed_order_without_fabricating_phone(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE orders (id VARCHAR(36) PRIMARY KEY, status VARCHAR(20) NOT NULL)"))
        conn.execute(text("INSERT INTO orders (id, status) VALUES ('old', 'confirmed')"))
    init_db(engine)
    init_db(engine)
    assert "customer_phone" in {c["name"] for c in inspect(engine).get_columns("orders")}
    with engine.connect() as conn:
        assert conn.execute(text("SELECT id, status, customer_phone FROM orders")).one() == ("old", "confirmed", None)
    engine.dispose()


@pytest.mark.parametrize("expected_path", sorted(Path("samples/expected").glob("*.json")), ids=lambda p: p.name)
def test_samples_have_matching_phone_in_intake_and_storage(db, expected_path):
    expected = json.loads(expected_path.read_text())
    filename = expected["source_file"]
    folder = "photos" if filename.endswith(".jpg") else "excel" if filename.endswith(".xlsx") else "emails"
    path = Path("samples") / folder / filename
    order = IntakeService(DemoClient("samples/fixtures")).process(filename, path.read_bytes())
    assert order.customer_phone == expected["customer_phone"]
    model = save_draft_order(db, order)
    assert order_model_to_dict(model)["customer_phone"] == expected["customer_phone"]
