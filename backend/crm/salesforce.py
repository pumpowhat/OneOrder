"""Live Salesforce adapter: REST API with the OAuth 2.0 client credentials flow (server to server, no user login).

Setup in the org (once): an External Client App with the client credentials flow and the ``api`` scope, and a
text field ``OneOrder_Id__c`` on Order marked *External ID* and *Unique*. Pushing an order is an upsert on that
field, so a retry updates the same Order instead of creating a second one. See docs/crm-integration.md.
"""

import os
import re

import httpx

from .base import CrmAccount, CrmContact, CrmOrder, CrmPermanentError, CrmTransientError, CustomerCandidate
from .matching import MIN_PHONE_DIGITS, phone_digits, rank_accounts

DEFAULT_API_VERSION = "62.0"
DEFAULT_EXTERNAL_ID_FIELD = "OneOrder_Id__c"
SEARCH_LIMIT = 20
# characters SOSL treats as operators; escaped so a customer name cannot change the query
_SOSL_RESERVED = re.compile(r"""([?&|!{}\[\]()^~*:\\"'+\-])""")


def sosl_escape(term: str) -> str:
    return _SOSL_RESERVED.sub(r"\\\1", term.strip())


class SalesforceDirectory:
    system = "salesforce"

    def __init__(
        self,
        login_url: str,
        client_id: str,
        client_secret: str,
        country: str = "DK",
        api_version: str = DEFAULT_API_VERSION,
        external_id_field: str = DEFAULT_EXTERNAL_ID_FIELD,
        timeout: float = 10.0,
        http: httpx.Client | None = None,
    ):
        if not (login_url and client_id and client_secret):
            raise CrmPermanentError("Salesforce is not configured: set SF_LOGIN_URL, SF_CLIENT_ID and SF_CLIENT_SECRET")
        self.country = country
        self.login_url = login_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_version = api_version
        self.external_id_field = external_id_field
        self.http = http or httpx.Client(timeout=timeout)
        self._token: str | None = None
        self._instance_url: str | None = None

    @classmethod
    def from_env(cls, country: str = "DK") -> "SalesforceDirectory":
        return cls(
            login_url=os.getenv("SF_LOGIN_URL", ""),
            client_id=os.getenv("SF_CLIENT_ID", ""),
            client_secret=os.getenv("SF_CLIENT_SECRET", ""),
            country=country,
            api_version=os.getenv("SF_API_VERSION", DEFAULT_API_VERSION),
            external_id_field=os.getenv("SF_ORDER_EXTERNAL_ID_FIELD", DEFAULT_EXTERNAL_ID_FIELD),
        )

    # --- auth and transport ------------------------------------------------------------------------

    def _authenticate(self) -> None:
        try:
            res = self.http.post(
                f"{self.login_url}/services/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
        except httpx.HTTPError as exc:
            raise CrmTransientError(f"Salesforce login failed: {exc}") from exc
        if res.status_code >= 500:
            raise CrmTransientError(f"Salesforce login failed with HTTP {res.status_code}")
        if res.status_code != 200:
            raise CrmPermanentError(f"Salesforce login rejected (HTTP {res.status_code}): {_error_text(res)}")
        body = res.json()
        self._token, self._instance_url = body["access_token"], body["instance_url"].rstrip("/")

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Call the REST API, logging in first and once more if the token expired. Maps failures to CrmError."""
        for attempt in (1, 2):
            if not self._token:
                self._authenticate()
            url = f"{self._instance_url}/services/data/v{self.api_version}{path}"
            try:
                res = self.http.request(method, url, headers={"Authorization": f"Bearer {self._token}"}, **kwargs)
            except httpx.HTTPError as exc:
                raise CrmTransientError(f"Salesforce request failed: {exc}") from exc
            if res.status_code == 401 and attempt == 1:
                self._token = None  # expired session: log in again and retry once
                continue
            if res.status_code == 429 or res.status_code >= 500:
                raise CrmTransientError(
                    f"Salesforce is unavailable (HTTP {res.status_code})", retry_after=_retry_after(res)
                )
            if res.status_code >= 400:
                raise CrmPermanentError(f"Salesforce rejected the request (HTTP {res.status_code}): {_error_text(res)}")
            return res
        raise CrmPermanentError("Salesforce rejected the credentials after logging in again")

    # --- CustomerDirectory -------------------------------------------------------------------------

    def find_customers(self, name: str | None, phone: str | None, limit: int = 5) -> list[CustomerCandidate]:
        accounts: dict[str, CrmAccount] = {}
        digits = phone_digits(phone)
        if len(digits) >= MIN_PHONE_DIGITS:
            # search the national part too, so "+45 33 12 45 78" also finds an account stored as "33 12 45 78"
            self._search(f"FIND {{{digits[-8:]}}} IN PHONE FIELDS RETURNING {self._returning(contacts=True)}", accounts)
        if name and len(name.strip()) >= 2:
            self._search(f"FIND {{{sosl_escape(name)}}} IN NAME FIELDS RETURNING {self._returning()}", accounts)
        return rank_accounts(accounts.values(), name, phone, limit)

    def push_order(self, order: CrmOrder) -> str:
        body = {
            "AccountId": order.account_id,
            "EffectiveDate": order.confirmed_on.isoformat(),
            "Status": "Draft",
            "Description": order.description,
        }
        if order.contact_id:
            body["ShipToContactId"] = order.contact_id
        path = f"/sobjects/Order/{self.external_id_field}/{order.order_id}"
        res = self._request("PATCH", path, json=body)
        if res.content:
            record_id = res.json().get("id")
            if record_id:
                return record_id
        # older API versions answer an update with 204 and no body: read the id back
        return self._request("GET", path, params={"fields": "Id"}).json()["Id"]

    # --- helpers -----------------------------------------------------------------------------------

    @staticmethod
    def _returning(contacts: bool = False) -> str:
        account = f"Account(Id, Name, Phone, BillingCity, ShippingCity LIMIT {SEARCH_LIMIT})"
        if not contacts:
            return account
        contact = (
            "Contact(Id, Name, Phone, MobilePhone, Email, AccountId, Account.Name, Account.Phone, "
            f"Account.BillingCity, Account.ShippingCity LIMIT {SEARCH_LIMIT})"
        )
        return f"{account}, {contact}"

    def _search(self, sosl: str, accounts: dict[str, CrmAccount]) -> None:
        records = self._request("GET", "/search/", params={"q": sosl}).json().get("searchRecords", [])
        contacts: dict[str, list[CrmContact]] = {}
        for rec in records:
            kind = rec.get("attributes", {}).get("type")
            if kind == "Account" and rec["Id"] not in accounts:
                accounts[rec["Id"]] = self._account(rec)
            elif kind == "Contact" and rec.get("AccountId"):
                acc = rec.get("Account") or {}
                if rec["AccountId"] not in accounts:
                    accounts[rec["AccountId"]] = self._account({**acc, "Id": rec["AccountId"]})
                for number in (rec.get("Phone"), rec.get("MobilePhone")):
                    if number:
                        contacts.setdefault(rec["AccountId"], []).append(
                            CrmContact(contact_id=rec["Id"], name=rec.get("Name") or "", phone=number, email=rec.get("Email"))
                        )
        for account_id, found in contacts.items():
            current = accounts[account_id]
            accounts[account_id] = CrmAccount(
                account_id=current.account_id,
                name=current.name,
                country=current.country,
                phone=current.phone,
                city=current.city,
                contacts=current.contacts + tuple(found),
            )

    def _account(self, rec: dict) -> CrmAccount:
        return CrmAccount(
            account_id=rec["Id"],
            name=rec.get("Name") or "",
            country=self.country,
            phone=rec.get("Phone"),
            city=rec.get("ShippingCity") or rec.get("BillingCity"),
        )


def _retry_after(res: httpx.Response) -> float | None:
    try:
        return float(res.headers["Retry-After"])
    except (KeyError, ValueError):
        return None


def _error_text(res: httpx.Response) -> str:
    try:
        body = res.json()
    except ValueError:
        return res.text[:200]
    if isinstance(body, list) and body and isinstance(body[0], dict):
        return "; ".join(f"{e.get('errorCode', '')}: {e.get('message', '')}" for e in body)[:300]
    if isinstance(body, dict):
        return str(body.get("error_description") or body.get("error") or body)[:300]
    return str(body)[:300]
