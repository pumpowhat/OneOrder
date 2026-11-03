from dataclasses import dataclass, field
from functools import lru_cache
import json
import os
from pathlib import Path

# Compute repository root directory (4 levels up from this file)
REPO_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_CATALOG_ENV = "CATALOG_PATH"
DEFAULT_CATALOG_FILE = REPO_ROOT / "data" / "catalog.json"
SAMPLE_CATALOG_FILE = REPO_ROOT / "tests" / "fixtures" / "catalog_sample.json"


@dataclass(frozen=True)
class CatalogItem:
    sku: str
    name: str
    unit: str | None = None
    aliases: tuple[str, ...] = field(default_factory=tuple)


def resolve_catalog_path(path: str | Path | None = None) -> Path:
    """Resolve the catalogue file path anchored to the repository root.

    Precedence:
    1. Explicit path passed as argument.
    2. CATALOG_PATH environment variable.
    3. Standard data/catalog.json.
    4. If in testing environment (PYTEST_CURRENT_TEST or USE_SAMPLE_CATALOG=1),
       and standard data/catalog.json is not present, fall back to tests/fixtures/catalog_sample.json.
    """
    if path:
        p = Path(path)
        return p if p.is_absolute() else (REPO_ROOT / p if (REPO_ROOT / p).exists() else p)

    env_path = os.getenv(DEFAULT_CATALOG_ENV)
    if env_path:
        p = Path(env_path)
        return p if p.is_absolute() else REPO_ROOT / p

    if DEFAULT_CATALOG_FILE.exists():
        return DEFAULT_CATALOG_FILE

    # Only fall back to test fixtures when explicitly in a test environment
    is_test_env = bool(
        os.getenv("USE_SAMPLE_CATALOG", "").lower() in ("1", "true", "yes")
        or "PYTEST_CURRENT_TEST" in os.environ
    )
    if is_test_env and SAMPLE_CATALOG_FILE.exists():
        return SAMPLE_CATALOG_FILE

    return DEFAULT_CATALOG_FILE


@lru_cache(maxsize=8)
def _read_catalog_file(target_str: str) -> tuple[CatalogItem, ...]:
    target = Path(target_str)
    if not target.exists():
        raise FileNotFoundError(
            f"Catalogue file not found: {target}. "
            f"Please ensure '{DEFAULT_CATALOG_FILE}' exists or configure {DEFAULT_CATALOG_ENV}."
        )

    with open(target, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Catalogue JSON must be a list of items, got {type(data).__name__}")

    items = []
    for entry in data:
        raw_aliases = entry.get("aliases") or []
        alias_tuple = tuple(str(a).strip() for a in raw_aliases if str(a).strip())
        items.append(
            CatalogItem(
                sku=str(entry["sku"]).strip(),
                name=str(entry["name"]).strip(),
                unit=str(entry["unit"]).strip() if entry.get("unit") else None,
                aliases=alias_tuple,
            )
        )
    return tuple(items)


def load_catalog(path: str | Path | None = None) -> list[CatalogItem]:
    """Read catalog products from JSON file with caching."""
    target = resolve_catalog_path(path)
    return list(_read_catalog_file(str(target)))


def clear_catalog_cache() -> None:
    """Clear cached catalogue data."""
    _read_catalog_file.cache_clear()
