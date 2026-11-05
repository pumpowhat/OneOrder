from datetime import datetime, timezone
import json
import os
import uuid
from typing import Generator

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, inspect, text
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

from backend.services.intake.schemas import line_needs_review

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./oneorder.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


class OrderModel(Base):
    """Persisted customer order with lines and history."""

    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    status = Column(String(20), default="draft", nullable=False)  # see backend/services/orders/status.py
    source_type = Column(String(20), nullable=False)
    source_name = Column(String(255), nullable=True)
    customer = Column(String(255), nullable=True)
    delivery_site = Column(String(255), nullable=True)
    requested_date = Column(String(20), nullable=True)
    warnings = Column(Text, nullable=True)
    plan = Column(Text, nullable=True)  # JSON of the latest fulfilment plan, set by /plan

    lines = relationship(
        "OrderLineModel",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderLineModel.line_index",
    )
    audit_logs = relationship(
        "AuditLogModel",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="AuditLogModel.timestamp",
    )
    reservations = relationship(
        "ReservationModel",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="ReservationModel.id",
    )


class OrderLineModel(Base):
    """Single material line belonging to an order."""

    __tablename__ = "order_lines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False)
    line_index = Column(Integer, nullable=False, default=0)
    description = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=False)
    source_text = Column(Text, nullable=True)
    matched_sku = Column(String(100), nullable=True)
    match_score = Column(Float, nullable=True)
    candidates = Column(Text, nullable=True)  # JSON-encoded list of candidate dicts
    confirmed = Column(Integer, default=0, nullable=False)  # 1 when verified by user
    ambiguous = Column(Integer, default=0, nullable=False)  # 1 when candidates had close scores

    order = relationship("OrderModel", back_populates="lines")


class ReservationModel(Base):
    """Stock reserved for a confirmed order: the mock ERPs' "write reservation" (see POST /confirm)."""

    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    warehouse_code = Column(String(50), nullable=False, index=True)
    sku = Column(String(100), nullable=False, index=True)
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), nullable=True)
    shipment_index = Column(Integer, nullable=True)

    order = relationship("OrderModel", back_populates="reservations")


class AuditLogModel(Base):
    """Immutable audit entry tracking every draft creation, line edit, and approval."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    order_id = Column(String(36), ForeignKey("orders.id"), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # "create_draft", "edit_line", "confirm_line", "approve", "plan", "cancel"
    user = Column(String(100), default="sales_desk", nullable=False)
    payload_before = Column(Text, nullable=True)  # JSON-encoded snapshot before change
    payload_after = Column(Text, nullable=True)  # JSON-encoded snapshot after change

    order = relationship("OrderModel", back_populates="audit_logs")


_db_initialized = False


def _ensure_columns(target_engine) -> None:
    """Add columns introduced after a database file was first created (create_all never alters tables)."""
    inspector = inspect(target_engine)
    if "orders" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("orders")}
    if "plan" not in existing:
        with target_engine.begin() as conn:
            conn.execute(text("ALTER TABLE orders ADD COLUMN plan TEXT"))


def init_db(target_engine=None) -> None:
    """Create all database tables if they do not exist, and add newer columns to old ones."""
    global _db_initialized
    Base.metadata.create_all(bind=target_engine or engine)
    _ensure_columns(target_engine or engine)
    if target_engine is None or target_engine is engine:
        _db_initialized = True


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session."""
    global _db_initialized
    if not _db_initialized:
        init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def record_audit_log(
    db: Session,
    order_id: str,
    action: str,
    user: str = "sales_desk",
    payload_before: dict | list | None = None,
    payload_after: dict | list | None = None,
) -> AuditLogModel:
    """Record an audit trail event for an order."""
    entry = AuditLogModel(
        order_id=order_id,
        action=action,
        user=user,
        payload_before=json.dumps(payload_before, default=str, ensure_ascii=False) if payload_before is not None else None,
        payload_after=json.dumps(payload_after, default=str, ensure_ascii=False) if payload_after is not None else None,
    )
    db.add(entry)
    return entry


def save_draft_order(db: Session, order, user: str = "sales_desk") -> OrderModel:
    """Persist a DraftOrder into the database, generating an id and recording an audit log."""
    if not order.id:
        order.id = str(uuid.uuid4())

    db_order = OrderModel(
        id=order.id,
        status=order.status or "draft",
        source_type=order.source_type.value if hasattr(order.source_type, "value") else str(order.source_type),
        source_name=order.source_name,
        customer=order.customer,
        delivery_site=order.delivery_site,
        requested_date=order.requested_date.isoformat() if order.requested_date else None,
        warnings=json.dumps(order.warnings, ensure_ascii=False) if order.warnings else None,
    )
    db.add(db_order)

    for idx, line in enumerate(order.lines):
        cand_data = [c.model_dump() if hasattr(c, "model_dump") else c for c in line.candidates]
        db_line = OrderLineModel(
            order_id=order.id,
            line_index=idx,
            description=line.description,
            quantity=line.quantity,
            unit=line.unit,
            confidence=line.confidence,
            source_text=line.source_text,
            matched_sku=line.matched_sku,
            match_score=line.match_score,
            candidates=json.dumps(cand_data, ensure_ascii=False) if cand_data else None,
            confirmed=1 if getattr(line, "confirmed", False) else 0,
            ambiguous=1 if getattr(line, "ambiguous", False) else 0,
        )
        db.add(db_line)

    order_dump = order.model_dump(mode="json") if hasattr(order, "model_dump") else order.__dict__
    record_audit_log(
        db,
        order_id=order.id,
        action="create_draft",
        user=user,
        payload_before=None,
        payload_after=order_dump,
    )
    db.commit()
    db.refresh(db_order)
    return db_order


def order_model_to_dict(model: OrderModel) -> dict:
    """Convert an OrderModel and its lines/audit logs into a serializable dict."""
    lines = []
    for l in model.lines:
        cands = []
        if l.candidates:
            try:
                cands = json.loads(l.candidates)
            except Exception:
                pass

        line_needs_review_val = line_needs_review(
            confidence=l.confidence,
            match_score=l.match_score,
            matched_sku=l.matched_sku,
            confirmed=bool(l.confirmed),
            ambiguous=bool(getattr(l, "ambiguous", 0)),
        )

        lines.append({
            "line_index": l.line_index,
            "description": l.description,
            "quantity": l.quantity,
            "unit": l.unit,
            "confidence": l.confidence,
            "source_text": l.source_text,
            "matched_sku": l.matched_sku,
            "match_score": l.match_score,
            "candidates": cands,
            "confirmed": bool(l.confirmed),
            "ambiguous": bool(getattr(l, "ambiguous", 0)),
            "needs_review": line_needs_review_val,
        })

    logs = []
    for log in model.audit_logs:
        before = None
        after = None
        if log.payload_before:
            try:
                before = json.loads(log.payload_before)
            except Exception:
                before = log.payload_before
        if log.payload_after:
            try:
                after = json.loads(log.payload_after)
            except Exception:
                after = log.payload_after

        logs.append({
            "id": log.id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "action": log.action,
            "user": log.user,
            "payload_before": before,
            "payload_after": after,
        })

    warnings = json.loads(model.warnings) if model.warnings else []
    plan = json.loads(model.plan) if model.plan else None
    return {
        "id": model.id,
        "status": model.status,
        "source_type": model.source_type,
        "source_name": model.source_name,
        "customer": model.customer,
        "delivery_site": model.delivery_site,
        "requested_date": model.requested_date,
        "lines": lines,
        "warnings": warnings,
        "needs_review": any(l["needs_review"] for l in lines),
        "plan": plan,
        "reservations": [
            {
                "warehouse_code": r.warehouse_code,
                "sku": r.sku,
                "quantity": r.quantity,
                "unit": r.unit,
                "shipment_index": r.shipment_index,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in model.reservations
        ],
        "audit_logs": logs,
    }
