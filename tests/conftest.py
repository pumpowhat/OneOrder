"""Suite-wide settings, applied before any test imports the app."""

import os

# Tests drive CRM retries themselves (crm_sync.retry_due); no background worker on the real database.
os.environ.setdefault("CRM_SYNC_WORKER", "0")
# Never call a real Salesforce org from the suite, whatever .env says.
os.environ["CRM_MODE"] = "mock"
