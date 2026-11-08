"""Check the mandated warnings catalogue and its real label fixtures (NOMI-017)."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from nomi_pipeline.extract.mandated_warnings import find_warnings, load_catalogue, normalize

PIPELINE = Path(__file__).resolve().parents[2]
WARNINGS = load_catalogue()
FIXTURES: list[dict[str, Any]] = [
    json.loads(path.read_text(encoding="utf-8"))
    for path in sorted((PIPELINE / "tests/fixtures/warnings").glob("*.json"))
]

COMMON = json.loads(
    (PIPELINE.parent / "packages/schema/schemas/common.schema.json").read_text(encoding="utf-8")
)
DIMENSIONS = set(COMMON["$defs"]["dimension"]["enum"])
CITATION = Draft202012Validator({**COMMON, "$ref": "#/$defs/citation"})


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


def test_no_variant_contains_another_warnings_variant() -> None:
    # Otherwise text with one warning would also report the other.
    variants = [(w["id"], normalize(v)) for w in WARNINGS for v in w["wording_variants"]]
    clashes = [(a, b) for a, va in variants for b, vb in variants if a != b and vb in va]
    assert clashes == []


def test_normalize_ignores_punctuation_quotes_and_accents() -> None:
    assert normalize("Reye’s syndrome:\n• Children") == "reye's syndrome children"
    assert normalize("Hígado") == "higado"


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


def test_full_warnings_sections_with_several_warnings() -> None:
    # Whole Warnings sections, so recall is measured on real layouts, not hand-cropped spans.
    full = [f for f in FIXTURES if f["id"].startswith("full_section_")]
    assert len(full) >= 5
    assert sum(len(f["expected_warnings"]) >= 2 for f in full) >= 5


def test_every_warning_covered_at_least_twice() -> None:
    coverage = Counter(w for fixture in FIXTURES for w in fixture["expected_warnings"])
    assert {w["id"]: coverage[w["id"]] for w in WARNINGS if coverage[w["id"]] < 2} == {}


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f["id"])
def test_catalogue_wording_finds_exactly_the_expected_warnings(fixture: dict[str, Any]) -> None:
    assert find_warnings(fixture["text"]) == set(fixture["expected_warnings"])
