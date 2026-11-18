"""Linking an order to a CRM customer: who decides, and when the link has to go.

A person links the customer by picking a CRM suggestion at review. The link is dropped when the customer on the
order changes into someone else (a different name, or a number that is not the same number), because the CRM
account would then describe the wrong company. Reformatting the same number ("+45 33 12 45 78" to "+4533124578",
as approval does) is not a change of customer.
"""

from fastapi import HTTPException

from backend.crm.matching import phones_match
from backend.db import record_audit_log
from backend.services.matching.matcher import normalize_text


def customer_changed(old_name: str | None, old_phone: str | None, new_name: str | None, new_phone: str | None) -> bool:
    # case, spacing and punctuation do not change the company; the legal form does ("A/S" and "ApS" are two entities)
    if normalize_text(old_name or "") != normalize_text(new_name or ""):
        return True
    if (old_phone or "").strip() == (new_phone or "").strip():
        return False
    return not phones_match(old_phone, new_phone)


def set_crm_link(db, order, account_id: str | None, contact_id: str | None, user: str) -> None:
    """Store the link (or its removal) and audit it. A contact without its account is refused."""
    if contact_id and not account_id:
        raise HTTPException(422, "A CRM contact can only be linked together with its CRM account")
    before = {"crm_account_id": order.crm_account_id, "crm_contact_id": order.crm_contact_id}
    after = {"crm_account_id": account_id or None, "crm_contact_id": contact_id or None}
    if before == after:
        return
    order.crm_account_id, order.crm_contact_id = after["crm_account_id"], after["crm_contact_id"]
    action = "link_crm_account" if after["crm_account_id"] else "unlink_crm_account"
    record_audit_log(db, order.id, action, user, before, after)


def unlink_if_customer_changed(db, order, old_name: str | None, old_phone: str | None, user: str) -> None:
    if order.crm_account_id and customer_changed(old_name, old_phone, order.customer, order.customer_phone):
        set_crm_link(db, order, None, None, user)
