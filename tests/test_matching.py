import pytest

from backend.services.intake.schemas import DraftLine, DraftOrder, SourceType
from backend.services.matching import (
    CatalogueMatcher,
    clear_catalog_cache,
    load_catalog,
    normalize_text,
)


@pytest.fixture
def catalog():
    clear_catalog_cache()
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
    assert len(matched.candidates) == 1
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


def test_medium_score_calls_ai_and_flags_review(catalog):
    calls = []

    class MockAI:
        def match_product(self, description, candidates):
            calls.append((description, candidates))
            # AI explicitly picks candidate #2 instead of top candidate #1
            return candidates[1]["sku"]

    matcher = CatalogueMatcher(catalog, ai=MockAI())
    # "Gips brand" scores ~0.855, which is strictly within [0.60, 0.90)
    line = DraftLine(description="Gips brand", quantity=4, confidence=0.95)
    matched = matcher.match_line(line)

    assert 0.60 <= matched.match_score < 0.90
    assert len(calls) == 1
    assert calls[0][0] == "Gips brand"
    assert matched.matched_sku == matched.candidates[1].sku
    # Must require human confirmation because score is in [0.60, 0.90)
    assert matched.needs_review is True


def test_ambiguous_short_query_does_not_blindly_autoselect(catalog):
    matcher = CatalogueMatcher(catalog)
    # Generic short query matching multiple products
    line = DraftLine(description="gipsplade", quantity=10, confidence=0.95)
    matched = matcher.match_line(line)

    # Flagged as ambiguous and real score preserved without being faked
    assert matched.ambiguous is True
    # Should not be treated as a definitive >0.90 match without human review
    assert matched.needs_review is True


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


@pytest.mark.parametrize("query", ["stone wool insulation 100mm", "stone wool insulation 10 cm", "stone wool insulation 0.1m"])
def test_conflicting_thickness_cannot_win_even_with_exact_alias(query):
    from backend.services.matching.catalog import CatalogItem

    wrong = CatalogItem("wrong", "Stone wool insulation 150mm", aliases=(query,))
    line = CatalogueMatcher([wrong]).match_line(DraftLine(description=query, quantity=1, confidence=0.99))
    assert line.matched_sku is None
    assert line.needs_review
    assert line.candidates == []


def test_ai_cannot_return_excluded_sku():
    from backend.services.matching.catalog import CatalogItem

    class AI:
        def match_product(self, description, candidates):
            return "wrong"

    catalog = [CatalogItem("wrong", "Stone wool insulation 150mm"),
               CatalogItem("compatible", "Wool insulation 100mm")]
    line = CatalogueMatcher(catalog, ai=AI()).match_line(
        DraftLine(description="stone wool insulation 100mm", quantity=1, confidence=0.99))
    assert line.matched_sku != "wrong"


def test_missing_board_length_requires_review():
    line = CatalogueMatcher(load_catalog()).match_line(
        DraftLine(description="gipspalde 13mm", quantity=1, confidence=0.99))
    assert line.needs_review


@pytest.mark.parametrize("query,name,compatible", [
    ("insulation 10 cm", "Insulation 100mm", True),
    ("board 12,5mm", "Board 12.5mm", True),
    ("board 12.5mm", "Board 125mm", False),
    ("pipe Ø110mm", "Pipe Ø160mm", False),
    ("timber 45×145mm", "Timber 45x95mm", False),
])
def test_numeric_unit_compatibility(query, name, compatible):
    from backend.services.matching.catalog import CatalogItem
    from backend.services.matching.matcher import compatible_specifications, specifications

    assert compatible_specifications(specifications(query), CatalogItem("test", name)) is compatible


@pytest.mark.parametrize("query", ["gipsplade 3m", "gipsskiva 3000mm", "drywall board 3000mm"])
def test_catalogue_board_dimensions_preserve_compatible_length_alias(query):
    line = CatalogueMatcher(load_catalog()).match_line(
        DraftLine(description=query, quantity=1, confidence=0.99))
    assert line.matched_sku == "GYP-13-3000"
    assert line.match_score == 1.0
    # Catalogue names do not label the role of the scalar versus board dimensions.
    assert line.needs_review
    assert all(c.sku != "GYP-13-2400" for c in line.candidates)


def test_rounded_catalogue_alias_cannot_override_explicit_thickness():
    from backend.services.matching.catalog import CatalogItem

    item = CatalogItem("wind", "Vindgips 9.5mm 1200x2700", aliases=("vindgips 9mm",))
    line = CatalogueMatcher([item]).match_line(
        DraftLine(description="vindgips 9mm", quantity=1, confidence=0.99))
    assert line.matched_sku is None
    assert line.needs_review


def test_specification_filter_resolves_explicit_timber_length():
    line = CatalogueMatcher(load_catalog()).match_line(
        DraftLine(description="Konstruktionstræ C24 45x145mm 4.2m", quantity=1, confidence=0.99))
    assert line.matched_sku == "TIM-SPRU-45145-42"
    assert not line.needs_review


@pytest.mark.parametrize("query,name", [
    ("timber C24 45x145mm 4.2m", "Timber C18 45x145mm 4.2m"),
    ("timber 45x145mm", "Timber 45x95mm 145x200mm"),
    ("board 100x100mm", "Board 100x150mm"),
])
def test_grade_or_grouped_dimensions_cannot_be_substituted(query, name):
    from backend.services.matching.catalog import CatalogItem

    line = CatalogueMatcher([CatalogItem("wrong", name)]).match_line(
        DraftLine(description=query, quantity=1, confidence=0.99))
    assert line.matched_sku is None
    assert line.needs_review


def test_scalar_cannot_silently_match_width_instead_of_thickness():
    from backend.services.matching.catalog import CatalogItem

    item = CatalogItem("wrong", "Insulation 150mm 100x1000mm", aliases=("insulation 100mm",))
    line = CatalogueMatcher([item]).match_line(
        DraftLine(description="insulation 100mm", quantity=1, confidence=0.99))
    assert line.match_score == 1.0
    assert line.needs_review
    assert line.ambiguous


@pytest.mark.parametrize("query,expected_review", [
    ("Konstruktionstræ C24 45x145mm 4.2m", False),
    ("Konstruktionstræ C24 45x145mm", True),
])
def test_timber_length_information_controls_review(query, expected_review):
    line = CatalogueMatcher(load_catalog()).match_line(
        DraftLine(description=query, quantity=1, confidence=0.99))
    assert line.needs_review is expected_review


@pytest.mark.parametrize("requested,offered", [("9", "9.5"), ("9.5", "9")])
def test_no_rounded_thickness_substitution(requested, offered):
    from backend.services.matching.catalog import CatalogItem

    line = CatalogueMatcher([CatalogItem("wrong", f"Wind board {offered}mm")]).match_line(
        DraftLine(description=f"Wind board {requested}mm", quantity=1, confidence=0.99))
    assert line.matched_sku is None
    assert line.needs_review


def test_c_code_in_profile_alias_remains_usable():
    line = CatalogueMatcher(load_catalog()).match_line(
        DraftLine(description="stender c70", quantity=1, confidence=0.99))
    assert line.matched_sku == "GYP-PROF-C70"
    assert not line.needs_review
