"""Check the five-warning catalogue and its real label fixtures."""

import json
from collections import Counter
from pathlib import Path

import yaml

PIPELINE = Path(__file__).resolve().parents[2]
WARNINGS = yaml.safe_load(
    (PIPELINE / "knowledge/mandated_warnings.yaml").read_text(encoding="utf-8")
)["warnings"]
FIXTURES = [
    json.loads(path.read_text(encoding="utf-8"))
    for path in sorted((PIPELINE / "tests/fixtures/warnings").glob("*.json"))
]


def test_catalogue():
    assert isinstance(WARNINGS, list) and len(WARNINGS) == 5
    ids = []
    for warning in WARNINGS:
        for field in ("id", "dimension"):
            assert isinstance(warning[field], str) and warning[field].strip()
        for field in ("wording_variants", "ingredients", "citations"):
            values = warning[field]
            assert isinstance(values, list) and values
            assert all(isinstance(value, str) and value.strip() for value in values)
        ids.append(warning["id"])
    assert len(set(ids)) == len(ids)


def test_fixtures():
    assert len(FIXTURES) == 50
    known_ids = {warning["id"] for warning in WARNINGS}
    ids = []
    for fixture in FIXTURES:
        assert isinstance(fixture["id"], str) and fixture["id"].strip()
        assert isinstance(fixture["text"], str) and fixture["text"].strip()
        expected = fixture["expected_warnings"]
        assert isinstance(expected, list)
        assert all(isinstance(warning_id, str) for warning_id in expected)
        assert len(set(expected)) == len(expected)
        assert set(expected) <= known_ids
        assert fixture["source"]["url"].startswith("https://")
        ids.append(fixture["id"])
    assert len(set(ids)) == len(ids)


def test_at_least_five_negatives():
    assert sum(fixture["expected_warnings"] == [] for fixture in FIXTURES) >= 5


def test_every_warning_covered_at_least_twice():
    coverage = Counter(
        warning_id
        for fixture in FIXTURES
        for warning_id in fixture["expected_warnings"]
    )
    for warning in WARNINGS:
        assert coverage[warning["id"]] >= 2, warning["id"]
