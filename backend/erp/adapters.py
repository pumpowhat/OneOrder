"""ERP Adapters for OneOrder.

Standardizes disparate native inventory data formats from Denmark (CSV),
Sweden (Swedish-keyed JSON), and Norway (English-keyed JSON) into a unified
OneOrder stock model.
"""

import csv
from dataclasses import dataclass
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"

DEFAULT_DK_PATH = DATA_DIR / "inventory_dk.csv"
DEFAULT_SE_PATH = DATA_DIR / "inventory_se.json"
DEFAULT_NO_PATH = DATA_DIR / "inventory_no.json"


@dataclass(frozen=True)
class UnifiedStockItem:
    sku: str
    warehouse_id: str
    country: str
    quantity_on_hand: int | float
    reserved_quantity: int | float
    available_quantity: int | float
    unit: str


def _qty(value) -> int | float:
    """Parse a stock quantity, keeping fractions (e.g. 12.5 m) and returning whole numbers as int."""
    number = float(value)
    return int(number) if number.is_integer() else number


def load_dk_inventory(path: str | Path | None = None) -> list[UnifiedStockItem]:
    """Adapter for Danish ERP: parses native CSV format."""
    target = Path(path) if path else DEFAULT_DK_PATH
    if not target.exists():
        raise FileNotFoundError(f"Danish inventory file not found: {target}")

    items = []
    with open(target, mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            on_hand = _qty(row["beholdning"])
            reserved = _qty(row["reserveret"])
            wh = row["lager_kode"].strip()
            country = wh.split("-")[0] if "-" in wh else "DK"
            items.append(
                UnifiedStockItem(
                    sku=row["varenr"].strip(),
                    warehouse_id=wh,
                    country=country,
                    quantity_on_hand=on_hand,
                    reserved_quantity=reserved,
                    available_quantity=max(0, on_hand - reserved),
                    unit=row["enhed"].strip(),
                )
            )
    return items


def load_se_inventory(path: str | Path | None = None) -> list[UnifiedStockItem]:
    """Adapter for Swedish ERP: parses native JSON format with Swedish keys."""
    target = Path(path) if path else DEFAULT_SE_PATH
    if not target.exists():
        raise FileNotFoundError(f"Swedish inventory file not found: {target}")

    with open(target, mode="r", encoding="utf-8") as f:
        raw_data = json.load(f)

    items = []
    for entry in raw_data:
        on_hand = _qty(entry["saldo"])
        reserved = _qty(entry["reserverat"])
        wh = str(entry["lagerplats"]).strip()
        country = wh.split("-")[0] if "-" in wh else "SE"
        items.append(
            UnifiedStockItem(
                sku=str(entry["artikelnr"]).strip(),
                warehouse_id=wh,
                country=country,
                quantity_on_hand=on_hand,
                reserved_quantity=reserved,
                available_quantity=max(0, on_hand - reserved),
                unit=str(entry["enhet"]).strip(),
            )
        )
    return items


def load_no_inventory(path: str | Path | None = None) -> list[UnifiedStockItem]:
    """Adapter for Norwegian ERP: parses native JSON format with English keys."""
    target = Path(path) if path else DEFAULT_NO_PATH
    if not target.exists():
        raise FileNotFoundError(f"Norwegian inventory file not found: {target}")

    with open(target, mode="r", encoding="utf-8") as f:
        raw_data = json.load(f)

    items = []
    for entry in raw_data:
        on_hand = _qty(entry["quantity_on_hand"])
        reserved = _qty(entry["reserved_quantity"])
        wh = str(entry["warehouse_id"]).strip()
        country = wh.split("-")[0] if "-" in wh else "NO"
        items.append(
            UnifiedStockItem(
                sku=str(entry["sku"]).strip(),
                warehouse_id=wh,
                country=country,
                quantity_on_hand=on_hand,
                reserved_quantity=reserved,
                available_quantity=max(0, on_hand - reserved),
                unit=str(entry["unit"]).strip(),
            )
        )
    return items


def get_group_inventory(
    dk_path: str | Path | None = None,
    se_path: str | Path | None = None,
    no_path: str | Path | None = None,
) -> list[UnifiedStockItem]:
    """Aggregate all 3 national ERP inventory sources into a single group-wide view."""
    all_items = []
    all_items.extend(load_dk_inventory(dk_path))
    all_items.extend(load_se_inventory(se_path))
    all_items.extend(load_no_inventory(no_path))
    return all_items

