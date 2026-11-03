import re
import unicodedata
from rapidfuzz import fuzz

from backend.services.intake.ai import AIClient
from backend.services.intake.schemas import DraftLine, DraftOrder, MatchCandidate
from .catalog import CatalogItem


def normalize_text(text: str) -> str:
    """Normalize text for cross-Nordic matching: lowercase, accents, units, punctuation."""
    if not text:
        return ""
    text = text.lower()
    # Normalize Nordic vowel variations
    text = text.translate(str.maketrans({"æ": "ae", "ø": "oe", "å": "aa", "ä": "ae", "ö": "oe"}))
    # Strip remaining diacritics
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    # Separate dimension numbers and common units (e.g., 13mm -> 13 mm, 45x145 -> 45 145)
    text = re.sub(r"(\d+)(mm|cm|m|kg|pk|stk)", r"\1 \2", text)
    text = re.sub(r"(\d+)x(\d+)", r"\1 \2", text)
    # Remove punctuation
    text = re.sub(r"[^\w\s]", " ", text)
    return " ".join(text.split())


class CatalogueMatcher:
    """Fuzzy-matches order lines against a product catalogue using RapidFuzz and AI."""

    def __init__(self, catalog: list[CatalogItem], ai: AIClient | None = None):
        self.catalog = catalog
        self.ai = ai

    def score_candidates(self, text: str, top_k: int = 3) -> list[MatchCandidate]:
        """Rank catalogue items by similarity to the given text, returning top-k."""
        q_norm = normalize_text(text)
        if not q_norm:
            return []

        q_tokens = set(q_norm.split())
        scored = []

        for item in self.catalog:
            targets = [item.name] + item.aliases
            best = 0.0

            for target in targets:
                t_norm = normalize_text(target)
                if not t_norm:
                    continue
                if q_norm == t_norm:
                    best = 1.0
                    break

                t_tokens = set(t_norm.split())
                is_subset = bool(q_tokens and q_tokens.issubset(t_tokens))

                w_ratio = fuzz.WRatio(q_norm, t_norm) / 100.0
                token_sort = fuzz.token_sort_ratio(q_norm, t_norm) / 100.0
                token_set = fuzz.token_set_ratio(q_norm, t_norm) / 100.0

                s = max(w_ratio, token_sort)
                if is_subset:
                    s = max(s, 0.95)
                elif token_set >= 0.95 and len(q_tokens) >= 2:
                    s = max(s, 0.90)

                best = max(best, s)

            scored.append(
                MatchCandidate(
                    sku=item.sku,
                    name=item.name,
                    score=round(best, 4),
                    unit=item.unit,
                )
            )

        scored.sort(key=lambda c: c.score, reverse=True)
        return scored[:top_k]

    def match_line(self, line: DraftLine) -> DraftLine:
        """Find catalogue matches and assign SKU based on threshold rules:

        - Score >= 0.90: automatically select top SKU.
        - Score in [0.60, 0.90): invoke AIClient to disambiguate among top-3.
        - Score < 0.60: leave SKU empty, requiring human review.
        """
        candidates = self.score_candidates(line.description, top_k=3)
        line.candidates = candidates
        top_score = candidates[0].score if candidates else 0.0
        line.match_score = top_score

        if top_score >= 0.90:
            line.matched_sku = candidates[0].sku
        elif top_score >= 0.60:
            chosen = None
            if self.ai and hasattr(self.ai, "match_product"):
                cand_dicts = [{"sku": c.sku, "name": c.name, "score": c.score} for c in candidates]
                try:
                    chosen = self.ai.match_product(line.description, cand_dicts)
                except Exception:
                    chosen = None
            # Fallback to top candidate if AI unavailable or returns None
            line.matched_sku = chosen or (candidates[0].sku if candidates else None)
        else:
            line.matched_sku = None

        return line

    def match_order(self, order: DraftOrder) -> DraftOrder:
        """Match all lines of a draft order."""
        for line in order.lines:
            self.match_line(line)
        return order
