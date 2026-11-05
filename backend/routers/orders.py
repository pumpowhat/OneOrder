from datetime import datetime
import json
import logging

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db import OrderModel, get_db, order_model_to_dict, record_audit_log
from backend.erp import get_group_inventory
from backend.services.eta import attach_eta
from backend.services.intake.schemas import line_needs_review
from backend.services.matching import load_catalog
from backend.services.orders import InvalidTransition, OrderStatus, require_transition
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


def _require_transition(order: OrderModel, target: OrderStatus, hint: str | None = None) -> None:
    """Turn an invalid status change into a 409 that names the order and its current status."""
    try:
        require_transition(order.status, target)
    except InvalidTransition as exc:
        detail = f"Order {order.id}: {exc}"
        if hint:
            detail += f" ({hint})"
        raise HTTPException(status_code=409, detail=detail) from exc


class PlanOrderRequest(BaseModel):
    user: str = "sales_desk"
    site_id: str | None = Field(
        default=None, description="Override the delivery site (e.g. SITE-NO-01) when the address does not match"
    )


@router.post("/{order_id}/plan", response_model=FulfillmentPlan)
def plan_order(
    order_id: str,
    payload: PlanOrderRequest = Body(default_factory=PlanOrderRequest),
    db: Session = Depends(get_db),
) -> FulfillmentPlan:
    """Build a multi-warehouse fulfilment plan, store it on the order and mark the order `planned`.

    Allowed from `approved` and from `planned` (planning again overwrites the stored plan, and the
    change is audit-logged). Nothing is reserved in any ERP; that is /confirm.
    - 404 unknown order, 409 order is draft / confirmed / cancelled, 422 site cannot be resolved or
      SKU unknown, 503 data or rules files missing/invalid. On any error the order is left untouched.
    """
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    _require_transition(order, OrderStatus.PLANNED, hint="approve the order before planning")

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
        result = plan_fulfillment(
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

    try:
        result = attach_eta(result, datetime.now())
    except Exception as exc:  # ETA is additive: a model/data problem must not block planning
        logger.exception("ETA failed for order %s", order_id)
        result.warnings.append(f"ETA unavailable: {exc}")

    previous = json.loads(order.plan) if order.plan else None
    before_status = order.status
    order.plan = result.model_dump_json()
    order.status = OrderStatus.PLANNED.value
    record_audit_log(
        db,
        order_id=order.id,
        action="plan",
        user=payload.user,
        payload_before={
            "status": before_status,
            "shipments": len(previous["shipments"]) if previous else None,
        },
        payload_after={
            "status": OrderStatus.PLANNED.value,
            "site_id": result.site.id,
            "shipments": len(result.shipments),
            "total_weight_kg": result.total_weight_kg,
            "fully_sourced": result.fully_sourced,
        },
    )
    db.commit()
    return result


class CancelOrderRequest(BaseModel):
    user: str = "sales_desk"
    reason: str | None = Field(default=None, max_length=500)


@router.post("/{order_id}/cancel")
def cancel_order(
    order_id: str,
    payload: CancelOrderRequest = Body(default_factory=CancelOrderRequest),
    db: Session = Depends(get_db),
) -> dict:
    """Cancel an order that is not confirmed yet (draft, approved or planned).

    The stored plan is kept for history. 409 for confirmed or already cancelled orders: reservations
    in the ERPs would have to be released first, which is outside the MVP.
    """
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    _require_transition(order, OrderStatus.CANCELLED)

    before_status = order.status
    order.status = OrderStatus.CANCELLED.value
    record_audit_log(
        db,
        order_id=order.id,
        action="cancel",
        user=payload.user,
        payload_before={"status": before_status},
        payload_after={"status": OrderStatus.CANCELLED.value, "reason": payload.reason},
    )
    db.commit()
    db.refresh(order)
    return order_model_to_dict(order)


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

    if order.status == OrderStatus.APPROVED.value:
        raise HTTPException(status_code=409, detail=f"Order {order_id} has already been approved")
    _require_transition(order, OrderStatus.APPROVED)

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
    order.status = OrderStatus.APPROVED.value
    record_audit_log(
        db,
        order_id=order.id,
        action="approve",
        user=payload.user,
        payload_before={"status": before_status},
        payload_after={"status": OrderStatus.APPROVED.value},
    )
    db.commit()
    db.refresh(order)

    return order_model_to_dict(order)
