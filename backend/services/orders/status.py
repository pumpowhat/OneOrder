"""Order lifecycle: the allowed statuses and the transitions between them.

    draft ──approve──► approved ──plan──► planned ──confirm──► confirmed
      │                   │                 │  ▲
      │                   │                 └──┘  plan again (re-plan)
      └───────────────────┴─────────────────┴──► cancelled

- `draft`: extracted from a photo / email / Excel, may still need human review.
- `approved`: every line reviewed by a person (AI proposes, humans decide).
- `planned`: a fulfilment plan is stored on the order. Planning again overwrites it.
- `confirmed`: stock reserved in the ERPs (POST /confirm); the stored plan and ETA are frozen. Final.
- `cancelled`: dropped before confirmation. Final. A confirmed order cannot be cancelled here
  because its ERP reservations would have to be released first (outside the MVP).

There is no `failed` status: a confirm that is rejected (shortage, late ETA, stock taken by another
order) answers 409 and leaves the order `planned`.
"""

from enum import Enum


class OrderStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    PLANNED = "planned"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.DRAFT: frozenset({OrderStatus.APPROVED, OrderStatus.CANCELLED}),
    OrderStatus.APPROVED: frozenset({OrderStatus.PLANNED, OrderStatus.CANCELLED}),
    OrderStatus.PLANNED: frozenset({OrderStatus.PLANNED, OrderStatus.CONFIRMED, OrderStatus.CANCELLED}),
    OrderStatus.CONFIRMED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
}


class InvalidTransition(ValueError):
    """Raised when an order cannot move from its current status to the requested one."""


def require_transition(current: str, target: OrderStatus) -> None:
    """Raise InvalidTransition unless `current` -> `target` is allowed."""
    try:
        source = OrderStatus(current)
    except ValueError as exc:
        raise InvalidTransition(f"Order has unknown status '{current}'") from exc
    if target not in TRANSITIONS[source]:
        allowed = ", ".join(sorted(s.value for s in TRANSITIONS[source])) or "none (final status)"
        raise InvalidTransition(
            f"Cannot move order from '{source.value}' to '{target.value}'; allowed from '{source.value}': {allowed}"
        )
