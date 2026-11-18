"""The CRM interface OneOrder depends on: look customers up at review, record confirmed orders.

OneOrder never talks to a CRM directly. Each country's CRM sits behind a ``CustomerDirectory``, the same way
each ERP sits behind an adapter, so a country moving CRM (Dynamics 365 to Salesforce in Denmark) changes one
line of ``rules.json``, not the order flow.
"""

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Protocol


class CrmError(Exception):
    """A CRM call failed."""


class CrmTransientError(CrmError):
    """Worth retrying: timeout, rate limit (429) or a server error (5xx)."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class CrmPermanentError(CrmError):
    """Retrying the same request will not help: the CRM rejected it (4xx) or is not configured."""


@dataclass(frozen=True)
class CrmContact:
    contact_id: str
    name: str
    phone: str | None = None
    email: str | None = None


@dataclass(frozen=True)
class CrmAccount:
    """A customer company as the CRM stores it."""

    account_id: str
    name: str
    country: str
    phone: str | None = None
    city: str | None = None
    contacts: tuple[CrmContact, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class CustomerCandidate:
    """One suggestion shown at review. A person picks it; OneOrder never links a customer on its own."""

    crm_account_id: str
    crm_contact_id: str | None
    name: str
    phone: str | None
    city: str | None
    country: str
    score: float
    matched_on: str  # "phone" | "name"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class CrmOrder:
    """What OneOrder writes to the CRM when an order is confirmed. ``order_id`` is the idempotency key."""

    order_id: str
    account_id: str
    contact_id: str | None
    confirmed_on: date
    requested_date: str | None
    expected_date: str | None  # P50
    promised_date: str | None  # P90, the date the sales desk commits to
    description: str


class CustomerDirectory(Protocol):
    system: str  # "salesforce" | "none"
    country: str

    def find_customers(self, name: str | None, phone: str | None, limit: int = 5) -> list[CustomerCandidate]:
        """Customers that may be the one on the order, best first. Raises CrmError when the CRM fails."""
        ...

    def push_order(self, order: CrmOrder) -> str:
        """Create or update the CRM order for ``order.order_id`` and return its CRM record id.

        Calling it twice for the same order must not create a second record."""
        ...


class NoCrmDirectory:
    """The adapter for a country without a CRM: nothing to look up, nothing to write."""

    system = "none"

    def __init__(self, country: str):
        self.country = country

    def find_customers(self, name: str | None, phone: str | None, limit: int = 5) -> list[CustomerCandidate]:
        return []

    def push_order(self, order: CrmOrder) -> str:
        raise CrmPermanentError(f"No CRM is configured for {self.country}")
