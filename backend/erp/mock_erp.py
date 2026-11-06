"""Simulated national ERPs (DK, SE, NO): native stock payloads and the reservation ledger.

Each country exposes what its ERP would:
- ``native_stock``: the stock list in the country's own format (DK CSV, SE Swedish-keyed JSON,
  NO English-keyed JSON) with the reserved quantity already including reservations written here.
- ``reserve`` / ``release`` / ``list_reservations``: the "write reservation" side. The ledger is the
  ``reservations`` table; the stock files in ``data/`` are the opening balance and are never
  modified, so ``git status`` stays clean while the demo runs.

The ERP is the authority on availability: ``reserve`` refuses a line the warehouse cannot cover.
OneOrder reads the same numbers back through the adapters (``apply_reservations``).
"""

import csv
import io
import json
from pathlib import Path

from sqlalchemy.orm import Session

from backend.db import ReservationModel
from backend.services.orchestration import load_warehouses

from .adapters import (
    DEFAULT_DK_PATH,
    DEFAULT_NO_PATH,
    DEFAULT_SE_PATH,
    UnifiedStockItem,
    _qty,
    load_dk_inventory,
    load_no_inventory,
    load_se_inventory,
)
from .reservations import apply_reservations, find_shortfalls, reserved_quantities

COUNTRIES = ("DK", "SE", "NO")


class ReservationRejected(Exception):
    """The ERP cannot cover a requested line. ``shortfalls`` = (warehouse, sku, needed, available)."""

    def __init__(self, shortfalls: list[tuple[str, str, float, float]]):
        self.shortfalls = shortfalls
        detail = "; ".join(f"{wh} {sku}: need {need:g}, available {avail:g}" for wh, sku, need, avail in shortfalls)
        super().__init__(detail)


class UnknownWarehouse(ValueError):
    """The warehouse does not exist or belongs to another country's ERP."""


def normalize_country(value: str) -> str:
    country = value.strip().upper()
    if country not in COUNTRIES:
        raise ValueError(f"Unknown ERP '{value}'; use one of: {', '.join(c.lower() for c in COUNTRIES)}")
    return country


def _fmt(n: float) -> int | float:
    return int(n) if float(n).is_integer() else round(n, 4)


def native_stock(country: str, db: Session) -> tuple[str, str]:
    """The country's stock in its native format, reservations included: ``(body, media_type)``."""
    country = normalize_country(country)
    ledger = reserved_quantities(db)

    if country == "DK":
        with open(DEFAULT_DK_PATH, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            fields = reader.fieldnames or []
            rows = list(reader)
        for row in rows:
            extra = ledger.get((row["lager_kode"].strip(), row["varenr"].strip()), 0)
            row["reserveret"] = _fmt(float(row["reserveret"]) + extra)
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        return out.getvalue(), "text/csv"

    path, wh_key, sku_key, reserved_key = (
        (DEFAULT_SE_PATH, "lagerplats", "artikelnr", "reserverat")
        if country == "SE"
        else (DEFAULT_NO_PATH, "warehouse_id", "sku", "reserved_quantity")
    )
    entries = json.loads(Path(path).read_text(encoding="utf-8"))
    for entry in entries:
        extra = ledger.get((str(entry[wh_key]).strip(), str(entry[sku_key]).strip()), 0)
        entry[reserved_key] = _fmt(float(entry[reserved_key]) + extra)
    return json.dumps(entries, ensure_ascii=False, indent=2), "application/json"


def _country_items(country: str, db: Session) -> list[UnifiedStockItem]:
    loader = {"DK": load_dk_inventory, "SE": load_se_inventory, "NO": load_no_inventory}[country]
    return apply_reservations(loader(), db)


def _warehouse_countries() -> dict[str, str]:
    return {w.code: w.country for w in load_warehouses()}


def reserve(
    db: Session, country: str, order_ref: str, lines: list[dict], *, commit: bool = False
) -> list[ReservationModel]:
    """Write reservations into one country's ERP. All lines are accepted or none is.

    ``lines``: dicts with ``warehouse``, ``sku``, ``quantity`` and optional ``unit`` / ``shipment_index``.
    Raises ``UnknownWarehouse`` (warehouse not in this country) or ``ReservationRejected`` (not enough
    available stock). Nothing is written in either case.
    """
    country = normalize_country(country)
    owners = _warehouse_countries()
    needed: dict[tuple[str, str], float] = {}
    for line in lines:
        wh = line["warehouse"]
        if owners.get(wh) != country:
            raise UnknownWarehouse(f"Warehouse '{wh}' is not in the {country} ERP")
        if float(line["quantity"]) <= 0:
            raise ValueError("Reservation quantity must be greater than 0")
        key = (wh, line["sku"])
        needed[key] = needed.get(key, 0) + float(line["quantity"])

    short = find_shortfalls(needed, _country_items(country, db))
    if short:
        raise ReservationRejected(short)

    rows = [
        ReservationModel(
            order_id=order_ref,
            warehouse_code=line["warehouse"],
            sku=line["sku"],
            quantity=float(line["quantity"]),
            unit=line.get("unit"),
            shipment_index=line.get("shipment_index"),
        )
        for line in lines
    ]
    db.add_all(rows)
    if commit:
        db.commit()
    return rows


def release(db: Session, country: str, order_ref: str, *, commit: bool = False) -> int:
    """Remove every reservation of ``order_ref`` held in this country's ERP; returns how many."""
    country = normalize_country(country)
    owners = _warehouse_countries()
    rows = [
        r
        for r in db.query(ReservationModel).filter(ReservationModel.order_id == order_ref).all()
        if owners.get(r.warehouse_code) == country
    ]
    for row in rows:
        db.delete(row)
    if commit:
        db.commit()
    return len(rows)


def list_reservations(db: Session, country: str) -> list[ReservationModel]:
    country = normalize_country(country)
    owners = _warehouse_countries()
    rows = db.query(ReservationModel).order_by(ReservationModel.id).all()
    return [r for r in rows if owners.get(r.warehouse_code) == country]


def reserve_for_order(db: Session, order_ref: str, shipments: list) -> int:
    """Write an order's planned allocations into the ERPs of the warehouses' countries.

    Checks every country first and writes only if all can cover their part, so the order is either
    reserved everywhere or nowhere. The caller commits. Returns the number of reservation lines.
    """
    owners = _warehouse_countries()
    by_country: dict[str, list[dict]] = {}
    for shipment in shipments:
        country = owners[shipment.origin_warehouse]
        for alloc in shipment.lines:
            by_country.setdefault(country, []).append(
                {
                    "warehouse": shipment.origin_warehouse,
                    "sku": alloc.sku,
                    "quantity": alloc.quantity,
                    "unit": alloc.unit,
                    "shipment_index": shipment.shipment_index,
                }
            )

    shortfalls: list[tuple[str, str, float, float]] = []
    for country, lines in by_country.items():
        needed: dict[tuple[str, str], float] = {}
        for line in lines:
            key = (line["warehouse"], line["sku"])
            needed[key] = needed.get(key, 0) + line["quantity"]
        shortfalls += find_shortfalls(needed, _country_items(country, db))
    if shortfalls:
        raise ReservationRejected(shortfalls)

    total = 0
    for country, lines in by_country.items():
        total += len(reserve(db, country, order_ref, lines))
    return total
