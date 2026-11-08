"""Check the ingredient ratings in pipeline/knowledge/ingredients (NOMI-034, NOMI-035)."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
import yaml
from nomi_schema import errors

PIPELINE = Path(__file__).resolve().parents[2]
FILES = sorted((PIPELINE / "knowledge" / "ingredients").glob("*.yaml"))
INGREDIENTS: dict[str, dict[str, Any]] = {
    path.name: yaml.safe_load(path.read_text(encoding="utf-8")) for path in FILES
}

COMMON = json.loads(
    (PIPELINE.parent / "packages/schema/schemas/common.schema.json").read_text(encoding="utf-8")
)
DIMENSIONS = COMMON["$defs"]["dimension"]["enum"]
PERSONAS = COMMON["$defs"]["persona"]["enum"]


@pytest.mark.parametrize("name", INGREDIENTS)
def test_matches_the_schema(name: str) -> None:
    assert errors("ingredient-dimensions", INGREDIENTS[name]) == []


@pytest.mark.parametrize("name", INGREDIENTS)
def test_rates_every_dimension_for_every_persona_once(name: str) -> None:
    # Scoring reads a missing rating as no risk, so every pair is written out, 0 included.
    pairs = Counter((r["dimension"], r["persona"]) for r in INGREDIENTS[name]["ratings"])
    assert {p: n for p, n in pairs.items() if n > 1} == {}
    assert {(d, p) for d in DIMENSIONS for p in PERSONAS} - set(pairs) == set()


def test_each_unii_has_one_file() -> None:
    uniis = Counter(ingredient["unii"] for ingredient in INGREDIENTS.values())
    assert {unii: n for unii, n in uniis.items() if n > 1} == {}
