"""CRM adapters: customer ranking, the CSV-fed mock, the Salesforce REST adapter and the per-country registry."""

from datetime import date
import json
from pathlib import Path
import shutil

from fastapi.testclient import TestClient
import httpx
import pytest

from backend.crm import (
    CrmAccount,
    CrmContact,
    CrmOrder,
    CrmPermanentError,
    CrmRegistry,
    CrmTransientError,
    MockSalesforceDirectory,
    NoCrmDirectory,
    SalesforceDirectory,
    clear_crm_cache,
    phones_match,
    rank_accounts,
)
from backend.crm.matching import name_ratio, normalize_company
from backend.crm.salesforce import sosl_escape
from backend.main import app
from backend.services.orchestration import clear_rules_cache

ACCOUNTS_CSV = """Name,Phone,BillingStreet,BillingCity,BillingCountry,ShippingStreet,ShippingCity
Hoffmann Byg A/S,+45 33 12 45 78,Havnegade 45,Odense C,Denmark,Havnegade 45,Odense C
Hofmann Byg ApS,+45 75 82 11 90,Søndergade 12,Vejle,Denmark,Søndergade 12,Vejle
Lars Byg ApS,+45 70 20 31 31,Amagerbrogade 101,København S,Denmark,"Sundkaj 7, Nordhavn",København
"""
CONTACTS_CSV = """FirstName,LastName,Phone,Email,AccountName
Mette,Hoffmann,+45 33 12 45 78,mette@example.invalid,Hoffmann Byg A/S
Lars,Nielsen,+45 31 24 56 78,lars@example.invalid,Lars Byg ApS
"""


@pytest.fixture
def crm_dir(tmp_path) -> Path:
    """The Data Import Wizard CSV layout used by samples/crm, with known rows."""
    directory = tmp_path / "crm"
    directory.mkdir()
    (directory / "accounts.csv").write_text(ACCOUNTS_CSV, encoding="utf-8")
    (directory / "contacts.csv").write_text(CONTACTS_CSV, encoding="utf-8")
    return directory


def _order(order_id: str = "ord-1", account_id: str = "001A") -> CrmOrder:
    return CrmOrder(
        order_id=order_id,
        account_id=account_id,
        contact_id=None,
        confirmed_on=date(2026, 11, 20),
        requested_date="2026-11-27",
        expected_date="2026-11-25",
        promised_date="2026-11-26",
        description="OneOrder ord-1",
    )


@pytest.fixture
def rules_file(tmp_path, monkeypatch):
    target = tmp_path / "rules.json"
    shutil.copy("data/rules.json", target)
    monkeypatch.setenv("RULES_PATH", str(target))
    clear_rules_cache()
    clear_crm_cache()
    yield target
    clear_rules_cache()
    clear_crm_cache()


# --- phone and name matching ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("a", "b", "same"),
    [
        ("+45 33 12 45 78", "+4533124578", True),
        ("+45 33 12 45 78", "33 12 45 78", True),  # one side without the country code
        ("0045 33124578", "+45 33-12-45-78", True),
        ("+46 70 123 45 67", "070 123 45 67", False),  # national trunk 0 is a different digit string
        ("+45 33 12 45 78", "+45 33 12 45 79", False),
        ("123", "123", False),  # too short to mean anything
        (None, "+45 33 12 45 78", False),
    ],
)
def test_phones_match(a, b, same):
    assert phones_match(a, b) is same


def test_company_names_compare_without_legal_form():
    assert normalize_company("Hoffmann Byg A/S") == normalize_company("Hoffmann Byg ApS") == "hoffmann byg"
    assert normalize_company("Bygg Väst AB") == "bygg vaest"
    assert name_ratio("Hoffman Byg", "Hoffmann Byg A/S") > 90
    assert name_ratio("Byg", "Hoffmann Byg A/S") < 75  # one shared word is not a match


def _accounts() -> list[CrmAccount]:
    return [
        CrmAccount("001A", "Hoffmann Byg A/S", "DK", phone="+45 33 12 45 78", city="Odense C"),
        CrmAccount("001B", "Hofmann Byg ApS", "DK", phone="+45 75 82 11 90", city="Vejle"),
        CrmAccount(
            "001C",
            "Lars Byg ApS",
            "DK",
            phone="+45 70 20 31 31",
            contacts=(CrmContact("003L", "Lars Nielsen", phone="+45 31 24 56 78"),),
        ),
    ]


def test_phone_match_ranks_above_name_only_match():
    ranked = rank_accounts(_accounts(), "Hofmann Byg", "+45 33 12 45 78")
    assert [c.crm_account_id for c in ranked[:2]] == ["001A", "001B"]
    assert ranked[0].matched_on == "phone" and ranked[0].score >= 0.9
    assert ranked[1].matched_on == "name" and ranked[1].score < 0.9


def test_contact_phone_finds_its_account_and_returns_the_contact():
    [hit] = rank_accounts(_accounts(), None, "+45 31 24 56 78")
    assert (hit.crm_account_id, hit.crm_contact_id, hit.name) == ("001C", "003L", "Lars Byg ApS")
    assert hit.phone == "+45 31 24 56 78"


def test_near_duplicate_names_both_suggested_for_a_person_to_choose():
    ranked = rank_accounts(_accounts(), "Hoffman Byg", None)
    assert {c.crm_account_id for c in ranked} == {"001A", "001B"}
    assert all(c.matched_on == "name" for c in ranked)


def test_nothing_to_search_with_returns_no_candidates():
    assert rank_accounts(_accounts(), None, None) == []
    assert rank_accounts(_accounts(), "  ", "12") == []
    assert rank_accounts(_accounts(), "Skanska Sverige AB", "+46 70 555 12 34") == []


def test_limit_caps_the_list():
    assert len(rank_accounts(_accounts(), "Byg ApS Hofmann Hoffmann Lars", None, limit=1)) <= 1


# --- mock Salesforce --------------------------------------------------------------------------------


def test_mock_reads_the_salesforce_import_csvs(crm_dir):
    crm = MockSalesforceDirectory.from_csv(crm_dir, "DK")
    [hoffmann, *_] = crm.find_customers("Hoffmann Byg A/S", "+4533124578")
    assert hoffmann.name == "Hoffmann Byg A/S" and hoffmann.city == "Odense C" and hoffmann.country == "DK"
    assert hoffmann.crm_account_id.startswith("001") and len(hoffmann.crm_account_id) == 18
    [lars] = crm.find_customers(None, "+45 31 24 56 78")  # the PDF order's phone is Lars's own number
    assert lars.name == "Lars Byg ApS" and lars.crm_contact_id and lars.crm_contact_id.startswith("003")


def test_mock_accepts_ids_given_in_the_csv(tmp_path):
    (tmp_path / "accounts.csv").write_text("Id,Name,Phone\n001XYZ,Test Byg A/S,+45 11 22 33 44\n", encoding="utf-8")
    crm = MockSalesforceDirectory.from_csv(tmp_path)
    assert crm.find_customers(None, "11223344")[0].crm_account_id == "001XYZ"


def test_mock_requires_an_accounts_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        MockSalesforceDirectory.from_csv(tmp_path)


def test_mock_push_is_idempotent_per_order():
    crm = MockSalesforceDirectory(_accounts())
    first = crm.push_order(_order("ord-1"))
    again = crm.push_order(_order("ord-1"))
    other = crm.push_order(_order("ord-2"))
    assert first == again != other and first.startswith("801")
    assert len(crm.orders) == 2 and crm.orders["ord-1"]["AccountId"] == "001A"


def test_mock_can_simulate_an_outage_then_recover():
    crm = MockSalesforceDirectory(_accounts())
    crm.failures = [CrmTransientError("timeout"), CrmPermanentError("bad AccountId")]
    with pytest.raises(CrmTransientError):
        crm.push_order(_order())
    with pytest.raises(CrmPermanentError):
        crm.push_order(_order())
    assert crm.push_order(_order()).startswith("801")


def test_no_crm_adapter_finds_nothing_and_refuses_to_push():
    none = NoCrmDirectory("SE")
    assert none.system == "none" and none.find_customers("Skanska", "+46 70 555 12 34") == []
    with pytest.raises(CrmPermanentError):
        none.push_order(_order())


# --- live Salesforce adapter, against a fake HTTP server --------------------------------------------


class FakeSalesforce:
    """Just enough of the Salesforce REST API to exercise the adapter."""

    def __init__(self):
        self.calls: list[httpx.Request] = []
        self.token_count = 0
        self.responses: dict[str, list[httpx.Response]] = {}  # "METHOD path-prefix" -> queued responses

    def queue(self, key: str, *responses: httpx.Response) -> None:
        self.responses.setdefault(key, []).extend(responses)

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        if request.url.path == "/services/oauth2/token":
            self.token_count += 1
            return httpx.Response(
                200, json={"access_token": f"tok{self.token_count}", "instance_url": "https://acme.my.salesforce.com"}
            )
        for key, queued in self.responses.items():
            method, prefix = key.split(" ", 1)
            if request.method == method and request.url.path.startswith(prefix) and queued:
                return queued.pop(0)
        return httpx.Response(404, json=[{"errorCode": "NOT_FOUND", "message": "no fake for this call"}])


def _sf(fake: FakeSalesforce) -> SalesforceDirectory:
    return SalesforceDirectory(
        "https://login.example.com", "cid", "secret", country="DK", http=httpx.Client(transport=httpx.MockTransport(fake))
    )


def test_salesforce_requires_configuration():
    with pytest.raises(CrmPermanentError):
        SalesforceDirectory("", "", "")


def test_salesforce_search_merges_accounts_and_contacts():
    fake = FakeSalesforce()
    fake.queue(
        "GET /services/data/v62.0/search",
        httpx.Response(200, json={"searchRecords": [
            {"attributes": {"type": "Contact"}, "Id": "003L", "Name": "Lars Nielsen", "Phone": "+45 31 24 56 78",
             "AccountId": "001C", "Account": {"Name": "Lars Byg ApS", "Phone": "+45 70 20 31 31", "ShippingCity": "København"}},
        ]}),
        httpx.Response(200, json={"searchRecords": [
            {"attributes": {"type": "Account"}, "Id": "001C", "Name": "Lars Byg ApS", "Phone": "+45 70 20 31 31"},
        ]}),
    )
    [hit] = _sf(fake).find_customers("Lars Byg", "+45 31 24 56 78")
    assert (hit.crm_account_id, hit.crm_contact_id, hit.city, hit.matched_on) == ("001C", "003L", "København", "phone")
    searches = [c for c in fake.calls if c.url.path.endswith("/search/")]
    assert "IN PHONE FIELDS" in searches[0].url.params["q"] and "31245678" in searches[0].url.params["q"]
    assert "IN NAME FIELDS" in searches[1].url.params["q"]
    assert searches[0].headers["Authorization"] == "Bearer tok1"


def test_salesforce_logs_in_again_when_the_session_expires():
    fake = FakeSalesforce()
    fake.queue(
        "GET /services/data/v62.0/search",
        httpx.Response(401, json=[{"errorCode": "INVALID_SESSION_ID"}]),
        httpx.Response(200, json={"searchRecords": []}),
    )
    assert _sf(fake).find_customers("Hoffmann", None) == []
    assert fake.token_count == 2


def test_salesforce_rate_limit_is_transient_with_retry_after():
    fake = FakeSalesforce()
    fake.queue("PATCH /services/data/v62.0/sobjects/Order", httpx.Response(429, headers={"Retry-After": "30"}))
    with pytest.raises(CrmTransientError) as err:
        _sf(fake).push_order(_order())
    assert err.value.retry_after == 30


def test_salesforce_validation_error_is_permanent():
    fake = FakeSalesforce()
    fake.queue(
        "PATCH /services/data/v62.0/sobjects/Order",
        httpx.Response(400, json=[{"errorCode": "INVALID_FIELD", "message": "No such column 'OneOrder_Id__c'"}]),
    )
    with pytest.raises(CrmPermanentError, match="INVALID_FIELD"):
        _sf(fake).push_order(_order())


def test_salesforce_push_upserts_on_the_external_id():
    fake = FakeSalesforce()
    fake.queue("PATCH /services/data/v62.0/sobjects/Order", httpx.Response(201, json={"id": "801NEW", "created": True}))
    assert _sf(fake).push_order(_order("ord-7")) == "801NEW"
    patch = next(c for c in fake.calls if c.method == "PATCH")
    assert patch.url.path.endswith("/sobjects/Order/OneOrder_Id__c/ord-7")
    body = json.loads(patch.content)
    assert body["AccountId"] == "001A" and body["Status"] == "Draft" and body["EffectiveDate"] == "2026-11-20"


def test_salesforce_update_without_body_reads_the_id_back():
    fake = FakeSalesforce()
    fake.queue("PATCH /services/data/v62.0/sobjects/Order", httpx.Response(204))
    fake.queue("GET /services/data/v62.0/sobjects/Order", httpx.Response(200, json={"Id": "801OLD"}))
    assert _sf(fake).push_order(_order()) == "801OLD"


def test_salesforce_network_failure_is_transient():
    def broken(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out", request=request)

    crm = SalesforceDirectory("https://login.example.com", "cid", "secret", http=httpx.Client(transport=httpx.MockTransport(broken)))
    with pytest.raises(CrmTransientError):
        crm.find_customers("Hoffmann", None)


def test_sosl_escape_neutralises_operators():
    assert sosl_escape('Byg & Co (DK) "A/S"') == 'Byg \\& Co \\(DK\\) \\"A/S\\"'


# --- registry and rules -----------------------------------------------------------------------------


def test_registry_follows_the_crm_block_in_rules(rules_file, crm_dir, monkeypatch):
    monkeypatch.setenv("CRM_MODE", "mock")
    monkeypatch.setenv("CRM_MOCK_DIR", str(crm_dir))
    registry = CrmRegistry()
    assert registry.enabled_countries() == ["DK"]
    assert registry.system_for("dk") == "salesforce" and registry.system_for("SE") == "none"
    assert registry.system_for(None) == "none"
    assert isinstance(registry.for_country("DK"), MockSalesforceDirectory)
    assert registry.for_country("DK") is registry.for_country("DK")  # one mock per process keeps its pushes
    assert isinstance(registry.for_country("SE"), NoCrmDirectory)


def test_registry_overrides_replace_the_adapter(rules_file):
    fake = MockSalesforceDirectory(_accounts())
    assert CrmRegistry({"dk": fake}).for_country("DK") is fake


def test_rules_api_exposes_and_validates_the_crm_block(rules_file):
    client = TestClient(app)
    rules = client.get("/api/rules").json()
    assert rules["crm"] == {"DK": "salesforce", "SE": "none", "NO": "none"}

    bad = client.put("/api/rules", json={**rules, "crm": {"DK": "dynamics365"}})
    assert bad.status_code == 422
    bad_code = client.put("/api/rules", json={**rules, "crm": {"Denmark": "salesforce"}})
    assert bad_code.status_code == 422

    saved = client.put("/api/rules", json={**rules, "crm": {"dk": "none", "SE": "salesforce"}}).json()
    assert saved["crm"] == {"DK": "none", "SE": "salesforce"}


def test_rules_saved_by_an_older_client_keep_the_crm_block(rules_file):
    client = TestClient(app)
    rules = client.get("/api/rules").json()
    rules.pop("crm")
    saved = client.put("/api/rules", json=rules).json()
    assert saved["crm"] == {"DK": "salesforce", "SE": "none", "NO": "none"}
    assert json.loads(rules_file.read_text(encoding="utf-8"))["crm"]["DK"] == "salesforce"
