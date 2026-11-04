"""Orchestration engine: turns approved order lines into a multi-warehouse fulfilment plan.

Pure functions only: all data (stock, warehouses, products, rules) is passed in, so the engine
is deterministic and easy to test. Steps:

1. Classify every warehouse relative to the site: branch / domestic_dc / cross_border_dc.
2. For each line, walk the tiers in rules.sourcing.priority. Inside a tier prefer a warehouse
   that covers the whole remaining quantity, then one already used by this order (fewer
   shipments), then the nearest. Split the line over several warehouses only when allowed.
3. Group allocations into shipments per (warehouse, crane need), then pick the smallest vehicle
   that carries the weight (several trips when even the largest one is too small).
"""

from collections import defaultdict
import math

from backend.erp import UnifiedStockItem

from .network import ProductLogistics, Site, Warehouse, haversine_km
from .rules import Rules
from .schemas import (
    Allocation,
    FulfillmentPlan,
    PlanLineInput,
    ResolvedSite,
    Shipment,
    Shortage,
)

TIER_LABEL = {
    "branch": "branch",
    "domestic_dc": "domestic DC",
    "cross_border_dc": "cross-border DC",
}
EPSILON = 1e-9


class PlanningError(ValueError):
    """Raised when an order cannot be planned at all (e.g. unknown SKU)."""


def classify_warehouse(warehouse: Warehouse, site: Site, distance_km: float, rules: Rules) -> str | None:
    """Return the sourcing tier of a warehouse for this site, or None when it is not eligible."""
    domestic = warehouse.country == site.country
    if warehouse.type == "branch":
        if domestic and distance_km <= rules.sourcing.branch_max_distance_km:
            return "branch"
        return None  # foreign branches and far-away branches never ship project orders
    if warehouse.type == "dc":
        if domestic:
            return "domestic_dc"
        return "cross_border_dc" if rules.sourcing.allow_cross_border else None
    return None


def _fmt(qty: float) -> str:
    return str(int(qty)) if float(qty).is_integer() else f"{qty:g}"


def choose_vehicle(total_weight_kg: float, crane_required: bool, rules: Rules) -> tuple[str, int]:
    """Smallest vehicle that fits; if none fits, the largest one with several trips."""
    fleet = sorted((v for v in rules.vehicles if v.crane == crane_required), key=lambda v: v.max_weight_kg)
    for vehicle in fleet:
        if total_weight_kg <= vehicle.max_weight_kg:
            return vehicle.type, 1
    largest = fleet[-1]
    return largest.type, math.ceil(total_weight_kg / largest.max_weight_kg)


def plan_fulfillment(
    lines: list[PlanLineInput],
    site: Site,
    site_match: str,
    inventory: list[UnifiedStockItem],
    warehouses: tuple[Warehouse, ...] | list[Warehouse],
    products: dict[str, ProductLogistics],
    rules: Rules,
    *,
    order_id: str | None = None,
    customer: str | None = None,
    delivery_site: str | None = None,
    requested_date: str | None = None,
) -> FulfillmentPlan:
    unknown = sorted({line.sku for line in lines if line.sku not in products})
    if unknown:
        raise PlanningError(f"SKU(s) not in catalogue: {', '.join(unknown)}")

    road = rules.distance.road_factor
    distance: dict[str, float] = {}
    tier_of: dict[str, str] = {}
    by_code: dict[str, Warehouse] = {}
    for wh in warehouses:
        km = round(haversine_km(site.latitude, site.longitude, wh.latitude, wh.longitude) * road, 1)
        tier = classify_warehouse(wh, site, km, rules)
        if tier:
            distance[wh.code], tier_of[wh.code], by_code[wh.code] = km, tier, wh

    # Mutable stock view: SKU → warehouse → available. Shared by all lines, so two lines of the
    # same SKU never promise the same units twice.
    stock: dict[str, dict[str, float]] = defaultdict(dict)
    for item in inventory:
        if item.warehouse_id in tier_of and item.available_quantity > 0:
            stock[item.sku][item.warehouse_id] = stock[item.sku].get(item.warehouse_id, 0) + float(
                item.available_quantity
            )

    used: list[str] = []  # warehouse codes in order of first use → shipment order
    allocations: dict[str, list[Allocation]] = defaultdict(list)
    shortages: list[Shortage] = []
    split = rules.sourcing.allow_line_split

    def rank(code: str) -> tuple[bool, float]:
        # Prefer a warehouse that already ships this order (fewer shipments), then the nearest.
        return (code not in used, distance[code])

    for line in lines:
        product = products[line.sku]
        remaining = float(line.quantity)
        sku_stock = stock[line.sku]

        # Pass 1: one warehouse for the whole line, walking tiers in priority order.
        skipped: list[str] = []
        for tier in rules.sourcing.priority:
            full = [c for c, q in sku_stock.items() if tier_of[c] == tier and q + EPSILON >= remaining]
            if full:
                was_used = set(used)
                code = min(full, key=rank)
                consolidated = code in was_used and distance[code] > min(distance[c] for c in full)
                sku_stock[code] -= remaining
                if code not in used:
                    used.append(code)
                allocations[code].append(
                    _allocation(line, product, remaining, code, tier, distance[code],
                                skipped=skipped, consolidated=consolidated, split=False, rules=rules)
                )
                remaining = 0.0
                break
            skipped.append(tier)

        # Pass 2: no single warehouse holds it all → split over warehouses, still in priority order.
        if remaining > EPSILON and split:
            for tier in rules.sourcing.priority:
                while remaining > EPSILON:
                    pool = [c for c, q in sku_stock.items() if tier_of[c] == tier and q > EPSILON]
                    if not pool:
                        break
                    code = min(pool, key=rank)
                    qty = min(remaining, sku_stock[code])
                    sku_stock[code] -= qty
                    remaining -= qty
                    if code not in used:
                        used.append(code)
                    allocations[code].append(
                        _allocation(line, product, qty, code, tier, distance[code],
                                    skipped=[], consolidated=False, split=True, rules=rules)
                    )

        if remaining > EPSILON:
            allocated = float(line.quantity) - remaining
            shortages.append(
                Shortage(
                    line_index=line.line_index,
                    sku=line.sku,
                    description=line.description or product.name,
                    requested=float(line.quantity),
                    allocated=round(allocated, 3),
                    missing=round(remaining, 3),
                    reason=(
                        "No single eligible warehouse holds the full quantity and line splitting is disabled"
                        if not split and allocated <= EPSILON and _group_total(stock[line.sku]) >= remaining
                        else "Not enough available stock in eligible warehouses (DK, SE, NO)"
                    ),
                )
            )

    # One shipment per (warehouse, crane need): crane goods ride a crane truck, the rest a normal
    # truck, so heavy non-crane goods never force extra crane trucks.
    groups: list[tuple[str, bool, list[Allocation]]] = []
    for code in used:
        for crane in (True, False):
            items = [a for a in allocations[code] if a.requires_crane == crane]
            if items:
                groups.append((code, crane, items))

    shipments: list[Shipment] = []
    for index, (code, crane, items) in enumerate(groups, start=1):
        wh = by_code[code]
        weight = round(sum(a.weight_kg for a in items), 2)
        vehicle, count = choose_vehicle(weight, crane, rules)
        shipments.append(
            Shipment(
                shipment_index=index,
                origin_warehouse=code,
                origin_name=wh.name,
                origin_country=wh.country,
                origin_type=wh.type,
                tier=tier_of[code],
                destination_site=site.id,
                destination_country=site.country,
                cross_border=wh.country != site.country,
                distance_km=distance[code],
                total_weight_kg=weight,
                crane_required=crane,
                vehicle_type=vehicle,
                vehicle_count=count,
                lines=items,
            )
        )

    warnings: list[str] = []
    if site_match == "city":
        warnings.append(
            f"Delivery address '{delivery_site}' matched site {site.id} by city only; check the site before confirming"
        )
    if any(s.crane_required for s in shipments) and not site.crane_accessible:
        warnings.append(f"Crane delivery needed but site {site.id} is marked as not crane accessible")
    if len(shipments) > rules.sourcing.max_shipments_per_order:
        warnings.append(
            f"Plan needs {len(shipments)} shipments, above the limit of {rules.sourcing.max_shipments_per_order}"
        )
    for s in shipments:
        if s.vehicle_count > 1:
            warnings.append(
                f"Shipment {s.shipment_index} ({s.total_weight_kg:g} kg) needs {s.vehicle_count} x {s.vehicle_type}"
            )
    if shortages:
        warnings.append(f"{len(shortages)} line(s) cannot be fully sourced")

    return FulfillmentPlan(
        order_id=order_id,
        customer=customer,
        delivery_site=delivery_site,
        requested_date=requested_date,
        site=ResolvedSite(
            id=site.id,
            name=site.name,
            country=site.country,
            latitude=site.latitude,
            longitude=site.longitude,
            crane_accessible=site.crane_accessible,
            match=site_match,
        ),
        shipments=shipments,
        shortages=shortages,
        total_weight_kg=round(sum(s.total_weight_kg for s in shipments), 2),
        fully_sourced=not shortages,
        warnings=warnings,
        rules_version=rules.version,
    )


def _group_total(per_warehouse: dict[str, float]) -> float:
    return sum(q for q in per_warehouse.values() if q > EPSILON)


def _allocation(
    line: PlanLineInput,
    product: ProductLogistics,
    qty: float,
    code: str,
    tier: str,
    km: float,
    *,
    skipped: list[str],
    consolidated: bool,
    split: bool,
    rules: Rules,
) -> Allocation:
    label = TIER_LABEL[tier]
    if split:
        reason_code = f"{tier}_partial"
        unit = f" {product.unit}" if product.unit else ""
        reason = (
            f"Split line: {_fmt(qty)} of {_fmt(float(line.quantity))}{unit} from {label} {code} ({km:g} km); "
            "no single warehouse holds the full quantity"
        )
    else:
        reason_code = f"{tier}_full"
        reason = (
            f"{label.capitalize()} {code} ({km:g} km) has full stock and already ships this order"
            if consolidated
            else f"Nearest {label} with full stock: {code} ({km:g} km)"
        )
        if skipped:
            parts = [
                f"branch within {rules.sourcing.branch_max_distance_km:g} km" if t == "branch" else TIER_LABEL[t]
                for t in skipped
            ]
            reason += f"; no {' or '.join(parts)} had the full quantity"
    return Allocation(
        line_index=line.line_index,
        sku=line.sku,
        description=line.description or product.name,
        quantity=round(qty, 3),
        unit=product.unit,
        weight_kg=round(qty * product.weight_kg, 2),
        requires_crane=product.requires_crane,
        tier=tier,
        reason_code=reason_code,
        reason=reason,
    )
