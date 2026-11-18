"""CRM adapters: customer lookup at review and order sync at confirm, one adapter per country's CRM."""

from .base import (
    CrmAccount,
    CrmContact,
    CrmError,
    CrmOrder,
    CrmPermanentError,
    CrmTransientError,
    CustomerCandidate,
    CustomerDirectory,
    NoCrmDirectory,
)
from .matching import phones_match, rank_accounts
from .mock import MockSalesforceDirectory
from .registry import CrmRegistry, clear_crm_cache, crm_mode, get_crm_registry
from .salesforce import SalesforceDirectory

__all__ = [
    "CrmAccount",
    "CrmContact",
    "CrmError",
    "CrmOrder",
    "CrmPermanentError",
    "CrmRegistry",
    "CrmTransientError",
    "CustomerCandidate",
    "CustomerDirectory",
    "MockSalesforceDirectory",
    "NoCrmDirectory",
    "SalesforceDirectory",
    "clear_crm_cache",
    "crm_mode",
    "get_crm_registry",
    "phones_match",
    "rank_accounts",
]
