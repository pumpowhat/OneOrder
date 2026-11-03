from datetime import date
from enum import Enum

from pydantic import BaseModel, Field

# Lines below this confidence must be reviewed by a person before approval.
REVIEW_THRESHOLD = 0.85


class SourceType(str, Enum):
    IMAGE = "image"
    EMAIL = "email"
    EXCEL = "excel"


class MatchCandidate(BaseModel):
    sku: str
    name: str
    score: float
    unit: str | None = None


class DraftLine(BaseModel):
    description: str
    quantity: float
    unit: str | None = None
    confidence: float = Field(ge=0, le=1)
    source_text: str | None = None
    matched_sku: str | None = None
    match_score: float | None = None
    candidates: list[MatchCandidate] = Field(default_factory=list)
    confirmed: bool = False

    @property
    def needs_review(self) -> bool:
        if self.confirmed:
            return False
        if self.confidence < REVIEW_THRESHOLD:
            return True
        if self.match_score is not None:
            if self.match_score < 0.60 or self.matched_sku is None:
                return True
        return False


class DraftOrder(BaseModel):
    id: str | None = None
    status: str = "draft"
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
