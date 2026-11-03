from datetime import date
from enum import Enum

from pydantic import BaseModel, Field

# Review thresholds
REVIEW_THRESHOLD = 0.85
MATCH_AUTO_THRESHOLD = 0.90
MATCH_MIN_THRESHOLD = 0.60


def line_needs_review(
    confidence: float,
    match_score: float | None = None,
    matched_sku: str | None = None,
    confirmed: bool = False,
    ambiguous: bool = False,
) -> bool:
    """Determine whether a line item requires human review before approval.

    A line requires human review if:
    1. It has NOT been explicitly confirmed by a user, AND
    2. It was marked ambiguous (e.g. multiple candidates with nearly identical scores), OR
    3. Extraction confidence is below REVIEW_THRESHOLD (0.85), OR
    4. Catalogue match score is below MATCH_AUTO_THRESHOLD (0.90) (meaning it was either
       matched by AI/heuristics in [0.60, 0.90), or failed), OR
    5. It has no matched SKU.

    If matching has not yet run (match_score is None), review is determined solely by confidence.
    """
    if confirmed:
        return False
    if ambiguous:
        return True
    if confidence < REVIEW_THRESHOLD:
        return True
    if match_score is not None:
        if match_score < MATCH_AUTO_THRESHOLD or not matched_sku:
            return True
    return False


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
    ambiguous: bool = False

    @property
    def needs_review(self) -> bool:
        return line_needs_review(
            confidence=self.confidence,
            match_score=self.match_score,
            matched_sku=self.matched_sku,
            confirmed=self.confirmed,
            ambiguous=self.ambiguous,
        )


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
