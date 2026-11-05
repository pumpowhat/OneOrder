"""Precomputed road distance and driving time between warehouses and sites.

The table is generated once by ``scripts/precompute_drive_times.py`` (OSRM, OpenStreetMap data)
and read from ``data/drive_times.json``; nothing here touches the network.
"""

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parents[3] / "data" / "drive_times.json"


@dataclass(frozen=True)
class DriveTime:
    distance_km: float
    duration_min: int


@lru_cache(maxsize=4)
def _load(path: str) -> dict[str, DriveTime]:
    file = Path(path)
    if not file.exists():
        raise FileNotFoundError(
            f"{file} not found. Generate it with: python scripts/precompute_drive_times.py"
        )
    raw = json.loads(file.read_text(encoding="utf-8"))
    return {
        key: DriveTime(float(v["distance_km"]), int(v["duration_min"]))
        for key, v in raw["pairs"].items()
    }


def load_drive_times(path: str | Path | None = None) -> dict[str, DriveTime]:
    return _load(str(path or DEFAULT_PATH))


def clear_drive_times_cache() -> None:
    _load.cache_clear()


def get_drive_time(
    warehouse_code: str, site_id: str, path: str | Path | None = None
) -> DriveTime:
    """Driving time for a (warehouse, site) pair; KeyError names the missing pair."""
    table = load_drive_times(path)
    try:
        return table[f"{warehouse_code}|{site_id}"]
    except KeyError:
        raise KeyError(f"No precomputed drive time for {warehouse_code} -> {site_id}") from None
