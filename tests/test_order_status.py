"""Order lifecycle: transition table, /plan and /cancel status changes, audit trail, DB migration."""

from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from backend.ai import get_ai_client
from backend.db import Base, get_db, init_db
from backend.main import app
from backend.services.intake.demo_client import DemoClient
from backend.services.matching import clear_catalog_cache
from backend.services.orders import TRANSITIONS, InvalidTransition, OrderStatus, require_transition

SAMPLES_DIR = Path(__file__).resolve().parents[1] / "samples"
S = OrderStatus

# --- Transition table -----------------------------------------------------------------------------

ALLOWED = {
    (S.DRAFT, S.APPROVED),
    (S.DRAFT, S.CANCELLED),
    (S.APPROVED, S.PLANNED),
    (S.APPROVED, S.CANCELLED),
    (S.PLANNED, S.PLANNED),
    (S.PLANNED, S.CONFIRMED),
    (S.PLANNED, S.CANCELLED),
}


@pytest.mark.parametrize("source", list(S))
@pytest.mark.parametrize("target", list(S))
def test_transition_table(source, target):
    if (source, target) in ALLOWED:
        require_transition(source.value, target)
    else:
        with pytest.raises(InvalidTransition):
            require_transition(source.value, target)


def test_final_statuses_have_no_exit():
    assert TRANSITIONS[S.CONFIRMED] == frozenset() and TRANSITIONS[S.CANCELLED] == frozenset()


def test_unknown_status_rejected():
    with pytest.raises(InvalidTransition, match="unknown status"):
        require_transition("shipped", S.APPROVED)


def test_error_message_lists_allowed_targets():
    with pytest.raises(InvalidTransition, match=r"allowed from 'draft': approved, cancelled"):
        require_transition("draft", S.PLANNED)


# --- API ----------------------------------------------------------------------------------------------


@pytest.fixture
def client(tmp_path):
    clear_catalog_cache()
    engine = create_engine(f"sqlite:///{tmp_path / 'status.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_ai_client] = lambda: DemoClient(SAMPLES_DIR / "fixtures")
    yield TestClient(app)
    app.dependency_overrides.clear()


def new_order(client) -> str:
    path = SAMPLES_DIR / "emails" / "dk_order.txt"
    res = client.post("/api/intake", files={"file": (path.name, path.read_bytes(), "text/plain")})
    assert res.status_code == 200
    return res.json()["id"]


def approve(client, order_id: str) -> None:
    order = client.get(f"/api/orders/{order_id}").json()
    corrections = [
        {"line_index": i, "sku": line["matched_sku"] or "GYP-13-2400", "confirmed": True}
        for i, line in enumerate(order["lines"])
    ]
    assert client.post(f"/api/orders/{order_id}/approve", json={"corrections": corrections}).status_code == 200


def status_of(client, order_id: str) -> str:
    return client.get(f"/api/orders/{order_id}").json()["status"]


def actions(client, order_id: str) -> list[str]:
    return [log["action"] for log in client.get(f"/api/orders/{order_id}").json()["audit_logs"]]


def test_full_lifecycle_draft_to_planned_with_audit_trail(client):
    oid = new_order(client)
    assert status_of(client, oid) == "draft"
    assert client.get(f"/api/orders/{oid}").json()["plan"] is None

    approve(client, oid)
    assert status_of(client, oid) == "approved"

    res = client.post(f"/api/orders/{oid}/plan", json={"user": "anna"})
    assert res.status_code == 200
    order = client.get(f"/api/orders/{oid}").json()
    assert order["status"] == "planned" and order["plan"] == res.json()

    plan_log = next(log for log in order["audit_logs"] if log["action"] == "plan")
    assert plan_log["user"] == "anna"
    assert plan_log["payload_before"] == {"status": "approved", "shipments": None}
    assert plan_log["payload_after"]["status"] == "planned"
    assert plan_log["payload_after"]["shipments"] == len(res.json()["shipments"])
    assert actions(client, oid)[-1] == "plan"


def test_plan_again_overwrites_plan_and_is_logged(client):
    oid = new_order(client)
    approve(client, oid)
    first = client.post(f"/api/orders/{oid}/plan", json={"site_id": "SITE-DK-01"}).json()
    second = client.post(f"/api/orders/{oid}/plan", json={"site_id": "SITE-DK-02"}).json()
    assert first["site"]["id"] == "SITE-DK-01" and second["site"]["id"] == "SITE-DK-02"

    order = client.get(f"/api/orders/{oid}").json()
    assert order["status"] == "planned" and order["plan"]["site"]["id"] == "SITE-DK-02"
    plan_logs = [log for log in order["audit_logs"] if log["action"] == "plan"]
    assert len(plan_logs) == 2
    assert plan_logs[1]["payload_before"] == {"status": "planned", "shipments": len(first["shipments"])}


def test_failed_plan_leaves_order_untouched(client):
    oid = new_order(client)
    approve(client, oid)
    assert client.post(f"/api/orders/{oid}/plan", json={"site_id": "SITE-XX-99"}).status_code == 422
    order = client.get(f"/api/orders/{oid}").json()
    assert order["status"] == "approved" and order["plan"] is None
    assert "plan" not in actions(client, oid)


def test_cannot_plan_draft_order(client):
    oid = new_order(client)
    res = client.post(f"/api/orders/{oid}/plan")
    assert res.status_code == 409
    assert "'draft'" in res.json()["detail"] and "approve the order before planning" in res.json()["detail"]
    assert status_of(client, oid) == "draft"


@pytest.mark.parametrize("start", ["draft", "approved", "planned"])
def test_cancel_from_any_open_status(client, start):
    oid = new_order(client)
    if start != "draft":
        approve(client, oid)
    if start == "planned":
        assert client.post(f"/api/orders/{oid}/plan").status_code == 200

    res = client.post(f"/api/orders/{oid}/cancel", json={"user": "anna", "reason": "customer cancelled"})
    assert res.status_code == 200 and res.json()["status"] == "cancelled"

    log = next(log for log in res.json()["audit_logs"] if log["action"] == "cancel")
    assert log["user"] == "anna"
    assert log["payload_before"] == {"status": start}
    assert log["payload_after"] == {"status": "cancelled", "reason": "customer cancelled"}


def test_cancelled_order_is_final(client):
    oid = new_order(client)
    approve(client, oid)
    plan = client.post(f"/api/orders/{oid}/plan").json()
    assert client.post(f"/api/orders/{oid}/cancel").status_code == 200

    assert client.post(f"/api/orders/{oid}/cancel").status_code == 409
    assert client.post(f"/api/orders/{oid}/plan").status_code == 409
    assert client.post(f"/api/orders/{oid}/approve", json={}).status_code == 409
    order = client.get(f"/api/orders/{oid}").json()
    assert order["status"] == "cancelled"
    assert order["plan"] == plan  # kept for history


def test_cancelled_draft_cannot_be_approved(client):
    oid = new_order(client)
    client.post(f"/api/orders/{oid}/cancel")
    res = client.post(f"/api/orders/{oid}/approve", json={})
    assert res.status_code == 409 and "'cancelled'" in res.json()["detail"]


def test_approve_planned_order_is_rejected(client):
    oid = new_order(client)
    approve(client, oid)
    client.post(f"/api/orders/{oid}/plan")
    res = client.post(f"/api/orders/{oid}/approve", json={})
    assert res.status_code == 409 and status_of(client, oid) == "planned"


def test_cancel_unknown_order(client):
    assert client.post("/api/orders/nope/cancel").status_code == 404


def test_cancel_reason_length_limit(client):
    oid = new_order(client)
    assert client.post(f"/api/orders/{oid}/cancel", json={"reason": "x" * 501}).status_code == 422
    assert status_of(client, oid) == "draft"


# --- Database upgrade ---------------------------------------------------------------------------------


def test_init_db_adds_plan_column_to_old_database(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'old.db'}")
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE orders (id VARCHAR(36) PRIMARY KEY, status VARCHAR(20) NOT NULL)"))
        conn.execute(text("INSERT INTO orders (id, status) VALUES ('a', 'approved')"))
    init_db(engine)
    init_db(engine)  # idempotent
    assert "plan" in {c["name"] for c in inspect(engine).get_columns("orders")}
    with engine.connect() as conn:
        assert conn.execute(text("SELECT status, plan FROM orders")).one() == ("approved", None)
