from datetime import date
from enum import Enum

from pydantic import BaseModel, Field

# Lines below this confidence must be reviewed by a person before approval.
REVIEW_THRESHOLD = 0.85


class SourceType(str, Enum):
    IMAGE = "image"
    EMAIL = "email"
    EXCEL = "excel"


class DraftLine(BaseModel):
    description: str
    quantity: float
    unit: str | None = None
    confidence: float = Field(ge=0, le=1)
    source_text: str | None = None

    @property
    def needs_review(self) -> bool:
        return self.confidence < REVIEW_THRESHOLD


class DraftOrder(BaseModel):
    source_type: SourceType
    source_name: str | None = None
    customer: str | None = None
    delivery_site: str | None = None
    requested_date: date | None = None
    lines: list[DraftLine] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    @property
    def needs_review(self) -> bool:
        return any(line.needs_review for line in self.lines)
