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
            "age_standardised": False,
            "annual_incidence": rate,
            "citation": {"section": "x"},
        }

    keep, dropped = ae._usable_baselines([b(False, 0.002), b(True, 0.001)])
    assert [k["annual_incidence"] for k in keep] == [0.001]
    assert len(dropped) == 1


def test_a_stratum_at_the_label_maximum_beats_an_undosed_pool() -> None:
    pool = _parsed(estimate=1.3, ci95=[1.2, 1.5], grade="meta_analysis")
    stratum = _parsed(
        estimate=3.6, ci95=[2.6, 5.1], grade="case_control", dose_mg_per_day=[2001, None]
    )
    keep, _, dropped = ae._usable("acetaminophen", [pool, stratum], 4000)
    assert [r["estimate"] for r in keep] == [3.6]
    assert any("rule 21" in d for d in dropped)


def test_a_meta_analysis_beats_a_single_study_without_dose() -> None:
    meta = _parsed(estimate=1.7, ci95=[1.4, 2.1], grade="meta_analysis")
    single = _parsed(estimate=3.2, ci95=[1.8, 5.8], grade="case_control")
    keep, _, _ = ae._usable("acetaminophen", [meta, single], None)
    assert [r["estimate"] for r in keep] == [1.7]


def test_a_dropped_subgroup_row_covered_by_a_general_row_makes_no_note() -> None:
    general = _parsed()
    subgroup = _parsed(
        applies_to={
            "persona": "adult_65_plus",
            "condition": "hypertension",
            "medication_type": None,
        },
        exposure_window="long_term",
    )
    _, auto, _ = ae._usable("acetaminophen", [general, subgroup], None)
    assert auto == []


def test_a_dropped_within_group_row_is_not_covered_by_a_general_row() -> None:
    general = _parsed()
    group = _parsed(
        applies_to={"persona": "all", "condition": None, "medication_type": "diuretics"},
        comparator="within_group",
        outcome_match=False,
    )
    _, auto, _ = ae._usable("acetaminophen", [general, group], None)
    assert auto and auto[0]["require_all"] and auto[0]["medication_types"] == ["diuretics"]


def test_unexposed_incidence_needs_a_quote() -> None:
    with pytest.raises(ValueError):
        _parsed(
            unexposed_incidence={"annual_incidence": 0.001, "as_reported": "x", "location": "y"}
        )
    with pytest.raises(ValueError):
        _parsed(
            unexposed_incidence={
                "annual_incidence": 0.001,
                "as_reported": "x",
                "location": "T2",
                "quote": "q",
            }
        )
    ok = _parsed(
        unexposed_incidence={
            "annual_incidence": 0.001,
            "personas": ["adult_65_plus"],
            "as_reported": "x",
            "location": "T2",
            "quote": "q",
        }
    )
    assert ok["unexposed_incidence"]["citation"]["section"] == "Doe 2020, T2"


def test_age_standardised_and_class_user_baselines_give_way() -> None:
    def b(persona: str, excludes: bool, standardised: Any, rate: float) -> dict[str, Any]:
        return {
            "dimension": "gi_bleeding",
            "persona": persona,
            "condition": None,
            "medication_type": None,
            "outcome": "upper_gi_bleeding",
            "outcome_match": True,
            "excludes_class_users": excludes,
            "age_standardised": standardised,
            "annual_incidence": rate,
            "citation": {"section": "x"},
        }

    keep, dropped = ae._usable_baselines(
        [
            b("adult_65_plus", False, False, 0.002),
            b("all", True, False, 0.0006),
            b("all", False, "all_ages", 0.001),
            b("adult_65_plus", True, "within_range", 0.0009),
        ]
    )
    assert [k["annual_incidence"] for k in keep] == [0.0006, 0.0009]
    assert len(dropped) == 2


def test_the_stratum_matching_the_baseline_population_is_used() -> None:
    def stratum(population: str, estimate: float) -> dict[str, Any]:
        return _parsed(
            dimension="anticoagulant_bleeding",
            outcome="major_bleeding",
            applies_to={"persona": "all", "condition": None, "medication_type": "anticoagulants"},
            comparator="within_group",
            estimate=estimate,
            ci95=[1.1, 2.0],
            stratum_population=population,
        )

    rows = [stratum("vka_users", 1.55), stratum("doac_users", 1.42)]
    key = ("anticoagulant_bleeding", "major_bleeding", "anticoagulants")
    keep, _, dropped = ae._usable("ibuprofen", rows, None, {key: {"doac_users"}})
    assert [r["estimate"] for r in keep] == [1.42]
    assert any("rule 25" in d for d in dropped)
    # A baseline of no named population matches neither stratum.
    keep, auto, _ = ae._usable("ibuprofen", rows, None, {})
    assert keep == [] and auto[0]["medication_types"] == ["anticoagulants"]


def test_a_meta_analysis_beats_a_single_study_among_strata_at_the_maximum() -> None:
    single = _parsed(
        estimate=3.6, ci95=[2.6, 5.1], grade="case_control", dose_mg_per_day=[2001, None]
    )
    meta = _parsed(
        estimate=1.0,
        ci95=[0.5, 1.9],
        grade="meta_analysis",
        dose_mg_per_day=[4000, None],
        source={"citation": "Roe J, et al. 2002", "url": "v", "location": "T4", "quote": "q"},
    )
    keep, _, _ = ae._usable("acetaminophen", [single, meta], 4000)
    assert [r["estimate"] for r in keep] == [1.0]


def test_a_comparator_other_than_non_use_is_dropped() -> None:
    keep, _, dropped = ae._usable("acetaminophen", [_parsed(comparator="other")], None)
    assert keep == [] and "rule 29" in dropped[0]


def test_the_narrowest_stratum_holding_the_maximum_is_used() -> None:
    wide = _parsed(estimate=3.6, ci95=[2.6, 5.1], dose_mg_per_day=[2001, None])
    narrow = _parsed(estimate=6.5, ci95=[2.4, 17.6], dose_mg_per_day=[4000, None])
    keep, _, _ = ae._usable("acetaminophen", [wide, narrow], 4000)
    assert [r["estimate"] for r in keep] == [6.5]
