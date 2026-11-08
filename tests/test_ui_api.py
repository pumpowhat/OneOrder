"""Read-only endpoints behind the UI: orders list, original file, line availability and group stock."""

from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.ai import get_ai_client
from backend.db import Base, get_db
from backend.main import app
from backend.services.intake.demo_client import DemoClient
from backend.services.matching import clear_catalog_cache

SAMPLES = Path("samples")


@pytest.fixture
def client(tmp_path):
    clear_catalog_cache()
    engine = create_engine(f"sqlite:///{tmp_path / 'ui.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_ai_client] = lambda: DemoClient(SAMPLES / "fixtures")
    yield TestClient(app)
    app.dependency_overrides.clear()


def upload(client, rel: str, mime: str) -> dict:
    path = SAMPLES / rel
    res = client.post("/api/intake", files={"file": (path.name, path.read_bytes(), mime)})
    assert res.status_code == 200, res.text
    return res.json()


XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def test_list_orders_newest_first_with_summary_and_status_filter(client):
    first = upload(client, "emails/dk_order.txt", "text/plain")
    second = upload(client, "emails/se_order.txt", "text/plain")
    rows = client.get("/api/orders").json()
    assert [r["id"] for r in rows] == [second["id"], first["id"]]
    row = rows[1]
    assert row["status"] == "draft" and row["customer"] == first["customer"]
    assert row["line_count"] == len(first["lines"])
    stored = client.get(f"/api/orders/{first['id']}").json()
    assert row["review_lines"] == sum(1 for l in stored["lines"] if l["needs_review"])
    assert row["risk"] is None and row["p90_date"] is None

    assert len(client.get("/api/orders", params={"status": "draft"}).json()) == 2
    assert client.get("/api/orders", params={"status": "approved"}).json() == []


def test_list_shows_eta_after_planning(client):
    order = upload(client, "emails/dk_order.txt", "text/plain")
    corrections = [
        {"line_index": i, "sku": l["matched_sku"] or "GYP-13-2400", "confirmed": True}
        for i, l in enumerate(order["lines"])
    ]
    assert client.post(f"/api/orders/{order['id']}/approve", json={"corrections": corrections, "customer_phone": "+45 00 00 00 01"}).status_code == 200
    assert client.post(f"/api/orders/{order['id']}/plan").status_code == 200
    row = client.get("/api/orders").json()[0]
    assert row["status"] == "planned" and row["shipment_count"] >= 1
    assert row["p50_date"] <= row["p90_date"] and row["risk"] in {"on_time", "at_risk", "late"}


def test_source_of_email_image_and_excel(client):
    email = upload(client, "emails/dk_order.txt", "text/plain")
    src = client.get(f"/api/orders/{email['id']}/source").json()
    assert src["kind"] == "text" and "Sundkaj 7" in src["text"]

    photo = upload(client, "photos/dk-handwritten-1.jpg", "image/jpeg")
    assert client.get(f"/api/orders/{photo['id']}/source").json()["kind"] == "image"
    raw = client.get(f"/api/orders/{photo['id']}/source/file")
    assert raw.status_code == 200 and raw.headers["content-type"] == "image/jpeg"
    assert raw.content == (SAMPLES / "photos/dk-handwritten-1.jpg").read_bytes()

    excel = upload(client, "excel/dk_materials.xlsx", XLSX)
    src = client.get(f"/api/orders/{excel['id']}/source").json()
    assert src["kind"] == "table" and len(src["rows"]) >= 2


def test_pasted_text_is_stored_as_source(client):
    res = client.post("/api/intake", data={"text": (SAMPLES / "emails/dk_order.txt").read_text(encoding="utf-8")})
    assert res.status_code == 200
    assert client.get(f"/api/orders/{res.json()['id']}/source").json()["kind"] == "text"


def test_source_errors(client):
    assert client.get("/api/orders/nope/source").status_code == 404
    assert client.get("/api/orders/nope/source/file").status_code == 404


def test_availability_per_line(client):
    order = upload(client, "emails/dk_order.txt", "text/plain")
    rows = client.get(f"/api/orders/{order['id']}/availability").json()
    assert len(rows) == len(order["lines"])
    for row, line in zip(rows, order["lines"]):
        assert row["requested"] == line["quantity"]
        if line["matched_sku"]:
            assert row["status"] in {"ok", "partial", "none"}
            assert row["available"] == pytest.approx(sum(row["by_country"].values()))
        else:
            assert row["status"] == "unmatched"
    assert any(r["status"] == "ok" for r in rows)
    assert client.get("/api/orders/nope/availability").status_code == 404


def test_stock_overview_and_filters(client):
    body = client.get("/api/stock").json()
    assert body["total"] == len(body["items"]) > 100
    assert set(body["summary"]) == {"DK", "SE", "NO"}
    item = body["items"][0]
    assert {"sku", "name", "unit", "by_country", "warehouses", "total_available", "level", "single_country"} <= set(item)
    assert item["total_available"] == pytest.approx(sum(c["available"] for c in item["by_country"].values()))
    assert item["level"] in {"ok", "low", "out"}

    only_no = client.get("/api/stock", params={"country": "no"}).json()
    assert 0 < only_no["total"] <= body["total"]
    assert all(i["by_country"]["NO"]["on_hand"] > 0 for i in only_no["items"])

    one = client.get("/api/stock", params={"q": item["sku"][:6]}).json()
    assert any(i["sku"] == item["sku"] for i in one["items"])

    issues = client.get("/api/stock", params={"only_issues": True}).json()
    assert all(i["level"] != "ok" for i in issues["items"])

    assert client.get("/api/stock", params={"country": "FR"}).status_code == 422


def test_stock_reflects_confirmed_reservations(client):
    before = {i["sku"]: i["total_available"] for i in client.get("/api/stock").json()["items"]}
    order = upload(client, "emails/dk_order.txt", "text/plain")
    corrections = [
        {"line_index": i, "sku": l["matched_sku"] or "GYP-13-2400", "confirmed": True}
        for i, l in enumerate(order["lines"])
    ]
    client.post(f"/api/orders/{order['id']}/approve", json={"corrections": corrections, "customer_phone": "+45 00 00 00 01"})
    client.post(f"/api/orders/{order['id']}/plan")
    done = client.post(f"/api/orders/{order['id']}/confirm", json={"accept_late_risk": True, "allow_partial": True})
    assert done.status_code == 200
    reserved = done.json()["reservations"]
    assert reserved
    after = {i["sku"]: i["total_available"] for i in client.get("/api/stock").json()["items"]}
    sku = reserved[0]["sku"]
    assert after[sku] < before[sku]


def test_sites_endpoint(client):
    sites = client.get("/api/sites").json()
    assert len(sites) == 10
    assert {"id", "name", "country", "address", "crane_accessible"} <= set(sites[0])
