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

# Draft fixture convention (see examples/README.md), from the docs/scoring/dimensions.md summary
# table: the low end of the 1 and 2 ranges, and 51 for 3 (inside "35-50+") so a 3 is red.
POINTS = {1: 5, 2: 15, 3: 51}
# Duplicate ingredients across products are the Medicine Cabinet's job, not the single-product
# score (docs/system-design.md, section 6.2).
NOT_SCORED = {"duplicate_dosing"}

# Where a product's own label differs from the ingredient-level rating in the knowledge base.
LABEL_OVERRIDES = {
    # "children under 12 yrs do not use"
    ("zzzquil", "TC2D6JAD40", "pediatric", "child_6_11"): 3,
    # "children 4 to under 12 yrs ask a doctor"
    ("nyquil", "V9BI9B5YI2", "pediatric", "child_6_11"): 2,
    # Adult products; children's acetaminophen liquids are dosed for ages 2 to 11.
    # "children under 12 years ask a doctor"
    ("tylenol", "362O9ITL9D", "pediatric", "child_6_11"): 2,
    # "children 4 to under 12 yrs ask a doctor"
    ("nyquil", "362O9ITL9D", "pediatric", "child_6_11"): 2,
}


# Hard stops each record must carry, by product and persona.
HARD_STOPS = {
    ("zzzquil", "child_6_11"): [
        {"id": "hs_zzzquil_under_12", "message": "This ZzzQuil label prohibits use below age 12."}
    ],
}

# Drug Facts sections (LOINC codes) that label citations may name. Labels code Warnings
# subsections such as "Stomach bleeding warning" as 42229-5 (SPL unclassified section).
SECTIONS = {
    "34068-7": "Directions",
    "42229-5": "Warnings / ",
    "50567-7": "When using",
    "50568-5": "Ask a doctor or pharmacist",
    "50569-3": "Ask a doctor",
    "50570-1": "Do not use",
    "53414-9": "Pregnancy or breast-feeding",
    "55105-1": "Purpose",
}


def read(folder: Path, name: str) -> Any:
    return json.loads((folder / f"{name}.json").read_text(encoding="utf-8"))


def knowledge_base() -> dict[str, dict[str, Any]]:
    files = (yaml.safe_load(p.read_text(encoding="utf-8")) for p in KNOWLEDGE.glob("*.yaml"))
    return {entry["unii"]: entry for entry in files}


def applies(modifier: dict[str, Any], profile: dict[str, Any]) -> bool:
    return (
        modifier.get("condition") in profile["conditions"]
        or modifier.get("medication_type") in profile["medication_types"]
    ) and profile["persona"] in modifier.get("personas", [profile["persona"]])


def expected_contributions(
    ingredients: list[dict[str, Any]], profile: dict[str, Any]
) -> list[dict[str, Any]]:
    """Contributions under the draft convention, largest first.

    Each ingredient's severity is its rating plus matching modifiers, capped at 3 (an unrated
    dimension counts as 0). Each dimension costs the points of its highest severity; the
    citations are those of the ingredients at that severity.
    """
    # dimension -> unii -> (severity, citations)
    found: dict[str, dict[str, tuple[int, list[dict[str, Any]]]]] = {}
    for ingredient in ingredients:
        ratings = {
            r["dimension"]: r for r in ingredient["ratings"] if r["persona"] == profile["persona"]
        }
        modifiers = [m for m in ingredient.get("modifiers", []) if applies(m, profile)]
        for dimension in ratings.keys() | {m["dimension"] for m in modifiers}:
            if dimension in NOT_SCORED:
                continue
            rating = ratings.get(dimension, {"severity": 0})
            used = [m for m in modifiers if m["dimension"] == dimension]
            severity = min(3, rating["severity"] + sum(m["severity_change"] for m in used))
            if severity:
                citations = rating.get("citations", []) + [c for m in used for c in m["citations"]]
                found.setdefault(dimension, {})[ingredient["unii"]] = (severity, citations)
    out = []
    for dimension, by_unii in found.items():
        top = max(severity for severity, _ in by_unii.values())
        uniis = sorted(u for u, (severity, _) in by_unii.items() if severity == top)
        sources: list[dict[str, Any]] = []
        for unii in uniis:
            sources += [c for c in by_unii[unii][1] if c not in sources]
        out.append(
            {
                "dimension": dimension,
                "points": POINTS[top],
                "ingredient_uniis": uniis,
                "citations": sources,
            }
        )
    return sorted(out, key=lambda c: (-c["points"], c["dimension"]))


def label_forbids_age(ingredients: list[dict[str, Any]], persona: str) -> bool:
    # The only hard stop the fixtures use: the product's label says do not use at this age.
    return any(
        r["dimension"] == "pediatric" and r["persona"] == persona and r["severity"] == 3
        for ingredient in ingredients
        for r in ingredient["ratings"]
    )


def modifier_key(m: dict[str, Any]) -> tuple[str, str, int, tuple[str, ...]]:
    return (
        m["dimension"],
        m.get("condition") or m["medication_type"],
        m["severity_change"],
        tuple(sorted(m.get("personas", []))),
    )


def tier(score: int, hard_stops: list[Any]) -> str:
    if hard_stops:
        return "red"
    return "green" if score >= 75 else "yellow" if score >= 50 else "red"


def test_a_hard_stop_makes_any_score_red() -> None:
    assert tier(100, [{"id": "x"}]) == "red"
    assert [tier(s, []) for s in (75, 74, 50, 49)] == ["green", "yellow", "yellow", "red"]


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
    assert [score["profile"] for score in scores] == PROFILES


@pytest.mark.parametrize("name", PRODUCTS)
def test_expected_scores_follow_from_the_ratings(name: str) -> None:
    folder = EXAMPLES / name
    ingredients = read(folder, "ingredient-dimensions")
    for score in read(folder, "expected-scores"):
        expected = expected_contributions(ingredients, score["profile"])
        assert score["contributions"] == expected, score["profile"]
        assert score["score"] == max(0, 100 - sum(c["points"] for c in expected))
        persona = score["profile"]["persona"]
        stops = HARD_STOPS.get((name, persona), [])
        assert score["hard_stops_triggered"] == stops, persona
        assert bool(stops) == label_forbids_age(ingredients, persona)
        assert score["tier"] == tier(score["score"], stops)
        # One explanation per contribution, citing the same sources.
        explained = {e["template_id"]: e["citations"] for e in score["explanation"]}
        extra = {"NOMI-015_fixture_draft", "NOMI-015_child_directions"}
        assert explained.keys() - extra == {f"NOMI-015_{c['dimension']}" for c in expected}
        for contribution in expected:
            assert explained[f"NOMI-015_{contribution['dimension']}"] == contribution["citations"]


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

        assert sorted(map(modifier_key, ingredient.get("modifiers", []))) == sorted(
            map(modifier_key, entry.get("modifiers", []))
        ), ingredient["name"]


@pytest.mark.parametrize("name", PRODUCTS)
def test_label_citations_point_at_this_label(name: str) -> None:
    folder = EXAMPLES / name
    product = read(folder, "product")
    items = [
        item
        for ingredient in read(folder, "ingredient-dimensions")
        for item in ingredient["ratings"] + ingredient.get("modifiers", [])
    ]
    for score in read(folder, "expected-scores"):
        items += score["contributions"] + score["explanation"]
    for item in items:
        for citation in item.get("citations", []):
            if citation["source"] != "fda_label":
                assert citation.get("url"), citation
                continue
            assert citation["document_id"] == product["spl_set_id"], citation
            prefix = f"SPL v{product['spl_version']}: "
            assert citation["section"].startswith(prefix), citation
            section = citation["section"].removeprefix(prefix)
            codes = [code for code in SECTIONS if f"({code})" in section]
            # A section without a code must be a Warnings subsection, like the liver warning.
            assert len(codes) == 1 or (not codes and section.startswith("Warnings / ")), citation
            if codes:
                assert section.startswith(SECTIONS[codes[0]]), citation


def test_label_overrides_are_still_needed() -> None:
    kb = knowledge_base()
    for (_, unii, dimension, persona), severity in LABEL_OVERRIDES.items():
        ratings = {(r["dimension"], r["persona"]): r["severity"] for r in kb[unii]["ratings"]}
        assert ratings[(dimension, persona)] != severity
