"""Reservations written by POST /confirm, and their effect on the group stock view.

The three national ERPs are simulated (see ``mock_erp``): their stock files are the opening balance
and "write reservation" is a row in the ``reservations`` table. These helpers subtract those rows
from the file-based stock, which is exactly what each ERP's native payload shows, so a second order
cannot be promised goods that are already reserved.
"""

from collections import defaultdict
from dataclasses import replace

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.db import ReservationModel

from .adapters import UnifiedStockItem


def reserved_quantities(db: Session) -> dict[tuple[str, str], float]:
    """Total reserved quantity per (warehouse_code, sku) across all confirmed orders."""
    rows = (
        db.query(ReservationModel.warehouse_code, ReservationModel.sku, func.sum(ReservationModel.quantity))
        .group_by(ReservationModel.warehouse_code, ReservationModel.sku)
        .all()
    )
    return {(wh, sku): float(total) for wh, sku, total in rows}


def apply_reservations(inventory: list[UnifiedStockItem], db: Session) -> list[UnifiedStockItem]:
    """Group stock with confirmed reservations deducted from ``available_quantity``."""
    reserved = reserved_quantities(db)
    if not reserved:
        return inventory
    adjusted = []
    for item in inventory:
        extra = reserved.get((item.warehouse_id, item.sku), 0)
        if extra:
            item = replace(
                item,
                reserved_quantity=item.reserved_quantity + extra,
                available_quantity=max(0, item.available_quantity - extra),
            )
        adjusted.append(item)
    return adjusted


def find_shortfalls(
    needed: dict[tuple[str, str], float], inventory: list[UnifiedStockItem]
) -> list[tuple[str, str, float, float]]:
    """(warehouse, sku, needed, available) for every pair where ``inventory`` cannot cover ``needed``."""
    available: dict[tuple[str, str], float] = defaultdict(float)
    for item in inventory:
        available[(item.warehouse_id, item.sku)] += item.available_quantity
    return [
        (wh, sku, qty, available[(wh, sku)])
        for (wh, sku), qty in sorted(needed.items())
        if qty - available[(wh, sku)] > 1e-9
    ]
