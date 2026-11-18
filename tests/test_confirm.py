"""POST /api/orders/{id}/confirm: reservations, guards, atomicity and the effect on later plans."""

from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
import re

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.ai import get_ai_client
from backend.db import Base, ReservationModel, get_db
from backend.erp import get_group_inventory
from backend.erp.reservations import apply_reservations, find_shortfalls, reserved_quantities
from backend.main import app
from backend.services.intake.demo_client import DemoClient
from backend.services.matching import clear_catalog_cache

SAMPLES_DIR = Path("samples")


@pytest.fixture
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'confirm.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False)


@pytest.fixture
def client(session_factory):
    clear_catalog_cache()

    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_ai_client] = lambda: DemoClient(SAMPLES_DIR / "fixtures")
    yield TestClient(app)
    app.dependency_overrides.clear()


def make_order(client, text: str | None = None, name="dk_order.txt", approve=True, plan=True, *, keep_requested_date=False) -> dict:
    data = (text or (SAMPLES_DIR / "emails" / name).read_text(encoding="utf-8")).encode("utf-8")
    res = client.post("/api/intake", files={"file": (name, data, "text/plain")})
    assert res.status_code == 200, res.text
    order = res.json()
    if not keep_requested_date:
        # Confirmation tests exercise reservations, not the ageing date in a recorded AI response.
        res = client.patch(
            f"/api/orders/{order['id']}",
            json={"requested_date": (date.today() + timedelta(days=30)).isoformat()},
        )
        assert res.status_code == 200, res.text
        order = res.json()
    if approve:
        corrections = [
            {"line_index": i, "sku": line["matched_sku"] or "GYP-13-2400", "confirmed": True}
            for i, line in enumerate(order["lines"])
        ]
        assert client.post(f"/api/orders/{order['id']}/approve", json={"corrections": corrections, "customer_phone": "+45 00 00 00 01"}).status_code == 200
    if plan:
        res = client.post(f"/api/orders/{order['id']}/plan")
        assert res.status_code == 200, res.text
    return order


def test_confirm_reserves_stock_and_freezes_plan(client):
    order = make_order(client)
    planned = client.get(f"/api/orders/{order['id']}").json()
    assert planned["status"] == "planned"

    res = client.post(f"/api/orders/{order['id']}/confirm")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "confirmed"
    assert body["plan"] == planned["plan"]  # plan and ETA are frozen as the commitment

    allocations = [
        (s["origin_warehouse"], a["sku"], a["quantity"]) for s in body["plan"]["shipments"] for a in s["lines"]
    ]
    got = [(r["warehouse_code"], r["sku"], r["quantity"]) for r in body["reservations"]]
    assert sorted(got) == sorted(allocations) and got

    confirm_log = [l for l in body["audit_logs"] if l["action"] == "confirm"]
    assert len(confirm_log) == 1
    assert confirm_log[0]["payload_after"]["reservations"] == len(allocations)
    assert confirm_log[0]["payload_after"]["order_eta"]["p90_date"] == body["plan"]["order_eta"]["p90_date"]


def test_confirm_requires_a_plan(client):
    drafted = make_order(client, approve=False, plan=False)
    assert client.post(f"/api/orders/{drafted['id']}/confirm").status_code == 409
    approved = make_order(client, plan=False)
    res = client.post(f"/api/orders/{approved['id']}/confirm")
    assert res.status_code == 409 and "plan the order" in res.json()["detail"]
    assert client.get(f"/api/orders/{approved['id']}").json()["status"] == "approved"


def test_confirm_unknown_order(client):
    assert client.post("/api/orders/nope/confirm").status_code == 404


def test_confirm_twice_and_cancel_after_confirm_are_rejected(client):
    order = make_order(client)
    assert client.post(f"/api/orders/{order['id']}/confirm").status_code == 200
    assert client.post(f"/api/orders/{order['id']}/confirm").status_code == 409
    assert client.post(f"/api/orders/{order['id']}/cancel").status_code == 409
    again = client.get(f"/api/orders/{order['id']}").json()
    assert again["status"] == "confirmed" and len(again["reservations"]) == len(set(map(str, again["reservations"])))


def test_shortage_blocks_confirm_unless_allow_partial(client, monkeypatch):
    monkeypatch.setattr("backend.routers.orders.get_group_inventory", lambda: [])
    order = make_order(client)
    plan = client.get(f"/api/orders/{order['id']}").json()["plan"]
    assert plan["shortages"] and not plan["fully_sourced"]

    res = client.post(f"/api/orders/{order['id']}/confirm")
    assert res.status_code == 409 and "shortages" in res.json()["detail"]
    assert client.get(f"/api/orders/{order['id']}").json()["status"] == "planned"

    ok = client.post(f"/api/orders/{order['id']}/confirm", json={"allow_partial": True})
    assert ok.status_code == 200 and ok.json()["status"] == "confirmed"
    assert ok.json()["reservations"] == []


def test_late_eta_blocks_confirm_unless_accepted(client):
    text = re.sub(r"20\d\d-\d\d-\d\d", "2020-01-01", (SAMPLES_DIR / "emails" / "dk_order.txt").read_text(encoding="utf-8"))
    order = make_order(client, text=text, keep_requested_date=True)
    stored = client.get(f"/api/orders/{order['id']}").json()
    assert stored["requested_date"] == "2020-01-01"
    assert stored["plan"]["order_eta"]["risk"] == "late"

    res = client.post(f"/api/orders/{order['id']}/confirm")
    assert res.status_code == 409 and "accept_late_risk" in res.json()["detail"]
    assert client.get(f"/api/orders/{order['id']}").json()["reservations"] == []

    ok = client.post(f"/api/orders/{order['id']}/confirm", json={"accept_late_risk": True})
    assert ok.status_code == 200
    assert ok.json()["audit_logs"][-1]["payload_after"]["accept_late_risk"] is True


def _scarce(monkeypatch, plan: dict) -> None:
    """Stock that covers exactly one copy of this plan's allocations."""
    exact = {}
    for s in plan["shipments"]:
        for a in s["lines"]:
            exact[(s["origin_warehouse"], a["sku"])] = exact.get((s["origin_warehouse"], a["sku"]), 0) + a["quantity"]

    def inventory():
        return [
            replace(i, available_quantity=exact[(i.warehouse_id, i.sku)])
            if (i.warehouse_id, i.sku) in exact
            else i
            for i in get_group_inventory()
        ]

    monkeypatch.setattr("backend.routers.orders.get_group_inventory", inventory)
    # confirm checks stock inside the ERPs, so they must see the same scarce stock
    monkeypatch.setattr(
        "backend.erp.mock_erp._country_items",
        lambda country, db: apply_reservations([i for i in inventory() if i.country == country], db),
    )


def test_second_order_cannot_take_stock_reserved_by_first(client, monkeypatch):
    first = make_order(client)
    second = make_order(client)  # planned while the stock was still free
    _scarce(monkeypatch, client.get(f"/api/orders/{first['id']}").json()["plan"])

    assert client.post(f"/api/orders/{first['id']}/confirm").status_code == 200
    res = client.post(f"/api/orders/{second['id']}/confirm")
    assert res.status_code == 409 and "stock changed since planning" in res.json()["detail"]
    after = client.get(f"/api/orders/{second['id']}").json()
    assert after["status"] == "planned" and after["reservations"] == []  # nothing half-written

    # Planning again sees the reduced stock: the exhausted (warehouse, sku) pairs are not offered again.
    reserved = {(r["warehouse_code"], r["sku"]) for r in client.get(f"/api/orders/{first['id']}").json()["reservations"]}
    replanned = client.post(f"/api/orders/{second['id']}/plan").json()
    reused = [
        (s["origin_warehouse"], a["sku"])
        for s in replanned["shipments"]
        for a in s["lines"]
        if (s["origin_warehouse"], a["sku"]) in reserved
    ]
    assert reused == []


# --- reservation helpers --------------------------------------------------------------------------


def test_apply_reservations_reduces_available_stock(session_factory):
    inventory = get_group_inventory()
    target = next(i for i in inventory if i.available_quantity >= 10)
    with session_factory() as db:
        assert apply_reservations(inventory, db) is inventory  # nothing reserved: untouched
        db.add(ReservationModel(order_id="o1", warehouse_code=target.warehouse_id, sku=target.sku, quantity=4))
        db.add(ReservationModel(order_id="o2", warehouse_code=target.warehouse_id, sku=target.sku, quantity=3))
        db.commit()
        assert reserved_quantities(db)[(target.warehouse_id, target.sku)] == 7
        adjusted = apply_reservations(inventory, db)
    item = next(i for i in adjusted if (i.warehouse_id, i.sku) == (target.warehouse_id, target.sku))
    assert item.available_quantity == target.available_quantity - 7
    assert item.reserved_quantity == target.reserved_quantity + 7
    assert len(adjusted) == len(inventory)


def test_find_shortfalls():
    inventory = get_group_inventory()
    item = next(i for i in inventory if i.available_quantity > 0)
    key = (item.warehouse_id, item.sku)
    assert find_shortfalls({key: item.available_quantity}, inventory) == []
    short = find_shortfalls({key: item.available_quantity + 1}, inventory)
    assert short and short[0][:2] == key
