"""CRM status, and a switch for simulated outages while demoing with the mock Salesforce.

    curl -X PUT localhost:8000/api/crm/mock-failure -H 'Content-Type: application/json' -d '{"modes": ["transient"]}'
    curl -X PUT localhost:8000/api/crm/mock-failure -H 'Content-Type: application/json' -d '{"modes": []}'

The switch only exists in ``CRM_MODE=mock``; against a real org it answers 409, so it can never fake an outage
of the live CRM.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.crm import CrmRegistry, MockSalesforceDirectory, crm_mode, get_crm_registry
from backend.crm.mock import FAIL_MODES, parse_fail_modes

router = APIRouter(prefix="/api/crm", tags=["crm"])


class MockFailure(BaseModel):
    modes: list[str] = Field(default_factory=list, description=f"Any of {list(FAIL_MODES)}; empty ends the outage")


def _mocks(crm: CrmRegistry) -> dict[str, MockSalesforceDirectory]:
    directories = {country: crm.for_country(country) for country in crm.enabled_countries()}
    return {c: d for c, d in directories.items() if isinstance(d, MockSalesforceDirectory)}


@router.get("/status")
def crm_status(crm: CrmRegistry = Depends(get_crm_registry)) -> dict:
    """Which country uses which CRM, the mode (mock or live), and any simulated outage."""
    mocks = _mocks(crm) if crm_mode() == "mock" else {}
    return {
        "mode": crm_mode(),
        "countries": {c: crm.system_for(c) for c in crm.enabled_countries()},
        "mock_failure": {c: sorted(d.fail_modes) for c, d in mocks.items()},
    }


@router.put("/mock-failure")
def set_mock_failure(body: MockFailure, crm: CrmRegistry = Depends(get_crm_registry)) -> dict:
    """Start or end a simulated Salesforce outage (demo only). 409 with a real CRM, 422 for an unknown mode."""
    if crm_mode() != "mock":
        raise HTTPException(409, "Simulated outages only exist with CRM_MODE=mock")
    try:
        modes = parse_fail_modes(",".join(body.modes))
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    mocks = _mocks(crm)
    if not mocks:
        raise HTTPException(409, "No country uses a CRM (rules.json 'crm'), so there is nothing to fail")
    for directory in mocks.values():
        directory.fail_modes = set(modes)
    return crm_status(crm)
