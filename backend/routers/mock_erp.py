"""HTTP face of the simulated national ERPs: what each country's system would expose."""

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.db import get_db
from backend.erp import mock_erp

router = APIRouter(prefix="/mock-erp", tags=["mock-erp"])


class ReservationLine(BaseModel):
    warehouse: str
    sku: str
    quantity: float = Field(gt=0)
    unit: str | None = None


class ReservationRequest(BaseModel):
    order_ref: str = Field(min_length=1, max_length=36)
    lines: list[ReservationLine] = Field(min_length=1)


def _country(value: str) -> str:
    try:
        return mock_erp.normalize_country(value)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _row(r) -> dict:
    return {
        "order_ref": r.order_id,
        "warehouse": r.warehouse_code,
        "sku": r.sku,
        "quantity": r.quantity,
        "unit": r.unit,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.get("/{country}/stock")
def stock(country: str, db: Session = Depends(get_db)) -> Response:
    """Stock in the country's native format (DK: CSV, SE: Swedish-keyed JSON, NO: English-keyed JSON)."""
    body, media_type = mock_erp.native_stock(_country(country), db)
    return Response(content=body, media_type=media_type)


@router.get("/{country}/reservations")
def reservations(country: str, db: Session = Depends(get_db)) -> list[dict]:
    return [_row(r) for r in mock_erp.list_reservations(db, _country(country))]


@router.post("/{country}/reservations", status_code=201)
def create_reservation(country: str, payload: ReservationRequest, db: Session = Depends(get_db)) -> dict:
    """Reserve stock for an order. 409 when a warehouse cannot cover a line; nothing is written then."""
    code = _country(country)
    try:
        rows = mock_erp.reserve(db, code, payload.order_ref, [line.model_dump() for line in payload.lines], commit=True)
    except mock_erp.UnknownWarehouse as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except mock_erp.ReservationRejected as exc:
        raise HTTPException(status_code=409, detail=f"Insufficient stock: {exc}") from exc
    return {"order_ref": payload.order_ref, "country": code, "reserved": [_row(r) for r in rows]}


@router.delete("/{country}/reservations/{order_ref}")
def delete_reservation(country: str, order_ref: str, db: Session = Depends(get_db)) -> dict:
    """Release every reservation an order holds in this country's ERP."""
    released = mock_erp.release(db, _country(country), order_ref, commit=True)
    if released == 0:
        raise HTTPException(status_code=404, detail=f"No reservations for {order_ref} in the {country.upper()} ERP")
    return {"order_ref": order_ref, "country": _country(country), "released": released}
