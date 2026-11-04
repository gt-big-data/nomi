"""Validate the five NOMI-015 reference products in the existing schema CI job."""

import json
from pathlib import Path

import pytest
from nomi_schema import validate

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"
PRODUCTS = ["tylenol", "aleve", "zzzquil", "nyquil", "store-brand-diphenhydramine"]
PROFILES = [
    {"persona": "adult_18_64", "conditions": [], "medication_types": []},
    {"persona": "adult_65_plus", "conditions": ["hypertension"], "medication_types": []},
    {"persona": "child_6_11", "conditions": [], "medication_types": []},
]


@pytest.mark.parametrize("name", PRODUCTS)
def test_reference_product_validates(name):
    folder = EXAMPLES / name
    product = json.loads((folder / "product.json").read_text())
    ingredients = json.loads((folder / "ingredient-dimensions.json").read_text())
    scores = json.loads((folder / "expected-scores.json").read_text())

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
        for contribution in score["contributions"]:
            assert set(contribution.get("ingredient_uniis", [])) <= active_uniis
    assert [score["profile"] for score in scores] == PROFILES
