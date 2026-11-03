from dataclasses import dataclass, field
import json
import os
from pathlib import Path

DEFAULT_CATALOG_ENV = "CATALOG_PATH"
DEFAULT_CATALOG_FILE = "data/catalog.json"
SAMPLE_CATALOG_FILE = Path(__file__).resolve().parent.parent.parent.parent / "tests" / "fixtures" / "catalog_sample.json"


@dataclass
class CatalogItem:
    sku: str
    name: str
    unit: str | None = None
    aliases: list[str] = field(default_factory=list)


def resolve_catalog_path(path: str | Path | None = None) -> Path:
    """Find the catalog file to use: explicit path, env var, default, or test sample."""
    if path:
        return Path(path)
    env_path = os.getenv(DEFAULT_CATALOG_ENV)
    if env_path:
        return Path(env_path)
    default_p = Path(DEFAULT_CATALOG_FILE)
    if default_p.exists():
        return default_p
    if SAMPLE_CATALOG_FILE.exists():
        return SAMPLE_CATALOG_FILE
    return default_p


def load_catalog(path: str | Path | None = None) -> list[CatalogItem]:
    """Read catalog products from JSON file.

    Expects a JSON array of objects with 'sku', 'name', optional 'unit' and 'aliases'.
    """
    target = resolve_catalog_path(path)
    if not target.exists():
        raise FileNotFoundError(f"Catalog file not found: {target}")

    with open(target, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Catalog JSON must be a list of items, got {type(data).__name__}")

    catalog = []
    for entry in data:
        catalog.append(
            CatalogItem(
                sku=str(entry["sku"]).strip(),
                name=str(entry["name"]).strip(),
                unit=str(entry["unit"]).strip() if entry.get("unit") else None,
                aliases=[str(a).strip() for a in entry.get("aliases") or [] if str(a).strip()],
            )
        )
    return catalog
