"""Simulated national ERPs: native payloads, reservation ledger, and /confirm writing through to them."""

import csv
import io
import json
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.ai import get_ai_client
from backend.db import Base, ReservationModel, get_db
from backend.erp import get_group_inventory, load_dk_inventory, load_no_inventory, load_se_inventory
from backend.erp import mock_erp
from backend.erp.reservations import apply_reservations
from backend.main import app
from backend.services.intake.demo_client import DemoClient
from backend.services.matching import clear_catalog_cache

SAMPLES = Path("samples")


@pytest.fixture
def session_factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'erp.db'}", connect_args={"check_same_thread": False})
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
    app.dependency_overrides[get_ai_client] = lambda: DemoClient(SAMPLES / "fixtures")
    yield TestClient(app)
    app.dependency_overrides.clear()


def stocked(country: str, minimum: float = 10):
    """A (warehouse, sku, available) with enough stock in the given country."""
    item = next(i for i in get_group_inventory() if i.country == country and i.available_quantity >= minimum)
    return item.warehouse_id, item.sku, float(item.available_quantity)


def reserved_in_native(client, country: str, warehouse: str, sku: str) -> float:
    body = client.get(f"/mock-erp/{country.lower()}/stock")
    assert body.status_code == 200
    if country == "DK":
        rows = list(csv.DictReader(io.StringIO(body.text)))
        return float(next(r for r in rows if r["lager_kode"] == warehouse and r["varenr"] == sku)["reserveret"])
    rows = body.json()
    wh_key, sku_key, res_key = (
        ("lagerplats", "artikelnr", "reserverat") if country == "SE" else ("warehouse_id", "sku", "reserved_quantity")
    )
    return float(next(r for r in rows if r[wh_key] == warehouse and r[sku_key] == sku)[res_key])


# --- native payloads ------------------------------------------------------------------------------


def test_native_stock_formats(client):
    dk = client.get("/mock-erp/dk/stock")
    assert dk.headers["content-type"].startswith("text/csv")
    assert dk.text.splitlines()[0] == "varenr,lager_kode,beholdning,reserveret,enhed"

    se = client.get("/mock-erp/se/stock")
    assert se.headers["content-type"].startswith("application/json")
    assert {"artikelnr", "lagerplats", "saldo", "reserverat", "enhet"} <= set(se.json()[0])

    no = client.get("/mock-erp/NO/stock")  # case-insensitive
    assert {"sku", "warehouse_id", "quantity_on_hand", "reserved_quantity", "unit"} <= set(no.json()[0])

    assert client.get("/mock-erp/fr/stock").status_code == 404


def test_untouched_native_payload_equals_the_opening_balance(client, tmp_path):
    path = tmp_path / "dk.csv"
    path.write_text(client.get("/mock-erp/dk/stock").text, encoding="utf-8")
    assert load_dk_inventory(path) == load_dk_inventory()


@pytest.mark.parametrize("country, loader, ext", [("DK", load_dk_inventory, "csv"), ("SE", load_se_inventory, "json"), ("NO", load_no_inventory, "json")])
def test_native_payload_read_back_matches_onorder_view_after_reservation(client, session_factory, tmp_path, country, loader, ext):
    wh, sku, _ = stocked(country)
    with session_factory() as db:
        mock_erp.reserve(db, country, "order-x", [{"warehouse": wh, "sku": sku, "quantity": 4}], commit=True)
        body, _ = mock_erp.native_stock(country, db)
        expected = apply_reservations(loader(), db)
    path = tmp_path / f"{country}.{ext}"
    path.write_text(body, encoding="utf-8")
    assert loader(path) == expected  # the ERP's own view and OneOrder's view agree


# --- reservation ledger ---------------------------------------------------------------------------


def test_reserve_list_and_release_through_the_api(client):
    wh, sku, available = stocked("SE")
    before = reserved_in_native(client, "SE", wh, sku)

    res = client.post("/mock-erp/se/reservations", json={"order_ref": "ord-1", "lines": [{"warehouse": wh, "sku": sku, "quantity": 3}]})
    assert res.status_code == 201 and res.json()["reserved"][0]["quantity"] == 3
    assert reserved_in_native(client, "SE", wh, sku) == before + 3
    assert [r["order_ref"] for r in client.get("/mock-erp/se/reservations").json()] == ["ord-1"]
    assert client.get("/mock-erp/dk/reservations").json() == []  # other countries' ledgers are separate

    released = client.delete("/mock-erp/se/reservations/ord-1")
    assert released.status_code == 200 and released.json()["released"] == 1
    assert reserved_in_native(client, "SE", wh, sku) == before
    assert client.delete("/mock-erp/se/reservations/ord-1").status_code == 404


def test_reservation_beyond_available_is_rejected_and_writes_nothing(client):
    wh, sku, available = stocked("NO")
    res = client.post("/mock-erp/no/reservations", json={"order_ref": "big", "lines": [{"warehouse": wh, "sku": sku, "quantity": available + 1}]})
    assert res.status_code == 409 and "Insufficient stock" in res.json()["detail"]
    assert client.get("/mock-erp/no/reservations").json() == []


def test_reservation_validation(client):
    wh, sku, _ = stocked("DK")
    wrong_country = client.post("/mock-erp/se/reservations", json={"order_ref": "o", "lines": [{"warehouse": wh, "sku": sku, "quantity": 1}]})
    assert wrong_country.status_code == 422 and "not in the SE ERP" in wrong_country.json()["detail"]
    assert client.post("/mock-erp/dk/reservations", json={"order_ref": "o", "lines": []}).status_code == 422
    assert client.post("/mock-erp/dk/reservations", json={"order_ref": "o", "lines": [{"warehouse": wh, "sku": sku, "quantity": 0}]}).status_code == 422
    assert client.post("/mock-erp/xx/reservations", json={"order_ref": "o", "lines": [{"warehouse": wh, "sku": sku, "quantity": 1}]}).status_code == 404


def test_two_lines_on_the_same_stock_are_checked_together(client):
    wh, sku, available = stocked("DK")
    half = available / 2 + 1
    res = client.post("/mock-erp/dk/reservations", json={"order_ref": "o", "lines": [
        {"warehouse": wh, "sku": sku, "quantity": half}, {"warehouse": wh, "sku": sku, "quantity": half}]})
    assert res.status_code == 409


def test_reserve_for_order_is_all_or_nothing_across_countries(session_factory):
    dk_wh, dk_sku, _ = stocked("DK")
    se_wh, se_sku, se_available = stocked("SE")

    def shipment(wh, sku, qty, index):
        return SimpleNamespace(origin_warehouse=wh, shipment_index=index, lines=[SimpleNamespace(sku=sku, quantity=qty, unit=None)])

    with session_factory() as db:
        with pytest.raises(mock_erp.ReservationRejected):
            mock_erp.reserve_for_order(db, "o1", [shipment(dk_wh, dk_sku, 1, 1), shipment(se_wh, se_sku, se_available + 5, 2)])
        db.commit()
        assert db.query(ReservationModel).count() == 0  # DK part was not written either

        total = mock_erp.reserve_for_order(db, "o2", [shipment(dk_wh, dk_sku, 1, 1), shipment(se_wh, se_sku, 1, 2)])
        db.commit()
        assert total == 2 and db.query(ReservationModel).count() == 2


# --- /confirm writes through ----------------------------------------------------------------------


def test_confirm_writes_reservations_into_each_countrys_erp(client):
    path = SAMPLES / "emails" / "dk_order.txt"
    order = client.post("/api/intake", files={"file": (path.name, path.read_bytes(), "text/plain")}).json()
    corrections = [{"line_index": i, "sku": l["matched_sku"] or "GYP-13-2400", "confirmed": True} for i, l in enumerate(order["lines"])]
    assert client.post(f"/api/orders/{order['id']}/approve", json={"corrections": corrections}).status_code == 200
    assert client.post(f"/api/orders/{order['id']}/plan").status_code == 200
    before = {(w, s): reserved_in_native(client, "DK", w, s) for w, s in [("DK-DC-01", "GYP-13-2400")]}

    done = client.post(f"/api/orders/{order['id']}/confirm", json={"accept_late_risk": True, "allow_partial": True})
    assert done.status_code == 200
    in_erps = sum((client.get(f"/mock-erp/{c}/reservations").json() for c in ("dk", "se", "no")), [])
    assert sorted((r["warehouse"], r["sku"], r["quantity"]) for r in in_erps) == sorted(
        (r["warehouse_code"], r["sku"], r["quantity"]) for r in done.json()["reservations"]
    )
    assert all(r["order_ref"] == order["id"] for r in in_erps) and in_erps
    for (w, s), was in before.items():
        planned = sum(r["quantity"] for r in in_erps if (r["warehouse"], r["sku"]) == (w, s))
        assert reserved_in_native(client, "DK", w, s) == was + planned
