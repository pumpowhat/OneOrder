"""Business rules (data/rules.json): read them, and change them with validation."""

import json
import os
from pathlib import Path
import tempfile

from fastapi import APIRouter, HTTPException

from backend.services.orchestration import Rules, clear_rules_cache, load_rules
from backend.services.orchestration.rules import resolve_rules_path

router = APIRouter(prefix="/api", tags=["rules"])


def _rules_json(rules: Rules) -> dict:
    return rules.model_dump(mode="json")


@router.get("/rules")
def get_rules() -> dict:
    try:
        return _rules_json(load_rules())
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=f"Rules unavailable: {exc}") from exc


@router.put("/rules")
def put_rules(rules: Rules) -> dict:
    """Replace the rules. The body is validated like the file (422 on a bad value) and the version goes up by 1.

    New plans use the new rules at once; plans already stored keep the ``rules_version`` they were made with.
    """
    target = resolve_rules_path()
    try:
        current = json.loads(target.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=f"Rules unavailable: {exc}") from exc

    updated = {**current, **_rules_json(rules)}
    if "crm" not in rules.model_fields_set and "crm" in current:
        updated["crm"] = current["crm"]  # a client that does not know the CRM block must not wipe it
    updated["version"] = int(current.get("version", 1)) + 1

    # write to a temp file next to the target, then swap it in: a crash never leaves half a file
    fd, tmp = tempfile.mkstemp(dir=target.parent, prefix=".rules-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(updated, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, target)
    except OSError as exc:
        Path(tmp).unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail=f"Cannot write rules: {exc}") from exc
    clear_rules_cache()
    return _rules_json(load_rules())
