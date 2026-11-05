"""Simulated shipment history for training the ETA risk layer.

There is no real delivery history for Company A, so this module *simulates* one. For every
simulated shipment it computes the deterministic baseline arrival (``baseline.py``) and then draws
how many extra business days the delivery really took, from a delay model whose drivers are
documented in ``docs/eta-calibration.md``:

    delay_days = 0                                  with probability 1 - p
               = 1 + Poisson(lam)                   with probability p

    logit(p) = -2.4 + 0.0010 * distance_km + 0.6 * cross_border + 0.5 * crane
             + 0.00008 * weight_kg + 0.1 * (vehicle_count - 1) + 0.9 * winter + 0.35 * friday_order
             + 0.3 * (tier == "cross_border_dc") + 0.3 * (dest == "NO")
    lam      = 0.4 + 0.6 * winter + 0.5 * cross_border

The coefficients are assumptions chosen to be directionally realistic (longer, heavier, crane,
cross-border and winter shipments are late more often and by more days). They are NOT fitted to
real data. Retrain on real history when it exists.
"""

from datetime import datetime, timedelta
import math

import numpy as np
import pandas as pd

from backend.services.orchestration import (
    classify_warehouse,
    haversine_km,
    load_rules,
    load_sites,
    load_warehouses,
)
from backend.services.orchestration.engine import choose_vehicle

from .baseline import BaselineConfig, add_business_days, baseline_eta
from .drive_times import get_drive_time

TIER_WEIGHTS = {"branch": 0.45, "domestic_dc": 0.40, "cross_border_dc": 0.15}
WINTER_MONTHS = (12, 1, 2)

FEATURES = [
    "tier",
    "cross_border",
    "crane_required",
    "total_weight_kg",
    "line_count",
    "vehicle_count",
    "order_dow",
    "order_hour",
    "month",
    "winter",
    "distance_km",
    "duration_min",
    "dest_country",
    "baseline_lead_days",
]
TARGET = "delay_days"
COLUMNS = FEATURES + [TARGET, "lead_days_actual"]


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def delay_probability(row: dict) -> float:
    logit = (
        -2.4
        + 0.0010 * row["distance_km"]
        + 0.6 * row["cross_border"]
        + 0.5 * row["crane_required"]
        + 0.00008 * row["total_weight_kg"]
        + 0.1 * (row["vehicle_count"] - 1)
        + 0.9 * row["winter"]
        + 0.35 * (row["order_dow"] == 4)
        + 0.3 * (row["tier"] == "cross_border_dc")
        + 0.3 * (row["dest_country"] == "NO")
    )
    return _sigmoid(logit)


def delay_lambda(row: dict) -> float:
    return 0.4 + 0.6 * row["winter"] + 0.5 * row["cross_border"]


def generate(n: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Simulate ``n`` shipments over one year of orders; fully reproducible for a given seed."""
    rng = np.random.default_rng(seed)
    rules = load_rules()
    warehouses = load_warehouses()
    sites = load_sites()
    cfg = BaselineConfig()

    # Only (warehouse, site) pairs the sourcing engine could actually use, grouped by tier.
    pairs_by_tier: dict[str, list] = {t: [] for t in TIER_WEIGHTS}
    for w in warehouses:
        for s in sites:
            crow = haversine_km(w.latitude, w.longitude, s.latitude, s.longitude) * rules.distance.road_factor
            tier = classify_warehouse(w, s, crow, rules)
            if tier:
                pairs_by_tier[tier].append((w, s))
    tiers = [t for t in TIER_WEIGHTS if pairs_by_tier[t]]
    probs = np.array([TIER_WEIGHTS[t] for t in tiers], dtype=float)
    probs /= probs.sum()

    start = datetime(2026, 1, 1)
    rows = []
    for _ in range(n):
        tier = tiers[rng.choice(len(tiers), p=probs)]
        w, s = pairs_by_tier[tier][rng.integers(len(pairs_by_tier[tier]))]
        drive = get_drive_time(w.code, s.id)

        order_time = start + timedelta(
            days=int(rng.integers(0, 365)), hours=int(rng.integers(7, 19)), minutes=int(rng.integers(0, 60))
        )
        crane = bool(s.crane_accessible and rng.random() < 0.25)
        weight = float(np.clip(rng.lognormal(mean=6.5, sigma=1.1), 30, 40000))
        line_count = int(np.clip(rng.poisson(4) + 1, 1, 20))
        _, vehicle_count = choose_vehicle(weight, crane, rules)

        base = baseline_eta(order_time, w.type, w.country, s.country, drive, cfg)
        row = {
            "tier": tier,
            "cross_border": int(w.country != s.country),
            "crane_required": int(crane),
            "total_weight_kg": round(weight, 1),
            "line_count": line_count,
            "vehicle_count": vehicle_count,
            "order_dow": order_time.weekday(),
            "order_hour": order_time.hour,
            "month": order_time.month,
            "winter": int(order_time.month in WINTER_MONTHS),
            "distance_km": drive.distance_km,
            "duration_min": drive.duration_min,
            "dest_country": s.country,
            "baseline_lead_days": (base.arrival_date - order_time.date()).days,
        }
        delay = 0
        if rng.random() < delay_probability(row):
            delay = 1 + int(rng.poisson(delay_lambda(row)))
        actual = add_business_days(base.arrival_date, delay, s.country)
        row[TARGET] = delay
        row["lead_days_actual"] = (actual - order_time.date()).days
        rows.append(row)

    return pd.DataFrame(rows, columns=COLUMNS)
