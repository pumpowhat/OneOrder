"""Simulated Salesforce outages for demos: CRM_MOCK_FAIL and PUT /api/crm/mock-failure."""

from datetime import datetime, timedelta, timezone

import pytest

from backend.crm import CrmPermanentError, CrmRegistry, CrmTransientError, MockSalesforceDirectory, clear_crm_cache
from backend.crm.mock import parse_fail_modes
from backend.services.orders.crm_sync import retry_due
from tests.test_confirm import client, session_factory  # noqa: F401
from tests.test_crm_adapters import _order
from tests.test_crm_sync import confirm, planned_order


@pytest.fixture
def shared_mock(monkeypatch):
    """The app's own mock Salesforce (no dependency override), fed by samples/crm."""
    monkeypatch.setenv("CRM_MODE", "mock")
    monkeypatch.setenv("CRM_MOCK_DIR", "samples/crm")
    monkeypatch.delenv("CRM_MOCK_FAIL", raising=False)
    clear_crm_cache()
    yield
    clear_crm_cache()


@pytest.mark.parametrize(
    ("value", "modes"),
    [(None, set()), ("", set()), ("transient", {"transient"}), (" Search , permanent ", {"search", "permanent"})],
)
def test_parse_fail_modes(value, modes):
    assert parse_fail_modes(value) == modes


@pytest.mark.parametrize("value", ["timeout", "transient,permanent"])
def test_parse_fail_modes_rejects_nonsense(value):
    with pytest.raises(ValueError):
        parse_fail_modes(value)


def test_each_mode_fails_the_matching_call():
    crm = MockSalesforceDirectory([], country="DK")
    crm.fail_modes = {"search"}
    with pytest.raises(CrmTransientError, match="CRM_MOCK_FAIL=search"):
        crm.find_customers("Hoffmann", None)
    assert crm.push_order(_order()).startswith("801")  # writing still works

    crm.fail_modes = {"transient"}
    with pytest.raises(CrmTransientError):
        crm.push_order(_order("ord-2"))
    crm.fail_modes = {"permanent"}
    with pytest.raises(CrmPermanentError):
        crm.push_order(_order("ord-3"))
    crm.fail_modes = set()
    assert crm.push_order(_order("ord-3")).startswith("801")


def test_env_sets_the_starting_outage(shared_mock, monkeypatch):
    monkeypatch.setenv("CRM_MOCK_FAIL", "transient")
    assert CrmRegistry().for_country("DK").fail_modes == {"transient"}


def test_outage_switch_drives_the_whole_demo(client, shared_mock, session_factory):
    status = client.get("/api/crm/status").json()
    assert status == {"mode": "mock", "countries": {"DK": "salesforce"}, "mock_failure": {"DK": []}}

    on = client.put("/api/crm/mock-failure", json={"modes": ["search", "transient"]})
    assert on.status_code == 200 and on.json()["mock_failure"] == {"DK": ["search", "transient"]}

    order = planned_order(client)
    lookup = client.get(f"/api/orders/{order['id']}/customer-candidates").json()
    assert lookup["candidates"] == [] and "outage" in lookup["error"]
    body = confirm(client, order)  # Salesforce is down, the order is confirmed anyway
    assert body["status"] == "confirmed" and body["reservations"] and body["crm_sync"]["status"] == "pending"

    assert client.put("/api/crm/mock-failure", json={"modes": []}).json()["mock_failure"] == {"DK": []}
    db = session_factory()
    try:  # what the background worker does once the back-off has passed
        assert retry_due(db, CrmRegistry(), now=datetime.now(timezone.utc) + timedelta(minutes=1)) == 1
    finally:
        db.close()
    assert client.get(f"/api/orders/{order['id']}").json()["crm_sync"]["status"] == "synced"


def test_rejection_mode_needs_a_person_to_retry(client, shared_mock):
    client.put("/api/crm/mock-failure", json={"modes": ["permanent"]})
    order = planned_order(client)
    assert confirm(client, order)["crm_sync"]["status"] == "failed"
    client.put("/api/crm/mock-failure", json={"modes": []})
    assert client.post(f"/api/orders/{order['id']}/crm-sync/retry").json()["status"] == "synced"


def test_switch_refuses_unknown_modes_and_a_live_crm(client, shared_mock, monkeypatch):
    assert client.put("/api/crm/mock-failure", json={"modes": ["meltdown"]}).status_code == 422
    monkeypatch.setenv("CRM_MODE", "live")
    assert client.put("/api/crm/mock-failure", json={"modes": ["transient"]}).status_code == 409
    assert client.get("/api/crm/status").json()["mode"] == "live"
