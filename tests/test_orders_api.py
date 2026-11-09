import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db import Base, get_db
from backend.main import app
from backend.services.matching import clear_catalog_cache

EMAIL_ORDER = """\
Fra: lars@byggefirma.dk
Til: ordre@bygma.dk
Emne: Materialer til Byggeplads Amager
Dato: 2026-11-20

Hej,
Vi skal bruge følgende leveret til Amager Strandvej 12:
- 40 stk Gipsplade standard 13mm 1200x2400
- 12.5 m2 Isolering glasuld 100mm
- 8 pk Gipsskruer 3.9x40mm til træ/stål

Hilsen Lars
"""


@pytest.fixture
def test_db(tmp_path):
    clear_catalog_cache()
    db_file = tmp_path / "test_oneorder.db"
    test_engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestingSessionLocal
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    return TestClient(app)


def test_intake_creates_order_and_audit_log(client):
    res = client.post("/api/intake", data={"text": EMAIL_ORDER})
    assert res.status_code == 200
    order_data = res.json()
    order_id = order_data["id"]
    assert order_id is not None
    assert order_data["status"] == "draft"
    assert len(order_data["lines"]) == 3

    # Check that lines have matched SKUs from catalog
    assert order_data["lines"][0]["matched_sku"] == "GYP-13-2400"
    assert order_data["lines"][1]["matched_sku"] == "ISO-GLAS-100"
    assert order_data["lines"][2]["matched_sku"] == "SCR-GIP-40"

    # Fetch via GET /api/orders/{id}
    order_res = client.get(f"/api/orders/{order_id}")
    assert order_res.status_code == 200
    stored_order = order_res.json()
    assert stored_order["id"] == order_id
    assert stored_order["status"] == "draft"

    # Verify audit log was recorded for draft creation
    logs = stored_order["audit_logs"]
    assert len(logs) >= 1
    assert logs[0]["action"] == "create_draft"
    assert logs[0]["user"] == "sales_desk"
    assert logs[0]["payload_after"] is not None


def test_approve_blocked_when_line_needs_review(client):
    # Order with an unmatchable line (needs review & missing SKU)
    unmatched_text = """\
Fra: jens@byg.dk
Levering: Havnegade 5

- 2 stk Cà phê sữa đá đặc biệt
"""
    res = client.post("/api/intake", data={"text": unmatched_text})
    assert res.status_code == 200
    order_id = res.json()["id"]

    # Attempt to approve without corrections -> Must return 409
    approve_res = client.post(f"/api/orders/{order_id}/approve", json={})
    assert approve_res.status_code == 409
    assert "missing SKU" in approve_res.json()["detail"] or "requires review" in approve_res.json()["detail"]


def test_approve_blocked_when_rule_confidence_low(client):
    # Rule-based email reading sets confidence to 0.75, which triggers review_threshold (< 0.85)
    res = client.post("/api/intake", data={"text": EMAIL_ORDER})
    assert res.status_code == 200
    order_id = res.json()["id"]

    # Even though SKUs matched, confidence < 0.85 requires human review confirmation
    approve_res = client.post(f"/api/orders/{order_id}/approve", json={})
    assert approve_res.status_code == 409
    assert "requires review" in approve_res.json()["detail"]


def test_approve_rejects_invalid_sku(client):
    res = client.post("/api/intake", data={"text": EMAIL_ORDER})
    assert res.status_code == 200
    order_id = res.json()["id"]

    approve_payload = {
        "corrections": [
            {"line_index": 0, "sku": "NON_EXISTENT_SKU_999"},
        ]
    }
    approve_res = client.post(f"/api/orders/{order_id}/approve", json=approve_payload)
    assert approve_res.status_code == 400
    assert "not found in catalogue" in approve_res.json()["detail"]


def test_approve_rejects_non_positive_quantity(client):
    res = client.post("/api/intake", data={"text": EMAIL_ORDER})
    assert res.status_code == 200
    order_id = res.json()["id"]

    approve_payload = {
        "corrections": [
            {"line_index": 0, "quantity": -5.0},
        ]
    }
    approve_res = client.post(f"/api/orders/{order_id}/approve", json=approve_payload)
    assert approve_res.status_code == 400
    assert "greater than 0" in approve_res.json()["detail"]


def test_approve_succeeds_with_corrections_and_confirmations(client):
    res = client.post("/api/intake", data={"text": EMAIL_ORDER})
    assert res.status_code == 200
    order_id = res.json()["id"]

    # User confirms lines and corrects line 0
    approve_payload = {
        "user": "anna_sales",
        "corrections": [
            {"line_index": 0, "sku": "GYP-13-2400", "confirmed": True},
        ],
        "confirm_lines": [1, 2],
        "customer": "Byggefirma ApS",
        "customer_phone": "+45 00 00 00 01",
    }

    approve_res = client.post(f"/api/orders/{order_id}/approve", json=approve_payload)
    assert approve_res.status_code == 200
    approved_data = approve_res.json()
    assert approved_data["status"] == "approved"
    assert approved_data["customer"] == "Byggefirma ApS"
    assert "set_customer" in [l["action"] for l in approved_data["audit_logs"]]

    # Verify audit logs for edit_line, confirm_line, and approve
    logs = approved_data["audit_logs"]
    actions = [l["action"] for l in logs]
    assert "create_draft" in actions
    assert "edit_line" in actions
    assert "confirm_line" in actions
    assert "approve" in actions

    # Verify user attribution in audit log
    approve_log = next(l for l in logs if l["action"] == "approve")
    assert approve_log["user"] == "anna_sales"
    assert approve_log["payload_before"] == {"status": "draft"}
    assert approve_log["payload_after"] == {"status": "approved"}


def test_approve_rejects_already_approved_order(client):
    res = client.post("/api/intake", data={"text": EMAIL_ORDER})
    order_id = res.json()["id"]

    approve_payload = {
        "corrections": [
            {"line_index": 0, "sku": "GYP-13-2400", "confirmed": True},
        ],
        "confirm_lines": [1, 2],
        "customer": "Byggefirma ApS",
        "customer_phone": "+45 00 00 00 01",
    }
    res_first = client.post(f"/api/orders/{order_id}/approve", json=approve_payload)
    assert res_first.status_code == 200

    # Second approval attempt must return 409
    res_second = client.post(f"/api/orders/{order_id}/approve", json=approve_payload)
    assert res_second.status_code == 409
    assert "already been approved" in res_second.json()["detail"]


def test_get_nonexistent_order_returns_404(client):
    res = client.get("/api/orders/non-existent-id")
    assert res.status_code == 404


def test_approve_returns_503_when_catalog_unavailable(client, monkeypatch):
    res = client.post("/api/intake", data={"text": EMAIL_ORDER})
    order_id = res.json()["id"]

    def broken_catalog():
        raise FileNotFoundError("catalog.json missing")

    monkeypatch.setattr("backend.routers.orders.load_catalog", broken_catalog)

    approve_res = client.post(f"/api/orders/{order_id}/approve", json={})
    assert approve_res.status_code == 503
    assert "Catalogue service unavailable" in approve_res.json()["detail"]


def test_init_db_custom_engine_does_not_set_global_flag():
    import backend.db as db_mod
    original_flag = db_mod._db_initialized
    try:
        db_mod._db_initialized = False
        custom_engine = create_engine("sqlite:///:memory:")
        db_mod.init_db(target_engine=custom_engine)
        assert db_mod._db_initialized is False
        db_mod.init_db()  # default engine
        assert db_mod._db_initialized is True
    finally:
        db_mod._db_initialized = original_flag


def test_approve_requires_customer_name_when_ocr_found_none(client):
    res = client.post("/api/intake", data={"text": EMAIL_ORDER})
    order = res.json()
    assert not order["customer"]
    corrections = [
        {"line_index": i, "sku": line["matched_sku"] or "GYP-13-2400", "confirmed": True}
        for i, line in enumerate(order["lines"])
    ]

    blank = client.post(f"/api/orders/{order['id']}/approve", json={"corrections": corrections, "customer": "   "})
    assert blank.status_code == 409
    assert "customer name" in blank.json()["detail"]
    assert client.get(f"/api/orders/{order['id']}").json()["status"] == "draft"

    ok = client.post(f"/api/orders/{order['id']}/approve", json={"corrections": corrections, "customer": " Byg ApS ", "customer_phone": "+45 00 00 00 01"})
    assert ok.status_code == 200
    assert ok.json()["customer"] == "Byg ApS"


def test_approve_can_correct_formerly_unflagged_sku(client, test_db):
    from backend.db import OrderModel, OrderLineModel

    with test_db() as db:
        order = OrderModel(source_type="email", customer="Byg ApS", customer_phone="+4512345678")
        order.lines = [OrderLineModel(
            line_index=0, description="stone wool insulation 100mm", quantity=1,
            confidence=0.95, match_score=0.9643, matched_sku="ISO-ROCK-150",
            ambiguous=0, confirmed=0,
        )]
        db.add(order)
        db.commit()
        order_id = order.id

    before = client.get(f"/api/orders/{order_id}").json()
    assert before["lines"][0]["needs_review"] is False
    response = client.post(f"/api/orders/{order_id}/approve", json={
        "corrections": [{"line_index": 0, "sku": "ISO-ROCK-100", "confirmed": True}],
    })
    assert response.status_code == 200
    assert response.json()["lines"][0]["matched_sku"] == "ISO-ROCK-100"
    assert any(log["action"] == "edit_line" for log in response.json()["audit_logs"])
