"""Sample inbox and the rules API."""

import json
from pathlib import Path
import shutil

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.ai import get_ai_client
from backend.db import Base, get_db
from backend.main import app
from backend.services.intake.demo_client import DemoClient
from backend.services.matching import clear_catalog_cache
from backend.services.orchestration import clear_rules_cache

SAMPLES = Path("samples")


@pytest.fixture
def client(tmp_path, monkeypatch):
    clear_catalog_cache()
    rules = tmp_path / "rules.json"
    shutil.copy("data/rules.json", rules)
    monkeypatch.setenv("RULES_PATH", str(rules))
    clear_rules_cache()
    engine = create_engine(f"sqlite:///{tmp_path / 'ir.db'}", connect_args={"check_same_thread": False})
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
    test_client = TestClient(app)
    test_client.rules_path = rules  # type: ignore[attr-defined]
    yield test_client
    app.dependency_overrides.clear()
    clear_rules_cache()


# --- inbox ----------------------------------------------------------------------------------------


def test_inbox_lists_emails_photos_and_excel(client):
    items = client.get("/api/inbox").json()
    ids = {i["id"] for i in items}
    assert {"emails/dk_order.txt", "photos/dk-handwritten-1.jpg", "excel/dk_materials.xlsx"} <= ids
    by_id = {i["id"]: i for i in items}
    assert by_id["emails/dk_order.txt"]["kind"] == "email" and "bestilling" in by_id["emails/dk_order.txt"]["preview"].lower()
    assert by_id["photos/dk-handwritten-1.jpg"]["kind"] == "image" and by_id["photos/dk-handwritten-1.jpg"]["preview"] is None
    assert by_id["excel/dk_materials.xlsx"]["kind"] == "excel" and by_id["excel/dk_materials.xlsx"]["size_bytes"] > 0


@pytest.mark.parametrize("item", ["emails/dk_order.txt", "photos/dk-handwritten-1.jpg", "excel/dk_materials.xlsx"])
def test_importing_an_inbox_item_creates_a_draft_with_its_original(client, item):
    res = client.post("/api/inbox/import", json={"id": item})
    assert res.status_code == 200, res.text
    order = res.json()
    assert order["status"] == "draft" and order["lines"]
    stored = client.get(f"/api/orders/{order['id']}").json()
    assert stored["has_source"] and stored["source_name"] == Path(item).name
    assert client.get(f"/api/orders/{order['id']}/source").status_code == 200


@pytest.mark.parametrize("bad", ["../README.md", "emails/../../README.md", "emails/nope.txt", "/etc/passwd", ""])
def test_import_only_accepts_listed_items(client, bad):
    assert client.post("/api/inbox/import", json={"id": bad}).status_code == 404


def test_inbox_dir_can_be_pointed_elsewhere(client, tmp_path, monkeypatch):
    monkeypatch.setenv("INBOX_DIR", str(tmp_path / "empty"))
    assert client.get("/api/inbox").json() == []


# --- rules ----------------------------------------------------------------------------------------


def test_get_rules(client):
    body = client.get("/api/rules").json()
    assert body["sourcing"]["priority"] == ["branch", "domestic_dc", "cross_border_dc"]
    assert {v["type"] for v in body["vehicles"]} == {"small_truck", "heavy_truck", "crane_truck"}
    assert body["version"] == 1


def test_put_rules_updates_file_bumps_version_and_keeps_extra_keys(client):
    body = client.get("/api/rules").json()
    body["sourcing"]["max_shipments_per_order"] = 2
    body["sourcing"]["allow_cross_border"] = False
    res = client.put("/api/rules", json=body)
    assert res.status_code == 200 and res.json()["version"] == 2

    again = client.get("/api/rules").json()
    assert again["sourcing"]["max_shipments_per_order"] == 2 and again["sourcing"]["allow_cross_border"] is False
    on_disk = json.loads(client.rules_path.read_text(encoding="utf-8"))
    assert on_disk["version"] == 2 and "description" in on_disk  # the file's own notes survive


def test_put_rules_rejects_invalid_values_and_leaves_the_file_alone(client):
    before = client.rules_path.read_text(encoding="utf-8")
    body = client.get("/api/rules").json()
    body["sourcing"]["priority"] = ["branch", "branch"]
    assert client.put("/api/rules", json=body).status_code == 422
    body = client.get("/api/rules").json()
    body["vehicles"] = [v for v in body["vehicles"] if not v["crane"]]
    assert client.put("/api/rules", json=body).status_code == 422
    assert client.put("/api/rules", json={"vehicles": "x"}).status_code == 422
    assert client.rules_path.read_text(encoding="utf-8") == before


def test_new_plans_use_the_new_rules_version(client):
    body = client.get("/api/rules").json()
    assert client.put("/api/rules", json=body).status_code == 200
    order = client.post("/api/inbox/import", json={"id": "emails/dk_order.txt"}).json()
    corrections = [{"line_index": i, "sku": l["matched_sku"] or "GYP-13-2400", "confirmed": True} for i, l in enumerate(order["lines"])]
    assert client.post(f"/api/orders/{order['id']}/approve", json={"corrections": corrections}).status_code == 200
    assert client.post(f"/api/orders/{order['id']}/plan").json()["rules_version"] == 2
