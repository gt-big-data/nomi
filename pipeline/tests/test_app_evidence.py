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
    _, uncovered, _ = ae.collect()
    assert uncovered == {}


def _row(**changes: Any) -> dict[str, Any]:
    row = {
        "ingredient": "acetaminophen",
        "dimension": "liver",
        "applies_to": {"persona": "all", "condition": None, "medication_type": None},
        "outcome": "acute_liver_injury",
        "outcome_match": True,
        "exposure_window": "community_oral",
        "comparator": "non_use",
        "dose_mg_per_day": None,
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
        {"outcome": "fracture"},
        {"outcome_match": "yes"},
        {"exposure_window": "chronic"},
        {"comparator": "within_group"},
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
        "outcome": "aki_hospital",
        "outcome_match": True,
        "excludes_class_users": False,
        "annual_incidence": 1.2,
        "as_reported": "x",
        "population": "y",
        "source": {"citation": "Doe 2020", "url": "u", "location": "T1", "quote": "q"},
    }
    with pytest.raises(ValueError):
        ae._baseline(row, "t")


def _parsed(**changes: Any) -> dict[str, Any]:
    return ae._relative_risk(_row(**changes), "t")


def test_rows_failing_rules_10_and_11_are_dropped_and_become_insufficient() -> None:
    keep, auto, dropped = ae._usable(
        "acetaminophen",
        [_parsed(outcome_match=False), _parsed(exposure_window="long_term")],
        None,
    )
    assert keep == []
    assert len(dropped) == 2
    assert [g["dimension"] for g in auto] == ["liver"]


def test_the_stratum_holding_the_label_maximum_is_used() -> None:
    strata = [
        _parsed(estimate=2.0, ci95=[1.5, 3.0], dose_mg_per_day=[0, 2999]),
        _parsed(estimate=6.0, ci95=[3.5, 11.0], dose_mg_per_day=[3000, None]),
    ]
    keep, _, dropped = ae._usable("acetaminophen", strata, 4000)
    assert [r["estimate"] for r in keep] == [6.0]
    assert len(dropped) == 1
    with pytest.raises(ValueError):
        ae._usable("acetaminophen", strata, None)


def test_a_stratum_below_the_maximum_is_used_when_none_holds_it() -> None:
    strata = [
        _parsed(estimate=2.0, ci95=[1.5, 3.0], dose_mg_per_day=[0, 500]),
        _parsed(estimate=3.0, ci95=[2.5, 4.0], dose_mg_per_day=[501, 1000]),
    ]
    keep, _, _ = ae._usable("aspirin", strata, 4000)
    assert [r["estimate"] for r in keep] == [3.0]


def test_baselines_without_class_users_win() -> None:
    def b(excludes: bool, rate: float) -> dict[str, Any]:
        return {
            "dimension": "gi_bleeding",
            "persona": "all",
            "condition": None,
            "medication_type": None,
            "outcome": "upper_gi_bleeding",
            "outcome_match": True,
            "excludes_class_users": excludes,
            "annual_incidence": rate,
            "citation": {"section": "x"},
        }

    keep, dropped = ae._usable_baselines([b(False, 0.002), b(True, 0.001)])
    assert [k["annual_incidence"] for k in keep] == [0.001]
    assert len(dropped) == 1
