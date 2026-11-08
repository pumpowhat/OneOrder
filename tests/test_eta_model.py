"""ETA delay model, its attachment to plans, and the /api/model + /plan API."""

from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.ai import get_ai_client
from backend.db import Base, get_db
from backend.main import app
from backend.services.eta import classify_risk, clear_model_cache, is_business_day, predict_delay_days, train
from backend.services.eta import model as eta_model
from backend.services.eta.simulation import FEATURES, generate
from backend.services.intake.demo_client import DemoClient
from backend.services.matching import clear_catalog_cache

SAMPLES_DIR = Path("samples")


@pytest.fixture(scope="module")
def small_df():
    return generate(2000, seed=3)


@pytest.fixture(autouse=True)
def isolated_model_file(tmp_path, monkeypatch):
    """Never write model.joblib into the repo from tests."""
    monkeypatch.setattr(eta_model, "MODEL_PATH", tmp_path / "model.joblib")
    clear_model_cache()
    yield
    clear_model_cache()


def row(**over) -> dict:
    base = {
        "tier": "branch", "cross_border": 0, "crane_required": 0, "total_weight_kg": 300.0,
        "line_count": 3, "vehicle_count": 1, "order_dow": 2, "order_hour": 10, "month": 6,
        "winter": 0, "distance_km": 40.0, "duration_min": 50, "dest_country": "DK",
        "baseline_lead_days": 1,
    }
    base.update(over)
    return base


# --- the model ----------------------------------------------------------------------------------


def test_train_reports_honest_metrics(small_df):
    bundle = train(small_df)
    m = bundle["metrics"]
    assert bundle["features"] == FEATURES
    assert bundle["data_source"] == "simulated"
    assert m["holdout_rows"] == 400
    assert 0.85 <= m["p90_coverage"] <= 1.0
    assert m["mae_p50_days"] >= 0
    assert set(bundle["importance"]) == set(FEATURES)
    assert sum(bundle["importance"].values()) == pytest.approx(1.0, abs=1e-6)


def test_p90_is_never_below_p50_and_values_are_whole_days(monkeypatch, small_df):
    monkeypatch.setattr(eta_model, "TRAINING_DATA_PATH", Path("/nonexistent"))
    monkeypatch.setattr(eta_model, "generate", lambda: small_df)
    rows = [row(), row(cross_border=1, winter=1, tier="cross_border_dc", distance_km=900.0, duration_min=700),
            row(crane_required=1, total_weight_kg=9000.0)]
    for p50, p90 in predict_delay_days(rows):
        assert isinstance(p50, int) and isinstance(p90, int)
        assert 0 <= p50 <= p90


def test_risky_shipment_gets_a_longer_p90(monkeypatch, small_df):
    monkeypatch.setattr(eta_model, "TRAINING_DATA_PATH", Path("/nonexistent"))
    monkeypatch.setattr(eta_model, "generate", lambda: small_df)
    easy, hard = predict_delay_days([
        row(),
        row(cross_border=1, winter=1, tier="cross_border_dc", crane_required=1,
            distance_km=1000.0, duration_min=800, total_weight_kg=8000.0, dest_country="NO"),
    ])
    assert hard[1] > easy[1]


def test_model_is_saved_and_reused(monkeypatch, small_df, tmp_path):
    monkeypatch.setattr(eta_model, "TRAINING_DATA_PATH", Path("/nonexistent"))
    monkeypatch.setattr(eta_model, "generate", lambda: small_df)
    first = eta_model.load_model()
    assert eta_model.MODEL_PATH.exists()
    clear_model_cache()
    second = eta_model.load_model()
    assert second["trained_at"] == first["trained_at"]  # loaded from disk, not retrained


def test_empty_prediction_list():
    assert predict_delay_days([]) == []


# --- risk classification -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "p50, p90, requested, expected",
    [
        (date(2026, 11, 10), date(2026, 11, 12), date(2026, 11, 12), "on_time"),
        (date(2026, 11, 10), date(2026, 11, 12), date(2026, 11, 11), "at_risk"),
        (date(2026, 11, 10), date(2026, 11, 12), date(2026, 11, 10), "at_risk"),
        (date(2026, 11, 10), date(2026, 11, 12), date(2026, 11, 9), "late"),
        (date(2026, 11, 10), date(2026, 11, 12), None, None),
    ],
)
def test_classify_risk(p50, p90, requested, expected):
    assert classify_risk(p50, p90, requested) == expected


# --- API ----------------------------------------------------------------------------------------


@pytest.fixture
def client(tmp_path):
    clear_catalog_cache()
    engine = create_engine(f"sqlite:///{tmp_path / 'eta.db'}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autoflush=False)

    def override_get_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_ai_client] = lambda: DemoClient(SAMPLES_DIR / "fixtures")
    yield TestClient(app)
    app.dependency_overrides.clear()


def approved_order(client, name="dk_order.txt") -> dict:
    res = client.post("/api/intake", files={"file": (name, (SAMPLES_DIR / "emails" / name).read_bytes(), "text/plain")})
    assert res.status_code == 200
    order = res.json()
    corrections = [
        {"line_index": i, "sku": line["matched_sku"] or "GYP-13-2400", "confirmed": True}
        for i, line in enumerate(order["lines"])
    ]
    assert client.post(f"/api/orders/{order['id']}/approve", json={"corrections": corrections, "customer_phone": "+45 00 00 00 01"}).status_code == 200
    return order


def test_plan_has_ordered_eta_dates_on_business_days(client):
    order = approved_order(client)
    body = client.post(f"/api/orders/{order['id']}/plan").json()
    assert body["shipments"]
    for s in body["shipments"]:
        eta = s["eta"]
        assert eta, "every shipment gets an ETA"
        dispatch, base, p50, p90 = (date.fromisoformat(eta[k]) for k in ("dispatch_date", "baseline_date", "p50_date", "p90_date"))
        assert dispatch <= base <= p50 <= p90
        assert is_business_day(p90, s["destination_country"])
        assert eta["delay_p50_days"] <= eta["delay_p90_days"]
    order_eta = body["order_eta"]
    assert order_eta["p50_date"] == max(s["eta"]["p50_date"] for s in body["shipments"])
    assert order_eta["p90_date"] == max(s["eta"]["p90_date"] for s in body["shipments"])


def test_order_with_requested_date_gets_a_risk_flag(client):
    order = approved_order(client)
    assert order["requested_date"]
    body = client.post(f"/api/orders/{order['id']}/plan").json()
    assert body["order_eta"]["risk"] in {"on_time", "at_risk", "late"}
    assert all(s["eta"]["risk"] for s in body["shipments"])


def test_eta_failure_does_not_block_planning(client, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("model file corrupt")

    monkeypatch.setattr("backend.routers.orders.attach_eta", boom)
    order = approved_order(client)
    res = client.post(f"/api/orders/{order['id']}/plan")
    assert res.status_code == 200
    body = res.json()
    assert body["shipments"] and body["order_eta"] is None
    assert any("ETA unavailable" in w for w in body["warnings"])


def test_model_endpoint(client):
    res = client.get("/api/model")
    assert res.status_code == 200
    body = res.json()
    assert body["features"] == FEATURES
    assert {"mae_p50_days", "p90_coverage"} <= set(body["metrics"])
    assert body["data_source"] == "simulated" and "simulated" in body["disclaimer"]
    assert body["quantiles"] == {"p50": 0.5, "p90": 0.9}
