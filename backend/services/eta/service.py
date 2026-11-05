"""Attach ETA predictions to a fulfilment plan."""

from datetime import date, datetime

from backend.services.orchestration.schemas import FulfillmentPlan, OrderETA, Shipment, ShipmentETA

from .baseline import BaselineConfig, add_business_days, baseline_eta
from .drive_times import get_drive_time
from .model import predict_delay_days

_RISK_ORDER = {"on_time": 0, "at_risk": 1, "late": 2}


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def classify_risk(p50: date, p90: date, requested: date | None) -> str | None:
    """on_time: P90 meets the date; at_risk: only the median does; late: not even the median."""
    if requested is None:
        return None
    if p90 <= requested:
        return "on_time"
    if p50 <= requested:
        return "at_risk"
    return "late"


def _features(shipment: Shipment, order_time: datetime, lead_days: int, drive) -> dict:
    return {
        "tier": shipment.tier,
        "cross_border": int(shipment.cross_border),
        "crane_required": int(shipment.crane_required),
        "total_weight_kg": shipment.total_weight_kg,
        "line_count": len(shipment.lines),
        "vehicle_count": shipment.vehicle_count,
        "order_dow": order_time.weekday(),
        "order_hour": order_time.hour,
        "month": order_time.month,
        "winter": int(order_time.month in (12, 1, 2)),
        "distance_km": drive.distance_km,
        "duration_min": drive.duration_min,
        "dest_country": shipment.destination_country,
        "baseline_lead_days": lead_days,
    }


def attach_eta(plan: FulfillmentPlan, order_time: datetime, config: BaselineConfig | None = None) -> FulfillmentPlan:
    """Return ``plan`` with ``eta`` on every shipment and ``order_eta`` on the order.

    Shipments whose (warehouse, site) pair has no precomputed drive time are left without ETA and a
    warning is added. Raises only for model/data failures the caller should handle.
    """
    requested = _parse_date(plan.requested_date)
    baselines, rows, usable = {}, [], []
    for sh in plan.shipments:
        try:
            drive = get_drive_time(sh.origin_warehouse, sh.destination_site)
        except KeyError:
            plan.warnings.append(
                f"ETA unavailable for shipment {sh.shipment_index}: no drive time for {sh.origin_warehouse} -> {sh.destination_site}"
            )
            continue
        base = baseline_eta(order_time, sh.origin_type, sh.origin_country, sh.destination_country, drive, config)
        baselines[sh.shipment_index] = base
        rows.append(_features(sh, order_time, (base.arrival_date - order_time.date()).days, drive))
        usable.append(sh)

    delays = predict_delay_days(rows)
    p50s, p90s = [], []
    for sh, (d50, d90) in zip(usable, delays):
        base = baselines[sh.shipment_index]
        p50 = add_business_days(base.arrival_date, d50, sh.destination_country)
        p90 = add_business_days(base.arrival_date, d90, sh.destination_country)
        sh.eta = ShipmentETA(
            dispatch_date=base.dispatch_date.isoformat(),
            baseline_date=base.arrival_date.isoformat(),
            p50_date=p50.isoformat(),
            p90_date=p90.isoformat(),
            delay_p50_days=d50,
            delay_p90_days=d90,
            risk=classify_risk(p50, p90, requested),
            notes=list(base.notes),
        )
        p50s.append(p50)
        p90s.append(p90)

    if p50s:
        order_p50, order_p90 = max(p50s), max(p90s)
        risks = [s.eta.risk for s in usable if s.eta and s.eta.risk]
        worst = max(risks, key=_RISK_ORDER.__getitem__) if risks else None
        plan.order_eta = OrderETA(p50_date=order_p50.isoformat(), p90_date=order_p90.isoformat(), risk=worst)
    return plan
