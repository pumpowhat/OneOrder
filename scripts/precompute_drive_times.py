"""Precompute road distance/duration between every warehouse and every site.

Calls the public OSRM demo server ONCE (``/table`` endpoint, car profile) and writes
``data/drive_times.json``. The ETA model reads that file at runtime, so the app and
the demo never need network access.

Usage:
    python scripts/precompute_drive_times.py            # writes data/drive_times.json
    python scripts/precompute_drive_times.py --base-url http://localhost:5000
"""

import argparse
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "data"
DEFAULT_BASE_URL = "https://router.project-osrm.org"
USER_AGENT = "OneOrder-hackathon-precompute/1.0"


def _fetch_table(base_url: str, warehouses: list[dict], sites: list[dict]) -> dict:
    coords = [(w["longitude"], w["latitude"]) for w in warehouses] + [
        (s["longitude"], s["latitude"]) for s in sites
    ]
    coord_str = ";".join(f"{lon:.6f},{lat:.6f}" for lon, lat in coords)
    n_w = len(warehouses)
    sources = ";".join(str(i) for i in range(n_w))
    dests = ";".join(str(i) for i in range(n_w, len(coords)))
    url = (
        f"{base_url}/table/v1/driving/{coord_str}"
        f"?sources={sources}&destinations={dests}&annotations=duration,distance"
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    if data.get("code") != "Ok":
        raise RuntimeError(f"OSRM error: {data.get('code')} {data.get('message')}")
    return data


def build(base_url: str) -> dict:
    warehouses = json.loads((DATA_DIR / "warehouses.json").read_text(encoding="utf-8"))
    sites = json.loads((DATA_DIR / "sites.json").read_text(encoding="utf-8"))
    data = _fetch_table(base_url, warehouses, sites)

    pairs = {}
    missing = []
    for i, w in enumerate(warehouses):
        for j, s in enumerate(sites):
            seconds = data["durations"][i][j]
            meters = data["distances"][i][j]
            if seconds is None or meters is None:
                missing.append(f"{w['code']} -> {s['id']}")
                continue
            pairs[f"{w['code']}|{s['id']}"] = {
                "distance_km": round(meters / 1000, 1),
                "duration_min": round(seconds / 60),
            }
    if missing:
        raise RuntimeError(f"No route for {len(missing)} pair(s): {missing}")
    return {
        "version": 1,
        "source": "OSRM table API, car profile (OpenStreetMap data)",
        "base_url": base_url,
        "key_format": "<warehouse_code>|<site_id>",
        "pairs": pairs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--out", default=str(DATA_DIR / "drive_times.json"))
    args = parser.parse_args()
    try:
        result = build(args.base_url.rstrip("/"))
    except (urllib.error.URLError, RuntimeError, TimeoutError) as exc:
        print(f"Failed: {exc}", file=sys.stderr)
        return 1
    Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(result['pairs'])} pairs to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
