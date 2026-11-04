"""Business rules loaded from data/rules.json (rules live in config, not in code)."""

from functools import lru_cache
import json
import os
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, model_validator

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_RULES_FILE = REPO_ROOT / "data" / "rules.json"
RULES_PATH_ENV = "RULES_PATH"

TIERS = ("branch", "domestic_dc", "cross_border_dc")


class IntakeRules(BaseModel):
    min_confidence: float = Field(default=0.85, ge=0, le=1)


class SourcingRules(BaseModel):
    priority: list[str] = Field(default_factory=lambda: list(TIERS))
    allow_cross_border: bool = True
    allow_line_split: bool = True
    branch_max_distance_km: float = Field(default=150, gt=0)
    max_shipments_per_order: int = Field(default=4, ge=1)

    @field_validator("priority")
    @classmethod
    def _valid_priority(cls, value: list[str]) -> list[str]:
        unknown = [tier for tier in value if tier not in TIERS]
        if unknown:
            raise ValueError(f"Unknown sourcing tier(s) {unknown}; allowed: {list(TIERS)}")
        if len(set(value)) != len(value):
            raise ValueError("Sourcing priority must not repeat a tier")
        if not value:
            raise ValueError("Sourcing priority must list at least one tier")
        return value


class DistanceRules(BaseModel):
    road_factor: float = Field(default=1.3, ge=1)


class VehicleRule(BaseModel):
    type: str
    max_weight_kg: float = Field(gt=0)
    crane: bool = False


class Rules(BaseModel):
    version: int = 1
    intake: IntakeRules = Field(default_factory=IntakeRules)
    sourcing: SourcingRules = Field(default_factory=SourcingRules)
    distance: DistanceRules = Field(default_factory=DistanceRules)
    vehicles: list[VehicleRule]
    country_lead_time_buffer_days: dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _vehicle_fleet(self) -> "Rules":
        if not any(not v.crane for v in self.vehicles):
            raise ValueError("Rules need at least one vehicle without crane")
        if not any(v.crane for v in self.vehicles):
            raise ValueError("Rules need at least one crane vehicle")
        return self


def resolve_rules_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(path)
    env_path = os.getenv(RULES_PATH_ENV)
    if env_path:
        p = Path(env_path)
        return p if p.is_absolute() else REPO_ROOT / p
    return DEFAULT_RULES_FILE


@lru_cache(maxsize=8)
def _read_rules(target_str: str) -> Rules:
    target = Path(target_str)
    if not target.exists():
        raise FileNotFoundError(f"Rules file not found: {target}")
    with open(target, encoding="utf-8") as f:
        return Rules.model_validate(json.load(f))


def load_rules(path: str | Path | None = None) -> Rules:
    """Load and validate rules. Raises FileNotFoundError or pydantic.ValidationError."""
    return _read_rules(str(resolve_rules_path(path)))


def clear_rules_cache() -> None:
    _read_rules.cache_clear()
