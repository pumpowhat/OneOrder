"""Which CRM each country uses (``crm`` in rules.json) and the adapter for it.

``CRM_MODE=mock`` (default) serves Salesforce from ``samples/crm`` so the app runs without an org or network;
``CRM_MODE=live`` calls the real org configured by the ``SF_*`` variables. The mode is the same idea as
``AI_MODE``: the order flow never knows which one it is talking to.
"""

from functools import lru_cache
import os
from pathlib import Path

from backend.services.orchestration import load_rules

from .base import CustomerDirectory, NoCrmDirectory
from .mock import DEFAULT_MOCK_DIR, MockSalesforceDirectory, parse_fail_modes
from .salesforce import SalesforceDirectory


def crm_mode() -> str:
    return "live" if os.getenv("CRM_MODE", "mock").lower() == "live" else "mock"


@lru_cache(maxsize=8)
def _shared_directory(system: str, mode: str, country: str) -> CustomerDirectory:
    """One adapter per (system, mode, country) for the whole process, so the mock keeps what it was sent."""
    if system == "salesforce":
        if mode == "live":
            return SalesforceDirectory.from_env(country)
        mock_dir = Path(os.getenv("CRM_MOCK_DIR") or DEFAULT_MOCK_DIR)
        mock = MockSalesforceDirectory.from_csv(mock_dir, country)
        mock.fail_modes = parse_fail_modes(os.getenv("CRM_MOCK_FAIL"))  # the starting state; the API can change it
        return mock
    raise ValueError(f"Unknown CRM system '{system}'")


class CrmRegistry:
    """Looks up the adapter for a country from the current rules. Tests pass ``directories`` to replace them."""

    def __init__(self, directories: dict[str, CustomerDirectory] | None = None):
        self._overrides = {k.upper(): v for k, v in (directories or {}).items()}

    def system_for(self, country: str | None) -> str:
        if not country:
            return "none"
        return load_rules().crm.get(country.upper(), "none")

    def enabled_countries(self) -> list[str]:
        return sorted(c for c, system in load_rules().crm.items() if system != "none")

    def for_country(self, country: str | None) -> CustomerDirectory:
        code = (country or "").upper()
        system = self.system_for(code)
        if system == "none":
            return NoCrmDirectory(code)
        if code in self._overrides:
            return self._overrides[code]
        return _shared_directory(system, crm_mode(), code)


def get_crm_registry() -> CrmRegistry:
    """FastAPI dependency; override it in tests with a registry built from mock directories."""
    return CrmRegistry()


def clear_crm_cache() -> None:
    _shared_directory.cache_clear()
