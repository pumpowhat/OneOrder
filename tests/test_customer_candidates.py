"""Review step: CRM customer suggestions, linking an order to a CRM account, and when that link is dropped."""

import json
from pathlib import Path
import shutil

import pytest

from backend.crm import CrmRegistry, CrmTransientError, MockSalesforceDirectory, clear_crm_cache, get_crm_registry
from backend.crm.matching import is_ambiguous
from backend.main import app
from backend.services.orchestration import clear_rules_cache
from tests.test_orders_api import ai_client, client, test_db  # noqa: F401

ACCOUNTS_CSV = """Name,Phone,BillingCity,ShippingCity
Hoffmann Byg A/S,+45 33 12 45 78,Odense C,Odense C
Hofmann Byg ApS,+45 75 82 11 90,Vejle,Vejle
Lars Byg ApS,+45 70 20 31 31,København S,København
"""
CONTACTS_CSV = """FirstName,LastName,Phone,Email,AccountName
Lars,Nielsen,+45 31 24 56 78,lars@example.invalid,Lars Byg ApS
"""


@pytest.fixture
def crm(tmp_path, monkeypatch):
    """Rules with CRM for DK only, and a mock Salesforce with three known accounts."""
    rules = tmp_path / "rules.json"
    data = json.loads(Path("data/rules.json").read_text(encoding="utf-8"))
    data["crm"] = {"DK": "salesforce", "SE": "none", "NO": "none"}
    rules.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setenv("RULES_PATH", str(rules))
    clear_rules_cache()
    clear_crm_cache()
    crm_dir = tmp_path / "crm"
    crm_dir.mkdir()
    (crm_dir / "accounts.csv").write_text(ACCOUNTS_CSV, encoding="utf-8")
    (crm_dir / "contacts.csv").write_text(CONTACTS_CSV, encoding="utf-8")
    directory = MockSalesforceDirectory.from_csv(crm_dir, "DK")
    app.dependency_overrides[get_crm_registry] = lambda: CrmRegistry({"DK": directory})
    directory.rules_path = rules  # type: ignore[attr-defined]
    yield directory
    app.dependency_overrides.pop(get_crm_registry, None)
    clear_rules_cache()
    clear_crm_cache()


def create(client, **changes) -> dict:
    body = {
        "customer": "Hoffmann Byg A/S",
        "customer_phone": "+45 33 12 45 78",
        "delivery_site": "Havnegade 45, 5000 Odense C",
        "requested_date": "2026-12-20",
        "lines": [{"sku": "GYP-13-2400", "description": "Plasterboard", "quantity": 2, "confirmed": True}],
        **changes,
    }
    res = client.post("/api/orders", json=body)
    assert res.status_code == 201, res.text
    return res.json()


def candidates(client, order_id: str, **params) -> dict:
    res = client.get(f"/api/orders/{order_id}/customer-candidates", params=params)
    assert res.status_code == 200, res.text
    return res.json()


def account_id(directory, name: str) -> str:
    return next(a.account_id for a in directory.accounts if a.name == name)


# --- suggestions -------------------------------------------------------------------------------------


def test_order_customer_is_suggested_from_its_phone(client, crm):
    order = create(client)
    body = candidates(client, order["id"])
    assert (body["crm"], body["countries"], body["error"]) == ("salesforce", ["DK"], None)
    top = body["candidates"][0]
    assert top["name"] == "Hoffmann Byg A/S" and top["matched_on"] == "phone" and top["country"] == "DK"
    assert top["crm_account_id"] == account_id(crm, "Hoffmann Byg A/S") and top["city"] == "Odense C"
    assert body["ambiguous"] is False


def test_search_terms_typed_in_the_form_replace_the_order_values(client, crm):
    order = create(client, customer=None, customer_phone=None)
    assert candidates(client, order["id"])["candidates"] == []  # nothing on the order to search with

    by_contact = candidates(client, order["id"], phone="+4531245678")
    [lars] = by_contact["candidates"]
    assert lars["name"] == "Lars Byg ApS" and lars["crm_contact_id"] and lars["crm_contact_id"].startswith("003")

    by_name = candidates(client, order["id"], name="Hoffman Byg", phone="")
    assert [c["name"] for c in by_name["candidates"]] == ["Hoffmann Byg A/S", "Hofmann Byg ApS"]
    assert by_name["ambiguous"] is True  # a name alone never settles which company it is


def test_swedish_customer_is_not_in_the_danish_crm(client, crm):
    order = create(client, customer="Skanska Sverige AB", customer_phone="+46 70 555 12 34")
    body = candidates(client, order["id"])
    assert body["candidates"] == [] and body["error"] is None


def test_no_country_with_crm_hides_the_feature(client, crm):
    rules = json.loads(crm.rules_path.read_text(encoding="utf-8"))
    rules["crm"] = {"DK": "none"}
    crm.rules_path.write_text(json.dumps(rules), encoding="utf-8")
    clear_rules_cache()
    order = create(client)
    assert candidates(client, order["id"]) == {"crm": "none", "countries": [], "candidates": [], "ambiguous": False, "error": None}


def test_crm_outage_still_answers_so_the_clerk_can_type_the_customer(client, crm, monkeypatch):
    def down(name, phone, limit=5):
        raise CrmTransientError("Salesforce is unavailable (HTTP 503)")

    monkeypatch.setattr(crm, "find_customers", down)
    order = create(client)
    body = candidates(client, order["id"])
    assert body["candidates"] == [] and "DK" in body["error"] and "503" in body["error"]


def test_unknown_order_is_404(client, crm):
    assert client.get("/api/orders/nope/customer-candidates").status_code == 404


# --- linking -----------------------------------------------------------------------------------------


def test_picking_a_suggestion_links_the_order_and_is_audited(client, crm):
    order = create(client, customer=None, customer_phone=None)
    [lars] = candidates(client, order["id"], phone="+45 31 24 56 78")["candidates"]
    res = client.patch(f"/api/orders/{order['id']}", json={
        "customer": lars["name"], "customer_phone": lars["phone"],
        "crm_account_id": lars["crm_account_id"], "crm_contact_id": lars["crm_contact_id"],
    })
    assert res.status_code == 200, res.text
    body = res.json()
    assert (body["crm_account_id"], body["crm_contact_id"]) == (lars["crm_account_id"], lars["crm_contact_id"])
    [link] = [a for a in body["audit_logs"] if a["action"] == "link_crm_account"]
    assert link["payload_before"] == {"crm_account_id": None, "crm_contact_id": None}
    assert link["payload_after"]["crm_account_id"] == lars["crm_account_id"]


def test_new_account_drops_the_previous_contact(client, crm):
    lars, hoffmann = account_id(crm, "Lars Byg ApS"), account_id(crm, "Hoffmann Byg A/S")
    order = create(client, crm_account_id=lars, crm_contact_id="003MK0000000000001")
    body = client.patch(f"/api/orders/{order['id']}", json={"crm_account_id": hoffmann}).json()
    assert (body["crm_account_id"], body["crm_contact_id"]) == (hoffmann, None)


def test_typing_the_customer_by_hand_unlinks(client, crm):
    order = create(client, crm_account_id=account_id(crm, "Hoffmann Byg A/S"))
    body = client.patch(f"/api/orders/{order['id']}", json={"crm_account_id": None, "crm_contact_id": None}).json()
    assert body["crm_account_id"] is None
    assert [a["action"] for a in body["audit_logs"]].count("unlink_crm_account") == 1


@pytest.mark.parametrize(
    ("change", "still_linked"),
    [
        ({"customer": "Bygg Väst AB"}, False),  # another company
        ({"customer_phone": "+45 99 99 99 99"}, False),  # another number
        ({"customer_phone": "+4533124578"}, True),  # same number, other format
        ({"customer": "Hoffmann Byg ApS"}, False),  # A/S and ApS are two legal entities
        ({"customer": "hoffmann byg  A/S"}, True),  # same name, other case and spacing
        ({"delivery_site": "Sundkaj 7, København"}, True),  # not about the customer
    ],
)
def test_changing_the_customer_without_a_new_pick_unlinks(client, crm, change, still_linked):
    order = create(client, crm_account_id=account_id(crm, "Hoffmann Byg A/S"))
    body = client.patch(f"/api/orders/{order['id']}", json=change).json()
    assert (body["crm_account_id"] is not None) is still_linked


@pytest.mark.parametrize(
    "bad",
    [
        {"crm_contact_id": "003MK0000000000001"},  # a contact needs its account
        {"crm_account_id": "not-a-salesforce-id"},
        {"crm_account_id": "001' OR 1=1 --xxxx"},
    ],
)
def test_invalid_links_are_refused(client, crm, bad):
    order = create(client)
    assert client.patch(f"/api/orders/{order['id']}", json=bad).status_code == 422
    assert client.get(f"/api/orders/{order['id']}").json()["crm_account_id"] is None


def test_approval_keeps_the_link_for_the_same_customer_and_drops_it_for_another(client, crm):
    hoffmann = account_id(crm, "Hoffmann Byg A/S")
    same = create(client, customer_phone="+45 33 12 45 78", crm_account_id=hoffmann)
    approved = client.post(f"/api/orders/{same['id']}/approve", json={}).json()
    assert approved["customer_phone"] == "+4533124578" and approved["crm_account_id"] == hoffmann

    other = create(client, crm_account_id=hoffmann)
    approved = client.post(f"/api/orders/{other['id']}/approve", json={"customer": "Lars Byg ApS"}).json()
    assert approved["status"] == "approved" and approved["crm_account_id"] is None
    assert "unlink_crm_account" in [a["action"] for a in approved["audit_logs"]]


# --- the acceptance cases prepared in issue #32 -----------------------------------------------------

CASES = json.loads(Path("tests/fixtures/customer_match_cases.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def sample_crm():
    return MockSalesforceDirectory.from_csv(Path("samples/crm"), "DK")


@pytest.mark.parametrize("case", CASES, ids=[f"{i:02d}-{c['note'][:40]}" for i, c in enumerate(CASES)])
def test_customer_match_cases(sample_crm, case):
    found = sample_crm.find_customers(case["query_name"], case["query_phone"])
    assert (found[0].name if found else None) == case["expected_account"]
    if case["expected_account"] is not None:
        assert is_ambiguous(found) is case["expected_review"]
