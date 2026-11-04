import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.ai import FIXTURE_DIR, get_ai_client
from backend.db import Base, get_db
from backend.main import app
from backend.services.intake.demo_client import DemoClient
from backend.services.intake.schemas import line_needs_review
from backend.services.matching import clear_catalog_cache
from backend.services.orchestration import load_sites, resolve_site

SAMPLES_DIR = Path("samples")
EXPECTED_DIR = SAMPLES_DIR / "expected"

SAMPLE_FILES = [
    ("photos/dk-handwritten-1.jpg", "dk-handwritten-1.jpg", "image/jpeg"),
    ("photos/se-handwritten-1.jpg", "se-handwritten-1.jpg", "image/jpeg"),
    ("photos/no-handwritten-1.jpg", "no-handwritten-1.jpg", "image/jpeg"),
    ("emails/dk_order.txt", "dk_order.txt", "text/plain"),
    ("emails/se_order.txt", "se_order.txt", "text/plain"),
    ("emails/no_order.txt", "no_order.txt", "text/plain"),
    ("emails/en_order.txt", "en_order.txt", "text/plain"),
    ("excel/dk_materials.xlsx", "dk_materials.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("excel/se_material.xlsx", "se_material.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    ("excel/en_boq.xlsx", "en_boq.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
]


@pytest.fixture
def test_db(tmp_path):
    clear_catalog_cache()
    db_file = tmp_path / "test_samples.db"
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
    app.dependency_overrides[get_ai_client] = lambda: DemoClient(FIXTURE_DIR)
    yield TestingSessionLocal
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_db):
    return TestClient(app)


@pytest.mark.parametrize("rel_path, filename, mime_type", SAMPLE_FILES, ids=[f[1] for f in SAMPLE_FILES])
def test_sample_intake_matches_expected(client, rel_path, filename, mime_type):
    file_path = SAMPLES_DIR / rel_path
    assert file_path.exists(), f"Sample file not found: {file_path}"

    expected_path = EXPECTED_DIR / f"{filename}.json"
    assert expected_path.exists(), f"Expected fixture not found: {expected_path}"
    with open(expected_path, encoding="utf-8") as f:
        expected = json.load(f)

    file_bytes = file_path.read_bytes()
    response = client.post(
        "/api/intake",
        files={"file": (filename, file_bytes, mime_type)},
    )
    assert response.status_code == 200, f"Intake failed for {filename}: {response.text}"

    data = response.json()
    assert data["id"] is not None
    assert data["status"] == "draft"
    assert len(data["lines"]) == expected["line_count"], (
        f"Line count mismatch for {filename}: expected {expected['line_count']}, got {len(data['lines'])}"
    )

    # Fetch persisted order from database to check stored needs_review flags
    order_res = client.get(f"/api/orders/{data['id']}")
    assert order_res.status_code == 200
    stored_data = order_res.json()

    for idx, (actual_line, stored_line, exp_line) in enumerate(
        zip(data["lines"], stored_data["lines"], expected["lines"])
    ):
        assert actual_line["matched_sku"] == exp_line["matched_sku"], (
            f"[{filename}] Line {idx + 1} SKU mismatch: expected {exp_line['matched_sku']!r}, "
            f"got {actual_line['matched_sku']!r}"
        )
        assert stored_line["needs_review"] == exp_line["needs_review"], (
            f"[{filename}] Line {idx + 1} needs_review mismatch: expected {exp_line['needs_review']}, "
            f"got {stored_line['needs_review']}"
        )


SAMPLES_WITH_DELIVERY_SITE = [
    ("photos/dk-handwritten-1.jpg", "dk-handwritten-1.jpg", "image/jpeg"),
    ("photos/se-handwritten-1.jpg", "se-handwritten-1.jpg", "image/jpeg"),
    ("photos/no-handwritten-1.jpg", "no-handwritten-1.jpg", "image/jpeg"),
    ("emails/dk_order.txt", "dk_order.txt", "text/plain"),
    ("emails/se_order.txt", "se_order.txt", "text/plain"),
    ("emails/no_order.txt", "no_order.txt", "text/plain"),
]


@pytest.mark.parametrize("rel_path, filename, mime_type", SAMPLES_WITH_DELIVERY_SITE, ids=[f[1] for f in SAMPLES_WITH_DELIVERY_SITE])
def test_sample_delivery_sites_resolve_to_address_match(client, rel_path, filename, mime_type):
    """Every sample email and photo with a delivery_site must resolve to a real site with match_type='address'."""
    file_path = SAMPLES_DIR / rel_path
    file_bytes = file_path.read_bytes()
    response = client.post(
        "/api/intake",
        files={"file": (filename, file_bytes, mime_type)},
    )
    assert response.status_code == 200, f"Intake failed for {filename}: {response.text}"

    data = response.json()
    delivery_site = data.get("delivery_site")
    assert delivery_site, f"Sample {filename} missing delivery_site in intake response"

    sites = load_sites()
    resolved = resolve_site(delivery_site, sites)
    assert resolved is not None, f"Could not resolve site for {filename} with address {delivery_site!r}"
    site, match_type = resolved
    assert match_type == "address", (
        f"Sample {filename} with address {delivery_site!r} resolved by {match_type!r}, expected 'address' (matched site: {site.id})"
    )


def test_approve_sample_email_order_workflow(client):
    """Test full intake -> approve lifecycle for an email order."""
    email_path = SAMPLES_DIR / "emails" / "dk_order.txt"
    email_bytes = email_path.read_bytes()

    intake_res = client.post(
        "/api/intake",
        files={"file": ("dk_order.txt", email_bytes, "text/plain")},
    )
    assert intake_res.status_code == 200
    order_data = intake_res.json()
    order_id = order_data["id"]
    line_count = len(order_data["lines"])
    assert line_count == 5

    # Since rule-based email intake sets confidence=0.75 (< 0.85 threshold),
    # approval without confirmations will be blocked (409 Conflict)
    blocked_res = client.post(f"/api/orders/{order_id}/approve", json={})
    assert blocked_res.status_code == 409

    # Approve with explicit user corrections and line confirmations
    approve_payload = {
        "user": "anna_sales",
        "corrections": [
            {"line_index": 0, "sku": "GYP-13-2400", "confirmed": True},
        ],
        "confirm_lines": [1, 2, 3, 4],
    }
    approve_res = client.post(f"/api/orders/{order_id}/approve", json=approve_payload)
    assert approve_res.status_code == 200

    approved_order = approve_res.json()
    assert approved_order["id"] == order_id
    assert approved_order["status"] == "approved"

    # Verify audit log entries
    audit_logs = approved_order["audit_logs"]
    actions = [log["action"] for log in audit_logs]
    assert "create_draft" in actions
    assert "approve" in actions

    approve_log = next(log for log in audit_logs if log["action"] == "approve")
    assert approve_log["user"] == "anna_sales"
    assert approve_log["payload_before"] == {"status": "draft"}
    assert approve_log["payload_after"] == {"status": "approved"}
