"""Static logistics network: warehouses, construction sites, product logistics data and distances."""

from dataclasses import dataclass
from functools import lru_cache
import json
import math
from pathlib import Path
import re
import unicodedata

from backend.services.matching.catalog import resolve_catalog_path

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
EARTH_RADIUS_KM = 6371.0


@dataclass(frozen=True)
class Warehouse:
    code: str
    name: str
    country: str
    type: str  # "branch" | "dc"
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Site:
    id: str
    name: str
    country: str
    address: str
    latitude: float
    longitude: float
    crane_accessible: bool


@dataclass(frozen=True)
class ProductLogistics:
    sku: str
    name: str
    unit: str | None
    weight_kg: float
    requires_crane: bool


def _read_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=4)
def load_warehouses(path: str | None = None) -> tuple[Warehouse, ...]:
    raw = _read_json(Path(path) if path else DATA_DIR / "warehouses.json")
    return tuple(
        Warehouse(
            code=w["code"],
            name=w["name"],
            country=w["country"],
            type=w["type"],
            latitude=float(w["latitude"]),
            longitude=float(w["longitude"]),
        )
        for w in raw
    )


@lru_cache(maxsize=4)
def load_sites(path: str | None = None) -> tuple[Site, ...]:
    raw = _read_json(Path(path) if path else DATA_DIR / "sites.json")
    return tuple(
        Site(
            id=s["id"],
            name=s["name"],
            country=s["country"],
            address=s["address"],
            latitude=float(s["latitude"]),
            longitude=float(s["longitude"]),
            crane_accessible=bool(s.get("crane_accessible", False)),
        )
        for s in raw
    )


@lru_cache(maxsize=4)
def _load_products(target: str) -> dict[str, ProductLogistics]:
    raw = _read_json(Path(target))
    return {
        str(p["sku"]).strip(): ProductLogistics(
            sku=str(p["sku"]).strip(),
            name=str(p.get("name", "")).strip(),
            unit=p.get("unit"),
            weight_kg=float(p.get("weight_kg") or 0),
            requires_crane=bool(p.get("requires_crane", False)),
        )
        for p in raw
    }


def load_products(path: str | Path | None = None) -> dict[str, ProductLogistics]:
    """Weight and crane flag per SKU, read from the same catalogue file as the matcher."""
    return _load_products(str(resolve_catalog_path(path)))


def clear_network_cache() -> None:
    load_warehouses.cache_clear()
    load_sites.cache_clear()
    _load_products.cache_clear()


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _normalize(text: str) -> str:
    """Casefold, fold æ/ø/å and accents, keep only letters, digits and single spaces."""
    text = text.casefold().replace("æ", "ae").replace("ø", "o").replace("å", "a")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def _city(address: str) -> str:
    """City of a site address: the last comma part without postcode and district letters ('1799 København V')."""
    words = [w for w in _normalize(address.split(",")[-1]).split() if not w.isdigit() and len(w) > 1]
    return words[0] if words else ""


def resolve_site(
    delivery_site: str | None,
    sites: tuple[Site, ...] | list[Site],
    site_id: str | None = None,
) -> tuple[Site, str] | None:
    """Find the construction site for an order.

    Order of checks: explicit site_id → full address or site name in the text → city in the text.
    Returns (site, match_type) or None when nothing matches.
    """
    if site_id:
        site = next((s for s in sites if s.id == site_id), None)
        return (site, "site_id") if site else None

    if not delivery_site or not delivery_site.strip():
        return None
    text = _normalize(delivery_site)
    padded = f" {text} "

    for site in sites:
        address = _normalize(site.address)
        street = _normalize(site.address.split(",")[0])
        if address in text or f" {street} " in padded or _normalize(site.name) in text:
            return site, "address"

    for site in sites:
        city = _city(site.address)
        if city and f" {city} " in padded:
            return site, "city"
    return None
