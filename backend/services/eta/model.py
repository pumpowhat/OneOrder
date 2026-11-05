"""Delay-risk model: two quantile regressors (P50, P90) on top of the baseline ETA.

Target is ``delay_days`` (extra business days beyond the baseline arrival). The trained bundle is
cached in ``model.joblib`` next to this file (git-ignored); if it is missing it is trained from
``data/eta_training.csv`` (generated on the fly when that is missing too), which takes a few seconds.
"""

from datetime import datetime, timezone
from functools import lru_cache
import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_pinball_loss
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from .simulation import FEATURES, TARGET, generate

MODEL_PATH = Path(__file__).with_name("model.joblib")
TRAINING_DATA_PATH = Path(__file__).resolve().parents[3] / "data" / "eta_training.csv"
CATEGORICAL = ["tier", "dest_country"]
NUMERIC = [f for f in FEATURES if f not in CATEGORICAL]
QUANTILES = {"p50": 0.5, "p90": 0.9}
SEED = 0


def _pipeline(alpha: float) -> Pipeline:
    pre = ColumnTransformer(
        [
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
            ("num", "passthrough", NUMERIC),
        ]
    )
    gbr = GradientBoostingRegressor(
        loss="quantile",
        alpha=alpha,
        n_estimators=150,
        max_depth=3,
        learning_rate=0.08,
        subsample=0.8,
        random_state=SEED,
    )
    return Pipeline([("pre", pre), ("gbr", gbr)])


def _importance(pipe: Pipeline) -> dict[str, float]:
    """Feature importance summed back to the original (pre one-hot) feature names."""
    names = pipe.named_steps["pre"].get_feature_names_out()
    values = pipe.named_steps["gbr"].feature_importances_
    out: dict[str, float] = {f: 0.0 for f in FEATURES}
    for name, value in zip(names, values):
        raw = name.split("__", 1)[1]
        original = next((c for c in CATEGORICAL if raw.startswith(c + "_")), raw)
        out[original] += float(value)
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def _to_days(x: np.ndarray) -> np.ndarray:
    """Delay is a whole number of business days. Nearest-integer rounding gave the lowest pinball
    loss on the hold-out (ceil over-covers, floor under-covers) and keeps P90 coverage >= 90%."""
    return np.maximum(0, np.rint(np.asarray(x))).astype(int)


def _predict_days(models: dict[str, Pipeline], X: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    p50 = _to_days(models["p50"].predict(X))
    p90 = _to_days(models["p90"].predict(X))
    return p50, np.maximum(p90, p50)  # a quantile curve must not cross below the median


def train(df: pd.DataFrame | None = None) -> dict:
    """Train on ``df`` (default: the simulated history) and return the bundle to persist."""
    if df is None:
        df = pd.read_csv(TRAINING_DATA_PATH) if TRAINING_DATA_PATH.exists() else generate()
    X, y = df[FEATURES], df[TARGET]

    # Honest metrics on a 20% hold-out, then refit on everything for the shipped model.
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=SEED)
    check = {k: _pipeline(a).fit(X_tr, y_tr) for k, a in QUANTILES.items()}
    p50, p90 = _predict_days(check, X_te)
    metrics = {
        "holdout_rows": int(len(X_te)),
        "mae_p50_days": round(float(mean_absolute_error(y_te, p50)), 3),
        "baseline_mae_days": round(float(mean_absolute_error(y_te, np.zeros(len(y_te)))), 3),
        "p90_coverage": round(float((y_te.to_numpy() <= p90).mean()), 3),
        "p50_coverage": round(float((y_te.to_numpy() <= p50).mean()), 3),
        "pinball_p50": round(float(mean_pinball_loss(y_te, p50, alpha=0.5)), 4),
        "pinball_p90": round(float(mean_pinball_loss(y_te, p90, alpha=0.9)), 4),
    }

    models = {k: _pipeline(a).fit(X, y) for k, a in QUANTILES.items()}
    return {
        "models": models,
        "features": list(FEATURES),
        "metrics": metrics,
        "importance": _importance(models["p90"]),
        "training_rows": int(len(df)),
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "data_source": "simulated",
    }


@lru_cache(maxsize=1)
def load_model() -> dict:
    if MODEL_PATH.exists():
        try:
            bundle = joblib.load(MODEL_PATH)
            if bundle.get("features") == list(FEATURES):
                return bundle
        except Exception:  # corrupt or from an incompatible sklearn: retrain below
            pass
    bundle = train()
    try:
        joblib.dump(bundle, MODEL_PATH)
    except OSError:
        pass  # read-only filesystem: keep the in-memory model
    return bundle


def clear_model_cache() -> None:
    load_model.cache_clear()


def predict_delay_days(rows: list[dict]) -> list[tuple[int, int]]:
    """(P50, P90) extra business days beyond the baseline arrival, one pair per feature row."""
    if not rows:
        return []
    X = pd.DataFrame(rows, columns=FEATURES)
    p50, p90 = _predict_days(load_model()["models"], X)
    return [(int(a), int(b)) for a, b in zip(p50, p90)]


def model_info() -> dict:
    bundle = load_model()
    return {
        "type": "GradientBoostingRegressor (quantile loss), one model per quantile",
        "quantiles": QUANTILES,
        "target": f"{TARGET}: extra business days beyond the deterministic baseline arrival",
        "features": bundle["features"],
        "feature_importance": {k: round(v, 4) for k, v in bundle["importance"].items()},
        "metrics": bundle["metrics"],
        "training_rows": bundle["training_rows"],
        "trained_at": bundle["trained_at"],
        "data_source": bundle["data_source"],
        "disclaimer": "Trained on simulated shipment history, not real delivery data; "
        "metrics describe fit to that simulation only.",
    }
