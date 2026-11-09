import re
import unicodedata
from rapidfuzz import fuzz

from backend.services.intake.ai import AIClient
from backend.services.intake.schemas import (
    MATCH_AUTO_THRESHOLD,
    MATCH_MIN_THRESHOLD,
    DraftLine,
    DraftOrder,
    MatchCandidate,
)
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


# Parse before normalize_text, which removes decimal points and dimension separators.
_NUMBER = r"\d+(?:[.,]\d+)?"
_MEASURE = re.compile(
    rf"(?<![\w.,])({_NUMBER}(?:\s*[x×]\s*{_NUMBER})*)\s*(mm|cm|m|kg|g|ml|l)\b",
    re.IGNORECASE,
)
_DIMENSION = re.compile(
    rf"(?<![\w.,])({_NUMBER}(?:\s*[x×]\s*{_NUMBER})+)\s*(mm|cm|m)?\b",
    re.IGNORECASE,
)
_UNIT_SCALE = {
    "mm": ("length", 1), "cm": ("length", 10), "m": ("length", 1000),
    "g": ("mass", 1), "kg": ("mass", 1000),
    "ml": ("volume", 1), "l": ("volume", 1000),
}


def specifications(text: str, *, catalog_dimensions: bool = False) -> dict[str, set[float]]:
    """Extract explicit measurements in base units, including 45x145mm."""
    result: dict[str, set[float]] = {}
    for match in _MEASURE.finditer(text.replace("Ø", " ").replace("ø", " ")):
        kind, scale = _UNIT_SCALE[match[2].lower()]
        values = result.setdefault(kind, set())
        for number in re.split(r"\s*[x×]\s*", match[1]):
            values.add(round(float(number.replace(",", ".")) * scale, 6))
    if catalog_dimensions:
        # Catalogue names use millimetres for unlabelled board dimensions such as
        # 1200x3000. This does not supply missing dimensions in a customer request.
        for match in _DIMENSION.finditer(text):
            if match[2] is None:
                result.setdefault("length", set()).update(
                    round(float(number.replace(",", ".")), 6)
                    for number in re.split(r"\s*[x×]\s*", match[1])
                )
    return result


def dimension_groups(text: str, *, catalog_dimensions: bool = False) -> set[tuple[float, ...]]:
    """Keep dimensions together: 45x145 must not match 45x95 plus 145x200."""
    groups = set()
    for match in _DIMENSION.finditer(text):
        if match[2] is None and not catalog_dimensions:
            continue
        scale = _UNIT_SCALE[(match[2] or "mm").lower()][1]
        groups.add(tuple(round(float(n.replace(",", ".")) * scale, 6)
                         for n in re.split(r"\s*[x×]\s*", match[1])))
    return groups


def standalone_lengths(text: str) -> set[float]:
    return {
        round(float(match[1].replace(",", ".")) * _UNIT_SCALE[match[2].lower()][1], 6)
        for match in _MEASURE.finditer(text.replace("Ø", " ").replace("ø", " "))
        if _UNIT_SCALE[match[2].lower()][0] == "length"
        and not re.search(r"[x×]", match[1])
    }


def uncertain_measurement_roles(text: str, item: CatalogItem) -> bool:
    # A scalar matching only part of a dimension group is not proof of the same
    # role (e.g. requested thickness versus catalogue width). Keep it for review.
    requested = standalone_lengths(text)
    available = standalone_lengths(item.name)
    if not specifications(item.name).get("length"):
        available.update(value for alias in item.aliases for value in standalone_lengths(alias))
    return bool(available) and not requested <= available


def compatible_specifications(requested: dict[str, set[float]], item: CatalogItem, text: str = "") -> bool:
    # The product name is authoritative; aliases may omit specifications or round them.
    available = specifications(item.name, catalog_dimensions=True)
    for alias in item.aliases:
        for kind, values in specifications(alias).items():
            if kind not in available:
                available[kind] = values
    if not all(values <= available.get(kind, set()) for kind, values in requested.items()):
        return False
    if not dimension_groups(text) <= dimension_groups(item.name, catalog_dimensions=True):
        return False
    # Preserve explicit C codes (e.g. timber C24 or steel profile C70).
    requested_grades = set(re.findall(r"\bC\d{2}\b", text.upper()))
    product_grades = set(re.findall(r"\bC\d{2}\b", item.name.upper()))
    if not product_grades:
        product_grades = {grade for alias in item.aliases
                          for grade in re.findall(r"\bC\d{2}\b", alias.upper())}
    return requested_grades <= product_grades


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

        requested = specifications(text)
        q_tokens = set(q_norm.split())
        scored = []

        for item in self.catalog:
            if not compatible_specifications(requested, item, text):
                continue
            targets = [item.name] + list(item.aliases)
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
                # Boost subset only when query contains enough specific tokens (>= 2)
                # to prevent single generic words like 'gipsplade' from falsely claiming 0.95
                if is_subset and len(q_tokens) >= 2:
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

        - Score >= 0.90 AND clear winner (gap between top-1 and top-2 >= 0.05, or exact 1.0):
          Automatically select top SKU.
        - Score in [0.60, 0.90) OR ambiguous close match (gap < 0.05):
          Invoke AIClient to disambiguate among top-3.
          Suggested SKU is assigned, but line continues to require human confirmation.
        - Score < 0.60:
          Leave SKU empty, requiring human assignment.
        """
        candidates = self.score_candidates(line.description, top_k=3)
        line.candidates = candidates
        top_score = candidates[0].score if candidates else 0.0
        line.match_score = top_score

        # Detect ambiguous ties or near-ties between top candidates
        is_ambiguous = False
        if len(candidates) >= 2 and top_score < 1.0:
            gap = top_score - candidates[1].score
            if gap < 0.05:
                is_ambiguous = True

        if candidates:
            item = next(item for item in self.catalog if item.sku == candidates[0].sku)
            is_ambiguous = is_ambiguous or uncertain_measurement_roles(line.description, item)
        line.ambiguous = is_ambiguous

        if top_score >= MATCH_AUTO_THRESHOLD and not is_ambiguous:
            line.matched_sku = candidates[0].sku
        elif top_score >= MATCH_MIN_THRESHOLD:
            chosen = None
            if self.ai and hasattr(self.ai, "match_product"):
                cand_dicts = [{"sku": c.sku, "name": c.name, "score": c.score} for c in candidates]
                try:
                    chosen = self.ai.match_product(line.description, cand_dicts)
                except Exception:
                    chosen = None
            # Fallback to top candidate if AI unavailable or returns None
            valid_skus = {candidate.sku for candidate in candidates}
            line.matched_sku = chosen if chosen in valid_skus else candidates[0].sku
        else:
            line.matched_sku = None

        return line

    def match_order(self, order: DraftOrder) -> DraftOrder:
        """Match all lines of a draft order."""
        for line in order.lines:
            self.match_line(line)
        return order
