"""A Salesforce stand-in for demos and tests, fed by the same CSV files used to load a real org.

``samples/crm/accounts.csv`` and ``contacts.csv`` use Salesforce's import column names (Data Import Wizard),
so one file seeds both the Developer org and this mock. Ids are generated in Salesforce's shape
(``001`` accounts, ``003`` contacts, ``801`` orders) so the UI sees realistic values.
"""

import csv
from pathlib import Path

from .base import CrmAccount, CrmContact, CrmError, CrmOrder, CustomerCandidate
from .matching import rank_accounts

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MOCK_DIR = REPO_ROOT / "samples" / "crm"


def _sf_id(prefix: str, n: int) -> str:
    return f"{prefix}MK{n:013d}"  # 18 characters, like a Salesforce id


def _clean(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


class MockSalesforceDirectory:
    system = "salesforce"

    def __init__(self, accounts: list[CrmAccount], country: str = "DK"):
        self.country = country
        self.accounts = accounts
        self.orders: dict[str, dict] = {}  # OneOrder order id -> what was written, with its "Id"
        # Errors raised by the next push_order calls, first one first: lets tests and demos show a CRM outage.
        self.failures: list[CrmError] = []

    @classmethod
    def from_csv(cls, directory: str | Path = DEFAULT_MOCK_DIR, country: str = "DK") -> "MockSalesforceDirectory":
        directory = Path(directory)
        accounts_file, contacts_file = directory / "accounts.csv", directory / "contacts.csv"
        if not accounts_file.exists():
            raise FileNotFoundError(f"Mock CRM accounts file not found: {accounts_file}")

        with open(accounts_file, encoding="utf-8", newline="") as f:
            account_rows = [r for r in csv.DictReader(f) if _clean(r.get("Name"))]
        contacts_by_account: dict[str, list[CrmContact]] = {}
        if contacts_file.exists():
            with open(contacts_file, encoding="utf-8", newline="") as f:
                for n, row in enumerate(csv.DictReader(f), start=1):
                    account_name = _clean(row.get("AccountName"))
                    if not account_name:
                        continue
                    full_name = " ".join(p for p in (_clean(row.get("FirstName")), _clean(row.get("LastName"))) if p)
                    contacts_by_account.setdefault(account_name.casefold(), []).append(
                        CrmContact(
                            contact_id=_clean(row.get("Id")) or _sf_id("003", n),
                            name=full_name,
                            phone=_clean(row.get("Phone")),
                            email=_clean(row.get("Email")),
                        )
                    )

        accounts = [
            CrmAccount(
                account_id=_clean(row.get("Id")) or _sf_id("001", n),
                name=row["Name"].strip(),
                country=country,
                phone=_clean(row.get("Phone")),
                city=_clean(row.get("ShippingCity")) or _clean(row.get("BillingCity")),
                contacts=tuple(contacts_by_account.get(row["Name"].strip().casefold(), [])),
            )
            for n, row in enumerate(account_rows, start=1)
        ]
        return cls(accounts, country=country)

    def find_customers(self, name: str | None, phone: str | None, limit: int = 5) -> list[CustomerCandidate]:
        return rank_accounts(self.accounts, name, phone, limit)

    def push_order(self, order: CrmOrder) -> str:
        if self.failures:
            raise self.failures.pop(0)
        existing = self.orders.get(order.order_id)
        record_id = existing["Id"] if existing else _sf_id("801", len(self.orders) + 1)
        self.orders[order.order_id] = {
            "Id": record_id,
            "AccountId": order.account_id,
            "ShipToContactId": order.contact_id,
            "EffectiveDate": order.confirmed_on.isoformat(),
            "Status": "Draft",
            "Description": order.description,
        }
        return record_id
