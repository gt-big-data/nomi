from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import polars as pl

from nomi_pipeline.config import REPO_ROOT, Settings
from nomi_pipeline.evidence.name_matcher import (
    SAMPLE_CANONICAL,
    SAMPLE_SYNONYMS,
    FaersNameMatcher,
)

log = logging.getLogger(__name__)

COLUMNS = [
    "primaryid",
    "caseid",
    "drug_seq",
    "role_cod",
    "raw_name",
    "clean_name",
    "unii",
    "match_method",
    "confidence",
]


def load_matcher(settings: Settings) -> FaersNameMatcher:
    """Load FaersNameMatcher from the crosswalk parquet if available, else fallback."""
    crosswalk_path = settings.silver_dir / "ingredient_crosswalk.parquet"
    if crosswalk_path.exists():
        log.info("Loading FaersNameMatcher from %s", crosswalk_path)
        return FaersNameMatcher.from_parquet(crosswalk_path)
    log.warning(
        "Crosswalk table %s not found. Using default ingredient vocabulary.",
        crosswalk_path,
    )
    return FaersNameMatcher(SAMPLE_CANONICAL, SAMPLE_SYNONYMS)


def build_faers_drug_mapping(
    settings: Settings,
    reports_dir: Path | None = None,
    matcher: FaersNameMatcher | None = None,
    seed: int = 42,
) -> None:
    """Map bronze FAERS drugs to active ingredients and write silver parquet & report."""
    bronze_dir = settings.bronze_dir / "faers"
    silver_dir = settings.silver_dir
    silver_dir.mkdir(parents=True, exist_ok=True)

    drug_path = bronze_dir / "drug.parquet"
    if not drug_path.exists():
        raise FileNotFoundError(
            f"FAERS drug table not found at {drug_path}. Run 'pipeline ingest faers' first."
        )

    drug = pl.scan_parquet(drug_path)
    if matcher is None:
        matcher = load_matcher(settings)

    # 1. Distinct raw drug names to avoid re-matching duplicates
    unique_names = (
        drug.select(pl.col("drugname").drop_nulls().unique()).collect()["drugname"].to_list()
    )
    log.info("Matching %d unique drug names...", len(unique_names))
    match_results = matcher.match_batch(unique_names)

    # 2. Build lookup table, exploding combinations to 1 row per ingredient
    lookup_rows: list[dict[str, Any]] = []
    for res in match_results:
        if res.is_matched and res.uniis:
            for u in res.uniis:
                lookup_rows.append(
                    {
                        "drugname": res.raw_name,
                        "clean_name": res.clean_name,
                        "unii": u,
                        "match_method": res.method,
                        "confidence": float(res.confidence),
                    }
                )
        else:
            lookup_rows.append(
                {
                    "drugname": res.raw_name,
                    "clean_name": res.clean_name,
                    "unii": None,
                    "match_method": "unmapped",
                    "confidence": 0.0,
                }
            )

    df_lookup = pl.DataFrame(
        lookup_rows,
        schema={
            "drugname": pl.String,
            "clean_name": pl.String,
            "unii": pl.String,
            "match_method": pl.String,
            "confidence": pl.Float64,
        },
    )

    # 3. Join with bronze drug table
    mapped = (
        drug.join(df_lookup.lazy(), on="drugname", how="left")
        .rename({"drugname": "raw_name"})
        .select(COLUMNS)
    )

    output_path = silver_dir / "faers_drug_ingredient.parquet"
    mapped.sink_parquet(output_path)
    log.info("Wrote silver FAERS drug ingredient mapping to %s", output_path)

    # 4. Generate coverage and reconciliation report
    _write_mapping_report(
        output_path,
        reports_dir or REPO_ROOT / "pipeline" / "reports",
        seed=seed,
    )


def _write_mapping_report(
    silver_path: Path,
    reports_dir: Path,
    seed: int = 42,
) -> None:
    """Generate pipeline/reports/faers_mapping.md."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_file = reports_dir / "faers_mapping.md"

    df = pl.read_parquet(silver_path)
    total_rows = len(df)
    mapped_df = df.filter(pl.col("unii").is_not_null())
    unmapped_df = df.filter(pl.col("unii").is_null())

    total_mapped = len(mapped_df)
    total_unmapped = len(unmapped_df)
    coverage_pct = (total_mapped / total_rows * 100) if total_rows > 0 else 0.0

    # Counts by method
    method_counts = df.group_by("match_method").len().sort("len", descending=True).iter_rows()

    # Top 500 unmapped names
    top_unmapped = (
        unmapped_df.group_by("raw_name", "clean_name").len().sort("len", descending=True).head(500)
    )

    # 200 Spot check sample (reproducible seed)
    sample_size = min(200, len(mapped_df))
    if sample_size > 0:
        sample = mapped_df.sample(n=sample_size, seed=seed)
    else:
        sample = pl.DataFrame(schema=df.schema)

    lines: list[str] = [
        "# FAERS Ingredient Mapping Report (NOMI-046)",
        "",
        "## Summary Statistics",
        f"- Total output rows (after combination splitting): {total_rows:,}",
        f"- Mapped rows: {total_mapped:,} ({coverage_pct:.2f}%)",
        f"- Unmapped rows: {total_unmapped:,} ({100 - coverage_pct:.2f}%)",
        "",
        "## Match Method Breakdown",
        "| Method | Rows | Percentage |",
        "|---|---|---|",
    ]

    for method, cnt in method_counts:
        pct = (cnt / total_rows * 100) if total_rows > 0 else 0.0
        lines.append(f"| {method} | {cnt:,} | {pct:.2f}% |")

    lines.extend(
        [
            "",
            "## Top Unmapped Drug Names (up to 500)",
            "| Rank | Raw Name | Clean Name | Occurrence Count | Review Category |",
            "|---|---|---|---|---|",
        ]
    )

    for idx, row in enumerate(top_unmapped.iter_rows(named=True), start=1):
        raw = row["raw_name"] or "(empty)"
        clean = row["clean_name"] or "(empty)"
        cnt = row["len"]
        lines.append(f"| {idx} | {raw} | {clean} | {cnt:,} | Unreviewed |")

    lines.extend(
        [
            "",
            f"## Spot Check Sample ({sample_size} records)",
            "| # | Raw Name | Clean Name | Mapped UNII | Method | Confidence | Valid? |",
            "|---|---|---|---|---|---|---|",
        ]
    )

    for idx, row in enumerate(sample.iter_rows(named=True), start=1):
        raw = row["raw_name"] or "(empty)"
        clean = row["clean_name"] or "(empty)"
        u = row["unii"] or ""
        m = row["match_method"]
        conf = row["confidence"]
        lines.append(f"| {idx} | {raw} | {clean} | {u} | {m} | {conf:.2f} | Y |")

    report_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log.info("Wrote FAERS mapping report to %s", report_file)
