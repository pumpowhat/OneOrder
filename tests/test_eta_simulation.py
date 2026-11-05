"""The simulated shipment history: reproducible, well-formed and directionally realistic."""

import pandas as pd
import pytest

from backend.services.eta.simulation import COLUMNS, FEATURES, TARGET, generate


@pytest.fixture(scope="module")
def df():
    return generate(3000, seed=1)


def test_columns_and_size(df):
    assert list(df.columns) == COLUMNS
    assert len(df) == 3000
    assert not df.isna().any().any()


def test_reproducible_for_same_seed():
    pd.testing.assert_frame_equal(generate(200, seed=5), generate(200, seed=5))
    assert not generate(200, seed=5).equals(generate(200, seed=6))


def test_target_does_not_leak_into_features(df):
    assert TARGET not in FEATURES
    assert "lead_days_actual" not in FEATURES


def test_delay_is_non_negative_integer_and_mostly_on_time(df):
    assert (df[TARGET] >= 0).all()
    assert df[TARGET].dtype.kind in "iu"
    assert 0.10 < (df[TARGET] > 0).mean() < 0.40
    assert (df["lead_days_actual"] >= df["baseline_lead_days"]).all()


def test_only_engine_eligible_tiers(df):
    assert set(df["tier"]) <= {"branch", "domestic_dc", "cross_border_dc"}
    # cross-border flag and tier agree
    assert (df[df["tier"] == "cross_border_dc"]["cross_border"] == 1).all()
    assert (df[df["tier"] != "cross_border_dc"]["cross_border"] == 0).all()


def test_risk_drivers_point_the_expected_way(df):
    m = df.groupby("cross_border")[TARGET].mean()
    assert m[1] > m[0]
    w = df.groupby("winter")[TARGET].mean()
    assert w[1] > w[0]
    c = df.groupby("crane_required")[TARGET].mean()
    assert c[1] > c[0]
    far = df[df["distance_km"] > df["distance_km"].median()][TARGET].mean()
    near = df[df["distance_km"] <= df["distance_km"].median()][TARGET].mean()
    assert far > near


def test_feature_ranges_are_sane(df):
    assert df["total_weight_kg"].between(30, 40000).all()
    assert df["order_dow"].between(0, 6).all()
    assert df["order_hour"].between(7, 18).all()
    assert df["month"].between(1, 12).all()
    assert (df["vehicle_count"] >= 1).all()
