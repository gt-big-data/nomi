"""Validation tests for digitized clinical criteria (STOPP/START and ACB).

Tests verify that YAML files in pipeline/knowledge/criteria/ are well-formed,
conform to expected schemas, contain valid risk dimensions and personas,
and have complete citation metadata.
"""

import json
from pathlib import Path

import yaml

CRITERIA_DIR = Path(__file__).resolve().parents[2] / "knowledge" / "criteria"
STOPP_START_PATH = CRITERIA_DIR / "stopp_start.yaml"
ACB_PATH = CRITERIA_DIR / "acb.yaml"

COMMON_DEFS = json.loads(
    (CRITERIA_DIR.parents[2] / "packages/schema/schemas/common.schema.json").read_text(
        encoding="utf-8"
    )
)["$defs"]
VALID_DIMENSIONS = set(COMMON_DEFS["dimension"]["enum"])
VALID_PERSONAS = set(COMMON_DEFS["persona"]["enum"])
VALID_CONDITIONS = set(COMMON_DEFS["condition"]["enum"])
VALID_MEDICATION_TYPES = set(COMMON_DEFS["medication_type"]["enum"])

VALID_RECOMMENDATIONS = {"avoid", "caution", "consider"}


def test_stopp_start_file_exists() -> None:
    """Verify that stopp_start.yaml exists and is non-empty."""
    assert STOPP_START_PATH.is_file(), f"Missing file: {STOPP_START_PATH}"
    assert STOPP_START_PATH.stat().st_size > 0, "stopp_start.yaml is empty"


def test_stopp_start_structure() -> None:
    """Verify top-level metadata and citation in stopp_start.yaml."""
    with open(STOPP_START_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["version"] == "3.0"
    assert data["source"] == "stopp_start"
    assert "citation" in data

    citation = data["citation"]
    assert citation.get("document_id")
    assert citation.get("title")
    assert citation.get("url")

    criteria = data.get("criteria", [])
    assert criteria, "stopp_start.yaml has no criteria"


def test_stopp_start_entries() -> None:
    """Verify each criterion in stopp_start.yaml has valid fields and values."""
    with open(STOPP_START_PATH, encoding="utf-8") as f:
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

        condition = item.get("condition")
        assert condition is None or condition in VALID_CONDITIONS, (
            f"{cid} has invalid condition: {condition}"
        )
        medication_type = item.get("medication_type")
        assert medication_type is None or medication_type in VALID_MEDICATION_TYPES, (
            f"{cid} has invalid medication_type: {medication_type}"
        )

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
    with open(ACB_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data["version"] == "2008"
    assert data["source"] == "acb"
    assert "citation" in data

    citation = data["citation"]
    assert citation.get("document_id")
    assert citation.get("title")
    assert citation.get("url")

    items = data.get("items", [])
    assert items, "acb.yaml has no items"


def test_acb_entries() -> None:
    """Verify each item in acb.yaml has valid fields, scores, and dimensions."""
    with open(ACB_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    seen_ids = set()
    seen_ingredients = set()

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
        assert isinstance(score, int) and 1 <= score <= 3, (
            f"{iid} has invalid acb_score: {score} (the ACB scale only lists scores 1-3)"
        )

        persona = item.get("target_persona")
        assert persona in VALID_PERSONAS, f"{iid} has invalid persona: {persona}"

        dim = item.get("risk_dimension")
        assert dim in VALID_DIMENSIONS, f"{iid} has invalid risk dimension: {dim}"

        rationale = item.get("clinical_rationale")
        assert rationale and len(rationale.strip()) > 20, (
            f"{iid} clinical rationale is too short or missing"
        )

        assert item.get("original_reference"), f"{iid} missing original_reference"
