"""Output schema of the orchestration engine (the contract for POST /api/orders/{id}/plan)."""

from typing import Literal

from pydantic import BaseModel, Field

EtaRisk = Literal["on_time", "at_risk", "late"]
SourceTier = Literal["branch", "domestic_dc", "cross_border_dc"]
VehicleType = Literal["small_truck", "heavy_truck", "crane_truck"]


class PlanLineInput(BaseModel):
    """One approved order line handed to the engine."""

    line_index: int
    sku: str
    quantity: float = Field(gt=0)
    description: str | None = None


class ResolvedSite(BaseModel):
    id: str
    name: str
    country: str
    latitude: float
    longitude: float
    crane_accessible: bool
    match: Literal["site_id", "address", "city"]


class Allocation(BaseModel):
    """Part (or all) of one order line taken from one warehouse."""

    line_index: int
    sku: str
    description: str | None = None
    quantity: float
    unit: str | None = None
    weight_kg: float
    requires_crane: bool
    tier: SourceTier
    reason_code: str
    reason: str


class ShipmentETA(BaseModel):
    """Predicted delivery dates of one shipment (see backend/services/eta)."""

    dispatch_date: str
    baseline_date: str = Field(description="Earliest arrival if nothing goes wrong")
    p50_date: str = Field(description="Expected arrival (median)")
    p90_date: str = Field(description="Safe commitment date (90% of deliveries arrive by then)")
    delay_p50_days: int
    delay_p90_days: int
    risk: EtaRisk | None = Field(default=None, description="vs. the requested date; null when none was given")
    notes: list[str] = Field(default_factory=list)


class OrderETA(BaseModel):
    """Order-level ETA: the order is ready when its latest shipment arrives."""

    p50_date: str
    p90_date: str
    risk: EtaRisk | None = None


class Shipment(BaseModel):
    shipment_index: int
    origin_warehouse: str
    origin_name: str
    origin_country: str
    origin_type: Literal["branch", "dc"]
    tier: SourceTier
    destination_site: str
    destination_country: str
    cross_border: bool
    distance_km: float
    total_weight_kg: float
    crane_required: bool
    vehicle_type: VehicleType
    vehicle_count: int
    lines: list[Allocation]
    eta: ShipmentETA | None = None


class Shortage(BaseModel):
    line_index: int
    sku: str
    description: str | None = None
    requested: float
    allocated: float
    missing: float
    reason: str


class FulfillmentPlan(BaseModel):
    order_id: str | None = None
    customer: str | None = None
    delivery_site: str | None = None
    requested_date: str | None = None
    site: ResolvedSite
    shipments: list[Shipment]
    shortages: list[Shortage] = Field(default_factory=list)
    total_weight_kg: float
    fully_sourced: bool
    warnings: list[str] = Field(default_factory=list)
    rules_version: int
    order_eta: OrderETA | None = None
