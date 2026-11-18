"""Write the ingredient ratings the app's scoring engine bundles (apps/mobile/src/scoring).

The output holds only what scoring reads: each knowledge-base ingredient's nonzero ratings and its
modifiers, and, for the reference products in packages/schema/examples, where their own label
differs from the knowledge base and the hard stops their records carry.

Usage:
    uv run python -m nomi_pipeline.build.app_ratings
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[4]
KNOWLEDGE = ROOT / "pipeline" / "knowledge" / "ingredients"
EXAMPLES = ROOT / "packages" / "schema" / "examples"
OUTPUT = ROOT / "apps" / "mobile" / "src" / "scoring" / "ratings.json"

# Duplicate ingredients across products are the Medicine Cabinet's job, not the single-product
# score (docs/system-design.md, section 6.2).
NOT_SCORED = {"duplicate_dosing"}
CITATION_FIELDS = ("source", "section", "url", "quote")
MODIFIER_FIELDS = ("dimension", "condition", "medication_type", "severity_change", "personas")


def _citations(item: dict[str, Any]) -> list[dict[str, Any]]:
    return [{k: c[k] for k in CITATION_FIELDS if k in c} for c in item.get("citations", [])]


def _rating(rating: dict[str, Any]) -> dict[str, Any]:
    return {
        "dimension": rating["dimension"],
        "persona": rating["persona"],
        "severity": rating["severity"],
        "citations": _citations(rating),
    }


def _ingredient(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": entry["name"],
        "ratings": [
            _rating(r)
            for r in entry["ratings"]
            if r["severity"] and r["dimension"] not in NOT_SCORED
        ],
        "modifiers": [
            {**{k: m[k] for k in MODIFIER_FIELDS if k in m}, "citations": _citations(m)}
            for m in entry.get("modifiers", [])
            if m["dimension"] not in NOT_SCORED
        ],
    }


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _label(folder: Path, kb: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """The ratings where this product's label differs from the knowledge base, for the personas
    its records cover, and the hard stops its records carry (they name the product)."""
    records = _read_json(folder / "expected-scores.json")
    personas = [record["profile"]["persona"] for record in records]
    ratings = []
    for ingredient in _read_json(folder / "ingredient-dimensions.json"):
        kb_ratings = {
            (r["dimension"], r["persona"]): r["severity"] for r in kb[ingredient["unii"]]["ratings"]
        }
        own = {(r["dimension"], r["persona"]): r for r in ingredient["ratings"]}
        for (dimension, persona), severity in sorted(kb_ratings.items()):
            if persona not in personas or dimension in NOT_SCORED:
                continue
            rating = own.get((dimension, persona), {"severity": 0})
            if rating["severity"] != severity:
                ratings.append(
                    {
                        "unii": ingredient["unii"],
                        **_rating({**rating, "dimension": dimension, "persona": persona}),
                    }
                )
    hard_stops = [
        {"persona": record["profile"]["persona"], **stop}
        for record in records
        for stop in record["hard_stops_triggered"]
    ]
    return {"personas": sorted(set(personas)), "ratings": ratings, "hard_stops": hard_stops}


def build() -> dict[str, Any]:
    kb = {
        entry["unii"]: entry
        for entry in (
            yaml.safe_load(path.read_text(encoding="utf-8"))
            for path in sorted(KNOWLEDGE.glob("*.yaml"))
        )
    }
    labels = {
        _read_json(folder / "product.json")["spl_set_id"]: _label(folder, kb)
        for folder in sorted(p for p in EXAMPLES.iterdir() if p.is_dir())
    }
    return {
        "ingredients": {unii: _ingredient(kb[unii]) for unii in sorted(kb)},
        "labels": dict(sorted(labels.items())),
    }


def render() -> str:
    return json.dumps(build(), indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(), encoding="utf-8")
