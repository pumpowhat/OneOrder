"""Rank CRM accounts against the customer name and phone read from an order.

Shared by every CRM adapter: the CRM only narrows the search, the score is always computed here, so the
mock and Salesforce suggest the same customers for the same data.
"""

from collections.abc import Iterable
import re

from rapidfuzz import fuzz

from backend.services.matching.matcher import normalize_text

from .base import CrmAccount, CustomerCandidate

NAME_MIN_RATIO = 75  # token_sort_ratio below this is not shown as a suggestion
NAME_ONLY_MAX = 0.85  # an exact name without a phone match still ranks below every phone match (>= 0.9)
MIN_PHONE_DIGITS = 7
# legal forms that say nothing about which company it is: "Hoffmann Byg A/S" and "Hoffmann Byg ApS" compare by "hoffmann byg"
_LEGAL_SUFFIX = re.compile(r"(?:\s+(?:a s|i s|k s|aps|ab|asa|as|oy|gmbh|ltd))+$")


def phone_digits(value: str | None) -> str:
    """Digits only, without the international 00 prefix: "+45 33 12 45 78" and "0045-33124578" both give "4533124578"."""
    digits = re.sub(r"\D", "", value or "")
    return digits[2:] if (value or "").strip().startswith("00") else digits


def phones_match(a: str | None, b: str | None) -> bool:
    """Same number, allowing one side to omit the country code ("33 12 45 78" matches "+45 33 12 45 78")."""
    da, db = phone_digits(a), phone_digits(b)
    if len(da) < MIN_PHONE_DIGITS or len(db) < MIN_PHONE_DIGITS:
        return False
    if da == db:
        return True
    short, long_ = sorted((da, db), key=len)
    return long_.endswith(short) and 1 <= len(long_) - len(short) <= 3


def normalize_company(name: str | None) -> str:
    return _LEGAL_SUFFIX.sub("", normalize_text(name or "")).strip()


def name_ratio(a: str | None, b: str | None) -> float:
    na, nb = normalize_company(a), normalize_company(b)
    if not na or not nb:
        return 0.0
    return fuzz.token_sort_ratio(na, nb)


def rank_accounts(
    accounts: Iterable[CrmAccount], name: str | None, phone: str | None, limit: int = 5
) -> list[CustomerCandidate]:
    """Accounts whose phone (or a contact's phone) matches, or whose name is close, best first.

    A phone match ranks above any name-only match (score 0.9 to 1.0, higher when the name also agrees);
    a name-only match scores at most NAME_ONLY_MAX. One candidate per account."""
    name = (name or "").strip() or None
    phone = (phone or "").strip() or None
    best: dict[str, CustomerCandidate] = {}
    for account in accounts:
        ratio = name_ratio(name, account.name) if name else 0.0
        candidate: CustomerCandidate | None = None
        if phone:
            if phones_match(phone, account.phone):
                candidate = _candidate(account, None, account.phone, ratio, name, "phone")
            else:
                contact = next((c for c in account.contacts if phones_match(phone, c.phone)), None)
                if contact:
                    candidate = _candidate(account, contact.contact_id, contact.phone, ratio, name, "phone")
        if candidate is None and name and ratio >= NAME_MIN_RATIO:
            candidate = CustomerCandidate(
                crm_account_id=account.account_id,
                crm_contact_id=None,
                name=account.name,
                phone=account.phone,
                city=account.city,
                country=account.country,
                score=round(ratio / 100 * NAME_ONLY_MAX, 3),
                matched_on="name",
            )
        if candidate and (account.account_id not in best or candidate.score > best[account.account_id].score):
            best[account.account_id] = candidate
    return sorted(best.values(), key=lambda c: (-c.score, c.name))[:limit]


def _candidate(
    account: CrmAccount, contact_id: str | None, phone: str | None, ratio: float, name: str | None, matched_on: str
) -> CustomerCandidate:
    name_part = ratio / 100 if name else 1.0
    return CustomerCandidate(
        crm_account_id=account.account_id,
        crm_contact_id=contact_id,
        name=account.name,
        phone=phone,
        city=account.city,
        country=account.country,
        score=round(0.9 + 0.1 * name_part, 3),
        matched_on=matched_on,
    )
