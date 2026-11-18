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


def _relative_risk(row: dict[str, Any], where: str) -> dict[str, Any]:
    if row["measure"] not in MEASURES:
        raise ValueError(f"{where}: unknown measure {row['measure']}")
    if row["grade"] not in GRADES:
        raise ValueError(f"{where}: unknown grade {row['grade']}")
    estimate = float(row["estimate"])
    low, high = (float(x) for x in row["ci95"])
    if not (0 < low <= estimate <= high):
        raise ValueError(f"{where}: estimate {estimate} outside its interval {low}-{high}")
    return {
        "dimension": _dimension(row, where),
        **_applies(row, where),
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
    incidence = float(row["annual_incidence"])
    if not 0 < incidence < 1:
        raise ValueError(f"{where}: annual incidence {incidence} is not a probability")
    return {
        "dimension": _dimension(row, where),
        **_applies(row, where),
        "annual_incidence": incidence,
        "as_reported": row["as_reported"],
        "population": row["population"],
        "citation": _source(row["source"], where),
    }


def _read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def collect(signals_path: Path = SIGNALS) -> tuple[dict[str, Any], dict[str, list[str]]]:
    """The evidence table and, by ingredient file, the dimensions it is missing (rule 9)."""
    if not signals_path.exists():
        raise FileNotFoundError(f"{signals_path} missing; run `uv run pipeline evidence signals`")
    signals: dict[str, list[dict[str, Any]]] = json.loads(signals_path.read_text(encoding="utf-8"))
    kb = {p.stem: _read_yaml(p) for p in sorted(KNOWLEDGE.glob("*.yaml"))}
    rows: dict[str, list[dict[str, Any]]] = {}
    gaps: dict[str, list[dict[str, Any]]] = {}
    baselines: list[dict[str, Any]] = []
    for path in sorted(EVIDENCE.glob("*.yaml")):
        data = _read_yaml(path)
        for i, row in enumerate(data.get("baselines") or []):
            baselines.append(_baseline(row, f"{path.name} baseline {i}"))
        if data.get("group") == "baselines":
            continue
        for kind, target in (("relative_risks", rows), ("insufficient", gaps)):
            for i, row in enumerate(data.get(kind) or []):
                where = f"{path.name} {kind} {i} ({row.get('ingredient')} {row.get('dimension')})"
                if row["ingredient"] not in kb:
                    raise ValueError(f"{where}: no ingredient file {row['ingredient']}.yaml")
                parse = _relative_risk if kind == "relative_risks" else _insufficient
                target.setdefault(row["ingredient"], []).append(parse(row, where))

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
        "course_days": 10,
        "ingredients": dict(sorted(ingredients.items())),
        "baselines": baselines,
    }
    return table, uncovered


def render(signals_path: Path = SIGNALS) -> str:
    return json.dumps(collect(signals_path)[0], indent=2, ensure_ascii=False) + "\n"


def coverage_report(signals_path: Path = SIGNALS) -> str:
    table, uncovered = collect(signals_path)
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
