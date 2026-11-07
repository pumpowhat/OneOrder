from datetime import datetime
import io
import json
import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Response
from openpyxl import load_workbook
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db import OrderModel, get_db, order_model_to_dict, record_audit_log
from backend.erp import get_group_inventory
from backend.erp.mock_erp import ReservationRejected, reserve_for_order
from backend.erp.reservations import apply_reservations
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
    customer: str | None = Field(default=None, max_length=255, description="Required when OCR found no customer name")


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
    change is audit-logged). Nothing is reserved in any ERP; that is /confirm. Stock already reserved by confirmed orders is not offered again.
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
        inventory = apply_reservations(get_group_inventory(), db)
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


class ConfirmOrderRequest(BaseModel):
    user: str = "sales_desk"
    allow_partial: bool = Field(default=False, description="Confirm although the plan has shortages")
    accept_late_risk: bool = Field(default=False, description="Confirm although the predicted ETA is late")


@router.post("/{order_id}/confirm")
def confirm_order(
    order_id: str,
    payload: ConfirmOrderRequest = Body(default_factory=ConfirmOrderRequest),
    db: Session = Depends(get_db),
) -> dict:
    """Reserve the planned stock in the (mock) ERPs and mark the order `confirmed`. Final.

    The stored plan, including its ETA, is frozen as the commitment. Everything is checked before
    anything is written, and written in one transaction, so a rejected confirm changes nothing.
    - 404 unknown order; 409 order is not `planned` (or has no plan);
    - 409 plan has shortages (unless `allow_partial`) or its ETA is `late` (unless `accept_late_risk`);
    - 409 stock was taken by another order since planning (plan again);
    - 503 stock data unavailable.
    """
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    _require_transition(order, OrderStatus.CONFIRMED, hint="plan the order before confirming")
    if order.status != OrderStatus.PLANNED.value or not order.plan:
        raise HTTPException(status_code=409, detail=f"Order {order_id} has no stored plan to confirm")

    try:
        plan = FulfillmentPlan.model_validate_json(order.plan)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=f"Order {order_id}: stored plan is invalid, plan again") from exc

    if plan.shortages and not payload.allow_partial:
        missing = ", ".join(f"{s.sku} (missing {s.missing:g})" for s in plan.shortages)
        raise HTTPException(
            status_code=409,
            detail=f"Order {order_id}: plan has shortages: {missing}. Send allow_partial=true to confirm anyway",
        )
    if plan.order_eta and plan.order_eta.risk == "late" and not payload.accept_late_risk:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Order {order_id}: predicted arrival {plan.order_eta.p50_date} (P50) is after the requested date "
                f"{plan.requested_date}. Send accept_late_risk=true to confirm anyway"
            ),
        )

    try:
        reserved_lines = reserve_for_order(db, order.id, plan.shipments)
    except ReservationRejected as exc:
        raise HTTPException(
            status_code=409,
            detail=f"Order {order_id}: stock changed since planning ({exc}). Plan the order again",
        ) from exc
    except (FileNotFoundError, KeyError, ValueError) as exc:
        logger.error("ERP unavailable while confirming order %s: %s", order_id, exc)
        raise HTTPException(status_code=503, detail=f"Stock data unavailable: {exc}") from exc

    before_status = order.status
    order.status = OrderStatus.CONFIRMED.value
    record_audit_log(
        db,
        order_id=order.id,
        action="confirm",
        user=payload.user,
        payload_before={"status": before_status},
        payload_after={
            "status": OrderStatus.CONFIRMED.value,
            "reservations": reserved_lines,
            "shipments": len(plan.shipments),
            "allow_partial": payload.allow_partial,
            "accept_late_risk": payload.accept_late_risk,
            "order_eta": plan.order_eta.model_dump() if plan.order_eta else None,
        },
    )
    db.commit()
    db.refresh(order)
    return order_model_to_dict(order)


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

    # The customer name is mandatory: if OCR did not find one, the clerk must type it
    customer_name = (payload.customer or "").strip() or (order.customer or "").strip()
    if not customer_name:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot approve order {order_id}: customer name is missing, enter it to approve",
        )

    # Record a customer name entered by hand
    if customer_name != (order.customer or ""):
        record_audit_log(
            db,
            order_id=order.id,
            action="set_customer",
            user=payload.user,
            payload_before={"customer": order.customer},
            payload_after={"customer": customer_name},
        )
        order.customer = customer_name

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


# --- read-only views for the UI ---------------------------------------------------------------------


def _order_summary(order: OrderModel) -> dict:
    """One row of the orders list: enough for the dashboard and the list without loading each order."""
    plan = json.loads(order.plan) if order.plan else None
    order_eta = plan.get("order_eta") if plan else None
    review_lines = sum(
        1
        for line in order.lines
        if line_needs_review(
            line.confidence, line.match_score, line.matched_sku, bool(line.confirmed), bool(line.ambiguous)
        )
    )
    return {
        "id": order.id,
        "status": order.status,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "source_type": order.source_type,
        "source_name": order.source_name,
        "customer": order.customer,
        "delivery_site": order.delivery_site,
        "requested_date": order.requested_date,
        "line_count": len(order.lines),
        "review_lines": review_lines,
        "shortage_count": len(plan["shortages"]) if plan else 0,
        "shipment_count": len(plan["shipments"]) if plan else 0,
        "p50_date": order_eta["p50_date"] if order_eta else None,
        "p90_date": order_eta["p90_date"] if order_eta else None,
        "risk": order_eta["risk"] if order_eta else None,
    }


@router.get("")
def list_orders(status: str | None = None, db: Session = Depends(get_db)) -> list[dict]:
    """All orders, newest first, as short summaries. Optional ``?status=draft`` filter."""
    query = db.query(OrderModel)
    if status:
        query = query.filter(OrderModel.status == status)
    return [_order_summary(o) for o in query.order_by(OrderModel.created_at.desc()).all()]


_PREVIEW_ROWS = 200


@router.get("/{order_id}/source")
def get_order_source(order_id: str, db: Session = Depends(get_db)) -> dict:
    """The original input of an order in a form the UI can show next to the extracted lines.

    ``kind`` is ``image`` (fetch the picture from ``/source/file``), ``text`` (email body) or
    ``table`` (first rows of the spreadsheet).
    """
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    if order.source_content is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} has no stored original")

    base = {"name": order.source_name, "mime": order.source_mime, "source_type": order.source_type}
    if order.source_type == "image":
        return {**base, "kind": "image"}
    if order.source_type == "excel":
        try:
            sheet = load_workbook(io.BytesIO(order.source_content), read_only=True, data_only=True).active
            rows = [
                ["" if c is None else str(c) for c in row]
                for row in sheet.iter_rows(values_only=True)
                if any(c is not None for c in row)
            ]
        except Exception as exc:  # corrupt workbook: the download link still works
            raise HTTPException(status_code=422, detail=f"Cannot read the stored spreadsheet: {exc}") from exc
        return {**base, "kind": "table", "rows": rows[:_PREVIEW_ROWS], "truncated": len(rows) > _PREVIEW_ROWS}
    return {**base, "kind": "text", "text": order.source_content.decode("utf-8", errors="replace")}


@router.get("/{order_id}/source/file")
def get_order_source_file(order_id: str, db: Session = Depends(get_db)) -> Response:
    """The original bytes (photo, .xlsx or email text) exactly as uploaded."""
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order or order.source_content is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} has no stored original")
    return Response(content=order.source_content, media_type=order.source_mime or "application/octet-stream")


@router.get("/{order_id}/availability")
def order_availability(order_id: str, db: Session = Depends(get_db)) -> list[dict]:
    """Pre-check of every line against the stock of all three countries (reservations deducted).

    ``status``: ``ok`` the group can cover the line, ``partial`` only part of it, ``none`` no stock,
    ``unmatched`` the line has no catalogue SKU yet. Lines of the same SKU share the stock.
    """
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    try:
        inventory = apply_reservations(get_group_inventory(), db)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=f"Stock data unavailable: {exc}") from exc

    pool: dict[str, dict[str, float]] = {}
    for item in inventory:
        by_country = pool.setdefault(item.sku, {})
        by_country[item.country] = by_country.get(item.country, 0) + float(item.available_quantity)

    result = []
    for line in order.lines:
        sku = line.matched_sku
        if not sku:
            result.append({"line_index": line.line_index, "sku": None, "requested": line.quantity,
                           "available": 0, "by_country": {}, "status": "unmatched"})
            continue
        by_country = pool.get(sku, {})
        available = sum(by_country.values())
        status = "ok" if available + 1e-9 >= line.quantity else ("partial" if available > 0 else "none")
        result.append({"line_index": line.line_index, "sku": sku, "requested": line.quantity,
                       "available": available, "by_country": dict(by_country), "status": status})
        # later lines of the same SKU only see what is left
        remaining = line.quantity
        for country in sorted(by_country, key=by_country.get, reverse=True):
            take = min(by_country[country], remaining)
            by_country[country] -= take
            remaining -= take
    return result
