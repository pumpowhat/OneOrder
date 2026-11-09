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
    """Aliases resolve to their SKU; unclear measurement roles still require review."""
    review_aliases = {
        "gipsplade 3m", "gipsskiva 3000mm", "gipsplate 3m lang", "drywall board 3000mm",
        "gulvvarmerør 20mm 120m", "golvvärmerör pex 20mm 120m",
        "gulvvarmerør pex 20mm", "underfloor heating pex pipe 20mm 120m",
    }
    clear_catalog_cache()
    catalog = load_catalog()
    matcher = CatalogueMatcher(catalog)
    for item in catalog:
        for alias in item.aliases:
            line = matcher.match_line(DraftLine(description=alias, quantity=1, confidence=0.95))
            assert line.matched_sku == item.sku, alias
            assert line.needs_review is (alias in review_aliases), alias


def test_dk_csv_uses_unix_line_endings():
    assert b"\r\n" not in DEFAULT_DK_PATH.read_bytes()


# ===================================================================
# Task 2 (Issue #6) - Phần A: Bổ sung các ca test biên cho Adapter ERP
# ===================================================================

@pytest.mark.parametrize("loader", [load_dk_inventory, load_se_inventory, load_no_inventory])
def test_adapter_raises_file_not_found(tmp_path, loader):
    """1. Truyền đường dẫn không tồn tại cho adapter DK, SE, NO; xác nhận ném FileNotFoundError."""
    missing_file = tmp_path / "non_existent_inventory_file.data"
    with pytest.raises(FileNotFoundError):
        loader(missing_file)


def test_missing_required_column_raises_key_error(tmp_path):
    """2. Thiếu cột bắt buộc (beholdning ở CSV, saldo ở SE JSON) -> ghi nhận lỗi KeyError."""
    # DK CSV thiếu beholdning
    dk_path = tmp_path / "dk_missing_col.csv"
    dk_path.write_text("varenr,lager_kode,reserveret,enhed\nGYP-13-2400,DK-DC-01,10,stk\n", encoding="utf-8")
    with pytest.raises(KeyError) as exc_dk:
        load_dk_inventory(dk_path)
    assert "beholdning" in str(exc_dk.value)

    # SE JSON thiếu saldo
    se_path = tmp_path / "se_missing_col.json"
    se_path.write_text(
        '[{"artikelnr": "GYP-13-2400", "lagerplats": "SE-DC-01", "reserverat": 10, "enhet": "stk"}]',
        encoding="utf-8",
    )
    with pytest.raises(KeyError) as exc_se:
        load_se_inventory(se_path)
    assert "saldo" in str(exc_se.value)


def test_reserved_greater_than_on_hand_yields_zero_available(tmp_path):
    """3. Cho reserved > on_hand; xác nhận available_quantity == 0 (không âm)."""
    dk_path = tmp_path / "dk_over_reserved.csv"
    dk_path.write_text(
        "varenr,lager_kode,beholdning,reserveret,enhed\nGYP-13-2400,DK-DC-01,10,25,stk\n",
        encoding="utf-8",
    )
    (item,) = load_dk_inventory(dk_path)
    assert item.quantity_on_hand == 10
    assert item.reserved_quantity == 25
    assert item.available_quantity == 0


def test_extra_whitespace_is_stripped(tmp_path):
    """4. Có khoảng trắng thừa trong SKU và mã kho; xác nhận các trường được strip sạch."""
    dk_path = tmp_path / "dk_whitespace.csv"
    dk_path.write_text(
        "varenr,lager_kode,beholdning,reserveret,enhed\n  GYP-13-2400  ,  DK-DC-01  ,100,5,  stk  \n",
        encoding="utf-8",
    )
    (dk_item,) = load_dk_inventory(dk_path)
    assert dk_item.sku == "GYP-13-2400"
    assert dk_item.warehouse_id == "DK-DC-01"
    assert dk_item.unit == "stk"

    se_path = tmp_path / "se_whitespace.json"
    se_path.write_text(
        '[{"artikelnr": "  TIM-SPRU-45145  ", "lagerplats": "  SE-DC-01  ", "saldo": 50, "reserverat": 0, "enhet": "  m  "}]',
        encoding="utf-8",
    )
    (se_item,) = load_se_inventory(se_path)
    assert se_item.sku == "TIM-SPRU-45145"
    assert se_item.warehouse_id == "SE-DC-01"
    assert se_item.unit == "m"

    no_path = tmp_path / "no_whitespace.json"
    no_path.write_text(
        '[{"sku": "  CEM-PORT-25  ", "warehouse_id": "  NO-DC-01  ", "quantity_on_hand": 80, "reserved_quantity": 2, "unit": "  sæk  "}]',
        encoding="utf-8",
    )
    (no_item,) = load_no_inventory(no_path)
    assert no_item.sku == "CEM-PORT-25"
    assert no_item.warehouse_id == "NO-DC-01"
    assert no_item.unit == "sæk"


def test_string_number_and_fraction_parsed_correctly(tmp_path):
    """5. Kiểm tra chuỗi số \"100\" và số lẻ 12.5 được đọc đúng."""
    # CSV với chuỗi số và số lẻ
    dk_path = tmp_path / "dk_numbers.csv"
    dk_path.write_text(
        "varenr,lager_kode,beholdning,reserveret,enhed\n"
        'ITEM-INT,DK-DC-01,"100","20",stk\n'
        'ITEM-FRAC,DK-DC-01,"12.5","2.5",m\n',
        encoding="utf-8",
    )
    items = load_dk_inventory(dk_path)
    assert len(items) == 2
    assert items[0].quantity_on_hand == 100
    assert isinstance(items[0].quantity_on_hand, int)
    assert items[0].reserved_quantity == 20
    assert isinstance(items[0].reserved_quantity, int)
    assert items[0].available_quantity == 80

    assert items[1].quantity_on_hand == 12.5
    assert isinstance(items[1].quantity_on_hand, float)
    assert items[1].reserved_quantity == 2.5
    assert items[1].available_quantity == 10.0


@pytest.mark.parametrize(
    "loader, default_country, filename, content",
    [
        (
            load_dk_inventory,
            "DK",
            "dk_no_dash.csv",
            "varenr,lager_kode,beholdning,reserveret,enhed\nSKU-1,CENTRALWAREHOUSE,50,0,stk\n",
        ),
        (
            load_se_inventory,
            "SE",
            "se_no_dash.json",
            '[{"artikelnr": "SKU-1", "lagerplats": "CENTRALWAREHOUSE", "saldo": 50, "reserverat": 0, "enhet": "stk"}]',
        ),
        (
            load_no_inventory,
            "NO",
            "no_no_dash.json",
            '[{"sku": "SKU-1", "warehouse_id": "CENTRALWAREHOUSE", "quantity_on_hand": 50, "reserved_quantity": 0, "unit": "stk"}]',
        ),
    ],
)
def test_warehouse_code_without_dash_falls_back_to_default_country(tmp_path, loader, default_country, filename, content):
    """6. Kiểm tra mã kho không có dấu '-' trên cả 3 adapter; rơi về quốc gia mặc định DK, SE, NO tương ứng."""
    path = tmp_path / filename
    path.write_text(content, encoding="utf-8")
    (item,) = loader(path)
    assert item.country == default_country
    assert item.warehouse_id == "CENTRALWAREHOUSE"


@pytest.mark.parametrize(
    "loader, filename, content",
    [
        (
            load_dk_inventory,
            "dk_empty.csv",
            "varenr,lager_kode,beholdning,reserveret,enhed\n",
        ),
        (
            load_se_inventory,
            "se_empty.json",
            "[]",
        ),
        (
            load_no_inventory,
            "no_empty.json",
            "[]",
        ),
    ],
)
def test_empty_files_return_empty_list(tmp_path, loader, filename, content):
    """7. Kiểm tra CSV chỉ có header và JSON hợp lệ '[]'; kết quả là danh sách rỗng, không lỗi."""
    path = tmp_path / filename
    path.write_text(content, encoding="utf-8")
    items = loader(path)
    assert items == []
