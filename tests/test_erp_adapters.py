from collections import defaultdict

import pytest

from backend.erp import (
    UnifiedStockItem,
    get_group_inventory,
    load_dk_inventory,
    load_no_inventory,
    load_se_inventory,
)
from backend.erp.adapters import DEFAULT_DK_PATH
from backend.services.matching import CatalogueMatcher, clear_catalog_cache, load_catalog
from backend.services.intake.schemas import DraftLine

RARE_ITEMS = {
    "SE": ["TIM-SE-PINE45", "STO-SE-GRANITE", "ARM-BEAM-HEA200"],
    "NO": ["ROOF-NO-SLATE", "CHM-NO-ARCTIC", "INS-NO-ECOWOOL"],
    "DK": ["BRK-DK-CPHRED", "WIN-DK-VELUX78"],
}


@pytest.fixture(scope="module")
def group_items():
    return get_group_inventory()


@pytest.mark.parametrize(
    "loader, country",
    [(load_dk_inventory, "DK"), (load_se_inventory, "SE"), (load_no_inventory, "NO")],
)
def test_national_inventory_loads(loader, country):
    items = loader()
    assert len(items) > 1000
    assert all(isinstance(i, UnifiedStockItem) for i in items)
    assert all(i.country == country for i in items)
    assert all(i.available_quantity == max(0, i.quantity_on_hand - i.reserved_quantity) for i in items)
    warehouses = {i.warehouse_id for i in items}
    assert {f"{country}-DC-01", f"{country}-BR-01"} <= warehouses


def test_group_inventory_size(group_items):
    assert len(group_items) == 3315


@pytest.mark.parametrize("origin, sku", [(o, s) for o, skus in RARE_ITEMS.items() for s in skus])
def test_rare_items_exist_in_one_country_only(group_items, origin, sku):
    stock = defaultdict(float)
    for i in group_items:
        if i.sku == sku:
            stock[i.country] += i.quantity_on_hand
    assert stock[origin] > 0
    assert all(qty == 0 for country, qty in stock.items() if country != origin)


def test_fractional_quantities_are_kept(tmp_path):
    path = tmp_path / "inventory_dk.csv"
    path.write_text("varenr,lager_kode,beholdning,reserveret,enhed\nA-1,DK-DC-01,12.5,2,m\n", encoding="utf-8")
    (item,) = load_dk_inventory(path)
    assert item.quantity_on_hand == 12.5
    assert item.available_quantity == 10.5
    assert isinstance(item.reserved_quantity, int)


def test_branches_do_not_all_carry_every_item(group_items):
    branch_rows = [i for i in group_items if "-BR-" in i.warehouse_id]
    empty_share = sum(i.quantity_on_hand == 0 for i in branch_rows) / len(branch_rows)
    assert 0.3 < empty_share < 0.7

    skus_with_dc_only = {
        sku
        for sku in {i.sku for i in group_items}
        if all(i.quantity_on_hand == 0 for i in branch_rows if i.sku == sku)
    }
    assert skus_with_dc_only


def test_some_items_are_short_in_one_country_but_available_elsewhere(group_items):
    rare = {s for skus in RARE_ITEMS.values() for s in skus}
    stock = defaultdict(lambda: defaultdict(float))
    for i in group_items:
        stock[i.sku][i.country] += i.available_quantity
    short = [
        sku for sku, per_country in stock.items()
        if sku not in rare and min(per_country.values()) < 30 and max(per_country.values()) > 300
    ]
    assert short


def test_every_item_is_available_somewhere(group_items):
    totals = defaultdict(float)
    for i in group_items:
        totals[i.sku] += i.available_quantity
    assert all(qty > 0 for qty in totals.values())


def test_catalog_aliases_are_not_generic():
    """No alias may be fully contained in another SKU's name or alias, or it would be auto-picked wrongly."""
    clear_catalog_cache()
    catalog = load_catalog()
    matcher = CatalogueMatcher(catalog)
    for item in catalog:
        for alias in item.aliases:
            line = matcher.match_line(DraftLine(description=alias, quantity=1, confidence=0.95))
            assert line.matched_sku == item.sku, alias
            assert not line.ambiguous, alias


def test_dk_csv_uses_unix_line_endings():
    assert b"\r\n" not in DEFAULT_DK_PATH.read_bytes()
