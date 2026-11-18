"""Write confirmed orders to the CRM, without ever letting the CRM block a confirmation.

The order is confirmed and its stock reserved first, in its own transaction. Only then is the CRM written:
- the delivery site's country has no CRM, or no customer was linked at review: ``not_applicable``;
- the CRM accepts the order: ``synced``, with the CRM's record id;
- a temporary failure (timeout, 429, 5xx): ``pending``; the worker tries again after a back-off, at most
  ``MAX_ATTEMPTS`` attempts in all, then ``failed``;
- the CRM refuses the order (4xx, bad configuration): ``failed`` at once, since sending it again would not help.

A person can retry a ``pending`` or ``failed`` sync; that starts a fresh round of attempts. Every write is an
upsert on the OneOrder order id, so a retry never creates a second CRM order.
"""

from datetime import date, datetime, timedelta, timezone

from backend.crm import CrmError, CrmOrder, CrmPermanentError, CrmRegistry, CrmTransientError
from backend.db import OrderModel, record_audit_log
from backend.services.orchestration import FulfillmentPlan

MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (30, 120)  # wait after the 1st and the 2nd failed attempt
SYNCED, PENDING, FAILED, NOT_APPLICABLE = "synced", "pending", "failed", "not_applicable"
RETRYABLE = (PENDING, FAILED)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _plan(order: OrderModel) -> FulfillmentPlan:
    return FulfillmentPlan.model_validate_json(order.plan)


def _confirmed_on(order: OrderModel) -> date:
    stamp = next((log.timestamp for log in order.audit_logs if log.action == "confirm"), None)
    return stamp.date() if stamp else _now().date()


def build_crm_order(order: OrderModel, plan: FulfillmentPlan) -> CrmOrder:
    eta = plan.order_eta
    lines = "\n".join(
        f"- {line.quantity:g} {line.unit or ''} {line.matched_sku or ''} {line.description}".replace("  ", " ")
        for line in order.lines
    )
    description = (
        f"OneOrder {order.id}\n"
        f"Customer: {order.customer or '-'} ({order.customer_phone or '-'})\n"
        f"Delivery: {plan.site.name} ({plan.site.country}), {len(plan.shipments)} shipment(s)\n"
        f"Requested: {plan.requested_date or '-'} | Expected (P50): {eta.p50_date if eta else '-'} | "
        f"Promised (P90): {eta.p90_date if eta else '-'}\n"
        f"Lines:\n{lines}"
    )
    return CrmOrder(
        order_id=order.id,
        account_id=order.crm_account_id,
        contact_id=order.crm_contact_id,
        confirmed_on=_confirmed_on(order),
        requested_date=plan.requested_date,
        expected_date=eta.p50_date if eta else None,
        promised_date=eta.p90_date if eta else None,
        description=description,
    )


def start_sync(db, order: OrderModel, registry: CrmRegistry, user: str) -> None:
    """Called once, right after /confirm committed. Decides whether the order belongs in a CRM and tries once."""
    country = _plan(order).site.country
    if registry.system_for(country) == "none":
        _set(order, NOT_APPLICABLE, reason="crm_disabled")  # no CRM call, so nothing to audit; crm_sync shows why
    elif not order.crm_account_id:
        _set(order, NOT_APPLICABLE, reason="no_account")
    else:
        order.crm_sync_attempts = 0
        attempt_sync(db, order, registry, user)


def attempt_sync(db, order: OrderModel, registry: CrmRegistry, user: str, now: datetime | None = None) -> None:
    """One write to the CRM; records the outcome on the order and in the audit log."""
    now = now or _now()
    attempts = (order.crm_sync_attempts or 0) + 1
    order.crm_sync_attempts, order.crm_sync_last_at = attempts, now
    try:
        directory = registry.for_country(_plan(order).site.country)
        record_id = directory.push_order(build_crm_order(order, _plan(order)))
    except CrmTransientError as exc:
        if attempts < MAX_ATTEMPTS:
            wait = max(BACKOFF_SECONDS[min(attempts, len(BACKOFF_SECONDS)) - 1], exc.retry_after or 0)
            _set(order, PENDING, error=str(exc), next_at=now + timedelta(seconds=wait))
        else:
            _set(order, FAILED, error=f"{exc} (gave up after {attempts} attempts)")
        _audit_failure(db, order, user, attempts)
    except (CrmPermanentError, CrmError, ValueError) as exc:
        _set(order, FAILED, error=str(exc))
        _audit_failure(db, order, user, attempts)
    else:
        _set(order, SYNCED, record_id=record_id)
        record_audit_log(
            db, order.id, "crm_sync", user, None, {"status": SYNCED, "crm_record_id": record_id, "attempt": attempts}
        )


def retry_sync(db, order: OrderModel, registry: CrmRegistry, user: str) -> None:
    """A person asked to try again: a fresh round of attempts, starting now."""
    record_audit_log(
        db, order.id, "crm_sync_retry", user, {"status": order.crm_sync_status, "attempts": order.crm_sync_attempts}, None
    )
    order.crm_sync_attempts = 0
    attempt_sync(db, order, registry, user)


def retry_due(db, registry: CrmRegistry, now: datetime | None = None, user: str = "crm_worker") -> int:
    """Try every pending sync whose back-off has passed. Returns how many were tried. Used by the worker."""
    now = now or _now()
    due = [
        order
        for order in db.query(OrderModel).filter(OrderModel.crm_sync_status == PENDING).all()
        if order.crm_sync_next_at is None or _aware(order.crm_sync_next_at) <= now
    ]
    for order in due:
        attempt_sync(db, order, registry, user, now)
        db.commit()
    return len(due)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)  # SQLite returns naive datetimes


def _set(order, status, reason=None, record_id=None, error=None, next_at=None) -> None:
    order.crm_sync_status, order.crm_sync_reason = status, reason
    order.crm_record_id = record_id if record_id is not None else (order.crm_record_id if status == SYNCED else None)
    order.crm_sync_error, order.crm_sync_next_at = error, next_at


def _audit_failure(db, order, user, attempts) -> None:
    record_audit_log(
        db,
        order.id,
        "crm_sync_failed",
        user,
        None,
        {
            "status": order.crm_sync_status,
            "error": order.crm_sync_error,
            "attempt": attempts,
            "next_attempt_at": order.crm_sync_next_at.isoformat() if order.crm_sync_next_at else None,
        },
    )
