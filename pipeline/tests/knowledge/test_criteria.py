"""Validation tests for digitized clinical criteria (STOPP/START and ACB).

Tests verify that YAML files in pipeline/knowledge/criteria/ are well-formed,
conform to expected schemas, contain valid risk dimensions and personas,
and have complete citation metadata.
"""

from pathlib import Path

import yaml

CRITERIA_DIR = Path(__file__).resolve().parents[2] / "knowledge" / "criteria"
STOPP_START_PATH = CRITERIA_DIR / "stopp_start.yaml"
ACB_PATH = CRITERIA_DIR / "acb.yaml"

VALID_DIMENSIONS = {
    "liver",
    "gi_bleeding",
    "cardiovascular_bp",
    "kidney",
    "anticholinergic_cognitive",
    "sedation_falls",
    "serotonergic_interactions",
    "anticoagulant_bleeding",
    "pediatric",
    "rebound_overuse",
    "pregnancy_lactation",
    "duplicate_dosing",
    "excipients",
    "local_skin",
    "efficacy_evidence",
}

VALID_PERSONAS = {
    "adult_18_64",
    "adult_65_plus",
    "teen_12_17",
    "child_6_11",
    "child_2_5",
    "under_2",
    "pregnant",
    "breastfeeding",
}

VALID_RECOMMENDATIONS = {"avoid", "caution", "consider"}


def test_stopp_start_file_exists() -> None:
    """Verify that stopp_start.yaml exists and is non-empty."""
    assert STOPP_START_PATH.is_file(), f"Missing file: {STOPP_START_PATH}"
    assert STOPP_START_PATH.stat().st_size > 0, "stopp_start.yaml is empty"


def test_stopp_start_structure() -> None:
    """Verify top-level metadata and citation in stopp_start.yaml."""
    with open(STOPP_START_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["version"] == "3.0"
    assert data["source"] == "stopp_start"
    assert "citation" in data

    citation = data["citation"]
    assert citation.get("document_id")
    assert citation.get("title")
    assert citation.get("url")

    criteria = data.get("criteria", [])
    assert len(criteria) >= 40, f"Expected at least 40 criteria, found {len(criteria)}"


def test_stopp_start_entries() -> None:
    """Verify each criterion in stopp_start.yaml has valid fields and values."""
    with open(STOPP_START_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    seen_ids = set()
    for item in data.get("criteria", []):
        cid = item.get("id")
        assert cid, "Criterion missing 'id'"
        assert cid not in seen_ids, f"Duplicate criterion id: {cid}"
        seen_ids.add(cid)

        assert item.get("criterion_code"), f"{cid} missing criterion_code"
        assert item.get("section"), f"{cid} missing section"
        assert item.get("drug_class"), f"{cid} missing drug_class"

        ingredients = item.get("ingredients")
        assert isinstance(ingredients, list) and len(ingredients) > 0, (
            f"{cid} must have non-empty ingredients list"
        )

        persona = item.get("target_persona")
        assert persona in VALID_PERSONAS, f"{cid} has invalid persona: {persona}"

        rec = item.get("recommendation")
        assert rec in VALID_RECOMMENDATIONS, f"{cid} has invalid recommendation: {rec}"

        dim = item.get("risk_dimension")
        assert dim in VALID_DIMENSIONS, f"{cid} has invalid risk dimension: {dim}"

        rationale = item.get("clinical_rationale")
        assert rationale and len(rationale.strip()) > 20, (
            f"{cid} clinical rationale is too short or missing"
        )

        assert item.get("original_reference"), f"{cid} missing original_reference"


def test_acb_file_exists() -> None:
    """Verify that acb.yaml exists and is non-empty."""
    assert ACB_PATH.is_file(), f"Missing file: {ACB_PATH}"
    assert ACB_PATH.stat().st_size > 0, "acb.yaml is empty"


def test_acb_structure() -> None:
    """Verify top-level metadata and citation in acb.yaml."""
    with open(ACB_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["version"] == "2008"
    assert data["source"] == "acb"
    assert "citation" in data

    citation = data["citation"]
    assert citation.get("document_id")
    assert citation.get("title")
    assert citation.get("url")

    items = data.get("items", [])
    assert len(items) >= 20, f"Expected at least 20 ACB items, found {len(items)}"


def test_acb_entries() -> None:
    """Verify each item in acb.yaml has valid fields, scores, and dimensions."""
    with open(ACB_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    seen_ids = set()
    seen_ingredients = set()
    scores_present = set()

    for item in data.get("items", []):
        iid = item.get("id")
        assert iid, "ACB item missing 'id'"
        assert iid not in seen_ids, f"Duplicate ACB item id: {iid}"
        seen_ids.add(iid)

        ingredient = item.get("ingredient")
        assert ingredient, f"{iid} missing ingredient"
        assert ingredient not in seen_ingredients, f"Duplicate ingredient: {ingredient}"
        seen_ingredients.add(ingredient)

        score = item.get("acb_score")
        assert isinstance(score, int) and 0 <= score <= 3, (
            f"{iid} has invalid acb_score: {score} (must be 0-3)"
        )
        scores_present.add(score)

        persona = item.get("target_persona")
        assert persona in VALID_PERSONAS, f"{iid} has invalid persona: {persona}"

        dim = item.get("risk_dimension")
        assert dim in VALID_DIMENSIONS, f"{iid} has invalid risk dimension: {dim}"

        rationale = item.get("clinical_rationale")
        assert rationale and len(rationale.strip()) > 20, (
            f"{iid} clinical rationale is too short or missing"
        )

        assert item.get("original_reference"), f"{iid} missing original_reference"

    # Ensure all ACB score levels (0, 1, 2, 3) are represented
    assert scores_present == {0, 1, 2, 3}, f"Missing ACB score tiers: {scores_present}"
