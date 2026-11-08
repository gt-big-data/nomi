"""Validate the five NOMI-015 reference products in the existing schema CI job."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from nomi_schema import validate

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
KNOWLEDGE = Path(__file__).resolve().parents[3] / "pipeline" / "knowledge" / "ingredients"
PRODUCTS = ["tylenol", "aleve", "zzzquil", "nyquil", "store-brand-diphenhydramine"]
PROFILES = [
    {"persona": "adult_18_64", "conditions": [], "medication_types": []},
    {"persona": "adult_65_plus", "conditions": ["hypertension"], "medication_types": []},
    {"persona": "child_6_11", "conditions": [], "medication_types": []},
]

# Draft fixture convention (see examples/README.md), not the rubric.
POINTS_PER_SEVERITY = 6
# Duplicate ingredients across products are the Medicine Cabinet's job, not the single-product
# score (docs/system-design.md, section 6.2).
NOT_SCORED = {"duplicate_dosing"}

# Where a product's own label differs from the ingredient-level rating in the knowledge base.
LABEL_OVERRIDES = {
    # "children under 12 yrs do not use"
    ("zzzquil", "TC2D6JAD40", "pediatric", "child_6_11"): 3,
    # "children 4 to under 12 yrs ask a doctor"
    ("nyquil", "V9BI9B5YI2", "pediatric", "child_6_11"): 2,
}


def read(folder: Path, name: str) -> Any:
    return json.loads((folder / f"{name}.json").read_text(encoding="utf-8"))


def knowledge_base() -> dict[str, dict[str, Any]]:
    files = (yaml.safe_load(p.read_text(encoding="utf-8")) for p in KNOWLEDGE.glob("*.yaml"))
    return {entry["unii"]: entry for entry in files}


def draft_points(ingredients: list[dict[str, Any]], profile: dict[str, Any]) -> dict[str, Any]:
    """Points and contributing UNIIs per dimension under the draft fixture convention."""
    severities: dict[str, dict[str, int]] = {}
    for ingredient in ingredients:
        for rating in ingredient["ratings"]:
            if rating["persona"] != profile["persona"] or rating["dimension"] in NOT_SCORED:
                continue
            change = sum(
                m["severity_change"]
                for m in ingredient.get("modifiers", [])
                if m["dimension"] == rating["dimension"]
                and (
                    m.get("condition") in profile["conditions"]
                    or m.get("medication_type") in profile["medication_types"]
                )
                and profile["persona"] in m.get("personas", [profile["persona"]])
            )
            severity = min(3, rating["severity"] + change)
            if severity:
                severities.setdefault(rating["dimension"], {})[ingredient["unii"]] = severity
    out = {}
    for dimension, by_unii in severities.items():
        top = max(by_unii.values())
        out[dimension] = {
            "points": top * POINTS_PER_SEVERITY,
            "ingredient_uniis": sorted(u for u, s in by_unii.items() if s == top),
        }
    return out


@pytest.mark.parametrize("name", PRODUCTS)
def test_reference_product_validates(name: str) -> None:
    folder = EXAMPLES / name
    product = read(folder, "product")
    ingredients = read(folder, "ingredient-dimensions")
    scores = read(folder, "expected-scores")

    validate("product", product)
    assert isinstance(ingredients, list) and ingredients
    for ingredient in ingredients:
        validate("ingredient-dimensions", ingredient)
    active_uniis = {ingredient["unii"] for ingredient in product["ingredients"]}
    assert len(ingredients) == len(active_uniis)
    assert {ingredient["unii"] for ingredient in ingredients} == active_uniis

    assert isinstance(scores, list) and len(scores) == 3
    for score in scores:
        validate("score-record", score)
        assert score["ndc11"] == product["ndc11"]
        assert score["score"] == max(0, 100 - sum(c["points"] for c in score["contributions"]))
        band = "green" if score["score"] >= 75 else "yellow" if score["score"] >= 50 else "red"
        assert score["tier"] == ("red" if score["hard_stops_triggered"] else band)
    assert [score["profile"] for score in scores] == PROFILES


@pytest.mark.parametrize("name", PRODUCTS)
def test_expected_scores_follow_from_the_ratings(name: str) -> None:
    folder = EXAMPLES / name
    ingredients = read(folder, "ingredient-dimensions")
    for score in read(folder, "expected-scores"):
        recorded = {
            c["dimension"]: {
                "points": c["points"],
                "ingredient_uniis": sorted(c["ingredient_uniis"]),
            }
            for c in score["contributions"]
        }
        assert recorded == draft_points(ingredients, score["profile"]), score["profile"]


@pytest.mark.parametrize("name", PRODUCTS)
def test_ratings_match_the_knowledge_base(name: str) -> None:
    # Ingredients rated in pipeline/knowledge/ingredients must agree with it for the three
    # profiles, except where the product's own label says otherwise (LABEL_OVERRIDES).
    kb = knowledge_base()
    personas = {profile["persona"] for profile in PROFILES}
    for ingredient in read(EXAMPLES / name, "ingredient-dimensions"):
        entry = kb.get(ingredient["unii"])
        if entry is None:
            continue
        expected = {
            (r["dimension"], r["persona"]): r["severity"]
            for r in entry["ratings"]
            if r["persona"] in personas and r["dimension"] not in NOT_SCORED
        }
        for key in list(expected):
            override = LABEL_OVERRIDES.get((name, ingredient["unii"], *key))
            if override is not None:
                expected[key] = override
        actual = {(r["dimension"], r["persona"]): r["severity"] for r in ingredient["ratings"]}
        # Dimensions the example leaves out count as 0, as in scoring.
        missing = {k: v for k, v in expected.items() if v and k not in actual}
        differ = {k: (actual[k], v) for k, v in expected.items() if k in actual and actual[k] != v}
        assert (missing, differ) == ({}, {}), ingredient["name"]
