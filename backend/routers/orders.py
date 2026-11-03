from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db import OrderModel, get_db, order_model_to_dict, record_audit_log

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

    Returns 409 if any line lacks an SKU or has unresolved review requirements.
    Accepts human corrections and confirmations in the body, writing audit logs for each.
    """
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

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
        if corr.quantity is not None:
            line.quantity = corr.quantity
        if corr.description is not None:
            line.description = corr.description
        if corr.confirmed:
            line.confirmed = 1

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

        needs_review = (
            line.confidence < 0.85
            or (line.match_score is not None and line.match_score < 0.60)
            or line.matched_sku is None
        )
        if needs_review and not line.confirmed:
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
