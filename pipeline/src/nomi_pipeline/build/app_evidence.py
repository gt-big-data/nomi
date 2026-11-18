"""Write the v1 evidence table the app's scoring engine bundles (apps/mobile/src/scoring).

Reads the cited relative risks and baselines in pipeline/knowledge/evidence/ and the FAERS signal
summary (pipeline/derived/faers_signals.json, written by `pipeline evidence signals`). The engine
applies the formula in docs/scoring/v1-method.md to them; nothing here changes a number, it only
checks and copies.

Usage:
    uv run python -m nomi_pipeline.build.app_evidence
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import yaml

from nomi_pipeline.config import REPO_ROOT

KNOWLEDGE = REPO_ROOT / "pipeline" / "knowledge" / "ingredients"
EVIDENCE = REPO_ROOT / "pipeline" / "knowledge" / "evidence"
SIGNALS = REPO_ROOT / "pipeline" / "derived" / "faers_signals.json"
OUTPUT = REPO_ROOT / "apps" / "mobile" / "src" / "scoring" / "evidence.json"
REPORT = REPO_ROOT / "pipeline" / "reports" / "evidence_coverage.md"

# v1-method.md section 1: the dimensions with a serious outcome. The rest give no points.
OUTCOME_DIMENSIONS = (
    "liver",
    "gi_bleeding",
    "kidney",
    "cardiovascular_bp",
    "anticholinergic_cognitive",
    "sedation_falls",
    "serotonergic_interactions",
    "anticoagulant_bleeding",
    "pregnancy_lactation",
)
PERSONAS = frozenset(
    {
        "adult_18_64",
        "adult_65_plus",
        "teen_12_17",
        "child_6_11",
        "child_2_5",
        "under_2",
        "pregnant",
        "breastfeeding",
    }
)
CONDITIONS = frozenset(
    {
        "hypertension",
        "heart_disease",
        "kidney_disease",
        "liver_disease",
        "stomach_ulcer_or_bleeding",
        "glaucoma",
        "enlarged_prostate",
        "asthma",
        "diabetes",
        "thyroid_disease",
        "phenylketonuria",
        "heavy_alcohol_use",
    }
)
MEDICATION_TYPES = frozenset(
    {
        "anticoagulants",
        "antiplatelets",
        "maoi",
        "ssri_snri",
        "sedatives",
        "diuretics",
        "blood_pressure_medications",
        "corticosteroids",
    }
)
SCOPE_KEYS = {"persona": PERSONAS, "condition": CONDITIONS, "medication_type": MEDICATION_TYPES}
MEASURES = {"RR", "OR", "HR", "IRR"}
# Rule 18: the outcome ids each dimension's rows may carry. pregnancy_lactation rows name their
# own outcome and are never paired with a baseline, so they carry none.
OUTCOME_IDS = {
    "liver": {"acute_liver_injury", "acute_liver_failure"},
    "gi_bleeding": {"upper_gi_bleeding"},
    "kidney": {"aki_hospital"},
    "cardiovascular_bp": {"mi", "stroke", "mi_stroke"},
    "anticholinergic_cognitive": {"delirium_hospital"},
    "sedation_falls": {"fall_injury", "fracture", "hip_fracture"},
    "serotonergic_interactions": {"serotonin_syndrome"},
    "anticoagulant_bleeding": {"major_bleeding"},
    "pregnancy_lactation": set(),
}
EXPOSURE_WINDOWS = {"community_oral", "long_term", "inpatient"}
# Rule 12: "other" records a reference group the source does not state is non-use of the
# ingredient; the build drops it.
COMPARATORS = {"non_use", "within_group", "other"}
INTERVALS = {"confidence", "credible"}
# Rule 26: a baseline's age standardisation. Only all_ages bars it.
STANDARDISATION = {False, "within_range", "all_ages"}
# Rule 13 and 21: lower is preferred.
GRADE_RANK = {"meta_analysis": 0, "cohort": 1, "case_control": 1, "regulatory": 2}
GRADES = {"meta_analysis", "cohort", "case_control", "regulatory"}
TOKEN = re.compile(r"[a-z0-9_]+")
YEAR = re.compile(r"\b(19|20)\d\d\b")


def leading_scope(reason: str) -> dict[str, list[str]]:
    """The personas, conditions and co-medications a reason names before its first colon, the
    way the evidence files state who an insufficient entry is about ("breastfeeding: ...",
    "applies_to condition heavy_alcohol_use: ...", "pregnant/breastfeeding: ...")."""
    head = reason.split(":", 1)[0] if ":" in reason else ""
    tokens = TOKEN.findall(head.lower())
    scope = {key: sorted({t for t in tokens if t in known}) for key, known in SCOPE_KEYS.items()}
    return {key: values for key, values in scope.items() if values}


def _short(citation: str) -> str:
    """'Donati M, Conforti A, ... 2016;82' -> 'Donati 2016'."""
    author = citation.split(",")[0].split()[0]
    year = YEAR.search(citation)
    return f"{author} {year.group(0)}" if year else author


def _source(source: dict[str, Any], where: str) -> dict[str, Any]:
    for key in ("citation", "url", "location", "quote"):
        if not str(source.get(key) or "").strip():
            raise ValueError(f"{where}: source has no {key}")
    return {
        "source": "publication",
        "section": f"{_short(source['citation'])}, {source['location']}",
        "url": source["url"],
        "quote": source["quote"],
        "citation": source["citation"],
    }


def _dimension(row: dict[str, Any], where: str) -> str:
    if row["dimension"] not in OUTCOME_DIMENSIONS:
        raise ValueError(f"{where}: {row['dimension']} is not a v1 outcome")
    return str(row["dimension"])


def _applies(row: dict[str, Any], where: str) -> dict[str, Any]:
    applies = row.get("applies_to") or {}
    persona = applies.get("persona") or row.get("persona") or "all"
    condition = applies.get("condition", row.get("condition"))
    medication = applies.get("medication_type", row.get("medication_type"))
    if persona != "all" and persona not in PERSONAS:
        raise ValueError(f"{where}: unknown persona {persona}")
    if condition is not None and condition not in CONDITIONS:
        raise ValueError(f"{where}: unknown condition {condition}")
    if medication is not None and medication not in MEDICATION_TYPES:
        raise ValueError(f"{where}: unknown medication type {medication}")
    return {"persona": persona, "condition": condition, "medication_type": medication}


def _outcome(row: dict[str, Any], dimension: str, where: str) -> tuple[bool, str | None]:
    """Rule 10 and 18: whether the row measures the dimension's outcome, and which one."""
    match = row.get("outcome_match")
    if not isinstance(match, bool):
        raise ValueError(f"{where}: outcome_match must be true or false")
    outcome = row.get("outcome")
    if outcome == "other" or (dimension == "pregnancy_lactation" and outcome is None):
        if outcome == "other" and match:
            raise ValueError(f"{where}: outcome other cannot match")
        return match, None
    if outcome not in OUTCOME_IDS[dimension]:
        raise ValueError(
            f"{where}: outcome {outcome} is not one of {sorted(OUTCOME_IDS[dimension])}"
        )
    return match, outcome


def _relative_risk(row: dict[str, Any], where: str) -> dict[str, Any]:
    dimension = _dimension(row, where)
    outcome_match, outcome = _outcome(row, dimension, where)
    if row.get("exposure_window") not in EXPOSURE_WINDOWS:
        raise ValueError(f"{where}: exposure_window must be one of {sorted(EXPOSURE_WINDOWS)}")
    if row.get("comparator") not in COMPARATORS:
        raise ValueError(f"{where}: comparator must be one of {sorted(COMPARATORS)}")
    dose = row.get("dose_mg_per_day")
    if dose is not None:
        low, high = dose
        if not (low is None or high is None or 0 <= low < high):
            raise ValueError(f"{where}: dose range {dose}")
    applies = _applies(row, where)
    if row["comparator"] == "within_group" and not (
        applies["condition"] or applies["medication_type"]
    ):
        raise ValueError(f"{where}: a within_group row must name its group in applies_to")
    if row["measure"] not in MEASURES:
        raise ValueError(f"{where}: unknown measure {row['measure']}")
    if row["grade"] not in GRADES:
        raise ValueError(f"{where}: unknown grade {row['grade']}")
    estimate = float(row["estimate"])
    low, high = (float(x) for x in row["ci95"])
    if not (0 < low <= estimate <= high):
        raise ValueError(f"{where}: estimate {estimate} outside its interval {low}-{high}")
    interval = row.get("interval", "confidence")
    if interval not in INTERVALS:
        raise ValueError(f"{where}: interval must be one of {sorted(INTERVALS)}")
    population = _stratum_population(row, where)
    own = row.get("unexposed_incidence")
    unexposed = None
    if own is not None:
        rate = float(own["annual_incidence"])
        if not 0 < rate < 1:
            raise ValueError(f"{where}: unexposed incidence {rate} is not a probability")
        for key in ("as_reported", "location", "quote"):
            if not str(own.get(key) or "").strip():
                raise ValueError(f"{where}: unexposed_incidence has no {key}")
        personas = own.get("personas")
        if not personas or not set(personas) <= PERSONAS - {"all"}:
            raise ValueError(
                f"{where}: unexposed_incidence needs the personas its population covers"
            )
        cited = _source(row["source"], where)
        unexposed = {
            "annual_incidence": rate,
            "personas": sorted(personas),
            "as_reported": own["as_reported"],
            "citation": {
                **cited,
                "section": f"{cited['section'].split(',')[0]}, {own['location']}",
                "quote": own["quote"],
            },
        }
    return {
        "dimension": dimension,
        **applies,
        "interval": interval,
        "stratum_population": population,
        "unexposed_incidence": unexposed,
        "outcome": outcome,
        "outcome_match": outcome_match,
        "exposure_window": row["exposure_window"],
        "comparator": row["comparator"],
        "dose_mg_per_day": dose,
        "measure": row["measure"],
        "estimate": estimate,
        "ci95": [low, high],
        "grade": row["grade"],
        "exposure": row["exposure"],
        "population": row["population"],
        "citation": _source(row["source"], where),
    }


def _insufficient(row: dict[str, Any], where: str) -> dict[str, Any]:
    """Rule 7: an entry is shown to profiles with any persona, condition or co-medication its
    structured applies_to lists; with none listed, to every profile."""
    scope = {key: sorted(row.get("applies_to", {}).get(key) or []) for key in SCOPE_KEYS}
    for key, values in scope.items():
        unknown = set(values) - SCOPE_KEYS[key]
        if unknown:
            raise ValueError(f"{where}: unknown {key} {sorted(unknown)}")
    stated = leading_scope(row["reason"])
    if any(scope[key] != stated.get(key, []) for key in SCOPE_KEYS):
        raise ValueError(f"{where}: applies_to {scope} does not match the reason's {stated}")
    return {
        "dimension": _dimension(row, where),
        "personas": scope["persona"],
        "conditions": scope["condition"],
        "medication_types": scope["medication_type"],
        "reason": row["reason"],
    }


def _baseline(row: dict[str, Any], where: str) -> dict[str, Any]:
    dimension = _dimension(row, where)
    outcome_match, outcome = _outcome(row, dimension, where)
    if not isinstance(row.get("excludes_class_users"), bool):
        raise ValueError(f"{where}: excludes_class_users must be true or false")
    if row.get("age_standardised", False) not in STANDARDISATION:
        raise ValueError(f"{where}: age_standardised must be one of false, within_range, all_ages")
    incidence = float(row["annual_incidence"])
    if not 0 < incidence < 1:
        raise ValueError(f"{where}: annual incidence {incidence} is not a probability")
    return {
        "dimension": dimension,
        **_applies(row, where),
        "outcome": outcome,
        "outcome_match": outcome_match,
        "excludes_class_users": row["excludes_class_users"],
        "age_standardised": row.get("age_standardised", False),
        "stratum_population": _stratum_population(row, where),
        "annual_incidence": incidence,
        "as_reported": row["as_reported"],
        "population": row["population"],
        "citation": _source(row["source"], where),
    }


def _stratum_population(row: dict[str, Any], where: str) -> str | None:
    """Rule 25: the subgroup a stratum or baseline measures, as a lowercase id."""
    population = row.get("stratum_population")
    if population is not None and not TOKEN.fullmatch(str(population)):
        raise ValueError(f"{where}: stratum_population must be a lowercase id")
    return population


def _read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def collect(
    signals_path: Path = SIGNALS,
) -> tuple[dict[str, Any], dict[str, list[str]], list[str]]:
    """The evidence table, by ingredient file the dimensions it is missing (rule 9), and the rows
    the v1.1 rules dropped."""
    if not signals_path.exists():
        raise FileNotFoundError(f"{signals_path} missing; run `uv run pipeline evidence signals`")
    signals: dict[str, list[dict[str, Any]]] = json.loads(signals_path.read_text(encoding="utf-8"))
    kb = {p.stem: _read_yaml(p) for p in sorted(KNOWLEDGE.glob("*.yaml"))}
    rows: dict[str, list[dict[str, Any]]] = {}
    gaps: dict[str, list[dict[str, Any]]] = {}
    baselines: list[dict[str, Any]] = []
    max_doses: dict[str, float] = {}
    for path in sorted(EVIDENCE.glob("*.yaml")):
        data = _read_yaml(path)
        for i, row in enumerate(data.get("baselines") or []):
            baselines.append(_baseline(row, f"{path.name} baseline {i}"))
        for row in data.get("max_daily_doses") or []:
            _source(row["source"], f"{path.name} max dose {row['ingredient']}")
            max_doses[row["ingredient"]] = float(row["max_daily_dose_mg"])
        if data.get("group") == "baselines":
            continue
        for kind, target in (("relative_risks", rows), ("insufficient", gaps)):
            for i, row in enumerate(data.get(kind) or []):
                where = f"{path.name} {kind} {i} ({row.get('ingredient')} {row.get('dimension')})"
                if row["ingredient"] not in kb:
                    raise ValueError(f"{where}: no ingredient file {row['ingredient']}.yaml")
                parse = _relative_risk if kind == "relative_risks" else _insufficient
                target.setdefault(row["ingredient"], []).append(parse(row, where))

    dropped: list[str] = []
    baselines, why = _usable_baselines(baselines)
    dropped += why
    populations: dict[tuple[Any, ...], set[str]] = {}
    for b in baselines:
        if b["stratum_population"]:
            key = (b["dimension"], b["outcome"], b["medication_type"])
            populations.setdefault(key, set()).add(b["stratum_population"])
    for stem in list(rows):
        rows[stem], auto, why = _usable(stem, rows[stem], max_doses.get(stem), populations)
        dropped += why
        gaps.setdefault(stem, []).extend(
            g
            for g in auto
            if not any(
                e["dimension"] == g["dimension"] and _scope(e) == _scope(g)
                for e in gaps.get(stem, [])
            )
        )

    # Rule 9: an ingredient is covered when every outcome dimension v0 rated above 0 for it has
    # a row or an insufficient entry. Uncovered ingredients are left out, so products with them
    # are unrated rather than scored on part of the evidence.
    ingredients: dict[str, Any] = {}
    uncovered: dict[str, list[str]] = {}
    for stem, entry in kb.items():
        rated = {
            r["dimension"]
            for r in entry.get("ratings", []) + entry.get("modifiers", [])
            if r["dimension"] in OUTCOME_DIMENSIONS
            and (r.get("severity") or r.get("severity_change") or 0) > 0
        }
        seen = {r["dimension"] for r in rows.get(stem, []) + gaps.get(stem, [])}
        missing = sorted(rated - seen)
        if missing:
            uncovered[stem] = missing
            continue
        ingredients[entry["unii"]] = {
            "name": stem,
            "relative_risks": rows.get(stem, []),
            "insufficient": gaps.get(stem, []),
            "faers": signals.get(entry["unii"], []),
        }
    table = {
        "method": "docs/scoring/v1-method.md",
        "version": "1.2",
        "course_days": 10,
        "ingredients": dict(sorted(ingredients.items())),
        "baselines": baselines,
    }
    return table, uncovered, dropped


def _scope(gap: dict[str, Any]) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(gap[k]) for k in ("personas", "conditions", "medication_types"))


def _usable(
    stem: str,
    rows: list[dict[str, Any]],
    max_dose: float | None,
    populations: dict[tuple[Any, ...], set[str]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    """Rules 8.1, 10, 11, 13, 19, 21 and 25: the rows the engine may use, insufficient entries
    for pairs left with none, and a line per dropped row for the coverage report. populations
    maps (dimension, outcome, medication_type) to the stratum_population ids of its baselines."""
    keep: list[dict[str, Any]] = []
    dropped: list[str] = []
    for row in rows:
        cite = row["citation"]["section"]
        if not row["outcome_match"]:
            dropped.append(f"{stem} {row['dimension']}: outcome does not match ({cite})")
        elif row["comparator"] == "other":
            dropped.append(
                f"{stem} {row['dimension']}: comparator is not non-use (rule 12) ({cite})"
            )
        elif row["exposure_window"] != "community_oral":
            dropped.append(f"{stem} {row['dimension']}: {row['exposure_window']} exposure ({cite})")
        elif row["stratum_population"] and row["stratum_population"] not in (populations or {}).get(
            (row["dimension"], row["outcome"], row["medication_type"]), set()
        ):
            dropped.append(
                f"{stem} {row['dimension']}: stratum {row['stratum_population']} does not match "
                f"the baseline's population (rule 25) ({cite})"
            )
        else:
            keep.append(row)

    # Rule 8.1: of a source's dose strata for one pair, the one holding the label maximum.
    strata: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in keep:
        if row["dose_mg_per_day"] is not None:
            key = (
                row["dimension"],
                row["persona"],
                row["condition"],
                row["medication_type"],
                row["citation"]["url"],
            )
            strata.setdefault(key, []).append(row)
    for group in strata.values():
        if max_dose is None:
            raise ValueError(f"{stem}: dose strata but no max_daily_doses entry (rule 8.1)")
        chosen = _stratum_for(group, max_dose)
        for row in group:
            if row is not chosen:
                keep.remove(row)
                dropped.append(
                    f"{stem} {row['dimension']}: stratum {row['dose_mg_per_day']} mg/day, "
                    f"not the label maximum {max_dose:g} ({row['citation']['section']})"
                )

    # Rules 13 and 21: within one pair and scope, a stratum holding the label maximum beats an
    # undosed pool; otherwise the best grade wins. Ties stay for rule 3 (the largest).
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in keep:
        key = (
            row["dimension"],
            row["persona"],
            row["condition"],
            row["medication_type"],
            row["outcome"],
        )
        groups.setdefault(key, []).append(row)
    for group in groups.values():
        at_max = [
            r
            for r in group
            if r["dose_mg_per_day"] is not None
            and max_dose is not None
            and _holds(r["dose_mg_per_day"], max_dose)
        ]
        # Rule 21, then rule 13 among what is left.
        pool = at_max or group
        best = min(GRADE_RANK[r["grade"]] for r in pool)
        winners = [r for r in pool if GRADE_RANK[r["grade"]] == best]
        why = (
            "an estimate at the label maximum dose exists (rule 21)"
            if at_max
            else "a higher-grade estimate exists (rule 13)"
        )
        for row in group:
            if row not in winners:
                keep.remove(row)
                dropped.append(f"{stem} {row['dimension']}: {why} ({row['citation']['section']})")

    # Rules 19 and 28: a dropped row's profiles get an insufficient entry only when no usable
    # row covers them. A within-group row is never covered by a general one (rule 12).
    auto: list[dict[str, Any]] = []
    for row in rows:
        if row in keep:
            continue

        def covers(k: dict[str, Any], row: dict[str, Any] = row) -> bool:
            if k["dimension"] != row["dimension"]:
                return False
            if (k["persona"], k["condition"], k["medication_type"]) == (
                row["persona"],
                row["condition"],
                row["medication_type"],
            ):
                return True
            general = k["persona"] == "all" and not k["condition"] and not k["medication_type"]
            return general and row["comparator"] != "within_group"

        if any(covers(k) for k in keep):
            continue
        gap = {
            "dimension": row["dimension"],
            "personas": [] if row["persona"] == "all" else [row["persona"]],
            "conditions": [row["condition"]] if row["condition"] else [],
            "medication_types": [row["medication_type"]] if row["medication_type"] else [],
            "require_all": True,
            "reason": "Only estimates that do not meet the v1.1 and v1.2 rules were found "
            f"({row['citation']['section']}).",
        }
        if not any(a["dimension"] == gap["dimension"] and _scope(a) == _scope(gap) for a in auto):
            auto.append(gap)
    return keep, auto, dropped


def _holds(dose: list[float | None], max_dose: float) -> bool:
    low = dose[0] or 0.0
    high = dose[1] if dose[1] is not None else math.inf
    return low <= max_dose <= high


def _stratum_for(group: list[dict[str, Any]], max_dose: float) -> dict[str, Any]:
    def low(r: dict[str, Any]) -> float:
        return r["dose_mg_per_day"][0] or 0.0

    def high(r: dict[str, Any]) -> float:
        return r["dose_mg_per_day"][1] if r["dose_mg_per_day"][1] is not None else math.inf

    holding = [r for r in group if low(r) <= max_dose <= high(r)]
    if holding:
        return min(holding, key=low)
    below = [r for r in group if high(r) < max_dose]
    if not below:
        raise ValueError(f"no stratum at or below the label maximum {max_dose}")
    return max(below, key=high)


def _usable_baselines(
    baselines: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Rules 10 and 15."""
    dropped = []
    keep = []
    for b in baselines:
        if b["outcome_match"]:
            keep.append(b)
        else:
            dropped.append(
                f"baseline {b['dimension']} {b['persona']}: outcome does not match "
                f"({b['citation']['section']})"
            )

    standardised = [b for b in keep if b["age_standardised"] == "all_ages"]
    for b in standardised:
        keep.remove(b)
        dropped.append(
            f"baseline {b['dimension']} {b['persona']}: age-standardised to all ages (rule 26) "
            f"({b['citation']['section']})"
        )

    # Rule 26: a rate without class users comes before the age rule, so the persona is not part
    # of the key.
    def key(b: dict[str, Any]) -> tuple[Any, ...]:
        return (b["dimension"], b["outcome"], b["condition"], b["medication_type"])

    excluding = {key(b) for b in keep if b["excludes_class_users"]}
    out = []
    for b in keep:
        if key(b) in excluding and not b["excludes_class_users"]:
            dropped.append(
                f"baseline {b['dimension']} {b['persona']}: a rate without class users exists "
                f"({b['citation']['section']})"
            )
        else:
            out.append(b)
    return out, dropped


def render(signals_path: Path = SIGNALS) -> str:
    return json.dumps(collect(signals_path)[0], indent=2, ensure_ascii=False) + "\n"


def coverage_report(signals_path: Path = SIGNALS) -> str:
    table, uncovered, dropped = collect(signals_path)
    ingredients = table["ingredients"]
    lines = [
        "# Evidence coverage (v1)",
        "",
        f"{len(ingredients)} of {len(ingredients) + len(uncovered)} ingredients covered.",
        "",
    ]
    if uncovered:
        lines += ["## Not covered (products with these are unrated)", ""]
        lines += [f"- {stem}: no row for {', '.join(dims)}" for stem, dims in uncovered.items()]
        lines.append("")
    lines += ["## Rows not used (rules 8.1, 10, 11, 15)", ""]
    lines += [f"- {line}" for line in dropped] or ["None."]
    lines.append("")
    lines += ["## FAERS signal with no published estimate (flagged for review)", ""]
    for entry in ingredients.values():
        estimated = {r["dimension"] for r in entry["relative_risks"]}
        for s in entry["faers"]:
            if s["dimension"] in OUTCOME_DIMENSIONS and s["dimension"] not in estimated:
                lines.append(
                    f"- {entry['name']} {s['dimension']} ({s['age_band']}): "
                    f"IC025 {s['ic025']}, {s['reports']} reports, {s['event_group']}"
                )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    OUTPUT.write_text(render(), encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(coverage_report(), encoding="utf-8")
