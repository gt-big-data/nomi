"""Tests for the v1 evidence build (apps/mobile/src/scoring/evidence.json)."""

from __future__ import annotations

from typing import Any

import pytest
from nomi_pipeline.build import app_evidence as ae
from nomi_pipeline.build.app_evidence import OUTPUT, render


def test_the_app_evidence_matches_the_knowledge_base() -> None:
    assert OUTPUT.read_text(encoding="utf-8") == render(), (
        "Stale: run uv run python -m nomi_pipeline.build.app_evidence"
    )


def test_every_ingredient_is_covered() -> None:
    _, uncovered = ae.collect()
    assert uncovered == {}


def _row(**changes: Any) -> dict[str, Any]:
    row = {
        "ingredient": "acetaminophen",
        "dimension": "liver",
        "applies_to": {"persona": "all", "condition": None, "medication_type": None},
        "measure": "OR",
        "estimate": 2.0,
        "ci95": [1.5, 3.0],
        "exposure": "x",
        "population": "y",
        "grade": "cohort",
        "source": {"citation": "Doe J, et al. 2020", "url": "u", "location": "T1", "quote": "q"},
    }
    return {**row, **changes}


def test_a_valid_row_is_copied() -> None:
    out = ae._relative_risk(_row(), "t")
    assert out["estimate"] == 2.0
    assert out["persona"] == "all"
    assert out["citation"]["section"] == "Doe 2020, T1"


@pytest.mark.parametrize(
    "changes",
    [
        {"estimate": 4.0},
        {"ci95": [0, 3.0]},
        {"dimension": "pediatric"},
        {"measure": "beta"},
        {"grade": "case_series"},
        {"applies_to": {"persona": "adults"}},
        {"applies_to": {"persona": "all", "condition": "gout"}},
        {"source": {"citation": "Doe 2020", "url": "u", "location": "T1", "quote": ""}},
    ],
)
def test_a_bad_row_fails_the_build(changes: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        ae._relative_risk(_row(**changes), "t")


def test_leading_scope_reads_ids_before_the_colon() -> None:
    assert ae.leading_scope("pregnant/breastfeeding: none") == {
        "persona": ["breastfeeding", "pregnant"]
    }
    assert ae.leading_scope("applies_to condition liver_disease: none") == {
        "condition": ["liver_disease"]
    }
    # Ids after the colon are not a scope.
    assert ae.leading_scope("no study: kidney_disease was not studied") == {}


def test_insufficient_scope_must_match_its_reason() -> None:
    row = {"ingredient": "x", "dimension": "liver", "reason": "liver_disease: none"}
    with pytest.raises(ValueError):
        ae._insufficient(row, "t")
    scoped = {**row, "applies_to": {"condition": ["liver_disease"]}}
    assert ae._insufficient(scoped, "t")["conditions"] == ["liver_disease"]


def test_baseline_must_be_a_probability() -> None:
    row = {
        "dimension": "kidney",
        "persona": "all",
        "annual_incidence": 1.2,
        "as_reported": "x",
        "population": "y",
        "source": {"citation": "Doe 2020", "url": "u", "location": "T1", "quote": "q"},
    }
    with pytest.raises(ValueError):
        ae._baseline(row, "t")
