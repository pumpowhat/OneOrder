import logging

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db import OrderModel, get_db, order_model_to_dict, record_audit_log
from backend.erp import get_group_inventory
from backend.services.intake.schemas import line_needs_review
from backend.services.matching import load_catalog
from backend.services.orchestration import (
    FulfillmentPlan,
    PlanLineInput,
    PlanningError,
    load_products,
    load_rules,
    load_sites,
    load_warehouses,
    plan_fulfillment,
    resolve_site,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["orders"])


class LineCorrection(BaseModel):
    line_index: int
    sku: str | None = None
    quantity: float | None = None
    description: str | None = None
    confirmed: bool = True


class ApproveOrderRequest(BaseModel):
    user: str = "sales_desk"
    corrections: list[LineCorrection] = Field(default_factory=list)
    confirm_lines: list[int] = Field(default_factory=list)


class PlanOrderRequest(BaseModel):
    site_id: str | None = Field(
        default=None, description="Override the delivery site (e.g. SITE-NO-01) when the address does not match"
    )


@router.post("/{order_id}/plan", response_model=FulfillmentPlan)
def plan_order(
    order_id: str,
    payload: PlanOrderRequest = Body(default_factory=PlanOrderRequest),
    db: Session = Depends(get_db),
) -> FulfillmentPlan:
    """Build a multi-warehouse fulfilment plan for an approved order.

    Read-only: nothing is reserved and the order status is not changed (ETA and /confirm come later).
    - 404 unknown order, 409 order not approved yet, 422 site cannot be resolved or SKU unknown,
      503 data or rules files missing/invalid.
    """
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    if order.status != "approved":
        raise HTTPException(
            status_code=409,
            detail=f"Order {order_id} must be approved before planning (status: {order.status})",
        )

    try:
        rules = load_rules()
        sites = load_sites()
        warehouses = load_warehouses()
        products = load_products()
        inventory = get_group_inventory()
    except (FileNotFoundError, KeyError, ValueError) as exc:
        logger.error("Planning data unavailable for order %s: %s", order_id, exc)
        raise HTTPException(status_code=503, detail=f"Planning data unavailable: {exc}") from exc

    resolved = resolve_site(order.delivery_site, sites, site_id=payload.site_id)
    if not resolved:
        known = ", ".join(s.id for s in sites)
        target = f"site_id '{payload.site_id}'" if payload.site_id else f"delivery site '{order.delivery_site}'"
        raise HTTPException(
            status_code=422,
            detail=f"Cannot resolve {target}. Send a site_id, one of: {known}",
        )
    site, match = resolved

    lines = [
        PlanLineInput(
            line_index=line.line_index,
            sku=line.matched_sku,
            quantity=line.quantity,
            description=line.description,
        )
        for line in order.lines
    ]
    try:
        return plan_fulfillment(
            lines,
            site,
            match,
            inventory,
            warehouses,
            products,
            rules,
            order_id=order.id,
            customer=order.customer,
            delivery_site=order.delivery_site,
            requested_date=order.requested_date,
        )
    except PlanningError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{order_id}")
def get_order(order_id: str, db: Session = Depends(get_db)) -> dict:
    """Retrieve an order by ID including all lines, candidate matches, and audit trail."""
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    return order_model_to_dict(order)


@router.post("/{order_id}/approve")
def approve_order(
    order_id: str,
    payload: ApproveOrderRequest = Body(default_factory=ApproveOrderRequest),
    db: Session = Depends(get_db),
) -> dict:
    """Approve a draft order.

    Validations:
    - Returns 409 if the order has already been approved.
    - Returns 400 if any corrected SKU does not exist in the catalogue or quantity <= 0.
    - Returns 409 if any line lacks an SKU or has unresolved review requirements.

    Transaction semantics:
    All corrections, confirmations, status updates, and audit logs are committed
    atomically. If validation fails with 409 or 400, no changes are committed to the DB.
    """
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

    if order.status == "approved":
        raise HTTPException(status_code=409, detail=f"Order {order_id} has already been approved")

    # Load valid catalogue SKUs to validate human corrections
    try:
        catalog = load_catalog()
        valid_skus = {item.sku for item in catalog}
    except Exception as exc:
        logger.error("Failed to load catalogue during order approval for %s: %s", order_id, exc)
        raise HTTPException(
            status_code=503,
            detail=f"Catalogue service unavailable: {exc}",
        ) from exc

    # Validate correction fields before applying
    for corr in payload.corrections:
        if corr.quantity is not None and corr.quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"Line quantity must be greater than 0, got {corr.quantity}",
            )
        if corr.sku is not None and corr.sku not in valid_skus:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid SKU '{corr.sku}': not found in catalogue",
            )

    # Apply manual corrections
    for corr in payload.corrections:
        line = next((l for l in order.lines if l.line_index == corr.line_index), None)
        if not line:
            raise HTTPException(status_code=400, detail=f"Invalid line index {corr.line_index}")

        before = {
            "line_index": line.line_index,
            "description": line.description,
            "matched_sku": line.matched_sku,
            "quantity": line.quantity,
            "confirmed": bool(line.confirmed),
        }

        if corr.sku is not None:
            line.matched_sku = corr.sku
            line.ambiguous = 0
        if corr.quantity is not None:
            line.quantity = corr.quantity
        if corr.description is not None:
            line.description = corr.description
        if corr.confirmed:
            line.confirmed = 1
            line.ambiguous = 0

        after = {
            "line_index": line.line_index,
            "description": line.description,
            "matched_sku": line.matched_sku,
            "quantity": line.quantity,
            "confirmed": bool(line.confirmed),
        }

        record_audit_log(
            db,
            order_id=order.id,
            action="edit_line",
            user=payload.user,
            payload_before=before,
            payload_after=after,
        )

    # Apply manual line confirmations
    for idx in payload.confirm_lines:
        line = next((l for l in order.lines if l.line_index == idx), None)
        if not line:
            raise HTTPException(status_code=400, detail=f"Invalid line index {idx}")
        if not line.confirmed:
            line.confirmed = 1
            line.ambiguous = 0
            record_audit_log(
                db,
                order_id=order.id,
                action="confirm_line",
                user=payload.user,
                payload_before={"line_index": idx, "confirmed": False},
                payload_after={"line_index": idx, "confirmed": True},
            )

    # Validate that all lines are ready for approval
    for line in order.lines:
        if not line.matched_sku:
            raise HTTPException(
                status_code=409,
                detail=f"Cannot approve order: line {line.line_index} ('{line.description}') is missing SKU",
            )

        if line.matched_sku not in valid_skus:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot approve order: SKU '{line.matched_sku}' on line {line.line_index} not found in catalogue",
            )

        if line_needs_review(
            confidence=line.confidence,
            match_score=line.match_score,
            matched_sku=line.matched_sku,
            confirmed=bool(line.confirmed),
            ambiguous=bool(getattr(line, "ambiguous", 0)),
        ):
            raise HTTPException(
                status_code=409,
                detail=f"Cannot approve order: line {line.line_index} ('{line.description}') requires review and has not been confirmed",
            )

    # Mark order as approved
    before_status = order.status
    order.status = "approved"
    record_audit_log(
        db,
        order_id=order.id,
        action="approve",
        user=payload.user,
        payload_before={"status": before_status},
        payload_after={"status": "approved"},
    )
    db.commit()
    db.refresh(order)

    return order_model_to_dict(order)
