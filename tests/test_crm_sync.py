"""CRM sync at confirm: acceptance tests prepared in issue #32 (Khang), wired to the backend in D4.

The adapter below is the real mock Salesforce with a switch for an outage. It records every write it is asked
to make, so the tests can check that the OneOrder order id is the only key ever used (no duplicate CRM orders).
"""

from datetime import date, timedelta

import pytest

from backend.crm import CrmOrder, CrmRegistry, CrmTransientError, MockSalesforceDirectory, get_crm_registry
from backend.main import app
from tests.test_confirm import client, session_factory  # noqa: F401

DK_ACCOUNT = "001MK0000000000001"  # a CRM customer picked at review (a well-formed Salesforce id)


class MockCRMAdapter(MockSalesforceDirectory):
    """Salesforce-like unique External ID store, with a controllable outage."""

    def __init__(self):
        super().__init__([], country="DK")
        self.available = True
        self.records = {}
        self.attempted_external_ids = []

    def push_order(self, order: CrmOrder) -> str:
        self.attempted_external_ids.append(order.order_id)
        if not self.available:
            raise CrmTransientError("Simulated Salesforce outage")
        record_id = super().push_order(order)
        self.records[order.order_id] = self.orders[order.order_id]
        return record_id


@pytest.fixture
def mock_crm(monkeypatch):
    adapter = MockCRMAdapter()
    monkeypatch.setitem(app.dependency_overrides, get_crm_registry, lambda: CrmRegistry({"DK": adapter}))
    return adapter


def planned_order(client, country="DK") -> dict:
    customers = {
        "DK": ("Hoffmann Byg A/S", "+45 33 12 45 78"),
        "SE": ("Bygg Väst AB", "+46 70 123 45 67"),
        "NO": ("Testkunde NO", "+47 00 00 00 01"),
    }
    customer, phone = customers[country]
    created = client.post("/api/orders", json={
        "customer": customer,
        "customer_phone": phone,
        **({"crm_account_id": DK_ACCOUNT} if country == "DK" else {}),
        "requested_date": (date.today() + timedelta(days=30)).isoformat(),
        "lines": [{"sku": "GYP-13-2400", "description": "Plasterboard",
                   "quantity": 1, "confirmed": True}],
    })
    assert created.status_code == 201, created.text
    order = created.json()
    url = f"/api/orders/{order['id']}"
    approved = client.post(url + "/approve", json={})
    assert approved.status_code == 200, approved.text
    planned = client.post(url + "/plan", json={"site_id": f"SITE-{country}-01"})
    assert planned.status_code == 200, planned.text
    return order


def confirm(client, order):
    result = client.post(f"/api/orders/{order['id']}/confirm")
    assert result.status_code == 200, result.text
    assert result.json()["status"] == "confirmed"
    return result.json()


def assert_one_crm_order(adapter, order):
    # A random/new External ID on a repeated request would fail these checks.
    assert set(adapter.records) == {order["id"]}
    assert set(adapter.attempted_external_ids) == {order["id"]}


def test_dk_confirm_syncs_order(client, mock_crm):
    order = planned_order(client)
    body = confirm(client, order)
    assert body["crm_sync"]["status"] == "synced"
    assert body["reservations"]
    assert_one_crm_order(mock_crm, order)


def test_crm_outage_keeps_confirm_and_stock_reservations(client, mock_crm):
    mock_crm.available = False
    order = planned_order(client)
    body = confirm(client, order)
    assert body["crm_sync"]["status"] == "pending"
    assert body["reservations"]
    stored = client.get(f"/api/orders/{order['id']}").json()
    assert stored["status"] == "confirmed"
    assert stored["crm_sync"]["status"] == "pending"
    assert stored["reservations"] == body["reservations"]
    assert mock_crm.records == {}
    assert mock_crm.attempted_external_ids == [order["id"]]


def test_retry_after_recovery_syncs_without_reserving_again(client, mock_crm):
    mock_crm.available = False
    order = planned_order(client)
    confirmed = confirm(client, order)
    assert confirmed["crm_sync"]["status"] == "pending"
    mock_crm.available = True
    retried = client.post(f"/api/orders/{order['id']}/crm-sync/retry")
    assert retried.status_code == 200, retried.text
    stored = client.get(f"/api/orders/{order['id']}").json()
    assert stored["crm_sync"]["status"] == "synced"
    assert stored["status"] == "confirmed"
    assert stored["reservations"] == confirmed["reservations"]
    assert_one_crm_order(mock_crm, order)


def test_confirm_twice_does_not_duplicate_salesforce_order(client, mock_crm):
    order = planned_order(client)
    confirmed = confirm(client, order)
    repeated = client.post(f"/api/orders/{order['id']}/confirm")
    assert repeated.status_code == 409, repeated.text
    stored = client.get(f"/api/orders/{order['id']}").json()
    assert stored["crm_sync"]["status"] == "synced"
    assert stored["reservations"] == confirmed["reservations"]
    assert_one_crm_order(mock_crm, order)


def test_retry_twice_uses_order_id_and_does_not_duplicate(client, mock_crm):
    mock_crm.available = False
    order = planned_order(client)
    confirmed = confirm(client, order)
    mock_crm.available = True
    url = f"/api/orders/{order['id']}/crm-sync/retry"
    first = client.post(url)
    assert first.status_code == 200, first.text
    # An already-synced retry may be a no-op (200) or a state guard (409).
    second = client.post(url)
    assert second.status_code in (200, 409), second.text
    stored = client.get(f"/api/orders/{order['id']}").json()
    assert stored["crm_sync"]["status"] == "synced"
    assert stored["reservations"] == confirmed["reservations"]
    assert_one_crm_order(mock_crm, order)


@pytest.mark.parametrize("country", ["SE", "NO"])
def test_non_dk_confirm_does_not_call_crm(client, mock_crm, country):
    order = planned_order(client, country)
    body = confirm(client, order)
    assert body["crm_sync"]["status"] == "not_applicable"
    assert body["reservations"]
    assert mock_crm.attempted_external_ids == []
    assert mock_crm.records == {}
