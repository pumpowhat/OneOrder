"""Orchestration engine: sourcing priority, line splitting, vehicles, sites, rules and the /plan API."""

import json
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db import Base, get_db
from backend.erp import UnifiedStockItem, get_group_inventory
from backend.main import app
from backend.ai import get_ai_client
from backend.services.intake.demo_client import DemoClient
from backend.services.matching import clear_catalog_cache
from backend.services.orchestration import (
    PlanLineInput,
    PlanningError,
    ProductLogistics,
    Rules,
    Site,
    Warehouse,
    choose_vehicle,
    load_products,
    load_rules,
    load_sites,
    load_warehouses,
    plan_fulfillment,
    resolve_site,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLES_DIR = REPO_ROOT / "samples"

# --- Small synthetic network around a Copenhagen site -------------------------------------------

SITE = Site("SITE-DK-T", "Test site", "DK", "Teststrasse 1, 2100 København", 55.70, 12.58, True)
NO_CRANE_SITE = Site("SITE-DK-N", "No crane", "DK", "Smalgade 2, 2100 København", 55.70, 12.58, False)

WAREHOUSES = (
    Warehouse("DK-BR-NEAR", "Near branch", "DK", "branch", 55.69, 12.57),  # ~1.5 km
    Warehouse("DK-BR-MID", "Mid branch", "DK", "branch", 55.60, 12.40),  # ~20 km
    Warehouse("DK-BR-FAR", "Far branch", "DK", "branch", 57.05, 9.92),  # Aalborg, >150 km
    Warehouse("DK-DC-01", "DK DC", "DK", "dc", 55.65, 12.30),
    Warehouse("SE-BR-01", "SE branch", "SE", "branch", 55.60, 13.00),  # Malmö: foreign branch
    Warehouse("SE-DC-01", "SE DC", "SE", "dc", 59.33, 18.06),
)

PRODUCTS = {
    "GYP": ProductLogistics("GYP", "Gipsplade 13mm", "stk", 25.0, False),
    "BEAM": ProductLogistics("BEAM", "Limtræsbjælke", "stk", 400.0, True),
    "RARE": ProductLogistics("RARE", "Granite slab", "stk", 50.0, False),
}

RULES = Rules.model_validate(json.loads((REPO_ROOT / "data" / "rules.json").read_text(encoding="utf-8")))


def stock(*rows: tuple[str, str, float]) -> list[UnifiedStockItem]:
    return [UnifiedStockItem(sku, wh, wh.split("-")[0], qty, 0, qty, "stk") for sku, wh, qty in rows]


def line(sku: str, qty: float, index: int = 0) -> PlanLineInput:
    return PlanLineInput(line_index=index, sku=sku, quantity=qty)


def plan(lines, inventory, rules=RULES, site=SITE, match="address"):
    return plan_fulfillment(lines, site, match, inventory, WAREHOUSES, PRODUCTS, rules)


def rules_with(**sourcing) -> Rules:
    data = RULES.model_dump()
    data["sourcing"].update(sourcing)
    return Rules.model_validate(data)


# --- Sourcing priority ----------------------------------------------------------------------------


def test_nearest_branch_with_full_stock_wins():
    p = plan([line("GYP", 10)], stock(("GYP", "DK-BR-NEAR", 50), ("GYP", "DK-BR-MID", 50), ("GYP", "DK-DC-01", 999)))
    assert [s.origin_warehouse for s in p.shipments] == ["DK-BR-NEAR"]
    alloc = p.shipments[0].lines[0]
    assert alloc.tier == "branch" and alloc.reason_code == "branch_full"
    assert "Nearest branch" in alloc.reason
    assert p.fully_sourced and not p.shortages


def test_domestic_dc_before_cross_border():
    p = plan([line("GYP", 100)], stock(("GYP", "DK-BR-NEAR", 5), ("GYP", "DK-DC-01", 200), ("GYP", "SE-DC-01", 999)))
    assert [s.origin_warehouse for s in p.shipments] == ["DK-DC-01"]
    assert p.shipments[0].lines[0].reason_code == "domestic_dc_full"
    assert "no branch within 150 km had the full quantity" in p.shipments[0].lines[0].reason


def test_cross_border_dc_for_item_only_abroad():
    p = plan([line("RARE", 4)], stock(("RARE", "SE-DC-01", 10)))
    s = p.shipments[0]
    assert s.origin_warehouse == "SE-DC-01" and s.tier == "cross_border_dc"
    assert s.cross_border and s.origin_country == "SE" and s.destination_country == "DK"


def test_full_source_further_down_beats_splitting():
    """A domestic DC that holds everything is preferred over splitting across branch + DC."""
    p = plan([line("GYP", 100)], stock(("GYP", "DK-BR-NEAR", 60), ("GYP", "DK-DC-01", 500)))
    assert [(s.origin_warehouse, s.lines[0].quantity) for s in p.shipments] == [("DK-DC-01", 100)]


def test_split_when_no_single_warehouse_has_enough():
    p = plan([line("GYP", 100)], stock(("GYP", "DK-BR-NEAR", 30), ("GYP", "DK-DC-01", 50), ("GYP", "SE-DC-01", 40)))
    taken = [(s.origin_warehouse, s.lines[0].quantity) for s in p.shipments]
    assert taken == [("DK-BR-NEAR", 30), ("DK-DC-01", 50), ("SE-DC-01", 20)]
    assert all(s.lines[0].reason_code.endswith("_partial") for s in p.shipments)
    assert p.fully_sourced


def test_split_disabled_reports_shortage():
    p = plan(
        [line("GYP", 100)],
        stock(("GYP", "DK-BR-NEAR", 60), ("GYP", "DK-DC-01", 60)),
        rules=rules_with(allow_line_split=False),
    )
    assert not p.shipments and not p.fully_sourced
    assert p.shortages[0].missing == 100
    assert "splitting is disabled" in p.shortages[0].reason


def test_shortage_when_group_stock_too_low():
    p = plan([line("GYP", 100)], stock(("GYP", "DK-BR-NEAR", 30), ("GYP", "DK-DC-01", 20)))
    assert p.shortages[0].allocated == 50 and p.shortages[0].missing == 50
    assert not p.fully_sourced
    assert any("cannot be fully sourced" in w for w in p.warnings)


def test_far_and_foreign_branches_are_never_used():
    p = plan([line("GYP", 10)], stock(("GYP", "DK-BR-FAR", 999), ("GYP", "SE-BR-01", 999)))
    assert not p.shipments and p.shortages[0].missing == 10


def test_cross_border_disabled():
    p = plan([line("RARE", 4)], stock(("RARE", "SE-DC-01", 10)), rules=rules_with(allow_cross_border=False))
    assert not p.shipments and p.shortages


def test_priority_order_comes_from_rules():
    p = plan(
        [line("GYP", 10)],
        stock(("GYP", "DK-BR-NEAR", 50), ("GYP", "DK-DC-01", 50)),
        rules=rules_with(priority=["domestic_dc", "branch"]),
    )
    assert p.shipments[0].origin_warehouse == "DK-DC-01"


def test_lines_of_same_sku_do_not_double_book_stock():
    p = plan([line("GYP", 40, 0), line("GYP", 40, 1)], stock(("GYP", "DK-BR-NEAR", 50), ("GYP", "DK-DC-01", 50)))
    sources = {a.line_index: s.origin_warehouse for s in p.shipments for a in s.lines}
    assert sources == {0: "DK-BR-NEAR", 1: "DK-DC-01"}


def test_prefers_warehouse_already_in_the_order():
    """Second line could come from a nearer branch, but DK-BR-MID already ships line 0."""
    p = plan(
        [line("BEAM", 1, 0), line("GYP", 10, 1)],
        stock(("BEAM", "DK-BR-MID", 5), ("GYP", "DK-BR-NEAR", 50), ("GYP", "DK-BR-MID", 50)),
    )
    assert {s.origin_warehouse for s in p.shipments} == {"DK-BR-MID"}
    gyp = next(a for s in p.shipments for a in s.lines if a.sku == "GYP")
    assert "already ships this order" in gyp.reason


# --- Shipments and vehicles -----------------------------------------------------------------------


def test_crane_goods_get_their_own_crane_shipment():
    p = plan([line("BEAM", 2, 0), line("GYP", 100, 1)], stock(("BEAM", "DK-DC-01", 9), ("GYP", "DK-DC-01", 999)))
    by_crane = {s.crane_required: s for s in p.shipments}
    assert by_crane[True].vehicle_type == "crane_truck" and by_crane[True].total_weight_kg == 800
    assert by_crane[False].vehicle_type == "heavy_truck" and by_crane[False].total_weight_kg == 2500
    assert {s.origin_warehouse for s in p.shipments} == {"DK-DC-01"}
    assert p.total_weight_kg == 3300


@pytest.mark.parametrize(
    ("weight", "crane", "expected"),
    [
        (100, False, ("small_truck", 1)),
        (1500, False, ("small_truck", 1)),
        (1501, False, ("heavy_truck", 1)),
        (30000, False, ("heavy_truck", 3)),
        (800, True, ("crane_truck", 1)),
        (25000, True, ("crane_truck", 3)),
    ],
)
def test_choose_vehicle(weight, crane, expected):
    assert choose_vehicle(weight, crane, RULES) == expected


def test_multi_trip_and_crane_site_warnings():
    p = plan([line("GYP", 600), line("BEAM", 1, 1)], stock(("GYP", "DK-DC-01", 999), ("BEAM", "DK-DC-01", 9)),
             site=NO_CRANE_SITE)
    assert any("needs 2 x heavy_truck" in w for w in p.warnings)
    assert any("not crane accessible" in w for w in p.warnings)


def test_too_many_shipments_warning():
    p = plan([line("GYP", 100)], stock(("GYP", "DK-BR-NEAR", 30), ("GYP", "DK-DC-01", 50), ("GYP", "SE-DC-01", 40)),
             rules=rules_with(max_shipments_per_order=2))
    assert any("above the limit of 2" in w for w in p.warnings)


def test_unknown_sku_raises():
    with pytest.raises(PlanningError, match="NOPE"):
        plan([line("NOPE", 1)], [])


def test_fractional_quantities():
    p = plan([line("GYP", 12.5)], stock(("GYP", "DK-BR-NEAR", 12.5)))
    assert p.shipments[0].lines[0].quantity == 12.5 and p.fully_sourced


# --- Rules file ------------------------------------------------------------------------------------


def test_rules_file_is_valid():
    rules = load_rules()
    assert rules.sourcing.priority == ["branch", "domestic_dc", "cross_border_dc"]
    assert rules.intake.min_confidence == 0.85


@pytest.mark.parametrize(
    "patch",
    [
        {"sourcing": {"priority": ["branch", "moon_dc"]}},
        {"sourcing": {"priority": ["branch", "branch"]}},
        {"vehicles": [{"type": "small_truck", "max_weight_kg": 1000, "crane": False}]},
    ],
)
def test_invalid_rules_rejected(patch):
    data = RULES.model_dump()
    for key, value in patch.items():
        data[key] = {**data[key], **value} if isinstance(value, dict) else value
    with pytest.raises(ValueError):
        Rules.model_validate(data)


# --- Site resolution and real data -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Sundkaj 7, 2150 Nordhavn, København", ("SITE-DK-01", "address")),
        ("Pasteurs Vej 24, 1799 København V", ("SITE-DK-02", "address")),
        ("Solnavägen 12, 113 65 Stockholm", ("SITE-SE-01", "address")),
        ("Leveres til Carlsberg Byen Karré 11 Boliger", ("SITE-DK-02", "address")),
        ("Stenersgata 1, 0184 Oslo", ("SITE-NO-01", "city")),
        ("Amager Strandvej 12", None),
        ("", None),
        (None, None),
    ],
)
def test_resolve_site(text, expected):
    found = resolve_site(text, load_sites())
    assert (found and (found[0].id, found[1])) == expected


def test_resolve_site_by_id():
    assert resolve_site("anything", load_sites(), site_id="SITE-NO-02")[0].id == "SITE-NO-02"
    assert resolve_site("anything", load_sites(), site_id="SITE-XX-99") is None


def test_real_data_rare_swedish_item_comes_cross_border():
    """TIM-SE-PINE45 only exists in Sweden: a Copenhagen order must get it from a Swedish DC."""
    site, match = resolve_site("Sundkaj 7, 2150 Nordhavn, København", load_sites())
    p = plan_fulfillment(
        [PlanLineInput(line_index=0, sku="GYP-13-2400", quantity=40), PlanLineInput(line_index=1, sku="TIM-SE-PINE45", quantity=10)],
        site, match, get_group_inventory(), load_warehouses(), load_products(), load_rules(),
    )
    origins = {a.sku: s for s in p.shipments for a in s.lines}
    assert origins["GYP-13-2400"].tier == "branch" and origins["GYP-13-2400"].origin_country == "DK"
    assert origins["TIM-SE-PINE45"].cross_border and origins["TIM-SE-PINE45"].origin_country == "SE"
    assert p.fully_sourced


# --- API: POST /api/orders/{id}/plan --------------------------------------------------------------


@pytest.fixture
def client(tmp_path):
    clear_catalog_cache()
    engine = create_engine(f"sqlite:///{tmp_path / 'plan.db'}", connect_args={"check_same_thread": False})
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


CITY_ONLY_EMAIL = """\
Hei OneOrder,

Kunde: Test Entreprenør AS
Leveringsadresse: Ukjent veg 99, 0150 Oslo
Leveringsdato: 2026-11-15

- 30 stk Brannplate gips 15mm
- 5 pk Gipsskruer 3.9x40mm
"""


def _intake(client, name: str) -> dict:
    res = client.post("/api/intake", files={"file": (name, (SAMPLES_DIR / "emails" / name).read_bytes(), "text/plain")})
    assert res.status_code == 200
    return res.json()


def _approve_all(client, order: dict) -> None:
    corrections = [
        {"line_index": i, "sku": line["matched_sku"] or "GYP-13-2400", "confirmed": True}
        for i, line in enumerate(order["lines"])
    ]
    res = client.post(f"/api/orders/{order['id']}/approve", json={"corrections": corrections})
    assert res.status_code == 200, res.text


def test_plan_api_for_approved_sample_order(client):
    order = _intake(client, "dk_order.txt")
    _approve_all(client, order)

    res = client.post(f"/api/orders/{order['id']}/plan")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["order_id"] == order["id"]
    assert body["site"]["id"] == "SITE-DK-01" and body["site"]["match"] == "address"
    assert body["shipments"] and body["rules_version"] == 1
    planned = sum(a["quantity"] for s in body["shipments"] for a in s["lines"]) + sum(
        s["missing"] for s in body["shortages"]
    )
    assert planned == pytest.approx(sum(line["quantity"] for line in order["lines"]))
    for s in body["shipments"]:
        assert s["vehicle_type"] in {"small_truck", "heavy_truck", "crane_truck"}
        assert all(a["reason"] for a in s["lines"])

    # Read-only: planning does not change the order.
    assert client.get(f"/api/orders/{order['id']}").json()["status"] == "approved"


def test_plan_api_rejects_draft_order(client):
    order = _intake(client, "dk_order.txt")
    res = client.post(f"/api/orders/{order['id']}/plan")
    assert res.status_code == 409


def test_plan_api_unknown_order(client):
    assert client.post("/api/orders/does-not-exist/plan").status_code == 404


def test_plan_api_city_match_warns_and_site_override(client):
    # Inline email on purpose: this address is in Oslo but is not in data/sites.json, and the
    # test must not depend on samples/ (whose addresses are meant to match known sites).
    res = client.post("/api/intake", data={"text": CITY_ONLY_EMAIL})
    assert res.status_code == 200
    order = res.json()
    _approve_all(client, order)

    res = client.post(f"/api/orders/{order['id']}/plan")
    assert res.status_code == 200
    assert res.json()["site"] == {**res.json()["site"], "id": "SITE-NO-01", "match": "city"}
    assert any("by city only" in w for w in res.json()["warnings"])

    override = client.post(f"/api/orders/{order['id']}/plan", json={"site_id": "SITE-NO-02"})
    assert override.status_code == 200 and override.json()["site"]["id"] == "SITE-NO-02"

    bad = client.post(f"/api/orders/{order['id']}/plan", json={"site_id": "SITE-XX-99"})
    assert bad.status_code == 422 and "SITE-NO-01" in bad.json()["detail"]
