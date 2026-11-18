"""Validated input for manual creation and draft editing."""
from datetime import date
import math
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator


class DraftLineInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    line_index: int | None = Field(default=None, ge=0)
    sku: str | None = Field(default=None, max_length=100)
    description: str = Field(min_length=1, max_length=255)
    quantity: float = Field(gt=0, allow_inf_nan=False)
    confirmed: bool = False


    @field_validator("quantity", mode="before")
    @classmethod
    def reject_nonfinite_json(cls, value):
        # FastAPI cannot encode an infinity echoed in its standard validation errors.
        if isinstance(value, float) and not math.isfinite(value):
            raise HTTPException(422, "Line quantity must be finite and greater than 0")
        return value


CRM_ID_PATTERN = r"^[A-Za-z0-9]{15}(?:[A-Za-z0-9]{3})?$"  # a Salesforce record id, 15 or 18 characters


class DraftOrderInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    user: str = Field(default="sales_desk", min_length=1, max_length=100)
    customer: str | None = Field(default=None, max_length=255)
    customer_phone: str | None = Field(default=None, max_length=64)
    # Set from a picked CRM suggestion; null unlinks. Left out: the link stays, unless the customer itself changes.
    crm_account_id: str | None = Field(default=None, pattern=CRM_ID_PATTERN)
    crm_contact_id: str | None = Field(default=None, pattern=CRM_ID_PATTERN)
    delivery_site: str | None = Field(default=None, max_length=255)
    requested_date: date | None = None
    lines: list[DraftLineInput] | None = Field(default=None, max_length=500)
