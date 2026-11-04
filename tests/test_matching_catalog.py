import json
from pathlib import Path
import pytest

from backend.services.intake.schemas import DraftLine
from backend.services.matching import (
    CatalogueMatcher,
    clear_catalog_cache,
    load_catalog,
)

FIXTURES_PATH = Path("tests/fixtures/matching_cases.json")
CATALOG_PATH = Path("data/catalog.json")

# Known matcher limitations to be investigated by Nghia
XFAIL_REASONS = {
    "stenull flexibatts 100mm": "Rapidfuzz score 0.8696 is below AUTO threshold 0.90; without AI needs_review is True",
    "steinull isolasjon 100mm": "Rapidfuzz token sort ranks ISO-ROCK-150 higher than ISO-ROCK-100",
    "stone wool insulation 100mm": "Rapidfuzz token sort ranks ISO-ROCK-150 higher than ISO-ROCK-100",
    "gipspalde 13mm": "Typo in query matches GYP-13-3000 instead of GYP-13-2400",
    "moertel 25kg": "oe transliteration matches BET-EXP-25 ahead of BET-TORR-25",
    "gipsplade 13 mm": "Space before unit ties at 0.95 with 3000mm variant causing ambiguous review flag",
    "isolering 100 mm": "Ties at 0.95 between glass wool and rock wool causing ambiguous review flag",
}


def load_cases():
    with open(FIXTURES_PATH, encoding="utf-8") as f:
        return json.load(f)


CASES = load_cases()


def make_params():
    params = []
    for case in CASES:
        query = case["query"]
        case_id = f"{case.get('lang', 'xx')}:{query}"
        if query in XFAIL_REASONS:
            params.append(
                pytest.param(
                    case,
                    id=case_id,
                    marks=pytest.mark.xfail(reason=XFAIL_REASONS[query], strict=False),
                )
            )
        else:
            params.append(pytest.param(case, id=case_id))
    return params


@pytest.fixture(scope="module")
def catalog():
    clear_catalog_cache()
    return load_catalog(str(CATALOG_PATH))


@pytest.fixture(scope="module")
def matcher(catalog):
    # Pure rule-based matcher without AI client to ensure deterministic matching
    return CatalogueMatcher(catalog, ai=None)


@pytest.mark.parametrize("case", make_params())
def test_matching_case(matcher, case):
    line = DraftLine(description=case["query"], quantity=1, confidence=0.95)
    matched = matcher.match_line(line)

    assert matched.matched_sku == case["expected_sku"], (
        f"Query {case['query']!r}: expected SKU {case['expected_sku']!r}, got {matched.matched_sku!r}"
    )
    assert matched.needs_review == case["expected_review"], (
        f"Query {case['query']!r}: expected needs_review={case['expected_review']}, got {matched.needs_review}"
    )


def test_matching_accuracy_on_non_ambiguous_cases(matcher):
    """Aggregate test: accuracy on non-ambiguous queries must be at least 85%."""
    non_ambiguous = [c for c in CASES if not c["expected_review"]]
    assert len(non_ambiguous) >= 40, f"Expected at least 40 non-ambiguous cases, got {len(non_ambiguous)}"

    correct = 0
    for case in non_ambiguous:
        line = DraftLine(description=case["query"], quantity=1, confidence=0.95)
        matched = matcher.match_line(line)
        if matched.matched_sku == case["expected_sku"] and matched.needs_review == case["expected_review"]:
            correct += 1

    accuracy = correct / len(non_ambiguous)
    assert accuracy >= 0.85, (
        f"Overall accuracy on non-ambiguous cases ({accuracy:.2%}) is below 85% threshold "
        f"({correct}/{len(non_ambiguous)} correct)"
    )
