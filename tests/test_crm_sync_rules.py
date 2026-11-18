"""CRM sync rules behind POST /confirm: when an order is synced, the retry schedule, and failures."""

from datetime import datetime, timedelta, timezone

import pytest

from backend.crm import CrmPermanentError, CrmRegistry, CrmTransientError, MockSalesforceDirectory, get_crm_registry
from backend.db import OrderModel
from backend.main import app
from backend.services.orders.crm_sync import BACKOFF_SECONDS, MAX_ATTEMPTS, retry_due
from tests.test_confirm import client, session_factory  # noqa: F401
from tests.test_crm_sync import DK_ACCOUNT, confirm, planned_order


@pytest.fixture
def crm(monkeypatch):
    directory = MockSalesforceDirectory([], country="DK")
    monkeypatch.setitem(app.dependency_overrides, get_crm_registry, lambda: CrmRegistry({"DK": directory}))
    return directory


def actions(client, order_id: str) -> list[str]:
    return [a["action"] for a in client.get(f"/api/orders/{order_id}").json()["audit_logs"]]


def test_synced_order_carries_the_crm_record_and_the_promised_date(client, crm):
    order = planned_order(client)
    body = confirm(client, order)
    sync = body["crm_sync"]
    assert sync["status"] == "synced" and sync["attempts"] == 1 and sync["last_error"] is None
    assert sync["crm_record_id"] == crm.orders[order["id"]]["Id"]
    written = crm.orders[order["id"]]
    assert written["AccountId"] == DK_ACCOUNT and written["Status"] == "Draft"
    p90 = body["plan"]["order_eta"]["p90_date"]
    assert f"Promised (P90): {p90}" in written["Description"] and order["id"] in written["Description"]
    assert "crm_sync" in actions(client, order["id"])


def test_order_delivered_outside_a_crm_country_is_not_written(client, crm):
    body = confirm(client, planned_order(client, "SE"))
    assert crm.orders == {}
    assert body["crm_sync"] == {
        "status": "not_applicable", "reason": "crm_disabled", "crm_record_id": None, "last_error": None,
        "attempts": 0, "last_attempt_at": None, "next_attempt_at": None,
    }


def test_no_account_is_not_applicable_even_in_a_crm_country(client, crm):
    created = client.post("/api/orders", json={
        "customer": "Walk-in Byg", "customer_phone": "+45 12 34 56 78",
        "requested_date": (datetime.now().date() + timedelta(days=30)).isoformat(),
        "lines": [{"sku": "GYP-13-2400", "description": "Plasterboard", "quantity": 1, "confirmed": True}],
    }).json()
    url = f"/api/orders/{created['id']}"
    assert client.post(url + "/approve", json={}).status_code == 200
    assert client.post(url + "/plan", json={"site_id": "SITE-DK-01"}).status_code == 200
    body = confirm(client, created)
    assert (body["crm_sync"]["status"], body["crm_sync"]["reason"]) == ("not_applicable", "no_account")
    assert crm.orders == {}


def test_rejected_order_fails_at_once_and_a_person_can_retry(client, crm):
    crm.failures = [CrmPermanentError("INVALID_CROSS_REFERENCE_KEY: Account not found")]
    order = planned_order(client)
    body = confirm(client, order)
    assert body["status"] == "confirmed" and body["reservations"]
    sync = body["crm_sync"]
    assert sync["status"] == "failed" and sync["attempts"] == 1 and "Account not found" in sync["last_error"]
    assert sync["next_attempt_at"] is None

    retried = client.post(f"/api/orders/{order['id']}/crm-sync/retry")
    assert retried.status_code == 200, retried.text
    assert retried.json()["status"] == "synced" and retried.json()["attempts"] == 1  # a fresh round
    assert {"crm_sync_failed", "crm_sync_retry", "crm_sync"} <= set(actions(client, order["id"]))


def test_temporary_failures_back_off_then_give_up(client, crm, session_factory):
    crm.failures = [CrmTransientError("timeout")] * MAX_ATTEMPTS
    order = planned_order(client)
    first = confirm(client, order)["crm_sync"]
    assert first["status"] == "pending" and first["attempts"] == 1
    last = datetime.fromisoformat(first["last_attempt_at"])
    assert datetime.fromisoformat(first["next_attempt_at"]) - last == timedelta(seconds=BACKOFF_SECONDS[0])

    registry = CrmRegistry({"DK": crm})
    db = session_factory()
    try:
        assert retry_due(db, registry, now=last + timedelta(seconds=BACKOFF_SECONDS[0] - 1)) == 0  # not due yet
        assert retry_due(db, registry, now=last + timedelta(seconds=BACKOFF_SECONDS[0])) == 1
        second = db.get(OrderModel, order["id"])
        assert (second.crm_sync_status, second.crm_sync_attempts) == ("pending", 2)
        wait = second.crm_sync_next_at.replace(tzinfo=timezone.utc) - second.crm_sync_last_at.replace(tzinfo=timezone.utc)
        assert wait == timedelta(seconds=BACKOFF_SECONDS[1])
        assert retry_due(db, registry, now=datetime.now(timezone.utc) + timedelta(hours=1)) == 1
    finally:
        db.close()

    gave_up = client.get(f"/api/orders/{order['id']}").json()["crm_sync"]
    assert gave_up["status"] == "failed" and gave_up["attempts"] == MAX_ATTEMPTS
    assert "gave up after 3 attempts" in gave_up["last_error"] and gave_up["next_attempt_at"] is None
    assert crm.orders == {}


def test_salesforce_retry_after_is_respected(client, crm):
    crm.failures = [CrmTransientError("HTTP 429", retry_after=600)]
    order = planned_order(client)
    sync = confirm(client, order)["crm_sync"]
    wait = datetime.fromisoformat(sync["next_attempt_at"]) - datetime.fromisoformat(sync["last_attempt_at"])
    assert wait == timedelta(seconds=600)


def test_retry_is_refused_when_there_is_nothing_to_retry(client, crm):
    planned = planned_order(client)
    assert client.post(f"/api/orders/{planned['id']}/crm-sync/retry").status_code == 409  # not confirmed yet
    confirm(client, planned)
    assert client.post(f"/api/orders/{planned['id']}/crm-sync/retry").status_code == 409  # already synced
    swedish = planned_order(client, "SE")
    confirm(client, swedish)
    assert client.post(f"/api/orders/{swedish['id']}/crm-sync/retry").status_code == 409  # not for a CRM
    assert client.post("/api/orders/nope/crm-sync/retry").status_code == 404


def test_orders_list_shows_the_sync_state_for_the_dashboard(client, crm):
    crm.failures = [CrmTransientError("timeout")]
    pending = planned_order(client)
    confirm(client, pending)
    draft = planned_order(client)
    rows = {r["id"]: r for r in client.get("/api/orders").json()}
    assert rows[pending["id"]]["crm_sync_status"] == "pending"
    assert rows[draft["id"]]["crm_sync_status"] is None


def test_a_broken_crm_step_never_hides_the_confirmation(client, monkeypatch):
    class Broken(CrmRegistry):
        def system_for(self, country):
            raise RuntimeError("bug in the CRM step")

    monkeypatch.setitem(app.dependency_overrides, get_crm_registry, lambda: Broken())
    order = planned_order(client)
    body = confirm(client, order)
    assert body["status"] == "confirmed" and body["reservations"] and body["crm_sync"] is None
