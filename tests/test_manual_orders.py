"""Manual entry uses the same approval and fulfillment lifecycle as OCR."""
import pytest
from tests.test_orders_api import test_db, ai_client, client, EMAIL_ORDER  # noqa: F401


def line(**changes):
    return {"sku": "GYP-13-2400", "description": "Plasterboard", "quantity": 2,
            "confirmed": True, **changes}


def create(client, **changes):
    response = client.post("/api/orders", json={"customer": "Byg ApS", "customer_phone": "+4500000001",
        "delivery_site": "Amager Strandvej 12", "requested_date": "2026-11-20", "lines": [line()], **changes})
    assert response.status_code == 201, response.text
    return response.json()


def test_manual_lifecycle(client, monkeypatch):
    def no_ai():
        raise AssertionError("Manual entry must never request AI")
    from backend.ai import get_ai_client
    from backend.main import app
    monkeypatch.setitem(app.dependency_overrides, get_ai_client, no_ai)
    order = create(client)
    assert order["source_type"] == "manual"
    assert not order["has_source"]
    assert order["lines"][0]["unit"] == "stk"
    assert not order["lines"][0]["needs_review"]
    assert order["lines"][0]["source_text"] is None
    url = f"/api/orders/{order['id']}"
    assert client.get(url).json()["customer"] == "Byg ApS"
    assert client.post(url + "/approve", json={}).json()["status"] == "approved"
    assert client.patch(url, json={"customer": "Changed"}).status_code == 409
    plan = client.post(url + "/plan", json={"site_id": "SITE-DK-01"})
    assert plan.status_code == 200, plan.text
    confirmed = client.post(url + "/confirm", json={"allow_partial": True, "accept_late_risk": True})
    assert confirmed.status_code == 200, confirmed.text
    assert client.patch(url, json={"lines": []}).status_code == 409


def test_edit_ocr_keeps_original_and_stable_indices(client):
    intake = client.post("/api/intake", data={"text": EMAIL_ORDER}).json()
    url = f"/api/orders/{intake['id']}"
    original = client.get(url + "/source").json()
    before = client.get(url).json()
    response = client.patch(url, json={"customer": "Updated", "lines": [line(line_index=0), line()]})
    assert response.status_code == 200, response.text
    order = response.json()
    assert order["source_type"] == "email"
    assert [l["line_index"] for l in order["lines"]] == [0, 3]
    assert order["lines"][0]["source_text"] == before["lines"][0]["source_text"]
    assert client.get(url + "/source").json() == original
    assert {"add_line", "delete_line", "edit_order"} <= {a["action"] for a in order["audit_logs"]}
    assert client.patch(url, json={"lines": [line(line_index=0)]}).status_code == 200
    result = client.patch(url, json={"lines": [line(line_index=0), line()]}).json()
    assert [l["line_index"] for l in result["lines"]] == [0, 4]


@pytest.mark.parametrize("patch", [
    {"lines": [line(sku="UNKNOWN")]}, {"lines": [line(line_index=999)]},
    {"lines": [line(line_index=0), line(line_index=0)]},
    {"lines": [line(quantity=0)]}, {"lines": [line(quantity=-1)]},
    {"requested_date": "bad-date"}, {"lines": [line(description="  ")]},
])
def test_invalid_save_is_atomic(client, patch):
    order = create(client)
    url = f"/api/orders/{order['id']}"
    before = client.get(url).json()
    result = client.patch(url, json={"customer": "Should not persist", **patch})
    assert result.status_code in (400, 422)
    assert client.get(url).json() == before


def test_empty_draft_and_incomplete_review(client):
    order = create(client, lines=[], customer=None, customer_phone=None)
    url = f"/api/orders/{order['id']}"
    assert client.post(url + "/approve", json={}).status_code == 409
    assert client.patch(url, json={"lines": [line(sku=None, confirmed=False)]}).status_code == 200
    assert client.post(url + "/approve", json={}).status_code == 409
    assert client.patch(url, json={"customer": "Customer", "customer_phone": "invalid", "lines": [line()]}).status_code == 200
    assert client.post(url + "/approve", json={}).status_code == 409
    assert client.patch(url, json={"customer_phone": "+4500000001"}).status_code == 200
    assert client.post(url + "/approve", json={}).status_code == 200


def test_catalog_and_missing_order(client):
    response = client.get("/api/orders/catalog")
    assert response.status_code == 200
    assert {"sku", "name", "unit"} <= response.json()[0].keys()
    assert client.patch("/api/orders/missing", json={}).status_code == 404


def test_deleted_original_index_is_not_reused(client):
    intake = client.post("/api/intake", data={"text": EMAIL_ORDER}).json()
    url = f"/api/orders/{intake['id']}"
    assert client.patch(url, json={"lines": []}).status_code == 200
    result = client.patch(url, json={"lines": [line()]}).json()
    assert result["lines"][0]["line_index"] == 3


def test_edited_ai_line_requires_fresh_confirmation(client):
    order = create(client)
    url = f"/api/orders/{order['id']}"
    saved = client.patch(url, json={"lines": [line(line_index=0, quantity=3, confirmed=False)]})
    assert saved.json()["lines"][0]["needs_review"] is True
    assert client.post(url + "/approve", json={}).status_code == 409
    assert client.post(url + "/approve", json={"confirm_lines": [0]}).status_code == 200


def test_nonfinite_quantity_rejected(client):
    order = create(client)
    url = f"/api/orders/{order['id']}"
    before = client.get(url).json()
    response = client.patch(url, content='{"customer":"Changed","lines":[{"description":"Bad","quantity":1e999}]}', headers={"Content-Type": "application/json"})
    assert response.status_code == 422
    assert client.get(url).json() == before
