"""Write the v1 evidence table the app's scoring engine bundles (apps/mobile/src/scoring).

Reads the cited relative risks and baselines in pipeline/knowledge/evidence/ and, when the FAERS
stage has run, the IC025 signals in silver/faers_signals.parquet. The engine applies the formula
in docs/scoring/v1-method.md to them; nothing here changes a number, it only checks and copies.

Usage:
    uv run python -m nomi_pipeline.build.app_evidence
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[4]
KNOWLEDGE = ROOT / "pipeline" / "knowledge" / "ingredients"
EVIDENCE = ROOT / "pipeline" / "knowledge" / "evidence"
OUTPUT = ROOT / "apps" / "mobile" / "src" / "scoring" / "evidence.json"
REPORT = ROOT / "pipeline" / "reports" / "evidence_coverage.md"

log = logging.getLogger(__name__)

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
PERSONAS = {
    "all",
    "adult_18_64",
    "adult_65_plus",
    "teen_12_17",
    "child_6_11",
    "child_2_5",
    "under_2",
    "pregnant",
    "breastfeeding",
}
MEASURES = {"RR", "OR", "HR", "IRR"}
GRADES = {"meta_analysis", "cohort", "case_control", "regulatory"}
# v1-method.md section 7 rule 7: an insufficient reason that names who it is about.
APPLIES_TO = re.compile(r"applies_to (persona|condition|medication_type) ([a-z0-9_]+)")
YEAR = re.compile(r"\b(19|20)\d\d\b")


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


def _applies(row: dict[str, Any], where: str) -> dict[str, Any]:
    applies = row.get("applies_to") or {}
    persona = applies.get("persona") or row.get("persona") or "all"
    if persona not in PERSONAS:
        raise ValueError(f"{where}: unknown persona {persona}")
    return {
        "persona": persona,
        "condition": applies.get("condition", row.get("condition")),
        "medication_type": applies.get("medication_type", row.get("medication_type")),
    }


def _relative_risk(row: dict[str, Any], where: str) -> dict[str, Any]:
    if row["dimension"] not in OUTCOME_DIMENSIONS:
        raise ValueError(f"{where}: {row['dimension']} is not a v1 outcome")
    if row["measure"] not in MEASURES:
        raise ValueError(f"{where}: unknown measure {row['measure']}")
    if row["grade"] not in GRADES:
        raise ValueError(f"{where}: unknown grade {row['grade']}")
    estimate = float(row["estimate"])
    low, high = (float(x) for x in row["ci95"])
    if not (0 < low <= estimate <= high):
        raise ValueError(f"{where}: estimate {estimate} outside its interval {low}-{high}")
    return {
        "dimension": row["dimension"],
        **_applies(row, where),
        "measure": row["measure"],
        "estimate": estimate,
        "ci95": [low, high],
        "grade": row["grade"],
        "exposure": row["exposure"],
        "population": row["population"],
        "citation": _source(row["source"], where),
    }


def _insufficient(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"dimension": row["dimension"], "reason": row["reason"]}
    for key, value in APPLIES_TO.findall(row["reason"]):
        out.setdefault(key, value)
    return out


def _baseline(row: dict[str, Any], where: str) -> dict[str, Any]:
    if row["dimension"] not in OUTCOME_DIMENSIONS:
        raise ValueError(f"{where}: {row['dimension']} is not a v1 outcome")
    incidence = float(row["annual_incidence"])
    if not 0 < incidence < 1:
        raise ValueError(f"{where}: annual incidence {incidence} is not a probability")
    return {
        "dimension": row["dimension"],
        **_applies(row, where),
        "annual_incidence": incidence,
        "as_reported": row["as_reported"],
        "population": row["population"],
        "citation": _source(row["source"], where),
    }


def _faers(signals_path: Path | None) -> dict[str, list[dict[str, Any]]]:
    """By UNII: the strongest signal (IC025 above 0) per dimension and age band, sexes pooled."""
    if signals_path is None or not signals_path.exists():
        return {}
    import polars as pl

    rows = (
        pl.read_parquet(signals_path)
        .filter(pl.col("sex") == "all", pl.col("ic025") > 0)
        .sort("ic025", descending=True)
        .unique(["unii", "dimension", "age_band"], keep="first")
        .sort("unii", "dimension", "age_band")
    )
    out: dict[str, list[dict[str, Any]]] = {}
    for r in rows.iter_rows(named=True):
        out.setdefault(r["unii"], []).append(
            {
                "dimension": r["dimension"],
                "age_band": r["age_band"],
                "event_group": r["event_group"],
                "ic025": round(r["ic025"], 3),
                "reports": r["report_count"],
            }
        )
    return out


def build(signals_path: Path | None = None) -> dict[str, Any]:
    kb = {p.stem: yaml.safe_load(p.read_text(encoding="utf-8")) for p in KNOWLEDGE.glob("*.yaml")}
    rows: dict[str, list[dict[str, Any]]] = {}
    gaps: dict[str, list[dict[str, Any]]] = {}
    baselines: list[dict[str, Any]] = []
    for path in sorted(EVIDENCE.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        for i, row in enumerate(data.get("baselines") or []):
            baselines.append(_baseline(row, f"{path.name} baseline {i}"))
        for i, row in enumerate(data.get("relative_risks") or []):
            where = f"{path.name} row {i} ({row.get('ingredient')} {row.get('dimension')})"
            if row["ingredient"] not in kb:
                raise ValueError(f"{where}: no ingredient file {row['ingredient']}.yaml")
            rows.setdefault(row["ingredient"], []).append(_relative_risk(row, where))
        if data.get("group") == "baselines":
            continue
        for row in data.get("insufficient") or []:
            if row["ingredient"] not in kb:
                raise ValueError(f"{path.name}: no ingredient file {row['ingredient']}.yaml")
            gaps.setdefault(row["ingredient"], []).append(_insufficient(row))

    # Rule 9: an ingredient is covered when every outcome dimension v0 rated above 0 for it has
    # a row or an insufficient entry. Uncovered ingredients are left out, so products with them
    # are unrated rather than scored on part of the evidence.
    signals = _faers(signals_path)
    ingredients: dict[str, Any] = {}
    uncovered: dict[str, list[str]] = {}
    for stem in sorted(kb):
        entry = kb[stem]
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
    _write_report(kb, ingredients, uncovered, bool(signals))
    return {
        "method": "docs/scoring/v1-method.md",
        "course_days": 10,
        "ingredients": ingredients,
        "baselines": baselines,
    }


def _write_report(
    kb: dict[str, Any], ingredients: dict[str, Any], uncovered: dict[str, list[str]], faers: bool
) -> None:
    lines = [
        "# Evidence coverage (v1)",
        "",
        f"{len(ingredients)} of {len(kb)} ingredients covered.",
        "",
    ]
    if uncovered:
        lines += ["## Not covered (products with these are unrated)", ""]
        lines += [f"- {stem}: no row for {', '.join(dims)}" for stem, dims in uncovered.items()]
        lines.append("")
    lines += ["## FAERS signal with no published estimate (flagged for review)", ""]
    if not faers:
        lines.append("FAERS signals not built; run `uv run pipeline evidence signals`.")
    for entry in ingredients.values():
        estimated = {r["dimension"] for r in entry["relative_risks"]}
        for s in entry["faers"]:
            if s["dimension"] in OUTCOME_DIMENSIONS and s["dimension"] not in estimated:
                lines.append(
                    f"- {entry['name']} {s['dimension']} ({s['age_band']}): "
                    f"IC025 {s['ic025']}, {s['reports']} reports, {s['event_group']}"
                )
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def render(signals_path: Path | None = None) -> str:
    return json.dumps(build(signals_path), indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    from nomi_pipeline.config import Settings

    OUTPUT.write_text(render(Settings().silver_dir / "faers_signals.parquet"), encoding="utf-8")
