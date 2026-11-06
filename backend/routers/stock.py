from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.erp import get_group_inventory
from backend.erp.reservations import apply_reservations
from backend.services.matching import load_catalog
from backend.services.orchestration import load_warehouses

router = APIRouter(prefix="/api", tags=["stock"])

COUNTRIES = ("DK", "SE", "NO")
LOW_STOCK_RATIO = 0.1  # available below 10% of on-hand counts as low
LOW_STOCK_MIN = 5


def _level(available: float, on_hand: float) -> str:
    if available <= 0:
        return "out"
    if available < max(LOW_STOCK_MIN, LOW_STOCK_RATIO * on_hand):
        return "low"
    return "ok"


@router.get("/stock")
def get_stock(
    country: str | None = None,
    q: str | None = None,
    only_issues: bool = False,
    db: Session = Depends(get_db),
) -> dict:
    """Group stock per SKU with the three countries side by side and the warehouse detail.

    Quantities are net of reservations from confirmed orders. ``level`` is ``ok`` / ``low`` / ``out``
    for the SKU's total, ``single_country`` marks SKUs that exist in one country only (cross-border
    goods). Filters: ``country`` (SKUs that have stock rows there), ``q`` (SKU or name),
    ``only_issues`` (low or out of stock).
    """
    if country and country.upper() not in COUNTRIES:
        raise HTTPException(status_code=422, detail=f"country must be one of {', '.join(COUNTRIES)}")
    try:
        inventory = apply_reservations(get_group_inventory(), db)
        names = {c.sku: c.name for c in load_catalog()}
        warehouses = {w.code: w for w in load_warehouses()}
    except (FileNotFoundError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=f"Stock data unavailable: {exc}") from exc

    skus: dict[str, dict] = {}
    for item in inventory:
        entry = skus.setdefault(
            item.sku,
            {
                "sku": item.sku,
                "name": names.get(item.sku, item.sku),
                "unit": item.unit,
                "by_country": {c: {"on_hand": 0, "reserved": 0, "available": 0} for c in COUNTRIES},
                "warehouses": [],
            },
        )
        cell = entry["by_country"].setdefault(item.country, {"on_hand": 0, "reserved": 0, "available": 0})
        cell["on_hand"] += item.quantity_on_hand
        cell["reserved"] += item.reserved_quantity
        cell["available"] += item.available_quantity
        wh = warehouses.get(item.warehouse_id)
        entry["warehouses"].append(
            {
                "code": item.warehouse_id,
                "name": wh.name if wh else item.warehouse_id,
                "type": wh.type if wh else None,
                "country": item.country,
                "on_hand": item.quantity_on_hand,
                "reserved": item.reserved_quantity,
                "available": item.available_quantity,
            }
        )

    rows = []
    needle = q.strip().casefold() if q else ""
    for entry in skus.values():
        totals = entry["by_country"].values()
        entry["total_available"] = sum(c["available"] for c in totals)
        on_hand = sum(c["on_hand"] for c in totals)
        entry["level"] = _level(entry["total_available"], on_hand)
        entry["single_country"] = sum(1 for c in totals if c["on_hand"] > 0) == 1
        entry["warehouses"].sort(key=lambda w: (-w["available"], w["code"]))
        if country and entry["by_country"][country.upper()]["on_hand"] <= 0:
            continue
        if needle and needle not in entry["sku"].casefold() and needle not in entry["name"].casefold():
            continue
        if only_issues and entry["level"] == "ok":
            continue
        rows.append(entry)
    rows.sort(key=lambda e: e["sku"])

    summary = {
        c: {
            "skus": sum(1 for e in skus.values() if e["by_country"][c]["on_hand"] > 0),
            "out_or_low": sum(1 for e in skus.values() if e["by_country"][c]["on_hand"] > 0
                              and _level(e["by_country"][c]["available"], e["by_country"][c]["on_hand"]) != "ok"),
        }
        for c in COUNTRIES
    }
    return {"summary": summary, "items": rows, "total": len(rows)}
