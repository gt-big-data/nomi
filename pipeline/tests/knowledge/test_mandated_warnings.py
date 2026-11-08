"""Check the mandated warnings catalogue and its real label fixtures (NOMI-017)."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator

PIPELINE = Path(__file__).resolve().parents[2]
WARNINGS: list[dict[str, Any]] = yaml.safe_load(
    (PIPELINE / "knowledge/mandated_warnings.yaml").read_text(encoding="utf-8")
)["warnings"]
FIXTURES: list[dict[str, Any]] = [
    json.loads(path.read_text(encoding="utf-8"))
    for path in sorted((PIPELINE / "tests/fixtures/warnings").glob("*.json"))
]

COMMON = json.loads(
    (PIPELINE.parent / "packages/schema/schemas/common.schema.json").read_text(encoding="utf-8")
)
DIMENSIONS = set(COMMON["$defs"]["dimension"]["enum"])
CITATION = Draft202012Validator({**COMMON, "$ref": "#/$defs/citation"})


def normalize(text: str) -> str:
    """Lowercase, straighten quotes, and keep only letters, digits and apostrophes."""
    text = text.lower().replace("’", "'").replace("‘", "'")
    return " ".join(re.sub(r"[^a-z0-9']+", " ", text).split())


def find_warnings(text: str) -> set[str]:
    """The catalogue's matching rule: any wording variant appears in the normalized text."""
    label = normalize(text)
    return {w["id"] for w in WARNINGS if any(normalize(v) in label for v in w["wording_variants"])}


def test_catalogue_has_at_least_ten_unique_warnings() -> None:
    ids = [w["id"] for w in WARNINGS]
    assert len(ids) >= 10
    assert len(set(ids)) == len(ids)


@pytest.mark.parametrize("warning", WARNINGS, ids=lambda w: w["id"])
def test_warning_entry(warning: dict[str, Any]) -> None:
    assert set(warning) == {"id", "ingredients", "dimensions", "wording_variants", "citations"}
    assert re.fullmatch(r"[a-z0-9_]+", warning["id"])
    for field in ("ingredients", "wording_variants"):
        assert warning[field] and all(isinstance(v, str) and v.strip() for v in warning[field])
    assert set(warning["dimensions"]) <= DIMENSIONS, "use dimension ids from common.schema.json"
    assert warning["citations"]
    for citation in warning["citations"]:
        problems = [e.message for e in CITATION.iter_errors(citation)]
        assert not problems, problems


def test_wording_variants_are_unique_to_one_warning() -> None:
    owners = Counter(normalize(v) for w in WARNINGS for v in set(w["wording_variants"]))
    assert [v for v, n in owners.items() if n > 1] == []


def test_fixtures_are_well_formed() -> None:
    assert len(FIXTURES) >= 50
    known = {w["id"] for w in WARNINGS}
    ids = []
    for fixture in FIXTURES:
        assert fixture["text"].strip()
        assert set(fixture["expected_warnings"]) <= known
        assert fixture["source"]["url"].startswith("https://")
        ids.append(fixture["id"])
    assert len(set(ids)) == len(ids)


def test_at_least_five_negatives() -> None:
    assert sum(fixture["expected_warnings"] == [] for fixture in FIXTURES) >= 5


def test_every_warning_covered_at_least_twice() -> None:
    coverage = Counter(w for fixture in FIXTURES for w in fixture["expected_warnings"])
    assert {w["id"]: coverage[w["id"]] for w in WARNINGS if coverage[w["id"]] < 2} == {}


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["id"])
def test_catalogue_wording_finds_exactly_the_expected_warnings(fixture: dict[str, Any]) -> None:
    assert find_warnings(fixture["text"]) == set(fixture["expected_warnings"])
