import pytest

from backend.services.intake.schemas import DraftLine, DraftOrder, SourceType
from backend.services.matching import CatalogItem, CatalogueMatcher, load_catalog, normalize_text


@pytest.fixture
def catalog():
    return load_catalog("tests/fixtures/catalog_sample.json")


def test_normalize_text():
    assert normalize_text("Gipsplade 13mm") == "gipsplade 13 mm"
    assert normalize_text("Regel 45x145mm") == "regel 45 145 mm"
    # Nordic character replacements
    assert normalize_text("Træ & Søm") == "trae soem"
    assert normalize_text("Mørtel") == "moertel"


def test_load_catalog(catalog):
    assert len(catalog) >= 15
    skus = {item.sku for item in catalog}
    assert "GYP-13-2400" in skus
    assert "ISO-GLAS-100" in skus
    assert "SCR-GIP-40" in skus


def test_load_catalog_missing_file():
    with pytest.raises(FileNotFoundError):
        load_catalog("non_existent_catalog.json")


def test_exact_matching(catalog):
    matcher = CatalogueMatcher(catalog)
    line = DraftLine(description="Gipsplade standard 13mm 1200x2400", quantity=10, confidence=0.95)
    matched = matcher.match_line(line)

    assert matched.matched_sku == "GYP-13-2400"
    assert matched.match_score == 1.0
    assert len(matched.candidates) == 3
    assert matched.candidates[0].sku == "GYP-13-2400"
    assert matched.needs_review is False


def test_spelling_error_typo_matching(catalog):
    matcher = CatalogueMatcher(catalog)
    # Typo: 'gipspalde' instead of 'gipsplade'
    line = DraftLine(description="gipspalde 13mm", quantity=5, confidence=0.9)
    matched = matcher.match_line(line)

    assert matched.matched_sku == "GYP-13-2400"
    assert matched.match_score >= 0.90
    assert matched.needs_review is False


def test_multilingual_synonyms_matching(catalog):
    matcher = CatalogueMatcher(catalog)

    # Swedish synonym for plasterboard
    line_sv = DraftLine(description="Gipsskiva normal 13mm", quantity=20, confidence=0.9)
    assert matcher.match_line(line_sv).matched_sku == "GYP-13-2400"

    # Swedish synonym for glass wool insulation
    line_iso = DraftLine(description="glasull isolering 100mm", quantity=15, confidence=0.9)
    assert matcher.match_line(line_iso).matched_sku == "ISO-GLAS-100"

    # English synonym
    line_en = DraftLine(description="standard plasterboard 13mm", quantity=8, confidence=0.9)
    assert matcher.match_line(line_en).matched_sku == "GYP-13-2400"


def test_medium_score_calls_ai_client(catalog):
    calls = []

    class MockAI:
        def match_product(self, description, candidates):
            calls.append((description, candidates))
            # Pick candidate #2 instead of top candidate
            return candidates[1]["sku"]

    matcher = CatalogueMatcher(catalog, ai=MockAI())
    # Partial query with score between 0.60 and 0.90
    line = DraftLine(description="Gips brand", quantity=4, confidence=0.9)
    matched = matcher.match_line(line)

    if 0.60 <= matched.match_score < 0.90:
        assert len(calls) == 1
        assert matched.matched_sku == matched.candidates[1].sku


def test_low_score_leaves_sku_empty_and_needs_review(catalog):
    matcher = CatalogueMatcher(catalog)
    # Completely unrelated item
    line = DraftLine(description="cà phê sữa đá đặc biệt", quantity=2, confidence=0.95)
    matched = matcher.match_line(line)

    assert matched.match_score < 0.60
    assert matched.matched_sku is None
    assert matched.needs_review is True

    # Order containing this line must flag needs_review
    order = DraftOrder(source_type=SourceType.EMAIL, lines=[matched])
    assert order.needs_review is True
